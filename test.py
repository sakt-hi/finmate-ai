from app.ai import process_message

from app.db.database import SessionLocal

from app.db.crud import (
    create_user,
    get_user,
    set_budget,
    delete_transactions,
    edit_transaction_amount
)

from app.services.transaction_service import (
    handle_transactions
)

from app.services.analytics_service import (
    build_summary_response,
    build_transaction_response
)

import re


phone = "local-test-user"

db = SessionLocal()

user = get_user(db, phone)

if not user:

    create_user(
        db,
        phone,
        "Sakthi",
        "₹"
    )

    user = get_user(db, phone)


print("\n==============================")
print("FinMate AI Terminal Testing")
print("==============================\n")


while True:

    message = input("You: ")

    lower_message = message.lower().strip()

    # EXIT

    if lower_message in ["exit", "quit"]:

        print("\nExiting...\n")

        break

    # ==========================================
    # DELETE
    # ==========================================

    delete_keywords = [
        "delete",
        "remove"
    ]

    if any(
        word in lower_message
        for word in delete_keywords
    ):

        detected_ids = [

            tx_id.replace("#", "")

            for tx_id in re.findall(
                r'#?[A-Za-z]{1,2}\d{3}',
                message.upper()
            )
        ]

        if detected_ids:

            deleted_transactions = delete_transactions(
                db,
                detected_ids
            )

            if not deleted_transactions:

                print("\nBot: Transaction not found 😊\n")

            else:

                print("\nBot: 🗑️ Deleted Transactions\n")

                for tx in deleted_transactions:

                    print(
                        f"#{tx['short_id']} • "
                        f"{user.currency}{tx['amount']} • "
                        f"{tx['category']} • "
                        f"{tx['description']}"
                    )

                print()

            continue

    # ==========================================
    # EDIT
    # ==========================================

    edit_keywords = [
        "edit",
        "change",
        "update",
        "modify"
    ]

    if any(
        word in lower_message
        for word in edit_keywords
    ):

        detected_ids = [

            tx_id.replace("#", "")

            for tx_id in re.findall(
                r'#?[A-Za-z]{1,2}\d{3}',
                message.upper()
            )
        ]

        detected_amounts = re.findall(
            r'\d+',
            message
        )

        if detected_ids and detected_amounts:

            short_id = detected_ids[0]

            amount = float(
                detected_amounts[-1]
            )

            transaction = edit_transaction_amount(
                db,
                short_id,
                amount
            )

            if transaction:

                print(
                    f"\nBot: ✏️ Transaction Updated\n"
                )

                print(
                    f"#{transaction.short_id}"
                )

                print(
                    f"{user.currency}{transaction.amount} • "
                    f"{transaction.category} • "
                    f"{transaction.description}\n"
                )

            else:

                print(
                    "\nBot: Transaction not found 😊\n"
                )

            continue

    # ==========================================
    # AI PROCESSING
    # ==========================================

    result = process_message(message)

    result_type = result.get("type")

    # CHAT

    if result_type == "chat":

        print(
            f"\nBot: {result.get('reply')}\n"
        )

        continue

    # SUMMARY

    if result_type == "summary":

        response = build_summary_response(
            db,
            phone,
            user.currency,
            result.get("period", "today"),
            result.get("category")
        )

        print(f"\nBot:\n{response}\n")

        continue

    # TRANSACTIONS

    if result_type in [
        "transactions",
        "transaction_history"
    ]:

        response = build_transaction_response(
            db,
            phone,
            user.currency,
            result.get("period", "today")
        )

        print(f"\nBot:\n{response}\n")

        continue

    # BUDGET

    if result_type == "budget":

        set_budget(
            db,
            phone,
            result.get("category"),
            result.get("amount")
        )

        print(
            f"\nBot: Budget set for "
            f"{result.get('category')} ✅\n"
        )

        continue

    # EXPENSES

    if result_type in [
        "expense",
        "expense_list"
    ]:

        transactions = result.get(
            "transactions",
            []
        )

        response = handle_transactions(
            db,
            phone,
            user.currency,
            transactions
        )

        print(f"\nBot:\n{response}\n")

        continue

    print(
        "\nBot: Sorry, I couldn't understand that 😊\n"
    )