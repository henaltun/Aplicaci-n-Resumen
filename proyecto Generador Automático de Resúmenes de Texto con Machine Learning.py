import streamlit as st
from transformers import pipeline
import docx
import re
import base64
from io import BytesIO
from docx import Document
import gc

# =========== FONDO ============
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

# =========== FUNCIONES ============
def leer_txt(archivo):
    return archivo.getvalue().decode("utf-8")

def leer_docx(archivo):
    doc = docx.Document(archivo)
    texto = "\n".join([p.text for p in doc.paragraphs])
    return texto

@st.cache_resource
def cargar_summarizer():
    return pipeline("summarization", model="mrm8488/bert2bert_shared-spanish-finetuned-summarization")

def fragmentar_texto(texto, max_chunk=500):
    frases = re.split(r'(?<=[.?!])\s+', texto)
    chunks = []
    chunk = ""
    for frase in frases:
        if len(chunk) + len(frase) <= max_chunk:
            chunk += frase + " "
        else:
            chunks.append(chunk.strip())
            chunk = frase + " "
    if chunk:
        chunks.append(chunk.strip())
    return chunks[:5]  # Máximo 5 fragmentos

def resumir_texto(texto, summarizer, max_length=150, min_length=30):
    chunks = fragmentar_texto(texto)
    resumenes = []
    for c in chunks:
        res = summarizer(c, max_length=max_length, min_length=min_length, do_sample=False)
        resumenes.append(res[0]['summary_text'])
    resumen_final = " ".join(resumenes)
    return resumen_final

def crear_word(texto):
    doc = Document()
    doc.add_heading("Resumen Generado", 0)
    doc.add_paragraph(texto)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# =========== INTERFAZ STREAMLIT ============
st.title("📝 Generador de Resumen Extractivo")

uploaded_file = st.file_uploader("Cargar archivo (.txt o .docx)", type=["txt", "docx"])
texto_largo = st.text_area("O escribe tu texto:", height=300)
max_palabras = st.slider("Máximo de palabras", 50, 300, 120, step=10)

if st.button("🔍 Generar Resumen"):
    if uploaded_file:
        if uploaded_file.type == "text/plain":
            texto_largo = leer_txt(uploaded_file)
        else:
            texto_largo = leer_docx(uploaded_file)

    if texto_largo:
        if len(texto_largo) > 5000:
            st.error("⚠️ Texto muy largo. Máximo 5000 caracteres.")
            st.stop()

        with st.spinner("Generando resumen..."):
            summarizer = cargar_summarizer()
            resumen = resumir_texto(texto_largo, summarizer, max_length=min(max_palabras, 200))
            del summarizer
            gc.collect()

        st.success("✅ Resumen generado")
        st.subheader("📄 Resumen:")
        st.write(resumen)
        st.download_button("💾 Descargar .txt", resumen.encode(), "resumen.txt")
        st.download_button("💾 Descargar .docx", crear_word(resumen), "resumen.docx")
    else:
        st.error("⚠️ Ingresa o carga un texto primero.")

