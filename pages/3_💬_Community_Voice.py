import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Long Beach Community Voice", page_icon="💬", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .big-title {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.3rem;
        color: #475569;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    .info-box {
        background: #F8FAFC;
        border-left: 4px solid #667eea;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
    }
    .methodology-box {
        background: #FFF7ED;
        border-left: 4px solid #F59E0B;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="big-title">💬 Long Beach Community Voice</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Real-time sentiment analysis of community discussions about Long Beach</div>', unsafe_allow_html=True)

# Why This Matters Section
with st.expander("ℹ️ Why This Dashboard Matters", expanded=False):
    st.markdown("""
    <div class="info-box">
    <h3>Understanding Community Sentiment</h3>
    <p>This dashboard analyzes thousands of real conversations from Long Beach residents to reveal:</p>
    <ul>
        <li><strong>What issues matter most</strong> to the community right now</li>
        <li><strong>How residents feel</strong> about key topics like housing, safety, and development</li>
        <li><strong>Sentiment trends over time</strong> - are concerns improving or worsening?</li>
        <li><strong>Unfiltered community voice</strong> - what people actually say, not just official reports</li>
    </ul>
    <p><strong>Use cases:</strong></p>
    <ul>
        <li>📊 Policymakers: Understand constituent concerns in real-time</li>
        <li>🏘️ Community organizers: Identify emerging issues</li>
        <li>📰 Journalists: Track public opinion trends</li>
        <li>👥 Residents: See what your neighbors are talking about</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Methodology Section
with st.expander("🔬 Methodology & Data Sources", expanded=False):
    st.markdown("""
    <div class="methodology-box">
    <h3>How We Analyze Community Sentiment</h3>
    
    <h4>📊 Data Collection</h4>
    <ul>
        <li><strong>Source:</strong> Reddit's r/longbeach community (10,000+ members)</li>
        <li><strong>Time Period:</strong> Rolling 6-month window, updated regularly</li>
        <li><strong>Topics Tracked:</strong> Homelessness, crime/safety, development, parking, housing, traffic</li>
        <li><strong>Volume:</strong> Hundreds of posts and thousands of comments analyzed</li>
    </ul>
    
    <h4>🤖 Sentiment Analysis</h4>
    <ul>
        <li><strong>Technology:</strong> TextBlob Natural Language Processing (NLP) library</li>
        <li><strong>Method:</strong> Each post is scored for:
            <ul>
                <li><em>Polarity:</em> -1 (very negative) to +1 (very positive)</li>
                <li><em>Subjectivity:</em> 0 (objective facts) to 1 (subjective opinions)</li>
            </ul>
        </li>
        <li><strong>Classification:</strong> Posts are categorized as Positive, Neutral, or Negative based on polarity scores</li>
    </ul>
    
    <h4>⚠️ Limitations</h4>
    <ul>
        <li><strong>Reddit demographic:</strong> May not represent all Long Beach residents (tends younger, more tech-savvy)</li>
        <li><strong>Self-selection bias:</strong> People with strong opinions are more likely to post</li>
        <li><strong>Sarcasm detection:</strong> NLP can struggle with sarcasm and nuanced language</li>
        <li><strong>Single platform:</strong> Currently only analyzes Reddit. Future versions may include:
            <ul>
                <li>Nextdoor (no public API currently available)</li>
                <li>Twitter/X mentions of Long Beach</li>
                <li>Local news comment sections</li>
            </ul>
        </li>
    </ul>
    
    <h4>🔄 Updates</h4>
    <p>Data is collected and analyzed periodically. Last update: {}</p>
    </div>
    """.format(datetime.now().strftime("%B %d, %Y")), unsafe_allow_html=True)

st.markdown("---")

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
        
        # Resample by week for better 6-month view
        time_series = filtered_df.set_index('created_utc').resample('W')['polarity'].mean().reset_index()
        
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
        volume = filtered_df.set_index('created_utc').resample('W').size().reset_index(name='count')
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
        <p>💡 <strong>Data Source:</strong> Reddit r/longbeach community | <strong>Analysis:</strong> TextBlob NLP | <strong>Updated:</strong> Periodically</p>
        <p><em>Note: Reddit demographics may not represent all Long Beach residents. Future updates will include additional platforms.</em></p>
        <p>Built with Streamlit, TextBlob, PRAW, and ❤️ for Long Beach</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Please run the Colab notebook to collect and analyze data first!")
    
    st.info("""
    **💡 About Data Collection:**
    
    This dashboard currently analyzes Reddit discussions from r/longbeach. 
    
    **Future enhancements may include:**
    - Nextdoor (pending API access)
    - Twitter/X Long Beach mentions
    - Local news comment sections
    - City council meeting transcripts
    
    Reddit provides a great snapshot of community sentiment, though it may skew towards younger, 
    more tech-savvy residents. We acknowledge this limitation and aim to expand data sources over time.
    """)
