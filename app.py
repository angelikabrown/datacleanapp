
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
    
        <h2>Here is your Summary</h2>
    """

if __name__ == '__main__':
    app.run(debug=True)