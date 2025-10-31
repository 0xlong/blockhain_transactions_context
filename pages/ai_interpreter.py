import streamlit as st
import pandas as pd
from modules.ai_module import generate_transaction_summary

# Initialize session state variables
if 'transaction_summary' not in st.session_state:
    st.session_state.transaction_summary = None
if 'price_impact_df' not in st.session_state:
    st.session_state.price_impact_df = None
if 'price_chart' not in st.session_state:
    st.session_state.price_chart = None
if 'enriched_data_df' not in st.session_state:
    st.session_state.enriched_data_df = None
if 'chart' not in st.session_state:
    st.session_state.chart = None

if st.session_state.enriched_data_df is None:
    st.info("No data found. Please extract and transform data first in the ETL section.")
else:
    with st.expander("Transaction Context", expanded=True):
        
        with st.status("Transaction Details (enriched)"):
            if st.session_state.enriched_data_df is not None:
                st.dataframe(st.session_state.enriched_data_df, width='stretch', hide_index=True, height=495)
            else:
                st.info("No enriched data found. Please extract and transform data first in the ETL section.")
        
        with st.status("Price Chart"):
            if st.session_state.chart is not None:
                st.plotly_chart(st.session_state.chart, use_container_width=True)
            else:
                st.info("No price chart found. Please create a price chart first in the Price chart section.")
    
        with st.status("Price Impact"):
            if st.session_state.price_impact_df is not None:
                st.dataframe(st.session_state.price_impact_df.iloc[1:], width='stretch')
            else:
                st.info("No price impact data found. Please create a price impact first in the Price chart section.")

    if st.button("Generate AI Summary", type="primary", use_container_width=True):
        transaction_summary = generate_transaction_summary([st.session_state.price_impact_analysis,
                                                            st.session_state.token_name,
                                                            st.session_state.token_price,
                                                            st.session_state.token_address,
                                                            st.session_state.enriched_data_df])
        st.session_state.transaction_summary = transaction_summary

    # Display the summary with proper text formatting
    if st.session_state.transaction_summary is not None:
        with st.container(border=1):
            st.text(st.session_state.transaction_summary, width='stretch')