import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Config
st.set_page_config(page_title="Order Flow Lab", layout="wide")
st.title("📊 Market Microstructure & Order Flow Lab")

# --- SIMULATED DATA ENGINE ---
def get_market_data(n_ticks=500):
    price = 100.0
    data = []
    for _ in range(n_ticks):
        side = np.random.choice(['Buy', 'Sell'])
        volume = np.random.randint(1, 100)
        # Price movement logic
        price += np.random.normal(0, 0.05) if side == 'Buy' else -np.random.normal(0, 0.05)
        data.append({"Price": round(price, 2), "Side": side, "Volume": volume})
    return pd.DataFrame(data)

df = get_market_data()

# --- CALCULATIONS ---
# Delta = Market Buys - Market Sells[cite: 1, 2]
df['Delta_Impact'] = df.apply(lambda x: x['Volume'] if x['Side'] == 'Buy' else -x['Volume'], axis=1)
df['Cumulative_Delta'] = df['Delta_Impact'].cumsum()

# --- VISUALIZATION ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🛡️ Absorption Detector")
    # Grouping volume by price level to see Footprint[cite: 1, 2]
    footprint = df.groupby(['Price', 'Side'])['Volume'].sum().unstack(fill_value=0)
    footprint['Total_Volume'] = footprint.get('Buy', 0) + footprint.get('Sell', 0)
    
    # Logic: High volume + little price movement = Absorption[cite: 1, 2]
    high_vol = footprint[footprint['Total_Volume'] > footprint['Total_Volume'].mean() * 1.5]
    st.write("Potential Iceberg Levels Identified:")
    st.dataframe(high_vol[['Total_Volume']])

with col2:
    st.subheader("📈 Delta Divergence Analysis")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(y=df['Price'], name="Price", line=dict(color='gold')), secondary_y=False)
    fig.add_trace(go.Bar(y=df['Cumulative_Delta'], name="Cumulative Delta", marker_color='teal', opacity=0.4), secondary_y=True)
    fig.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(fig, use_container_width=True)

# --- FOOTPRINT HEATMAP ---
st.subheader("👣 Volume Footprint (Buy/Sell Density)")
fp_fig = go.Figure(data=go.Heatmap(
    z=footprint['Total_Volume'],
    y=footprint.index,
    x=['Sells', 'Buys'],
    colorscale='Viridis'
))
st.plotly_chart(fp_fig, use_container_width=True)
