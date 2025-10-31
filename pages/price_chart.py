import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import plotly.graph_objects as go
from modules.moralis_data import get_token_address, fetch_ohlcv, get_best_pair_address

# Initialize session state variables
if 'chart' not in st.session_state:
    st.session_state.chart = None
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = None
if 'price_impact_analysis' not in st.session_state:
    st.session_state.price_impact_analysis = None
if 'price_impact_df' not in st.session_state:
    st.session_state.price_impact_df = None
if 'token_name' not in st.session_state:
    st.session_state.token_name = None
if 'token_address' not in st.session_state:
    st.session_state.token_address = None
if 'enriched_data' not in st.session_state:
    st.info("No data found. Please run the data pipeline extract and transform first in the Data pipeline section.")
    st.session_state.enriched_data = None

def create_price_chart(df, event_datetime, symbol, interval="1h"):
    """
    Create a simple price chart with OHLC data and a vertical line at transaction time.
    
    This is a basic, straightforward function that creates a candlestick chart
    with a single vertical line marking when a whale transaction occurred.
    Perfect for quick visualization without complex features.
    
    Args:
        df (pd.DataFrame): DataFrame containing OHLCV data with columns:
                          ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        event_datetime (dict): Dictionary containing event information with keys:
                                   ['timestamp', 'token_name', 'token_amount', 'value_token_usd', 'From', 'To', 'tx_url']
                                    This is where the vertical line will be drawn
        symbol (str): Token name for the chart title (e.g., 'PEPE', 'ETH')
        interval (str): Time interval for the chart data ('5m', '15m', '1h', '4h', '1d')
                       This is displayed in the chart title to show the candle timeframe
    
    Returns:
        plotly.graph_objects.Figure: Simple candlestick chart with transaction marker
    
    Example:
        # After getting df from OHLCV data and last_transaction from CSV
        df = pd.DataFrame(ohlcv_data)
        fig = create_price_chart(df, last_transaction, 'PEPE', '1h')
        st.plotly_chart(fig, use_container_width=True)
    """
    # Step 1: Convert all price columns to numeric format
    # This ensures we can plot the data without type errors
    # errors='coerce' means invalid values become NaN instead of raising errors
    df['open'] = pd.to_numeric(df['open'], errors='coerce')
    df['high'] = pd.to_numeric(df['high'], errors='coerce')
    df['low'] = pd.to_numeric(df['low'], errors='coerce')
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # Step 2: Convert timestamp column to datetime format
    # This allows Plotly to properly display time on the x-axis
    # Use utc=True to ensure consistent timezone handling
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
    
    # Step 2.5: Extract transaction data from event_datetime dictionary
    # event_datetime contains {'timestamp': '...', 'token_name': '...'}
    # We extract these values so we can use them in the chart annotations
    transaction_timestamp_str = event_datetime.get('timestamp', '')
    token_name = event_datetime.get('token_name', symbol)
    
    # Convert timestamp string to datetime object for fig.add_vline
    # This ensures the timestamp is in the correct format for Plotly
    # Use utc=True to match the dataframe timestamp format
    if transaction_timestamp_str:
        transaction_timestamp = pd.to_datetime(transaction_timestamp_str, utc=True)
    else:
        transaction_timestamp = None
    
    # Step 3: Create a new empty figure to hold our chart
    # This is the canvas we'll draw on
    fig = go.Figure()

    # Step 4: Add candlestick chart to the figure
    # Each candle shows: open, high, low, close prices for a time period
    # Green candles = price went up, Red candles = price went down
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],                      # Time data for x-axis
            open=df['open'],                        # Price at period start
            high=df['high'],                        # Highest price in period
            low=df['low'],                          # Lowest price in period
            close=df['close'],                      # Price at period end
            name=symbol,                            # Name shown in legend
            increasing_line_color='green',          # Color for up candles
            decreasing_line_color='red'             # Color for down candles
        )
    )

    # Step 5: Add vertical line at the exact transaction timestamp
    # This marks when the whale transaction occurred on the chart

    if transaction_timestamp is not None:
        
        fig.add_vline(
            x=transaction_timestamp.timestamp() * 1000 - 2*60*60*1000,  # subtract 2 hours in milliseconds cause conversion to utc shifts the time by 2 hours
            line_dash="dash",                                           # Dashed style for clarity    
            line_color="yellow",                                        # Yellow color
            line_width=2,                                               # Make line visible
            annotation_text=str(token_name).upper() + " event",         # Label for the line (safe concatenation)
            annotation_position="top"                                   # Put label at top of chart
        )

    # Step 6: Configure the chart layout and styling
    # This sets the title, size, and overall appearance
    # The title includes the symbol, interval, and transaction info
    # Build title string safely by concatenating validated string components
    chart_title = str(symbol).upper() + " Price (" + interval.upper() + " timeframe)"
    #chart title in the center of the chart with text and padding
    fig.update_layout(
        title=chart_title,                          # Chart title with all components
        height=500,                                 # Chart height in pixels
        xaxis_title="Time (UTC)",                         # Label for x-axis
        yaxis_title="Price (USD)",                  # Label for y-axis
        template='plotly_white',                    # Clean white background
        xaxis_rangeslider_visible=False,            # Hide extra slider at bottom
        hovermode='x unified'                       # Show all data on hover
    )

    return fig

