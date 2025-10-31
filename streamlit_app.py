import streamlit as st
from modules import config
import logging

# Validate required environment variables
is_valid, missing = config.validate_required_keys()
if not is_valid:
    st.error(f"❌ Missing required environment variables: {', '.join(missing)}")
    st.info("Please create a `.env` file with API keys. See README.md for setup instructions.")
    st.stop()  # Stop execution but keep UI visible
else:
    logging.info("streamlit_app.py: Environment variables validated successfully")

# Initialize centralized logging configuration - consistent logging format across all modules
config.setup_logging()

# Configure the main page
st.set_page_config(
    page_title="Trading Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Slack integration page
data_pipeline_etl = st.Page("pages/data_pipeline_etl.py", title="ETL")
architecture = st.Page("pages/app_architecture.py", title="Architecture")
price_chart = st.Page("pages/price_chart.py", title="Price Chart")
ai_interpreter = st.Page("pages/ai_interpreter.py", title="AI Interpreter")
full_analysis = st.Page("pages/full_analysis.py", title="Full Analysis")

# Create navigation with proper structure
# Each key represents a section in the sidebar navigation
# Each value is a list of pages under that section
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