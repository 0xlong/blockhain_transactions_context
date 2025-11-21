#### **Typical User Workflow**
1. **Start with Architecture** → Understand the system capabilities
2. **Move to ETL Pipeline** → Extract and enrich transaction data
3. **Analyze with Price Chart** → Visualize price impact and market reaction
4. **Get AI Insights** → Generate intelligent analysis and interpretation
5. **Create Full Analysis** → Compile comprehensive report with all findings

#### 1. **Architecture** Page
System overview and technical documentation

#### 2. **ETL** Page
**Purpose**: Data extraction, transformation, and loading

**User Flow:**
1. **Enter Token Information**
   - User inputs token symbol (e.g., "PEPE", "ETH", "BTC")
   - System automatically fetches and displays:
     - Token address
     - Current token price
     - 24-hour price change  

2. **Select Data Sources**
   - User chooses from available APIs:
     - Etherscan API
     - Alchemy API
     - Infura API
     - Moralis API
   - Can select multiple sources for redundancy

3. **Extract Data**
   - User clicks "Collect API data" button
   - System fetches transaction data from selected APIs
   - Shows real-time status for each API call
   - Displays latest transaction details from each source

4. **View API Summary**
   - User sees consolidated summary table
   - Compares data across different APIs
   - Identifies most recent transaction

5. **Transform Data (Enrichment)**
   - User clicks "Enrich Transaction Data" button
   - System adds metadata to transaction:
     - ENS domains for addresses
     - Net worth information
     - Unstoppable domains
     - Method signature descriptions
   - Shows progress for each enrichment step

6. **Load Final Data**
   - User views complete enriched transaction data
   - All metadata is displayed in structured format
   - Data is saved to CSV files for further analysis

#### 3. **Price Chart** Page
**Purpose**: Interactive price analysis with transaction impact

**User Flow:**
1. **View Transaction Context**
   - User sees token information and transaction details
   - Displays from/to addresses, value, timestamp, and transaction hash

2. **Create Price Chart**
   - User clicks "Create Price Chart" button
   - System fetches OHLCV data for 24 hours before and after transaction
   - Creates interactive candlestick chart with:
     - Price movement visualization
     - Vertical line marking transaction time
     - Transaction event annotation

3. **Analyze Price Data**
   - User views raw OHLCV data in table format
   - Can examine price movements around transaction time

4. **Calculate Price Impact**
   - System automatically calculates price impact at multiple time horizons:
     - 1 hour after transaction
     - 2 hours after transaction
     - 4 hours after transaction
     - 8 hours after transaction
     - 12 hours after transaction
   - Shows percentage returns and absolute price changes

5. **View Results**
   - User sees comprehensive price impact analysis
   - Data is saved to JSON file for future reference

#### 4. **AI Interpreter** Page
**Purpose**: AI-powered transaction analysis and insights

**User Flow:**
1. **Review Transaction Context**
   - User sees enriched transaction details
   - Views price chart with transaction marker
   - Examines price impact analysis table

2. **Generate AI Summary**
   - User clicks "Generate AI Summary" button
   - AI analyzes all available data:
     - Transaction metadata
     - Price impact analysis
     - Token information
     - Market context
   - Generates human-readable summary

3. **Read AI Analysis**
   - User views comprehensive AI-generated report
   - Gets insights on:
     - Transaction significance
     - Market impact
     - Potential implications
     - Risk assessment

#### 5. **Full Analysis** Page
**Purpose**: Comprehensive transaction analysis dashboard

**User Flow:**
1. **View Complete Transaction Overview**
   - User sees token and transaction details
   - Views all enriched metadata:
     - Address intelligence (ENS, net worth, domains)
     - Method descriptions
     - Transaction context

2. **Review Price Analysis**
   - User examines price chart with transaction markers
   - Views detailed price impact analysis
   - Understands market reaction to transaction

3. **Read AI Interpretation**
   - User reviews AI-generated summary
   - Gets comprehensive analysis of the transaction
   - Understands market implications

4. **Generate PDF Report**
   - User clicks "Generate PDF report" button
   - System creates comprehensive PDF report
   - Includes all analysis, charts, and insights
   - Report is saved with timestamp for future reference