import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from statsmodels.tsa.stattools import coint

st.set_page_config(
    layout="wide", page_title="Crude Oil Spread Dashboard", page_icon="⛽️"
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: #000000;
        color: #ffffff;
    }
    .sidebar .sidebar-content {
        background-color: #000000;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    .stDataFrame {
        background-color: #0e1117;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Function to fetch data from Alpha Vantage
def get_commodity_data(commodity, interval="daily"):
    api_key = "ERTAXAG6XF79PJ66"  # Replace with your actual API key
    url = f"https://www.alphavantage.co/query?function={commodity}&interval={interval}&apikey={api_key}&datatype=json"
    response = requests.get(url)
    data = response.json()

    if "data" not in data:
        st.error("Error fetching data from API.")
        return pd.DataFrame()

    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = df["value"].replace(".", np.nan).astype(float)
    df["value"] = df["value"].apply(lambda x: max(x, 1))
    df.dropna(subset=["value"], inplace=True)
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)
    return df


# Fetch data
brent_data = get_commodity_data("BRENT")
wti_data = get_commodity_data("WTI")

if brent_data.empty or wti_data.empty:
    st.stop()

# Align the data
data = pd.merge(
    brent_data, wti_data, left_index=True, right_index=True, suffixes=("_brent", "_wti")
)

# Calculate spread and z-score
data["spread"] = data["value_brent"] - data["value_wti"]
data["zscore"] = (data["spread"] - data["spread"].mean()) / data["spread"].std()

# Determine significant spread points for potential trades (Z-score > 1 or < -1)
data["trade_signal"] = np.where((data["zscore"] > 1) | (data["zscore"] < -1), 1, 0)

# Streamlit dashboard layout
st.title("Crude Oil Spread Dashboard")
st.code("This dashboard visualizes the spread between Brent and WTI crude oil prices.")

# Plot Brent and WTI Prices
st.header("Brent vs WTI Crude Oil Prices")
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["value_brent"],
        mode="lines",
        name="Brent",
        line=dict(color="#0068ff"),
    )
)
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["value_wti"],
        mode="lines",
        name="WTI",
        line=dict(color="#fb8b1e"),
    )
)
fig.update_layout(
    plot_bgcolor="#000000",
    paper_bgcolor="#000000",
    font_color="#ffffff",
    title="Brent vs WTI Crude Oil Prices",
)
st.plotly_chart(fig)

# Plot Spread and Mark Trade Signals
st.header("Spread Between Brent and WTI Crude Oil Prices")
fig_spread = go.Figure()
fig_spread.add_trace(
    go.Scatter(
        x=data.index,
        y=data["spread"],
        mode="lines",
        name="Spread",
        line=dict(color="#ff433d"),
    )
)

# Mark the trades with white dots
trade_dates = data[data["trade_signal"] == 1].index
trade_spread_values = data[data["trade_signal"] == 1]["spread"]
fig_spread.add_trace(
    go.Scatter(
        x=trade_dates,
        y=trade_spread_values,
        mode="markers",
        name="Trade Signal",
        marker=dict(color="white", size=8, symbol="circle"),
    )
)

fig_spread.update_layout(
    plot_bgcolor="#000000",
    paper_bgcolor="#000000",
    font_color="#ffffff",
    title="Spread Between Brent and WTI Crude Oil Prices with Trade Signals",
)
st.plotly_chart(fig_spread)

# Plot Z-Score and Mark Trade Signals
st.header("Z-Score of the Spread")
fig_zscore = go.Figure()
fig_zscore.add_trace(
    go.Scatter(
        x=data.index,
        y=data["zscore"],
        mode="lines",
        name="Z-Score",
        line=dict(color="#00cc96"),
    )
)

# Mark the trades with white dots
trade_zscore_values = data[data["trade_signal"] == 1]["zscore"]
fig_zscore.add_trace(
    go.Scatter(
        x=trade_dates,
        y=trade_zscore_values,
        mode="markers",
        name="Trade Signal",
        marker=dict(color="white", size=8, symbol="circle"),
    )
)

fig_zscore.add_hline(
    y=1, line_dash="dash", line_color="red", annotation_text="Upper Threshold"
)
fig_zscore.add_hline(
    y=-1, line_dash="dash", line_color="red", annotation_text="Lower Threshold"
)

fig_zscore.update_layout(
    plot_bgcolor="#000000",
    paper_bgcolor="#000000",
    font_color="#ffffff",
    title="Z-Score of the Spread with Trade Signals",
)
st.plotly_chart(fig_zscore)
