import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Long Beach Community Pulse", page_icon="💬", layout="wide")

# Dark Mode CSS
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
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">💬 Long Beach Community Pulse</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-platform opinion tracking powered by AI</div>', unsafe_allow_html=True)

# Load data with detailed error messages
@st.cache_data
def load_data():
    import os
    
    # Debug: Show what files exist
    st.sidebar.write("🔍 Debug: Files in root directory:")
    try:
        files = os.listdir('.')
        for f in files[:10]:
            st.sidebar.write(f"  - {f}")
    except Exception as e:
        st.sidebar.error(f"Can't list files: {e}")
    
    # Try to load the data
    try:
        df = pd.read_csv('community_pulse_data.csv')
        st.sidebar.success(f"✅ Loaded community_pulse_data.csv ({len(df)} rows)")
        df['created_utc'] = pd.to_datetime(df['created_utc'])
        return df
    except FileNotFoundError:
        st.sidebar.error("❌ community_pulse_data.csv not found")
        
        # Try reddit_sentiment_data.csv as backup
        try:
            df = pd.read_csv('reddit_sentiment_data.csv')
            st.sidebar.warning("⚠️ Using reddit_sentiment_data.csv instead")
            df['created_utc'] = pd.to_datetime(df['created_utc'])
            return df
        except:
            st.sidebar.error("❌ reddit_sentiment_data.csv also not found")
            return None
    except Exception as e:
        st.sidebar.error(f"❌ Error loading data: {e}")
        return None

# Load the data
data_df = load_data()

if data_df is not None:
    st.success(f"📊 Analyzing {len(data_df):,} community posts")
    
    # Show data sources
    sources = data_df['source'].unique() if 'source' in data_df.columns else ['Unknown']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Posts", f"{len(data_df):,}")
    with col2:
        if 'Reddit' in sources:
            reddit_count = len(data_df[data_df['source'] == 'Reddit']) if 'source' in data_df.columns else 0
            st.metric("🔴 Reddit", f"{reddit_count:,}")
    with col3:
        if 'Twitter' in sources:
            twitter_count = len(data_df[data_df['source'] == 'Twitter']) if 'source' in data_df.columns else 0
            st.metric("🐦 Twitter", f"{twitter_count:,}")
    with col4:
        avg_sentiment = data_df['polarity'].mean() if 'polarity' in data_df.columns else 0
        st.metric("Avg Sentiment", f"{avg_sentiment:.2f}")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Trends", "📝 Data"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sentiment Distribution")
            if 'sentiment' in data_df.columns:
                sentiment_counts = data_df['sentiment'].value_counts()
                fig = px.pie(
                    values=sentiment_counts.values,
                    names=sentiment_counts.index,
                    color=sentiment_counts.index,
                    color_discrete_map={'Positive': '#10B981', 'Neutral': '#F59E0B', 'Negative': '#EF4444'},
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No sentiment column found")
        
        with col2:
            st.subheader("Opinion by Topic")
            if 'topic' in data_df.columns and 'sentiment' in data_df.columns:
                topic_sentiment = data_df.groupby(['topic', 'sentiment']).size().reset_index(name='count')
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
            else:
                st.error("Missing topic or sentiment columns")
    
    with tab2:
        st.subheader("Sentiment Over Time")
        
        if 'created_utc' in data_df.columns and 'polarity' in data_df.columns:
            time_series = data_df.set_index('created_utc').resample('W')['polarity'].mean().reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time_series['created_utc'],
                y=time_series['polarity'],
                mode='lines+markers',
                name='Sentiment',
                line=dict(color='#818CF8', width=2),
                fill='tozeroy'
            ))
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Average Sentiment",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Missing time or sentiment data")
        
        # Volume
        st.subheader("Discussion Volume")
        if 'created_utc' in data_df.columns:
            volume = data_df.set_index('created_utc').resample('W').size().reset_index(name='count')
            fig = px.bar(volume, x='created_utc', y='count', color_discrete_sequence=['#A78BFA'])
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Raw Data")
        
        # Show available columns
        st.write("**Available columns:**", list(data_df.columns))
        
        # Display data
        st.dataframe(data_df.head(50), use_container_width=True)
        
        # Download
        csv = data_df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"community_pulse_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #9CA3AF;'>
        <p>💡 Data from Reddit & Twitter | Analyzed with TextBlob NLP</p>
        <p>Built with ❤️ for Long Beach</p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("❌ Could not load data file")
    
    st.info("""
    **Troubleshooting:**
    1. Check the sidebar for debug info
    2. Verify community_pulse_data.csv exists in the repo root
    3. Try rebooting the Streamlit app
    4. Check Streamlit logs for errors
    """)
    
    # Show what we tried
    st.write("**Attempted to load:**")
    st.write("- community_pulse_data.csv")
    st.write("- reddit_sentiment_data.csv")
