"""
A simple end to end Text-to-SQL analytics agent.
"""

from app.sql_executor import execute_sql
from app.sql_generator import generate_sql
from app.answer_generator import generate_answer


def run_agent(question):
    """ Turn a plain English question into a SQL and execute it. """

    # Generating SQL from the question
    sql_query = generate_sql(question)

    # Executing the generated SQL
    query_result = execute_sql(sql_query)

    plain_english_answer= generate_answer(question, sql_query, query_result)

    return {
        "question": question,
        "sql": sql_query,
        "result": query_result,
        "answer": plain_english_answer,
    }

if __name__ == "__main__":
    # testing the complete flow with a sample question
    user_question = "Which 5 products have the highest price?"

    agent_response = run_agent(user_question)

    print("Question:")
    print(agent_response["question"])

    print("\nGenerated SQL:")
    print(agent_response["sql"])

    print("\nResults:")
    for row in agent_response["result"]["rows"]:
        print(row)

    print("\nPlain English Answer:")
    print(agent_response["answer"])