import streamlit as st
import pymysql
import json
from decimal import Decimal
from groq import Groq

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

# Function to generate SQL query using Groq
def grok(user_input):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        schema = get_database_schema()
        system_message = f"""
        You are an intelligent assistant trained to generate SQL queries based on the provided database schema.
        Don't give any explanation, just the SQL query. in the plain text
        Don't use ```sql
        {schema}
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_message},
                      {"role": "user", "content": f"Generate an SQL query for `{user_input}`"}],
            model="llama3-8b-8192"
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred while using Groq: {str(e)}"


    
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

# Function to save chat history
def save_chat_history(user_id, user_input, generated_sql, response, query_result=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        query = """
        INSERT INTO chat_history (user_id, user_input, generated_sql, response, query_result)
        VALUES (%s, %s, %s, %s, %s)
        """
        query_result_converted = convert_decimal(query_result) if query_result else None
        query_result_json = json.dumps(query_result_converted) if query_result_converted else None
        cursor.execute(query, (user_id, user_input, generated_sql, response, query_result_json))
        connection.commit()

# Function to fetch chat history
def fetch_chat_history(user_id):
    connection = get_connection()
    with connection.cursor() as cursor:
        query = "SELECT user_input, generated_sql, response, query_result, timestamp FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()

# Streamlit UI code
def main():
    st.title("SQL Query Generator with Chat History")

    # User Login
    user_id = st.text_input("Enter your username:")
    if not user_id:
        st.warning("Please enter a username to proceed.")
        return

    # Fetch and display chat history
    st.subheader("Chat History")
    chat_history = fetch_chat_history(user_id)
    if chat_history:
        for entry in chat_history:
            with st.expander(f"{entry['timestamp']} - Query"):
                st.markdown(f"**Input:** {entry['user_input']}")
                st.code(entry['generated_sql'], language="sql")
                st.markdown(f"**Response:** {entry['response']}")
                if entry['query_result']:
                    st.json(json.loads(entry['query_result']))
    else:
        st.info("No chat history found.")

    # Input for new queries
    user_input = st.text_area("Enter your query description:")
    if st.button("Ask"):
        if user_input:
            try:
                # Generate SQL query
                generated_sql = grok(user_input)
                st.write(generated_sql)
                # Execute SQL query and fetch results
                query_result = execute_query(generated_sql)

                # Create a bot response
                response = f"Query executed successfully. Returned {len(query_result)} rows."

                # Display in chat
                st.markdown(f"**User:** {user_input}")
                st.markdown(f"**Bot:** {response}")
                st.json(query_result)

                # Save to chat history
                save_chat_history(user_id, user_input, generated_sql, response, query_result)
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please enter a query description.")

if __name__ == "__main__":
    main()
