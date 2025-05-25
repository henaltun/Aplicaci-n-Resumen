import streamlit as st
from transformers import pipeline
import docx
import base64
from io import BytesIO
from docx import Document
import gc

# ================= IMAGEN DE FONDO =====================
with open("imagen fondo proyecto.jpg", "rb") as img_file:
    img_bytes = img_file.read()
    img_base64 = base64.b64encode(img_bytes).decode()

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ================= FUNCIONES =====================
def leer_txt(archivo):
    return archivo.getvalue().decode("utf-8")

def leer_docx(archivo):
    doc = docx.Document(archivo)
    texto = "\n".join([p.text for p in doc.paragraphs])
    return texto

@st.cache_resource
def cargar_summarizer():
    return pipeline("summarization", model="mrm8488/t5-small-finetuned-summarization-es")

def crear_word(texto):
    doc = Document()
    doc.add_heading("Resumen Generado", 0)
    doc.add_paragraph(texto)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ================= INTERFAZ STREAMLIT =====================
st.title("📝 Generador Automático de Resúmenes (Abstractive)")

uploaded_file = st.file_uploader("Cargar archivo (.txt o .docx)", type=["txt", "docx"])
texto_largo = st.text_area("O escribe tu texto aquí (máx. 1500 caracteres):", height=300)

max_palabras = st.slider("Máximo de palabras del resumen", min_value=30, max_value=200, value=100, step=10)

if st.button("🔍 Generar Resumen"):
    if uploaded_file:
        if uploaded_file.type == "text/plain":
            texto_largo = leer_txt(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            texto_largo = leer_docx(uploaded_file)

    if texto_largo:
        if len(texto_largo) > 1500:
            st.error("⚠️ El texto es demasiado largo. Por favor, limita a 1500 caracteres.")
            st.stop()

        with st.spinner("Generando resumen..."):
            summarizer = cargar_summarizer()
            entrada = "summarize: " + texto_largo
            resumen = summarizer(entrada, max_length=max_palabras, min_length=30, do_sample=False)[0]['summary_text']

        st.success("✅ ¡Resumen generado exitosamente!")
        st.subheader("📄 Resumen:")
        st.write(resumen)
        st.write(f"✏️ El resumen contiene **{len(resumen.split())} palabras**.")

        st.download_button("💾 Descargar .txt", resumen.encode('utf-8'), "resumen.txt", "text/plain")
        st.download_button("💾 Descargar .docx", crear_word(resumen), "resumen.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        # Liberar memoria
        del summarizer
        gc.collect()
    else:
        st.error("⚠️ Por favor, introduce o carga un texto para generar el resumen.")


