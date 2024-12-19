# generates query but not being executed correctly due to the inclusion of the explanatory text within the SQL query.

from langchain.utilities.sql_database import SQLDatabase
from langchain.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_groq import ChatGroq
import os

# Environment variables
os.environ["GROQ_API_KEY"] = "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"
os.environ["LANGCHAIN_API_KEY"] = "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"

# Initialize the LLM
llm = ChatGroq(model="llama3-8b-8192")

# Database connection
db = SQLDatabase.from_uri("mysql+pymysql://heetjain:heetjain@localhost:3306/fin")

# Query Execution Tool
execute_query_tool = QuerySQLDataBaseTool(db=db)

# Functions
def write_query(question):
    """Generate SQL query for the given question."""
    prompt = f"""
    Use SQL to answer the following question based on the database schema provided:
    {db.get_table_info()}
    Question: {question}
    """
    response = llm.invoke(prompt)
    print(f"Generated SQL Query: {response.content.strip()}")
    return response.content.strip()

def execute_query(query):
    """Execute the SQL query."""
    print(f"Executing Query: {query}")
    result = execute_query_tool.invoke(query)
    print(f"Query Result: {result}")
    return result

def generate_answer(question, query, result):
    """Generate an answer using the SQL query and result."""
    prompt = f"""
    Given the following question, SQL query, and result, answer the question.
    Question: {question}
    SQL Query: {query}
    Result: {result}
    """
    response = llm.invoke(prompt)
    return response.content.strip()

# Example
question = "How many companies are there?"
sql_query = write_query(question)
result = execute_query(sql_query)
answer = generate_answer(question, sql_query, result)

print(f"Final Answer: {answer}")