def create_chart_with_recent_whale_activity(token_name, event_data=None, selected_interval="5m"):
    """
    Create a price chart using Moralis OHLCV data with whale transaction markers.
    
    This function fetches OHLCV data from Moralis API for the specified token and time interval,
    then creates a candlestick chart with vertical lines marking whale transaction events.
    The function handles data fetching, transformation, and chart creation in one place.
    
    Args:
        token_name (str): Token symbol to fetch data for (e.g., 'PEPE', 'ETH', 'BTC')
        event_data (dict, optional): Dictionary containing event timestamps to mark on chart
        selected_interval (str): Time interval for OHLCV data ('5m', '15m', '1h')
    
    Returns:
        plotly.graph_objects.Figure or None: Returns the chart figure if successful, None if error
    """
    try:
        # Convert interval format from UI to Moralis API format
        # Moralis uses different format than our UI (5m -> 5min, 1h -> 1h)
        interval_mapping = {
            "5m": "5min",
            "30m": "30min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        moralis_interval = interval_mapping.get(selected_interval, "5min")
        
        # Get current timestamp for 'to_date' parameter
        # Moralis API requires both from_date and to_date parameters
        # Convert string timestamp to datetime object, then back to expected string format
        # The to_date parameter represents the event timestamp (transaction time)
        # The function will calculate the actual date range internally using hours_before_transaction and hours_after_transaction
        event_timestamp = pd.to_datetime(event_data['Timestamp']).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Calculate from_date by subtracting hours_before_transaction from event timestamp
        # This is required because fetch_ohlcv() expects both from_date and to_date as required parameters
        # Even though the function recalculates them internally, Python requires them to be provided
        hours_before = 24  # Get 24 hours of data before transaction
        hours_after = 24   # Get 24 hours of data after transaction
        
        # Convert event timestamp to datetime object for date arithmetic
        event_dt = pd.to_datetime(event_data['Timestamp'])
        
        # Calculate from_date by subtracting hours_before from event timestamp
        # This represents the start of our data range
        from_date = (event_dt - timedelta(hours=hours_before)).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Use event timestamp as to_date (the function will add hours_after internally)
        to_date = event_timestamp

    
        # Fetch OHLCV data using Moralis API
        ohlcv_data = fetch_ohlcv(
            token_symbol=token_name,
            timeframe=moralis_interval,
            from_date=from_date,  # Start date: event timestamp minus hours_before_transaction
            to_date=to_date,      # Event timestamp: transaction time (function adds hours_after internally)
            chain="eth",
            hours_before_transaction=hours_before,  # Get 24 hours of data before transaction 
            hours_after_transaction=hours_after,    # Get 24 hours of data after transaction
            limit=1000  # Maximum data points for 5min intervals (24h * 12 = 288)
        )
             
        # Check if we received valid OHLCV data
        if not ohlcv_data or len(ohlcv_data) == 0:
            st.error(f"No OHLCV data found for {token_name}. Please check the token symbol.")
            return
        
        # Convert Moralis OHLCV data to pandas DataFrame
        # Moralis returns list of dictionaries with OHLCV data
        df = pd.DataFrame(ohlcv_data)
        
        # df[timestamp] is in ISO format, convert to format 2025-10-20 10:51:47 UTC
        # Use .dt accessor to apply strftime to each datetime element in the Series
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Ensure all price columns are numeric for proper charting
        # Convert string values to float and handle any invalid data gracefully
        price_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in price_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        
        # Prepare event data for the chart if transaction data is provided
        # Convert last_transaction format to the format expected by create_simple_price_chart
        chart_event_data = None
        if event_data:
            # Extract timestamp and token name from the transaction data
            # create_simple_price_chart expects a dict with 'timestamp' and 'token_name' keys
            chart_event_data = {
                'timestamp': event_data.get('Timestamp', ''),  # Transaction timestamp (not in a list)
                'token_name': token_name  # Token symbol being charted (e.g., 'PEPE')
            }

        # Create the candlestick chart using the new create_simple_price_chart function
        fig = create_price_chart(
            df=df,
            symbol=token_name,
            event_datetime=chart_event_data,
            interval=selected_interval
        )
        
        # Return the chart figure so it can be used in conditional logic
        # The calling code will handle displaying the chart
        return df, fig
        
    except Exception as e:
        # Handle any errors during data fetching or chart creation
        # Provide clear error message to help users understand what went wrong
        st.error(f"Error creating chart for {token_name}: {str(e)}")
        return None

def calculate_price_impact(ohlcv_data, event_timestamp, output_file="price_impact_analysis.json"):
    """
    Calculate price impact (returns) at different time horizons after a whale transaction event.
    
    This function analyzes how the price of a token changes after a significant whale transaction
    by calculating percentage returns at 1h, 2h, 4h, 8h, and 12h intervals after the event.
    
    Args:
        ohlcv_data (list or pd.DataFrame): OHLCV data containing price information
                                          Can be a list of dictionaries or pandas DataFrame
        event_timestamp (str): Timestamp of the whale transaction event in ISO format
                              Example: "2025-10-20T10:51:47.000Z"
        output_file (str): Path where to save the JSON results file
                          Default: "price_impact_analysis.json"
    
    Returns:
        dict: Dictionary containing price impact analysis with keys:
              - event_timestamp: Original event timestamp
              - event_price: Price at the time of the event
              - time_horizons: Dictionary with returns for each time period
              - analysis_metadata: Additional information about the analysis
    
    Example:
        # Load OHLCV data and calculate price impact
        with open('data/prices/ohlc/ohlcv_data_PEPE_1h.json', 'r') as f:
            ohlcv_data = json.load(f)
        
        results = calculate_price_impact(
            ohlcv_data=ohlcv_data,
            event_timestamp="2025-10-20T10:51:47.000Z",
            output_file="data/price_impact_PEPE.json"
        )
    """
    try:
        # Step 1: Convert OHLCV data to pandas DataFrame if it's not already
        # This ensures we can work with the data using pandas methods
        if isinstance(ohlcv_data, list):
            df = pd.DataFrame(ohlcv_data)
        else:
            df = ohlcv_data.copy()
        
        # Step 2: Convert timestamp column to datetime format for proper time calculations
        # This allows us to perform time-based operations on the data
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        
        # Step 3: Convert event timestamp to datetime for comparison
        # This is the exact moment when the whale transaction occurred
        event_dt = pd.to_datetime(event_timestamp, utc=True)
        
        # Step 4: Find the price at the time of the event
        # We look for the closest candle to the event timestamp
        # This gives us the baseline price to calculate returns from
        event_price = None
        closest_candle = None
        
        # Find the candle that contains or is closest to the event timestamp
        # We look for candles where the event time falls within the candle's time range
        for idx, row in df.iterrows():
            candle_start = row['timestamp']
            # For hourly candles, the next candle starts exactly 1 hour later
            candle_end = candle_start + timedelta(hours=1)
            
            # Check if event timestamp falls within this candle's time range
            if candle_start <= event_dt < candle_end:
                event_price = row['close']  # Use close price as the event price
                closest_candle = row
                break
        
        # If no exact match found, find the closest candle by time difference
        if event_price is None:
            # Calculate time differences and find the minimum
            df['time_diff'] = abs(df['timestamp'] - event_dt)
            closest_idx = df['time_diff'].idxmin()
            closest_candle = df.loc[closest_idx]
            event_price = closest_candle['close']
        
        # Step 5: Define the time horizons we want to analyze
        # These represent how long after the event we want to measure price impact
        time_horizons = {
            '1h': 1,    # 1 hour after event
            '2h': 2,    # 2 hours after event  
            '4h': 4,    # 4 hours after event
            '8h': 8,    # 8 hours after event
            '12h': 12   # 12 hours after event
        }
        
        # Step 6: Calculate price impact for each time horizon
        # Price impact = (Price at horizon - Event price) / Event price * 100
        # This gives us the percentage change in price after the event
        results = {
            'event_timestamp': event_timestamp,
            'event_price': float(event_price), #round to 2 decimal places
            'event_price_impact': {},
        }
        
        # Calculate returns for each time horizon
        for horizon_name, hours_after in time_horizons.items():
            # Calculate the target timestamp (event time + horizon hours)
            target_time = event_dt + timedelta(hours=hours_after)
            
            # Find the candle closest to the target time
            # This gives us the price at the specified time after the event
            df['target_time_diff'] = abs(df['timestamp'] - target_time)
            closest_target_idx = df['target_time_diff'].idxmin()
            target_candle = df.loc[closest_target_idx]
            target_price = target_candle['close']
            
            # Calculate percentage return: (New Price - Old Price) / Old Price * 100
            # Positive return = price went up, Negative return = price went down
            price_return = ((target_price - event_price) / event_price) * 100
            
            # Store the results for this time horizon
            results['event_price_impact'][horizon_name] = {
                'hours_after_event': hours_after,
                'impact_timestamp': target_candle['timestamp'].strftime("%Y-%m-%d %H:%M:%S UTC"),
                'impact_price': float(target_price),
                'impact_return_percent': round(price_return, 2),  # Round to 4 decimal places
                'impact_change_absolute': float(target_price - event_price)
            }
        
        # Step 7: Save results to JSON file
        # This allows us to persist the analysis for later use or sharing
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Step 8: Return the results dictionary
        # This allows the calling code to use the results immediately
        return results
        
    except Exception as e:
        # Handle any errors during the calculation process
        # Provide detailed error information to help with debugging
        error_message = f"Error calculating price impact: {str(e)}"
        print(error_message)
        
        # Return error information in the same format as successful results
        return {
            'error': error_message,
            'event_timestamp': event_timestamp,
            'time_horizons': {},
            'analysis_metadata': {
                'error_occurred': True,
                'analysis_timestamp': datetime.now().isoformat()
            }
        }

# MAIN
# Page configuration
st.set_page_config(layout="wide")

# Check if we have any transaction data to work with
if st.session_state.enriched_data is not None:
    with st.container(border=1):
        st.markdown(f"""
        **Token:** 
        - **Token Name:** {str(st.session_state.token_name).upper()}
        - **Token Address:** {st.session_state.token_address}
        """, unsafe_allow_html=True)

    last_transaction = st.session_state.enriched_data
    st.session_state.last_transaction = last_transaction
    with st.container(border=1):
        st.markdown(f"""
    **Transaction Details:**
    - **From:** {last_transaction['From']}
    - **To:** {last_transaction['To']}
    - **Value (token):** {last_transaction['Value (token)']}
    - **Value (USD):** ${last_transaction['Value (USD)']}
    - **Timestamp:** {last_transaction['Timestamp']}
    - **Transaction Hash:** {last_transaction['Transaction Hash']}
    """, unsafe_allow_html=True)

    if st.session_state.token_name:
        if st.button("Create Price Chart", type="primary", use_container_width=True):
            with st.spinner("Creating price chart..."):
                chart = create_chart_with_recent_whale_activity(
                    token_name=st.session_state.token_name, 
                    event_data=last_transaction,
                    selected_interval="1h")

                if chart:
                    st.session_state.chart = chart[1]  # Store the figure object
                    st.session_state.chart_data = chart[0]  # Store the dataframe with price data
                    with st.container(border=1):
                        st.plotly_chart(chart[1], use_container_width=True)  # Pass only the figure object
                else:
                    st.error("Error creating chart")
                
                # Calculate price impact
                with st.status("Price Data"):
                    st.dataframe(st.session_state.chart_data)

                with st.status("Price Impact"):
                    results = calculate_price_impact(
                        ohlcv_data=st.session_state.chart_data,
                        event_timestamp=last_transaction['Timestamp'],
                        output_file="data/price_impact_analysis_" + st.session_state.token_name + ".json")

                    if results:
                        st.session_state.price_impact_analysis = results
                        # dataframe with event_price_impact as a dataframe with hours dates and returns, skip first row
                        price_impact_df = pd.DataFrame(st.session_state.price_impact_analysis['event_price_impact'])
                        price_impact_df.index = ['Hours After Event (h)', 'Impact Timestamp (UTC)', 'Impact Price (USD)', 'Impact Return (%)', 'Impact Change (USD)']
                        price_impact_df.columns = ['1h after event', '2h after event', '4h after event', '8h after event', '12h after event']
                        st.dataframe(price_impact_df.iloc[1:], width='stretch')
                        st.session_state.price_impact_df = price_impact_df
                    else:
                        st.error(f"Error in price impact analysis: {st.session_state.price_impact_analysis['error']}")
else:
    st.info("No data found. Please extract and transform data first in the ETL section.")