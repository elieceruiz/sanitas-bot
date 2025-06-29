import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz

# --- Configuración inicial ---
st.set_page_config(page_title="Bot Sanitas - Estado", layout="centered")
st.title("🤖 Estado del Bot de Sanitas")

# --- Zona horaria ---
tz = pytz.timezone("America/Bogota")
agora = datetime.now(tz)

# --- Conexión a MongoDB ---
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]
estado_actual = db["estado_actual"].find_one({"_id": "sanitas_estado"})

# --- Estado del bot ---
if estado_actual:
    ultimo_update = estado_actual.get("ultimo_update")
    paso = estado_actual.get("paso", "(desconocido)")
    ciclo = estado_actual.get("ciclo", 0)
    inicio_sesion = estado_actual.get("inicio_sesion")
    ip = estado_actual.get("ip", "-")

    tiempo_sin_update = agora - ultimo_update.astimezone(tz)
    if tiempo_sin_update.total_seconds() > 300:
        st.error(f"🛑 El bot NO está activo. Última actualización: {ultimo_update.strftime('%H:%M:%S')}")
    else:
        st.success(f"🟢 Bot activo — Paso actual: **{paso}**")

    st.metric("Ciclos ejecutados", ciclo)
    st.metric("IP última sesión", ip)

    if inicio_sesion:
        duracion_sesion = agora - inicio_sesion.astimezone(tz)
        st.metric("🕒 Duración sesión", str(timedelta(seconds=int(duracion_sesion.total_seconds()))))
else:
    st.warning("No hay información disponible sobre el estado actual del bot.")

st.markdown("---")

# --- Racha de días consecutivos ---
st.subheader("🔥 Racha de días con búsqueda")
intentos_dias = intentos.distinct("timestamp")
fechas = sorted({ts.astimezone(tz).date() for ts in intentos_dias})

racha = 0
hoy = agora.date()
for i in range(len(fechas) - 1, -1, -1):
    if fechas[i] == hoy - timedelta(days=racha):
        racha += 1
    else:
        break
st.metric("Días consecutivos de búsqueda", racha)

st.markdown("---")

# --- Última disponibilidad encontrada ---
evento_disp = eventos.find_one({"tipo": "agenda_encontrada"}, sort=[("timestamp", -1)])
if evento_disp:
    hora_disp = evento_disp["timestamp"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
    st.success(f"✅ Última disponibilidad detectada: {hora_disp}")
else:
    st.info("No se ha detectado ninguna disponibilidad aún.")

# --- Último bloqueo o caída ---
evento_bloqueo = eventos.find_one({"tipo": "error_critico"}, sort=[("timestamp", -1)])
if evento_bloqueo:
    hora_error = evento_bloqueo["timestamp"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
    st.error(f"❌ Último error crítico: {hora_error}")

st.markdown("---")

# --- Historial resumido ---
st.subheader("📜 Historial reciente de eventos")
eventos_recientes = eventos.find().sort("timestamp", -1).limit(10)
for ev in eventos_recientes:
    hora = ev["timestamp"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
    tipo = ev.get("tipo", "sin_tipo")
    mensaje = ev.get("mensaje", "")
    st.markdown(f"- **{hora}** — `{tipo}` — {mensaje}")
