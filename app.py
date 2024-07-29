import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide",
                   page_title="StockValuator")

st.title("Stock Valuation App")

input_s, metric1, metric2, metric3 = st.columns(4)
with input_s:
    symbol = st.text_input("Select a Stock by Yahoo ticker symbol", value="MSFT",
                           help="For stocks on foreign exchanges you need to specify the exchange e.g DTE.DE")

@st.cache_data
def get_yahoo_data(symbol):
    ticker = yf.Ticker(symbol)
    past_fcf = ticker.cashflow
    # st.write(ticker.info)

    return past_fcf, ticker.info

# Yahoo Finace Data

try:
    past_fcf, ticker_info = get_yahoo_data(symbol)
    shares = ticker_info['sharesOutstanding']
    l_close_price = ticker_info["previousClose"]
    dividend = ticker_info["dividendRate"]
    currency = ticker_info["currency"]
    name = ticker_info["shortName"]

except:
    st.error("Couldn´t load the desired stock information for the mentioned ticker symbol. \n\nPlease provide a valid ticker or try it again later.")
    shares = None
    l_close_price = None
    dividend = None
    currency = None
    name = None
    past_fcf = pd.DataFrame()
    st.stop()

#Metrics next to ticker symbol
with metric1:
    st.metric("Company", value=name)
with metric2:
    price_col, cur_col = st.columns(2)
    with price_col:
        st.metric("Share Price", l_close_price)
    with cur_col:
        st.metric("Currency", currency)
with metric3:
    st.empty()


# Calculations based on Yahoo data
past_fcf = past_fcf[past_fcf.index == "Free Cash Flow"]
past_fcf.columns = pd.to_datetime(past_fcf.columns).year

dcf_tab, ddm_tab = st.tabs(["Discounted Cash Flow Model", "Discounted Dividend Model"])

with dcf_tab:

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        expected_rate = st.number_input("Expected min. return", value=0.07)
    with col2:
        risk_free_rate = st.number_input("Risk free Return", value=0.03)
    with col3:
        fcf_growth_rate = st.number_input("Free Cashflow Growth Rate", value=0.03)
    with col4:
        forcast_period = st.number_input("Forcast Years", value=5, step=1)

    st.divider()

    years = list(range(1, forcast_period + 1))
    furture_fcf = []
    dicount_factor = []
    year_col = []

    for year in years:
        cashflow = past_fcf.iloc[0, 0] * (1 + fcf_growth_rate) ** year
        furture_fcf.append(cashflow)
        dicount_factor.append((1 + expected_rate) ** year)
        year_col.append(past_fcf.columns[0] + year)

    dcf = np.array(furture_fcf) / np.array(dicount_factor)

    future_dict = {
        "Free Cash Flow": furture_fcf,
        "Discount Factor": dicount_factor,
        "Discounted FCF": dcf,
    }
    furture_fcf_df = pd.DataFrame(data=future_dict.values(), index=list(future_dict.keys()), columns=year_col)

    # Terminal Value Calculation
    terminal_value = past_fcf.iloc[0, 0] * (1 + risk_free_rate) / (expected_rate - risk_free_rate)
    disc_terminal_value = terminal_value / (1 + expected_rate) ** years[-1]
    furture_fcf_df["Terminal Value"] = [terminal_value, furture_fcf_df.iloc[1,-1], disc_terminal_value]

    #combining past and future FCF tables
    fcf_table = furture_fcf_df.combine_first(past_fcf)
    fcf_table = fcf_table.loc[["Free Cash Flow", "Discount Factor", "Discounted FCF"]]
    fcf_table = fcf_table.fillna(0).map('{:,.2f}'.format)
    fcf_table.columns = [f"{col}e" if (isinstance(col, int) and col > max(past_fcf.columns))
                         else col for col in fcf_table.columns]


    #Fair Value Calculation
    fair_value = round(furture_fcf_df.iloc[2].sum() / shares, 2)
    value_dif_fcf = abs(l_close_price - fair_value)/fair_value

    if l_close_price > fair_value:
        fcf_price_level = "overvalued"
        fcf_color = "red"
    else:
        fcf_price_level = "undervalued"
        fcf_color = "green"

    st.table(fcf_table)

    st.markdown(f"The intrinsic / fair value of the Company is {fair_value} {currency} and the current share price is {l_close_price} {currency}")
    st.markdown(f"{name} is {value_dif_fcf:.0%} :{fcf_color}[ {fcf_price_level} !]")

with ddm_tab:
    st.info("Comming soon")