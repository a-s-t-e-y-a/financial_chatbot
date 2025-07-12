import streamlit as st
import database
import ui

def main():
    st.title("Chatbot with Persistent Memory")
    database.init_db()
    ui.initialize_session_state()
    ui.handle_sidebar()
    ui.handle_chat_interface()

if __name__ == "__main__":
    main()