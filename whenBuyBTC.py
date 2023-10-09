# where the trading algorithm decides to make a buy order, we will plot an upwards facing green arrow.
# Where the algorithm places a sell order, we will plot a downwards facing red arrow.

import yfinance as yf
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter

# Retrieve two weeks of BTC to USD exchange rates with a 1 hour interval and save the dataframe to a variable.
BTC_USD = yf.download("BTC-USD", start="2023-01-01", end="2023-09-30", interval="1d")

# Create a pandas dataframe that is the same size as the BTC_USD dataframe and covers the same dates
trade_signals = pd.DataFrame(index=BTC_USD.index)

# Define the intervals for the Fast and Slow Simple Moving Averages (in days)
short_interval = 10
long_interval = 40

# Compute the Simple Moving Averages and add it to the dateframe as new columns
trade_signals["Short"] = (
    BTC_USD["Close"].rolling(window=short_interval, min_periods=1).mean()
)
trade_signals["Long"] = (
    BTC_USD["Close"].rolling(window=long_interval, min_periods=1).mean()
)

# Now we have a dataframe containing the dates we're interested in and two Simple Moving Averages,
# one with a short interval and the other with a longer sampling interval.
# This gives us the information we need to figure out where the two Moving Averages cross,
# which is the core of this trading strategy. Let's create a new column called Signal that
# is populated everywhere with zeros, except for a one wherever the two Moving Averages cross.

# Create a new column populated with zeros
trade_signals["Signal"] = 0.0

# Wherever the Shorter term SMA is above the Longer term SMA, set the Signal column to 1, otherwise 0
trade_signals["Signal"] = np.where(
    trade_signals["Short"] > trade_signals["Long"], 1.0, 0.0
)

# According to our Moving Average Crossover strategy, we want to buy when the short-term SMA crosses
# the long-term SMA from below, and sell when it crosses over from above. We can easily use the Signal
# column in the trade_signals dataframe to determine where exactly these events occur. If the Signal
# column has value 0.0 on a given date then switches to 1.0, this means the short-term SMA crossed the
# long-term SMA from below - this is our time to buy BTC according to our strategy. On the other hand,
# if the value goes from 1.0 to 0.0, that tells us the short-term SMA was above the long-term SMA and
# then crossed over - this is our time to sell.

trade_signals["Position"] = trade_signals["Signal"].diff()

# Graph
fig, ax = plt.subplots(dpi=100)

# Formatting the date axis
date_format = DateFormatter("%h-%d-%y")
ax.xaxis.set_major_formatter(date_format)
ax.tick_params(axis="x", labelsize=8)
fig.autofmt_xdate()


# Plotting the BTC closing price against the date (1 day interval)
ax.plot(BTC_USD["Close"], lw=0.75, label="Closing Price")

# Plot the shorter-term moving average
ax.plot(
    trade_signals["Short"], lw=0.75, alpha=0.75, color="orange", label="Short-term SMA"
)

# Plot the longer-term moving average
ax.plot(
    trade_signals["Long"], lw=0.75, alpha=0.75, color="purple", label="Long-term SMA"
)


# Adding green arrows to indicate buy orders
ax.plot(
    trade_signals.loc[trade_signals["Position"] == 1.0].index,
    trade_signals.Short[trade_signals["Position"] == 1.0],
    marker=6,
    ms=4,
    linestyle="none",
    color="green",
)

# Adding red arrows to indicate sell orders
ax.plot(
    trade_signals.loc[trade_signals["Position"] == -1.0].index,
    trade_signals.Short[trade_signals["Position"] == -1.0],
    marker=7,
    ms=4,
    linestyle="none",
    color="red",
)


# Adding labels and title to the plot
ax.set_ylabel("Price of BTCN (USD)")
ax.set_title("BTC to USD Exchange Rate")
ax.grid()  # adding a grid
ax.legend()  # adding a legend

# Displaying the price chart
plt.show()


# Once you have a trading algorithm implemented, you will certainly want to test it to see if it can actually produce a
# profit and compare its performace with other strategies. Often, the first way to do this is to perform a backtest.
# The core idea behind a backtest is to simulate running your trading algorithm on historical data and compute several
#  metrics, such as the return. While this method certainly does not guarantee that the algorithmn will be consistently
# profitable, it's a quick way to test the viability of a strategy and reject clearly unfeasable strategies.
# Let's do a simple backtest over the 2020 BTC-USD data on the trading algorithm we implemented.
# There are many libraries that can perform sophisticated backtests on a variety of algorithms,
# however, to develop an understanding of the underlying principle, let's implement our own simple backtest.
# Let's suppose we start with an account with $1000 USD.
# Define how much money you will start with (in USD)
initial_balance = 159000

# Create dataframe containing all the dates considered
backtest = pd.DataFrame(index=trade_signals.index)

# Add column containing the daily percent returns of BTC
backtest["BTC_Return"] = BTC_USD["Close"] / BTC_USD["Close"].shift(
    1
)  # Current closing price / yesterday's closing price

# Now to compute the daily returns of the trading algorithm, let's assume that at any given point,
# our portfolio is either all in on BTC or is entirely holding USD. This means that whenever
# the algorithm is currently holding BTC, it's daily returns are the same as the daily returns of BTC.
# On the other hand, when the algorithm is holding USD, its returns are entirely detached from BTC price movements.
# Thus when holding USD, the value of the portfolio remains constant during that period. We will also make the simplifying
# assumption that we are able to perform zero comission trades. This reasoning is condensed into the following two lines of code.

# Add column containing the daily percent returns of the Moving Average Crossover strategy
backtest["Alg_Return"] = np.where(trade_signals.Signal == 1, backtest.BTC_Return, 1.0)

# Add column containing the daily value of the portfolio using the Crossover strategy
backtest["Balance"] = (
    initial_balance * backtest.Alg_Return.cumprod()
)  # cumulative product


# Graph
fig, ax = plt.subplots(dpi=100)
# Formatting the date axis
date_format = DateFormatter("%h-%d-%y")
ax.xaxis.set_major_formatter(date_format)
ax.tick_params(axis="x", labelsize=8)
fig.autofmt_xdate()
# Plotting the value of Buy and Hold Strategy
ax.plot(
    initial_balance * backtest.BTC_Return.cumprod(),
    lw=0.75,
    alpha=0.75,
    label="Buy and Hold",
)
# Plotting total value of Crossing Averages Strategy
ax.plot(backtest["Balance"], lw=0.75, alpha=0.75, label="Crossing Averages")
# Adding labels and title to the plot
ax.set_ylabel("USD")
ax.set_title("Value of Portfolio")
ax.grid()  # adding a grid
ax.legend()  # adding a legend
# Displaying the price chart
plt.show()


# Obtenemos el último valor de la columna balance para calcular ganancias
lastBalance = backtest["Balance"].tail(1).values[0]
winnings = lastBalance - initial_balance
percent = (lastBalance - initial_balance) / initial_balance * 100
porciento = str("{:.2f}".format(percent)) + " %"
print(initial_balance)
print(backtest)
print("Total earnings: ", porciento, ",", "{:.2f}".format(winnings))
print("Final Balance: $", "{:.2f}".format(lastBalance))
