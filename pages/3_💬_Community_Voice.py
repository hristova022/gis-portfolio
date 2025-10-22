import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Long Beach Community Pulse", page_icon="💬", layout="wide")

# Enhanced Dark Mode CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E40AF;
        margin-bottom: 1rem;
    }
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
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Trends", "☁️ Word Clouds", "📝 Top Posts & Data"])
    
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
        
        # Key insights
        st.subheader("💡 Key Insights")
        
        most_discussed = filtered_df['topic'].value_counts().index[0] if len(filtered_df) > 0 else "N/A"
        most_discussed_count = filtered_df['topic'].value_counts().iloc[0] if len(filtered_df) > 0 else 0
        
        topic_sentiment_avg = filtered_df.groupby('topic')['polarity'].mean().sort_values()
        most_positive = topic_sentiment_avg.index[-1] if len(topic_sentiment_avg) > 0 else "N/A"
        most_negative = topic_sentiment_avg.index[0] if len(topic_sentiment_avg) > 0 else "N/A"
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="insight-box">
            <strong>🔥 Hottest Topic:</strong> {most_discussed} ({most_discussed_count} posts)<br>
            <strong>😊 Most Positive:</strong> {most_positive}<br>
            <strong>😟 Most Negative:</strong> {most_negative}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            positive_pct = (filtered_df['sentiment'] == 'Positive').sum() / len(filtered_df) * 100
            negative_pct = (filtered_df['sentiment'] == 'Negative').sum() / len(filtered_df) * 100
            
            st.markdown(f"""
            <div class="insight-box">
            <strong>📊 Sentiment Breakdown:</strong><br>
            Positive: {positive_pct:.1f}%<br>
            Negative: {negative_pct:.1f}%<br>
            Neutral: {100-positive_pct-negative_pct:.1f}%
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Opinion Trends Over Time")
        st.caption("Weekly average sentiment - spot trends and patterns")
        
        time_series = filtered_df.set_index('created_utc').resample('W')['polarity'].mean().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_series['created_utc'],
            y=time_series['polarity'],
            mode='lines+markers',
            name='Opinion Score',
            line=dict(color='#818CF8', width=3),
            fill='tozeroy',
            fillcolor='rgba(129, 140, 248, 0.2)'
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
        fig.update_layout(
            xaxis_title="Week",
            yaxis_title="Average Sentiment Score",
            hovermode='x unified',
            yaxis_range=[-1, 1]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Discussion Volume")
            st.caption("Posts per week")
            volume = filtered_df.set_index('created_utc').resample('W').size().reset_index(name='count')
            fig = px.bar(volume, x='created_utc', y='count', color_discrete_sequence=['#A78BFA'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Sentiment Distribution Over Time")
            st.caption("How opinions evolve")
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
        st.subheader("Most Common Words")
        st.caption("Bigger words appear more frequently")
        
        col1, col2, col3 = st.columns(3)
        
        for col, sentiment, color in zip([col1, col2, col3], 
                                         ['Positive', 'Neutral', 'Negative'],
                                         ['Greens', 'Oranges', 'Reds']):
            with col:
                st.write(f"**{sentiment}**")
                sentiment_text = ' '.join(filtered_df[filtered_df['sentiment'] == sentiment]['combined_text'].dropna())
                
                if sentiment_text:
                    wordcloud = WordCloud(
                        width=400,
                        height=300,
                        background_color='white',
                        colormap=color,
                        max_words=50
                    ).generate(sentiment_text)
                    
                    fig, ax = plt.subplots(figsize=(5, 4))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                else:
                    st.info(f"No {sentiment.lower()} posts")
    
    with tab4:
        st.subheader("📌 Top Engaged Posts")
        st.caption("Most liked and commented discussions")
        
        # Calculate engagement score
        filtered_df['engagement'] = filtered_df['score'] + (filtered_df['num_comments'] * 2)
        top_posts = filtered_df.nlargest(15, 'engagement')
        
        # Sentiment filter
        sentiment_filter = st.radio("Filter:", ["All", "Positive", "Neutral", "Negative"], horizontal=True)
        
        if sentiment_filter != "All":
            top_posts = top_posts[top_posts['sentiment'] == sentiment_filter]
        
        # Display posts
        for idx, post in top_posts.iterrows():
            emoji = {'Positive': '🟢', 'Neutral': '🟡', 'Negative': '🔴'}[post['sentiment']]
            
            with st.container():
                st.markdown(f"""
                <div class="highlight-box">
                <strong>{emoji} {post['title'][:120]}...</strong><br>
                <small>
                📅 {post['created_utc'].strftime('%Y-%m-%d')} | 
                📊 {post['source']} | 
                🏷️ {post['topic']} | 
                ⭐ {post['score']} points | 
                💬 {post['num_comments']} comments | 
                📈 Sentiment: {post['polarity']:.2f}
                </small><br>
                <a href="{post['url']}" target="_blank" style="color: #818CF8;">View Discussion →</a>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Raw Data Section
        st.subheader("📊 Download Raw Data")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**Dataset Info:** {len(filtered_df):,} posts | "
                    f"{len(filtered_df['topic'].unique())} topics | "
                    f"Date range: {filtered_df['created_utc'].min().strftime('%Y-%m-%d')} to "
                    f"{filtered_df['created_utc'].max().strftime('%Y-%m-%d')}")
        
        with col2:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                f"community_pulse_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        # Show sample with selected columns
        with st.expander("👁️ Preview Data (50 most recent posts)"):
            display_cols = ['created_utc', 'source', 'topic', 'sentiment', 'polarity', 'title', 'score', 'num_comments']
            available_cols = [col for col in display_cols if col in filtered_df.columns]
            
            st.dataframe(
                filtered_df[available_cols].sort_values('created_utc', ascending=False).head(50),
                use_container_width=True,
                height=400
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #9CA3AF;'>
        <p><strong>Data:</strong> Reddit r/longbeach, Twitter/X | 
        <strong>Analysis:</strong> TextBlob sentiment scoring | 
        <strong>Updated:</strong> {}</p>
        <p><em>This tracks online discussions, not comprehensive public opinion. See "About This Dashboard" for limitations.</em></p>
        <p>Built with Streamlit and ❤️ for Long Beach</p>
    </div>
    """.format(datetime.now().strftime('%B %d, %Y')), unsafe_allow_html=True)

else:
    st.error("❌ Data file not found")
    st.info("""
    **To generate data:**
    
    Run the data collection script to gather posts from Reddit and Twitter about Long Beach topics.
    The script analyzes sentiment and creates the community_pulse_data.csv file.
    
    See the repository for the data collection notebook.
    """)
