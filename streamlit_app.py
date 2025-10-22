import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Long Beach GIS Portfolio",
    page_icon="🏖️",
    layout="wide"
)

# Header
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E40AF;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.5rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 3rem;
    }
    .project-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: white;
    }
    .project-card h3 {
        color: white;
        margin-bottom: 1rem;
    }
    .project-card p {
        color: #F3F4F6;
        line-height: 1.6;
    }
    .feature-box {
        background: #F8FAFC;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏖️ Long Beach GIS Portfolio</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Data-driven insights for Long Beach, California</div>', unsafe_allow_html=True)

# Introduction
st.markdown("""
Welcome to my GIS and data analysis portfolio focused on Long Beach, California. 
This collection of interactive dashboards explores urban challenges, community sentiment, 
and spatial patterns using real-world data and modern analytical techniques.
""")

st.markdown("---")

# Featured Projects
st.header("📊 Featured Dashboards")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="project-card">
    <h3>💬 Community Pulse</h3>
    <p><strong>Track online conversations about Long Beach</strong></p>
    <p>Analyzes thousands of posts from Reddit and Twitter to identify trending topics, 
    track sentiment, and monitor community discussions. Uses natural language processing 
    to understand what residents are talking about.</p>
    <ul>
        <li>📊 6 months of community discussions</li>
        <li>🤖 AI sentiment analysis with TextBlob</li>
        <li>📈 Trend tracking over time</li>
        <li>☁️ Word clouds and topic analysis</li>
    </ul>
    <p><em>Topics: Housing, homelessness, crime, parking, traffic, development</em></p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="project-card">
    <h3>🏠 Homelessness Resources</h3>
    <p><strong>Mapping services and support locations</strong></p>
    <p>Interactive map showing shelters, services, and resources for people 
    experiencing homelessness in Long Beach. Helps connect people to critical services.</p>
    <ul>
        <li>🗺️ Interactive resource map</li>
        <li>📍 Service locations and details</li>
        <li>🏥 Healthcare and support facilities</li>
        <li>🍽️ Food and emergency services</li>
    </ul>
    <p><em>Vital community resource mapping</em></p>
    </div>
    """, unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div class="project-card">
    <h3>🅿️ Parking Analysis</h3>
    <p><strong>Understanding parking patterns and availability</strong></p>
    <p>Analyzes parking data to identify problem areas, peak times, and opportunities 
    for improvement in Long Beach parking infrastructure.</p>
    <ul>
        <li>📊 Usage patterns and trends</li>
        <li>🕐 Peak hour analysis</li>
        <li>🗺️ Spatial distribution maps</li>
        <li>💡 Data-driven recommendations</li>
    </ul>
    <p><em>Solving real urban mobility challenges</em></p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="project-card">
    <h3>🔥 Wildfire Analysis</h3>
    <p><strong>Historical wildfire data and patterns</strong></p>
    <p>Examines past and present wildfire activity near Long Beach to understand 
    historical patterns and inform preparedness efforts.</p>
    <ul>
        <li>📅 Historical fire data</li>
        <li>🗺️ Geographic patterns</li>
        <li>📈 Temporal trends</li>
        <li>🎯 Risk area identification</li>
    </ul>
    <p><em>Climate and disaster preparedness insights</em></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# About the Portfolio
st.header("🎯 About This Portfolio")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-box">
    <h4>🛠️ Technologies Used</h4>
    <ul>
        <li>Python & Pandas</li>
        <li>Streamlit</li>
        <li>Plotly & Matplotlib</li>
        <li>Natural Language Processing</li>
        <li>GIS & Spatial Analysis</li>
        <li>Web Scraping & APIs</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
    <h4>📊 Data Sources</h4>
    <ul>
        <li>Reddit & Twitter APIs</li>
        <li>City of Long Beach Open Data</li>
        <li>California Fire Data</li>
        <li>Census & Demographics</li>
        <li>Public Transportation Data</li>
        <li>Community Resources</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-box">
    <h4>🎓 Skills Demonstrated</h4>
    <ul>
        <li>Data Collection & Cleaning</li>
        <li>Sentiment Analysis (NLP)</li>
        <li>Spatial Analysis & Mapping</li>
        <li>Interactive Visualization</li>
        <li>Statistical Analysis</li>
        <li>Dashboard Development</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Why Long Beach
st.header("🏖️ Why Long Beach?")

st.markdown("""
Long Beach is California's 7th largest city with a diverse population of nearly 500,000 residents. 
As a coastal city facing challenges common to many urban areas—housing affordability, homelessness, 
traffic congestion, and climate change—it provides an excellent case study for applying GIS and 
data analysis techniques to real-world urban problems.

These dashboards demonstrate how data can inform community understanding, support decision-making, 
and make complex urban issues more accessible to residents, policymakers, and researchers.
""")

# Getting Started
st.info("""
👈 **Use the sidebar to navigate between dashboards.** Each page is interactive—explore the data, 
filter by topics or dates, and discover insights about Long Beach!
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748B;'>
    <p><strong>Long Beach GIS Portfolio</strong> | Built with Streamlit and Python</p>
    <p>Data analysis and visualization for community insight</p>
</div>
""", unsafe_allow_html=True)
