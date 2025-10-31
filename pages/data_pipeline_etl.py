import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
from modules import config
from modules.config import CSV_DIR

from modules.etherscan_data import etherscan_data_extract_token_transactions, etherscan_data_transform
from modules.moralis_data import moralis_data_extract_token_transactions, moralis_data_transform, get_token_address, get_token_price
from modules.infura_data import infura_data_extract_token_transactions, infura_data_transform
from modules.alchemy_data import alchemy_data_extract_token_transactions, alchemy_data_transform
from modules.transactions_context import get_etherface_signature_description, get_4bytes_signature_description, get_etherscan_transaction_method_selector, get_address_ens_domain_moralis, get_address_networth_moralis, get_address_unstoppable_domain_moralis

#PAGE CONFIG
st.set_page_config(layout="wide")

# Initialize session state variables only if they don't exist yet
# This prevents resetting data on every page rerun (which happens on button clicks)
if 'api_summary_data' not in st.session_state:
    st.session_state.api_summary_data = None
if 'enriched_data' not in st.session_state:
    st.session_state.enriched_data = None
if 'enriched_data_df' not in st.session_state:
    st.session_state.enriched_data_df = None
if 'token_address' not in st.session_state:
    st.session_state.token_address = None
if 'token_price' not in st.session_state:
    st.session_state.token_price = None
if 'token_price_24hr_change' not in st.session_state:
    st.session_state.token_price_24hr_change = None

