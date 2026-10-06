"""
Admin dashboard aggregation service.

Pure business logic for the ADMIN/SUPERADMIN dashboard (spec 4.12). Computes
platform KPIs and chart series with SQL-side aggregation instead of pulling full
lists and counting in Python. All figures ignore soft-deleted rows unless noted.

Returns a plain dict; the route layer wraps it in the standard envelope.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, cast, case, Date

from app.extensions import db
from app.models import Product, Order
from app.models.order_model import OrderStatus
from app.models.user_model import User, UserRole
from app.models.seller_product_model import SellerProduct
from app.models.product_model import ProductStatus


# Order statuses that represent realized revenue (GMV).
_REVENUE_STATUSES = (OrderStatus.PAID, OrderStatus.COMPLETED)


def _kpis():
    """Headline counters shown as KPI cards."""
    total_users = (
        db.session.query(func.count(User.id))
        .filter(User.deleted_at.is_(None))
        .scalar() or 0
    )

    total_listings = (
        db.session.query(func.count(SellerProduct.id))
        .filter(SellerProduct.deleted_at.is_(None))
        .scalar() or 0
    )

    pending_listings = (
        db.session.query(func.count(SellerProduct.id))
        .filter(
            SellerProduct.deleted_at.is_(None),
            SellerProduct.status == ProductStatus.PENDING,
        )
        .scalar() or 0
    )

    # "Orders today" — created since UTC midnight.
    start_of_day = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    orders_today = (
        db.session.query(func.count(Order.id))
        .filter(Order.deleted_at.is_(None), Order.created_at >= start_of_day)
        .scalar() or 0
    )

    # GMV — sum of totals across revenue-realizing orders.
    gmv = (
        db.session.query(func.coalesce(func.sum(Order.total), 0))
        .filter(
            Order.deleted_at.is_(None),
            Order.status.in_(_REVENUE_STATUSES),
        )
        .scalar() or 0
    )

    return {
        "total_users": int(total_users),
        "total_listings": int(total_listings),
        "pending_listings": int(pending_listings),
        "orders_today": int(orders_today),
        "gmv": float(gmv),
    }


def _orders_revenue_series(days):
    """Line chart: orders count + revenue per day for the last `days` days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day_col = cast(Order.created_at, Date)

    rows = (
        db.session.query(
            day_col.label("day"),
            func.count(Order.id).label("orders"),
            func.coalesce(
                func.sum(
                    case(
                        (Order.status.in_(_REVENUE_STATUSES), Order.total),
                        else_=0,
                    )
                ),
                0,
            ).label("revenue"),
        )
        .filter(Order.deleted_at.is_(None), Order.created_at >= since)
        .group_by(day_col)
        .order_by(day_col.asc())
        .all()
    )

    return [
        {
            "date": r.day.isoformat() if r.day else None,
            "orders": int(r.orders),
            "revenue": float(r.revenue),
        }
        for r in rows
    ]


def _orders_by_status():
    """Bar chart: order count grouped by business status."""
    rows = (
        db.session.query(Order.status, func.count(Order.id))
        .filter(Order.deleted_at.is_(None))
        .group_by(Order.status)
        .all()
    )
    counts = {status.value: 0 for status in OrderStatus}
    for status, count in rows:
        if status is not None:
            counts[status.value] = int(count)
    return [{"status": k, "count": v} for k, v in counts.items()]


def _users_by_role():
    """Pie chart: user count per role (roles is an ARRAY, so a user can appear in several)."""
    counts = {role.value: 0 for role in UserRole}
    users = (
        db.session.query(User.roles)
        .filter(User.deleted_at.is_(None))
        .all()
    )
    for (roles,) in users:
        for role in (roles or []):
            key = role.value if hasattr(role, "value") else str(role)
            if key in counts:
                counts[key] += 1
    return [{"role": k, "count": v} for k, v in counts.items()]


def get_admin_dashboard(days=30):
    """
    Aggregate all admin dashboard data in one pass.

    Args:
        days: window for the time-series chart (7 / 30 / 90 typically).

    Returns:
        dict with `kpis` and `charts` (orders_revenue, orders_by_status, users_by_role).
    """
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 30
    days = max(1, min(days, 365))

    return {
        "kpis": _kpis(),
        "charts": {
            "orders_revenue": _orders_revenue_series(days),
            "orders_by_status": _orders_by_status(),
            "users_by_role": _users_by_role(),
        },
        "range_days": days,
    }
