import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Long Beach Community Voice", page_icon="🔍", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .big-title {
        font-size: 3rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="big-title">🔍 Long Beach Community Voice</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Community Opinion Dashboard - Real-time sentiment analysis of Long Beach topics</div>', unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    try:
        reddit_df = pd.read_csv('reddit_sentiment_data.csv')
        reddit_df['created_utc'] = pd.to_datetime(reddit_df['created_utc'])
        return reddit_df
    except FileNotFoundError:
        st.error("Data files not found. Please run the Colab notebook first!")
        return None

reddit_df = load_data()

if reddit_df is not None:
    # Sidebar filters
    st.sidebar.header("🎛️ Filters")
    
    # Topic filter
    topics = st.sidebar.multiselect("Topics", reddit_df['topic'].unique(), default=reddit_df['topic'].unique())
    filtered_df = reddit_df[reddit_df['topic'].isin(topics)]
    
    # Date range
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
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Posts/Reviews", len(filtered_df))
    
    with col2:
        positive_pct = (filtered_df['sentiment'] == 'Positive').sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
        st.metric("Positive Sentiment", f"{positive_pct:.1f}%")
    
    with col3:
        negative_pct = (filtered_df['sentiment'] == 'Negative').sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
        st.metric("Negative Sentiment", f"{negative_pct:.1f}%")
    
    with col4:
        avg_polarity = filtered_df['polarity'].mean() if len(filtered_df) > 0 else 0
        st.metric("Avg Sentiment Score", f"{avg_polarity:.2f}")
    
    st.markdown("---")
    
    # Visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Trends", "☁️ Word Clouds", "📝 Raw Data"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sentiment Distribution")
            sentiment_counts = filtered_df['sentiment'].value_counts()
            fig = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                color=sentiment_counts.index,
                color_discrete_map={'Positive': '#10B981', 'Neutral': '#F59E0B', 'Negative': '#EF4444'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Sentiment by Topic")
            topic_sentiment = filtered_df.groupby(['topic', 'sentiment']).size().reset_index(name='count')
            fig = px.bar(
                topic_sentiment,
                x='topic',
                y='count',
                color='sentiment',
                color_discrete_map={'Positive': '#10B981', 'Neutral': '#F59E0B', 'Negative': '#EF4444'},
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Sentiment Over Time")
        
        # Resample by day
        time_series = filtered_df.set_index('created_utc').resample('D')['polarity'].mean().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_series['created_utc'],
            y=time_series['polarity'],
            mode='lines+markers',
            name='Sentiment',
            line=dict(color='#667eea', width=2),
            fill='tozeroy'
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Average Sentiment Score",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Volume over time
        st.subheader("Post/Review Volume Over Time")
        volume = filtered_df.set_index('created_utc').resample('D').size().reset_index(name='count')
        fig = px.bar(volume, x='created_utc', y='count', color_discrete_sequence=['#764ba2'])
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Word Clouds by Sentiment")
        
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
                        colormap=color
                    ).generate(sentiment_text)
                    
                    fig, ax = plt.subplots(figsize=(5, 4))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                else:
                    st.info(f"No {sentiment.lower()} posts/reviews in selection")
    
    with tab4:
        st.subheader("Raw Data Explorer")
        
        # Display columns selector
        display_cols = st.multiselect(
            "Select columns to display",
            filtered_df.columns.tolist(),
            default=['source', 'topic', 'sentiment', 'polarity', 'created_utc']
        )
        
        if display_cols:
            st.dataframe(
                filtered_df[display_cols].sort_values('created_utc', ascending=False),
                use_container_width=True
            )
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"sentiment_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748B;'>
        <p>💡 Data collected from Reddit (r/longbeach) | Updated periodically</p>
        <p>Built with Streamlit, TextBlob, and ❤️</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Please run the Colab notebook to collect and analyze data first!")
