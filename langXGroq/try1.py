import os
from langchain_groq import ChatGroq

# Set the API key directly
os.environ["GROQ_API_KEY"] = "your-api-key-here"

# Initialize the ChatGroq instance
llm = ChatGroq(model="llama3-8b-8192")

# Example usage (optional)
response = llm.chat("What is the capital of France?")
print(response)
