from sqlalchemy.orm import Session

from sqlalchemy import func

from datetime import datetime
from datetime import timedelta

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


def get_summary(
    db: Session,
    phone: str,
    period: str,
    category: str = None
):

    now = datetime.utcnow()

    start_date = now

    # PERIOD LOGIC
    if period == "today":

        start_date = datetime(
            now.year,
            now.month,
            now.day
        )

    elif period == "this_week":

        start_date = now - timedelta(
            days=now.weekday()
        )

    elif period == "this_month":

        start_date = datetime(
            now.year,
            now.month,
            1
        )

    elif period == "last_month":

        first_day_this_month = datetime(
            now.year,
            now.month,
            1
        )

        last_day_last_month = (
            first_day_this_month
            - timedelta(days=1)
        )

        start_date = datetime(
            last_day_last_month.year,
            last_day_last_month.month,
            1
        )

        now = datetime(
            last_day_last_month.year,
            last_day_last_month.month,
            last_day_last_month.day,
            23,
            59,
            59
        )

    query = db.query(
        Transaction.category,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.phone == phone,
        Transaction.created_at >= start_date,
        Transaction.created_at <= now
    )

    # CATEGORY FILTER
    if category:

        query = query.filter(
            Transaction.category.ilike(category)
        )

    results = query.group_by(
        Transaction.category
    ).all()

    return results

def get_transactions(
    db: Session,
    phone: str,
    period: str
):

    now = datetime.utcnow()

    start_date = now

    # PERIOD LOGIC
    if period == "today":

        start_date = datetime(
            now.year,
            now.month,
            now.day
        )

    elif period == "this_week":

        start_date = now - timedelta(
            days=now.weekday()
        )

    elif period == "this_month":

        start_date = datetime(
            now.year,
            now.month,
            1
        )

    elif period == "last_month":

        first_day_this_month = datetime(
            now.year,
            now.month,
            1
        )

        last_day_last_month = (
            first_day_this_month
            - timedelta(days=1)
        )

        start_date = datetime(
            last_day_last_month.year,
            last_day_last_month.month,
            1
        )

        now = datetime(
            last_day_last_month.year,
            last_day_last_month.month,
            last_day_last_month.day,
            23,
            59,
            59
        )

    results = db.query(
        Transaction
    ).filter(
        Transaction.phone == phone,
        Transaction.created_at >= start_date,
        Transaction.created_at <= now
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return results