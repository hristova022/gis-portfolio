import os, json, math, datetime, re
import pandas as pd
import numpy as np
import requests
import streamlit as st
import plotly.express as px
import pydeck as pdk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer

st.set_page_config(page_title="Long Beach Community Voice — Past & Recent", page_icon="📣", layout="wide")

st.title("📣 Long Beach Community Voice (Past & Recent)")
st.subheader("Public posts summarized for a personal portfolio demo — **not a survey, not a prediction**.")

# ----------------------------
# Sidebar: data source & filters
# ----------------------------
with st.sidebar:
    st.header("Data")
    default_terms = "Long Beach OR #LongBeach OR #LBC OR Belmont Shore OR Alamitos OR Downtown Long Beach"
    query_text = st.text_input("Keywords/hashtags", value=default_terms, help="Use OR to combine terms")
    radius_km  = st.slider("Search radius (km)", 3, 30, 15, help="Around downtown Long Beach")
    days_back  = st.slider("Lookback (days)", 1, 10, 3)
    live_mode  = st.toggle("Use X API live (requires X_BEARER_TOKEN)", value=False)
    st.caption("If off, upload a CSV named **lb_posts.csv** with columns: id,created_at,text,longitude,latitude,source,topic,like_count,reply_count,retweet_count,score,num_comments,url,title")

# ----------------------------
# Data loader (X API or CSV)
# ----------------------------
@st.cache_data(show_spinner=False)
def fetch_x(query_text, radius_km, days_back, token):
    if not token:
        return pd.DataFrame()
    # Downtown LB
    lon, lat = -118.1937, 33.7701
    end   = datetime.datetime.utcnow()
    start = end - datetime.timedelta(days=int(days_back))
    q = f"({query_text}) lang:en -is:retweet point_radius:[{lon} {lat} {radius_km}km]"

    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": q,
        "start_time": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time":   end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_results": 100,
        "tweet.fields": "created_at,public_metrics,geo,lang",
        "expansions": "geo.place_id,author_id",
        "place.fields": "full_name,geo,name,place_type"
    }
    headers = {"Authorization": f"Bearer {token}"}

    all_rows, next_token = [], None
    for _ in range(5):  # up to ~500 posts
        if next_token:
            params["next_token"] = next_token
        r = requests.get(url, params=params, headers=headers, timeout=30)
        if r.status_code != 200:
            break
        js = r.json()
        data = js.get("data", [])
        places = {p["id"]: p for p in js.get("includes", {}).get("places", [])}
        for t in data:
            # Coordinates: point or place centroid
            lon2, lat2 = None, None
            if t.get("geo", {}).get("coordinates", {}).get("coordinates"):
                lon2, lat2 = t["geo"]["coordinates"]["coordinates"]  # [lon, lat]
            elif t.get("geo", {}).get("place_id") and t["geo"]["place_id"] in places:
                bbox = places[t["geo"]["place_id"]]["geo"].get("bbox")  # [w,s,e,n]
                if bbox:
                    w,s,e,n = bbox
                    lon2, lat2 = (w+e)/2.0, (s+n)/2.0
            pm = t.get("public_metrics", {}) or {}
            all_rows.append({
                "id": t.get("id"),
                "created_at": t.get("created_at"),
                "text": t.get("text"),
                "longitude": lon2,
                "latitude": lat2,
                "like_count": pm.get("like_count", 0),
                "retweet_count": pm.get("retweet_count", 0),
                "reply_count": pm.get("reply_count", 0),
                "source": "X/Twitter",
                "topic": ""
            })
        next_token = js.get("meta", {}).get("next_token")
        if not next_token:
            break

    df = pd.DataFrame(all_rows)
    return df

@st.cache_data(show_spinner=False)
def load_csv_or_upload():
    try:
        df = pd.read_csv("lb_posts.csv")
    except Exception:
        up = st.file_uploader("Upload lb_posts.csv", type=["csv"])
        if up:
            df = pd.read_csv(up)
        else:
            return pd.DataFrame()
    return df

if live_mode:
    token = os.getenv("X_BEARER_TOKEN", "")
    df = fetch_x(query_text, radius_km, days_back, token)
else:
    df = load_csv_or_upload()

if df.empty:
    st.info("No data yet. Turn on **Use X API live** (and set X_BEARER_TOKEN) or upload **lb_posts.csv**.")
    st.stop()

# Normalize expected columns (add if missing)
defaults = {
    "source": "Unknown",
    "topic": "Uncategorized",
    "sentiment": "",
    "polarity": np.nan,
    "score": 0,
    "num_comments": 0,
    "url": "",
    "title": "",
    "like_count": 0,
    "retweet_count": 0,
    "reply_count": 0,
    "longitude": np.nan,
    "latitude": np.nan,
}
for col, default in defaults.items():
    if col not in df.columns:
        df[col] = default

# Timestamps
df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
df = df.dropna(subset=["created_at"]).sort_values("created_at")

