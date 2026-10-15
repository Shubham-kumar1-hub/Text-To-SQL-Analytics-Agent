"""
LangGraph workflow for the Text-to-SQL analytics agent.
"""

from typing import TypedDict

from langgraph.graph import START, END, StateGraph


from app.sql_executor import execute_sql
from app.sql_generator import generate_sql
from app.answer_generator import generate_answer

# The agent gets at most two SQL- generation attempts.
MAX_SQL_ATTEMPTS = 2


class AgentState(TypedDict):
    """ Data passed between LangGraph nodes."""

    question: str
    sql: str
    result: dict
    answer: str
    error: str
    attempts: int

def generate_sql_node(state):
    """Generate Validatd SQL using an error message if this is a retry."""

    sql_query = generate_sql(
        question=state["question"],
        error_message=state.get("error"),
    )

    return {
        "sql": sql_query,
        "error": "",
        "attempts": state.get("attempts", 0) + 1,
    }

def execute_sql_node(state):
    """Execute the generated SQL safely and capture any errors for a retry."""

    try:

        query_result = execute_sql(state["sql"])

        return {
            "result": query_result,
            "error": "",
        }
    except Exception as error:
        # It will make sure that the agent do not crash immediately and first sends the error back to the SQL Generator.
        return {"error": str(error)}

def generate_answer_node(state):
    """ Generate a plain English answer from the SQL results"""

    plain_english_answer = generate_answer(
        question=state["question"],
        sql_query=state["sql"],
        query_result=state["result"],
    )

    return {"answer": plain_english_answer}

def generate_error_answer_node(state):
    """ Returns  clear message after every allowed SQL attempt has failed."""

    return {
        "answer": (
            "I could not create a valid query for this question after "
            f"{state['attempts']} attempts. Database error: {state['error']}"
        )
    }

def decide_next_setps(state):
    """ Decide whether to retry SQL generation or return an error answer."""

    if not state.get("error"):
        return "generate_answer"

    if state.get("attempts", 0) < MAX_SQL_ATTEMPTS:
        return "generate_sql"

    return "generate_error_answer"


# Building the LangGraph workflow

workflow = StateGraph(AgentState)

workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)
workflow.add_node("generate_answer", generate_answer_node)
workflow.add_node("generate_error_answer", generate_error_answer_node)


workflow.add_edge(START, "generate_sql")
workflow.add_edge("generate_sql", "execute_sql")

# After execution, we decide wheteher to retry SQL generation or generate an error answer.
workflow.add_conditional_edges(
    "execute_sql",
    decide_next_setps,
    {
        "generate_sql": "generate_sql",
        "generate_answer": "generate_answer",
        "generate_error_answer": "generate_error_answer",
    },
)

workflow.add_edge("generate_answer", END)
workflow.add_edge("generate_error_answer", END)

# Compiling the graph into a callable function

agent_graph = workflow.compile()

# def run_agent(question):
#     """ Turn a plain English question into a SQL and execute it. """

#     # Generating SQL from the question
#     sql_query = generate_sql(question)

#     # Executing the generated SQL
#     query_result = execute_sql(sql_query)

#     # Generating a plain English answer
#     plain_english_answer= generate_answer(question, sql_query, query_result)

#     return {
#         "question": question,
#         "sql": sql_query,
#         "result": query_result,
#         "answer": plain_english_answer,
#     }

def run_agent(question):
    """Running the complete Langgraph Text-To-Sql workflow"""

    return agent_graph.invoke(
        {
            "question": question,
            "attempts": 0,
        }
    )

if __name__ == "__main__":
    user_question = "Which 5 products have the highest price?"

    agent_response = run_agent(user_question)

    print("Question:")
    print(agent_response["question"])

    print("\nGenerated SQL:")
    print(agent_response["sql"])

    if "result" in agent_response:
        print("\nResults:")
        for row in agent_response["result"]["rows"]:
            print(row)

    print("\nPlain-English Answer:")
    print(agent_response["answer"])

    print("\nSQL attempts:")
    print(agent_response["attempts"])