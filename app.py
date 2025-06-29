import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz

# --- Configuración de zona horaria ---
TZ = pytz.timezone("America/Bogota")

# --- Conexión a MongoDB Atlas ---
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client["sanitas_bot"]
eventos = db["eventos"]
estado = db["estado_actual"]

# --- UI Principal ---
st.set_page_config("Sanitas Bot - Estado", layout="centered")
st.title("🤖 Estado Actual del Bot de Citas - Sanitas")

# --- Estado actual ---
doc_estado = estado.find_one({"_id": "sanitas_estado"})

if doc_estado:
    paso = doc_estado.get("paso", "Desconocido")
    inicio = doc_estado.get("inicio_sesion")
    ciclos = doc_estado.get("ciclo", 0)
    ip = doc_estado.get("ip", "?")

    try:
        dt_inicio = datetime.fromisoformat(inicio).astimezone(TZ)
        duracion = datetime.now(TZ) - dt_inicio
        tiempo_activo = str(timedelta(seconds=int(duracion.total_seconds())))
    except:
        dt_inicio = None
        tiempo_activo = "No disponible"

    st.subheader("🔄 Paso en curso")
    st.markdown(f"**{paso}**")

    st.divider()
    st.markdown(f"### 🟡 Resultado reciente")
    resultado = eventos.find_one({"tipo": "sin_agenda"}, sort=[("timestamp", -1)])
    if resultado:
        st.warning(f"⚠️ {resultado['mensaje']}")
    else:
        st.info("Sin resultados recientes.")

    st.divider()
    st.markdown("### ⏱️ Duración de la sesión")
    if dt_inicio:
        st.write(f"Iniciada: {dt_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Duración: {tiempo_activo}")
    else:
        st.write("No disponible")

    st.markdown(f"### 🔁 Ciclo en ejecución")
    st.write(f"Ciclo actual: **#{ciclos}**")

    st.markdown(f"### 🌐 IP pública detectada")
    st.code(ip)

else:
    st.error("No se ha detectado actividad reciente del bot.")

# --- Historial resumido ---
st.divider()
st.subheader("📜 Historial resumido de eventos")
recientes = list(eventos.find().sort("timestamp", -1).limit(5))

if recientes:
    for ev in recientes:
        fecha = ev["timestamp"].astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
        mensaje = ev.get("mensaje", "Sin mensaje")
        tipo = ev.get("tipo", "?")

        with st.expander(f"🗓️ {fecha} — {tipo}"):
            st.write(mensaje)
else:
    st.info("No hay eventos registrados.")
