from fastapi import APIRouter
from fastapi import Form

from fastapi.responses import Response

from twilio.twiml.messaging_response import MessagingResponse

from app.ai import process_message

from app.db.database import SessionLocal

from app.db.crud import (
    create_user,
    get_user,
    save_transaction,
    get_summary,
    get_transactions
)

from app.state import pending_confirmations

router = APIRouter()

# CONFIRM WORDS
CONFIRM_WORDS = [
    "yes",
    "y",
    "1",
    "yeah",
    "yup",
    "sure",
    "confirm",
    "ok",
    "okay"
]

# CANCEL WORDS
CANCEL_WORDS = [
    "no",
    "n",
    "2",
    "nah",
    "nope",
    "cancel",
    "stop"
]


@router.post("/webhook")
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...)
):

    db = SessionLocal()

    message = Body.strip()

    lower_message = message.lower().strip()

    phone = From

    twilio_response = MessagingResponse()

    # CHECK USER
    user = get_user(db, phone)

    # FIRST TIME USER
    if not user:

        if "|" not in message:

            twilio_response.message(
                "Welcome to FinMate AI 🚀\n\n"
                "Setup format:\n"
                "Name | Currency\n\n"
                "Example:\n"
                "Sakthi | ₹"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        parts = message.split("|")

        name = parts[0].strip()

        currency = parts[1].strip()

        create_user(
            db,
            phone,
            name,
            currency
        )

        twilio_response.message(
            f"Setup completed ✅\n\n"
            f"Welcome {name}!\n\n"
            f"You can now track expenses like:\n"
            f"'Spent 120 for biriyani'"
        )

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # HANDLE PENDING CONFIRMATIONS
    if phone in pending_confirmations:

        pending = pending_confirmations[phone]

        # CONFIRM
        if lower_message in CONFIRM_WORDS:

            save_transaction(
                db,
                phone,
                pending["amount"],
                pending["category"],
                pending["description"]
            )

            del pending_confirmations[phone]

            twilio_response.message(
                f"Added {user.currency}{pending['amount']} "
                f"under {pending['category']} ✅"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        # CANCEL
        if lower_message in CANCEL_WORDS:

            del pending_confirmations[phone]

            twilio_response.message(
                "Okay 👍 Transaction cancelled."
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

    # AI PROCESSING
    result = process_message(message)

    print("FINAL RESULT:")
    print(result)

    result_type = result.get("type")

    # CHAT FLOW
    if result_type == "chat":

        twilio_response.message(
            result.get(
                "reply",
                "Hello 👋"
            )
        )

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # OUT OF SCOPE
    if result_type == "out_of_scope":

        twilio_response.message(
            result.get(
                "reply",
                "I'm focused on finance tracking 😊"
            )
        )

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # CONFIRMATION FLOW
    if result_type == "confirm":

        pending_confirmations[phone] = {
            "amount": result.get("amount", 0),
            "category": result.get(
                "category",
                "Other"
            ),
            "description": result.get(
                "description",
                "Expense"
            )
        }

        twilio_response.message(
            result.get(
                "reply",
                "Please confirm this transaction."
            )
            + "\n\n"
            + "1️⃣ Confirm\n"
            + "2️⃣ Cancel"
        )

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # SUMMARY FLOW
    if result_type == "summary":

        period = result.get(
            "period",
            "today"
        )

        category = result.get(
            "category",
            None
        )

        summary = get_summary(
            db,
            phone,
            period,
            category
        )

        if not summary:

            twilio_response.message(
                "No transactions found 😊"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        total = 0

        lines = []

        for cat, amount in summary:

            total += amount

            lines.append(
                f"{cat} → {user.currency}{amount}"
            )

        title_map = {
            "today": "Today's Spending 💸",
            "this_week": "This Week's Spending 💸",
            "this_month": "This Month's Spending 💸",
            "last_month": "Last Month's Spending 💸"
        }

        response_text = (
            title_map.get(
                period,
                "Summary 💸"
            )
            + "\n\n"
            + "\n".join(lines)
            + f"\n\nTotal → {user.currency}{total}"
        )

        twilio_response.message(response_text)

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # TRANSACTIONS FLOW
    if result_type == "transactions":

        period = result.get(
            "period",
            "today"
        )

        transactions = get_transactions(
            db,
            phone,
            period
        )

        if not transactions:

            twilio_response.message(
                "No transactions found 😊"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        lines = []

        total = 0

        for tx in transactions:

            total += tx.amount

            lines.append(
                f"• {tx.description} → "
                f"{user.currency}{tx.amount}"
            )

        response_text = (
            f"Transactions ({period}) 💸\n\n"
            + "\n".join(lines[:15])
            + f"\n\nTotal → {user.currency}{total}"
        )

        twilio_response.message(response_text)

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # EXPENSE FLOW
    if result_type in ["expense", "expense_list"]:

        transactions = result.get(
            "transactions",
            []
        )

        if not transactions:

            twilio_response.message(
                "I couldn't identify the expenses clearly 😊"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        saved_messages = []

        for transaction in transactions:

            amount = transaction.get("amount", 0)

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

            # LARGE AMOUNT CONFIRMATION
            if amount >= 10000:

                pending_confirmations[phone] = {
                    "amount": amount,
                    "category": category,
                    "description": description
                }

                twilio_response.message(
                    f"Large expense detected ⚠️\n\n"
                    f"{user.currency}{amount} under "
                    f"{category}\n\n"
                    f"1️⃣ Confirm\n"
                    f"2️⃣ Cancel"
                )

                return Response(
                    content=str(twilio_response),
                    media_type="application/xml"
                )

            # SAVE TRANSACTION
            save_transaction(
                db,
                phone,
                amount,
                category,
                description
            )

            saved_messages.append(
                f"• {user.currency}{amount} → {category}"
            )

        # NO VALID TRANSACTIONS
        if not saved_messages:

            twilio_response.message(
                "I couldn't identify valid expenses 😊"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        response_text = (
            "Transactions added ✅\n\n"
            + "\n".join(saved_messages)
        )

        twilio_response.message(response_text)

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # FALLBACK
    twilio_response.message(
        "Sorry, I couldn't understand that 😊"
    )

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )