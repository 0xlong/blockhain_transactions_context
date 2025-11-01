import streamlit as st
from modules import config
import logging

# Initialize centralized logging configuration - consistent logging format across all modules
config.setup_logging()

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="Trading Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Validate required environment variables
# This checks if all necessary API keys and login credentials are present in the .env file
is_valid, missing = config.validate_required_keys()
if not is_valid:
    st.error(f"❌ Missing required environment variables: {', '.join(missing)}")
    st.info("Please create a `.env` file with API keys. See README.md for setup instructions.")
    st.stop()  # Stop execution but keep UI visible
else:
    logging.info("streamlit_app.py: Environment variables validated successfully")


# ===== AUTHENTICATION SYSTEM =====
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False  # User starts as not authenticated

if not st.session_state.authenticated:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                if username == config.LOGIN_USERNAME and password == config.LOGIN_PASSWORD:
                    st.session_state.authenticated = True
                    logging.info("streamlit_app.py: Login successful")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
    st.stop()

# Only show app content and sidebar after successful login
if st.session_state.authenticated:
    
    # Define pages
    data_pipeline_etl = st.Page("pages/data_pipeline_etl.py", title="ETL")
    architecture = st.Page("pages/app_architecture.py", title="Architecture")
    price_chart = st.Page("pages/price_chart.py", title="Price Chart")
    ai_interpreter = st.Page("pages/ai_interpreter.py", title="AI Interpreter")
    full_analysis = st.Page("pages/full_analysis.py", title="Full Analysis")
    
    # Create navigation
    pg = st.navigation(
        [
            architecture,   
            data_pipeline_etl,
            price_chart,
            ai_interpreter,
            full_analysis
        ],
        position="sidebar"
    )
    pg.run()