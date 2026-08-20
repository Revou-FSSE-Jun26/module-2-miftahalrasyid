import logging
from app import create_app
from app.extensions import db
from app.models import User, UserRole, AuthProvider, Product, Category, Order, Order_item
from app.models.order_model import OrderStatus
from app.models.category_items_model import category_items

logging.basicConfig(level=logging.INFO)


def seed_database():
    app = create_app()
    with app.app_context():
        logging.info("Starting database seeding...")

        # --- CATEGORIES ---
        if not Category.query.first():
            categories = [
                Category(id=1, name="livestyle"),
                Category(id=2, name="gaming"),
                Category(id=3, name="apple"),
                Category(id=4, name="komputer"),
            ]
            db.session.add_all(categories)
            db.session.flush()
            logging.info("Categories seeded.")

        # --- USERS ---
        if not User.query.first():
            users = [
                User(
                    id=1, email="budi@gmail.com", age=27, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="2159cea8efdb8491058156ee571bcc0ce09c896dc591e4a7f840d59c95be771e",
                    username="budi", roles=[UserRole.BUYER]
                ),
                User(
                    id=2, email="arini@gmail.com", age=27, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2",
                    username="arini", roles=[UserRole.BUYER, UserRole.SELLER]
                ),
                User(
                    id=3, email="husni@gmail.com", age=27, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="e10adc3949ba59abbe56e057f20f883e28b4b4dbd33b58c4886d22698e7341ea",
                    username="husni", roles=[UserRole.BUYER]
                ),
                User(
                    id=4, email="angel@gmail.com", age=21, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="6514970c5ed4c2eb312bc1bb799477cbb8c616c8a798a1a28b175680f738a299",
                    username="angel", roles=[UserRole.BUYER],
                    deleted_at="2026-08-15 17:13:06.407376+07"
                ),
                User(
                    id=5, email="justin@gmail.com", age=28, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="a3f0956da3cfb843d8e7ee5d867bf0d4bbdd6955587d235678ab68e13ce67846",
                    username="justin", roles=[UserRole.BUYER]
                ),
                User(
                    id=10, email="mike@gmail.com", age=18, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="1fb0ab1378099448c8800dd96f25409ec10e9ea802c0bcadbf8d322b3e9f94ec",
                    username="mike", roles=[UserRole.BUYER]
                ),
                User(
                    id=12, email="adriana@gmail.com", age=35, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="f96354dd9b0cb206ba156f52be94e4cdfebad293e834fd8276643942d9e6b83f",
                    username="adriana", roles=[UserRole.BUYER]
                ),
                User(
                    id=14, email="funnyclown1112@gmail.com", age=35, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="5ab1de808ce6c7194bf7de510c5f082cf7a979fb246355db118fbce769538b0e",
                    username="funnyclown1112", roles=[UserRole.SUPERADMIN]
                ),
                User(
                    id=15, email="budiarie@gmail.com", age=70, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="375465ccbe9e4c51234b1431066b6c9297a04efe191da70b2b4fabcdacab3245",
                    username="budiarie", roles=[UserRole.BUYER]
                ),
                User(
                    id=16, email="rafaelalun@gmail.com", age=50, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH,
                    provider_key="8470cef960b11e01639514a918479325358725499d546c250152b2fb97307619",
                    username="rafaelalun", roles=[UserRole.BUYER]
                ),
            ]
            db.session.add_all(users)
            db.session.flush()
            logging.info("Users seeded.")

        # --- PRODUCTS ---
        if not Product.query.first():
            products = [
                Product(id=1, name="laptop asus", stock=50, brand="asus",
                        description="laptop dengan batre cepat rusak", price=0.00, user_id=2),
                Product(id=2, name="laptop lenovo", stock=150, brand="lenovo",
                        description="terkenal dengan laptop gaming murahnya", price=0.00, user_id=2),
                Product(id=3, name="laptop surface", stock=30, brand="microsoft",
                        description="laptop dari sang pembuat os dengan harga lebih mahal dari yang lain", price=0.00, user_id=2),
                Product(id=4, name="laptop macbook", stock=50, brand="apple",
                        description="laptop dengan prioritas keamanan yang tinggi", price=0.00, user_id=2),
            ]
            db.session.add_all(products)
            db.session.flush()
            logging.info("Products seeded.")

        # --- CATEGORY_ITEMS (junction table) ---
        existing = db.session.execute(db.select(category_items)).first()
        if not existing:
            db.session.execute(category_items.insert().values([
                {"category_id": 1, "product_id": 1},
                {"category_id": 2, "product_id": 2},
                {"category_id": 3, "product_id": 4},
                {"category_id": 4, "product_id": 4},
            ]))
            db.session.flush()
            logging.info("Category items seeded.")

        # --- ORDERS ---
        if not Order.query.first():
            orders = [
                Order(id=1, user_id=1, name="inv-4229435", status=OrderStatus.PENDING, total=1.00),
                Order(id=2, user_id=2, name="inv-3245435", status=OrderStatus.PENDING, total=1.00),
                Order(id=3, user_id=3, name="inv-4374343", status=OrderStatus.PENDING, total=1.00),
                Order(id=4, user_id=2, name="inv-2938673", status=OrderStatus.PENDING, total=1.00),
            ]
            db.session.add_all(orders)
            db.session.flush()
            logging.info("Orders seeded.")

        # --- ORDER_ITEMS ---
        if not Order_item.query.first():
            order_items = [
                Order_item(id=1, product_id=1, order_id=4, quantity=1, compound_price=0.00),
                Order_item(id=2, product_id=2, order_id=2, quantity=1, compound_price=0.00),
                Order_item(id=3, product_id=2, order_id=3, quantity=1, compound_price=0.00),
                Order_item(id=4, product_id=1, order_id=3, quantity=1, compound_price=0.00),
            ]
            db.session.add_all(order_items)
            db.session.flush()
            logging.info("Order items seeded.")

        # --- COMMIT ---
        try:
            db.session.commit()
            logging.info("Database seeding completed successfully!")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Seeding failed: {str(e)}")


if __name__ == "__main__":
    seed_database()
