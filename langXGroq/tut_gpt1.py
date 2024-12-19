from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
import os
from langchain import hub
from typing_extensions import TypedDict
from typing_extensions import Annotated

# Set environment variables
os.environ["GROQ_API_KEY"] = "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"
os.environ["LANGCHAIN_API_KEY"] = "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"

# Initialize LLM and SQL prompt
llm = ChatGroq(model="llama3-8b-8192")
query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

# Ensure the template is fetched
if not query_prompt_template:
    raise ValueError("Query prompt template could not be fetched.")

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]

# Connect to the database
db = SQLDatabase.from_uri("mysql+pymysql://heetjain:heetjain@localhost:3306/fin")

def write_query(state: State):
    """Generate SQL query to fetch information."""
    try:
        # Fetch schema and dialect
        dialect = db.dialect
        print("dia",dialect)
        table_info = db.get_table_info()
        
        # Debugging outputs
        # print("Dialect:", dialect)
        # print("Table Info:", table_info)

        # Generate query prompt
        prompt = query_prompt_template.invoke(
            {
                "dialect": dialect,
                "top_k": 10,
                "table_info": table_info,
                "input": state["question"],
            }
        )

        # Debugging output for the prompt
        # print("Generated Prompt:", prompt)

        # Generate SQL query using LLM
        structured_llm = llm.with_structured_output(QueryOutput)
        result = structured_llm.invoke(prompt)

        # Debugging output for the result
        # print("LLM Result:", result)

        return {"query": result["query"]}
    except Exception as e:
        print("Error:", e)
        raise

# Test the function
state = {"question": "How many companies are there?"}
output = write_query(state)
print("Generated Query:", output)
