import json
import streamlit as st
from polyline_encoder import encode_polyline_from_shape
from shapely.geometry import Polygon, MultiPolygon

def create_link_immobiliare(isochrones_gdf, priceMin, priceMax, areaMin, areaMax, roomsMin, roomsMax, n_bagni, typology, fascia_piano, asta):
    try:
        geojson_data = json.loads(isochrones_gdf.to_json())

        coordinates = []
        for feature in geojson_data.get('features', []):  # Handle missing 'features'
            geometry = feature.get('geometry', {})
            for polygon in geometry.get('coordinates', []):
                for ring in polygon:
                    if isinstance(ring[0], list): # Check if ring is a list of coords
                        for coord in ring:
                            if isinstance(coord, list) and len(coord) == 2: # Check if coord is a list of 2 floats
                                    longitude, latitude = coord
                                    coordinates.append(f"{latitude},{longitude}")
                            else:
                                    print(f"Warning: Invalid coordinate format: {coord}")
                    elif isinstance(ring, list) and len(ring) == 2: #Handle single coordinate rings
                        longitude, latitude = ring
                        coordinates.append(f"{latitude},{longitude}")
                    else:
                        print(f"Warning: Invalid ring format: {ring}")
        
        coordinates_edit = ";".join(coordinates)
        
        api_call_immobiliare = f"https://www.immobiliare.it/search-list/?idContratto=1&idCategoria=1&prezzoMinimo={priceMin}&prezzoMassimo={priceMax}&superficieMinima={areaMin}&superficieMassima={areaMax}&idTipologia%5B0%5D={typology}&localiMinimo={roomsMin}&localiMassimo={roomsMax}&bagni={n_bagni}&tipoProprieta=1&fasciaPiano%5B0%5D=20&fasciaPiano%5B1%5D={fascia_piano}&cantina=1&noAste={asta}&__lang=it&vrt={coordinates_edit}&pag=1"
        
        return api_call_immobiliare

    except Exception as e:
        st.write(f"create_link_immobiliare, An error occurred: {e}")
        return None
    

def create_link_idealista(isochrones, priceMax, priceMin, areaMin, areaMax, roomsMin, roomsMax, n_bagni):
    try: 
        polyline = encode_polyline_from_shape(isochrones)
        api_call_idealista = f"https://www.idealista.it/aree/vendita-case/con-prezzo_{priceMax},prezzo-min_{priceMin},dimensione_{areaMin},dimensione-max_{areaMax},bilocali-{roomsMin},trilocali-{roomsMax},bagno-{n_bagni},bagno-2,bagno-3,aste_no/lista-mappa?shape={polyline}"
        return api_call_idealista

    except Exception as e:
        st.write(f"create_link_idealista, An error occurred: {e}")
        return None