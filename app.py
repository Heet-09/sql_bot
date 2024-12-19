import streamlit as st
import pymysql
from groq import Groq

# Groq API Key
GROQ_API_KEY = "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"

# Function to get the database schema
def get_database_schema():
    schema = {}
    target_tables = ["financial_data"]

    connection = pymysql.connect(
        host="localhost",
        user="heetjain",  # Replace with your database username
        password="heetjain",  # Replace with your database password
        db="fin",  # Replace with your database name
        charset="utf8mb4"
    )

    with connection.cursor() as cursor:
        for table_name in target_tables:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            schema[table_name] = [
                {
                    "Field": column[0],
                    "Type": column[1],
                    "Null": column[2],
                    "Key": column[3],
                    "Default": column[4],
                    "Extra": column[5],
                }
                for column in columns
            ]
    return schema

# Function to use Groq and generate SQL query
def grok(user_input):
    try:
        # Initialize the Groq client with the API key
        client = Groq(api_key=GROQ_API_KEY)

        # Get database schema
        schema = get_database_schema()

        # System message to instruct the assistant
        system_message = f"""
        You are an intelligent assistant trained to generate SQL queries based on the provided database schema. 
        Don't give any explanation, just the SQL query.
        dont give ```  ``` this also
        {schema}
        """

        # Send a query to the Groq API with the system message
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_message},
                      {"role": "user", "content": f"Generate an SQL query for `{user_input}`"}],
            model="llama3-8b-8192"
        )

        # Return the generated SQL query
        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        return f"An error occurred while using Groq: {str(e)}"

# Function to execute the generated SQL query
def query_execute(query):
    # try:
        # Connect to the database directly using pymysql
        connection = pymysql.connect(
            host="localhost",
            user="heetjain",  # Replace with your database username
            password="heetjain",  # Replace with your database password
            db="fin",  # Replace with your database name
            charset="utf8mb4"
        )

        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

        return result

    # except Exception as e:
    #     return f"An error occurred: {e}"
    # finally:
    #     if connection:
    #         connection.close()

# Streamlit UI code
def main():
    st.title("SQL Query Generator")

    # Input form for the user
    user_input = st.text_area("Enter your query description:")

    if st.button("Generate SQL Query"):
        if user_input:
            try:
                # Step 1: Generate the SQL query
                generated_sql = grok(user_input)

                # Display the generated SQL query
                st.subheader("Generated SQL Query:")
                st.code(generated_sql, language="sql")

                # Step 2: Execute the SQL query
                results = query_execute(generated_sql)

                # If results are empty, handle it
                if not results:
                    st.subheader("Query Results:")
                    st.write("No data found for this query.")

                else:
                    # Display results in a nicely formatted table
                    st.subheader("Query Results:")
                    # Displaying as a dataframe if results are a list of tuples (i.e., SQL result)
                    st.write(results)

            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please enter a query description.")

if __name__ == "__main__":
    main()
