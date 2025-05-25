import streamlit as st
from transformers import pipeline
import docx
import re
import base64
from io import BytesIO
from docx import Document
import gc  # Liberar memoria

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
def cargar_summarizer(nombre_modelo):
    return pipeline("summarization", model=nombre_modelo)

def fragmentar_texto(texto, max_chunk=1000):
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

def contar_palabras(texto):
    return len(texto.split())

def crear_word(texto):
    doc = Document()
    doc.add_heading("Resumen Generado", 0)
    doc.add_paragraph(texto)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ================= INTERFAZ STREAMLIT =====================
st.title("📝 Generador Automático de Resúmenes en Español")

uploaded_file = st.file_uploader("Cargar archivo (.txt o .docx)", type=["txt", "docx"])
texto_largo = st.text_area("O introduce tu texto largo aquí:", height=300)

opcion = st.selectbox("Selecciona el tipo de resumen", ("Extractivo", "Abstractive"))
max_palabras = st.slider("Máximo de palabras", min_value=50, max_value=500, value=150, step=10)

if st.button("🔍 Generar Resumen"):
    if uploaded_file:
        if uploaded_file.type == "text/plain":
            texto_largo = leer_txt(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            texto_largo = leer_docx(uploaded_file)

    if texto_largo:
        if len(texto_largo) > 5000:
            st.error("⚠️ El texto es demasiado largo. Por favor, limita a 5000 caracteres.")
            st.stop()

        with st.spinner("Generando resumen en español..."):
            if opcion == "Extractivo":
                modelo = "mrm8488/bert2bert_shared-spanish-finetuned-summarization"
                summarizer = cargar_summarizer(modelo)
                resumen = resumir_texto(texto_largo, summarizer, max_length=max_palabras, min_length=30)
            else:
                modelo = "mrm8488/t5-base-finetuned-summarization-es"
                summarizer = cargar_summarizer(modelo)
                texto_preprocesado = "summarize: " + texto_largo
                resumen = resumir_texto(texto_preprocesado, summarizer, max_length=max_palabras, min_length=30)

        st.success("✅ ¡Resumen generado exitosamente!")
        st.subheader("📄 Resumen:")
        st.write(resumen)
        st.write(f"✏️ El resumen contiene **{contar_palabras(resumen)} palabras**.")

        st.download_button("💾 Descargar .txt", resumen.encode('utf-8'), "resumen.txt", "text/plain")
        st.download_button("💾 Descargar .docx", crear_word(resumen), "resumen.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        # Liberar memoria
        del summarizer
        gc.collect()
    else:
        st.error("⚠️ Por favor, introduce o carga un texto para generar el resumen.")



