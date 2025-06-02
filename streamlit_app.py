import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon
import pydeck as pdk

from utils import overpass_query, load_city_boundary, clean_poi_dataset, calculate_isochrones, dissolve_isochrone
from link_generator import create_link_immobiliare

st.set_page_config(
    page_title="Homie",
    page_icon="assets/homie-icon.png",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.logo(f"assets/homie-icon.png", size="large")

with st.sidebar:
    st.title("Homie")
    st.text("Trova la tua casa ideale vicino ai mezzi pubblici")


city_name = st.selectbox("Inserisci la città ", ("Milano", "Roma", "Torino"))

col1, col2, col3 = st.columns(3)

station_options_map = {
    "subway": "Metro",
    "tram": "Tram",
    "bus": "Bus",
}
station_type = col1.pills("Seleziona il tipo di stazione", options=list(station_options_map.keys()), format_func=lambda val: station_options_map[val], default="subway")
    
transport_options_map = {
    "foot-walking": "A piedi",
    "driving-car": "In auto",
    "cycling-regular": "In bicicletta",
}
transport_mode = col2.pills("Seleziona il mezzo di trasporto", options=list(transport_options_map.keys()), format_func=lambda val: transport_options_map[val], default="foot-walking")
    
minutes = col3.slider("Seleziona il tempo di percorrenza (in minuti)", 5, 60, 10)

submitted = st.button("Cerca case", type="primary")

if submitted:
    try:
        poi_coords = overpass_query(city_name, station_type)
        st.success(f"Trovate {len(poi_coords)} stazioni a {city_name}.")
    except Exception as e:
        st.warning(f"Could not fetch metro stations: {e}")
        poi_coords = []

    city_boundary = load_city_boundary(city_name)
    poi_coords = clean_poi_dataset(poi_coords, city_boundary)

    poi_coords_straight = poi_coords[:1]
    #poi_coords_inverted = [(lon, lat) for lat, lon in poi_coords]
    #poi_coords_inverted = poi_coords_inverted[:2]

    st.write("POI Coordinates Testing:", poi_coords_straight)

    isochrones = calculate_isochrones(poi_coords_straight, transport_mode, minutes)
    # Dissolve isochrones
    isochrones_dissolved = dissolve_isochrone(isochrones)
    # Create GeoDataFrame
    isochrones_gdf = gpd.GeoDataFrame(geometry=isochrones_dissolved)

    # Extract coordinates for pydeck
    isochrones_gdf["coordinates"] = isochrones_gdf["geometry"].apply(
        lambda geom: [list(geom.exterior.coords)] if geom.geom_type == "Polygon" else []
    )

    # Create pydeck layer
    layer = pdk.Layer(
        "PolygonLayer",
        data=isochrones_gdf,
        get_polygon="coordinates",
        get_fill_color=[255, 0, 0, 100],
        get_line_color=[255, 255, 255, 200],
        pickable=True,
        auto_highlight=True,
    )

    # Define initial view
    initial_view = pdk.ViewState(
        latitude=poi_coords_straight[0][0],
        longitude=poi_coords_straight[0][1],
        zoom=9,
    )

    # Render the deck with a white background basemap
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=initial_view,
        map_style="mapbox://styles/mapbox/dark-v11",  # Mapbox style with white background
        #map_style="light",  
    )

    st.pydeck_chart(deck)

    st.write("POIs Map")
    # Display POIs coordinates on a map
    metro_df = pd.DataFrame(poi_coords, columns=["lat", "lon"])
    st.map(metro_df)


    col1, col2 = st.columns(2)

    priceMin = col1.number_input("Prezzo Minimo", 0, value = 250000, step=10000)
    priceMax = col2.number_input("Prezzo Massimo", 0, value = 350000, step=10000)

    col3, col4 = st.columns(2)

    areaMin = col3.number_input("Superficie Minima", 0, value = 60, step=5)
    areaMax = col4.number_input("Superficie Massima", 0, value = 80, step=5)

    col5, col6 = st.columns(2)

    roomsMin = col5.number_input("Locali Minimi", 0, value = 2, step=1)
    roomsMax = col6.number_input("Locali Massimi", 0, value = 3, step=1)

    link = create_link_immobiliare(isochrones_gdf,priceMax, priceMin, 
                                areaMin, areaMax, roomsMin, roomsMax
    )

    col1, col2, col3 = st.columns(3)
    with col2:
        st.link_button("Genera ricerca Immobiliare.it", url=link, type="primary")

