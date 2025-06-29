import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
import time

# --- Configuración inicial ---
st.set_page_config("Bot Sanitas - Monitor", layout="wide")
st.title("🤖 Estado del Bot de Citas - Sanitas")

# --- Zona horaria ---
TZ = pytz.timezone("America/Bogota")

# --- Conexión a MongoDB ---
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]
estado = db["estado_actual"]

# --- Función para calcular cronómetro ---
def calcular_duracion(inicio):
    ahora = datetime.now(TZ)
    dt_inicio = inicio.astimezone(TZ)
    delta = ahora - dt_inicio
    return str(timedelta(seconds=int(delta.total_seconds())))

# --- Lectura del estado actual ---
estado_actual = estado.find_one({"_id": "sanitas_estado"})

col1, col2, col3 = st.columns([3, 2, 2])

with col1:
    st.subheader("🔄 Paso actual")
    if estado_actual:
        paso = estado_actual.get("paso", "Desconocido")
        st.markdown(f"### {paso}")
    else:
        st.warning("No hay estado en ejecución. El bot podría estar detenido.")

with col2:
    st.subheader("🕐 Tiempo desde inicio")
    if estado_actual and "inicio_sesion" in estado_actual:
        duracion = calcular_duracion(estado_actual["inicio_sesion"])
        st.success(f"⏱️ {duracion}")
    else:
        st.info("No hay sesión activa")

with col3:
    st.subheader("🔁 Ciclos ejecutados")
    if estado_actual:
        st.metric("Total ciclos", estado_actual.get("ciclo", 0))
        ip = estado_actual.get("ip", "?")
        st.caption(f"📡 IP: {ip}")

# --- Tabs con secciones ---
tabs = st.tabs(["📜 Eventos", "📊 Intentos", "📈 Resumen racha"])

# --- 📜 EVENTOS ---
with tabs[0]:
    st.subheader("Historial reciente de eventos")
    ultimos_eventos = list(eventos.find().sort("timestamp", -1).limit(50))
    if ultimos_eventos:
        for ev in ultimos_eventos:
            ts = ev["timestamp"].astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            tipo = ev["tipo"].replace("_", " ").capitalize()
            mensaje = ev.get("mensaje", "")
            with st.expander(f"{ts} — {tipo}", expanded=False):
                st.write(mensaje)
    else:
        st.info("No hay eventos recientes.")

# --- 📊 INTENTOS ---
with tabs[1]:
    st.subheader("Últimos intentos de búsqueda")
    datos = list(intentos.find().sort("timestamp", -1))
    if datos:
        tabla = []
        for doc in datos:
            ts = doc["timestamp"].astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            tabla.append({
                "#": "",
                "Fecha y hora": ts,
                "Estado": doc.get("estado", "?").capitalize(),
                "IP": doc.get("ip", "?")
            })
        for idx, fila in enumerate(tabla):
            fila["#"] = len(tabla) - idx
        st.dataframe(tabla, use_container_width=True)
    else:
        st.info("Sin intentos registrados.")

# --- 📈 RESUMEN RACHA ---
with tabs[2]:
    st.subheader("📅 Racha de días consecutivos en búsqueda")
    fechas = set([i["timestamp"].astimezone(TZ).date() for i in datos])
    hoy = datetime.now(TZ).date()
    racha = 0
    for i in range(0, 30):
        dia = hoy - timedelta(days=i)
        if dia in fechas:
            racha += 1
        else:
            break
    st.success(f"🔥 {racha} días consecutivos ejecutando el bot")

# --- Autorefresh cada segundo ---
st.rerun()
