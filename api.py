#!/usr/bin/env python3
import requests
import re
import json
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import PyPDF2
import io

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de Telegram
BOT_TOKEN = '7608685164:AAE0WMqRP2s6VrLXNHtWCss0FS0PIxTlVzY'
CHAT_ID = '-4884673739'

# Lista para almacenar logs
debug_logs = []

def add_log(message):
    """Añade un mensaje al registro de logs."""
    timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ')
    log_entry = timestamp + message
    debug_logs.append(log_entry)
    logger.info(message)

def enviar_mensaje_telegram(mensaje):
    """Envía un mensaje a Telegram usando el bot configurado."""
    add_log("Intentando enviar mensaje a Telegram")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': mensaje,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=params)
        if response.status_code == 200:
            add_log("Mensaje enviado a Telegram correctamente")
        else:
            add_log(f"Error enviando mensaje a Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        add_log(f"Error enviando mensaje a Telegram: {str(e)}")

def descargar_pdf(url):
    """Descarga un archivo PDF desde una URL y devuelve su contenido en binario."""
    add_log(f"Intentando descargar PDF desde: {url}")
    try:
        respuesta = requests.get(url)
        respuesta.raise_for_status()
        add_log("PDF descargado exitosamente")
        return respuesta.content
    except Exception as e:
        add_log(f"Error al descargar el PDF: {str(e)}")
        return None

def extraer_texto_pdf(contenido_pdf):
    """Extrae el texto de un archivo PDF en memoria."""
    add_log("Extrayendo texto del PDF")
    try:
        pdf_stream = io.BytesIO(contenido_pdf)
        lector_pdf = PyPDF2.PdfReader(pdf_stream)
        
        texto_completo = ""
        num_paginas = len(lector_pdf.pages)
        add_log(f"El PDF tiene {num_paginas} páginas")
        
        for pagina in range(num_paginas):
            texto_pagina = lector_pdf.pages[pagina].extract_text()
            texto_completo += texto_pagina + "\n\n"
        
        return texto_completo
    except Exception as e:
        add_log(f"Error al extraer texto del PDF: {str(e)}")
        return None

def extraer_valor_factura(texto):
    """Extrae el valor de la factura del texto del PDF."""
    add_log("Buscando valor de la factura en el texto")
    try:
        # Buscar el primer valor monetario con formato $ XXX.XXX
        patron = r'\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)'
        coincidencia = re.search(patron, texto)
        
        if coincidencia:
            valor_factura = coincidencia.group(0)
            add_log(f"Valor de factura encontrado: {valor_factura}")
            return valor_factura.strip()
        else:
            add_log("No se encontró el valor de la factura en el texto")
            return "No se encontró el valor de la factura"
    except Exception as e:
        add_log(f"Error al extraer el valor de la factura: {str(e)}")
        return None

def obtener_color_de_pagina(html):
    """Extrae el color del captcha de la página."""
    add_log("Intentando obtener color de la página")
    
    pattern = r'<div class="pi pi-circle-on text-5xl text-(\w+)-(?:\d+)">\s*<\/div>'
    match = re.search(pattern, html)
    
    if match:
        color_en_ingles = match.group(1)
        add_log(f"Color encontrado: {color_en_ingles}")
        
        colores = {
            'gray': 'Gris',
            'purple': 'Morado',
            'orange': 'Naranja',
            'green': 'Verde',
            'black': 'Negro',
            'pink': 'Rosado',
            'blue': 'Azul',
            'brown': 'Marrón',
            'red': 'Rojo',
            'yellow': 'Amarillo'
        }
        
        return colores.get(color_en_ingles, False)
    
    add_log("No se encontró el patrón del color en el HTML")
    add_log(f"Fragmento de HTML: {html[:500]}...")
    return False

def extraer_datos_tabla(html):
    """Extrae los datos de la tabla de facturas del HTML."""
    add_log(f"HTML recibido (primeros 1000 caracteres): {html[:1000]}")
    
    # Buscar mensajes de error específicos
    error_match = re.search(r'<span class="[^"]*ui-messages-error-summary[^"]*">(.*?)<\/span>', html)
    if error_match:
        add_log(f"Error encontrado en mensajes: {error_match.group(1)}")
    
    # Buscar cualquier div con clase que contenga 'message' o 'error'
    message_match = re.search(r'<div class="[^"]*(?:message|error)[^"]*">(.*?)<\/div>', html)
    if message_match:
        add_log(f"Mensaje encontrado: {message_match.group(1)}")
    
    add_log("Iniciando extracción de datos de la tabla")
    datos = []
    
    # Extraer el contenido CDATA de la respuesta AJAX
    cdata_match = re.search(r'<!\[CDATA\[(.*?)\]\]>', html, re.DOTALL)
    if cdata_match:
        html_content = cdata_match.group(1)
        add_log(f"Contenido CDATA extraído (primeros 200 caracteres): {html_content[:200]}")
    else:
        html_content = html
        add_log("No se encontró contenido CDATA, usando HTML completo")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Buscar filas en la tabla - intentar diferentes selectores
    filas = soup.select('tr[data-ri]')
    if not filas:
        filas = soup.select('table tbody tr')
    if not filas:
        filas = soup.select('.ui-datatable-data tr')
    if not filas:
        # Buscar cualquier tabla y sus filas
        tablas = soup.select('table')
        for tabla in tablas:
            filas = tabla.select('tr')
            if filas and len(filas) > 1:  # Al menos una fila de encabezado y una de datos
                add_log(f"Encontrada tabla con {len(filas)} filas")
                break
    
    add_log(f"Filas encontradas: {len(filas)}")
    
    if not filas:
        # Intentar un enfoque más directo buscando el patrón directamente en el HTML
        add_log("Intentando extraer información directamente del HTML")
        
        # Buscar patrones para nombre/identificación
        nombre_match = re.search(r'<div[^>]*>\s*Cliente:\s*(.*?)\s*<\/div>', html_content, re.DOTALL)
        if nombre_match:
            nombre = nombre_match.group(1).strip()
            add_log(f"Nombre encontrado directamente: {nombre}")
            
            # Buscar otros campos
            identificacion_match = re.search(r'<div[^>]*>\s*Identificación:\s*(.*?)\s*<\/div>', html_content, re.DOTALL)
            identificacion = identificacion_match.group(1).strip() if identificacion_match else ""
            
            periodo_match = re.search(r'<div[^>]*>\s*Periodo:\s*(.*?)\s*<\/div>', html_content, re.DOTALL)
            periodo = periodo_match.group(1).strip() if periodo_match else ""
            
            fecha_match = re.search(r'<div[^>]*>\s*Fecha[^:]*:\s*(.*?)\s*<\/div>', html_content, re.DOTALL)
            fecha_limite_pago = fecha_match.group(1).strip() if fecha_match else ""
            
            # Buscar cualquier URL que pueda ser la factura
            url_match = re.search(r'href="([^"]*\.pdf)"', html_content)
            url_factura = url_match.group(1) if url_match else ""
            
            datos.append({
                'nombre': nombre,
                'identificacion': identificacion,
                'periodo': periodo,
                'fecha_limite_pago': fecha_limite_pago,
                'fecha_limite_suspension': "",
                'url_factura': url_factura
            })
    else:
        for fila in filas:
            celdas = fila.select('td')
            
            if celdas:
                try:
                    # Inicializar variables
                    nombre = ""
                    identificacion = ""
                    periodo = ""
                    fecha_limite_pago = ""
                    fecha_limite_suspension = ""
                    url_factura = ""
                    
                    # Celda 0: Nombre
                    nombre_node = fila.select_one('td:nth-child(1) span.text-center')
                    if nombre_node:
                        nombre = nombre_node.text.strip()
                    elif len(celdas) > 0:
                        nombre = celdas[0].text.strip()
                    
                    # Celda 1: Identificación
                    id_node = fila.select_one('td:nth-child(2) span.text-center')
                    if id_node:
                        identificacion = id_node.text.strip()
                    elif len(celdas) > 1:
                        identificacion = celdas[1].text.strip()
                    
                    # Celda 2: Periodo
                    periodo_node = fila.select_one('td:nth-child(3) span.text-center')
                    if periodo_node:
                        periodo = periodo_node.text.strip()
                    elif len(celdas) > 2:
                        periodo = celdas[2].text.strip()
                    
                    # Celda 3: Fecha límite de pago
                    fecha_pago_node = fila.select_one('td:nth-child(4) span.text-center')
                    if fecha_pago_node:
                        fecha_limite_pago = fecha_pago_node.text.strip()
                    elif len(celdas) > 3:
                        fecha_limite_pago = celdas[3].text.strip()
                    
                    # Celda 5: Fecha límite para suspensión
                    if len(celdas) > 5:
                        fecha_limite_suspension = celdas[5].text.strip()
                    
                    # Celda 6: Link de la factura
                    link_node = celdas[6].select_one('a') if len(celdas) > 6 else None
                    if link_node and link_node.has_attr('href'):
                        url_factura = link_node['href']
                    else:
                        # Buscar en toda la fila
                        link_node = fila.select_one('a')
                        if link_node and link_node.has_attr('href'):
                            url_factura = link_node['href']
                    
                    # Agregar datos a la lista (sin incluir el valor)
                    datos.append({
                        'nombre': nombre,
                        'identificacion': identificacion,
                        'periodo': periodo,
                        'fecha_limite_pago': fecha_limite_pago,
                        'fecha_limite_suspension': fecha_limite_suspension,
                        'url_factura': url_factura
                    })
                except Exception as e:
                    add_log(f"Error procesando fila: {str(e)}")
    
    # Si no se encontraron datos con los métodos anteriores, buscar cualquier información útil
    if not datos:
        add_log("No se encontraron datos estructurados, intentando encontrar información básica")
        
        # Buscar el NIC en el HTML (generalmente está presente)
        nic_match = re.search(r'NIC:\s*(\d+)', html_content)
        if nic_match:
            nic = nic_match.group(1)
            add_log(f"NIC encontrado: {nic}")
            
            # Buscar cualquier otra información que pueda ser útil
            client_info = soup.select('.text-center.p-2')
            info_text = ' '.join([el.text.strip() for el in client_info])
            add_log(f"Información encontrada: {info_text}")
            
            # Intentar extraer datos de texto no estructurado
            datos.append({
                'nombre': info_text[:30] if info_text else "Cliente",
                'identificacion': nic,
                'periodo': "Periodo actual",
                'fecha_limite_pago': "",
                'fecha_limite_suspension': "",
                'url_factura': ""
            })
    
    add_log(f"Datos extraídos: {json.dumps(datos)}")
    return datos

def consultar_factura(nic, intentos=0, ip='Desconocida'):
    """Consulta la factura para un NIC específico."""
    global debug_logs
    tiempo_inicio = time.time()
    add_log(f"Iniciando consulta para NIC: {nic} (intento: {intentos}) desde IP: {ip}")
    
    if intentos >= 3:
        add_log(f"Máximo de intentos alcanzado para NIC: {nic}")
        tiempo_fin = time.time()
        tiempo_ejecucion = round(tiempo_fin - tiempo_inicio, 2)
        return {
            'error': 'No se pudo obtener la información después de 3 intentos',
            'tiempo_ejecucion': tiempo_ejecucion,
            'debug_logs': debug_logs
        }

    url = 'https://afinia.docuplanet.co/'
    
    # Encabezados HTTP con la IP del cliente
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-419,es;q=0.9',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'X-Forwarded-For': ip,
        'Client-IP': ip,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }
    
    # Crear una sesión para mantener cookies
    session = requests.Session()
    
    try:
        # Primera petición para obtener la página inicial
        response = session.get(url, headers=headers, verify=False, timeout=10)
        html = response.text
        
        # Obtener el color del captcha
        color = obtener_color_de_pagina(html)
        if not color:
            add_log("No se pudo obtener el color de la página")
            return consultar_factura(nic, intentos + 1, ip)
        
        # Obtener el ViewState
        viewstate_match = re.search(r'name="jakarta\.faces\.ViewState" id=".*?" value="(.*?)"', html)
        if not viewstate_match:
            add_log("No se pudo obtener ViewState")
            return consultar_factura(nic, intentos + 1, ip)
        
        viewstate = viewstate_match.group(1)
        add_log(f"ViewState obtenido: {viewstate[:50]}...")
        
        # Buscar el ID del botón en el HTML
        button_match = re.search(r'button[^>]+id="(form:j_idt\d+)"', html)
        if not button_match:
            add_log("No se pudo encontrar el ID del botón")
            return consultar_factura(nic, intentos + 1, ip)
        
        button_id = button_match.group(1)
        add_log(f"ID del botón encontrado: {button_id}")
        
        # Preparar datos para la segunda petición
        post_data = {
            'jakarta.faces.partial.ajax': 'true',
            'jakarta.faces.source': button_id,
            'jakarta.faces.partial.execute': '@all',
            'jakarta.faces.partial.render': 'form',
            button_id: button_id,
            'form': 'form',
            'form:account': nic,
            'form:color_input': color,
            'jakarta.faces.ViewState': viewstate
        }
        
        add_log("Post data preparada")
        
        # Encabezados para la segunda petición
        headers_post = {
            'Accept': 'application/xml, text/xml, */*',
            'Accept-Language': 'es-419,es;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Faces-Request': 'partial/ajax',
            'Origin': url.rstrip('/'),
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'X-Forwarded-For': ip,
            'Client-IP': ip,
        }
        
        # Segunda petición para obtener los datos
        response = session.post(url, data=post_data, headers=headers_post, verify=False, timeout=15)
        
        add_log(f"Código de respuesta HTTP: {response.status_code}")
        
        # Procesar respuesta
        if response.text:
            datos = extraer_datos_tabla(response.text)
            if datos:
                add_log("Datos obtenidos exitosamente")
                
                # Si hay facturas, intentar obtener el valor de la primera
                primera_factura = None
                if datos and len(datos) > 0:
                    primera_factura = datos[0]
                    if 'url_factura' in primera_factura and primera_factura['url_factura']:
                        url_factura = primera_factura['url_factura']
                        add_log(f"URL de factura encontrada: {url_factura}")
                        
                        # Descargar PDF y extraer valor
                        contenido_pdf = descargar_pdf(url_factura)
                        if contenido_pdf:
                            texto_pdf = extraer_texto_pdf(contenido_pdf)
                            if texto_pdf:
                                valor_factura = extraer_valor_factura(texto_pdf)
                                # Agregar el valor a la primera factura
                                primera_factura['valor_factura'] = valor_factura
                            else:
                                primera_factura['valor_factura'] = "No se pudo extraer texto del PDF"
                        else:
                            primera_factura['valor_factura'] = "No se pudo descargar el PDF"
                
                tiempo_fin = time.time()
                tiempo_ejecucion = round(tiempo_fin - tiempo_inicio, 2)
                return {
                    'success': True,
                    'nic': nic,
                    'factura': primera_factura if primera_factura else None,
                    'tiempo_ejecucion': tiempo_ejecucion,
                    'debug_logs': debug_logs
                }
            else:
                # Verificar si hay un mensaje que indica "no hay facturas" o similar
                if re.search(r'no hay facturas|no se encontraron resultados|sin resultados', response.text, re.IGNORECASE):
                    add_log("No hay facturas pendientes para este NIC")
                    tiempo_fin = time.time()
                    tiempo_ejecucion = round(tiempo_fin - tiempo_inicio, 2)
                    return {
                        'success': True,
                        'nic': nic,
                        'factura': None,
                        'mensaje': 'No hay facturas pendientes para este NIC',
                        'tiempo_ejecucion': tiempo_ejecucion,
                        'debug_logs': debug_logs
                    }
                
                if 'error' in response.text.lower():
                    error_match = re.search(r'<div class="ui-message-error-detail">(.*?)<\/div>', response.text)
                    error = error_match.group(1) if error_match else 'Error desconocido'
                    add_log(f"Error encontrado en respuesta: {error}")
                    if error == 'Error desconocido':
                        time.sleep(1)
                        return consultar_factura(nic, intentos + 1, ip)
                    tiempo_fin = time.time()
                    tiempo_ejecucion = round(tiempo_fin - tiempo_inicio, 2)
                    return {
                        'error': error,
                        'tiempo_ejecucion': tiempo_ejecucion,
                        'debug_logs': debug_logs
                    }
                    
                # Si llegamos aquí, es posible que la respuesta sea exitosa pero con formato diferente
                # Intentar extraer información básica
                nic_match = re.search(r'NIC:\s*(\d+)', response.text)
                if nic_match and nic_match.group(1) == nic:
                    add_log("Se encontró información del NIC pero sin facturas estructuradas")
                    tiempo_fin = time.time()
                    tiempo_ejecucion = round(tiempo_fin - tiempo_inicio, 2)
                    return {
                        'success': True,
                        'nic': nic,
                        'factura': None,
                        'mensaje': 'Se encontró el NIC pero no hay información de facturas disponible',
                        'tiempo_ejecucion': tiempo_ejecucion,
                        'html_respuesta': response.text[:1000],  # Incluir parte de la respuesta para debug
                        'debug_logs': debug_logs
                    }
                    
                add_log("No se encontraron datos ni mensajes de error")
                add_log(f"Fragmento de respuesta: {response.text[:500]}...")
                time.sleep(1)
                return consultar_factura(nic, intentos + 1, ip)
        
        add_log("No se obtuvo respuesta")
        time.sleep(1)
        return consultar_factura(nic, intentos + 1, ip)
        
    except requests.exceptions.Timeout:
        add_log("Tiempo de espera agotado en la petición")
        time.sleep(2)  # Esperar más tiempo en caso de timeout
        return consultar_factura(nic, intentos + 1, ip)
    except requests.exceptions.ConnectionError:
        add_log("Error de conexión al servidor")
        time.sleep(2)
        return consultar_factura(nic, intentos + 1, ip)
    except Exception as e:
        add_log(f"Error en la petición: {str(e)}")
        time.sleep(1)
        return consultar_factura(nic, intentos + 1, ip)

