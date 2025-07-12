from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from elo_calculator import EloCalculator

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Initialize the EloCalculator
elo_calculator = EloCalculator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/input', methods=['GET', 'POST'])
def input_data():
    if request.method == 'POST':
        player1 = request.form['player1']
        player2 = request.form['player2']
        score1 = float(request.form['score1'])
        score2 = float(request.form['score2'])
        
        # Process the input data
        result = 1.0 if score1 > score2 else 0.0
        elo_calculator.update_elo_and_rankings()  # Update ELO based on the new match
        
        flash('Match results processed successfully!', 'success')
        return redirect(url_for('results'))

    return render_template('input.html')

@app.route('/results')
def results():
    # Display the updated rankings or results
    rankings = elo_calculator.df_ranking
    return render_template('results.html', rankings=rankings)

if __name__ == '__main__':
    app.run(debug=True)