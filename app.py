import streamlit as st
import pandas as pd
import random
import time
from urllib.parse import quote

# --- CONFIGURACIÓN PRINCIPAL ---
SPREADSHEET_ID = "11NEFkg-uUe1zTWKse1yC0jEUZB5gd8QZP0gBS9Rj-Kw" 
WORKSHEET_NAME = "BANCO DE PREGUNTAS"

# --- TÍTULO Y CONFIGURACIÓN ---
st.set_page_config(page_title="Simulador DEMO", layout="wide")
st.title("🚀 Simulador de Examen de Abogados (DEMO)")

# --- FUNCIÓN DE CARGA DE DATOS ---
@st.cache_data(ttl=300)
def load_data():
    try:
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
df = load_data()
if df is None:
    st.stop()

# --- INICIALIZACIÓN DE ESTADO ---
if 'page' not in st.session_state:
    st.session_state.page = 'config'

# --- LÓGICA DE NAVEGACIÓN ---
def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()

def reset_and_go_to_config():
    keys_to_clear = list(st.session_state.keys())
    for key in keys_to_clear:
        if key != 'page':
            del st.session_state[key]
    st.session_state.page = 'config'
    st.rerun()

# -------------------------------------------------------------------
# ----- PÁGINA DE CONFIGURACIÓN Y BIENVENIDA ------------------------
# -------------------------------------------------------------------
if st.session_state.page == 'config':
    
    with st.sidebar:
        st.header("🛠️ Configurar Simulacro")
        header_list = df.columns.tolist()
        AREA_COL_NAME = header_list[1]
        TIPO_COL_NAME = header_list[3]
        areas = ["Todas"] + sorted([str(area) for area in df[AREA_COL_NAME].unique() if str(area).strip() != ''])
        tipos = ["Todos"] + sorted([str(tipo) for tipo in df[TIPO_COL_NAME].unique() if str(tipo).strip() != ''])

        # Usamos st.session_state.get para evitar errores si la clave no existe
        area_filter = st.sidebar.selectbox("Filtrar por Área:", options=areas, key="area_filter")
        tipo_filter = st.sidebar.selectbox("Filtrar por Tipo de Pregunta:", options=tipos, key="tipo_filter")
        num_questions = st.sidebar.slider("Número de preguntas:", 1, len(df), 10, key="num_questions")
        time_minutes = st.sidebar.number_input("Tiempo (minutos):", min_value=1, value=20, key="time_minutes")

        if st.button("🚀 Iniciar Simulacro"):
            filtered_df = df.copy()
            if st.session_state.get("area_filter", "Todas") != "Todas": filtered_df = filtered_df[filtered_df[AREA_COL_NAME] == st.session_state.area_filter]
            if st.session_state.get("tipo_filter", "Todos") != "Todos": filtered_df = filtered_df[filtered_df[TIPO_COL_NAME] == st.session_state.tipo_filter]
            
            if len(filtered_df) == 0:
                st.warning("No se encontraron preguntas con los filtros seleccionados.")
            else:
                num_to_sample = min(st.session_state.num_questions, len(filtered_df))
                st.session_state.questions = filtered_df.sample(n=num_to_sample).to_dict('records')
                st.session_state.user_answers = {}
                st.session_state.end_time = time.time() + st.session_state.time_minutes * 60
                go_to_page('quiz')

    st.header("👋 ¡Bienvenido al Simulador!")
    st.markdown("---")
    st.subheader("Instrucciones para empezar:")
    col1, col2 = st.columns([1, 2])
    with col1:
        # IMAGEN NUEVA Y MEJORADA (Blanca, se ve bien en ambos modos)
        st.image("https://upload.wikimedia.org/wikipedia/commons/d/da/Flechas_Avanzar.png", 
         caption="En móvil, haz clic parte superior izquierda para abrir la configuración.", 
         width=90) # Ajustamos el tamaño para que se vea bien
    with col2:
        st.markdown("""
        **1. Configura tu examen en el panel lateral.**
        *   Filtra por área y tipo de pregunta.
        *   Elige el número de preguntas y el tiempo.
        
        **2. ¡Inicia el Simulacro!**
        *   Haz clic en el botón azul **'Iniciar Simulacro'**.
        """)
    st.markdown("---")


