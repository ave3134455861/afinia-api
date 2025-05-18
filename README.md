# API de Consulta de Facturas Afinia

API para consultar facturas de Afinia y obtener su valor.

## Funcionalidades

- Consulta de facturas por NIC
- Extracción automática del valor de la factura desde PDF
- Notificación de consultas vía Telegram
- Medición del tiempo de ejecución

## Despliegue en Heroku

### Requisitos previos

- Cuenta en [Heroku](https://heroku.com)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalada
- Git instalado

### Pasos para desplegar

1. Clonar este repositorio:
   ```
   git clone <url-del-repositorio>
   cd <nombre-del-directorio>
   ```

2. Iniciar sesión en Heroku:
   ```
   heroku login
   ```

3. Crear una nueva aplicación en Heroku:
   ```
   heroku create nombre-de-tu-app
   ```

4. Enviar el código a Heroku:
   ```
   git push heroku main
   ```

5. Verificar que la aplicación está funcionando:
   ```
   heroku open
   ```

### Variables de entorno

Si necesitas configurar variables de entorno (para tokens, etc.), puedes hacerlo con:
```
heroku config:set BOT_TOKEN=tu_token_de_telegram
heroku config:set CHAT_ID=tu_chat_id_de_telegram
```

## Uso local

1. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

2. Ejecutar la aplicación:
   ```
   python api.py
   ```

3. La API estará disponible en `http://localhost:5000/api?nic=NUMERO_NIC`

## Endpoints

- `GET /`: Verifica si la API está en funcionamiento
- `GET /api?nic={NIC}`: Consulta información de factura por NIC

## Respuesta de ejemplo

```json
{
  "success": true,
  "nic": "7753905",
  "factura": {
    "nombre": "AHUMEDO BLANCO MARIA DEL PILAR",
    "identificacion": "2025-05",
    "periodo": "08/05/2025",
    "fecha_limite_pago": "21/05/2025",
    "url_factura": "https://dp-afinia.s3.us-east-1.amazonaws.com/08052025REGUBOL/Regulado_7753905120_08052025.pdf",
    "valor_factura": "$ 221.030"
  },
  "tiempo_ejecucion": 4.48
}
``` 
