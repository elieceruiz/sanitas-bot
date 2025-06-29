import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz

# Config general
st.set_page_config("Sanitas Bot Monitor", layout="centered")
st.title("🩺 Monitor del Bot de Sanitas")

# Zona horaria
tz = pytz.timezone("America/Bogota")

# Conexion Mongo
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]
estado_col = db["estado"]

# Estado actual
doc_estado = estado_col.find_one({"_id": "sanitas_estado"})
if doc_estado:
    st.subheader("🔄 Estado Actual del Bot")
    st.success(f"**Paso:** {doc_estado.get('paso', 'Desconocido')}")

    inicio = doc_estado.get("inicio_sesion")
    if inicio:
        inicio_dt = datetime.fromisoformat(inicio).astimezone(tz)
        duracion = datetime.now(tz) - inicio_dt
        st.info(f"🕒 Sesion activa desde: {inicio_dt.strftime('%Y-%m-%d %H:%M:%S')} ({str(duracion).split('.')[0]})")

    st.metric("🔁 Ciclos ejecutados", doc_estado.get("ciclo", 0))
    st.text(f"IP actual: {doc_estado.get('ip', 'N/D')}")
else:
    st.warning("No se ha detectado estado actual del bot.")

# Ultima agenda encontrada
ultimo_exito = eventos.find_one({"tipo": "agenda_encontrada"}, sort=[("timestamp", -1)])
if ultimo_exito:
    ts = ultimo_exito["timestamp"].astimezone(tz)
    desde = datetime.now(tz) - ts
    st.subheader("📬 Ultima disponibilidad detectada")
    st.info(f"Fecha: {ts.strftime('%Y-%m-%d %H:%M:%S')} ({str(desde).split('.')[0]} atrás)")

# Ultima caida de sesion
ultimo_bloqueo = eventos.find_one({"tipo": "bloqueo"}, sort=[("timestamp", -1)])
if ultimo_bloqueo:
    ts = ultimo_bloqueo["timestamp"].astimezone(tz)
    desde = datetime.now(tz) - ts
    st.subheader("🔒 Ultima caida de sesión")
    st.error(f"Fecha: {ts.strftime('%Y-%m-%d %H:%M:%S')} ({str(desde).split('.')[0]} atrás)")

# Racha de días consecutivos
st.subheader("📆 Racha de búsqueda diaria")
fechas = [i["timestamp"].astimezone(tz).date() for i in intentos.find({}, {"timestamp": 1})]
fechas_unicas = sorted(set(fechas))

racha = 0
hoy = datetime.now(tz).date()
for i in range(len(fechas_unicas)):
    if hoy - timedelta(days=i) in fechas_unicas:
        racha += 1
    else:
        break
st.metric("🔥 Días consecutivos buscando", racha)

# Historial visual
st.subheader("🧾 Registro reciente")
registros = eventos.find({}, sort=[("timestamp", -1)]).limit(15)
iconos = {
    "agenda_encontrada": "📅",
    "bloqueo": "🔒",
    "error_critico": "❌",
    "iframe_no_detectado": "🖼️",
    "inicio": "🚀",
    "reinicio": "♻️",
    "fin": "🛑",
}

for reg in registros:
    tipo = reg.get("tipo", "evento")
    icono = iconos.get(tipo, "🔔")
    hora = reg["timestamp"].astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
    mensaje = reg.get("mensaje", "Sin mensaje")
    with st.container():
        st.markdown(f"**{icono} {tipo.replace('_', ' ').capitalize()}** — `{hora}`\n> {mensaje}")
        st.divider()
