# 🏠 Homie - Cerca la tua casa veramente *dove* vuoi tu

Homie è una web app interattiva che ti aiuta a **trovare la casa ideale vicino alle fermate dei mezzi pubblici**. L'app calcola un'area di ricerca basata sulle scelte dell'utente e genera un **link diretto per effettuare la ricerca su Immobiliare.it**.

[🌐**Prova l'app Homie**](https://homie-app.streamlit.app/)

## Funzionalità principali

- **Selezione della città**: Scegli tra Milano, Roma e Torino.
- **Filtri di trasporto**: Specifica il tipo di stazione (Metro, Tram, Bus), come vuoi muoverti (a piedi, In auto, In bicicletta) e il tempo di percorrenza.
- **Filtri casa**: Imposta parametri come prezzo, superficie, numero di locali, bagni, tipologia e fascia piano.
- **Calcolo area di ricerca**: Visualizza su una mappa interattiva l'area di ricerca basata sui tuoi criteri.
- **Link diretto a Immobiliare.it**: Genera un link per cercare case direttamente su Immobiliare.it.

## Come eseguire l'app

1. Installa le dipendenze:

   ```bash
   pip install -r requirements.txt
   ```

2. Avvia l'app:

   ```bash
   streamlit run streamlit_app.py
   ```

## Tecnologie utilizzate

- **Streamlit**: Per la creazione dell'interfaccia web.
- **Pydeck**: Per la visualizzazione interattiva delle mappe.
- **Geopandas e Shapely**: Per l'elaborazione dei dati geografici.
- **Overpass API**: Per ottenere i dati delle stazioni di trasporto pubblico.
