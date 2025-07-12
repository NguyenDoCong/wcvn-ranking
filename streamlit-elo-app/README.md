# Streamlit ELO Calculator

This project is a web application built using Streamlit that allows users to input player match data and calculate ELO ratings based on the results. The application provides a user-friendly interface for entering player scores and displays the updated rankings.

## Project Structure

```
streamlit-elo-app
├── src
│   ├── app.py                # Main entry point of the Streamlit application
│   ├── elo_calculator.py     # Contains the EloCalculator class for ELO logic
│   └── types
│       └── index.py          # Defines custom types or data structures
├── requirements.txt          # Lists project dependencies
└── README.md                 # Documentation for the project
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd streamlit-elo-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit application:
   ```
   streamlit run src/app.py
   ```

## Usage Guidelines

- Open the application in your web browser after running the command above.
- Input the names and scores of the players in the provided fields.
- Submit the data to see the updated ELO rankings.

## Dependencies

- Streamlit
- Pandas
- Any other libraries required for the ELO calculation logic

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.