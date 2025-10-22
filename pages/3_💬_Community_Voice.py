import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Long Beach Community Pulse", page_icon="💬", layout="wide")

# Enhanced Dark Mode CSS
st.markdown("""
<style>
    .big-title {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #818CF8 0%, #A78BFA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.3rem;
        color: #D1D5DB;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    .info-box {
        background: rgba(99, 102, 241, 0.1);
        border-left: 4px solid #818CF8;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        color: #E5E7EB;
    }
    .info-box h3, .info-box h4 { color: #A78BFA; }
    .info-box p, .info-box li { color: #D1D5DB; line-height: 1.6; }
    .info-box strong { color: #F3F4F6; }
    
    .methodology-box {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #F59E0B;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        color: #E5E7EB;
    }
    .methodology-box h3, .methodology-box h4 { color: #FBBF24; }
    .methodology-box p, .methodology-box li { color: #D1D5DB; }
    
    .insight-box {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10B981;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #D1FAE5;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">💬 Long Beach Community Pulse</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-platform opinion tracking powered by AI sentiment analysis</div>', unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('community_pulse_data.csv')
        df['created_utc'] = pd.to_datetime(df['created_utc'])
        return df
    except:
        return None

data_df = load_data()

if data_df is not None:
    st.success(f"📊 Analyzing {len(data_df):,} posts from Reddit and Twitter")
    
    # Your dashboard code here...
    st.write("Dashboard loaded successfully!")
    
    # Display summary
    st.subheader("Sentiment Distribution")
    sentiment_counts = data_df['sentiment'].value_counts()
    fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index)
    st.plotly_chart(fig)
    
else:
    st.error("No data available. Run the collection script first!")
