import hashlib
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token

from app.models.user_model import User, UserRole, AuthProvider
from app.models.product_model import Product
from app.models.order_model import Order, OrderStatus
from app.models.order_items_model import Order_item
from app.models.address_model import Address
from app.services.payment_service import initiate_payment, handle_notification
from app.services.order_service import update_order
from app.services import ValidationResponse


# =============================================================================
# HELPERS
# =============================================================================

def _make_signature(order_id, status_code, gross_amount, server_key):
    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    return hashlib.sha512(raw.encode("utf-8")).hexdigest()


def _mock_snap(token="tok-123", redirect="https://sandbox.midtrans.example/redirect/tok-123"):
    """Return a MagicMock Snap client whose create_transaction returns a fixed token."""
    snap = MagicMock()
    snap.create_transaction.return_value = {"token": token, "redirect_url": redirect}
    return snap


class _Base:
    _counter = 0

    @classmethod
    def _next_id(cls):
        _Base._counter += 1
        return _Base._counter

    def _seller(self, db_session):
        n = self._next_id()
        u = User(username=f'pseller{n}', email=f'pseller{n}@test.com', age=30, is_active=True,
                 provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
                 roles=[UserRole.SELLER])
        db_session.add(u); db_session.commit()
        return u

    def _buyer(self, db_session):
        n = self._next_id()
        u = User(username=f'pbuyer{n}', email=f'pbuyer{n}@test.com', age=25, is_active=True,
                 provider=AuthProvider.PASSWORD_HASH, provider_key=generate_password_hash('p'),
                 roles=[UserRole.BUYER])
        db_session.add(u); db_session.commit()
        return u

    def _product(self, db_session, seller, stock=10, price='100'):
        n = self._next_id()
        p = Product(user_id=seller.id, name=f'PProd{n}', slug=f'pprod{n}', uuid=f'puuid{n}',
                    stock=stock, brand='B', description='D', price=Decimal(price), is_active=True)
        db_session.add(p); db_session.commit()
        return p

    def _pending_order(self, db_session, buyer, product, quantity=2):
        order = Order(user_id=buyer.id, name='pay order', status=OrderStatus.PENDING,
                      subtotal=Decimal('200'), discount_percent=0, discount_amount=0,
                      tax_percent=11, tax_amount=Decimal('22'), total=Decimal('222'))
        db_session.add(order); db_session.commit()
        oi = Order_item(order_id=order.id, product_id=product.id, quantity=quantity,
                        compound_price=Decimal('200'))
        db_session.add(oi); db_session.commit()
        return order

    def _address(self, db_session, buyer, is_default=True):
        a = Address(user_id=buyer.id, label='Home', recipient_name='Buyer',
                    phone='+6281234567890', address_line='Jl. Test 1', city='Jakarta',
                    province='DKI Jakarta', postal_code='12345', is_default=is_default)
        db_session.add(a); db_session.commit()
        return a


# =============================================================================
# INITIATE PAYMENT
# =============================================================================

