"""
LangGraph workflow for the Text-to-SQL analytics agent.
"""

from typing import TypedDict

from langgraph.graph import START, END, StateGraph


from app.sql_executor import execute_sql
from app.sql_generator import generate_sql
from app.answer_generator import generate_answer


class AgentState(TypedDict):
    """ Data passed between LangGraph nodes."""

    question: str
    sql: str
    result: dict
    answer: str

def generate_sql_node(state):
    """Generate Validatd SQL from the user's question."""

    sql_query = generate_sql(state["question"])

    return {"sql": sql_query}

def execute_sql_node(state):
    """Execute the generated SQL safely"""

    query_result = execute_sql(state["sql"])

    return {"result": query_result}

def generate_answer_node(state):
    """ Generate a plain English answer from the SQL results"""

    plain_english_answer = generate_answer(
        question=state["question"],
        sql_query=state["sql"],
        query_result=state["result"],
    )

    return {"answer": plain_english_answer}


# Building the LangGraph workflow

workflow = StateGraph(AgentState)

workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)
workflow.add_node("generate_answer", generate_answer_node)

workflow.add_edge(START, "generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_edge("execute_sql", "generate_answer")
workflow.add_edge("generate_answer", END)

# Compiling the graph into a callable function

agent_graph = workflow.compile()

# def run_agent(question):
#     """ Turn a plain English question into a SQL and execute it. """

#     # Generating SQL from the question
#     sql_query = generate_sql(question)

#     # Executing the generated SQL
#     query_result = execute_sql(sql_query)

#     plain_english_answer= generate_answer(question, sql_query, query_result)

#     return {
#         "question": question,
#         "sql": sql_query,
#         "result": query_result,
#         "answer": plain_english_answer,
#     }

def run_agent(question):
    """Running the complete Langgraph Text-To-Sql workflow"""

    return agent_graph.invoke({"question": question})

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