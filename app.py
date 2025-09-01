import streamlit as st
import gspread
import pandas as pd
import random
import time

# --- CONFIGURACIÓN PRINCIPAL ---
# La URL COMPLETA de tu hoja de cálculo DEMO
# ¡¡Asegúrate de que sea pública con "Cualquier persona con el enlace"!!
SHEET_URL = "11NEFkg-uUe1zTWKse1yC0jEUZB5gd8QZP0gBS9Rj-Kw"
WORKSHEET_NAME = "BANCO DE PREGUNTAS"

# --- TÍTULO Y CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador DEMO", layout="wide")
st.title("🚀 Simulador de Examen de Abogados (DEMO)")

# --- FUNCIÓN DE CARGA DE DATOS (AHORA PÚBLICA) ---
@st.cache_data(ttl=300)
def load_public_data():
    try:
        # Autorización pública, no necesita credenciales
        gc = gspread.service_account() # Se deja vacío para modo público
        sh = gc.open_by_url(SHEET_URL)
        ws = sh.worksheet(WORKSHEET_NAME)
        df = pd.DataFrame(ws.get_all_records())
        df.fillna('', inplace=True)
        return df
    except Exception as e:
        st.error(f"Ocurrió un error al leer la hoja pública: {e}. Asegúrate de que la URL es correcta y que el permiso es 'Cualquier persona con el enlace puede ver'.")
        return None

# --- CARGA DE DATOS ---
df = load_public_data()
if df is None:
    st.stop()

# --- El resto del código de la aplicación (la lógica del simulacro) es EXACTAMENTE EL MISMO que antes ---
# (Pega aquí el resto del código de la versión v2.5, desde la inicialización del estado en adelante)

# --- INICIALIZACIÓN DE ESTADO ---
if 'page' not in st.session_state:
    st.session_state.page = 'config'

# --- LÓGICA DE NAVEGACIÓN ---
def show_config_page(): st.session_state.page = 'config'
def show_quiz_page(): st.session_state.page = 'quiz'
def show_results_page(): st.session_state.page = 'results'

# ----- PÁGINA DE CONFIGURACIÓN -----
if st.session_state.page == 'config':
    st.sidebar.header("🛠️ Configurar Simulacro")
    header_list = df.columns.tolist()
    AREA_COL_NAME = header_list[1]
    TIPO_COL_NAME = header_list[3]
    
    areas = ["Todas"] + sorted(df[AREA_COL_NAME].astype(str).unique().tolist())
    tipos = ["Todos"] + sorted(df[TIPO_COL_NAME].astype(str).unique().tolist())

    area_filter = st.sidebar.selectbox("Filtrar por Área:", options=areas, key="area_filter")
    tipo_filter = st.sidebar.selectbox("Filtrar por Tipo de Pregunta:", options=tipos, key="tipo_filter")
    num_questions = st.sidebar.slider("Número de preguntas:", 1, len(df), 10, key="num_questions")
    time_minutes = st.sidebar.number_input("Tiempo (minutos):", min_value=1, value=num_questions * 2, key="time_minutes")

    if st.sidebar.button("🚀 Iniciar Simulacro"):
        # ... (La lógica de inicio es la misma que v2.5)
        filtered_df = df.copy()
        if st.session_state.area_filter != "Todas": filtered_df = filtered_df[filtered_df[AREA_COL_NAME] == st.session_state.area_filter]
        if st.session_state.tipo_filter != "Todos": filtered_df = filtered_df[filtered_df[TIPO_COL_NAME] == st.session_state.tipo_filter]
        if len(filtered_df) == 0: st.sidebar.warning("No se encontraron preguntas con los filtros seleccionados.")
        else:
            num_to_sample = min(st.session_state.num_questions, len(filtered_df))
            st.session_state.questions = filtered_df.sample(n=num_to_sample).to_dict('records')
            st.session_state.user_answers = [None] * num_to_sample
            st.session_state.end_time = time.time() + st.session_state.time_minutes * 60
            show_quiz_page()
            st.rerun()

    st.header("Bienvenido al Simulador (Versión DEMO)")
    st.write("Configura tu examen en la barra lateral y haz clic en 'Iniciar Simulacro'.")

# ... (El resto de las páginas 'quiz' y 'results' son las mismas que la versión v2.5)
elif st.session_state.page == 'quiz':
    remaining_time = st.session_state.end_time - time.time()
    if remaining_time <= 0:
        st.sidebar.error("⌛ ¡Tiempo Terminado!")
        show_results_page()
        st.rerun()
    minutes, seconds = divmod(int(remaining_time), 60)
    st.sidebar.metric("⏳ Tiempo Restante", f"{minutes:02d}:{seconds:02d}")
    for i, q in enumerate(st.session_state.questions):
        st.subheader(f"Pregunta {i+1} (ID: {q[df.columns[0]]})")
        if q[df.columns[4]]:
            with st.expander("Ver Supuesto de Hecho"):
                st.info(q[df.columns[4]])
        st.write(q[df.columns[5]])
        options = [q[df.columns[6]], q[df.columns[7]], q[df.columns[8]], q[df.columns[9]]]
        valid_options = [opt for opt in options if opt]
        if valid_options:
            st.session_state.user_answers[i] = st.radio("Selecciona tu respuesta:", valid_options, key=f"q_{i}", index=None)
        else:
            st.warning("Pregunta sin opciones de respuesta.")
        st.markdown("---")
    if st.button("✅ Calificar Simulacro"):
        show_results_page()
        st.rerun()

elif st.session_state.page == 'results':
    st.header("🏁 Resultados del Simulacro")
    score = 0
    for i, q in enumerate(st.session_state.questions):
        user_answer = st.session_state.user_answers[i]
        correct_option_char = str(q[df.columns[10]]).strip()
        correct_answer = q.get(f"Opción {correct_option_char}")
        if user_answer == correct_answer:
            score += 1
    percentage = (score / len(st.session_state.questions)) * 100
    st.sidebar.subheader("Puntuación Final")
    st.sidebar.metric(label="Correctas", value=f"{score}/{len(st.session_state.questions)}", delta=f"{percentage:.1f}%")
    for i, q in enumerate(st.session_state.questions):
        user_answer = st.session_state.user_answers[i]
        correct_option_char = str(q[df.columns[10]]).strip()
        correct_answer = q.get(f"Opción {correct_option_char}")
        st.subheader(f"Pregunta {i+1} (ID: {q[df.columns[0]]})")
        st.write(f"**Pregunta:** {q[df.columns[5]]}")
        if user_answer == correct_answer: st.success(f"✔️ Tu respuesta: {user_answer} (Correcto)")
        else:
            st.error(f"❌ Tu respuesta: {user_answer if user_answer else 'No respondida'}")
            st.info(f"✔️ Respuesta correcta: {correct_answer}")
        with st.expander("Ver Explicación Jurídica"):
            st.info(q.get(df.columns[11], 'No disponible.'))
        st.markdown("---")
    if st.sidebar.button("↩️ Configurar Nuevo Simulacro"):
        show_config_page()
        st.rerun()

if st.session_state.page == 'quiz':
    time.sleep(1)
    st.rerun()