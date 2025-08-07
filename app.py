
from flask import Flask, request, render_template, send_file
import pandas as pd
import os
from dotenv import load_dotenv
import openai
from io import StringIO

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

openai.api_key = api_key

# create Flask app
app = Flask(__name__)



##  ----- Routes -----

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    #grab the uploaded file
    file = request.files['file']
    # check if the file is a CSV
    if not file or not file.filename.endswith('.csv'):
        return "Please upload a valid CSV file.", 400
    # read the CSV file into a DataFrame
    df = pd.read_csv(file)

    # give a summary of the DataFrame
    summary = summarize_data(df)

    #suggest cleaning to the user
    cleaning = suggest_cleaning(df)

    #suggest cleaning code to the user
    cleaning_code = suggest_cleaning_code(df)

    


 

    return f"""
    
        <h2>Here is your Summary</h2><p>{summary}</p>

        <h2> Preview of your data</h2>
        {df.head().to_html()}

        <h2>Suggested Cleaning Steps</h2><p>{cleaning}</p>

        <h2>Suggested Cleaning Code</h2>

        <pre><code>{cleaning_code}</code></pre>

        

        <form action="/clean" method="post">
            <input type="hidden" name="csv" value="{df.to_csv(index=False)}">
            <button type="submit">Clean Data</button>
        </form>
        <form action="/apply_cleaning" method="post">
            <input type="hidden" name="cleaning_code" value="{cleaning_code}">
            <button type="submit">Apply Cleaning Code</button>
        </form>
        
        
    """

@app.route('/clean', methods=['POST'])
def clean():

    cvs_data = request.form['csv']
    # Convert the CSV string back to a DataFrame
    df = pd.read_csv(StringIO(cvs_data))

    # Here you would implement your data cleaning logic
    cleaned = basic_cleaning(df)

    
    global cleaned_df
    cleaned_df = cleaned

    return f"""
        <h2>Cleaning complete!/h2>
        {cleaned_df.head().to_html()}
        <p>✅ Basic cleaning applied (missing values filled, duplicates removed, etc.)</p>
        <br><a href="/download">Download Finished Data</a>
        <br><a href="/">Clean another file!</a></br>

        """

app.route('/apply_cleaning', methods=['POST'])
def apply_cleaning():
    global cleaned_df

    if 'cleaned_df' not in globals():
        return "No cleaned data available. Please clean a file first.", 400
    
    #grab cleaning code from the form
    cleaning_code = request.form['cleaning_code']

    #create local directory with df pointing to global cleaned_df
    local_env = {'df': cleaned_df.copy()}
    try:
        # Execute the cleaning code in the local environment
        exec(cleaning_code, {}, local_env)

        # Update the global cleaned_df with the cleaned df
        cleaned_df = local_env['df']
    except Exception as e:
        return f"Error applying cleaning code: {e}", 500
    return """
        <h2>Cleaning Code Applied Successfully!</h2>
        < a href="/download">Download Cleaned Data</a>
        <br><a href="/">Clean another file!</a></b>
        """


@app.route('/download')
def download():
    #download the cleaned data
    global cleaned_df

    #make sure cleaned_df exists
    if 'cleaned_df' not in globals():
        return "No cleaned data available. Please clean a file first.", 400

    file_path = "cleaned_data.csv"
    cleaned_df.to_csv(file_path, index=False)

    return send_file(file_path, as_attachment=True)



#    ----- Helper Functions -----

def summarize_data(df):
    text = f"This dataset has {df.shape[0]} rows and {df.shape[1]} columns. The columns are: {', '.join(df.columns)}.\n"
    text += f"Here is some statistics about the data:\n{df.describe(include='all').to_string()}"

    # Use OpenAI to summarize the data here
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful data analyst."},
            {"role": "user", "content": f"Summaraize the following dataset:\n{text}"}
        ]
    )


    return response.choices[0].message.content



def suggest_cleaning(df):
    text = f"The dataset contains the following columns: {', '.join(df.columns)}.\n"
    text += f"Preview of your data:\n"
    text += df.head().to_string()

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a senior data engineer."},
            {"role": "user", "content": f"Suggest how you would clean this dataset step by step:\n{text}"}
        ]
    )


    return response.choices[0].message.content

def suggest_cleaning_code(df):
    prompt = f"""
    Here is a preview of the dataset:
    {df.head().to_string()}

Provide python code to clean this dataset step by step.
    The code should include:
    - Removing duplicate rows
    - Handling missing values (fill with mean for numeric, mode for categorical)
    - Stripping whitespace from column names
    - Removing special characters from column names
    - Dropping columns with more than 50% missing values
    - Any other relevant cleaning steps based on the data provided
    Make sure to include comments explaining each step. Keep explanations of code simple and concise.

    """
    response = openai.chat.completions.create(  
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful senior data engineer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip("```python").strip("```")



def basic_cleaning(df):
    df = df.copy()

    # Strip column names of whitespace and special characters
    df.columns = df.columns.str.strip().str.replace('[^A-Za-z0-9_]+', '_', regex=True)

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Drop columns with more than 50% missing values
    df = df.dropna(thresh=len(df) * 0.5, axis=1)

    # Fill missing numeric values with column mean
    for col in df.select_dtypes(include='number'):
        df[col] = df[col].fillna(df[col].mean())

    # Fill missing categorical values with mode
    for col in df.select_dtypes(include='object'):
        if not df[col].mode().empty:
            df[col] = df[col].fillna(df[col].mode()[0])

    return df



if __name__ == '__main__':
    app.run(debug=True)