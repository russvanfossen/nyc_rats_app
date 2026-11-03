import pandas as pd
import folium
import streamlit as st
from folium.plugins import MarkerCluster
from sodapy import Socrata
from streamlit_folium import st_folium

DATASET_ID = "p937-wjvj"
NYC_COORDS = [40.742122160341616, -73.90645332300794]
BATCH_SIZE = 50_000

st.set_page_config(page_title="NYC Rat Inspections", layout="wide")


@st.cache_data(ttl=3600, show_spinner="Downloading inspection data...")
def load_data(day_delta: int) -> pd.DataFrame:
    """Pull failed rat inspections from the last `day_delta` days."""
    since = (pd.Timestamp("now") - pd.Timedelta(days=day_delta)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3]
    token = st.secrets.get("NYCDATA_TOKEN")

    batches, offset = [], 0
    with Socrata("data.cityofnewyork.us", token, timeout=120) as client:
        while True:
            rows = client.get(
                DATASET_ID,
                where=f"inspection_date > '{since}' and result like 'Fail%'",
                limit=BATCH_SIZE,
                offset=offset,
                order=":id",
            )
            if not rows:
                break
            batches.append(pd.DataFrame.from_records(rows))
            offset += len(rows)

    if not batches:
        return pd.DataFrame()

    df = pd.concat(batches, ignore_index=True)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["inspection_date"] = pd.to_datetime(df["inspection_date"])
    return df.dropna(subset=["latitude", "longitude"])


def build_map(df: pd.DataFrame) -> folium.Map:
    m = folium.Map(location=NYC_COORDS, zoom_start=10, tiles="OpenStreetMap.HOT")
    cluster = MarkerCluster().add_to(m)
    for record in df.itertuples():
        popup_text = (
            f"{record.house_number} {record.street_name}<br>"
            f"Result: {record.result}<br>"
            f"Date: {record.inspection_date:%Y-%m-%d %H:%M}"
        )
        folium.Marker(
            location=[record.latitude, record.longitude],
            icon=folium.DivIcon(
                html='<div style="font-size: 28px;">🐀</div>',
                icon_size=(32, 32),
                icon_anchor=(16, 16),
            ),
            popup=folium.Popup(popup_text, max_width=300),
        ).add_to(cluster)
    return m


# --- Sidebar controls ---
st.sidebar.header("Filters")
day_delta = st.sidebar.slider("Days to look back", 7, 90, 30)

df = load_data(day_delta)
if df.empty:
    st.warning("No failed inspections found for that period.")
    st.stop()

boroughs = sorted(df["borough"].dropna().unique())
picked = st.sidebar.multiselect("Borough", boroughs, default=boroughs)
filtered = df[df["borough"].isin(picked)]

# --- Main page ---
st.title("🐀 NYC Failed Rat Inspections")
st.caption(f"Last {day_delta} days · source: NYC Open Data ({DATASET_ID})")

col1, col2 = st.columns(2)
col1.metric("Failed inspections", f"{len(filtered):,}")
col2.metric("Neighborhoods", filtered["nta"].nunique())

# returned_objects=[] keeps panning/zooming from rerunning the whole script
with st.spinner("Building map..."):
    m = build_map(filtered)
    st_folium(m, width=True, height=600,
              returned_objects=[])

with st.expander("Raw data"):
    st.dataframe(
        filtered[["inspection_date", "house_number", "street_name", "borough",
                  "nta", "result", "observations"]],
        use_container_width=True,
    )