class TestInitiatePayment(_Base):

    def test_initiate_success_keeps_pending_and_stores_ref(self, app, db_session):
        """Initiate creates a Snap tx, stores payment_ref, and leaves order PENDING (no stock deducted)."""
        with app.app_context():
            seller = self._seller(db_session)
            buyer = self._buyer(db_session)
            product = self._product(db_session, seller, stock=10)
            order = self._pending_order(db_session, buyer, product, quantity=3)
            addr = self._address(db_session, buyer, is_default=True)

            with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
                result = initiate_payment(order.id, str(buyer.id))

            assert not isinstance(result, ValidationResponse)
            assert result["snap_token"] == "tok-123"
            assert result["redirect_url"].endswith("tok-123")
            # Order stays PENDING; stock untouched
            db_session.refresh(order)
            db_session.refresh(product)
            assert order.status == OrderStatus.PENDING
            assert order.payment_status == "pending"
            assert order.payment_ref.startswith(f"ORDER-{order.id}-")
            assert order.address_id == addr.id
            assert product.stock == 10

    def test_initiate_explicit_address(self, app, db_session):
        with app.app_context():
            seller = self._seller(db_session)
            buyer = self._buyer(db_session)
            product = self._product(db_session, seller, stock=10)
            order = self._pending_order(db_session, buyer, product)
            self._address(db_session, buyer, is_default=True)
            other = Address(user_id=buyer.id, label='Office', recipient_name='B',
                            phone='+6289876543210', address_line='Jl. 2', city='Bandung',
                            province='Jabar', postal_code='40123', is_default=False)
            db_session.add(other); db_session.commit()

            with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
                result = initiate_payment(order.id, str(buyer.id), address_id=other.id)

            assert not isinstance(result, ValidationResponse)
            db_session.refresh(order)
            assert order.address_id == other.id

    def test_initiate_fails_no_default_address(self, app, db_session):
        with app.app_context():
            seller = self._seller(db_session)
            buyer = self._buyer(db_session)
            product = self._product(db_session, seller, stock=10)
            order = self._pending_order(db_session, buyer, product)

            with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
                result = initiate_payment(order.id, str(buyer.id))

            assert isinstance(result, ValidationResponse)
            assert "Default address is not set" in result.message

    def test_initiate_fails_not_pending(self, app, db_session):
        with app.app_context():
            seller = self._seller(db_session)
            buyer = self._buyer(db_session)
            product = self._product(db_session, seller, stock=10)
            self._address(db_session, buyer)
            order = Order(user_id=buyer.id, name='paid order', status=OrderStatus.PAID,
                          subtotal=Decimal('200'), discount_percent=0, discount_amount=0,
                          tax_percent=11, tax_amount=Decimal('22'), total=Decimal('222'))
            db_session.add(order); db_session.commit()

            with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
                result = initiate_payment(order.id, str(buyer.id))

            assert isinstance(result, ValidationResponse)
            assert "Only PENDING orders can be paid" in result.message

    def test_initiate_fails_not_owner(self, app, db_session):
        with app.app_context():
            seller = self._seller(db_session)
            buyer = self._buyer(db_session)
            product = self._product(db_session, seller, stock=10)
            order = self._pending_order(db_session, buyer, product)
            other = self._buyer(db_session)
            self._address(db_session, other)

            with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
                result = initiate_payment(order.id, str(other.id))

            assert isinstance(result, ValidationResponse)
            assert "Unauthorized" in result.message

    def test_initiate_fails_insufficient_stock(self, app, db_session):
        with app.app_context():
            seller = self._seller(db_session)
            buyer = self._buyer(db_session)
            product = self._product(db_session, seller, stock=1)
            order = self._pending_order(db_session, buyer, product, quantity=5)
            self._address(db_session, buyer)

            with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
                result = initiate_payment(order.id, str(buyer.id))

            assert isinstance(result, ValidationResponse)
            assert "Insufficient stock" in result.message
            db_session.refresh(product)
            assert product.stock == 1

    def test_initiate_fails_order_not_found(self, app, db_session):
        with app.app_context():
            with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
                result = initiate_payment(999999, "1")
            assert isinstance(result, ValidationResponse)
            assert "Order not found" in result.message


# =============================================================================
# WEBHOOK NOTIFICATION
# =============================================================================

