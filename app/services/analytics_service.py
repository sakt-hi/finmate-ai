from app.db.crud import (
    get_summary,
    get_transactions
)


def build_summary_response(
    db,
    phone,
    currency,
    period,
    category=None
):

    summary = get_summary(
        db,
        phone,
        period,
        category
    )

    if not summary:

        return "No transactions found 😊"

    total = 0

    lines = []

    for cat, amount in summary:

        total += amount

        lines.append(
            f"{cat} → {currency}{amount}"
        )

    return (
        f"Summary ({period}) 💸\n\n"
        + "\n".join(lines)
        + f"\n\nTotal → {currency}{total}"
    )


def build_transaction_response(
    db,
    phone,
    currency,
    period
):

    transactions = get_transactions(
        db,
        phone,
        period
    )

    if not transactions:

        return "No transactions found 😊"

    total = 0

    lines = []

    for tx in transactions[:15]:

        total += tx.amount

        lines.append(
            f"• {tx.description} → "
            f"{currency}{tx.amount}"
        )

    return (
        f"Transactions ({period}) 💸\n\n"
        + "\n".join(lines)
        + f"\n\nTotal → {currency}{total}"
    )