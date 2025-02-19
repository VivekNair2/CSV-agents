import streamlit as st
import re
import os
import pandas as pd
from dotenv import find_dotenv, load_dotenv
from groq import Groq

# 1. Load environment variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Ensure this is set in your .env

# 2. Load dataset & prepare partial data string
df = pd.read_excel("updated_coffee_shop_sales.xlsx", nrows=10000)

df_5_rows = df.head()
csv_string = df_5_rows.to_string(index=False)

# 3. Define the model
client = Groq(api_key=GROQ_API_KEY)

# 4. Helper function to execute code blocks and retrieve 'fig'
def get_fig_from_code(code):
    local_variables = {}
    exec(code, {}, local_variables)
    return local_variables.get("fig")

# 5. Streamlit UI
st.title("Business Analytics AI Agent")

# Display the dataset preview
st.subheader("Data Preview")
st.dataframe(df)

# Text area for user input
user_input = st.text_area("Enter your request:", height=100)

# Button to trigger the LLM invocation
if st.button("Submit"):
    st.write("Generating code...")
    
    prompt = (
        "You're a data visualization expert and use your favorite graphing library Plotly only. "
        "Suppose the data is provided as an updated_coffee_shop_sales.xlsx file. "
        "Here are the first 5 rows of the dataset:\n{data}\n"
        "Follow the user's indications when creating the graph. "
        "User request: {request}"
    )
    
    # Invoke the model
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": prompt.format(data=csv_string, request=user_input)},
            {"role": "user", "content": user_input},
        ]
    )
    
    result_output = response.choices[0].message.content
    
    
    # Extract Python code block
    code_block_match = re.search(r'```(?:[Pp]ython)?(.*?)```', result_output, re.DOTALL)
    
    if code_block_match:
        code_block = code_block_match.group(1).strip()
        
        # Ensure necessary imports are present
        if "import pandas as pd" not in code_block:
            code_block = "import pandas as pd\n" + code_block
        if "import plotly.express as px" not in code_block:
            code_block = "import plotly.express as px\n" + code_block

        cleaned_code = re.sub(r'(?m)^\s*fig\.show\(\)\s*$', '', code_block)

        try:
            fig = get_fig_from_code(cleaned_code)
            if fig:
                st.subheader("Generated Plot")
                st.plotly_chart(fig)
            else:
                st.error("No figure found in the generated code.")
        except Exception as e:
            st.error(f"Error generating figure: {e}")
else:
    st.info("No code block found in the response.")

