import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = r'c:\Users\Tuchi\MiEstudioIA\credenciales_drive.json'

def authenticate():
    print("Autenticando con Google Drive...")
    creds = None
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return creds
    except Exception as e:
        print(f"Error autenticando: {e}")
        return None

def search_folder(service, folder_name, parent_id=None):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
         query += f" and '{parent_id}' in parents"
    
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    return items

def list_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    # Get all files and folders inside
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get('files', [])

def main():
    creds = authenticate()
    if not creds:
        return
        
    service = build('drive', 'v3', credentials=creds)
    print("Conexion exitosa.")
    
    # 1. Look for MiEstudioIA
    print("\nBuscando carpeta 'MiEstudioIA'...")
    miestudio = search_folder(service, 'MiEstudioIA')
    
    if not miestudio:
        print("[ERROR] No se encontro la carpeta 'MiEstudioIA'.")
        print("IMPORTANTE: Debes compartir la carpeta 'MiEstudioIA' desde tu Google Drive con el correo:")
        print("bot-drive@procesamiento-compras.iam.gserviceaccount.com")
        print("Dale permisos de Editor/Lector.")
        return
        
    miestudio_id = miestudio[0]['id']
    print(f"[OK] Encontrado 'MiEstudioIA' (ID: {miestudio_id})")
    
    # 2. Look for Proyecto FCI Cater inside MiEstudioIA
    print("\nBuscando carpeta 'Proyecto FCI Cater' dentro de 'MiEstudioIA'...")
    proyecto = search_folder(service, 'Proyecto FCI Cater', parent_id=miestudio_id)
    
    if not proyecto:
        print("[ERROR] No se encontro 'Proyecto FCI Cater' dentro de 'MiEstudioIA'.")
        # Let's list what *is* inside MiEstudioIA to see if there's a typo
        contents = list_files_in_folder(service, miestudio_id)
        if contents:
            print("Contenido encontrado en 'MiEstudioIA':")
            for item in contents:
                tipo = "Carpeta" if item['mimeType'] == 'application/vnd.google-apps.folder' else "Archivo"
                print(f"  - [{tipo}] {item['name']}")
        return
        
    proyecto_id = proyecto[0]['id']
    print(f"[OK] Encontrado 'Proyecto FCI Cater' (ID: {proyecto_id})")
    
    # List contents of Proyecto FCI Cater
    print("\nContenido de 'Proyecto FCI Cater':")
    contents = list_files_in_folder(service, proyecto_id)
    if not contents:
        print("  (Carpeta vacia)")
    else:
        for item in contents:
            tipo = "Carpeta" if item['mimeType'] == 'application/vnd.google-apps.folder' else "Archivo"
            print(f"  - [{tipo}] {item['name']}")

if __name__ == '__main__':
    main()
