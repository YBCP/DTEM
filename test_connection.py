"""Script de diagnostico para conexion a Google Sheets"""
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

print("=" * 60)
print("DIAGNOSTICO DE CONEXION A GOOGLE SHEETS")
print("=" * 60)

# 1. Verificar archivos
print("\n1. Verificando archivos de configuracion...")
if os.path.exists('credentials.json'):
    print("   OK credentials.json encontrado")
    with open('credentials.json', 'r') as f:
        creds_data = json.load(f)
        print(f"   Email: {creds_data.get('client_email')}")
else:
    print("   ERROR credentials.json NO encontrado")
    exit(1)

if os.path.exists('config.json'):
    print("   OK config.json encontrado")
    with open('config.json', 'r') as f:
        config = json.load(f)
        spreadsheet_id = config.get('spreadsheet_id')
        print(f"   Spreadsheet ID: {spreadsheet_id}")
else:
    print("   ERROR config.json NO encontrado")
    exit(1)

# 2. Crear credenciales
print("\n2. Creando credenciales...")
try:
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    print("   OK Credenciales creadas")
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# 3. Conectar con Google Sheets
print("\n3. Conectando con Google Sheets API...")
try:
    service = build('sheets', 'v4', credentials=credentials)
    print("   OK Servicio creado")
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# 4. Obtener informacion del spreadsheet
print("\n4. Obteniendo informacion del spreadsheet...")
try:
    metadata = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()

    title = metadata.get('properties', {}).get('title', 'Sin titulo')
    print(f"   OK Spreadsheet encontrado: {title}")

    # Listar hojas
    print("\n5. Hojas disponibles:")
    sheets = metadata.get('sheets', [])
    for sheet in sheets:
        sheet_name = sheet.get('properties', {}).get('title')
        print(f"   - {sheet_name}")

    # Verificar hojas requeridas
    print("\n6. Verificando hojas requeridas...")
    sheet_names = [s.get('properties', {}).get('title') for s in sheets]

    if 'Registros' in sheet_names:
        print("   OK Hoja 'Registros' encontrada")
    else:
        print("   ERROR Hoja 'Registros' NO encontrada")
        print("   SOLUCION: Crea una hoja llamada 'Registros' en tu spreadsheet")

    if 'Metas' in sheet_names:
        print("   OK Hoja 'Metas' encontrada")
    else:
        print("   ERROR Hoja 'Metas' NO encontrada")
        print("   SOLUCION: Crea una hoja llamada 'Metas' en tu spreadsheet")

    # Leer datos de Registros
    if 'Registros' in sheet_names:
        print("\n7. Leyendo hoja 'Registros'...")
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Registros'
            ).execute()

            values = result.get('values', [])
            print(f"   OK {len(values)} filas encontradas")

            if values:
                print(f"   Primera fila (headers): {values[0][:5] if len(values[0]) >= 5 else values[0]}")
            else:
                print("   ADVERTENCIA: La hoja 'Registros' esta vacia")

        except Exception as e:
            print(f"   ERROR leyendo Registros: {e}")

    print("\n" + "=" * 60)
    print("DIAGNOSTICO COMPLETADO")
    print("=" * 60)

except Exception as e:
    error_msg = str(e)
    print(f"   ERROR: {error_msg}")

    if '404' in error_msg:
        print("\n   PROBLEMA: Spreadsheet no encontrado")
        print("   SOLUCION: Verifica el spreadsheet_id en config.json")
        print(f"   URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    elif '403' in error_msg or 'PERMISSION_DENIED' in error_msg:
        print("\n   PROBLEMA: Sin permisos de acceso")
        print("   SOLUCION: Comparte el spreadsheet con:")
        print(f"   {creds_data.get('client_email')}")
        print("   Permisos: Editor")
        print(f"   URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")

    print("\n" + "=" * 60)
    exit(1)
