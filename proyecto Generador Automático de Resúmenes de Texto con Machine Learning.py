import streamlit as st
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer as SumyTokenizer
from sumy.summarizers.lsa import LsaSummarizer
from transformers import T5Tokenizer, T5ForConditionalGeneration
from io import BytesIO
import docx
from docx import Document
from PIL import Image
import base64

# ==== MODELO ABSTRÁCTIVO CARGADO UNA VEZ ====
@st.cache_resource
def cargar_modelo_t5():
    modelo = T5ForConditionalGeneration.from_pretrained("t5-base")
    tokenizador = T5Tokenizer.from_pretrained("t5-base")
    return modelo, tokenizador

modelo_t5, tokenizador_t5 = cargar_modelo_t5()

# ==== FONDO PERSONALIZADO ====
with open("imagen fondo proyecto.jpg", "rb") as img_file:
    img_bytes = img_file.read()
    img_base64 = base64.b64encode(img_bytes).decode()

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url('data:image/jpg;base64,{img_base64}');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: #FFFFFF;
    }}
    label, .stSelectbox label, .stSlider label, .stFileUploader label {{
        color: white !important;
    }}
    .stButton > button {{
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 0.5em 1em;
        font-size: 18px;
    }}
    .stTextInput > div > div > input, .stTextArea > div > textarea {{
        background-color: rgba(0, 0, 0, 0.6);
        color: #FFFFFF;
        border: 1px solid #ccc;
        border-radius: 10px;
    }}
    .css-1v0mbdj, .css-1d391kg, .st-cj {{
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 15px;
        padding: 1em;
    }}
    .css-1cpxqw2, .css-q8sbsg, .css-10trblm {{
        color: white !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==== FUNCIONES ====
def leer_txt(archivo):
    return archivo.getvalue().decode("utf-8")

def leer_docx(archivo):
    doc = docx.Document(archivo)
    return "\n".join([p.text for p in doc.paragraphs])

def resumen_extractivo(texto, num_oraciones=3):
    try:
        parser = PlaintextParser.from_string(texto, SumyTokenizer("english"))
    except LookupError:
        from sumy.nlp.tokenizers import Tokenizer as BaseTokenizer
        class SimpleTokenizer(BaseTokenizer):
            def to_sentences(self, text):
                return text.split(". ")
        parser = PlaintextParser.from_string(texto, SimpleTokenizer("english"))

    resumen = LsaSummarizer()(parser.document, num_oraciones)
    return ' '.join(str(oracion) for oracion in resumen)

def resumen_abstractive(texto, max_input_length=512, max_output_length=150):
    entrada = "summarize: " + texto
    entradas = tokenizador_t5.encode(entrada, return_tensors="pt", max_length=max_input_length, truncation=True)
    salida = modelo_t5.generate(
        entradas,
        max_length=max_output_length,
        min_length=120,
        length_penalty=2.0,
        num_beams=4,
        no_repeat_ngram_size=3,
        early_stopping=True
    )
    return tokenizador_t5.decode(salida[0], skip_special_tokens=True)

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

# ==== INTERFAZ STREAMLIT ====
st.title("📝 Generador Automático de Resúmenes de Texto")
st.write("Introduce un texto largo, carga un archivo, o elige el tipo de resumen que deseas obtener:")

uploaded_file = st.file_uploader("Cargar archivo (.txt o .docx)", type=["txt", "docx"])
texto_largo = st.text_area("O introduce tu texto largo aquí:", height=300)
opcion = st.selectbox("Selecciona el tipo de resumen", ("Resumen Extractivo", "Resumen Abstractive"))

if opcion == "Resumen Extractivo":
    num_oraciones = st.slider("Número de oraciones en el resumen", min_value=1, max_value=30, value=3)
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
                resumen = resumen_extractivo(texto_largo, num_oraciones)
            else:
                resumen = resumen_abstractive(texto_largo, max_output_length=max_palabras)

        st.success("¡Resumen generado exitosamente!")
        st.subheader("📄 Resumen:")
        st.write(resumen)

        st.write(f"📝 El resumen contiene {contar_palabras(resumen)} palabras.")

        # Descargar .txt
        st.download_button("💾 Descargar Resumen (.txt)", resumen.encode("utf-8"), "resumen.txt", "text/plain")

        # Descargar .docx
        word_buffer = crear_word(resumen)
        st.download_button("💾 Descargar Resumen (.docx)", word_buffer, "resumen.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    else:
        st.error("⚠️ Por favor, introduce o carga un texto para generar el resumen.")



