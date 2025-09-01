import streamlit as st
import gspread
import pandas as pd
import random
import time

# --- CONFIGURACIÓN PRINCIPAL ---
SPREADSHEET_ID = "11NEFkg-uUe1zTWKse1yC0jEUZB5gd8QZP0gBS9Rj-Kw" 
WORKSHEET_NAME = "BANCO DE PREGUNTAS"
CREDENTIALS_FILE = "google_credentials.json"

# --- TÍTULO Y CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador de Examen", layout="wide")
st.title("🚀 Simulador de Examen de Abogados (VERSIÓN DEMO)")

# --- FUNCIÓN DE CARGA DE DATOS ---
@st.cache_data(ttl=300)
def load_data():
    try:
        sa = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = sa.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet(WORKSHEET_NAME)
        df = pd.DataFrame(ws.get_all_records())
        # Limpiar datos: Reemplazar celdas vacías en opciones con un string vacío
        option_cols = ['Opción A', 'Opción B', 'Opción C', 'Opción D']
        for col in option_cols:
            if col in df.columns:
                df[col] = df[col].fillna('')
        return df
    except Exception as e:
        st.error(f"Ocurrió un error al conectar o leer Google Sheets: {e}")
        return None

# --- CARGA DE DATOS ---
df = load_data()
if df is None:
    st.stop()

# --- INICIALIZACIÓN DE ESTADO ---
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False

# --- PANEL DE CONFIGURACIÓN ---
with st.sidebar:
    st.header("🛠️ Configurar Simulacro")
    if not st.session_state.quiz_started:
        areas = ["Todas"] + sorted(df['Área Principal'].unique().tolist())
        tipos = ["Todos"] + sorted(df['Tipo de Pregunta'].unique().tolist())

        area_filter = st.selectbox("Filtrar por Área:", options=areas)
        tipo_filter = st.selectbox("Filtrar por Tipo de Pregunta:", options=tipos)
        num_questions = st.slider("Número de preguntas:", 1, len(df), 10)
        time_minutes = st.number_input("Tiempo (minutos):", min_value=1, value=num_questions * 2)

        if st.button("🚀 Iniciar Nuevo Simulacro"):
            filtered_df = df.copy()
            if area_filter != "Todas":
                filtered_df = filtered_df[filtered_df['Área Principal'] == area_filter]
            if tipo_filter != "Todos":
                filtered_df = filtered_df[filtered_df['Tipo de Pregunta'] == tipo_filter]

            if len(filtered_df) < num_questions:
                st.warning(f"Solo se encontraron {len(filtered_df)} preguntas con esos filtros. Mostrando todas las encontradas.")
                num_to_sample = len(filtered_df)
            else:
                num_to_sample = num_questions
            
            if num_to_sample > 0:
                st.session_state.questions = filtered_df.sample(n=num_to_sample).to_dict('records')
                st.session_state.user_answers = {}
                st.session_state.end_time = time.time() + time_minutes * 60
                st.session_state.quiz_started = True
                st.rerun()
            else:
                st.error("No se encontraron preguntas con los filtros seleccionados.")
    
    if st.session_state.quiz_started:
        remaining_time = st.session_state.end_time - time.time()
        if remaining_time > 0:
            minutes, seconds = divmod(int(remaining_time), 60)
            st.metric("⏳ Tiempo Restante", f"{minutes:02d}:{seconds:02d}")
        else:
            st.error("⌛ ¡Tiempo Terminado!")
            # Esto forza la calificación si el tiempo se acaba
            st.session_state.quiz_started = False 

# --- LÓGICA PRINCIPAL ---
if st.session_state.quiz_started:
    with st.form(key='quiz_form'):
        user_answers = {}
        for i, q in enumerate(st.session_state.questions):
            st.subheader(f"Pregunta {i+1} (ID: {q.get('ID_Pregunta', 'N/A')})")
            
            if q.get('Caso / Supuesto de Hecho') and len(str(q.get('Caso / Supuesto de Hecho'))) > 10:
                with st.expander("Ver Supuesto de Hecho"):
                    st.info(q['Caso / Supuesto de Hecho'])
            
            st.write(q['Pregunta'])
            
            options = [q.get('Opción A'), q.get('Opción B'), q.get('Opción C'), q.get('Opción D')]
            # Filtrar opciones que no estén vacías
            valid_options = [opt for opt in options if isinstance(opt, str) and opt.strip() != '']
            
            if not valid_options:
                st.warning("Esta pregunta no tiene opciones de respuesta en la base de datos.")
                user_answers[i] = None
            else:
                user_answers[i] = st.radio("Selecciona tu respuesta:", valid_options, key=f"q_{i}", index=None)
            
            st.markdown("---")

        submitted = st.form_submit_button("✅ Calificar Simulacro")
        if submitted:
            st.session_state.user_answers = user_answers
            st.session_state.quiz_started = False
            st.rerun()

else: # Mostrar resultados o pantalla de bienvenida
    if 'user_answers' in st.session_state and st.session_state.user_answers:
        score = 0
        st.header("🏁 Resultados del Simulacro")

        for i, q in enumerate(st.session_state.questions):
            user_answer = st.session_state.user_answers.get(i)
            correct_option_key = str(q.get('Respuesta Correcta', '')).strip()
            correct_answer = q.get(f"Opción {correct_option_key}")

            st.subheader(f"Pregunta {i+1} (ID: {q.get('ID_Pregunta', 'N/A')})")
            st.write(f"**Pregunta:** {q['Pregunta']}")

            if user_answer == correct_answer:
                score += 1
                st.success(f"✔️ Tu respuesta: {user_answer} (Correcto)")
            else:
                st.error(f"❌ Tu respuesta: {user_answer if user_answer else 'No respondida'}")
                st.info(f"✔️ Respuesta correcta: {correct_answer}")
            
            with st.expander("Ver Explicación Jurídica"):
                st.info(q.get('Explicación Jurídica', 'No disponible.'))
            st.markdown("---")

        percentage = (score / len(st.session_state.questions)) * 100
        st.sidebar.subheader("Puntuación Final")
        st.sidebar.metric(label="Correctas", value=f"{score}/{len(st.session_state.questions)}", delta=f"{percentage:.1f}%")
        
        if st.sidebar.button("↩️ Iniciar Otro Simulacro"):
            st.session_state.clear()
            st.rerun()
            
# Para el cronómetro
if st.session_state.quiz_started:
    time.sleep(1)
    st.rerun()