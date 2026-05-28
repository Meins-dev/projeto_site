import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean, inspect, text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nshop.db")
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)
Base = declarative_base()


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    category = Column(String)
    emoji = Column(String)
    sold = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    reviews = Column(Integer, default=0)
    stock = Column(Integer, default=0)
    tags = Column(JSON, default=list)


class Coupon(Base):
    __tablename__ = "coupons"
    code = Column(String, primary_key=True)
    discount = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    min_value = Column(Float, nullable=False)
    label = Column(String)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    cpf = Column(String)
    address = Column(Text)
    is_admin = Column(Boolean, default=False)
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(String, unique=True, nullable=False)
    refresh_token = Column(String, unique=True, nullable=False)
    access_expires_at = Column(DateTime)
    refresh_expires_at = Column(DateTime)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="sessions")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_name = Column(String)
    customer_email = Column(String)
    customer_cpf = Column(String)
    customer_address = Column(Text)
    customer_zip = Column(String)
    subtotal = Column(Float)
    discount = Column(Float)
    shipping = Column(Float)
    shipping_days = Column(Integer)
    total = Column(Float)
    coupon_code = Column(String, ForeignKey("coupons.code"), nullable=True)
    payment = Column(String)
    pix_code = Column(Text)
    pix_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer)
    name = Column(String)
    qty = Column(Integer)
    price = Column(Float)
    subtotal = Column(Float)
    order = relationship("Order", back_populates="items")


def init_db():
    """Create DB file, missing columns, and tables if they don't exist."""
    inspector = inspect(ENGINE)
    if "users" in inspector.get_table_names():
        existing_columns = [col["name"] for col in inspector.get_columns("users")]
        if "is_admin" not in existing_columns:
            with ENGINE.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
    Base.metadata.create_all(ENGINE)


def migrate_from_memory(products, coupons, users, orders):
    """Insert data from in-memory structures into the DB if tables are empty.
    Designed to be idempotent: won't duplicate existing rows with same PKs.
    """
    session = SessionLocal()
    try:
        # Products
        if session.query(Product).first() is None:
            for p in products:
                prod = Product(
                    id=p.get("id"),
                    name=p.get("name"),
                    description=p.get("description"),
                    price=p.get("price", 0.0),
                    original_price=p.get("original_price"),
                    category=p.get("category"),
                    emoji=p.get("emoji"),
                    sold=p.get("sold", 0),
                    rating=p.get("rating", 0.0),
                    reviews=p.get("reviews", 0),
                    stock=p.get("stock", 0),
                    tags=p.get("tags", []),
                )
                session.add(prod)

        # Coupons
        if session.query(Coupon).first() is None:
            for code, c in coupons.items():
                cp = Coupon(
                    code=code,
                    discount=c.get("discount", 0),
                    type=c.get("type", "percent"),
                    min_value=c.get("min_value", 0),
                    label=c.get("label"),
                )
                session.add(cp)

        # Users
        if session.query(User).first() is None and users:
            for index, u in enumerate(users):
                user = User(
                    name=u.get("name"),
                    email=u.get("email"),
                    password_hash=u.get("password_hash", ""),
                    cpf=u.get("cpf", ""),
                    address=u.get("address", ""),
                    is_admin=(index == 0),
                )
                session.add(user)

        # Orders
        if session.query(Order).first() is None and orders:
            for o in orders:
                ord_obj = Order(
                    id=o.get("id"),
                    customer_name=o.get("customer", {}).get("name"),
                    customer_email=o.get("customer", {}).get("email"),
                    customer_cpf=o.get("customer", {}).get("cpf"),
                    customer_address=o.get("customer", {}).get("address"),
                    customer_zip=o.get("customer", {}).get("zip"),
                    subtotal=o.get("subtotal", 0.0),
                    discount=o.get("discount", 0.0),
                    shipping=o.get("shipping", 0.0),
                    shipping_days=o.get("shipping_days", 0),
                    total=o.get("total", 0.0),
                    coupon_code=(o.get("coupon") or {}).get("code") if o.get("coupon") else None,
                    payment=o.get("payment"),
                    pix_code=o.get("pix_code"),
                    pix_expires_at=datetime.fromisoformat(o.get("pix_expires_at")) if o.get("pix_expires_at") else None,
                    created_at=datetime.fromisoformat(o.get("created_at")) if o.get("created_at") else None,
                    status=o.get("status"),
                )
                session.add(ord_obj)
                for it in o.get("items_detail", []):
                    item = OrderItem(
                        order=ord_obj,
                        product_id=it.get("id"),
                        name=it.get("name"),
                        qty=it.get("qty"),
                        price=it.get("price"),
                        subtotal=it.get("subtotal"),
                    )
                    session.add(item)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
