from app import db
import datetime as dt

order_items = db.Table(
    "order_items",
    db.Column("order_id",db.Integer,db.ForeignKey("orders.id",ondelete="CASCADE"),primary_key=True),
    db.Column("product_id",db.Integer,db.ForeignKey("products.id",ondelete="CASCADE"),primary_key=True),
    db.Column("created_at",db.DateTime(timezone=True),default=lambda:dt.datetime.now(dt.timezone.utc))
)

