from fastapi import APIRouter
from fastapi import Form

from fastapi.responses import Response

from twilio.twiml.messaging_response import MessagingResponse

from app.ai import process_message

from app.db.database import SessionLocal

from app.db.crud import (
    create_user,
    get_user,
    save_transaction
)

from app.state import pending_confirmations

router = APIRouter()

# CONFIRMATION WORDS
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

    # CHECK EXISTING USER
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

    # HANDLE PENDING CONFIRMATION
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

    # PROCESS MESSAGE USING AI
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

    # EXPENSE FLOW
    # SINGLE OR MULTIPLE EXPENSES
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

            # SKIP INVALID
            if amount <= 0:
                continue

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

        # NOTHING VALID
        if not saved_messages:

            twilio_response.message(
                "I couldn't identify valid expenses 😊"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        # SUCCESS RESPONSE
        response_text = (
            "Transactions added ✅\n\n"
            + "\n".join(saved_messages)
        )

        twilio_response.message(response_text)

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )