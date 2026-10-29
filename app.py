import io
import google.generativeai as genai
from docx import Document
from PIL import Image
import streamlit as st

# Configuración de la interfaz
st.set_page_config(page_title="Digitalizador de Informes", layout="centered")

st.title("Digitalizador Automático de Informes")
st.write(
    "Sube una o varias fotos del documento para convertirlas a un archivo Word"
    " editable."
)

# Gestión de la clave API
if "GEMINI_API_KEY" in st.secrets:
  api_key = st.secrets["GEMINI_API_KEY"]
else:
  api_key = st.sidebar.text_input(
      "Ingresa tu Gemini API Key:", type="password"
  )

if not api_key:
  st.info(
      "Por favor, configura la API Key en los Secrets de Streamlit o ingrésala"
      " en la barra lateral para continuar."
  )
  st.stop()

# Configurar el cliente de IA (Se ajusta a gemini-1.5-flash)
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Carga de archivos
archivos = st.file_uploader(
    "Selecciona la(s) imagen(es) del papel",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True,
)

if archivos and st.button("Procesar y Generar Word", type="primary"):
  with st.spinner("Procesando imagen(es) con IA..."):
    doc = Document()
    doc.add_heading("Informe Digitalizado", level=1)

    contenido_extraido = False

    # Instrucción para el modelo de visión
    prompt = (
        "Transcripción exacta de esta imagen. Mantiene la estructura,"
        " encabezados, párrafos y listas. No añadas introducciones ni"
        " comentarios adicionales, solo devuelve el texto digitalizado."
    )

    for idx, archivo in enumerate(archivos, start=1):
      try:
        # Abrir la imagen con Pillow
        imagen = Image.open(archivo)

        # Enviar la imagen y el prompt a Gemini
        response = model.generate_content([prompt, imagen])

        # Si hay múltiples imágenes, agrega una sección por página
        if len(archivos) > 1:
          doc.add_heading(f"Página / Imagen {idx}", level=2)

        # Agregar el texto transcrito al documento Word
        doc.add_paragraph(response.text)
        contenido_extraido = True

      except Exception as e:
        st.error(f"Error procesando la imagen '{archivo.name}': {e}")

    if contenido_extraido:
      # Guardar el documento .docx en memoria
      buffer = io.BytesIO()
      doc.save(buffer)
      buffer.seek(0)

      st.success("¡Procesamiento completado con éxito!")

      # Botón para descargar el archivo .docx
      st.download_button(
          label="📥 Descargar documento Word (.docx)",
          data=buffer,
          file_name="Informe_Digitalizado.docx",
          mime=(
              "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          ),
      )