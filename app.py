import streamlit as st
import pandas as pd
import ccxt
import plotly.graph_objects as go
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="AlphaFlow Live", layout="wide")
st.title("⚡ AlphaFlow: Live WebSocket Order Flow")

# --- LIVE DATA CONNECTION ---
# We use CCXT to connect to the global exchange ledger
exchange = ccxt.binance()

def get_live_data(symbol='BTC/USDT'):
    try:
        # Fetch the most recent 500 market trades (The 'Tape')
        trades = exchange.fetch_trades(symbol, limit=500)
        df = pd.DataFrame(trades, columns=['price', 'amount', 'side', 'timestamp'])
        
        # Microstructure Logic: Delta = Market Buy Volume - Market Sell Volume
        df['Delta'] = df.apply(lambda x: x['amount'] if x['side'] == 'buy' else -x['amount'], axis=1)
        df['CVD'] = df['Delta'].cumsum()
        return df
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# Auto-refresh the live data
df = get_live_data()

# --- THE "ONE-CLICK" INSTITUTIONAL WALL FEATURE ---
st.sidebar.header("🎯 Pro Tools")
if st.sidebar.button("🔍 Find Institutional Wall"):
    # Scans for the price level with the highest concentrated volume (Absorption)
    wall_level = df.groupby('price')['amount'].sum().idxmax()
    wall_vol = df.groupby('price')['amount'].sum().max()
    st.sidebar.success(f"Wall Detected at: ${wall_level}")
    st.sidebar.info(f"Total Absorption: {round(wall_vol, 4)} BTC")
    st.toast(f"Major Institutional Wall found at ${wall_level}!")

# --- UI LAYOUT ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("👣 Live Footprint Concentration")
    # Grouping volume by price to visualize the 'Footprint' density
    footprint = df.groupby('price')['amount'].sum().sort_index(ascending=False).head(15)
    st.bar_chart(footprint)
    st.caption("Higher bars = Significant Absorption/Iceberg Zones")

with col2:
    st.subheader("📈 Cumulative Delta (Conviction)")
    fig = go.Figure()
    # CVD shows the net aggression of the buyers vs sellers[cite: 1, 2]
    fig.add_trace(go.Scatter(x=df.index, y=df['CVD'], fill='tozeroy', 
                             line=dict(color='#00ff88'), name="CVD"))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

# --- REAL-TIME ALERTS ---
st.divider()
last_delta = df['Delta'].iloc[-1]
if abs(last_delta) > df['Delta'].mean() * 3:
    st.warning(f"🚨 LARGE ORDER DETECTED: {'Buy' if last_delta > 0 else 'Sell'} of {abs(round(last_delta, 2))} BTC")
