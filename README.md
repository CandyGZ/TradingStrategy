# TradingStrategy
a very simple trading strategy incluiding graph and calc about % earning and actual balance

This Python script implements a simple trading algorithm based on Moving Average Crossovers using historical cryptocurrency to USD exchange rate data. It provides a visualization of the strategy's performance and includes a basic backtest.

![TradingStrategy Chart](https://github.com/CandyGZ/TradingStrategy/raw/main/chartBTC.png)

**Disclaimer**: This code is provided for educational purposes only and should not be considered as financial advice or a suggestion for investment. Trading cryptocurrencies and financial assets carries risk, and past performance does not guarantee future results. Please consult with a financial advisor before making any investment decisions.

## Usage

1. Make sure you have the required libraries installed:
   - yfinance
   - pandas
   - numpy
   - matplotlib

2. Modify the script to specify your desired parameters, such as the cryptocurrency, date range, and initial balance.

3. Run the script in a Python environment.

4. The script will retrieve historical cryptocurrency to USD exchange rate data using the `yfinance` library, compute Moving Averages, and plot them along with buy and sell signals on a chart.

5. It will also perform a basic backtest to compare the strategy's performance with a "Buy and Hold" strategy, displaying the final portfolio balance and earnings.

## How to Use `yfinance` and Change the Cryptocurrency

- To change the cryptocurrency from BTC to another coin, modify the following line in the script:

   ```python
   # Replace "BTC-USD" with the desired cryptocurrency symbol, e.g., "ETH-USD" for Ethereum.
   BTC_USD = yf.download("BTC-USD", start="2023-01-01", end="2023-09-30", interval="1d")

# Modify the script's parameters as needed
initial_balance = 159000
start_date = "2023-01-01"
end_date = "2023-09-30"
cryptocurrency = "ETH-USD"  # Change to the desired cryptocurrency symbol

# Run the script
# ...

# The script will generate visualizations and display the final portfolio balance and earnings for the chosen cryptocurrency.


Important Notes
This script is for educational purposes only and should not be used for real trading without thorough testing and validation.
Always exercise caution and conduct your own research before making any financial decisions.
Make sure to have the required Python libraries installed before running the script.
Consider using more advanced trading libraries and strategies for real-world trading scenarios.
