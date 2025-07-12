import pandas as pd
import numpy as np
import json
from datetime import datetime
import os

class EloCalculator:
    def __init__(self):
        self.players = {}
        self.df_ranking = pd.DataFrame(columns=['Player', 'ELO'])

    def update_elo(self, player1, player2, score1, score2):
        # Initialize players if they don't exist
        if player1 not in self.players:
            self.players[player1] = 1000  # Starting ELO
        if player2 not in self.players:
            self.players[player2] = 1000  # Starting ELO

        # Calculate expected scores
        expected_score1 = self.expected_score(self.players[player1], self.players[player2])
        expected_score2 = self.expected_score(self.players[player2], self.players[player1])

        # Update ELO ratings based on the match result
        if score1 > score2:
            self.players[player1] += 32 * (1 - expected_score1)
            self.players[player2] += 32 * (0 - expected_score2)
        elif score1 < score2:
            self.players[player1] += 32 * (0 - expected_score1)
            self.players[player2] += 32 * (1 - expected_score2)

        self.update_rankings()

    def expected_score(self, player_elo, opponent_elo):
        return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))

    def update_rankings(self):
        self.df_ranking = pd.DataFrame(list(self.players.items()), columns=['Player', 'ELO'])
        self.df_ranking = self.df_ranking.sort_values(by='ELO', ascending=False).reset_index(drop=True)

    def get_rankings(self):
        return self.df_ranking