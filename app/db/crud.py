from sqlalchemy.orm import Session

from app.db.models import User
from app.db.models import Transaction


def create_user(
    db: Session,
    phone: str,
    name: str,
    currency: str
):

    user = User(
        phone=phone,
        name=name,
        currency=currency
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user


def get_user(
    db: Session,
    phone: str
):

    return db.query(User).filter(
        User.phone == phone
    ).first()


def save_transaction(
    db: Session,
    phone: str,
    amount: float,
    category: str,
    description: str
):

    transaction = Transaction(
        phone=phone,
        amount=amount,
        category=category,
        description=description
    )

    db.add(transaction)

    db.commit()

    db.refresh(transaction)

    return transaction