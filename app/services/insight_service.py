def generate_basic_insights(summary):

    if not summary:

        return []

    insights = []

    highest = max(
        summary,
        key=lambda x: x[1]
    )

    insights.append(
        f"Highest spending: "
        f"{highest[0]}"
    )

    return insights