import streamlit as st
import google.generativeai as genai
from docx import Document
from PIL import Image
import io

# Configuracion de la pagina
st.set_page_config(page_title="Digitalizador de Informes", layout="centered")

st.title("Digitalizador Automatico de Informes")
st.write("Sube una o varias fotos del documento para convertirlas a un archivo Word editable.")

# Gestion de la clave API con sanitizacion (elimina espacios no deseados)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
else:
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password").strip()

if not api_key:
    st.info("Por favor, configura la API Key en los Secrets de Streamlit o ingresala en la barra lateral para continuar.")
    st.stop()

# Configurar cliente y seleccionar modelo ligero activo
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3.5-flash-lite')

# Carga de archivos
archivos = st.file_uploader("Selecciona la(s) imagen(es) del papel", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if archivos and st.button("Procesar y Generar Word", type="primary"):
    doc = Document()
    doc.add_heading("Informe Digitalizado", level=1)
    
    contenido_extraido = False
    total_archivos = len(archivos)
    
    barra_progreso = st.progress(0)
    estado_texto = st.empty()

    for idx, archivo in enumerate(archivos, start=1):
        estado_texto.text(f"Procesando imagen {idx} de {total_archivos}: {archivo.name}")
        
        try:
            # Sanitizacion de la imagen: convertir obligatoriamente a RGB y redimensionar
            img = Image.open(archivo).convert('RGB')
            img.thumbnail((2048, 2048))
            
            prompt = """
            Analiza esta imagen minuciosamente. Transcribe y organiza toda la informacion visible.
            Usa formato Markdown estructurado:
            - Usa titulos (# o ##) para los encabezados principales o secciones.
            - Usa listas con vinetas (-) para detalles, observaciones o puntos clave.
            - Transcribe fielmente nombres, numeros, fechas y textos.
            """
            
            response = model.generate_content([prompt, img])
            
            if response and response.text and response.text.strip():
                contenido_extraido = True
                
                if total_archivos > 1:
                    doc.add_heading(f"Documento / Pagina {idx}", level=2)
                
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
            else:
                st.warning(f"No se pudo obtener texto legible de la imagen: {archivo.name}")

        except Exception as e:
            st.error(f"Error al procesar {archivo.name}: {e}")

        barra_progreso.progress(idx / total_archivos)

    estado_texto.empty()

    if contenido_extraido:
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.success("Documento procesado con exito.")
        st.download_button(
            label="Descargar Documento Word (.docx)",
            data=buffer,
            file_name="Informe_Digitalizado.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        st.error("No se genero el archivo Word porque no se logro procesar ningun contenido.")