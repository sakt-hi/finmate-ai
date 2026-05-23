VALID_CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "Entertainment",
    "Groceries",
    "Health",
    "Other"
]


def validate_amount(amount):

    try:

        amount = float(amount)

        return amount > 0

    except:

        return False


def normalize_category(category):

    if not category:
        return "Other"

    category = category.title()

    if category not in VALID_CATEGORIES:
        return "Other"

    return category