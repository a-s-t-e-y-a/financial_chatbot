# Streamlit Chatbot

This project is a simple chatbot application built using Streamlit. It allows users to interact with a chatbot through a user-friendly interface. Users can create new chat sessions and load existing ones, with chat sessions stored in a simple database.

## Project Structure

```
streamlit-chatbot
├── app.py          # Main entry point for the Streamlit application
├── database.py     # Functions for database interaction
├── requirements.txt # List of dependencies
└── README.md       # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd streamlit-chatbot
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment. You can create one using:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
   Then install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. **Run the application:**
   Start the Streamlit application by running:
   ```
   streamlit run app.py
   ```

## Usage Guidelines

- Upon launching the application, users will see a chat interface.
- Users can create a new chat session by clicking the "New Chat" button.
- To load an existing chat session, users can select from the available sessions and click "Load Chat".
- The chatbot will respond to user inputs in real-time.

## Database

The application uses a simple SQLite database to store chat sessions. The `database.py` file contains functions to add new sessions and retrieve existing ones.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.