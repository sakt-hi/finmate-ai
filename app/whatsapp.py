from fastapi import APIRouter
from fastapi import Form

from fastapi.responses import Response

from twilio.twiml.messaging_response import MessagingResponse

from app.ai import process_message

from app.db.database import SessionLocal

from app.db.crud import (
    create_user,
    get_user,
    set_budget
)

from app.services.transaction_service import (
    handle_transactions
)

from app.services.analytics_service import (
    build_summary_response,
    build_transaction_response
)

from app.state import pending_confirmations

router = APIRouter()

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
            f"Welcome {name}!"
        )

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # CONFIRMATION FLOW
    if phone in pending_confirmations:

        pending = pending_confirmations[phone]

        if lower_message in CONFIRM_WORDS:

            handle_transactions(
                db,
                phone,
                user.currency,
                [pending]
            )

            del pending_confirmations[phone]

            twilio_response.message(
                f"Added {user.currency}{pending['amount']} under {pending['category']} ✅"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        if lower_message in CANCEL_WORDS:

            del pending_confirmations[phone]

            twilio_response.message(
                "Okay 👍 Transaction cancelled."
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )
    GREETINGS = [
        "hi",
        "hello",
        "hey",
        "hii",
        "yo"
    ]

    if lower_message in GREETINGS:

        twilio_response.message(
            f"Hello {user.name} 👋\n\n"
            f"I'm FinMate AI — your personal finance assistant.\n\n"
            f"I can help you:\n"
            f"• Track expenses\n"
            f"• View summaries\n"
            f"• Check transactions\n"
            f"• Manage budgets\n\n"
            f"Example:\n"
            f"'Spent 120 for biriyani'"
        )

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    result = process_message(message)

    result_type = result.get("type")

    # CHAT
    if result_type == "chat":

        twilio_response.message(
            result.get("reply", "Hello 👋")
        )

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # SUMMARY
    if result_type == "summary":

        response_text = build_summary_response(
            db,
            phone,
            user.currency,
            result.get("period", "today"),
            result.get("category")
        )

        twilio_response.message(response_text)

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # TRANSACTIONS
    if result_type == "transactions":

        response_text = build_transaction_response(
            db,
            phone,
            user.currency,
            result.get("period", "today")
        )

        twilio_response.message(response_text)

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # BUDGET
    if result_type == "budget":

        set_budget(
            db,
            phone,
            result.get("category"),
            result.get("amount")
        )

        twilio_response.message(
            f"Budget set for {result.get('category')} ✅"
        )

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    # EXPENSES
    if result_type in ["expense", "expense_list"]:

        transactions = result.get(
            "transactions",
            []
        )

        # FILTER VALID TRANSACTIONS

        valid_transactions = []

        for tx in transactions:

            try:

                amount = float(tx.get("amount", 0))

                if amount > 0:

                    tx["amount"] = amount

                    valid_transactions.append(tx)

            except:

                continue

        transactions = valid_transactions

        if not transactions:

            twilio_response.message(
                "Please send a valid expense 😊\n\n"
                "Example:\n"
                "Spent 120 for tea"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        large_transaction = next(
            (
                tx for tx in transactions
                if tx.get("amount", 0) >= 10000
            ),
            None
        )

        if large_transaction:

            pending_confirmations[phone] = large_transaction

            twilio_response.message(
                f"Large expense detected ⚠️\n\n"
                f"{user.currency}{large_transaction['amount']} under {large_transaction['category']}\n\n"
                f"1️⃣ Confirm\n"
                f"2️⃣ Cancel"
            )

            return Response(
                content=str(twilio_response),
                media_type="application/xml"
            )

        response_text = handle_transactions(
            db,
            phone,
            user.currency,
            transactions
        )

        twilio_response.message(response_text)

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )

    twilio_response.message(
        "Sorry, I couldn't understand that 😊"
    )

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )