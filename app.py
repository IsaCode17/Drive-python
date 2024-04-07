from flask import Flask, redirect, url_for, session, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
from googleapiclient.discovery import build
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave secreta para la sesión

# Configuración de la API de Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

# ID del cliente OAuth 2.0 (obtenido desde Google Cloud Console)
CLIENT_ID = 'tu-client-id.apps.googleusercontent.com'


@app.route('/')
def index():
    if 'google_token' in session:
        return 'Estás autenticado con Google. <a href="/upload">Subir archivo</a>'
    else:
        return 'Por favor, <a href="/login">inicia sesión con Google</a> para continuar.'


@app.route('/login')
def login():
    # Redirecciona al servicio de autenticación de Google
    redirect_uri = url_for('auth', _external=True)
    return redirect(f'https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={CLIENT_ID}&redirect_uri={redirect_uri}&scope=openid%20profile%20email')


@app.route('/auth')
def auth():
    # Procesa la respuesta de autenticación
    code = request.args.get('code')
    token_response = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': 'tu-client-secret',
        'redirect_uri': url_for('auth', _external=True),
        'grant_type': 'authorization_code'
    })

    # Guarda el token de acceso en la sesión
    session['google_token'] = token_response.json()['id_token']
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'google_token' in session:
        if request.method == 'POST':
            file_url = request.form['file_url']
            file_name = request.form['file_name']

            # Validar y obtener el token de acceso
            try:
                id_info = id_token.verify_oauth2_token(session['google_token'], requests.Request(), CLIENT_ID)
                access_token = id_info['sub']
            except Exception as e:
                return jsonify({'error': str(e)}), 401

            # Inicializar el cliente de Google Drive
            drive_service = build(API_SERVICE_NAME, API_VERSION, credentials=access_token)

            # Crear metadatos del archivo
            file_metadata = {
                'name': file_name
            }

            # Subir el archivo desde la URL
            file = drive_service.files().create(body=file_metadata, media_body=file_url).execute()

            return f'Archivo "{file_name}" subido correctamente a Google Drive.'

        return '''
            <form method="POST">
                <label>URL del archivo:</label>
                <input type="text" name="file_url"><br>
                <label>Nombre del archivo en Drive:</label>
                <input type="text" name="file_name"><br>
                <input type="submit" value="Subir">
            </form>
        '''
    else:
        return 'Por favor, <a href="/login">inicia sesión con Google</a> para continuar.'


if __name__ == '__main__':
    app.run(debug=True)
