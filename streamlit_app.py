import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.ops import unary_union
import pydeck as pdk

from utils import overpass_query, load_city_boundary, clean_poi_dataset, calculate_isochrones, dissolve_isochrone, connect_polygons, check_if_shapely_polygon, plot_polygon, count_vertices
from link_generator import create_link_immobiliare, create_link_idealista

st.set_page_config(
    page_title="Homie",
    page_icon="assets/homie-icon.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.logo(f"assets/homie-icon.png", size="large")

with st.sidebar:
    st.title("Homie")
    st.text("Trova la tua casa ideale vicino ai mezzi pubblici")

with st.container(border=True):
    st.markdown("### Area di ricerca")

    city_name = st.selectbox("Città ", ("Milano", "Roma", "Torino"))

    col1, col2, col3 = st.columns(3)

    station_options_map = {
        "subway": "Metro",
        "tram": "Tram",
        "bus": "Bus",
    }
    station_type = col1.pills("Tipo di stazione", options=list(station_options_map.keys()), format_func=lambda val: station_options_map[val], default="subway")
        
    transport_options_map = {
        "foot-walking": "A piedi",
        "driving-car": "In auto",
        "cycling-regular": "In bicicletta",
    }
    transport_mode = col2.pills("Mezzo di trasporto", options=list(transport_options_map.keys()), format_func=lambda val: transport_options_map[val], default="foot-walking")
        
    minutes = col3.slider("Tempo di percorrenza (in minuti)", 5, 30, 10)

with st.container(border=True):
    st.markdown("### Filtri casa")

    col1, col2 = st.columns(2)

    priceMin = col1.number_input("Prezzo Minimo", 0, value = 250000, step=10000)
    priceMax = col2.number_input("Prezzo Massimo", 0, value = 350000, step=10000)

    col3, col4 = st.columns(2)

    areaMin = col3.number_input("Superficie Minima", 1, value = 60, step=5)
    areaMax = col4.number_input("Superficie Massima", 1, value = 80, step=5)

    col5, col6 = st.columns(2)

    roomsMin = col5.number_input("Locali Minimi", 1, value = 2, step=1)
    roomsMax = col6.number_input("Locali Massimi", 1, value = 3, step=1)

    col7, col8 = st.columns(2)
    typology_options_map = {
        "4": "Appartamento",
        "5": "Attico/Mansarda",
        "7": "Casa indipendente",
        "31": "Loft",
        "12": "Villa",
    }
    typology = col7.pills("Tipologia", options=list(typology_options_map.keys()), format_func=lambda val: typology_options_map[val], default="4")
    n_bagni = col8.number_input("Numero bagni", 1, value = 1, step=1)

    col9, col10 = st.columns(2)
    fascia_piano_map = {
        "10": "Piano terra",
        "20": "Piani intermedi",
        "30": "Ultimo piano",
    }
    fascia_piano = col9.pills("Fascia Piano", options=list(fascia_piano_map.keys()), format_func=lambda val: fascia_piano_map[val], default="10")
    asta_bool = col10.selectbox("Escludi aste", ["Sì", "No"])
    asta = 1 if asta_bool == 'Sì' else 0


submitted = st.button("Calcola area di ricerca", type="primary")

if submitted:
    try:
        poi_coords = overpass_query(city_name, station_type)
        st.success(f"Trovate {len(poi_coords)} stazioni {station_options_map[station_type]} a {city_name}.")
    except Exception as e:
        st.warning(f"Impossibile trovare stazioni del tipo selezionato, riprova. {e}")
        poi_coords = []

    city_boundary = load_city_boundary(city_name)
    poi_coords = clean_poi_dataset(poi_coords, city_boundary)

    poi_coords_straight = poi_coords[:20]

    isochrones = calculate_isochrones(poi_coords_straight, transport_mode, minutes)
    isochrones_dissolved = dissolve_isochrone(isochrones)
    connected_isochrones = connect_polygons(isochrones_dissolved)

    st.write("count vertices:", count_vertices(connected_isochrones))
    plot_polygon(connected_isochrones)

    # Simplify the connected_isochrones polygon
    connected_isochrones_simple = connected_isochrones.simplify(tolerance=0.0008, preserve_topology=True)

    st.write("count vertices (simplified):", count_vertices(connected_isochrones_simple))

    # Create GeoDataFrame from simplified polygon
    isochrones_gdf = gpd.GeoDataFrame(geometry=[connected_isochrones_simple])
    
    # Duplicate isochrones_gdf
    isochrones_gdf_pdk = isochrones_gdf.copy()

    # Extract coordinates for pydeck
    isochrones_gdf_pdk["coordinates"] = isochrones_gdf["geometry"].apply(
        lambda geom: [list(geom.exterior.coords)] if geom.geom_type == "Polygon" else []
    )
    # Remove non-serializable geometry column
    isochrones_gdf_pdk = isochrones_gdf_pdk.drop(columns=["geometry"])

    # Create isochrones layer
    layer_iso = pdk.Layer(
        "PolygonLayer",
        data=isochrones_gdf_pdk,
        get_polygon="coordinates",
        get_fill_color=[0, 222, 77, 75],
        pickable=False,
        auto_highlight=False,
    )
    # Create stations layer
    layer_stations = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame(poi_coords_straight),  # <-- Fix: use list of dicts directly
        get_position=["lon", "lat"],  # Correctly reference longitude and latitude
        get_fill_color=[255, 0, 0, 100],
        get_radius=150,  # Set radius for the scatterplot points
        pickable=True,
        auto_highlight=True,
    )

    # Create highlighted vertices layer
    layer_vertices = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame(connected_isochrones.exterior.coords, columns=["lon", "lat"]),
        get_position=["lon", "lat"],
        get_fill_color=[255, 255, 0, 200],
        get_radius=5,
        pickable=True,
        auto_highlight=True,
    )

    # Define initial view
    initial_view = pdk.ViewState(
        latitude=poi_coords_straight[0]["lat"],
        longitude=poi_coords_straight[0]["lon"],
        zoom=9,
    )

    # Render the deck with a background basemap
    deck = pdk.Deck(
        layers=[layer_iso, layer_stations, layer_vertices],
        tooltip={
            "html": "Stazione: <b>{name}</b>",
            "style": {"color": "white"},
        },
        initial_view_state=initial_view,
        map_style="mapbox://styles/mapbox/dark-v11",  # Mapbox style with white background
        #map_style="light",  
    )

    st.pydeck_chart(deck)

    #st.write("POIs Map")
    # Display POIs coordinates on a map
    #metro_df = pd.DataFrame(poi_coords, columns=["lat", "lon"])
    #st.map(metro_df)

    link_immobiliare = create_link_immobiliare(isochrones_gdf, priceMax, priceMin, 
                                areaMin, areaMax, roomsMin, roomsMax, 
                                n_bagni, typology, fascia_piano, asta
    )

    link_idealista = create_link_idealista(connected_isochrones_simple, priceMax, priceMin, 
                                areaMin, areaMax, roomsMin, roomsMax, 
                                n_bagni 
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button("Apri ricerca Idealista.it", url=link_idealista, type="primary")
        st.write(link_idealista)
    with col2:
        st.link_button("Apri ricerca Immobiliare.it", url=link_immobiliare, type="primary")
        st.write(link_immobiliare)