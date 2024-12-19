# Maintains memory and answers evry question but not from db
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import os
from langchain_groq import ChatGroq

# Initialize memory for context tracking
memory = ConversationBufferMemory()
os.environ["GROQ_API_KEY"] = "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"
os.environ["LANGCHAIN_API_KEY"] = "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"
llm = ChatGroq(model="llama3-8b-8192")

# Initialize the chat model and conversation chain
chatbot = ConversationChain(
    llm=llm,  # Replace with your API setup
    memory=memory
)

# Chat loop
print("Chatbot: Hello! Ask me anything. Type 'exit' to end the chat.")
while True:
    # Take user input
    user_input = input("You: ")
    
    # Exit condition
    if user_input.lower() == "exit":
        print("Chatbot: Goodbye!")
        break
    
    # Get the bot's response
    response = chatbot.run(user_input)
    
    # Print the bot's reply
    print(f"Chatbot: {response}")
