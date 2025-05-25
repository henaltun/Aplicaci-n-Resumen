import streamlit as st
import docx
from io import BytesIO
from docx import Document
import spacy
from collections import Counter

# ================= FUNCIONES =====================
def leer_txt(archivo):
    return archivo.getvalue().decode("utf-8")

def leer_docx(archivo):
    doc = docx.Document(archivo)
    texto = "\n".join([p.text for p in doc.paragraphs])
    return texto

@st.cache_resource
def cargar_spacy():
    return spacy.load("es_core_news_sm")

def resumen_extractivo_spacy(texto, max_oraciones=5):
    nlp = cargar_spacy()
    doc = nlp(texto)

    oraciones = list(doc.sents)
    palabras = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    frecuencia = Counter(palabras)

    puntuaciones = {}
    for oracion in oraciones:
        puntuacion = sum(frecuencia.get(token.text.lower(), 0) for token in oracion if token.is_alpha)
        puntuaciones[oracion] = puntuacion

    oraciones_importantes = sorted(puntuaciones, key=puntuaciones.get, reverse=True)[:max_oraciones]
    oraciones_ordenadas = sorted(oraciones_importantes, key=lambda x: x.start)
    resumen = " ".join([oracion.text for oracion in oraciones_ordenadas])

    return resumen

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

# ================= INTERFAZ =====================
st.title("📝 Generador Automático de Resúmenes en Español (spaCy)")

uploaded_file = st.file_uploader("📤 Cargar archivo (.txt o .docx)", type=["txt", "docx"])
texto_largo = st.text_area("✍️ O escribe o pega tu texto aquí:", height=300)

num_oraciones = st.slider("🔢 Número de oraciones del resumen", min_value=2, max_value=15, value=5)

if st.button("🔍 Generar Resumen"):
    if uploaded_file:
        if uploaded_file.type == "text/plain":
            texto_largo = leer_txt(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            texto_largo = leer_docx(uploaded_file)

    if texto_largo:
        if len(texto_largo) > 10000:
            st.error("⚠️ Texto demasiado largo. Máximo 10,000 caracteres.")
            st.stop()

        with st.spinner("Procesando texto con spaCy..."):
            resumen = resumen_extractivo_spacy(texto_largo, max_oraciones=num_oraciones)

        st.success("✅ ¡Resumen generado!")
        st.subheader("📄 Resumen:")
        st.write(resumen)
        st.write(f"✏️ Palabras en el resumen: **{contar_palabras(resumen)}**")

        st.download_button("💾 Descargar resumen (.txt)", resumen.encode('utf-8'), "resumen.txt", "text/plain")
        st.download_button("💾 Descargar resumen (.docx)", crear_word(resumen), "resumen.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.error("⚠️ Debes ingresar o cargar un texto primero.")


