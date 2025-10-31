import streamlit as st
import pandas as pd
from datetime import datetime
import json
import plotly.graph_objects as go
from modules.config import REPORTS_DIR

# Generate markdown report function
def generate_markdown_report():
    """
    Generate a comprehensive markdown report with all available data
    """
    # Create reports directory if it doesn't exist
    # Using pathlib.Path ensures cross-platform compatibility
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    # Using pathlib.Path to build the file path safely
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = REPORTS_DIR / f"{st.session_state.token_name.upper()}_analysis_report_{timestamp}.md"
    
    # Start building the markdown content
    markdown_content = f"""
    ## Whale Alert Analysis Report

    ## Asset Information
    - **Token Name:** {st.session_state.token_name}
    - **Token Address:** {st.session_state.token_address}
    - **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    ## Latest Transaction Details
    """
        
        # Add transaction details if available

    markdown_content += f"""
    ### Transaction Information
    - **From:** {st.session_state.enriched_data.get('From', 'N/A')}
    - **To:** {st.session_state.enriched_data.get('To', 'N/A')}
    - **Value (Token):** {st.session_state.enriched_data.get('Value (token)', 'N/A')}
    - **Value (USD):** ${st.session_state.enriched_data.get('Value (USD)', 'N/A')}
    - **Timestamp:** {st.session_state.enriched_data.get('Timestamp', 'N/A')}
    - **Transaction Hash:** {st.session_state.enriched_data.get('Transaction Hash', 'N/A')}

    ### Enriched Metadata
    - **From Net Worth:** {st.session_state.enriched_data.get('From_Net_Worth', 'N/A')}
    - **From ENS Domain:** {st.session_state.enriched_data.get('From_ENS_Domain', 'N/A')}
    - **From Unstoppable Domain:** {st.session_state.enriched_data.get('From_Unstoppable_Domain', 'N/A')}
    - **To Net Worth:** {st.session_state.enriched_data.get('To_Net_Worth', 'N/A')}
    - **To ENS Domain:** {st.session_state.enriched_data.get('To_ENS_Domain', 'N/A')}
    - **To Unstoppable Domain:** {st.session_state.enriched_data.get('To_Unstoppable_Domain', 'N/A')}
    """
        
    # Add AI analysis if available
    if st.session_state.transaction_summary:
        markdown_content += f"""
    ## AI Analysis
    {st.session_state.transaction_summary}
    """

    # Write the report to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filename

# Initialize session state variables
if 'enriched_transactions' not in st.session_state:
    st.session_state.enriched_transactions = None
if 'chart' not in st.session_state:
    st.session_state.chart = None
if 'price_impact_df' not in st.session_state:
    st.session_state.price_impact_df = None
if 'transaction_summary' not in st.session_state:
    st.session_state.transaction_summary = None
    
# MAIN
# Page configuration
st.set_page_config(layout="wide")

# Main logic - display transaction data and create price chart
# Check if we have any transaction data to work with
if st.session_state.enriched_data is not None:

    with st.container(border=1):
        st.markdown(f"""
        **Asset:** 
        - **Token Name:** {st.session_state.token_name}
        - **Token Address:** {st.session_state.token_address}
        """, unsafe_allow_html=True)

    # Display transaction details in a formatted container
    with st.status("Transaction Details", expanded=True):
        st.markdown(f"""
        - **From:** {st.session_state.enriched_data['From']}
        - **To:** {st.session_state.enriched_data['To']}
        - **Value (token):** {st.session_state.enriched_data['Value (token)']}
        - **Value (USD):** ${st.session_state.enriched_data['Value (USD)']}
        - **Timestamp:** {st.session_state.enriched_data['Timestamp']}
        - **Transaction Hash:** {st.session_state.enriched_data['Transaction Hash']}
        """, unsafe_allow_html=True)

    with st.status("Enriched Transaction Details"):
        st.markdown(f"""
        - **Sender Net Worth:** {st.session_state.enriched_data['From_Net_Worth']} USD
        - **Sender ENS Domain:** {st.session_state.enriched_data['From_ENS_Domain']}
        - **Sender Unstoppable Domain:** {st.session_state.enriched_data['From_Unstoppable_Domain']}
        - **Receiver Net Worth:** {st.session_state.enriched_data['To_Net_Worth']} USD
        - **Receiver ENS Domain:** {st.session_state.enriched_data['To_ENS_Domain']}
        - **Receiver Unstoppable Domain:** {st.session_state.enriched_data['To_Unstoppable_Domain']}
        """, unsafe_allow_html=True)

    if st.session_state.chart is not None:
        with st.status("Price chart"):
            st.plotly_chart(st.session_state.chart, use_container_width=True)

    if st.session_state.price_impact_df is not None:
        with st.status("Price impact"):
            st.dataframe(st.session_state.price_impact_df)

    # AI interpreter
    with st.status("AI interpreter"):
        if st.session_state.transaction_summary is not None:
            st.text(st.session_state.transaction_summary)
        else:
            st.info("No transaction summary found. Please generate a transaction summary first in the AI interpreter section.")

    # Generate report button
    if st.button("Generate report", type="primary", use_container_width=True):
        if st.session_state.token_name:
            with st.status("Full Transaction Report", expanded=True):
                try:
                    with st.spinner("Generating report..."):
                        report_path = generate_markdown_report()
                        st.write(f"📄 Report saved to: `{report_path}`")
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
