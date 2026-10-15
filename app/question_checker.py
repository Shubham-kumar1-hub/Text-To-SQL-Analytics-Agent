"""
Check wheter the user's question needs clarification. (Ambiguity detection)
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

    prompt = f"""
You help decide whether an ecommerce analytics question is ready for SQL.

A question is ambiguous when it does not specify an important metric,
time period, comparison, or meaning. For example, "What are the best 
products?" is ambiguous because "best" could mean highest sales,
highest profit, highest rating, or something else.

Return exactly one of these formats:


CLEAR

AMBIGUOUS: followed by one short clarification question.

User question:
{question}
"""

    response = llm.invoke(prompt)
    decision = response.content.strip()

    if decision.upper().startswith("AMBIGUOUS:"):
        clarification = decision.split(":", 1)[1].strip()

        return {
            "is_clear": False,
            "clarification": clarification,
        }

    return {
        "is_clear": True,
        "clarification": "",
    }


if __name__ == "__main__":
    test_questions = [
        "Which 5 products have the highest price?",
        "What are the best products?",
    ]

    for question in test_questions:
        result = check_question(question)

        print(f"\nQuestion: {question}")
        print("Is clear:", result["is_clear"])

        if result["clarification"]:
            print("clarification:", result["clarification"])