class TestHandleNotification(_Base):

    def _initiate(self, app, db_session, stock=10, quantity=3):
        seller = self._seller(db_session)
        buyer = self._buyer(db_session)
        product = self._product(db_session, seller, stock=stock)
        order = self._pending_order(db_session, buyer, product, quantity=quantity)
        self._address(db_session, buyer, is_default=True)
        with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
            initiate_payment(order.id, str(buyer.id))
        db_session.refresh(order)
        return order, product

    def _notification(self, app, ref, status="settlement", gross="222", fraud=None):
        server_key = app.config["MIDTRANS_SERVER_KEY"] or ""
        status_code = "200"
        return {
            "order_id": ref,
            "status_code": status_code,
            "gross_amount": gross,
            "signature_key": _make_signature(ref, status_code, gross, server_key),
            "transaction_status": status,
            "fraud_status": fraud,
        }

    def test_settlement_marks_paid_and_deducts_stock(self, app, db_session):
        with app.app_context():
            order, product = self._initiate(app, db_session, stock=10, quantity=3)
            notif = self._notification(app, order.payment_ref, status="settlement")

            result = handle_notification(notif)

            assert result.success is True
            db_session.refresh(order); db_session.refresh(product)
            assert order.status == OrderStatus.PAID
            assert order.payment_status == "settlement"
            assert product.stock == 7  # 10 - 3

    def test_capture_accept_marks_paid(self, app, db_session):
        with app.app_context():
            order, product = self._initiate(app, db_session, stock=10, quantity=2)
            notif = self._notification(app, order.payment_ref, status="capture", fraud="accept")

            result = handle_notification(notif)

            assert result.success is True
            db_session.refresh(order)
            assert order.status == OrderStatus.PAID

    def test_invalid_signature_rejected(self, app, db_session):
        with app.app_context():
            order, product = self._initiate(app, db_session)
            notif = self._notification(app, order.payment_ref)
            notif["signature_key"] = "deadbeef"

            result = handle_notification(notif)

            assert result.success is False
            assert result.status_code == 403
            db_session.refresh(order)
            assert order.status == OrderStatus.PENDING  # unchanged

    def test_duplicate_settlement_is_idempotent(self, app, db_session):
        with app.app_context():
            order, product = self._initiate(app, db_session, stock=10, quantity=3)
            notif = self._notification(app, order.payment_ref, status="settlement")

            handle_notification(notif)   # first -> PAID, stock 7
            result = handle_notification(notif)  # second -> no-op

            assert result.success is True
            db_session.refresh(product)
            assert product.stock == 7  # not double-deducted

    def test_expire_records_status_no_deduction(self, app, db_session):
        with app.app_context():
            order, product = self._initiate(app, db_session, stock=10, quantity=3)
            notif = self._notification(app, order.payment_ref, status="expire")

            result = handle_notification(notif)

            assert result.success is True
            db_session.refresh(order); db_session.refresh(product)
            assert order.status == OrderStatus.PENDING
            assert order.payment_status == "expire"
            assert product.stock == 10  # untouched

    def test_unknown_reference_404(self, app, db_session):
        with app.app_context():
            notif = self._notification(app, "ORDER-999999-1", status="settlement")
            result = handle_notification(notif)
            assert result.success is False
            assert result.status_code == 404


# =============================================================================
# REFUND ON PAID -> CANCELED
# =============================================================================

