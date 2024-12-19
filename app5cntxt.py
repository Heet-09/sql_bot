import streamlit as st
import pymysql
import json
from decimal import Decimal
from groq import Groq

# Add contextual memory for follow-up queries
contextual_memory = {}

# Initialize memory context
memory_context = "Sample memory content for demonstration."

mc=''

# Groq API Key
GROQ_API_KEY = "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"

# Function to connect to the database
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="heetjain",
        password="heetjain",
        db="fin",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor  # Returns results as dictionaries
    )

# Function to convert Decimal objects to JSON-serializable types
def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Or str(obj) if you prefer
    elif isinstance(obj, dict):
        return {key: convert_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    else:
        return obj

# Function to fetch the database schema
def get_database_schema():
    schema = {}
    target_tables = ["financial_data"]  # Add other table names as needed

    connection = get_connection()
    with connection.cursor() as cursor:
        for table_name in target_tables:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            schema[table_name] = [
                {
                    "Field": column["Field"],
                    "Type": column["Type"],
                    "Null": column["Null"],
                    "Key": column["Key"],
                    "Default": column["Default"],
                    "Extra": column["Extra"],
                }
                for column in columns
            ]
    connection.close()
    return schema

def grok(user_input, memory_context=None):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        schema = get_database_schema()
        
        # Add the memory context if available
        if memory_context:
            mc = groq_context(memory_context)
            context_message = f"Here is the context of your previous query: {mc}\n"
            print("memoery_context",mc)
        else:
            mc = "This is a new query."

        system_message = f"""
        You are an intelligent assistant trained to generate SQL queries based on the provided database schema.
        below is the provided context
        {mc}
        Don't give any explanation, just the SQL query. in the plain text
        Don't use ```sql
        Dont use ```\n
        Dont use 'Here is the SQL query
        {schema}
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_message},
                      {"role": "user", "content": f"Generate an SQL query for `{user_input}`"}],
            model="llama3-8b-8192"
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print("normal groq")
        return f"An error occurred while using Groq: {str(e)}"


def groq_context(memory_context):
    print("memoery context",memory_context)
    print("mc",mc)
    try:
        client = Groq(api_key=GROQ_API_KEY)

        system_message = f"""  You are an advanced AI assistant capable of generating coherent responses based on the context of previous 
        interactions. Your primary role is to provide relevant answers and insights by considering the entire history of the conversation up to 
        the most recent interaction. Each time you respond, you should take into account the most recent user input and any system messages you 
        have processed before. When generating responses, reflect the latest user queries and the context established by previous conversations. 
        Don’t rephrase past inputs or responses verbatim but use them to inform your new answers. Always strive to provide answers that are 
        contextually appropriate and aligned with the latest user needs
        If there are conflict same name or any other like that give prefernce to the latest one
        this is the context {memory_context}
        """

        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_message}],
            model="llama3-8b-8192"  # Replace with the correct model if needed
        )

        context = chat_completion.choices[0].message.content.strip()

        # Return the formatted response from Groq
        return context

    except Exception as e:
        # Handle any potential errors that may occur during the API request
        print("context")
        return f"An error occurred while contacting Groq: {e}"

def grok_format(user_input, query_result):
    try:
        # Initialize the Groq client with your API key
        client = Groq(api_key=GROQ_API_KEY)

        # Create the system message that will instruct Groq on the format
        system_message = f"""
        I am giving you user input and query results, and I want you to show only the main result.

        User Input: {user_input}
        Query Result: {query_result}
        Please extract the value from the result and return only that value. 
        give in this format " The value is: "   
        Dont give Here's how you can extract the value: 
        also dont give : I understand that you want me to extract the value from the query result and return only that value.
          The value you want is the count of companies that are of the trading industry.  
          dont give You want me to extract the value from the query result and return only that value. The value you want is  Here is the value:
          
          """

        # Create the chat completion request to Groq's API
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_message}],
            model="llama3-8b-8192"  # Replace with the correct model if needed
        )
        
        # Extract the response from Groq's API and strip any extra spaces or newlines
        formatted_response = chat_completion.choices[0].message.content.strip()

        # Return the formatted response from Groq
        return formatted_response

    except Exception as e:
        # Handle any potential errors that may occur during the API request
        print("format")
        return f"An error occurred while contacting Groq: {e}"

# Function to execute SQL query and fetch results
def execute_query(sql):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
        return result
    finally:
        connection.close()

def save_chat_history(user_id, user_input, generated_sql, formatted_response, query_result=None, memory_context=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        query = """
        INSERT INTO chat_history (user_id, user_input, generated_sql, response, query_result, memory_context)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        query_result_converted = convert_decimal(query_result) if query_result else None
        query_result_json = json.dumps(query_result_converted) if query_result_converted else None
        
        # If there's a memory context from previous conversations, add it to the new entry
        cursor.execute(query, (user_id, user_input, generated_sql, formatted_response, query_result_json, memory_context))
        connection.commit()

def fetch_chat_history(user_id):
    connection = get_connection()
    with connection.cursor() as cursor:
        query = "SELECT user_input, generated_sql, response, query_result, timestamp, memory_context FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()

def main():
    st.title("SQL Query Generator with Chat History and Memory")

    

    user_id = st.text_input("Enter your username:")
    if not user_id:
        st.warning("Please enter a username to proceed.")
        return
    


    # Fetch and display chat history
    chat_history = fetch_chat_history(user_id)
    memory_context = ""

    # Show memory context if available
    st.subheader("Chat History")
    if chat_history:
        # Reverse the order of chat history for latest interactions at the bottom
        for idx, entry in reversed(list(enumerate(chat_history))):  # Reverse the order here
            user_input = entry["user_input"]
            response = entry["response"]
            timestamp = entry["timestamp"]

            # Consolidate memory context
            memory_context += f"User: {user_input}\nAssistant: {response}\n"

            # Assign a unique key to each button
            if st.button("Show Memory Context", key=f"show_memory_{idx}"):
                if memory_context:
                    st.subheader("Memory Context")
                    st.text(memory_context)
                else:
                    st.info("No memory context available.")

            # Display chat bubbles
            st.markdown(
                f'<div style="background-color:#dcf8c6;padding:10px;border-radius:15px;margin-bottom:5px;max-width:70%;word-wrap: break-word;">{user_input}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div style="background-color:#f1f0f0;padding:10px;border-radius:15px;margin-bottom:5px;max-width:70%;word-wrap: break-word;">{response}</div>',
                unsafe_allow_html=True
            )
        print("in main",groq_context(memory_context))
    else:
        st.info("No chat history found for this user.")



    # Input for new queries
    user_input = st.text_area("Enter your query description:")
    if st.button("Send"):
        if user_input:
            # Display the user input in a chat bubble
            st.markdown(f'<div style="background-color:#dcf8c6;padding:10px;border-radius:15px;margin-bottom:5px;max-width:70%;word-wrap: break-word;">{user_input}</div>', unsafe_allow_html=True)

            try:
                # Generate SQL query considering memory context
                generated_sql = grok(user_input, memory_context)
                st.write(generated_sql)
                
                # Execute SQL query and fetch results
                query_result = execute_query(generated_sql)

                # Create a bot response
                response = f"Query executed successfully. Returned {len(query_result)} rows."

                # Format the response using Groq
                formatted_response = grok_format(user_input, query_result)
                
                # Display the assistant's response in a chat bubble
                st.markdown(f'<div style="background-color:#f1f0f0;padding:10px;border-radius:15px;margin-bottom:5px;max-width:70%;word-wrap: break-word;">{formatted_response}</div>', unsafe_allow_html=True)
                
                # Update memory context with the latest interaction
                memory_context += f"User: {user_input}\nAssistant: {formatted_response}\n"

                # Save to chat history
                save_chat_history(user_id, user_input, generated_sql, formatted_response, query_result, memory_context)
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please enter a query description.")

if __name__ == "__main__":
    main()
