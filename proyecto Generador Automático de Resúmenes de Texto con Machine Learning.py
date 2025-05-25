import streamlit as st
from transformers import pipeline
import docx
import re

# Cachear los pipelines para no cargarlos cada vez
@st.cache_resource
def cargar_summarizers():
    summarizer_extractivo = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    summarizer_abstractive = pipeline("summarization", model="t5-base")
    return summarizer_extractivo, summarizer_abstractive

summarizer_extractivo, summarizer_abstractive = cargar_summarizers()

def fragmentar_texto(texto, max_chunk=1000):
    """Fragmenta texto en chunks sin cortar oraciones (aprox max_chunk chars)."""
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
    return chunks

def resumir_texto(texto, summarizer, max_length=130, min_length=30, max_chunk=1000):
    """Resumir textos largos fragmentando y luego resumiendo resumen final si es muy largo."""
    chunks = fragmentar_texto(texto, max_chunk=max_chunk)
    resumenes = []
    for c in chunks:
        res = summarizer(c, max_length=max_length, min_length=min_length, do_sample=False)
        resumenes.append(res[0]['summary_text'])
    resumen_final = " ".join(resumenes)
    if len(resumen_final) > max_chunk:
        res_final = summarizer(resumen_final, max_length=max_length, min_length=min_length, do_sample=False)
        resumen_final = res_final[0]['summary_text']
    return resumen_final

def leer_docx(archivo):
    doc = docx.Document(archivo)
    texto = "\n".join([p.text for p in doc.paragraphs])
    return texto

def leer_txt(archivo):
    return archivo.getvalue().decode("utf-8")

# --- Interfaz Streamlit ---

st.title("📝 Generador Automático de Resúmenes con Transformers")

uploaded_file = st.file_uploader("Cargar archivo (.txt o .docx)", type=["txt", "docx"])
texto_largo = st.text_area("O introduce tu texto largo aquí:", height=300)

opcion = st.selectbox("Selecciona el tipo de resumen", ("Resumen Extractivo", "Resumen Abstractive"))

if opcion == "Resumen Extractivo":
    max_palabras = st.slider("Máximo de palabras en el resumen", min_value=50, max_value=500, value=150, step=10)
else:
    max_palabras = st.slider("Máximo de palabras en el resumen", min_value=50, max_value=500, value=150, step=10)

if st.button("🔍 Generar Resumen"):
    if uploaded_file is not None:
        if uploaded_file.type == "text/plain":
            texto_largo = leer_txt(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            texto_largo = leer_docx(uploaded_file)
    
    if texto_largo:
        with st.spinner("Generando resumen..."):
            if opcion == "Resumen Extractivo":
                resumen = resumir_texto(texto_largo, summarizer_extractivo, max_length=max_palabras, min_length=30)
            else:
                # Para T5, agregamos prefijo "summarize: " para mejor rendimiento
                texto_preprocesado = "summarize: " + texto_largo
                resumen = resumir_texto(texto_preprocesado, summarizer_abstractive, max_length=max_palabras, min_length=30)
        
        st.success("¡Resumen generado exitosamente!")
        st.subheader("📄 Resumen:")
        st.write(resumen)
    else:
        st.error("⚠️ Por favor, introduce o carga un texto para generar el resumen.")

