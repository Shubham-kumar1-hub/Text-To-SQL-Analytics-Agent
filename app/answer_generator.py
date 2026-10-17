
"""
Turns SQL query results into a clear plain English answer.
"""

import json

from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)

def generate_answer(question, sql_query, query_result):
    """ Creating a concise answer from the SQL query results. """

    # Avoid asking the LLM to explain an empty result set.
    if not query_result["rows"]:
        return (
            "I couldn't find any records that match your question. "
            "Try different wording or broader filters."
        )

    # default=str handles database values such as Decimal and dates.
    result_rows = json.dumps(query_result["rows"], default=str)

    prompt = f"""
You are a helpful ecommerce analytics assistant.

Answer the user's question using only the database results below.
Do not invent facts that are not present in the results.
You can only read data. Never say or imply that any data was changed, updated, deleted, or created.
Never write INSERT, UPDATE, DELETE, DROP, or any other data-changing SQL in your answer.
If the results do not do what the user asked, say so plainly instead of claiming success.
Do not add or assume a currency symbol unless the database results explicitly include one.
Keep the answer concise amd easy for a non-technical person to understand.

User question:
{question}

SQL used:
{sql_query}

Database results:
{result_rows}
"""

    response = llm.invoke(prompt)
    answer = response.content.strip()

    # Warn the user if the database results were cut off at the row limit
    if query_result.get("truncated"):
        answer += (
            f"\n\nNote: only the first {len(query_result['rows'])} rows are shown "
            "because results are limited."
        )

    return answer