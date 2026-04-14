import streamlit as st
import duckdb
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image

st.title("🎮 Lila Player Journey Tool")
st.markdown("### 🎯 Player Journey Visualization Tool")
st.markdown("Analyze player movement, events, and hotspots on game maps")

@st.cache_data
def load_data():
    con = duckdb.connect()
    df = con.execute("""
        SELECT * FROM read_parquet('player_data/February_*/*.parquet')
LIMIT 200000
    """).df()

    def clean_event(value):
        if value is None:
            return "Unknown"
        if isinstance(value, (bytes, bytearray)):
            return bytes(value).decode("utf-8", errors="ignore")
        return str(value)

    df["event"] = df["event"].apply(clean_event)
    df["ts"] = df["ts"].astype("datetime64[ns]")
    df["ts_numeric"] = df["ts"].astype("int64") // 10**9

    return df

df = load_data()

# ---------------- FILTERS ----------------
st.sidebar.header("Filters")

selected_map = st.sidebar.selectbox("Select Map", df["map_id"].unique())
map_df = df[df["map_id"] == selected_map]

selected_match = st.sidebar.selectbox("Select Match", map_df["match_id"].unique())
match_df = map_df[map_df["match_id"] == selected_match]

selected_player = st.sidebar.selectbox("Select Player", match_df["user_id"].unique())
filtered_df = match_df[match_df["user_id"] == selected_player].sort_values("ts_numeric")

# ---------------- METRICS ----------------
col1, col2, col3 = st.columns(3)
col1.metric("Players", match_df["user_id"].nunique())
col2.metric("Events", len(match_df))
col3.metric("Event Types", match_df["event"].nunique())

# ---------------- PLAYBACK ----------------
min_time = int(filtered_df["ts_numeric"].min())
max_time = int(filtered_df["ts_numeric"].max())

if min_time == max_time:
    st.warning("Only one timestamp — playback disabled")
    playback_df = filtered_df
else:
    selected_time = st.slider("Playback", min_time, max_time, max_time)
    playback_df = filtered_df[filtered_df["ts_numeric"] <= selected_time]

# ---------------- MAP IMAGE FIX ----------------
map_paths = {
    "AmbroseValley": "player_data/minimaps/AmbroseValley_Minimap.png",
    "GrandRift": "player_data/minimaps/GrandRift_Minimap.png",
    "Lockdown": "player_data/minimaps/Lockdown_Minimap.jpg"
}

map_image_path = map_paths.get(selected_map)

try:
    img = Image.open(map_image_path)
except:
    st.error(f"Map image not found: {map_image_path}")
    st.stop()

# ---------------- NORMALIZATION ----------------
x_min, x_max = map_df["x"].min(), map_df["x"].max()
y_min, y_max = map_df["y"].min(), map_df["y"].max()

x_norm = (playback_df["x"] - x_min) / (x_max - x_min) * img.size[0]
y_norm = (playback_df["y"] - y_min) / (y_max - y_min) * img.size[1]
y_norm = img.size[1] - y_norm

# ---------------- PLOT ----------------
fig = go.Figure()

fig.add_layout_image(
    dict(
        source=img,
        x=0,
        y=img.size[1],
        sizex=img.size[0],
        sizey=img.size[1],
        xref="x",
        yref="y",
        layer="below"
    )
)

fig.add_trace(go.Scatter(
    x=x_norm,
    y=y_norm,
    mode="lines",
    line=dict(color="red"),
    name="Path"
))

for event in playback_df["event"].unique():
    event_df = playback_df[playback_df["event"] == event]

    x_e = (event_df["x"] - x_min) / (x_max - x_min) * img.size[0]
    y_e = (event_df["y"] - y_min) / (y_max - y_min) * img.size[1]
    y_e = img.size[1] - y_e

    fig.add_trace(go.Scatter(
        x=x_e,
        y=y_e,
        mode="markers",
        name=event,
        marker=dict(size=6)
    ))

fig.update_layout(
    width=800,
    height=800,
    title="Player Movement",
    xaxis=dict(visible=False),
    yaxis=dict(visible=False)
)

st.plotly_chart(fig)

# ---------------- HEATMAP ----------------
st.subheader("🔥 Heatmap")

heat_df = match_df

x_h = (heat_df["x"] - x_min) / (x_max - x_min) * img.size[0]
y_h = (heat_df["y"] - y_min) / (y_max - y_min) * img.size[1]
y_h = img.size[1] - y_h

heatmap = px.density_heatmap(x=x_h, y=y_h, nbinsx=50, nbinsy=50)
st.plotly_chart(heatmap)