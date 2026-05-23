from sqlalchemy.orm import Session

from sqlalchemy import func

from datetime import datetime
from datetime import timedelta

from app.db.models import User
from app.db.models import Transaction
from app.db.models import Budget


def create_user(
    db,
    phone,
    name,
    currency
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
    db,
    phone
):

    return db.query(User).filter(
        User.phone == phone
    ).first()


def save_transaction(
    db,
    phone,
    amount,
    category,
    description
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


def set_budget(
    db,
    phone,
    category,
    amount
):

    budget = Budget(
        phone=phone,
        category=category,
        monthly_limit=amount
    )

    db.add(budget)

    db.commit()

    db.refresh(budget)

    return budget


def get_summary(
    db,
    phone,
    period,
    category=None
):

    now = datetime.utcnow()

    start_date = datetime(
        now.year,
        now.month,
        1
    )

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

    query = db.query(
        Transaction.category,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.phone == phone,
        Transaction.created_at >= start_date
    )

    if category:

        query = query.filter(
            Transaction.category.ilike(category)
        )

    return query.group_by(
        Transaction.category
    ).all()


def get_transactions(
    db,
    phone,
    period
):

    now = datetime.utcnow()

    start_date = datetime(
        now.year,
        now.month,
        1
    )

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

    return db.query(Transaction).filter(
        Transaction.phone == phone,
        Transaction.created_at >= start_date
    ).order_by(
        Transaction.created_at.desc()
    ).all()