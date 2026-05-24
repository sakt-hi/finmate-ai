import re

from fastapi import APIRouter
from fastapi import Form

from fastapi.responses import Response

from twilio.twiml.messaging_response import MessagingResponse

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


def send_reply(
    twilio_response,
    message
):

    twilio_response.message(message)

    print("\n========== TWILIO RESPONSE ==========")
    print(str(twilio_response))
    print("=====================================\n")

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )


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

    # ==========================================
    # FIRST TIME USER
    # ==========================================

    if not user:

        if "|" not in message:

            return send_reply(
                twilio_response,
                "Welcome to FinMate AI 🚀\n\n"
                "Setup format:\n"
                "Name | Currency\n\n"
                "Example:\n"
                "Sakthi | ₹"
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

        return send_reply(
            twilio_response,
            f"Setup completed ✅\n\n"
            f"Welcome {name}!"
        )

    # ==========================================
    # CONFIRMATION FLOW
    # ==========================================

    if phone in pending_confirmations:

        pending = pending_confirmations[phone]

        if lower_message in CONFIRM_WORDS:

            response_text = handle_transactions(
                db,
                phone,
                user.currency,
                [pending]
            )

            del pending_confirmations[phone]

            return send_reply(
                twilio_response,
                response_text
            )

        if lower_message in CANCEL_WORDS:

            del pending_confirmations[phone]

            return send_reply(
                twilio_response,
                "Okay 👍 Transaction cancelled."
            )

    # ==========================================
    # GREETINGS
    # ==========================================

    greetings = [
        "hi",
        "hello",
        "hey",
        "hii",
        "yo"
    ]

    if lower_message in greetings:

        return send_reply(
            twilio_response,
            f"Hello {user.name} 👋\n\n"
            f"I'm FinMate AI — your personal finance assistant.\n\n"
            f"I can help you:\n"
            f"• Track expenses\n"
            f"• View summaries\n"
            f"• Manage budgets\n"
            f"• Edit transactions\n"
            f"• Delete transactions\n\n"
            f"Examples:\n"
            f"• Spent 120 for biriyani\n"
            f"• Show recent transactions\n"
            f"• Delete #F001\n"
            f"• Edit #F001 to 150"
        )

    # ==========================================
    # DIRECT DELETE DETECTION
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

                return send_reply(
                    twilio_response,
                    "Transaction not found 😊"
                )

            response_text = (
                "🗑️ Deleted Transactions\n\n"
            )

            for tx in deleted_transactions:

                response_text += (
                    f"#{tx['short_id']} • "
                    f"{user.currency}{tx['amount']} • "
                    f"{tx['category']} • "
                    f"{tx['description']}\n"
                )

            return send_reply(
                twilio_response,
                response_text
            )

    # ==========================================
    # DIRECT EDIT DETECTION
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

            if not transaction:

                return send_reply(
                    twilio_response,
                    "Transaction not found 😊"
                )

            return send_reply(
                twilio_response,
                f"✏️ Transaction Updated\n\n"
                f"#{transaction.short_id}\n"
                f"{user.currency}{transaction.amount} • "
                f"{transaction.category} • "
                f"{transaction.description}"
            )

    # ==========================================
    # AI PROCESSING
    # ==========================================

    result = process_message(message)

    result_type = result.get("type")

    # ==========================================
    # CHAT
    # ==========================================

    if result_type == "chat":

        return send_reply(
            twilio_response,
            result.get("reply", "Hello 👋")
        )

    # ==========================================
    # SUMMARY
    # ==========================================

    if result_type == "summary":

        response_text = build_summary_response(
            db,
            phone,
            user.currency,
            result.get("period", "today"),
            result.get("category")
        )

        return send_reply(
            twilio_response,
            response_text
        )

    # ==========================================
    # TRANSACTIONS
    # ==========================================

    if result_type in [
        "transactions",
        "transaction_history"
    ]:

        response_text = build_transaction_response(
            db,
            phone,
            user.currency,
            result.get("period", "today")
        )

        return send_reply(
            twilio_response,
            response_text
        )

    # ==========================================
    # BUDGET
    # ==========================================

    if result_type == "budget":

        set_budget(
            db,
            phone,
            result.get("category"),
            result.get("amount")
        )

        return send_reply(
            twilio_response,
            f"Budget set for "
            f"{result.get('category')} ✅"
        )

    # ==========================================
    # EXPENSES
    # ==========================================

    if result_type in [
        "expense",
        "expense_list"
    ]:

        minimum_words = len(
            lower_message.split()
        )

        if minimum_words <= 1:

            return send_reply(
                twilio_response,
                "Please provide a valid transaction 😊\n\n"
                "Examples:\n"
                "• Spent 120 for tea\n"
                "• 50 for bus ticket"
            )

        transactions = result.get(
            "transactions",
            []
        )

        valid_transactions = []

        for tx in transactions:

            amount = tx.get(
                "amount",
                0
            )

            description = tx.get(
                "description"
            )

            if not isinstance(
                amount,
                (int, float)
            ):
                continue

            if amount <= 0:
                continue

            if amount > 1000000000:
                continue

            if not description:
                continue

            valid_transactions.append(tx)

        if not valid_transactions:

            return send_reply(
                twilio_response,
                "I couldn't identify a valid transaction 😊"
            )

        # LARGE TRANSACTION

        large_transaction = next(
            (
                tx for tx in valid_transactions
                if tx.get("amount", 0) >= 10000
            ),
            None
        )

        if large_transaction:

            pending_confirmations[phone] = large_transaction

            return send_reply(
                twilio_response,
                f"Large expense detected ⚠️\n\n"
                f"{user.currency}"
                f"{large_transaction['amount']} • "
                f"{large_transaction['category']}\n\n"
                f"1️⃣ Confirm\n"
                f"2️⃣ Cancel"
            )

        # SAVE TRANSACTIONS

        response_text = handle_transactions(
            db,
            phone,
            user.currency,
            valid_transactions
        )

        return send_reply(
            twilio_response,
            response_text
        )

    # ==========================================
    # FALLBACK
    # ==========================================

    return send_reply(
        twilio_response,
        "Sorry, I couldn't understand that 😊"
    )