class TestRefundOnCancel(_Base):

    def _paid_order_via_gateway(self, app, db_session, stock=10, quantity=3):
        seller = self._seller(db_session)
        buyer = self._buyer(db_session)
        product = self._product(db_session, seller, stock=stock)
        order = self._pending_order(db_session, buyer, product, quantity=quantity)
        self._address(db_session, buyer, is_default=True)
        with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
            initiate_payment(order.id, str(buyer.id))
        # simulate settlement
        db_session.refresh(order)
        server_key = app.config["MIDTRANS_SERVER_KEY"] or ""
        notif = {
            "order_id": order.payment_ref, "status_code": "200", "gross_amount": "222",
            "signature_key": _make_signature(order.payment_ref, "200", "222", server_key),
            "transaction_status": "settlement", "fraud_status": None,
        }
        handle_notification(notif)
        db_session.refresh(order); db_session.refresh(product)
        return seller, buyer, product, order

    def test_seller_cancel_refunds_and_restores_stock(self, app, db_session):
        with app.app_context():
            seller, buyer, product, order = self._paid_order_via_gateway(app, db_session, stock=10, quantity=3)
            assert order.status == OrderStatus.PAID
            assert product.stock == 7

            refund_snap = MagicMock()
            with patch('app.services.midtrans_client.get_snap_client', return_value=refund_snap):
                result = update_order(order.id, {"status": "CANCELED"}, str(seller.id), ["SELLER"])

            assert not isinstance(result, ValidationResponse)
            refund_snap.transaction.refund.assert_called_once()
            db_session.refresh(order); db_session.refresh(product)
            assert order.status == OrderStatus.CANCELED
            assert order.payment_status == "refund"
            assert product.stock == 10  # restored

    def test_cancel_aborts_when_gateway_refund_fails(self, app, db_session):
        with app.app_context():
            seller, buyer, product, order = self._paid_order_via_gateway(app, db_session, stock=10, quantity=3)

            failing_snap = MagicMock()
            failing_snap.transaction.refund.side_effect = Exception("gateway down")
            with patch('app.services.midtrans_client.get_snap_client', return_value=failing_snap):
                result = update_order(order.id, {"status": "CANCELED"}, str(seller.id), ["SELLER"])

            assert isinstance(result, ValidationResponse)
            assert result.success is False
            db_session.refresh(order); db_session.refresh(product)
            # Nothing changed: still PAID, stock still deducted
            assert order.status == OrderStatus.PAID
            assert product.stock == 7

    def test_cancel_legacy_order_without_payment_ref_skips_refund(self, app, db_session):
        """A PAID order with no payment_ref (seeded/legacy) cancels with stock restore, no gateway call."""
        with app.app_context():
            seller = self._seller(db_session)
            buyer = self._buyer(db_session)
            product = self._product(db_session, seller, stock=7)
            order = Order(user_id=buyer.id, name='legacy order', status=OrderStatus.PAID,
                          subtotal=Decimal('200'), discount_percent=0, discount_amount=0,
                          tax_percent=11, tax_amount=Decimal('22'), total=Decimal('222'))
            db_session.add(order); db_session.commit()
            oi = Order_item(order_id=order.id, product_id=product.id, quantity=3,
                            compound_price=Decimal('200'))
            db_session.add(oi); db_session.commit()

            snap = MagicMock()
            with patch('app.services.midtrans_client.get_snap_client', return_value=snap):
                result = update_order(order.id, {"status": "CANCELED"}, str(seller.id), ["SELLER"])

            assert not isinstance(result, ValidationResponse)
            snap.transaction.refund.assert_not_called()
            db_session.refresh(order); db_session.refresh(product)
            assert order.status == OrderStatus.CANCELED
            assert product.stock == 10  # 7 + 3 restored


# =============================================================================
# ROUTE INTEGRATION
# =============================================================================

class TestPaymentRoute(_Base):

    def test_initiate_route_success(self, app, db_session, client):
        seller = self._seller(db_session)
        product = self._product(db_session, seller, stock=10)
        buyer = self._buyer(db_session)
        self._address(db_session, buyer, is_default=True)
        order = self._pending_order(db_session, buyer, product, quantity=2)

        token = create_access_token(identity=str(buyer.id), additional_claims={'roles': ['BUYER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
            resp = client.post('/api/v1/payment/', headers=headers, json={'order_id': order.id})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['snap_token'] == 'tok-123'
        assert data['data']['status'] == 'PENDING'  # not PAID yet
        db_session.refresh(product)
        assert product.stock == 10  # no deduction on initiate

    def test_initiate_route_seller_forbidden(self, app, db_session, client):
        seller = self._seller(db_session)
        token = create_access_token(identity=str(seller.id), additional_claims={'roles': ['SELLER']})
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        resp = client.post('/api/v1/payment/', headers=headers, json={'order_id': 1})
        assert resp.status_code == 403

    def test_notification_route_settlement(self, app, db_session, client):
        seller = self._seller(db_session)
        product = self._product(db_session, seller, stock=10)
        buyer = self._buyer(db_session)
        self._address(db_session, buyer, is_default=True)
        order = self._pending_order(db_session, buyer, product, quantity=2)

        with patch('app.services.payment_service.get_snap_client', return_value=_mock_snap()):
            initiate_payment(order.id, str(buyer.id))
        db_session.refresh(order)

        server_key = app.config["MIDTRANS_SERVER_KEY"] or ""
        payload = {
            "order_id": order.payment_ref, "status_code": "200", "gross_amount": "222",
            "signature_key": _make_signature(order.payment_ref, "200", "222", server_key),
            "transaction_status": "settlement",
        }
        resp = client.post('/api/v1/payment/notification', json=payload)
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        db_session.refresh(order); db_session.refresh(product)
        assert order.status == OrderStatus.PAID
        assert product.stock == 8
