from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime, os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quickdine.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Restaurant(Base):
    __tablename__ = "restaurants"
    id            = Column(String, primary_key=True)          # e.g. "resto_abc123"
    restaurant_name = Column(String, nullable=False)
    owner_name    = Column(String, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone         = Column(String, default="")
    logo_url      = Column(String, default="")
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)


class MenuItem(Base):
    __tablename__ = "menu_items"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(String, nullable=False)
    name          = Column(String, nullable=False)
    description   = Column(Text, default="")
    image_url     = Column(String, default="")
    category      = Column(String, default="General")
    price         = Column(Float, nullable=False)
    is_available  = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(String, nullable=False)
    customer_name = Column(String, nullable=False)
    table_number  = Column(String, default="")
    ordered_items = Column(JSON, nullable=False)   # list of {id, name, price, qty}
    total_amount  = Column(Float, nullable=False)
    status        = Column(String, default="Pending")  # Pending/Preparing/Ready/Served
    timestamp     = Column(DateTime, default=datetime.datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
