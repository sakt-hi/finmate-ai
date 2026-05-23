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
        save_transaction(
            db,
            phone,
            amount,
            category,
            description
        )

        saved_messages.append(
            f"• {currency}{amount} → {category}"
        )

    # NOTHING SAVED
    if not saved_messages:

        return (
            "No valid transactions found 😊"
        )

    return (
        "Transactions added ✅\n\n"
        + "\n".join(saved_messages)
    )