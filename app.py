import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz

# === Config ===
st.set_page_config("🩺 Sanitas Bot Monitor", layout="centered")
st.title("🤖 Estado del Bot de Citas - Sanitas")

# Zona horaria
TZ = pytz.timezone("America/Bogota")

# Conexión MongoDB
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]
estado_actual = db["estado_actual"]

# Estado actual
doc = estado_actual.find_one({"_id": "sanitas_estado"})
now = datetime.now(TZ)
bot_activo = False

if doc and doc.get("ultimo_update"):
    last_update = doc["ultimo_update"].astimezone(TZ)
    if (now - last_update).total_seconds() < 180:
        bot_activo = True

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Estado actual", "🗂️ Eventos recientes", "📊 Historial de intentos"])

# === TAB 1: Estado ===
with tab1:
    if bot_activo:
        st.success("🟢 Bot activo")
    else:
        st.error("🔴 Bot detenido")

    # Cronómetro
    dt_inicio = None
    mensaje_tiempo = ""

    if bot_activo:
        dt_inicio = doc.get("inicio_sesion", now).astimezone(TZ)
        mensaje_tiempo = "🕐 Tiempo desde inicio"
    else:
        ult_error = eventos.find_one(
            {"tipo": {"$in": ["error_critico", "sesion_cerrada"]}},
            sort=[("timestamp", -1)]
        )
        if ult_error:
            dt_inicio = ult_error["timestamp"].astimezone(TZ)
            mensaje_tiempo = "🕐 Tiempo desde la última caída"

    if dt_inicio:
        duracion = str(timedelta(seconds=int((now - dt_inicio).total_seconds())))
        st.metric(mensaje_tiempo, duracion)

    st.metric("🔁 Ciclos ejecutados", doc.get("ciclo", 0) if doc else 0)

    paso = doc.get("paso") if doc else None
    if paso:
        st.info(f"🔄 Paso actual: {paso}")

# === TAB 2: Eventos ===
with tab2:
    st.subheader("📜 Historial de eventos recientes")
    raw = list(eventos.find().sort("timestamp", -1).limit(10))
    if raw:
        for ev in raw:
            fecha = ev["timestamp"].astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            with st.expander(f"{fecha} - {ev['tipo']}"):
                st.code(ev["mensaje"])
    else:
        st.info("No hay eventos registrados.")

# === TAB 3: Intentos ===
with tab3:
    st.subheader("📊 Historial completo de intentos")
    tabla_intentos = list(intentos.find().sort("timestamp", -1))

    if tabla_intentos:
        data = []
        total = len(tabla_intentos)
        for i, intento in enumerate(tabla_intentos, 1):
            data.append({
                "Intento #": total - i + 1,
                "Estado": intento["estado"],
                "IP": intento.get("ip", "N/A"),
                "Hora": intento["timestamp"].astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("No hay intentos registrados.")

# Refresco automático
st.rerun()
