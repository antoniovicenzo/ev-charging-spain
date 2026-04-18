import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="EV Charging Network Spain 2027 — Iberdrola",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa; border-radius: 10px;
        padding: 16px; text-align: center; border: 1px solid #e0e0e0;
    }
    .metric-value { font-size: 28px; font-weight: 700; }
    .metric-label { font-size: 13px; color: #666; margin-top: 4px; }
    .sufficient  { color: #27ae60; }
    .moderate    { color: #f39c12; }
    .congested   { color: #e74c3c; }
    .stDataFrame { font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ── Load data ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    file2 = pd.read_csv("File 2.csv")
    file3 = pd.read_csv("File 3.csv")
    file1 = pd.read_csv("File 1.csv")
    return file2, file3, file1

file2, file3, file1 = load_data()

STATUS_COLOR_HEX = {
    "Sufficient": "#27ae60",
    "Moderate"  : "#f39c12",
    "Congested" : "#e74c3c",
}
STATUS_RGB = {
    "Sufficient": [39, 174, 96],
    "Moderate"  : [243, 156, 18],
    "Congested" : [231, 76, 60],
}

# ── Sidebar filters ─────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Iberdrola_logo.svg/320px-Iberdrola_logo.svg.png",
    width=160
)
st.sidebar.title("Filters")

status_filter = st.sidebar.multiselect(
    "Grid status",
    options=["Sufficient", "Moderate", "Congested"],
    default=["Sufficient", "Moderate", "Congested"]
)

distributor_options = sorted(file2["distributor_network"].dropna().unique())
distributor_filter = st.sidebar.multiselect(
    "Distributor",
    options=distributor_options,
    default=distributor_options
)

route_options = sorted(file2["route_segment"].dropna().unique())
route_filter = st.sidebar.multiselect(
    "Route segment",
    options=route_options,
    default=route_options
)

show_friction = st.sidebar.toggle("Show friction points", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**IE Datathon March 2026**  \nIntelligent Electric Mobility – Iberdrola")

# ── Apply filters ───────────────────────────────────────────────────────────
filtered = file2[
    file2["grid_status"].isin(status_filter) &
    file2["distributor_network"].isin(distributor_filter) &
    file2["route_segment"].isin(route_filter)
].copy()

filtered["color"] = filtered["grid_status"].map(STATUS_RGB)

# ── Header ──────────────────────────────────────────────────────────────────
st.title("⚡ EV Charging Network — Spain 2027")
st.caption("Iberdrola · IE Sustainability Datathon March 2026 · Interurban network optimization")

# ── KPI row ─────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{int(file1['total_proposed_stations'].iloc[0])}</div>
        <div class="metric-label">Proposed stations</div>
    </div>""", unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:#27ae60">
            {(file2['grid_status']=='Sufficient').sum()}
        </div>
        <div class="metric-label">Sufficient grid</div>
    </div>""", unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:#f39c12">
            {(file2['grid_status']=='Moderate').sum()}
        </div>
        <div class="metric-label">Moderate grid</div>
    </div>""", unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:#e74c3c">
            {int(file1['total_friction_points'].iloc[0])}
        </div>
        <div class="metric-label">Friction points</div>
    </div>""", unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{int(file1['total_ev_projected_2027'].iloc[0]):,}</div>
        <div class="metric-label">EVs projected 2027</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Map + Charts ────────────────────────────────────────────────────────────
map_col, chart_col = st.columns([3, 1])

with map_col:
    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=filtered,
            get_position=["longitude", "latitude"],
            get_fill_color="color",
            get_radius=12000,
            pickable=True,
            opacity=0.9,
            stroked=True,
            get_line_color=[255, 255, 255],
            line_width_min_pixels=1,
        )
    ]

    if show_friction and len(file3) > 0:
        file3_map = file3.copy()
        file3_map["color"] = [[180, 0, 0]] * len(file3_map)
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=file3_map,
                get_position=["longitude", "latitude"],
                get_fill_color=[180, 0, 0],
                get_radius=18000,
                pickable=True,
                opacity=0.6,
                stroked=True,
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
            )
        )

    view = pdk.ViewState(latitude=40.2, longitude=-3.5, zoom=5.5, pitch=0)

    tooltip = {
        "html": """
            <b>{location_id}</b><br>
            Route: {route_segment}<br>
            Chargers: {n_chargers_proposed}<br>
            Grid: {grid_status}<br>
            Distributor: {distributor_network}
        """,
        "style": {"backgroundColor": "white", "color": "black",
                  "fontSize": "13px", "padding": "8px", "borderRadius": "6px"}
    }

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        tooltip=tooltip,
        map_style="light",
    )
    st.pydeck_chart(deck, use_container_width=True)

    # Legend
    st.markdown("""
    <div style="display:flex;gap:20px;font-size:13px;margin-top:8px">
        <span><span style="color:#27ae60;font-size:18px">●</span> Sufficient</span>
        <span><span style="color:#f39c12;font-size:18px">●</span> Moderate</span>
        <span><span style="color:#e74c3c;font-size:18px">●</span> Congested</span>
        <span><span style="color:#b40000;font-size:18px">●</span> Friction point</span>
    </div>
    """, unsafe_allow_html=True)

