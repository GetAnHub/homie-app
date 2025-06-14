import requests
import time
import streamlit as st
from shapely.geometry import shape, Polygon, MultiPolygon
import geopandas as gpd


def overpass_query(city, poi_type):
    """
    Query OSM Overpass API to get coordinates of POIs in the given city.

    Args:
        city (str): Name of the city.
        poi_type (str): One of 'subway', 'tram', or 'bus'.

    Returns:
        list of (lat, lon)
    """

    type_filters = {
        "subway": """
            node["railway"="station"]["station"="subway"](area.searchArea);
        """,
        "tram": """
            node["railway"="tram_stop"](area.searchArea);
            node["station"="tram"](area.searchArea);
            node["public_transport"="platform"]["tram"="yes"](area.searchArea);
        """,
        "bus": """
            node["highway"="bus_stop"](area.searchArea);
            node["public_transport"="platform"]["bus"="yes"](area.searchArea);
            node["amenity"="bus_station"](area.searchArea);
        """
    }

    if poi_type not in type_filters:
        raise ValueError("Unsupported POI type. Choose from 'subway', 'tram', 'bus'.")

    query = f"""
    [out:json][timeout:25];
    area["name"="{city}"]->.searchArea;
    (
      {type_filters[poi_type]}
    );
    out body;
    """

    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data={"data": query})
    response.raise_for_status()
    data = response.json()

    #st.write("Sample station name:", data["elements"][0]["tags"].get("name", "Unknown"))
    #st.write("Sample station name:", data["elements"])

    coords = [
        {
            "lat": element["lat"],
            "lon": element["lon"],
            "name": element["tags"].get("name", "Unknown")
        }
        for element in data.get("elements", [])
        if "lat" in element and "lon" in element
    ]
    return coords

def load_city_boundary(city_name):
    file_path = f"data/{city_name}_boundary.geojson"
    try:
        with open(file_path, "r") as file:
            boundary = gpd.read_file(file)
        return boundary.geometry.unary_union.__geo_interface__
    except FileNotFoundError:
        raise FileNotFoundError(f"Boundary file for {city_name} not found at {file_path}.")
    except Exception as e:
        raise RuntimeError(f"Error loading city boundary: {e}")    


def clean_poi_dataset(poi_coords, boundary):
    """
    Filter POI coordinates to ensure they are within the city boundary.

    Args:
        poi_coords (list of dict): List of POI coordinates with keys 'lat', 'lon', and 'name'.
        boundary (Polygon or MultiPolygon): City boundary as a shapely geometry.

    Returns:
        list of dict: Filtered POI coordinates within the city boundary.
    """
    boundary_shape = shape(boundary)
    filtered_coords = [
        {
            "lat": poi["lat"],
            "lon": poi["lon"],
            "name": poi["name"]
        }
        for poi in poi_coords
        if boundary_shape.contains(shape({"type": "Point", "coordinates": (poi["lon"], poi["lat"])}))
    ]
    return filtered_coords


# Calculate walking isochrones for the POIs using OpenRouteService API
def calculate_isochrones(poi_coords, mode, time_minutes):
    """
    Calculate walking isochrones for a list of POIs using OpenRouteService API.
    Returns the geometry of the isochrones in GeoJSON format.
    """
    try:
        # OpenRouteService API endpoint
        ors_url = "https://api.openrouteservice.org/v2/isochrones/" + mode # modes: cycling-regular, cycling-electric, driving-car, foot-walking
        #api_key = "5b3ce3597851110001cf6248a0daf93b2ba54f95b8bb3266ed6fcae6"
        api_key = "5b3ce3597851110001cf62480c0a8084fb284f72a913a0269907ada3"

        isochrones = []
        
        with st.spinner("Calculating isochrones..."):
               
            for poi in poi_coords:
                payload = {
                    "locations": [[poi["lon"], poi["lat"]]],
                    "range": [time_minutes * 60],  # Convert minutes to seconds
                    "range_type": "time",
                    "attributes": ["area"]
                }
                headers = {
                    "Authorization": api_key,
                    "Content-Type": "application/json"
                }
                response = requests.post(ors_url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                for feature in data.get("features", []):
                    geometry = feature.get("geometry")
                    if geometry:
                        isochrones.append(geometry)
                time.sleep(3)
        st.success(f"Fetched {len(isochrones)} isochrones for {len(poi_coords)} POIs.")

        return isochrones

    except Exception as e:
        st.warning(f"Could not calculate isochrones: {e}")
        return []
    


# Dissolve all isochrones into a single geometry
def dissolve_isochrone(iso_polygon):
    iso_polygon_diss = gpd.GeoSeries([shape(geometry) for geometry in iso_polygon]).unary_union
    # Handle both Polygon and MultiPolygon
    if isinstance(iso_polygon_diss, Polygon):
        isochrones_shapes  = [iso_polygon_diss]
    elif isinstance(iso_polygon_diss, MultiPolygon):
        isochrones_shapes  = list(iso_polygon_diss.geoms)

    return isochrones_shapes