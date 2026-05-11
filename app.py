import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- APP CONFIG & UI ---
st.set_page_config(page_title="AlphaFlow Microstructure", layout="wide")
st.title("🏹 AlphaFlow: Order Flow & Divergence Lab")

# --- ENGINE: SYNTHETIC DATA & LOGIC ---
def get_market_data(n_ticks=500):
    price = 100.0
    data = []
    for _ in range(n_ticks):
        side = np.random.choice(['Buy', 'Sell'])
        volume = np.random.randint(5, 150)
        # Random walk price with momentum weight
        price += np.random.normal(0, 0.05) if side == 'Buy' else -np.random.normal(0, 0.05)
        data.append({"Price": round(price, 2), "Side": side, "Volume": volume})
    return pd.DataFrame(data)

df = get_market_data()
df['Delta'] = df.apply(lambda x: x['Volume'] if x['Side'] == 'Buy' else -x['Volume'], axis=1)
df['CVD'] = df['Delta'].cumsum()

# --- ALERT LOGIC: DIVERGENCE DETECTION ---
def detect_alerts(df):
    recent = df.tail(20)
    price_trend = recent['Price'].iloc[-1] > recent['Price'].iloc[0]
    delta_trend = recent['CVD'].iloc[-1] > recent['CVD'].iloc[0]
    
    # Bearish Divergence: Price Up, Delta Down (Exhaustion)
    if price_trend and not delta_trend:
        return "⚠️ BEARISH DIVERGENCE: Price rising but buying pressure is fading. Possible Exhaustion."
    # Bullish Divergence: Price Down, Delta Up (Absorption)
    if not price_trend and delta_trend:
        return "✅ BULLISH DIVERGENCE: Price falling but selling pressure is decreasing. Possible Absorption."
    return None

alert = detect_alerts(df)
if alert:
    st.warning(alert)
    st.toast(alert) # Pop-up notification in-app

# --- DASHBOARD LAYOUT ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🛡️ Absorption Detector")
    footprint = df.groupby(['Price', 'Side'])['Volume'].sum().unstack(fill_value=0)
    footprint['Total_Volume'] = footprint.get('Buy', 0) + footprint.get('Sell', 0)
    
    # Highlight high-volume nodes (Potential Icebergs)
    icebergs = footprint[footprint['Total_Volume'] > footprint['Total_Volume'].mean() * 2]
    st.write("Identified Institutional Absorption Zones:")
    st.dataframe(icebergs[['Total_Volume']])

with col2:
    st.subheader("📈 Delta vs. Price Analysis")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(y=df['Price'], name="Price", line=dict(color='#00f2ff')), secondary_y=False)
    fig.add_trace(go.Bar(y=df['CVD'], name="CVD", marker_color='white', opacity=0.2), secondary_y=True)
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

# --- FOOTPRINT HEATMAP ---
st.subheader("👣 Footprint Heatmap")

fp_fig = go.Figure(data=go.Heatmap(
    z=footprint['Total_Volume'],
    y=footprint.index,
    x=['Sells (Bid)', 'Buys (Ask)'],
    colorscale='Hot'
))
fp_fig.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fp_fig, use_container_width=True)
