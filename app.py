import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import time

# --- CONFIGURACIÓN ---
st.set_page_config("🩺 Estado del Bot Sanitas", layout="centered")
tz = pytz.timezone("America/Bogota")

# --- REFRESH AUTOMÁTICO ---
st_autorefresh(interval=5000, key="refresh")  # cada 5 segundos

# --- SECRETO DE MONGO ---
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]
estado_actual = db["estado_actual"]

# --- ESTADO ACTUAL ---
actual = estado_actual.find_one({"_id": "sanitas_estado"})
if actual:
    paso = actual.get("paso", "-")
    inicio_sesion = actual.get("inicio_sesion")
    ciclo = actual.get("ciclo", 0)
    ip = actual.get("ip", "desconocida")
    
    st.title("📡 Monitoreo en Tiempo Real del Bot")
    st.markdown(f"**Paso actual:** `{paso}`")
    st.markdown(f"**Ciclo actual:** `{ciclo}`")
    st.markdown(f"**IP:** `{ip}`")

    # Cronómetro desde inicio_sesion
    if inicio_sesion:
        inicio_dt = inicio_sesion.astimezone(tz)
        segundos = int((datetime.now(tz) - inicio_dt).total_seconds())
        duracion = str(timedelta(seconds=segundos))
        st.markdown(f"⏱️ Sesión activa desde: `{inicio_dt.strftime('%H:%M:%S')}`")
        st.markdown(f"### 🕒 Duración: {duracion}")
else:
    st.title("🔴 Bot no está activo")
    st.warning("No se ha detectado un ciclo activo del bot en ejecución.")

# --- RACHAS DE DÍAS ---
st.subheader("📆 Racha de días consecutivos de búsqueda")
fechas = list(intentos.find().sort("timestamp", -1))
fechas_unicas = sorted(set(e["timestamp"].astimezone(tz).date() for e in fechas), reverse=True)

racha = 0
hoy = datetime.now(tz).date()
for i, dia in enumerate(fechas_unicas):
    if dia == hoy - timedelta(days=i):
        racha += 1
    else:
        break
st.markdown(f"**🔥 Racha actual:** `{racha}` días consecutivos ejecutando el bot")

# --- ÚLTIMA DISPONIBILIDAD / BLOQUEO ---
st.subheader("📬 Últimos eventos clave")
ultima_agenda = eventos.find_one({"tipo": "agenda_encontrada"}, sort=[("timestamp", -1)])
ultimo_bloqueo = eventos.find_one({"tipo": "error_critico"}, sort=[("timestamp", -1)])

if ultima_agenda:
    st.success(f"📅 Última agenda detectada: `{ultima_agenda['timestamp'].astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')}`")
if ultimo_bloqueo:
    with st.expander("❌ Último error crítico", expanded=False):
        st.error(f"{ultimo_bloqueo['timestamp'].astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')}\n\n{ultimo_bloqueo['mensaje']}")

# --- HISTORIAL DE EVENTOS ---
st.subheader("🧾 Registro de actividad reciente")
eventos_recientes = list(eventos.find().sort("timestamp", -1).limit(30))
if eventos_recientes:
    for ev in eventos_recientes:
        color = "🟢"
        if ev["tipo"] == "error_critico":
            color = "❌"
        elif ev["tipo"] == "agenda_encontrada":
            color = "📅"
        elif ev["tipo"] == "iframe_no_detectado":
            color = "⚠️"
        hora = ev["timestamp"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        with st.expander(f"{color} {ev['tipo']} — {hora}", expanded=False):
            st.write(ev.get("mensaje", "(Sin mensaje)"))
else:
    st.info("Sin eventos recientes.")
