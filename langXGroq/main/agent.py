from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain import hub
from langgraph.checkpoint.memory import MemorySaver
import os

# Set environment variables
os.environ["GROQ_API_KEY"] = "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"
os.environ["LANGCHAIN_API_KEY"] = "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"

# Initialize LLM and database
llm = ChatGroq(model="llama3-8b-8192")
db = SQLDatabase.from_uri("mysql+pymysql://heetjain:heetjain@localhost:3306/fin")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

# Load the prompt template
prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
assert len(prompt_template.messages) == 1
prompt_template.messages[0].pretty_print()

# Format the system message
system_message = prompt_template.format(dialect="SQL", top_k=5)

# Initialize memory
memory = MemorySaver()

# Create the agent with memory
agent_executor = create_react_agent(llm, tools, state_modifier=system_message, checkpointer=memory)

# User question
question = "Who has the highest current Price?"

# Thread configuration for memory (optional, enables thread-based memory management)
config = {"configurable": {"thread_id": "1"}}

# Stream the response
for step in agent_executor.stream(
    {"messages": [{"role": "user", "content": question}]},
    config=config,
    stream_mode="values",
):
    step["messages"][-1].pretty_print()

# Test additional interaction to demonstrate memory
follow_up = "Can you tell me their details?"

for step in agent_executor.stream(
    {"messages": [{"role": "user", "content": follow_up}]},
    config=config,
    stream_mode="values",
):
    step["messages"][-1].pretty_print()
