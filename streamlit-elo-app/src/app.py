import streamlit as st
import pandas as pd
from elo_calculator import EloCalculator

# Initialize the EloCalculator
elo_calculator = EloCalculator()

def main():
    st.title("ELO Calculator")

    # Input form for player data
    with st.form(key='elo_form'):
        player1 = st.text_input("Player 1 Name")
        score1 = st.number_input("Player 1 Score", min_value=0.0, step=0.1)
        player2 = st.text_input("Player 2 Name")
        score2 = st.number_input("Player 2 Score", min_value=0.0, step=0.1)
        
        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            # Process the input data
            result = 1.0 if score1 > score2 else 0.0
            elo_calculator.update_elo_and_rankings(player1, player2, score1, score2)  # Update ELO based on the new match
            
            st.success('Match results processed successfully!')

    # Display the updated rankings
    st.subheader("Current Rankings")
    rankings = elo_calculator.df_ranking
    st.dataframe(rankings)

if __name__ == "__main__":
    main()