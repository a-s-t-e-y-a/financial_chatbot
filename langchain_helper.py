import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationChain
from langchain_core.prompts import PromptTemplate
from langchain.memory import VectorStoreRetrieverMemory

# Import financial advisory system
from financial_product_manager import FinancialProductManager
from financial_products.base_product import ProductCategory

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
FAISS_INDEX_PATH = "faiss_indexes"
os.makedirs(FAISS_INDEX_PATH, exist_ok=True)

# Get API key from environment
api_key = os.getenv("GOOGLE_API_KEY")
print(api_key)
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# --- LLM and Embeddings Initialization (Lazy) ---
llm = None
embeddings = None
financial_manager = None

def get_llm():
    """Lazy initialization of LLM"""
    global llm
    if llm is None:
        llm = GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7, google_api_key=api_key)
    return llm

def get_embeddings():
    """Lazy initialization of embeddings"""
    global embeddings
    if embeddings is None:
        import asyncio
        # Try to get existing event loop, create one if none exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in current thread, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    return embeddings

def get_financial_manager():
    """Lazy initialization of financial manager"""
    global financial_manager
    if financial_manager is None:
        embedding_func = lambda text: get_embeddings().embed_query(text)
        financial_manager = FinancialProductManager(
            data_directory="data",
            use_cloudflare=False,  # Set to True when Cloudflare credentials are available
            embedding_function=embedding_func
        )
    return financial_manager

# --- Prompt Template ---
# Generate a summary of available product categories
product_categories = [p.name.replace("_", " ").title() for p in ProductCategory]
financial_recommendations_summary = ", ".join(product_categories)

template = """You are an expert financial advisor AI assistant with deep knowledge of financial products including credit cards, mutual funds, fixed deposits, and insurance.

When users ask about financial products or advice, you will:
1. Analyze their query to understand their financial needs
2. Use the financial product recommendation system to find suitable products
3. Provide personalized recommendations with clear explanations
4. Explain the pros and cons of different options
5. Give practical advice based on their situation

For general conversation, you are friendly and helpful.

Financial Product Recommendations Available:
{financial_recommendations}

Relevant pieces of previous conversation:
{history}

Current conversation:
Human: {input}
AI:"""
PROMPT = PromptTemplate(
    input_variables=["history", "input"],
    partial_variables={"financial_recommendations": financial_recommendations_summary},
    template=template
)

def get_faiss_index_path(session_id: int) -> str:
    """Constructs the file path for a session's FAISS index."""
    return os.path.join(FAISS_INDEX_PATH, f"session_{session_id}")

def get_conversation_chain(session_id: int) -> ConversationChain:
    """
    Creates or loads a ConversationChain for a given session ID.

    Args:
        session_id: The unique identifier for the chat session.

    Returns:
        A ConversationChain object configured with memory.
    """
    index_path = get_faiss_index_path(session_id)

    if os.path.exists(index_path):
        # Load existing index from disk
        vectorstore = FAISS.load_local(index_path, get_embeddings(), allow_dangerous_deserialization=True)
    else:
        # Create a new index if it doesn't exist
        vectorstore = FAISS.from_texts(["This is the start of the conversation."], embedding=get_embeddings())
        vectorstore.save_local(index_path)

    retriever = vectorstore.as_retriever(search_kwargs=dict(k=3))
    memory = VectorStoreRetrieverMemory(retriever=retriever)
    
    chain = ConversationChain(
        llm=get_llm(),
        prompt=PROMPT,
        memory=memory,
        verbose=True
    )
    return chain

def get_bot_response(chain: ConversationChain, input_text: str, session_id: int) -> str:
    """
    Gets a response from the bot and saves the updated memory.

    Args:
        chain: The ConversationChain object for the session.
        input_text: The user's message.
        session_id: The current session ID.

    Returns:
        The bot's response message.
    """
    # Get the bot's prediction
    bot_response = chain.predict(input=input_text)
    
    # Save the updated vector store to disk
    index_path = get_faiss_index_path(session_id)
    chain.memory.retriever.vectorstore.save_local(index_path)
    
    return bot_response

