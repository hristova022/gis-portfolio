import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Community Pulse", page_icon="💬", layout="wide")

st.title("💬 Long Beach Community Pulse")
st.markdown("*Tracking online conversations about Long Beach topics*")
st.divider()

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('community_pulse_data.csv')
        df['created_utc'] = pd.to_datetime(df['created_utc'], format='ISO8601', utc=True)
        return df
    except:
        try:
            df = pd.read_csv('reddit_sentiment_data.csv')
            df['created_utc'] = pd.to_datetime(df['created_utc'], format='ISO8601', utc=True)
            return df
        except:
            return None

data_df = load_data()

if data_df is not None:
    sources = data_df['source'].unique() if 'source' in data_df.columns else ['Reddit']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Posts", f"{len(data_df):,}")
    with col2:
        if 'Reddit' in sources:
            st.metric("🔴 Reddit", f"{len(data_df[data_df['source']=='Reddit']):,}")
    with col3:
        if 'Twitter' in sources:
            st.metric("🐦 Twitter", f"{len(data_df[data_df['source']=='Twitter']):,}")
    with col4:
        avg = data_df['polarity'].mean()
        mood = "Positive 😊" if avg > 0.05 else "Negative 😟" if avg < -0.05 else "Neutral 😐"
        st.metric("Mood", mood, f"{avg:.2f}")
    
    st.divider()
    
    st.sidebar.header("🎛️ Filters")
    
    if len(sources) > 1:
        sel_sources = st.sidebar.multiselect("Sources", sources, default=sources)
        filtered_df = data_df[data_df['source'].isin(sel_sources)]
    else:
        filtered_df = data_df
    
    topics = st.sidebar.multiselect("Topics", filtered_df['topic'].unique(), default=filtered_df['topic'].unique())
    filtered_df = filtered_df[filtered_df['topic'].isin(topics)]
    
    if len(filtered_df) > 0:
        dr = st.sidebar.date_input("Date Range", value=(filtered_df['created_utc'].min().date(), filtered_df['created_utc'].max().date()))
        if len(dr) == 2:
            filtered_df = filtered_df[(filtered_df['created_utc'].dt.date >= dr[0]) & (filtered_df['created_utc'].dt.date <= dr[1])]
    
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Trends", "📝 Data"])
    
    with tab1:
        st.markdown("### Sentiment Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribution")
            sc = filtered_df['sentiment'].value_counts()
            fig = px.pie(values=sc.values, names=sc.index, color=sc.index, 
                        color_discrete_map={'Positive':'#10B981','Neutral':'#F59E0B','Negative':'#EF4444'}, hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("By Topic")
            ts = filtered_df.groupby(['topic','sentiment']).size().reset_index(name='count')
            fig = px.bar(ts, x='topic', y='count', color='sentiment',
                        color_discrete_map={'Positive':'#10B981','Neutral':'#F59E0B','Negative':'#EF4444'}, barmode='group')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Trends Over Time")
        series = filtered_df.set_index('created_utc').resample('W')['polarity'].mean().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series['created_utc'], y=series['polarity'], mode='lines+markers', fill='tozeroy'))
        fig.add_hline(y=0, line_dash="dash")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Volume")
        vol = filtered_df.set_index('created_utc').resample('W').size().reset_index(name='count')
        fig = px.bar(vol, x='created_utc', y='count')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Top Posts")
        filtered_df['engagement'] = filtered_df['score'] + (filtered_df['num_comments']*2)
        top = filtered_df.nlargest(10, 'engagement')
        
        for _, p in top.iterrows():
            e = {'Positive':'🟢','Neutral':'🟡','Negative':'🔴'}[p['sentiment']]
            st.markdown(f"**{e} {p['title'][:100]}...**")
            st.markdown(f"📅 {p['created_utc'].strftime('%Y-%m-%d')} | {p['source']} | {p['topic']} | ⭐{p['score']} | 💬{p['num_comments']}")
            st.markdown(f"[View →]({p['url']})")
            st.divider()
        
        st.subheader("Download Data")
        csv = filtered_df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, f"data_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    
    st.divider()
    st.markdown("**Data:** Reddit & Twitter | **Analysis:** Sentiment scoring | Built with ❤️ for Long Beach")

else:
    st.error("❌ Data file not found")
    st.info("Run the data collection script to generate community_pulse_data.csv")