# -------------------------------------------------------------------
# ----- PÁGINA DEL SIMULACRO ----------------------------------------
# -------------------------------------------------------------------
elif st.session_state.page == 'quiz':
    # ... (código igual a la versión anterior) ...
    remaining_time = st.session_state.end_time - time.time()
    if remaining_time <= 0:
        st.sidebar.error("⌛ ¡Tiempo Terminado!")
        go_to_page('results')
        st.rerun()
    else:
        minutes, seconds = divmod(int(remaining_time), 60)
        st.sidebar.metric("⏳ Tiempo Restante", f"{minutes:02d}:{seconds:02d}")
    with st.form(key='quiz_form'):
        for i, q in enumerate(st.session_state.questions):
            st.subheader(f"Pregunta {i+1} (ID: {q[df.columns[0]]})")
            if q[df.columns[4]]:
                with st.expander("Ver Supuesto de Hecho"): st.info(q[df.columns[4]])
            st.write(q[df.columns[5]])
            options = [q[df.columns[6]], q[df.columns[7]], q[df.columns[8]], q[df.columns[9]]]
            valid_options = [opt for opt in options if opt]
            if valid_options:
                st.radio("Selecciona tu respuesta:", valid_options, key=f"q_{i}", index=None)
            else:
                st.warning("Pregunta sin opciones de respuesta.")
            st.markdown("---")
        if st.form_submit_button("✅ Calificar Simulacro"):
            for i in range(len(st.session_state.questions)):
                st.session_state.user_answers[i] = st.session_state.get(f"q_{i}")
            go_to_page('results')
            st.rerun()

# -------------------------------------------------------------------
# ----- PÁGINA DE RESULTADOS ----------------------------------------
# -------------------------------------------------------------------
elif st.session_state.page == 'results':
    st.header("🏁 Resultados del Simulacro")
    if 'celebrated' not in st.session_state:
        st.balloons()
        st.session_state.celebrated = True
    
    # ... (código de cálculo de puntaje y botón de reinicio es igual) ...
    score = 0
    for i, q in enumerate(st.session_state.questions):
        user_answer = st.session_state.user_answers.get(i)
        correct_option_char = str(q[df.columns[10]]).strip()
        correct_answer = q.get(f"Opción {correct_option_char}")
        if user_answer == correct_answer: score += 1
    percentage = (score / len(st.session_state.questions)) * 100 if st.session_state.questions else 0
    st.sidebar.subheader("Puntuación Final")
    st.sidebar.metric(label="Correctas", value=f"{score}/{len(st.session_state.questions)}", delta=f"{percentage:.1f}%")
    if st.sidebar.button("↩️ Configurar Nuevo Simulacro"):
        reset_and_go_to_config()

    for i, q in enumerate(st.session_state.questions):
        # ... (código de muestra de resultados es igual) ...
        user_answer = st.session_state.user_answers.get(i)
        correct_option_char = str(q[df.columns[10]]).strip()
        correct_answer = q.get(f"Opción {correct_option_char}")
        st.subheader(f"Pregunta {i+1} (ID: {q[df.columns[0]]})"); st.write(f"**Pregunta:** {q[df.columns[5]]}")
        if user_answer == correct_answer: st.success(f"✔️ Tu respuesta: {user_answer} (Correcto)")
        else:
            st.error(f"❌ Tu respuesta: {user_answer if user_answer else 'No respondida'}"); st.info(f"✔️ Respuesta correcta: {correct_answer}")
        with st.expander("Ver Explicación Jurídica"): st.info(q.get(df.columns[11], 'No disponible.'))
        st.markdown("---")
        
    # --- MENSAJE DE MARKETING CORREGIDO ---
    whatsappNumber = "+573192463945"
    whatsapp_message = "Hola, probé la DEMO del simulador y quiero la versión completa por $10.000 COP."
    whatsapp_link = f"https://wa.me/{whatsappNumber}?text={quote(whatsapp_message)}"
    
    st.markdown(f"""
    <div style="padding: 20px; border: 2px dashed #25D366; border-radius: 8px; background-color: #f0fff0; color: #000000; text-align: center; margin-top: 40px;">
        <h3 style="color: #128C7E;">¡Gracias por completar el simulacro!</h3>
        <p style="font-size: 1.1em;">
            Esperamos que esta herramienta te sea de gran ayuda. La práctica constante es la clave del éxito.
        </p>
        <p style="font-size: 1.2em; font-weight: bold;">
            ¿Listo para llevar tu preparación al siguiente nivel?
        </p>
        <p>
            La versión completa incluye acceso a nuestro banco con más de <strong>166 preguntas</strong>, simulacros ilimitados y la posibilidad de filtrar por temas específicos para atacar tus debilidades.
        </p>
        <p style="font-size: 1.4em; text-align: center; font-weight: bold; color: #000000; margin-top: 15px; margin-bottom: 15px;">
            Acceso total por un pago único de $10.000 COP
        </p>
        <a href="{whatsapp_link}" target="_blank" style="text-decoration: none;">
            <button style="background-color: #25D366; color: white; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; width: 80%; margin-top: 10px;">
                ¡Quiero la Versión PREMIUM! (Contactar por WhatsApp)
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- BUCLE DE REFRESCO PARA EL CRONÓMETRO ---
if st.session_state.page == 'quiz':
    time.sleep(1)
    st.rerun()