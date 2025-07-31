
from flask import Flask, request, render_template
import pandas as pd
import openai
import os
from dotenv import load_dotenv


#Loading OpenAI API key securely



# create Flask app
app = Flask(__name__)

def index():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)