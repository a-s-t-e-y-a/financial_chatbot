import streamlit as st
import database
import langchain_helper as lch

def initialize_session_state():
    """Initializes the session state variables."""
    if 'session_ids' not in st.session_state:
        st.session_state.session_ids = []
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'chain' not in st.session_state:
        st.session_state.chain = None
    if 'financial_system_initialized' not in st.session_state:
        st.session_state.financial_system_initialized = False

def initialize_financial_system():
    """Initialize the financial advisory system once"""
    if not st.session_state.financial_system_initialized:
        with st.spinner("Initializing financial advisory system..."):
            success = lch.initialize_financial_system()
            st.session_state.financial_system_initialized = success
            if success:
                st.success("Financial advisory system ready!")
            else:
                st.warning("Financial system initialized with limited functionality")
        return success
    return True

def handle_sidebar():
    """Manages the sidebar for session creation, loading, and selection."""
    st.sidebar.title("🏦 Financial Advisor Chatbot")
    
    # Financial system status
    if st.session_state.financial_system_initialized:
        st.sidebar.success("✅ Financial Advisory System: Active")
    else:
        st.sidebar.warning("⚠️ Financial Advisory System: Limited")
    
    # Show financial product stats
    try:
        stats = lch.financial_manager.get_category_stats()
        st.sidebar.subheader("📊 Available Products")
        
        for category, data in stats.items():
            if 'error' not in data:
                st.sidebar.text(f"{category.replace('_', ' ').title()}: {data['total_products']} products")
            else:
                st.sidebar.text(f"{category.replace('_', ' ').title()}: Error loading")
    except Exception as e:
        st.sidebar.text("Product stats unavailable")

    if st.sidebar.button("Load Old Chat Sessions"):
        st.session_state.session_ids = database.get_all_sessions()
        if st.session_state.session_ids:
            st.sidebar.success("Loaded old chat sessions.")
            if not st.session_state.current_session_id:
                st.session_state.current_session_id = st.session_state.session_ids[0]
        else:
            st.sidebar.warning("No old chat sessions found.")

    if st.sidebar.button("Create New Chat Session"):
        new_session_id = database.create_new_session()
        st.session_state.session_ids.insert(0, new_session_id)
        st.session_state.current_session_id = new_session_id
        st.sidebar.success("Created a new chat session.")
        st.rerun()

    # Add delete session button
    if st.session_state.current_session_id and st.session_state.session_ids:
        if st.sidebar.button("🗑️ Delete Current Session", type="secondary"):
            # Delete from database
            database.delete_session(st.session_state.current_session_id)
            
            # Delete FAISS index
            lch.delete_session_faiss_index(st.session_state.current_session_id)
            
            # Remove from session list
            st.session_state.session_ids.remove(st.session_state.current_session_id)
            
            # Reset current session
            if st.session_state.session_ids:
                st.session_state.current_session_id = st.session_state.session_ids[0]
                st.session_state.chain = None  # Reset chain to force reload
            else:
                st.session_state.current_session_id = None
                st.session_state.chain = None
            
            st.sidebar.success("Session deleted successfully!")
            st.rerun()

    if st.session_state.session_ids:
        session_options = {session_id: f"Chat Session {session_id}" for session_id in st.session_state.session_ids}
        
        current_index = st.session_state.session_ids.index(st.session_state.current_session_id) if st.session_state.current_session_id in st.session_state.session_ids else 0

        selected_session = st.sidebar.radio(
            "Select a chat session:",
            options=st.session_state.session_ids,
            format_func=lambda x: session_options[x],
            index=current_index
        )

        if selected_session != st.session_state.current_session_id or st.session_state.chain is None:
            st.session_state.current_session_id = selected_session
            st.session_state.chain = lch.get_conversation_chain(st.session_state.current_session_id)
            st.sidebar.info("Loaded memory for the session.")
    
    # Add financial advisor quick actions
    st.sidebar.subheader("💡 Quick Financial Queries")
    quick_queries = [
        "Best credit cards for cashback",
        "Low risk mutual funds",
        "High interest fixed deposits",
        "Tax saving investment options",
        "Travel credit cards comparison"
    ]
    
    for query in quick_queries:
        if st.sidebar.button(query, key=f"quick_{query}"):
            if st.session_state.current_session_id and st.session_state.chain:
                st.session_state.quick_query = query
                st.rerun()

def handle_chat_interface():
    """Manages the main chat interface for displaying and sending messages."""
    if st.session_state.current_session_id and st.session_state.chain:
        st.header(f"💬 Chat Session {st.session_state.current_session_id}")
        
        # Add financial advisor intro
        st.info("🏦 **Financial Advisor AI** - Ask me about credit cards, mutual funds, fixed deposits, and investment advice!")
        
        messages = database.get_messages_for_session(st.session_state.current_session_id)
        for message in messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Handle quick query from sidebar
        user_input = None
        if hasattr(st.session_state, 'quick_query'):
            user_input = st.session_state.quick_query
            delattr(st.session_state, 'quick_query')
        else:
            user_input = st.chat_input("Ask me about financial products, investments, or any financial advice...")
        
        if user_input:
            # Display user message immediately
            with st.chat_message("user"):
                st.write(user_input)
            
            # Add user message to database
            database.add_message_to_session(st.session_state.current_session_id, "user", user_input)
            
            # Display streaming bot response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Show thinking indicator for financial queries
                if lch.is_financial_query(user_input):
                    with st.spinner("🔍 Analyzing financial products..."):
                        pass
                
                # Stream the response
                for chunk in lch.get_bot_response_streaming(st.session_state.chain, user_input, st.session_state.current_session_id):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                
                # Final response without cursor
                message_placeholder.markdown(full_response)

            # Add bot response to database
            database.add_message_to_session(st.session_state.current_session_id, "assistant", full_response)
    else:
        st.info("Create a new chat session or load an old one to start chatting.")
        
        # Show sample financial queries
        st.subheader("💡 Sample Financial Queries")
        sample_queries = [
            "What are the best cashback credit cards available?",
            "I want to invest ₹10,000 monthly in mutual funds. What do you recommend?", 
            "Which fixed deposit offers the highest interest rate?",
            "I'm looking for tax-saving investment options under 80C",
            "Compare travel credit cards with low annual fees",
            "Suggest mutual funds for retirement planning",
            "What are the best investment options for a 25-year-old?"
        ]
        
        for i, query in enumerate(sample_queries, 1):
            st.text(f"{i}. {query}")

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Financial Advisor Chatbot",
        page_icon="🏦",
        layout="wide"
    )
    
    initialize_session_state()
    initialize_financial_system()
    handle_sidebar()
    handle_chat_interface()

if __name__ == "__main__":
    main()
