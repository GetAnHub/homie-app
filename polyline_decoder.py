import streamlit as st
from urllib.parse import urlparse, parse_qs, unquote
import polyline

def decode_shape_from_url(url: str) -> list:
    # Estrae e percent-decodifica il param 'shape'
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    shape_enc = params.get('shape', [''])[0]
    decoded = unquote(shape_enc)  # → "((m|ntGsdtv@whAse@...))"
    # Togli le doppie parentesi incapsulanti
    core = decoded.strip("()")
    # Decode con polyline (rimuovi eventuali prefissi/suffissi non-standard)
    return polyline.decode(core)

st.title("Polyline Decoder")
url = "https://www.idealista.it/aree/vendita-case/con-prezzo_350000,prezzo-min_250000,dimensione_60,dimensione-max_80,bilocali-2,trilocali-3,bagno-1,bagno-2,bagno-3,aste_no/lista-mappa?shape=%28%28u%7CqtG%7Dldw%40c%40%7DE%5BiDeB_YGoC%5BwL%3FCv%40o%40fDaC%3F%3FilD%7DtF%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3FkPf%40mHoLoH_R_G%7Db%40aAY%7BAkJnCwFzHaLpFsDfA%40v%40dApFzH~Vn%5Bl%40V%5ERd%40VXX%5E%60%40d%40bAd%40bA%5C%7C%40%5E~%40%7BDnc%40%3FfAgBjDaFnFy%40j%40%3F%3FjlD%7CtF%3F%3F%3F%3FbFyB%60TwGbBSbOXjM%7CVjHfMvCvGpAlFJb%40%7B%40zBeEp%60%40%3FRq%40r%40%7DGrDcN%7CEkErA_BFsRTw%40%3Fe%40AICwGoB%3F%3FiBzE%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3FzEzHn%40vBrCbKjG%60%5BBj%40RfSYbA_%40r%40cCxBQFoVzOmMtMgAKmVwKw%40k%40qBaIQaA%5DiK%3F%3Fc_AzC%3F%3F%3F%3F%3F%3FgAzLgAjLaCtVwDdIgLfPeARaSPeAIyF%7BA%7BOcV%3F%3FyTfN%3F%3Fq%40xSf%40zO%7B%40lDyL%7CTGLe%5EvGgAL%7DIuFuOkKaCma%40GgAUaKBGv%40qAbGqG%60QuM%7C%40e%40jFSpL_%40lFjCbSpLnAfBh%40x%40xTgNg%40%7B%40%3FSjAkZdAUdAStBi%40%60Ru%5BzJkMTOdAHjPbIj%40%5ChMnHLj%40DP%3F%3F%3F%3Fb_A%7BCSeG%5BiIAWFgAdAqRDe%40%7CH%7BUpJmHbFe%40fPQzFL%3F%3F%3F%3F%3F%3F%3F%3FhB%7BE%3F%3F%3F%3F%3F%3FII%5DeAuBq%5D%29%29"
if url:
    try:
        coords = decode_shape_from_url(url)
        st.write(f"Ho trovato **{len(coords)}** punti:")
        st.map([{"lat": lat, "lon": lng} for lat, lng in coords])
    except Exception as e:
        st.error(f"Errore nel decoding: {e}")

# %28%28u%7CqtG%7Dldw%40c%40%7DE%5BiDeB_YGoC%5BwL%3FCv%40o%40fDaC%3F%3FilD%7DtF%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3FkPf%40mHoLoH_R_G%7Db%40aAY%7BAkJnCwFzHaLpFsDfA%40v%40dApFzH~Vn%5Bl%40V%5ERd%40VXX%5E%60%40d%40bAd%40bA%5C%7C%40%5E~%40%7BDnc%40%3FfAgBjDaFnFy%40j%40%3F%3FjlD%7CtF%3F%3F%3F%3FbFyB%60TwGbBSbOXjM%7CVjHfMvCvGpAlFJb%40%7B%40zBeEp%60%40%3FRq%40r%40%7DGrDcN%7CEkErA_BFsRTw%40%3Fe%40AICwGoB%3F%3FiBzE%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3FzEzHn%40vBrCbKjG%60%5BBj%40RfSYbA_%40r%40cCxBQFoVzOmMtMgAKmVwKw%40k%40qBaIQaA%5DiK%3F%3Fc_AzC%3F%3F%3F%3F%3F%3FgAzLgAjLaCtVwDdIgLfPeARaSPeAIyF%7BA%7BOcV%3F%3FyTfN%3F%3Fq%40xSf%40zO%7B%40lDyL%7CTGLe%5EvGgAL%7DIuFuOkKaCma%40GgAUaKBGv%40qAbGqG%60QuM%7C%40e%40jFSpL_%40lFjCbSpLnAfBh%40x%40xTgNg%40%7B%40%3FSjAkZdAUdAStBi%40%60Ru%5BzJkMTOdAHjPbIj%40%5ChMnHLj%40DP%3F%3F%3F%3Fb_A%7BCSeG%5BiIAWFgAdAqRDe%40%7CH%7BUpJmHbFe%40fPQzFL%3F%3F%3F%3F%3F%3F%3F%3FhB%7BE%3F%3F%3F%3F%3F%3FII%5DeAuBq%5D%29%29
