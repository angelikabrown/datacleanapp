
from flask import Flask, request, render_template
import pandas as pd
import openai
import os
from dotenv import load_dotenv


#Loading OpenAI API key securely

#basic app is working

# create Flask app
app = Flask(__name__)

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


    return f"""
    
        <h2>Here is your Summary</h2><p>{summary}</p>
        <h2>Suggested Cleaning Steps</h2><p>{cleaning}</p>
        <h2> Preview of your data</h2>
        {df.head().to_html()}
    """


def summarize_data(df):
    text = f"This dataset has {df.shape[0]} rows and {df.shape[1]} columns. The columns are: {', '.join(df.columns)}.\n"
    text += f"Here is some statistics about the data:\n{df.describe(include='all').to_string()}"

    # Use OpenAI to summarize the data here
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful data analyst."},
            {"role": "user", "content": f"Summaraize the following dataset:\n{text}"}
        ]
    )


    return response['choices'][0]['message']['content']

def suggest_cleaning(df):
    text = f"The dataset contains the following columns: {', '.join(df.columns)}.\n"
    text += f"Preview of your data:\n"
    text += df.head().to_string()

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a senior data engineer."},
            {"role": "user", "content": f"Suggest how you would clean this dataset step by step:\n{text}"}
        ]
    )


    return response['choices'][0]['message']['content']



if __name__ == '__main__':
    app.run(debug=True)