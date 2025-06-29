import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz

# Configuración de página
st.set_page_config(page_title="Sanitas Bot - Dossier", layout="wide")
st.title("🕵️ Dossier de movimientos recientes")

st.markdown("""
### 🔍 Seguimiento en tiempo real del bot
Cada intento, hallazgo y anomalía queda registrado aquí. El sistema está bajo la lupa — y vos tenés el control.
""")

# Zona horaria Colombia
tz = pytz.timezone("America/Bogota")

# Conexión a MongoDB
client = MongoClient(st.secrets["mongo_uri"])
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]

# Filtro de eventos recientes (por defecto, últimas 24 horas)
hoy = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
eventos_recientes = list(eventos.find({"timestamp": {"$gte": hoy}}).sort("timestamp", -1))

# Iconos por tipo de evento
iconos = {
    "agenda_encontrada": "📅",
    "sin_agenda": "📥",
    "error_critico": "❌",
    "iframe_no_detectado": "⚠️",
    "bloqueo": "🔒",
}

# Mostrar tarjetas
for ev in eventos_recientes[:25]:
    tipo = ev.get("tipo", "evento")
    icono = iconos.get(tipo, "🔹")
    mensaje = ev.get("mensaje", "Sin mensaje")
    hora = ev["timestamp"].astimezone(tz).strftime("%H:%M:%S")
    fecha = ev["timestamp"].astimezone(tz).strftime("%Y-%m-%d")

    with st.container():
        st.markdown(f"""
        <div style='border-left: 6px solid #888; padding: 0.5em 1em; margin: 0.5em 0; background-color: #f9f9f9;'>
            <span style='font-size: 1.2em;'>{icono} <strong>{tipo.replace('_', ' ').capitalize()}</strong></span><br>
            <span style='color: #555;'>{mensaje}</span><br>
            <span style='font-size: 0.85em; color: #999;'>🕛 {fecha} — {hora}</span>
        </div>
        """, unsafe_allow_html=True)

if not eventos_recientes:
    st.info("No hay eventos registrados hoy. El bot aún no ha sido ejecutado o no ha generado actividad.")
