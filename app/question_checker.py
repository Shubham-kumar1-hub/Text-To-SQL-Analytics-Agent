"""
Check whether the user's question needs clarification. (Ambiguity detection)
"""

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


def check_question(question):
    """
    Decide whether a question is clear enough to turn into SQL.

    Returns a dictionary with:
    - is_clear: True or False
    - clarification: a question for the user when clarification is needed
    """

    # General rules only. No hints written for specific test questions.
    prompt = f"""
You decide whether an ecommerce analytics question is ready to be turned into SQL.

Mark a question AMBIGUOUS only when two or more reasonable readings would give
materially different answers, and the question does not say which one it means.
For example, "popular" could mean most units sold, most revenue, or most reviews.

Do NOT mark a question ambiguous just because:
- it has no time period (assume all available data is wanted)
- it can be read in slightly different ways that give the same or almost the same answer

Do not invent extra filters or distinctions.

Reference notes about the data:
- orders.status is one of: placed, shipped, delivered, cancelled.
- payments.payment_status is one of: paid, failed, refunded.

Return exactly one of these formats:

CLEAR

AMBIGUOUS: followed by one short clarification question.

User question:
{question}
"""

    response = llm.invoke(prompt)
    decision = response.content.strip()

    # If the LLM says AMBIGUOUS, return its clarification question
    if decision.upper().startswith("AMBIGUOUS:"):
        clarification = decision.split(":", 1)[1].strip()

        return {
            "is_clear": False,
            "clarification": clarification,
        }

    # Otherwise treat the question as clear
    return {
        "is_clear": True,
        "clarification": "",
    }


if __name__ == "__main__":
    # Quick sanity checks only. These will NOT be used in the real eval set.
    test_questions = [
        "How many products are in the Laptops category?",   # expect clear
        "What is the average rating given in reviews?",     # expect clear
        "How many orders were cancelled?",                  # expect clear
        "List the brands from Japan.",                      # expect clear
        "Who are our top customers?",                       # expect ambiguous
        "Which products are doing well?",                   # expect ambiguous
    ]

    for question in test_questions:
        result = check_question(question)

        print(f"\nQuestion: {question}")
        print("Is clear:", result["is_clear"])

        if result["clarification"]:
            print("Clarification:", result["clarification"])