# ----------------------------
# Sentiment (VADER compound)
# ----------------------------
an = SentimentIntensityAnalyzer()
def score_sent(x):
    s = an.polarity_scores(str(x))["compound"]
    if s >= 0.05: lab = "Positive"
    elif s <= -0.05: lab = "Negative"
    else: lab = "Neutral"
    return s, lab

if df["sentiment"].eq("").any() or df["polarity"].isna().any():
    vals = df["text"].apply(score_sent)
    df["polarity"]  = [v[0] for v in vals]
    df["sentiment"] = [v[1] for v in vals]

# ----------------------------
# Filters (sidebar)
# ----------------------------
st.sidebar.header("Filters")
# Sources
sources = sorted(df["source"].dropna().unique().tolist())
sel_sources = st.sidebar.multiselect("Sources", sources, default=sources)
fdf = df[df["source"].isin(sel_sources)]

# Topics
topics = sorted([t for t in fdf["topic"].fillna("").unique().tolist() if t != ""])
if topics:
    sel_topics = st.sidebar.multiselect("Topics", topics, default=topics)
    if sel_topics:
        fdf = fdf[fdf["topic"].isin(sel_topics)]

# Date range
dmin = fdf["created_at"].min().date()
dmax = fdf["created_at"].max().date()
dr   = st.sidebar.date_input("Date range", (dmin, dmax))
if isinstance(dr, (list, tuple)) and len(dr) == 2:
    start = pd.to_datetime(dr[0], utc=True, errors="coerce")
    end   = pd.to_datetime(dr[1], utc=True, errors="coerce") + pd.Timedelta(days=1)
    fdf = fdf[(fdf["created_at"] >= start) & (fdf["created_at"] < end)]

if fdf.empty:
    st.warning("No posts with the current filters.")
    st.stop()

# ----------------------------
# Metrics (top row)
# ----------------------------
SENT_COLORS = {"Positive": "#2A9D8F", "Neutral": "#7A7A7A", "Negative": "#C2185B"}  # colorblind-friendly

n_posts = len(fdf)
pos_pct = fdf["sentiment"].eq("Positive").mean()*100.0
neg_pct = fdf["sentiment"].eq("Negative").mean()*100.0
avg_compound = fdf["polarity"].mean()

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Posts analyzed", f"{n_posts:,}")
with c2: st.metric("Positive share", f"{pos_pct:,.1f}%")
with c3: st.metric("Negative share", f"{neg_pct:,.1f}%")
with c4:
    label = "😊 Positive" if avg_compound >= 0.05 else "😐 Neutral" if avg_compound > -0.05 else "😟 Negative"
    st.metric("Avg sentiment (compound)", f"{avg_compound:.2f}", label)

st.markdown("---")

# ----------------------------
# 2-minute tour (plain)
# ----------------------------
with st.container(border=True):
    st.markdown("### What you're seeing (quick tour)")
    st.markdown("""
- **Share of tone** (positive / neutral / negative), **topics**, and **weekly trends** for public posts about Long Beach.
- **Engagement** is source-aware (Reddit uses score/comments; X uses likes/replies/retweets).
- **Map** shows geotagged posts when available (not all posts are geotagged).
- This reflects public online conversations — **not a representative poll** and **not a prediction**.
""")

# ----------------------------
# Visuals
# ----------------------------
colA, colB = st.columns([1,1])

# Sentiment share (100% stacked bar)
with colA:
    st.markdown("#### Tone share")
    share = fdf["sentiment"].value_counts(normalize=True).rename_axis("sentiment").reset_index(name="pct")
    share["pct"] = (share["pct"]*100.0).round(1)
    fig_share = px.bar(
        share, x=["All"], y="pct", color="sentiment",
        color_discrete_map=SENT_COLORS, text="pct",
        category_orders={"sentiment": ["Positive","Neutral","Negative"]},
    )
    fig_share.update_layout(showlegend=True, barmode="stack", height=260, margin=dict(l=10,r=10,t=10,b=10))
    fig_share.update_traces(texttemplate="%{text}%")
    st.plotly_chart(fig_share, use_container_width=True)

# Top topics
with colB:
    st.markdown("#### Top topics")
    if "topic" in fdf.columns and fdf["topic"].str.len().gt(0).any():
        tcounts = fdf.groupby("topic").size().sort_values(ascending=False).head(10).reset_index(name="count")
        fig_topics = px.bar(tcounts.sort_values("count"), y="topic", x="count", orientation="h")
        fig_topics.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_topics, use_container_width=True)
    else:
        st.caption("No topic labels in the data.")

# Weekly trend by sentiment
st.markdown("#### Weekly sentiment trend")
wk = fdf.set_index("created_at").resample("W")["sentiment"].value_counts().rename_axis(["week","sentiment"]).reset_index(name="count")
fig_trend = px.area(
    wk, x="week", y="count", color="sentiment", color_discrete_map=SENT_COLORS,
    category_orders={"sentiment": ["Positive","Neutral","Negative"]},
)
fig_trend.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10))
st.plotly_chart(fig_trend, use_container_width=True)

