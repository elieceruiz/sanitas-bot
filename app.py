import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
import time

# --- CONFIGURACIÓN ---
st.set_page_config("Sanitas Bot Monitor", layout="centered")
st.title("🤖 Estado Actual del Bot de Citas - Sanitas")

# --- ZONA HORARIA ---
TZ = pytz.timezone("America/Bogota")

# --- CONEXIÓN A MONGO ---
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client["sanitas_bot"]
eventos = db["eventos"]
intentos = db["intentos"]
estado_actual = db["estado_actual"]

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🟢 Estado Actual", "📜 Eventos", "📌 Intentos"])

# ============================
# 🟢 TAB 1 - ESTADO ACTUAL
# ============================
with tab1:
    estado = estado_actual.find_one({"_id": "sanitas_estado"})

    if estado:
        paso = estado.get("paso", "-")
        inicio = estado.get("inicio_sesion")
        ciclo = estado.get("ciclo", 0)
        actualizado = estado.get("ultimo_update")

        dt_inicio = inicio.astimezone(TZ) if inicio else None
        dt_update = actualizado.astimezone(TZ) if actualizado else None

        if dt_inicio:
            tiempo_total = datetime.now(TZ) - dt_inicio
            st.metric("🕐 Tiempo desde que arrancó la sesión actual", str(tiempo_total).split('.')[0])
        else:
            st.warning("No hay datos de inicio de sesión")

        st.metric("🔁 Ciclos ejecutados", ciclo)
        st.success(f"🔄 Paso actual: {paso}")
        st.caption(f"Última actualización: {dt_update.strftime('%Y-%m-%d %H:%M:%S') if dt_update else '-'}")

    else:
        st.warning("No hay información disponible del estado actual.")

# ============================
# 📜 TAB 2 - HISTORIAL DE EVENTOS
# ============================
with tab2:
    st.subheader("📜 Historial de Eventos")
    rows = list(eventos.find().sort("timestamp", -1).limit(20))
    if rows:
        data = []
        for ev in rows:
            data.append({
                "Tipo": ev.get("tipo", "-"),
                "Mensaje": ev.get("mensaje", "-"),
                "Fecha y Hora": ev["timestamp"].astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("No hay eventos recientes.")

# ============================
# 📌 TAB 3 - INTENTOS
# ============================
with tab3:
    st.subheader("📌 Historial de Intentos")
    rows = list(intentos.find().sort("timestamp", -1).limit(30))
    if rows:
        data = []
        for idx, intento in enumerate(rows, start=1):
            data.append({
                "Intento": len(rows) - idx + 1,
                "Estado": intento.get("estado", "-"),
                "IP": intento.get("ip", "-"),
                "Fecha y Hora": intento["timestamp"].astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("No hay intentos registrados.")
