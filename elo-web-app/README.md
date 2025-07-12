# ELO Web Application

This project is a web application that implements an ELO rating system for players based on match results. It allows users to input match data, calculates new ELO ratings, and displays the updated rankings.

## Project Structure

```
elo-web-app
├── app.py                     # Main entry point of the web application
├── elo_calculator.py          # Contains the ELOCalculator class for ELO calculations
├── templates                  # HTML templates for the web application
│   ├── index.html             # Main interface for navigation
│   ├── results.html           # Displays results of ELO calculations
│   └── input.html             # Form for user input of match results
├── static                     # Static files for the web application
│   └── style.css              # CSS styles for the application
├── config.json                # Configuration settings for the application
├── ELO ranking by map - Kết quả.csv  # CSV file for match results
├── ELO ranking by map - Danh sách người chơi.csv  # CSV file for player list and ELO ratings
├── ELO ranking by map - Lịch sử ELO.csv  # CSV file for ELO history
├── ELO ranking by map - Bảng xếp hạng ELO.csv  # CSV file for current player rankings
└── README.md                  # Documentation for the project
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd elo-web-app
   ```

2. **Install dependencies**:
   Ensure you have Python installed, then install Flask and other required packages:
   ```
   pip install Flask pandas numpy
   ```

3. **Run the application**:
   Start the Flask web server:
   ```
   python app.py
   ```

4. **Access the application**:
   Open your web browser and go to `http://127.0.0.1:5000` to access the ELO calculator web application.

## Usage Guidelines

- Navigate to the input page to enter match results.
- After submitting the results, the application will calculate the new ELO ratings and display the updated rankings.
- You can reset the ELO ratings and statistics if needed.

## License

This project is licensed under the MIT License.