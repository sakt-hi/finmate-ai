from sqlalchemy.orm import Session

from sqlalchemy import func

from datetime import datetime
from datetime import timedelta

from app.db.models import User
from app.db.models import Transaction
from app.db.models import Budget

import uuid

CATEGORY_PREFIX = {

    "Food": "F",

    "Transportation": "T",

    "Shopping": "S",

    "Entertainment": "E",

    "Medical": "M",

    "Groceries": "G",

    "Bills": "B",

    "Travel": "TR",

    "Stationery": "ST",

    "Miscellaneous": "O",

    "Other": "O"
}

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

    prefix = CATEGORY_PREFIX.get(
        category,
        "O"
    )

    # GET LAST CATEGORY TRANSACTION

    last_transaction = db.query(Transaction).filter(
        Transaction.short_id.like(f"{prefix}%")
    ).order_by(
        Transaction.id.desc()
    ).first()

    next_number = 1

    if last_transaction:

        try:

            last_number = int(
                last_transaction.short_id.replace(
                    prefix,
                    ""
                )
            )

            next_number = last_number + 1

        except:
            pass

    short_id = f"{prefix}{next_number:03d}"

    transaction = Transaction(

        transaction_id=f"TXN-{uuid.uuid4().hex[:6].upper()}",
        short_id=short_id,
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


def get_recent_transactions(
    db,
    phone,
    limit=5
):

    return db.query(Transaction).filter(
        Transaction.phone == phone
    ).order_by(
        Transaction.id.desc()
    ).limit(limit).all()

def delete_transactions(
    db,
    short_ids
):

    deleted_transactions = []

    for short_id in short_ids:

        transaction = db.query(Transaction).filter(
            Transaction.short_id == short_id.upper()
        ).first()

        if transaction:

            deleted_transactions.append({
                "short_id": transaction.short_id,
                "amount": transaction.amount,
                "category": transaction.category,
                "description": transaction.description
            })

            db.delete(transaction)

    db.commit()

    return deleted_transactions

def edit_transaction_amount(
    db,
    short_id,
    amount
):

    transaction = db.query(Transaction).filter(
        Transaction.short_id == short_id.upper()
    ).first()

    if not transaction:
        return None

    transaction.amount = amount

    db.commit()

    db.refresh(transaction)

    return transaction