def main():
    """Función principal que maneja la consulta desde API web."""
    from flask import Flask, request, jsonify
    import urllib3
    import os
    
    # Desactivar advertencias de certificados SSL no verificados
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return jsonify({
            'status': 'online',
            'message': 'API de consulta de facturas Afinia',
            'uso': '/api?nic=NUMERO_NIC'
        })
    
    @app.route('/api')
    def api():
        global debug_logs
        debug_logs = []  # Reiniciar logs para cada consulta
        
        nic = request.args.get('nic')
        ip = request.args.get('ip', request.remote_addr)
        
        if not nic:
            return jsonify({
                'error': 'Por favor proporcione un NIC en la URL. Ejemplo: ?nic=7998567',
                'debug_logs': debug_logs
            })
        
        add_log(f"Iniciando consulta para NIC: {nic} desde IP: {ip}")
        resultado = consultar_factura(nic, 0, ip)
        
        # Enviar mensaje a Telegram si la consulta fue exitosa
        if resultado.get('success') and resultado.get('factura'):
            factura = resultado['factura']  # Tomamos la factura más reciente
            
            # Obtener nombre del cliente
            nombre = factura['nombre'] if 'nombre' in factura else factura['periodo']
            
            # Crear mensaje para Telegram
            mensaje = "<b>🔔 CONSULTA AFINIA</b>\n\n"
            mensaje += f"<b>Cliente:</b> {nombre}\n"
            mensaje += f"<b>NIC:</b> {resultado['nic']}\n"
            mensaje += f"<b>Fecha de vencimiento:</b> {factura['fecha_limite_pago']}\n"
            
            # Agregar valor de la factura si está disponible
            if 'valor_factura' in factura:
                mensaje += f"<b>Valor:</b> {factura['valor_factura']}\n"
                
            mensaje += f"<b>IP del usuario:</b> {ip}\n"
            mensaje += f"<b>Link factura:</b> {factura['url_factura']}"
            
            # Enviar mensaje a Telegram
            enviar_mensaje_telegram(mensaje)
        
        return jsonify(resultado)
    
    # Si se ejecuta como script, iniciar el servidor
    if __name__ == '__main__':
        # Obtener puerto del entorno (Heroku) o usar 5000 por defecto
        port = int(os.environ.get('PORT', 5000))
        # Host '0.0.0.0' para aceptar conexiones externas
        app.run(host='0.0.0.0', port=port, debug=False)
    
    return app

# Si se ejecuta como script, iniciar el servidor
if __name__ == '__main__':
    main()
else:
    # Para WSGI servers (Gunicorn)
    app = main()