# Optional: map if we have coords
if {"latitude","longitude"}.issubset(fdf.columns):
    mdf = fdf.dropna(subset=["latitude","longitude"])
    if not mdf.empty:
        st.markdown("#### Where posts are geotagged")
        figm = px.scatter_mapbox(
            mdf, lat="latitude", lon="longitude", color="sentiment",
            color_discrete_map=SENT_COLORS, hover_name="topic",
            hover_data={"sentiment":True, "polarity":":.2f"},
            zoom=11, height=380
        )
        figm.update_layout(mapbox_style="carto-positron", margin=dict(l=0,r=0,t=0,b=0), legend=dict(orientation="h"))
        st.plotly_chart(figm, use_container_width=True)

# Time-of-day heatmap (fun + useful)
st.markdown("#### When people post (local time-of-day vs day-of-week)")
tz = "America/Los_Angeles"
tdf = fdf.copy()
tdf["ts_local"] = tdf["created_at"].dt.tz_convert(tz)
tdf["hour"] = tdf["ts_local"].dt.hour
tdf["dow"]  = tdf["ts_local"].dt.day_name()
order_dow = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
hv = tdf.groupby(["dow","hour"]).size().reset_index(name="count")
hv["dow"] = pd.Categorical(hv["dow"], order_dow)
hv = hv.pivot(index="dow", columns="hour", values="count").fillna(0)
fig_heat = px.imshow(hv, aspect="auto", color_continuous_scale="Viridis", labels=dict(color="Posts"))
fig_heat.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10))
st.plotly_chart(fig_heat, use_container_width=True)

# Keyword bars (quick TF count)
st.markdown("#### Frequent keywords")
stop = set("""
the a an and or but if while is are was were be have has had do does did of to for from in on at by with into over under near after before during between
this that those these there here out up down off about across around again more most less least just very really
long beach lb downtown city police school schools parking traffic street streets water beach beaches park parks
""".split())
def tokenize(texts, topn=20):
    cv = CountVectorizer(
        lowercase=True, stop_words="english",
        token_pattern=r"(?u)\b[A-Za-z][A-Za-z\-']{2,}\b", max_features=5000
    )
    X = cv.fit_transform(texts)
    vocab = np.array(cv.get_feature_names_out())
    counts = np.asarray(X.sum(axis=0)).ravel()
    tbl = pd.DataFrame({"term": vocab, "count": counts}).sort_values("count", ascending=False)
    tbl = tbl[~tbl["term"].isin(stop)]
    return tbl.head(topn)

kw = tokenize(fdf["text"].astype(str).tolist(), 25)
if not kw.empty:
    fig_kw = px.bar(kw.sort_values("count"), y="term", x="count", orientation="h")
    fig_kw.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
    st.plotly_chart(fig_kw, use_container_width=True)

st.markdown("---")

# Top posts (source-aware engagement)
st.markdown("### Top posts")
def engagement_row(r):
    src = str(r.get("source", "Unknown")).lower()
    if "reddit" in src:
        return (r.get("score", 0) or 0) + 2*(r.get("num_comments", 0) or 0)
    if "twitter" in src or "x" in src:
        return (r.get("like_count", 0) or 0) + 2*(r.get("reply_count", 0) or 0) + 3*(r.get("retweet_count", 0) or 0)
    return 0

fdf["engagement"] = fdf.apply(engagement_row, axis=1)
top = fdf.nlargest(10, "engagement")

for _, p in top.iterrows():
    title = (str(p.get("title") or p.get("text") or "")).strip()
    if len(title) > 140: title = title[:140] + "…"
    link  = p.get("url") or ""
    cols = st.columns([6,1,1,1])
    with cols[0]:
        if link:
            st.markdown(f"**[{title}]({link})**")
        else:
            st.markdown(f"**{title}**")
        st.caption(f"{p.get('source','Unknown')} • {p['created_at'].strftime('%b %d, %Y')} • Sentiment: {p.get('sentiment','')}")
    with cols[1]: st.metric("Likes", int(p.get("like_count", 0)))
    with cols[2]: st.metric("Replies", int(p.get("reply_count", 0)))
    with cols[3]: st.metric("Retweets", int(p.get("retweet_count", 0)))
    st.divider()

# Download
st.download_button("Download current view (CSV)", data=fdf.to_csv(index=False), file_name="lb_community_voice_filtered.csv")

# ----------------------------
# Methodology & Data Use
# ----------------------------
with st.expander("🧪 Methodology & data use", expanded=False):
    st.markdown("""
**Scope**
- Public posts about Long Beach collected via keywords/hashtags and geofence around downtown.

**Sentiment**
- VADER compound score (−1 to +1); Positive ≥ +0.05, Negative ≤ −0.05, else Neutral.

**Engagement (ranking)**
- Reddit: `score + 2×comments`
- X/Twitter: `likes + 2×replies + 3×retweets`

**Map**
- Shows posts with coordinates or place centroids when available (many posts are not geotagged).

**Use & privacy (portfolio)**
- Personal demonstration only; no ads/resale; no DMs; respects platform rules and deletions.
- Stores IDs, timestamps, and aggregates; displays links to originals, not usernames.
""")

st.caption("Summarizes public online conversations about Long Beach. Not representative of residents, and not an official city view.")
