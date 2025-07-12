import pandas as pd
import numpy as np
import json
from datetime import datetime
import os

FILE_CONFIG = 'config.json'
FILE_RESULTS = 'ELO ranking by map - Kết quả.csv'
FILE_PLAYER_LIST = 'ELO ranking by map - Danh sách người chơi.csv'
FILE_ELO_HISTORY = 'ELO ranking by map - Lịch sử ELO.csv'
FILE_RANKING = 'ELO ranking by map - Bảng xếp hạng ELO.csv'

class EloCalculator:
    def __init__(self):
        self.config = self._load_config()
        self._check_files_exist()
        self._load_data()

    def _load_data(self):
        try:
            self.df_results = pd.read_csv(FILE_RESULTS)
            self.df_players = pd.read_csv(FILE_PLAYER_LIST)
            self.df_history = pd.read_csv(FILE_ELO_HISTORY)
            self.df_ranking = pd.read_csv(FILE_RANKING)
            if 'Processed' not in self.df_results.columns:
                self.df_results['Processed'] = False
            else:
                self.df_results['Processed'] = self.df_results['Processed'].astype(bool)
        except FileNotFoundError as e:
            print(f"Lỗi: Không tìm thấy tệp {e.filename}.")
            exit()
        except Exception as e:
            print(f"Đã xảy ra lỗi khi đọc tệp: {e}")
            exit()

    def _check_files_exist(self):
        files_to_check = [FILE_RESULTS, FILE_PLAYER_LIST, FILE_ELO_HISTORY, FILE_RANKING]
        for f in files_to_check:
            if not os.path.exists(f):
                print(f"Lỗi: Tệp '{f}' không tồn tại.")
                exit()

    def _load_config(self):
        try:
            with open(FILE_CONFIG, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'LAST_PROCESSED_ROW': 1}
        except json.JSONDecodeError:
            return {'LAST_PROCESSED_ROW': 1}

    def calculate_new_elo(self, elo1, elo2, result):
        k = 32
        expected_score1 = 1 / (1 + 10**((elo2 - elo1) / 400))
        new_elo1 = round(elo1 + k * (result - expected_score1))
        new_elo2 = round(elo2 + k * ((1 - result) - (1 - expected_score1)))
        return new_elo1, new_elo2

    def update_elo_and_rankings(self, player1_name, player2_name, result):
        current_elo1 = self._get_player_elo(player1_name)
        current_elo2 = self._get_player_elo(player2_name)
        new_elo1, new_elo2 = self.calculate_new_elo(current_elo1, current_elo2, result)
        self._update_elo_in_player_list(player1_name, new_elo1)
        self._update_elo_in_player_list(player2_name, new_elo2)
        self._update_player_stats(player1_name, result)
        self._update_player_stats(player2_name, 1 - result)
        self._save_all_data()

    def _get_player_elo(self, player_name):
        player_row = self.df_players[self.df_players['Tên'] == player_name]
        return player_row['ELO'].iloc[0] if not player_row.empty else 1500

    def _update_player_stats(self, player_name, result):
        player_index = self.df_players.index[self.df_players['Tên'] == player_name].tolist()
        if player_index:
            idx = player_index[0]
            self.df_players.loc[idx, 'Số trận'] += 1
            if result == 1:
                self.df_players.loc[idx, 'Thắng'] += 1
            games_played = self.df_players.loc[idx, 'Số trận']
            games_won = self.df_players.loc[idx, 'Thắng']
            self.df_players.loc[idx, 'Tỉ lệ thắng'] = games_won / games_played if games_played > 0 else 0
        else:
            new_player = pd.DataFrame([{
                'Tên': player_name,
                'ELO': 1500,
                'Số trận': 1,
                'Thắng': 1 if result == 1 else 0,
                'Tỉ lệ thắng': 1.0 if result == 1 else 0.0
            }])
            self.df_players = pd.concat([self.df_players, new_player], ignore_index=True)

    def _update_elo_in_player_list(self, player_name, new_elo):
        self.df_players.loc[self.df_players['Tên'] == player_name, 'ELO'] = new_elo

    def _save_all_data(self):
        self.df_results.to_csv(FILE_RESULTS, index=False)
        self.df_players.to_csv(FILE_PLAYER_LIST, index=False)
        self.df_history.to_csv(FILE_ELO_HISTORY, index=False)
        self.df_ranking.to_csv(FILE_RANKING, index=False)

    def reset_elo_and_status(self):
        self.df_players['ELO'] = 1500
        self.df_players[['Số trận', 'Thắng', 'Tỉ lệ thắng']] = 0
        self.df_history = self.df_history.iloc[0:0]
        self._save_all_data()