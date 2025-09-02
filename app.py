import streamlit as st
import pandas as pd
import random
import time
from urllib.parse import quote # Importamos la librería correcta para codificar URLs

# --- CONFIGURACIÓN PRINCIPAL ---
# Pega aquí el ID de tu hoja de cálculo DEMO (la que hiciste pública)
SPREADSHEET_ID = "11NEFkg-uUe1zTWKse1yC0jEUZB5gd8QZP0gBS9Rj-Kw" 
WORKSHEET_NAME = "BANCO DE PREGUNTAS"

# --- TÍTULO Y CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador DEMO", layout="wide")
st.title("🚀 Simulador de Examen de Abogados (DEMO)")

# --- FUNCIÓN DE CARGA DE DATOS (MÉTODO PÚBLICO - CORREGIDO Y MODERNO) ---
@st.cache_data(ttl=300)
def load_public_data():
    try:
        # Usamos 'quote' para codificar correctamente el nombre de la hoja
        worksheet_name_encoded = quote(WORKSHEET_NAME)
        csv_url = f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={worksheet_name_encoded}'
        
        df = pd.read_csv(csv_url)
        df.fillna('', inplace=True)
        return df
    except Exception as e:
        st.error(f"Error al leer la hoja pública: {e}.")
        st.info("Asegúrate de que el ID de la hoja sea correcto y que el permiso en 'Compartir' sea 'Cualquier persona con el enlace puede ver'.")
        return None

# --- CARGA INICIAL DE DATOS ---
df = load_public_data() # Llamada a la función correcta
if df is None:
    st.stop()

# (El resto del código se queda exactamente igual que en la v2.5. Lo incluyo para que sea copiar y pegar)
# --- INICIALIZACIÓN DE ESTADO ---
if 'page' not in st.session_state:
    st.session_state.page = 'config'
# ... (El resto del código es idéntico al anterior)
def show_config_page(): st.session_state.page = 'config'
def show_quiz_page(): st.session_state.page = 'quiz'
def show_results_page(): st.session_state.page = 'results'
Iniciar Simulacro
elif st.session_state.page == 'quiz':
    remaining_time = st.session_state.end_time - time.time()
    if remaining_time <= 0: st.sidebar.error("⌛ ¡Tiempo Terminado!"); show_results_page(); st.rerun()
    minutes, seconds = divmod(int(remaining_time), 60); st.sidebar.metric("⏳ Tiempo Restante", f"{minutes:02d}:{seconds:02d}")
    with st.form(key='quiz_form'):
        user_answers = {}
        for i, q in enumerate(st.session_state.questions):
            st.subheader(f"Pregunta {i+1} (ID: {q[df.columns[0]]})"); 
            if q[df.columns[4]]:
                with st.expander("Ver Supuesto de Hecho"): st.info(q[df.columns[4]])
            st.write(q[df.columns[5]])
            options = [q[df.columns[6]], q[df.columns[7]], q[df.columns[8]], q[df.columns[9]]]; valid_options = [opt for opt in options if opt]
            if valid_options: user_answers[i] = st.radio("Selecciona tu respuesta:", valid_options, key=f"q_{i}", index=None)
            else: st.warning("Pregunta sin opciones de respuesta."); user_answers[i] = None
            st.markdown("---")
        if st.form_submit_button("✅ Calificar Simulacro"):
            st.session_state.user_answers = user_answers; show_results_page(); st.rerun()
elif st.session_state.page == 'results':
    st.header("🏁 Resultados del Simulacro"); score = 0
    for i, q in enumerate(st.session_state.questions):
        user_answer = st.session_state.user_answers[i]; correct_option_char = str(q[df.columns[10]]).strip(); correct_answer = q.get(f"Opción {correct_option_char}")
        if user_answer == correct_answer: score += 1
    percentage = (score / len(st.session_state.questions)) * 100
    st.sidebar.subheader("Puntuación Final"); st.sidebar.metric(label="Correctas", value=f"{score}/{len(st.session_state.questions)}", delta=f"{percentage:.1f}%")
    for i, q in enumerate(st.session_state.questions):
        user_answer = st.session_state.user_answers[i]; correct_option_char = str(q[df.columns[10]]).strip(); correct_answer = q.get(f"Opción {correct_option_char}")
        st.subheader(f"Pregunta {i+1} (ID: {q[df.columns[0]]})"); st.write(f"**Pregunta:** {q[df.columns[5]]}")
        if user_answer == correct_answer: st.success(f"✔️ Tu respuesta: {user_answer} (Correcto)")
        else:
            st.error(f"❌ Tu respuesta: {user_answer if user_answer else 'No respondida'}"); st.info(f"✔️ Respuesta correcta: {correct_answer}")
        with st.expander("Ver Explicación Jurídica"): st.info(q.get(df.columns[11], 'No disponible.'))
        st.markdown("---")
    if st.sidebar.button("↩️ Configurar Nuevo Simulacro"): show_config_page(); st.rerun()
if st.session_state.page == 'quiz': time.sleep(1); st.rerun()