with st.expander("Data Pipeline - Extract", expanded=True):
    # Create form container for better organization
    with st.container(border=1):
        
        token_name = st.text_input(
            "Token Symbol",
            value="PEPE",
            help="Enter the symbol of the token you want to extract data for. Must match Coingecko symbols."
        )
        st.session_state.token_name = token_name
        if st.session_state.token_name not in st.session_state:
            with st.spinner("Getting token information..."):
                st.session_state.token_address = get_token_address(token_name)
                token_price_info = get_token_price(st.session_state.token_address)
                st.session_state.token_price = token_price_info[0]
                st.session_state.token_price_24hr_change = token_price_info[1]
                st.markdown(f":blue-badge[Token Address: {st.session_state.token_address}] \
                                :grey-badge[Token Price: {st.session_state.token_price} USD] \
                                :orange-badge[24hr change: {st.session_state.token_price_24hr_change} %]",
                                unsafe_allow_html=True)

    with st.container(border=True):
        # options to choose from datasource - etherscan, alchemy, arkham api
        datasource = st.multiselect(
            "Data Source (APIs)",
            options=["Etherscan API", "Alchemy API", "Infura API", "Moralis API"],
            default=["Etherscan API", "Alchemy API", "Infura API", "Moralis API"]
        )

    # Submit button
    submitted = st.button(
        "Collect API data",
        type="primary",
        width='stretch'
    )

    if submitted:
        # Initialize variables to avoid NameError
        moralis_data = None
        etherscan_data = None
        alchemy_transactions = None
        infura_transactions = None

        columns = st.columns(4)
        with columns[0]:
            with st.status("Moralis API"):
                moralis_data = moralis_data_extract_token_transactions(
                    token_address=st.session_state.token_address,
                    moralis_api_key=config.MORALIS_API_KEY,
                    max_transactions=1
                )
                if moralis_data:
                    moralis_data = moralis_data_transform(moralis_data)
                    st.session_state.moralis_data = moralis_data
                    st.write("Moralis API - ", moralis_data[0]['blockTimestamp'])
                    # moralis_data[0] is a dictionary and we need to show it as dataframe but transposed
                    st.dataframe(pd.DataFrame([moralis_data[0]]).T)
                else:
                    st.write("Moralis API - No data found")
    
        with columns[1]:
            #ETHERSCAN API
            with st.status("Etherscan API", ):
                etherscan_data = etherscan_data_extract_token_transactions(
                    token_address=st.session_state.token_address,
                    max_transactions=1,  # Maximum number of transfers to return
                    etherscan_api_key=config.ETHERSCAN_API_KEY
                )
                if etherscan_data:
                    etherscan_data = etherscan_data_transform(etherscan_data)
                    st.session_state.etherscan_data = etherscan_data
                    st.write("Etherscan API - ", etherscan_data[0]['blockTimestamp'])
                    st.dataframe(pd.DataFrame([etherscan_data[0]]).T)
                else:
                    st.write("Etherscan API - No data found")
        
        with columns[2]:
            with st.status("Alchemy API"):
                alchemy_transactions = alchemy_data_extract_token_transactions(
                    token_address=st.session_state.token_address,
                    max_transactions=1,  # Maximum number of transfers to return
                    alchemy_api_key=config.ALCHEMY_API_KEY
                )
                if alchemy_transactions:
                    alchemy_transactions = alchemy_data_transform(alchemy_transactions)
                    st.session_state.alchemy_transactions = alchemy_transactions
                    st.write("Alchemy API - ", alchemy_transactions[0]['blockTimestamp'])
                    st.dataframe(pd.DataFrame([alchemy_transactions[0]]).T)
                else:
                    st.write("Alchemy API - No data found")

        with columns[3]:
            with st.status("Infura API"):
                infura_transactions = infura_data_extract_token_transactions(
                    token_address=st.session_state.token_address,
                    max_transactions=1,  # Maximum number of transfers to return
                    infura_api_key=config.INFURA_API_KEY
                )
                if infura_transactions:
                    infura_transactions = infura_data_transform(infura_transactions)
                    st.session_state.infura_transactions = infura_transactions
                    st.write("Infura API - ", infura_transactions[0]['blockTimestamp'])
                    st.dataframe(pd.DataFrame([infura_transactions[0]]).T)
                else:
                    st.write("Infura API - No data found")

        # Create summary dataframe only after data extraction is complete
        # Simple summary dataframe using existing variables
        
        api_summary_data = pd.DataFrame({
            'API': ['Moralis', 'Etherscan', 'Alchemy', 'Infura'],
            'Timestamp': [
                moralis_data[0]['blockTimestamp'] if moralis_data else 'No Data',
                etherscan_data[0]['blockTimestamp'] if etherscan_data else 'No Data', 
                alchemy_transactions[0]['blockTimestamp'] if alchemy_transactions else 'No Data',
                infura_transactions[0]['blockTimestamp'] if infura_transactions else 'No Data'
            ],
            'From': [
                moralis_data[0]['fromAddress'] if moralis_data else 'No Data',
                etherscan_data[0]['fromAddress'] if etherscan_data else 'No Data',
                alchemy_transactions[0]['fromAddress'] if alchemy_transactions else 'No Data', 
                infura_transactions[0]['fromAddress'] if infura_transactions else 'No Data'
            ],
            'To': [
                moralis_data[0]['toAddress'] if moralis_data else 'No Data',
                etherscan_data[0]['toAddress'] if etherscan_data else 'No Data',
                alchemy_transactions[0]['toAddress'] if alchemy_transactions else 'No Data',
                infura_transactions[0]['toAddress'] if infura_transactions else 'No Data'
            ],
            'Value (token)': [
                moralis_data[0]['transferAmountFormatted'] if moralis_data else 'No Data',
                etherscan_data[0]['transferAmountFormatted'] if etherscan_data else 'No Data',
                alchemy_transactions[0]['transferAmountFormatted'] if alchemy_transactions else 'No Data',
                infura_transactions[0]['transferAmountFormatted'] if infura_transactions else 'No Data'
            ],
            'Value (USD)': [
                float(moralis_data[0]['transferAmountFormatted'].replace(',', '')) * st.session_state.token_price if moralis_data else 'No Data',
                float(etherscan_data[0]['transferAmountFormatted'].replace(',', '')) * st.session_state.token_price if etherscan_data else 'No Data',
                float(alchemy_transactions[0]['transferAmountFormatted'].replace(',', '')) * st.session_state.token_price if alchemy_transactions else 'No Data',
                float(infura_transactions[0]['transferAmountFormatted'].replace(',', '')) * st.session_state.token_price if infura_transactions else 'No Data'
            ],
            'Transaction Hash': [
                moralis_data[0]['transactionHash'] if moralis_data else 'No Data',
                etherscan_data[0]['transactionHash'] if etherscan_data else 'No Data',
                alchemy_transactions[0]['transactionHash'] if alchemy_transactions else 'No Data',
                infura_transactions[0]['transactionHash'] if infura_transactions else 'No Data'
            ]

        })

        with st.status("API Summary"):
            # sort summary data by timestamp
            api_summary_data = api_summary_data.sort_values(by='Timestamp', ascending=False)
            # save summary data to csv and session state
            # Using pathlib.Path from config ensures cross-platform compatibility
            csv_path = CSV_DIR / f"api_summary_{st.session_state.token_name}.csv"
            api_summary_data.to_csv(csv_path, index=False)
            st.session_state.api_summary_data = api_summary_data
            st.dataframe(api_summary_data, width='stretch', hide_index=True)


