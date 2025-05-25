import streamlit as st
from transformers import pipeline
import docx
import re
import base64
from io import BytesIO
from docx import Document
import base64

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
    label, .stSelectbox label, .stSlider label, .stFileUploader label {{
        color: white !important;
    }}
    .stButton > button {{
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        font-size: 18px;
    }}
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {{
        background-color: rgba(0, 0, 0, 0.6);
        color: white;
        border: 1px solid #ccc;
        border-radius: 10px;
    }}
    .css-1v0mbdj, .css-1d391kg {{
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 15px;
        padding: 1em;
    }}
    .css-1cpxqw2, .css-q8sbsg {{
        color: white !important;
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
def cargar_summarizers():
    summarizer_extractivo = pipeline("summarization", model="mrm8488/bert2bert_shared-spanish-finetuned-summarization")
    summarizer_abstractive = pipeline("summarization", model="mrm8488/t5-base-finetuned-summarization-es)
    return summarizer_extractivo, summarizer_abstractive

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

st.title("📝 Generador Automático de Resúmenes con Transformers")

uploaded_file = st.file_uploader("Cargar archivo (.txt o .docx)", type=["txt", "docx"])
texto_largo = st.text_area("O introduce tu texto largo aquí:", height=300)

opcion = st.selectbox("Selecciona el tipo de resumen", ("Resumen Extractivo", "Resumen Abstractive"))
max_palabras = st.slider("Máximo de palabras en el resumen", min_value=50, max_value=500, value=150, step=10)

if st.button("🔍 Generar Resumen"):
    if uploaded_file is not None:
        if uploaded_file.type == "text/plain":
            texto_largo = leer_txt(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            texto_largo = leer_docx(uploaded_file)
    
    if texto_largo:
        with st.spinner("Generando resumen..."):
            summarizer_extractivo, summarizer_abstractive = cargar_summarizers()

            if opcion == "Resumen Extractivo":
                resumen = resumir_texto(texto_largo, summarizer_extractivo, max_length=max_palabras, min_length=30)
            else:
                texto_preprocesado = texto_largo
                resumen = resumir_texto(texto_preprocesado, summarizer_abstractive, max_length=max_palabras, min_length=30)

        st.success("✅ ¡Resumen generado exitosamente!")
        st.subheader("📄 Resumen:")
        st.write(resumen)
        st.write(f"📝 El resumen contiene **{contar_palabras(resumen)} palabras**.")

        st.download_button(
            label="💾 Descargar .txt",
            data=resumen.encode('utf-8'),
            file_name="resumen.txt",
            mime="text/plain"
        )

        st.download_button(
            label="💾 Descargar .docx",
            data=crear_word(resumen),
            file_name="resumen.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        st.error("⚠️ Por favor, introduce o carga un texto para generar el resumen.")