with chart_col:
    # Grid status donut
    status_counts = file2["grid_status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    colors = [STATUS_COLOR_HEX.get(s, "#999") for s in status_counts["status"]]

    fig_donut = go.Figure(go.Pie(
        labels=status_counts["status"],
        values=status_counts["count"],
        hole=0.55,
        marker_colors=colors,
        textinfo="label+percent",
        textfont_size=12,
    ))
    fig_donut.update_layout(
        title="Grid status", height=260,
        margin=dict(t=40, b=0, l=0, r=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_donut, use_container_width=True)

    # Chargers by distributor
    dist_summary = (
        filtered.groupby("distributor_network")["n_chargers_proposed"]
        .sum().reset_index().sort_values("n_chargers_proposed", ascending=True)
    )
    fig_bar = px.bar(
        dist_summary, x="n_chargers_proposed", y="distributor_network",
        orientation="h", title="Chargers by distributor",
        color_discrete_sequence=["#2c3e50"]
    )
    fig_bar.update_layout(
        height=220, margin=dict(t=40, b=0, l=0, r=0),
        xaxis_title="", yaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Route-level breakdown ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Route-level breakdown")

route_summary = (
    filtered.groupby(["route_segment", "grid_status"])
    .agg(stations=("location_id", "count"),
         chargers=("n_chargers_proposed", "sum"))
    .reset_index()
    .pivot_table(index="route_segment",
                 columns="grid_status",
                 values=["stations","chargers"],
                 fill_value=0)
)
route_summary.columns = [f"{c[0]}_{c[1]}" for c in route_summary.columns]
route_summary = route_summary.reset_index()
route_summary["total_stations"] = filtered.groupby("route_segment")["location_id"].count().reindex(route_summary["route_segment"]).values
route_summary["total_chargers"] = filtered.groupby("route_segment")["n_chargers_proposed"].sum().reindex(route_summary["route_segment"]).values
route_summary["peak_demand_kw"] = route_summary["total_chargers"] * 150

st.dataframe(
    route_summary.sort_values("total_stations", ascending=False),
    use_container_width=True, hide_index=True
)

# ── Friction points table ───────────────────────────────────────────────────
if show_friction and len(file3) > 0:
    st.markdown("---")
    st.subheader("⚠ Friction points — grid reinforcement required")
    st.dataframe(
        file3[["bottleneck_id","route_segment","distributor_network",
               "grid_status","estimated_demand_kw","latitude","longitude"]],
        use_container_width=True, hide_index=True
    )
