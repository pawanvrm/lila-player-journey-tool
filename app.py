import streamlit as st
import duckdb
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image

# -----------------------------
# 🎮 HEADER
# -----------------------------
st.title("🎮 Lila Player Journey Tool")
st.markdown("### 🎯 Player Journey Visualization Tool")
st.markdown("Analyze player movement, events, and hotspots on game maps")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    con = duckdb.connect()
    df = con.execute("""
        SELECT * FROM read_parquet('player_data/February_*/*')
    """).df()

    # Clean event column
    def clean_event(value):
        if value is None:
            return "Unknown"
        if isinstance(value, (bytes, bytearray, memoryview)):
            try:
                return bytes(value).decode("utf-8", errors="ignore")
            except:
                return str(value)

        s = str(value)
        if s.startswith("bytearray(b'") and s.endswith("')"):
            s = s[len("bytearray(b'"):-2]
        elif s.startswith("b'") and s.endswith("'"):
            s = s[2:-1]
        return s

    df["event"] = df["event"].apply(clean_event)

    # Timestamp handling
    df["ts"] = df["ts"].astype("datetime64[ns]")
    df["ts_numeric"] = df["ts"].astype("int64") // 10**9

    return df

df = load_data()

# -----------------------------
# 🎯 FILTERS
# -----------------------------
st.sidebar.header("Filters")

selected_map = st.sidebar.selectbox("Select Map", df["map_id"].unique())
map_df = df[df["map_id"] == selected_map]

selected_match = st.sidebar.selectbox("Select Match", map_df["match_id"].unique())
match_df = map_df[map_df["match_id"] == selected_match]

selected_player = st.sidebar.selectbox("Select Player", match_df["user_id"].unique())
filtered_df = match_df[match_df["user_id"] == selected_player].sort_values("ts_numeric")

# -----------------------------
# 📊 QUICK METRICS (NEW)
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Players in Match", match_df["user_id"].nunique())
col2.metric("Total Events", len(match_df))
col3.metric("Unique Events", match_df["event"].nunique())

# -----------------------------
# ⏱️ PLAYBACK
# -----------------------------
min_time = int(filtered_df["ts_numeric"].min())
max_time = int(filtered_df["ts_numeric"].max())

if min_time == max_time:
    st.warning("⚠️ Only one timestamp available — playback disabled")
    st.info("👉 Try selecting another player with more activity")
    playback_df = filtered_df
else:
    selected_time = st.slider(
        "⏱️ Playback Time",
        min_value=min_time,
        max_value=max_time,
        value=max_time
    )
    playback_df = filtered_df[filtered_df["ts_numeric"] <= selected_time]

# -----------------------------
# 🗺️ LOAD MAP
# -----------------------------
map_image_path = f"player_data/minimaps/{selected_map}_Minimap.png"
img = Image.open(map_image_path)

# -----------------------------
# 🎯 COORDINATE NORMALIZATION
# -----------------------------
x_min, x_max = map_df["x"].min(), map_df["x"].max()
y_min, y_max = map_df["y"].min(), map_df["y"].max()

x_norm = (playback_df["x"] - x_min) / (x_max - x_min) * img.size[0]
y_norm = (playback_df["y"] - y_min) / (y_max - y_min) * img.size[1]
y_norm = img.size[1] - y_norm

# -----------------------------
# 📍 PLOT MOVEMENT
# -----------------------------
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

# Player path
fig.add_trace(go.Scatter(
    x=x_norm,
    y=y_norm,
    mode="lines",
    line=dict(color="red"),
    name="Player Path"
))

# Events
events = playback_df["event"].unique()

for event_type in events:
    event_df = playback_df[playback_df["event"] == event_type]

    x_e = (event_df["x"] - x_min) / (x_max - x_min) * img.size[0]
    y_e = (event_df["y"] - y_min) / (y_max - y_min) * img.size[1]
    y_e = img.size[1] - y_e

    fig.add_trace(go.Scatter(
        x=x_e,
        y=y_e,
        mode="markers",
        name=event_type,
        marker=dict(size=8)
    ))

fig.update_layout(
    width=800,
    height=800,
    title="🗺️ Player Movement on Map",
    xaxis=dict(visible=False),
    yaxis=dict(visible=False)
)

st.plotly_chart(fig)

# -----------------------------
# 🔥 HEATMAP
# -----------------------------
st.write("🔥 Heatmap (All Players in Match)")

heat_df = match_df

x_h = (heat_df["x"] - x_min) / (x_max - x_min) * img.size[0]
y_h = (heat_df["y"] - y_min) / (y_max - y_min) * img.size[1]
y_h = img.size[1] - y_h

heatmap_fig = px.density_heatmap(
    x=x_h,
    y=y_h,
    nbinsx=50,
    nbinsy=50,
    title="🔥 Player Density Heatmap"
)

st.plotly_chart(heatmap_fig)