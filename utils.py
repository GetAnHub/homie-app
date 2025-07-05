import requests
import time
import streamlit as st
from shapely.geometry import shape, Polygon, MultiPolygon, LineString
from shapely.geometry import GeometryCollection
import geopandas as gpd
from shapely.ops import nearest_points, unary_union
import matplotlib.pyplot as plt 



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

def load_geojson(filename):
    file_path = f"data/{filename}.geojson"
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
        
        with st.spinner("Calcolo isocrone..."):
               
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
        st.success(f"Calcolate isocrone attorno a {len(poi_coords)} stazioni.")

        return isochrones

    except Exception as e:
        st.warning(f"Impossibile calcolare le isocrone, riprova. {e}")
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


def connect_polygons(polygons, bridge_width=1e-6):
    """
    Connect a list of shapely Polygon geometries by creating bridges between them so that all polygons
    are linked into a single continuous shape. Bridges are created along the minimum spanning tree (MST)
    based on the pairwise distances between polygons.

    Parameters:
    - polygons: list of shapely Polygon geometries
    - bridge_width: float, width for buffer around connecting lines

    Returns:
    - A single shapely Polygon or MultiPolygon representing the unified connected shape.
    """
    if not polygons:
        return None
    if len(polygons) == 1:
        return polygons[0]

    n = len(polygons)
    bridges = []
    # Build a Minimum Spanning Tree (MST) using Prim's algorithm
    connected = {0}
    available = set(range(1, n))
    
    while available:
        min_edge = None
        min_dist = float('inf')
        for i in connected:
            for j in available:
                # Calculate the distance between the two polygons
                dist = polygons[i].distance(polygons[j])
                if dist < min_dist:
                    min_dist = dist
                    min_edge = (i, j)
        # Create a bridge between the closest points of the two polygons in the chosen edge
        i, j = min_edge
        p1, p2 = nearest_points(polygons[i], polygons[j])
        bridge = LineString([p1, p2]).buffer(bridge_width)
        bridges.append(bridge)
        connected.add(j)
        available.remove(j)
    
    unified = unary_union(polygons + bridges)
    return unified

def check_if_shapely_polygon(geometry):
    return isinstance(geometry, (Polygon, MultiPolygon))

def plot_polygon(geom, figsize=(8, 6), edgecolor='black', facecolor='blue', alpha=0.5):
    """
    Streamlit helper to plot a single shapely Polygon or MultiPolygon.

    Parameters:
    - geom: shapely geometry (Polygon or MultiPolygon)
    - figsize: tuple for figure size (width, height)
    - edgecolor: border color
    - facecolor: fill color
    - alpha: transparency
    """
    # Wrap geometry in GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
    # Create matplotlib figure
    fig, ax = plt.subplots(figsize=figsize)
    gdf.plot(ax=ax, edgecolor=edgecolor, facecolor=facecolor, alpha=alpha)
    ax.set_axis_off()
    st.pyplot(fig)

def count_vertices(geom):
    """
    Count the number of vertices in a shapely Polygon or MultiPolygon.

    Parameters:
    - geom: shapely Polygon or MultiPolygon

    Returns:
    - int: total count of distinct vertices (excluding repeated closing coordinates)
    """
    if isinstance(geom, Polygon):
        # Exterior ring: subtract the repeated closing coordinate
        exterior_count = len(geom.exterior.coords) - 1
        # Sum interior rings similarly
        interior_count = sum(len(ring.coords) - 1 for ring in geom.interiors)
        return exterior_count + interior_count
    elif isinstance(geom, MultiPolygon):
        # Sum over all component polygons
        return sum(count_vertices(poly) for poly in geom.geoms)
    else:
        raise TypeError(f"Unsupported geometry type: {type(geom)}")
