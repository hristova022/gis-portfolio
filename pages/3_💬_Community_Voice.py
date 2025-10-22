import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Community Pulse", page_icon="💬", layout="wide")

# Enhanced Dark Mode CSS
st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: bold; color: #1E40AF; }
</style>
""", unsafe_allow_html=True)

st.title("💬 Long Beach Community Pulse")
st.markdown("Tracking online conversations about Long Beach topics")


st.markdown("---")

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('community_pulse_data.csv')
        df['created_utc'] = pd.to_datetime(df['created_utc'], format='ISO8601', utc=True)
        return df
    except FileNotFoundError:
        try:
            df = pd.read_csv('reddit_sentiment_data.csv')
            df['created_utc'] = pd.to_datetime(df['created_utc'], format='ISO8601', utc=True)
            return df
        except:
            return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

data_df = load_data()

if data_df is not None:
    # Header metrics
    sources = data_df['source'].unique() if 'source' in data_df.columns else ['Reddit']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Posts", f"{len(data_df):,}")
    with col2:
        if 'Reddit' in sources:
            reddit_count = len(data_df[data_df['source'] == 'Reddit'])
            st.metric("🔴 Reddit", f"{reddit_count:,}")
    with col3:
        if 'Twitter' in sources:
            twitter_count = len(data_df[data_df['source'] == 'Twitter'])
            st.metric("🐦 Twitter", f"{twitter_count:,}")
    with col4:
        avg_sentiment = data_df['polarity'].mean()
        mood = "Positive 😊" if avg_sentiment > 0.05 else "Negative 😟" if avg_sentiment < -0.05 else "Neutral 😐"
        st.metric("Community Mood", mood, f"{avg_sentiment:.2f}")
    
    st.markdown("---")
    
    # Sidebar filters
    st.sidebar.header("🎛️ Filters")
    
    if len(sources) > 1:
        selected_sources = st.sidebar.multiselect("Data Sources", sources, default=sources)
        filtered_df = data_df[data_df['source'].isin(selected_sources)]
    else:
        filtered_df = data_df
    
    topics = st.sidebar.multiselect("Topics", filtered_df['topic'].unique(), default=filtered_df['topic'].unique())
    filtered_df = filtered_df[filtered_df['topic'].isin(topics)]
    
    if len(filtered_df) > 0:
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(filtered_df['created_utc'].min().date(), filtered_df['created_utc'].max().date()),
            min_value=filtered_df['created_utc'].min().date(),
            max_value=filtered_df['created_utc'].max().date()
        )
        
        if len(date_range) == 2:
            filtered_df = filtered_df[
                (filtered_df['created_utc'].dt.date >= date_range[0]) & 
                (filtered_df['created_utc'].dt.date <= date_range[1])
            ]
    
    # Tabs
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Trends", "📝 Top Posts & Data"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Opinion Distribution")
            st.caption("Overall breakdown of community sentiment")
            sentiment_counts = filtered_df['sentiment'].value_counts()
            fig = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                color=sentiment_counts.index,
                color_discrete_map={'Positive': '#10B981', 'Neutral': '#F59E0B', 'Negative': '#EF4444'},
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Opinion by Topic")
            st.caption("Compare sentiment across different topics")
            topic_sentiment = filtered_df.groupby(['topic', 'sentiment']).size().reset_index(name='count')
            fig = px.bar(
                topic_sentiment,
                x='topic',
                y='count',
                color='sentiment',
                color_discrete_map={'Positive': '#10B981', 'Neutral': '#F59E0B', 'Negative': '#EF4444'},
                barmode='group'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Platform comparison if both sources exist
        sources = data_df['source'].unique() if 'source' in data_df.columns else ['Reddit']
        if len(sources) > 1:
            st.subheader("Platform Comparison")
            st.caption("How sentiment differs between platforms")
            
            col1, col2 = st.columns(2)
            
            with col1:
                platform_sentiment = filtered_df.groupby(['source', 'sentiment']).size().reset_index(name='count')
                fig = px.bar(
                    platform_sentiment,
                    x='source',
                    y='count',
                    color='sentiment',
                    color_discrete_map={'Positive': '#10B981', 'Neutral': '#F59E0B', 'Negative': '#EF4444'},
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                platform_avg = filtered_df.groupby('source')['polarity'].mean().reset_index()
                fig = px.bar(
                    platform_avg,
                    x='source',
                    y='polarity',
                    color='polarity',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                fig.add_hline(y=0, line_dash="dash", line_color="white")
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Opinion Trends Over Time")
        st.caption("Weekly average sentiment")
        
        time_series = filtered_df.set_index('created_utc').resample('W')['polarity'].mean().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_series['created_utc'],
            y=time_series['polarity'],
            mode='lines+markers',
            name='Opinion Score',
            line=dict(color='#818CF8', width=3),
            fill='tozeroy'
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(
            xaxis_title="Week",
            yaxis_title="Average Sentiment",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Discussion Volume")
            volume = filtered_df.set_index('created_utc').resample('W').size().reset_index(name='count')
            fig = px.bar(volume, x='created_utc', y='count', color_discrete_sequence=['#A78BFA'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Sentiment Over Time")
            weekly = filtered_df.copy()
            weekly['week'] = weekly['created_utc'].dt.to_period('W').astype(str)
            weekly_counts = weekly.groupby(['week', 'sentiment']).size().reset_index(name='count')
            
            fig = px.area(
                weekly_counts,
                x='week',
                y='count',
                color='sentiment',
                color_discrete_map={'Positive': '#10B981', 'Neutral': '#F59E0B', 'Negative': '#EF4444'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("📌 Top Engaged Posts")
        st.caption("Most liked and commented discussions")
        
        filtered_df['engagement'] = filtered_df['score'] + (filtered_df['num_comments'] * 2)
        top_posts = filtered_df.nlargest(15, 'engagement')
        
        sentiment_filter = st.radio("Filter:", ["All", "Positive", "Neutral", "Negative"], horizontal=True)
        
        if sentiment_filter != "All":
            top_posts = top_posts[top_posts['sentiment'] == sentiment_filter]
        
        for idx, post in top_posts.iterrows():
            emoji = {'Positive': '🟢', 'Neutral': '🟡', 'Negative': '🔴'}[post['sentiment']]
            
            st.markdown(f"""
            **{emoji} {post['title'][:120]}...**  
            📅 {post['created_utc'].strftime('%Y-%m-%d')} | 
            📊 {post['source']} | 
            🏷️ {post['topic']} | 
            ⭐ {post['score']} | 
            💬 {post['num_comments']} comments
            """)
            st.markdown(f"[View Discussion →]({post['url']})")
            st.markdown("---")
        
        st.markdown("### 📊 Download Raw Data")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Dataset:** {len(filtered_df):,} posts")
        with col2:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "📥 CSV",
                csv,
                f"community_pulse_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
    
    st.markdown("---")
    st.markdown("**Data:** Reddit & Twitter | **Analysis:** Sentiment scoring | Built with ❤️ for Long Beach")

else:
    st.error("❌ Data file not found")

else:
    st.error("❌ Data file not found")
    st.info("""
    **To generate data:**
    
    Run the data collection script to gather posts from Reddit and Twitter about Long Beach topics.
    The script analyzes sentiment and creates the community_pulse_data.csv file.
    
    See the repository for the data collection notebook.
    """)
