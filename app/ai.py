import os
import json
import requests

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def process_message(message):

    prompt = f"""
    You are FinMate AI.

    ROLE:
    Personal finance assistant.

    USER MESSAGE:
    "{message}"

    POSSIBLE RESPONSE TYPES:

    1. chat

    Example:
    {{
        "type": "chat",
        "reply": "Hello 👋"
    }}

    2. expense

    Example:
    {{
        "type": "expense",
        "transactions": [
            {{
                "amount": 120,
                "category": "Food",
                "description": "Tea"
            }}
        ]
    }}

    3. expense_list

    Example:
    {{
        "type": "expense_list",
        "transactions": [
            {{
                "amount": 25,
                "category": "Food",
                "description": "Tea"
            }},
            {{
                "amount": 100,
                "category": "Groceries",
                "description": "Groceries"
            }}
        ]
    }}

    4. summary

    For grouped spending totals.

    Examples:
    - summary today
    - summary this week
    - how much did i spend this month

    Return:
    {
        "type": "summary",
        "period": "today"
    }

    Optional category filter:
    {
        "type": "summary",
        "period": "this_month",
        "category": "Food"
    }

    5. transactions

    For listing individual transactions.

    Examples:
    - all transactions today
    - show my expenses this week
    - list transactions this month

    Return:
    {
        "type": "transactions",
        "period": "today"
    }

    6. confirm

    Example:
    {{
        "type": "confirm",
        "amount": 50000,
        "category": "Shopping",
        "description": "Shopping",
        "reply": "Do you want me to record ₹50000 under Shopping?"
    }}

    7. out_of_scope

    Example:
    {{
        "type": "out_of_scope",
        "reply": "I'm focused on finance tracking 😊"
    }}

    IMPORTANT RULES:
    - Convert word amounts into numbers
    - Return ONLY valid JSON
    - No markdown
    - No explanations
    """

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict JSON API."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_object"
            }
        }
    )

    data = response.json()

    content = data["choices"][0]["message"]["content"]

    print("AI RESPONSE:")
    print(content)

    try:

        return json.loads(content)

    except Exception:

        return {
            "type": "chat",
            "reply": "Sorry 😊"
        }