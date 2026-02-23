import os
import io
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = r'c:\Users\Tuchi\MiEstudioIA\credenciales_drive.json'
TARGET_FOLDER_ID = '1lfXtA5yuKc1ZkwZxAgN35PEUN4K0tRlJ'  # ID for 'Proyecto FCI Cater'
LOCAL_INPUT_DIR = r'c:\Users\Tuchi\MiEstudioIA\FCI\Input'

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def authenticate():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return creds
    except Exception as e:
        logging.error(f"Error autenticando: {e}")
        return None

def list_files(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    # Only pull files (skip nested folders for now)
    query += " and mimeType != 'application/vnd.google-apps.folder'"
    
    try:
        results = service.files().list(q=query, fields="files(id, name, mimeType, md5Checksum)").execute()
        return results.get('files', [])
    except Exception as e:
        logging.error(f"Error listando archivos: {e}")
        return []

def download_file(service, file_id, file_name, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        
    file_path = os.path.join(destination_folder, file_name)
    
    # Basic sync check: if file already exists with same name, skip it
    if os.path.exists(file_path):
        logging.info(f"Omitiendo '{file_name}' (El archivo ya existe localmente)")
        return False
        
    logging.info(f"Descargando: {file_name}...")
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        logging.info(f"✅ Descarga completa: {file_name}")
        return True
    except Exception as e:
        logging.error(f"Error descargando {file_name}: {e}")
        # Clean up partial file if failed
        fh.close()
        if os.path.exists(file_path):
            os.remove(file_path)
        return False

def sync_drive_to_local():
    logging.info("Iniciando sincronizacion con Google Drive...")
    creds = authenticate()
    if not creds:
        return
        
    service = build('drive', 'v3', credentials=creds)
    
    files = list_files(service, TARGET_FOLDER_ID)
    if not files:
        logging.info("No se encontraron archivos en la carpeta de Drive.")
        return
        
    logging.info(f"Se encontraron {len(files)} archivos en Drive.")
    
    downloaded_count = 0
    for f in files:
        if download_file(service, f['id'], f['name'], LOCAL_INPUT_DIR):
            downloaded_count += 1
            
    logging.info(f"Sincronizacion terminada. Se descargaron {downloaded_count} archivos nuevos.")

if __name__ == '__main__':
    sync_drive_to_local()
