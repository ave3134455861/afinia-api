import requests
import PyPDF2
import io
import os
import re

def descargar_pdf(url, nombre_archivo):
    """
    Descarga un archivo PDF desde una URL
    """
    try:
        respuesta = requests.get(url)
        respuesta.raise_for_status()  # Verifica si hubo errores en la descarga
        
        # Guardar el PDF descargado
        with open(nombre_archivo, 'wb') as archivo:
            archivo.write(respuesta.content)
            
        print(f"Archivo descargado exitosamente como {nombre_archivo}")
        return True
    except Exception as e:
        print(f"Error al descargar el archivo: {e}")
        return False

def extraer_texto_pdf(nombre_archivo):
    """
    Extrae el texto de un archivo PDF
    """
    try:
        texto_completo = ""
        
        # Abrir el archivo PDF
        with open(nombre_archivo, 'rb') as archivo:
            lector_pdf = PyPDF2.PdfReader(archivo)
            
            # Obtener el número de páginas
            num_paginas = len(lector_pdf.pages)
            print(f"El PDF tiene {num_paginas} páginas")
            
            # Extraer texto de cada página
            for pagina in range(num_paginas):
                texto_pagina = lector_pdf.pages[pagina].extract_text()
                texto_completo += texto_pagina + "\n\n"
        
        return texto_completo
    except Exception as e:
        print(f"Error al extraer texto del PDF: {e}")
        return None

def extraer_valor_factura(texto):
    """
    Extrae el valor de la factura del texto del PDF
    """
    try:
        # Buscar el primer valor monetario con formato $ XXX.XXX
        patron = r'\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)'
        coincidencia = re.search(patron, texto)
        
        if coincidencia:
            valor_factura = coincidencia.group(0)
            return valor_factura.strip()
        else:
            return "No se encontró el valor de la factura"
    except Exception as e:
        print(f"Error al extraer el valor de la factura: {e}")
        return None

def main():
    # URL del PDF
    url = "https://dp-afinia.s3.us-east-1.amazonaws.com/24112024REGULADO/Regulado_7753900113_24112024.pdf"
    
    # Nombre del archivo a guardar
    nombre_pdf = "Regulado_7753900113_24112024.pdf"
    
    # Descargar el PDF
    if descargar_pdf(url, nombre_pdf):
        # Extraer el texto
        texto = extraer_texto_pdf(nombre_pdf)
        
        if texto:
            # Extraer el valor de la factura
            valor_factura = extraer_valor_factura(texto)
            
            # Mostrar el valor de la factura
            print("\nValor de la factura:")
            print(valor_factura)
            
            # Opcionalmente eliminar el archivo PDF descargado
            # os.remove(nombre_pdf)

if __name__ == "__main__":
    main()