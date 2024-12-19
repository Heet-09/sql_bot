#   https://python.langchain.com/docs/tutorials/rag/
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
import os
from langchain import hub
from typing_extensions import TypedDict
from typing_extensions import Annotated
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from IPython.display import Image, display  
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver


os.environ["GROQ_API_KEY"] = "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"
os.environ["LANGCHAIN_API_KEY"] = "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"
llm = ChatGroq(model="llama3-8b-8192")
query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]

db = SQLDatabase.from_uri("mysql+pymysql://heetjain:heetjain@localhost:3306/fin")


def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}

# print(write_query({"question": "How many companies are there?"}))

def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDataBaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}

print(execute_query({"query": "SELECT COUNT(DISTINCT Name) FROM financial_data"}))


def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}

# memory = MemorySaver()

# graph_builder = StateGraph(State).add_sequence(
#     [write_query, execute_query, generate_answer]
# )
# graph_builder.add_edge(START, "write_query")
# graph = graph_builder.compile()

# # Now that we're using persistence, we need to specify a thread ID
# # so that we can continue the run after review.
# config = {"configurable": {"thread_id": "1"}}

# graph = graph_builder.compile(checkpointer=memory, interrupt_before=["execute_query"])

# display(Image(graph.get_graph().draw_mermaid_png()))

# for step in graph.stream(
#     {"question": "How many employees are there?"},
#     config,
#     stream_mode="updates",
# ):
#     print(step)

# try:
#     user_approval = input("Do you want to go to execute query? (yes/no): ")
# except Exception:
#     user_approval = "no"

# if user_approval.lower() == "yes":
#     # If approved, continue the graph execution
#     for step in graph.stream(None, config, stream_mode="updates"):
#         print(step)
# else:
#     print("Operation cancelled by user.")
 
