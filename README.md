# Whales Alert - Transaction Interpreter

A tool to extract and interpret large-scale cryptocurrency transactions (whale movements).

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

## Required API Keys

- INFURA_API_KEY  
- ALCHEMY_API_KEY
- ETHERSCAN_API_KEY
- MORALIS_API_KEY
- COINGECKO_API_KEY
- GEMINI_API_KEY

## Testing

```bash
python -m pytest tests/
```

## Project Structure
whales_alert/
├── modules/          # Data extraction modules
├── pages/            # Streamlit pages
├── utils/             # Utility functions
├── tests/             # Test files
└── streamlit_app.py   # Main application