"""
LangGraph workflow for the Text-to-SQL analytics agent.
"""

from typing import TypedDict

from langgraph.graph import START, END, StateGraph


from app.sql_executor import execute_sql
from app.sql_generator import generate_sql
from app.answer_generator import generate_answer
from app.question_checker import check_question

# The agent gets at most two SQL- generation attempts.
MAX_SQL_ATTEMPTS = 2


class AgentState(TypedDict):
    """ Data passed between LangGraph nodes."""

    question: str
    is_clear: bool
    clarification: str
    sql: str
    result: dict
    answer: str
    error: str
    attempts: int

def check_question_node(state):
    """ Check whether the user must clarify their question first."""

    question_check = check_question(state["question"])

    return {
        "is_clear": question_check["is_clear"],
        "clarification": question_check["clarification"],
    }

def decide_after_question_check(state):
    """ Route clear question to SQL generation, otherwise ask for clarification."""

    if state["is_clear"]:
        return "generate_sql"

    return "generate_clarification"

def generate_clarification_node(state):
    """Return the clarification question without generating or running SQL."""

    return {"answer": state["clarification"]}


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


workflow.add_node("check_question", check_question_node)
workflow.add_node("generate_clarification", generate_clarification_node)
workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)
workflow.add_node("generate_answer", generate_answer_node)
workflow.add_node("generate_error_answer", generate_error_answer_node)


workflow.add_edge(START, "check_question")

workflow.add_conditional_edges(
    "check_question",
    decide_after_question_check,
    {
        "generate_sql": "generate_sql",
        "generate_clarification": "generate_clarification",
    },
)

workflow.add_edge("generate_clarification", END)
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
    #user_question = "Which 5 products have the highest price?"
    #user_question = "Show me products named Product That Does Not Exist"
    user_question = "What are the best products?"   # testing the ambiguity path.

    agent_response = run_agent(user_question)

    print("Question:")
    print(agent_response["question"])

    if "sql" in agent_response:
        print("\nGenerated SQL:")
        print(agent_response["sql"])

    if "result" in agent_response:
        print("\nResults:")
        for row in agent_response["result"]["rows"]:
            print(row)

    print("\nAgent Response:")
    print(agent_response["answer"])

    print("\nSQL attempts:")
    print(agent_response["attempts"])