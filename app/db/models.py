from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import DateTime

from datetime import datetime

from app.db.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    phone = Column(String, unique=True)

    name = Column(String)

    currency = Column(String)


class Transaction(Base):

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    phone = Column(String)

    amount = Column(Float)

    category = Column(String)

    description = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )