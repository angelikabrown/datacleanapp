
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

uploaded_df = None
cleaned_df = None

##  ----- Routes -----

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle file upload and process the CSV file.
    
    """
    

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

    csv_data = df.to_csv(index=False)

    return render_template('upload_result.html',
                           summary=summary,
                           preview=df.head().to_html(),
                           cleaning=cleaning,
                           cleaning_code=cleaning_code,
                           csv_data=csv_data
    )


@app.route('/clean', methods=['POST'])
def clean():
    """
    
    Handle cleaning the uploaded CSV data.
    
    """

    cvs_data = request.form['csv']
    # Convert the CSV string back to a DataFrame
    df = pd.read_csv(StringIO(cvs_data))

    # Here you would implement your data cleaning logic
    cleaned = basic_cleaning(df)

    
    global cleaned_df
    cleaned_df = cleaned

    return render_template('clean_result.html', table=cleaned_df.head().to_html())


@app.route("/apply_cleaning", methods=["POST"])
def apply_cleaning():
    """

    Apply user-provided cleaning code to the DataFrame.
    
    """
    global cleaned_df

    csv_data = request.form['csv']
    if not csv_data:
        return "No CSV data provided.", 400
    
    # Convert the CSV string back to a DataFrame
    df = pd.read_csv(StringIO(csv_data))

    cleaning_code = request.form.get("cleaning_code", "").strip()
    if not cleaning_code:
        return "No cleaning code provided.", 400

    # Remove markdown fences if any
    cleaning_code = cleaning_code.replace("```python", "").replace("```", "").strip()

    # Run cleaning code safely on a copy of the current cleaned_df
    local_env = {"df": df.copy()}
    try:
        exec(cleaning_code, {}, local_env)
        cleaned_df = local_env["df"]
    except Exception as e:
        return f"Error applying cleaning code: {e}", 500

    return render_template('ai_clean_result.html', table=cleaned_df.head().to_html())


@app.route('/download')
def download():
    """
    
    Download the cleaned DataFrame as a CSV file.
    
    """
    #download the cleaned data
    global cleaned_df

    #make sure cleaned_df exists
    if 'cleaned_df' not in globals():
        return "No cleaned data available. Please clean a file first.", 400

    file_path = "cleaned_data.csv"
    cleaned_df.to_csv(file_path, index=False)

    return send_file(file_path, as_attachment=True)



#    ----- Helper Functions LLM calls -----

def summarize_data(df):
    """ 
    Summarize the DataFrame using OpenAI.
    
    """
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
    """
    Suggest cleaning steps for the DataFrame using OpenAI.  
    
    """
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

Provide python code to clean this dataset. This code will be executed in another function.
    The code should include:
    - Removing duplicate rows
    - Handling missing values (fill with mean for numeric, mode for categorical)
    - Stripping whitespace from column names
    - Removing special characters from column names
    - Dropping columns with more than 50% missing values
    - Any other relevant cleaning steps based on the data provided
    Do not add comments. I want the code clean and ready to be executed without errors.

    """
    response = openai.chat.completions.create(  
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful senior data engineer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip("```python").strip("```")



#    ----- Basic Cleaning Function -----

def basic_cleaning(df):
    """   
    Perform basic cleaning on the DataFrame:
    Strip column names of whitespace and special characters
    
    """
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