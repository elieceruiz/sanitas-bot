import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import pytz

# Configuración
st.set_page_config("Sanitas Bot - Estado", layout="wide")
st_autorefresh(interval=5000, limit=None, key="refresh")

st.title("🤖 Estado Actual del Bot de Citas - Sanitas")

# Zona horaria y conexión
TZ = pytz.timezone("America/Bogota")
client = MongoClient(st.secrets["mongo_uri"])
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]
estado = db["estado_actual"]

# Leer estado actual
doc_estado = estado.find_one({"_id": "sanitas_estado"})
if doc_estado:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔄 Paso actual", doc_estado.get("paso", "Desconocido"))
    with col2:
        inicio = doc_estado.get("inicio_sesion")
        if inicio:
            dt_inicio = datetime.fromisoformat(inicio).astimezone(TZ)
            duracion = datetime.now(TZ) - dt_inicio
            st.metric("🕒 Duración de la sesión", str(timedelta(seconds=int(duracion.total_seconds()))))
        else:
            st.warning("Sesín no iniciada")
    with col3:
        st.metric("🔁 Ciclos ejecutados", doc_estado.get("ciclo", 0))
else:
    st.error("El bot no ha actualizado su estado.")

# Últimos eventos
st.subheader("📜 Historial reciente")
recientes = list(eventos.find().sort("timestamp", -1).limit(10))

for ev in recientes:
    tipo = ev.get("tipo", "evento")
    ts = ev["timestamp"].astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
    msj = ev.get("mensaje", "")
    if tipo == "agenda_encontrada":
        st.success(f"📬 {ts} — **Agenda disponible**")
    elif tipo == "error_critico":
        with st.expander(f"❌ {ts} — Error Crítico"):
            st.error(msj)
    elif tipo == "bloqueo" or "redirect" in tipo:
        st.warning(f"🚫 {ts} — Sesion tumbada o redirigida")
    else:
        st.info(f"ℹ️ {ts} — {msj}")

# Racha
st.subheader("🔥 Racha de búsqueda")
fechas_intentos = list(intentos.find().sort("timestamp", -1))
fechas = sorted(list(set([i["timestamp"].astimezone(TZ).date() for i in fechas_intentos])))

racha = 1
for i in range(1, len(fechas)):
    if (fechas[i-1] - fechas[i]).days == 1:
        racha += 1
    else:
        break
st.info(f"Días consecutivos con ejecución del bot: **{racha}**")

# Desde última agenda encontrada
ult_agenda = eventos.find_one({"tipo": "agenda_encontrada"}, sort=[("timestamp", -1)])
if ult_agenda:
    ts_agenda = ult_agenda["timestamp"].astimezone(TZ)
    segundos = int((datetime.now(TZ) - ts_agenda).total_seconds())
    dur = str(timedelta(seconds=segundos))
    st.success(f"⏱️ Tiempo desde última agenda: {dur}")

# Desde último resultado distinto a "sin agenda"
ult_dif = intentos.find_one({"estado": {"$ne": "Sin agenda"}}, sort=[("timestamp", -1)])
if ult_dif:
    ts_dif = ult_dif["timestamp"].astimezone(TZ)
    segundos = int((datetime.now(TZ) - ts_dif).total_seconds())
    st.warning(f"⏱️ Tiempo desde último resultado diferente a 'Sin agenda': {str(timedelta(seconds=segundos))}")

# Footer
st.caption("Desarrollado por Eliecer Ruiz - Seguimiento del bot de Sanitas EPS")
