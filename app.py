import streamlit as st
import google.generativeai as genai
from docx import Document
from PIL import Image
import io

# Configuración de la interfaz
st.set_page_config(page_title="Digitalizador de Informes", page_icon="📄", layout="centered")

st.title("📄 Digitalizador Automático de Informes")
st.write("Sube una o varias fotos del documento para convertirlas a un archivo Word editable.")

# Gestión de la clave API (desde Secrets de Streamlit o entrada manual)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

if not api_key:
    st.info("💡 Por favor, configura la API Key en los Secrets de Streamlit o ingrésala en la barra lateral para continuar.")
    st.stop()

# Configurar el cliente de IA
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Carga de archivos
archivos = st.file_uploader("Selecciona la(s) imagen(es) del papel", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if archivos and st.button("Procesar y Generar Word", type="primary"):
    with st.spinner("Procesando imagen(es) con IA..."):
        doc = Document()
        doc.add_heading("Informe Digitalizado", level=1)
        
        for idx, archivo in enumerate(archivos, start=1):
            img = Image.open(archivo)
            
            prompt = """
            Analiza esta imagen minuciosamente. Transcribe y organiza toda la información visible.
            Usa formato Markdown estructurado:
            - Usa títulos (# o ##) para los encabezados principales o secciones.
            - Usa listas con viñetas (-) para detalles, observaciones o puntos clave.
            - Transcribe fielmente nombres, números, fechas y textos.
            """
            
            try:
                response = model.generate_content([prompt, img])
                
                if len(archivos) > 1:
                    doc.add_heading(f"Documento / Página {idx}", level=2)
                
                # Conversión básica de Markdown a párrafos/encabezados de Word
                lineas = response.text.split('\n')
                for linea in lineas:
                    l = linea.strip()
                    if l.startswith('# '):
                        doc.add_heading(l.replace('# ', ''), level=1)
                    elif l.startswith('## '):
                        doc.add_heading(l.replace('## ', ''), level=2)
                    elif l.startswith('### '):
                        doc.add_heading(l.replace('### ', ''), level=3)
                    elif l.startswith('- ') or l.startswith('* '):
                        doc.add_paragraph(l[2:], style='List Bullet')
                    elif l:
                        doc.add_paragraph(l)
                        
            except Exception as e:
                st.error(f"Error al procesar el archivo {archivo.name}: {e}")

        # Guardar en memoria para descarga
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.success("¡Documento procesado con éxito!")
        st.download_button(
            label="📥 Descargar Documento Word (.docx)",
            data=buffer,
            file_name="Informe_Digitalizado.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )