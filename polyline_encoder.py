import polyline
from shapely.geometry import Polygon
import streamlit as st
from urllib.parse import quote


def encode_polyline_from_shape(polygon: Polygon) -> str:
    if not isinstance(polygon, Polygon):
        raise TypeError("encode_polyline_from_shape, L'oggetto deve essere un shapely.geometry.Polygon")

    # Estrai coordinate come lista [lat, lng]
    coords = [(lat, lng) for lng, lat in polygon.exterior.coords]

    # Codifica in polyline string
    encoded = polyline.encode(coords)

    # Avvolgi in doppie parentesi
    wrapped = f"(({encoded}))"

    # Percent-encode per l'URL
    return quote(wrapped, safe='')
