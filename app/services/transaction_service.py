from app.db.crud import save_transaction


def handle_transactions(
    db,
    phone,
    currency,
    transactions
):

    saved_messages = []

    for transaction in transactions:

        amount = transaction.get(
            "amount",
            0
        )

        category = transaction.get(
            "category",
            "Other"
        )

        description = transaction.get(
            "description",
            "Expense"
        )

        # INVALID AMOUNT
        if amount <= 0:
            continue

        # SAVE
        saved_transaction = save_transaction(
            db,
            phone,
            amount,
            category,
            description
        )

        # BUILD RESPONSE
        saved_messages.append(
            f"✅ Added Transaction\n\n"
            f"{saved_transaction.short_id}\n"
            f"{currency}{saved_transaction.amount} • "
            f"{saved_transaction.category} • "
            f"{saved_transaction.description}"
        )

    # NOTHING SAVED
    if not saved_messages:

        return (
            "No valid transactions found 😊"
        )

    return "\n\n".join(saved_messages)
