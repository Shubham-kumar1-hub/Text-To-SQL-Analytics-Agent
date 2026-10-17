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

A question is AMBIGUOUS only when its core measure or ranking criterion is
undefined. This happens when it uses a vague quality word, such as a word like
"popular", with no metric that says how to measure it.
Several different metrics could be meant, and they would give different answers.

A question is CLEAR when it names its metric, or when the metric is obvious
from the question (a count, a total, an average, the most or least common value).

Scope rules:
- If the question does not mention a filter, there is no filter. Use all rows
  in the relevant table.
- Never ask whether to restrict the data to a subset (for example by status,
  by whether something was sold, or by active or inactive items).
  If the user wanted a subset, they would have said so.
- Never ask about time periods. If none is given, use all available data.
- Do not invent extra filters, distinctions, or definitions.

Example of a CLEAR question: "How many addresses are in each state?"
Nobody needs to choose anything to answer it.

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