# Data Pipeline - Transform

# get the last transaction
if st.session_state.api_summary_data is not None:
    last_transaction = st.session_state.api_summary_data.iloc[0]

    with st.expander("Data Pipeline - Transform"):
        enriched_data = last_transaction.to_dict()
        with st.container(border=True):
            st.write("Last Transaction Data:")
            
            # Convert the last transaction to a DataFrame for better display
            # Create a DataFrame with the transaction data in a key-value format
            transaction_df = pd.DataFrame({
                'Field': ['Timestamp', 'From', 'To', 'Value (token)', 'Value (USD)', 'Transaction Hash'],
                'Value': [
                    last_transaction['Timestamp'],
                    last_transaction['From'],
                    last_transaction['To'],
                    last_transaction['Value (token)'],
                    last_transaction['Value (USD)'],
                    last_transaction['Transaction Hash']
                ]
            })
            
            # Display the DataFrame with better formatting
            st.dataframe(
                transaction_df, 
                width='stretch', 
                hide_index=True,
                column_config={
                    "Field": st.column_config.TextColumn("Field", width="medium"),
                    "Value": st.column_config.TextColumn("Value", width="large")
                }
            )
    
        if st.button("Enrich Transaction Data", type="primary", width='stretch'):

            # Loop through each attribute of the transaction and enrich it
            for attribute, value in last_transaction.items():
                with st.status(attribute):
                    st.info(f"{attribute}: {value}")
                    if attribute == 'From':
                        # Get ENS domain name associated with the address
                        from_ens = get_address_ens_domain_moralis(value)
                        st.write("ENS Domain:", from_ens)
                        enriched_data['From_ENS_Domain'] = from_ens

                        # Get the net worth of the address
                        from_networth = get_address_networth_moralis(value)
                        st.write("Net Worth:", from_networth)
                        enriched_data['From_Net_Worth'] = from_networth
                        
                        # Get Unstoppable Domain (UD) associated with the address
                        from_ud = get_address_unstoppable_domain_moralis(value)
                        st.write("Unstoppable Domain (UD):", from_ud)
                        enriched_data['From_Unstoppable_Domain'] = from_ud
                        #st.write("Metasleuth addresses nametags:", get_metasleuth_addresses_nametags(value))
                    
                    # Enrich 'To' address with various data sources
                    elif attribute == 'To':
                        # Get ENS domain name associated with the address
                        to_ens = get_address_ens_domain_moralis(value)
                        st.write("ENS Domain:", to_ens)
                        enriched_data['To_ENS_Domain'] = to_ens
                        
                        # Get the net worth of the address
                        to_networth = get_address_networth_moralis(value)
                        st.write("Net Worth:", to_networth)
                        enriched_data['To_Net_Worth'] = to_networth
                        
                        # Get Unstoppable Domain (UD) associated with the address
                        to_ud = get_address_unstoppable_domain_moralis(value)
                        st.write("Unstoppable Domain (UD):", to_ud)
                        enriched_data['To_Unstoppable_Domain'] = to_ud
                        #st.write("Metasleuth addresses nametags:", get_metasleuth_addresses_nametags(value))
                    
                    # Enrich 'Transaction Hash' with method signature descriptions
                    elif attribute == 'Transaction Hash':
                        # First, get the method selector from the transaction
                        method_selector = get_etherscan_transaction_method_selector(value)
                        
                        # Get human-readable method description from Etherface
                        etherface_desc = get_etherface_signature_description(method_selector)
                        st.write("Etherface method description:", etherface_desc)
                        enriched_data['Method_Description_Etherface'] = etherface_desc
                        
                        # Get human-readable method description from 4bytes.directory
                        fourbytes_desc = get_4bytes_signature_description(method_selector)
                        st.write("4bytes.directory method description:", fourbytes_desc)
                        enriched_data['Method_Description_4bytes'] = fourbytes_desc
            
            # save enriched data to session state
            st.session_state.enriched_data = enriched_data

            # Convert the enriched data dictionary to a DataFrame with arguments as columns
            # Each key in enriched_data becomes a column, each value becomes a row
            enriched_df = pd.DataFrame([st.session_state.enriched_data])
            # Using pathlib.Path from config ensures cross-platform compatibility
            csv_path = CSV_DIR / f"enriched_transaction_metadata_{st.session_state.token_name}.csv"
            enriched_df.to_csv(csv_path, mode='w', index=False)
            enriched_df = enriched_df.T.reset_index()
            enriched_df.columns = ['Metadata', 'Values']
            
            if st.session_state.enriched_data is not None:
                with st.status("Enriched Transaction Data"):
                    st.dataframe(enriched_df, width='stretch', hide_index=True)
            else:
                st.warning("No enriched data found")

