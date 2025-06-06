import json

def create_link_immobiliare(isochrones_gdf, priceMin, priceMax, areaMin, areaMax, roomsMin, roomsMax, n_bagni, typology, fascia_piano, asta):
    try:
        geojson_data = json.loads(isochrones_gdf.to_json())

        coordinates = []
        for feature in geojson_data.get('features', []):  # Handle missing 'features'
            geometry = feature.get('geometry', {})
            if geometry.get('type') == 'Polygon': # Check geometry type
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
            else:
                print(f"Warning: Geometry is not a Polygon: {geometry.get('type')}")

        
        coordinates_edit = ";".join(coordinates)
        
        api_call = f"https://www.immobiliare.it/search-list/?idContratto=1&idCategoria=1&prezzoMinimo={priceMin}&prezzoMassimo={priceMax}&superficieMinima={areaMin}&superficieMassima={areaMax}&idTipologia%5B0%5D={typology}&localiMinimo={roomsMin}&localiMassimo={roomsMax}&bagni={n_bagni}&tipoProprieta=1&fasciaPiano%5B0%5D=20&fasciaPiano%5B1%5D={fascia_piano}&cantina=1&noAste={asta}&__lang=it&vrt={coordinates_edit}&pag=1"
        
        return api_call

    except Exception as e:
        print(f"An error occurred: {e}")
        return None