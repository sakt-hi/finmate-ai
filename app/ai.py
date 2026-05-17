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
    Personal finance and expense tracking assistant.

    USER MESSAGE:
    "{message}"

    TASK:
    Analyze the message carefully.

    POSSIBLE RESPONSE TYPES:

    1. chat

    Example:
    {{
        "type": "chat",
        "reply": "Hello 👋"
    }}

    2. expense

    Single expense example:
    {{
        "type": "expense",
        "transactions": [
            {{
                "amount": 120,
                "category": "Food",
                "description": "Biriyani"
            }}
        ]
    }}

    3. expense_list

    Multiple expenses example:
    "Spent 25 for tea and 100 for groceries"

    Return:
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

    4. confirm

    For:
    - unusually large amounts
    - doubtful transactions

    Example:
    {{
        "type": "confirm",
        "amount": 50000,
        "category": "Shopping",
        "description": "Shopping",
        "reply": "Do you want me to record ₹50000 under Shopping?"
    }}

    5. out_of_scope

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
    - No code
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
                        "You are a strict JSON API. "
                        "Always return valid JSON only."
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

    except Exception as e:

        print("JSON ERROR:", e)

        return {
            "type": "chat",
            "reply": "Sorry, I couldn't understand that."
        }