import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz

# Configuración inicial
st.set_page_config(page_title="Monitoreo Sanitas", layout="centered")
st.title("🩺 Monitoreo de Bot - EPS Sanitas")

# Conexión a MongoDB Atlas
client = MongoClient(st.secrets["mongo_uri"])
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]
estado_col = db["estado_actual"]

# Zona horaria de Colombia
tz = pytz.timezone("America/Bogota")

# ==============================
# 🔄 Estado actual del bot
# ==============================
estado = estado_col.find_one({"_id": "sanitas_estado"})

if estado:
    st.subheader("🔄 Estado Actual del Bot")
    st.markdown(f"**Paso actual:** `{estado.get('paso', 'desconocido')}`")
    st.markdown(f"**IP usada:** `{estado.get('ip', 'N/D')}`")
    st.markdown(f"**Ciclos ejecutados:** `{estado.get('ciclo', 0)}`")

    inicio = estado.get("inicio_sesion")
    if inicio:
        inicio_dt = inicio.astimezone(tz) if inicio.tzinfo else tz.localize(inicio)
        tiempo_activo = datetime.now(tz) - inicio_dt
        st.success(f"⏱️ Duración de la sesión: {str(tiempo_activo).split('.')[0]}")

    st.caption(f"⏰ Última actualización: {estado.get('ultimo_update').astimezone(tz).strftime('%Y-%m-%d %H:%M:%S') if estado.get('ultimo_update') else 'N/D'}")
else:
    st.warning("No hay estado actual registrado.")

# ==============================
# 📊 Historial de Intentos
# ==============================
st.subheader("📊 Historial de Intentos")
int_hist = list(intentos.find().sort("timestamp", -1).limit(20))
if int_hist:
    for intento in int_hist:
        ts = intento["timestamp"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"[{ts}] — `{intento['estado']}` — IP: `{intento.get('ip', 'N/D')}`")
else:
    st.info("No hay intentos registrados.")

# ==============================
# 📅 Eventos relevantes
# ==============================
st.subheader("📅 Eventos Críticos")
ev_hist = list(eventos.find().sort("timestamp", -1).limit(20))
if ev_hist:
    for ev in ev_hist:
        ts = ev["timestamp"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        tipo = ev.get("tipo", "desconocido")
        mensaje = ev.get("mensaje", "")
        st.write(f"[{ts}] — **{tipo}**: {mensaje}")
else:
    st.info("No hay eventos críticos registrados.")

# ==============================
# ♻️ Refresco cada 3 segundos
# ==============================
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=3000, key="refresh")
