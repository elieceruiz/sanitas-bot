import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# Configuración inicial
st.set_page_config("Sanitas Bot Tracker", layout="wide", page_icon="🤖")
st_autorefresh(interval=1000, key="refresh")  # Refrescar cada segundo
TZ = pytz.timezone("America/Bogota")

# Conectar a MongoDB
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client["sanitas_bot"]
eventos = db["eventos"]
estado = db["estado_actual"]

# Leer estado actual del bot
estado_doc = estado.find_one({"_id": "sanitas_estado"})

st.title("🤖 Estado Actual del Bot de Citas - Sanitas")

if estado_doc:
    paso = estado_doc.get("paso", "Desconocido")
    inicio = estado_doc.get("inicio_sesion")
    actualizacion = estado_doc.get("ultimo_update")
    ciclos = estado_doc.get("ciclo", 0)
    ip = estado_doc.get("ip", "N/A")

    if isinstance(inicio, datetime):
        dt_inicio = inicio.astimezone(TZ)
    else:
        dt_inicio = datetime.now(TZ)  # fallback

    duracion = datetime.now(TZ) - dt_inicio
    horas, resto = divmod(duracion.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    duracion_str = f"{horas:02}h {minutos:02}m {segundos:02}s"

    col1, col2, col3 = st.columns(3)
    col1.metric("🔄 Paso actual", paso)
    col2.metric("🕐 Tiempo desde inicio", duracion_str)
    col3.metric("🔁 Ciclos ejecutados", ciclos)

    st.caption(f"🌐 IP: `{ip}` • Última actualización: {actualizacion.astimezone(TZ).strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.warning("⚠️ El bot no ha iniciado sesión o no ha actualizado su estado aún.")

# 🧠 Últimos eventos importantes
st.subheader("📌 Últimos eventos relevantes")

eventos_recientes = list(eventos.find().sort("timestamp", -1).limit(15))
if eventos_recientes:
    for ev in eventos_recientes:
        tipo = ev.get("tipo", "Evento")
        ts = ev["timestamp"].astimezone(TZ).strftime('%Y-%m-%d %H:%M:%S')
        mensaje = ev.get("mensaje", "")
        if tipo == "agenda_encontrada":
            st.success(f"📅 {ts} — **¡Agenda encontrada!** {mensaje}")
        elif tipo == "bloqueo":
            st.error(f"🚫 {ts} — **Sesión bloqueada** {mensaje}")
        elif tipo == "error_critico":
            with st.expander(f"❌ {ts} — Error crítico"):
                st.code(mensaje, language="bash")
        elif tipo == "iframe_no_detectado":
            st.warning(f"⚠️ {ts} — Problema con iframe: {mensaje}")
        else:
            st.info(f"ℹ️ {ts} — {tipo}: {mensaje}")
else:
    st.info("No hay eventos registrados aún.")