elif submitted and st.session_state.api_summary_data is None:
    st.warning("No API summary data found")

# Data Pipeline - Load
if st.session_state.enriched_data is not None:
    with st.expander("Data Pipeline - Load", expanded=False):
        # enriched_data as a dataframe
        enriched_data_df = pd.DataFrame({
                'Field': ['Timestamp', 'From', 'To', 'Value (token)', 'Value (USD)', 'Transaction Hash', 'From_ENS_Domain', 'From_Net_Worth', 'From_Unstoppable_Domain', 'To_ENS_Domain', 'To_Net_Worth', 'To_Unstoppable_Domain', 'Method_Description_Etherface', 'Method_Description_4bytes'],
                'Value': [
                    st.session_state.enriched_data['Timestamp'],
                    st.session_state.enriched_data['From'],
                    st.session_state.enriched_data['To'],
                    st.session_state.enriched_data['Value (token)'],
                    st.session_state.enriched_data['Value (USD)'],
                    st.session_state.enriched_data['Transaction Hash'],
                    st.session_state.enriched_data['From_ENS_Domain'],
                    st.session_state.enriched_data['From_Net_Worth'],
                    st.session_state.enriched_data['From_Unstoppable_Domain'],
                    st.session_state.enriched_data['To_ENS_Domain'],
                    st.session_state.enriched_data['To_Net_Worth'],
                    st.session_state.enriched_data['To_Unstoppable_Domain'], 
                    st.session_state.enriched_data['Method_Description_Etherface'],
                    st.session_state.enriched_data['Method_Description_4bytes']
                ]
            })
            
        st.session_state.enriched_data_df = enriched_data_df
        st.dataframe(enriched_data_df, width='stretch', hide_index=True, height=530)