def get_bot_response_streaming(chain: ConversationChain, input_text: str, session_id: int):
    """
    Gets a streaming response from the bot and saves the updated memory.

    Args:
        chain: The ConversationChain object for the session.
        input_text: The user's message.
        session_id: The current session ID.

    Yields:
        Chunks of the bot's response as they are generated.
    """
    # Get relevant history from memory using the input text
    memory_variables = chain.memory.load_memory_variables({"input": input_text})
    
    # Check if this is a financial query and get recommendations
    financial_recommendations = ""
    if is_financial_query(input_text):
        # Extract user preferences from current input and history
        conversation_history = memory_variables.get('history', '')
        user_preferences = extract_user_preferences(input_text, conversation_history)
        
        # Get financial recommendations
        financial_recommendations = get_financial_recommendations(input_text, user_preferences)
    
    # Format the prompt with history, current input, and financial recommendations
    prompt_value = chain.prompt.format_prompt(
        input=input_text,
        financial_recommendations=financial_recommendations,
        **memory_variables
    )
    
    # Print the final prompt for debugging
    final_prompt = prompt_value.to_string()
    print("=" * 80)
    print("FINAL PROMPT BEING SENT TO GEMINI:")
    print("=" * 80)
    print(final_prompt)
    print("=" * 80)
    
    # Stream the response from the LLM
    full_response = ""
    for chunk in chain.llm.stream(prompt_value.to_string()):
        full_response += chunk
        yield chunk
    
    # Save the conversation to memory
    chain.memory.save_context(
        {"input": input_text},
        {"output": full_response}
    )
    
    # Save the updated vector store to disk
    index_path = get_faiss_index_path(session_id)
    chain.memory.retriever.vectorstore.save_local(index_path)

def delete_session_faiss_index(session_id: int):
    """
    Deletes the FAISS index files for a given session.

    Args:
        session_id: The unique identifier for the chat session.
    """
    import shutil
    index_path = get_faiss_index_path(session_id)
    if os.path.exists(index_path):
        shutil.rmtree(index_path)
        print(f"Deleted FAISS index for session {session_id}")

def is_financial_query(input_text: str) -> bool:
    """
    Determine if the user query is related to financial products
    
    Args:
        input_text: User's input message
        
    Returns:
        True if query is finance-related, False otherwise
    """
    financial_keywords = [
        'credit card', 'loan', 'mutual fund', 'fixed deposit', 'fd', 'investment',
        'insurance', 'savings', 'bank', 'finance', 'money', 'invest', 'portfolio',
        'cashback', 'reward', 'interest rate', 'returns', 'risk', 'sip',
        'recommend', 'suggest', 'best', 'compare', 'which card', 'which fund'
    ]
    
    input_lower = input_text.lower()
    return any(keyword in input_lower for keyword in financial_keywords)

def extract_user_preferences(input_text: str, conversation_history: str = "") -> dict:
    """
    Extract user preferences from their query and conversation history
    
    Args:
        input_text: Current user input
        conversation_history: Previous conversation context
        
    Returns:
        Dictionary of extracted preferences
    """
    preferences = {}
    text = (input_text + " " + conversation_history).lower()
    
    # Extract income range
    if any(word in text for word in ['high income', 'premium', 'luxury']):
        preferences['income_range'] = 'premium'
    elif any(word in text for word in ['middle', 'average', 'regular']):
        preferences['income_range'] = 'mid'
    elif any(word in text for word in ['student', 'low income', 'basic']):
        preferences['income_range'] = 'entry'
    
    # Extract spending categories
    categories = []
    if any(word in text for word in ['travel', 'vacation', 'flight', 'hotel']):
        categories.append('travel')
    if any(word in text for word in ['food', 'restaurant', 'dining']):
        categories.append('dining')
    if any(word in text for word in ['fuel', 'petrol', 'gas']):
        categories.append('fuel')
    if any(word in text for word in ['shopping', 'online', 'purchase']):
        categories.append('shopping')
    if categories:
        preferences['spending_categories'] = categories
    
    # Extract investment preferences
    if any(word in text for word in ['long term', 'retirement', '10 year']):
        preferences['investment_horizon'] = 'long term'
    elif any(word in text for word in ['short term', 'quick', '1 year']):
        preferences['investment_horizon'] = 'short term'
    elif any(word in text for word in ['medium term', '3 year', '5 year']):
        preferences['investment_horizon'] = 'medium term'
    
    # Extract risk tolerance
    if any(word in text for word in ['safe', 'low risk', 'conservative']):
        preferences['risk_tolerance'] = 'low risk'
    elif any(word in text for word in ['aggressive', 'high risk', 'growth']):
        preferences['risk_tolerance'] = 'high risk'
    else:
        preferences['risk_tolerance'] = 'moderate risk'
    
    # Extract investment goals
    if any(word in text for word in ['tax saving', 'elss', '80c']):
        preferences['investment_goal'] = 'tax saving'
    elif any(word in text for word in ['retirement', 'pension']):
        preferences['investment_goal'] = 'retirement'
    elif any(word in text for word in ['wealth', 'growth', 'appreciation']):
        preferences['investment_goal'] = 'wealth creation'
    elif any(word in text for word in ['income', 'dividend', 'regular']):
        preferences['investment_goal'] = 'regular income'
    
    # Extract product type preferences
    if any(word in text for word in ['sip', 'systematic']):
        preferences['investment_type'] = 'sip'
    
    return preferences

def get_financial_recommendations(input_text: str, user_preferences: dict = None) -> str:
    """
    Get financial product recommendations based on user query
    
    Args:
        input_text: User's query
        user_preferences: Extracted user preferences
        
    Returns:
        Formatted recommendations string
    """
    try:
        # Determine relevant product categories based on query
        categories = []
        input_lower = input_text.lower()
        
        if any(word in input_lower for word in ['credit card', 'card', 'cashback', 'reward']):
            categories.append(ProductCategory.CREDIT_CARDS)
        if any(word in input_lower for word in ['mutual fund', 'fund', 'sip', 'investment']):
            categories.append(ProductCategory.MUTUAL_FUNDS)
        if any(word in input_lower for word in ['fixed deposit', 'fd', 'deposit', 'safe investment']):
            categories.append(ProductCategory.FIXED_DEPOSITS)
        
        # If no specific category detected, search all
        if not categories:
            categories = list(ProductCategory)
        
        # Get recommendations
        recommendations = get_financial_manager().recommend_products(
            user_query=input_text,
            product_categories=categories,
            user_preferences=user_preferences or {},
            max_results=5
        )
        
        if not recommendations.products:
            return "I couldn't find specific financial products matching your query. Please provide more details about what you're looking for."
        
        # Format recommendations
        formatted_recs = []
        formatted_recs.append(f"Based on your query '{input_text}', here are my top recommendations:")
        formatted_recs.append("")
        
        for i, scored_product in enumerate(recommendations.products[:3], 1):
            product = scored_product.product
            formatted_recs.append(f"{i}. **{product.name}**")
            formatted_recs.append(f"   Category: {product.category.value}")
            formatted_recs.append(f"   Score: {scored_product.score:.1f}/100")
            
            # Add key features (limit to 3)
            if product.features:
                formatted_recs.append(f"   Key Features:")
                for feature in product.features[:3]:
                    formatted_recs.append(f"   • {feature}")
            
            formatted_recs.append(f"   Reasoning: {scored_product.reasoning}")
            formatted_recs.append("")
        
        formatted_recs.append(recommendations.recommendations_reasoning)
        
        return "\n".join(formatted_recs)
        
    except Exception as e:
        print(f"Error getting financial recommendations: {e}")
        return "I'm having trouble accessing financial product data right now. Please try again later."

def initialize_financial_system() -> bool:
    """
    Initialize the financial advisory system
    
    Returns:
        True if successful, False otherwise
    """
    try:
        print("Initializing financial advisory system...")
        success = get_financial_manager().initialize_vector_store()
        if success:
            print("Financial advisory system initialized successfully")
        else:
            print("Warning: Financial system initialized but vector store setup failed")
        return success
    except Exception as e:
        print(f"Error initializing financial system: {e}")
        return False
