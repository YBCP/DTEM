import streamlit as st
import pandas as pd
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
from datetime import datetime

class GoogleSheetsManager:
    def __init__(self):
        self.service = None
        self.spreadsheet_id = None
        self.conectar()
    
    def conectar(self):
        """Establece conexión con Google Sheets API"""
        try:
            # Método 1: Desde st.secrets (recomendado para Streamlit Cloud)
            if 'google_sheets' in st.secrets:
                credentials_dict = dict(st.secrets['google_sheets'])
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.spreadsheet_id = st.secrets['google_sheets']['spreadsheet_id']
            
            # Método 2: Desde archivo JSON local (para desarrollo local)
            elif os.path.exists('credentials.json'):
                credentials = service_account.Credentials.from_service_account_file(
                    'credentials.json',
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                # Buscar spreadsheet_id en config.json o como variable de entorno
                if os.path.exists('config.json'):
                    with open('config.json', 'r') as f:
                        config = json.load(f)
                        self.spreadsheet_id = config.get('spreadsheet_id')
                else:
                    self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
            
            # Método 3: Desde variables de entorno
            else:
                credentials_info = {
                    "type": os.getenv('GOOGLE_TYPE'),
                    "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                    "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
                    "private_key": os.getenv('GOOGLE_PRIVATE_KEY', '').replace('\\n', '\n'),
                    "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL')
                }
                
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
            
            # Construir el servicio
            self.service = build('sheets', 'v4', credentials=credentials)
            
            if not self.spreadsheet_id:
                raise ValueError("No se encontró SPREADSHEET_ID en la configuración")
                
            # Verificar conexión
            self.verificar_conexion()
            
        except Exception as e:
            st.error(f"Error al conectar con Google Sheets: {str(e)}")
            st.error("Por favor, verifica la configuración de credenciales.")
            raise e
    
    def verificar_conexion(self):
        """Verifica que la conexión funcione correctamente"""
        try:
            # Intentar obtener metadatos del spreadsheet
            metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            st.success(f"✅ Conectado exitosamente a: {metadata.get('properties', {}).get('title', 'Google Sheet')}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                st.error("❌ Spreadsheet no encontrado. Verifica el SPREADSHEET_ID.")
            elif e.resp.status == 403:
                st.error("❌ Sin permisos. Verifica que el service account tenga acceso al spreadsheet.")
            else:
                st.error(f"❌ Error HTTP {e.resp.status}: {e}")
            return False
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")
            return False
    
    def leer_hoja(self, nombre_hoja="Registros", rango=None):
        """Lee datos de una hoja específica"""
        try:
            if rango:
                range_name = f"{nombre_hoja}!{rango}"
            else:
                range_name = nombre_hoja
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueRenderOption='UNFORMATTED_VALUE',
                dateTimeRenderOption='FORMATTED_STRING'
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                st.warning(f"La hoja '{nombre_hoja}' está vacía.")
                return pd.DataFrame()
            
            # Convertir a DataFrame
            if len(values) > 1:
                headers = values[0]
                data = values[1:]
                
                # Asegurar que todas las filas tengan el mismo número de columnas
                max_cols = len(headers)
                data_normalized = []
                for row in data:
                    # Extender filas cortas con valores vacíos
                    if len(row) < max_cols:
                        row.extend([''] * (max_cols - len(row)))
                    # Truncar filas largas
                    elif len(row) > max_cols:
                        row = row[:max_cols]
                    data_normalized.append(row)
                
                df = pd.DataFrame(data_normalized, columns=headers)
                
                # Limpiar valores None y convertir a string
                df = df.fillna('')
                df = df.astype(str)
                
                # Limpiar valores que sean 'None' como string
                df = df.replace('None', '')
                
                return df
            else:
                # Solo headers, sin datos
                return pd.DataFrame(columns=values[0])
                
        except HttpError as e:
            if e.resp.status == 400:
                st.error(f"❌ Rango inválido o hoja '{nombre_hoja}' no existe.")
            else:
                st.error(f"❌ Error al leer Google Sheets: {e}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"❌ Error inesperado al leer datos: {str(e)}")
            return pd.DataFrame()
    
    def escribir_hoja(self, df, nombre_hoja="Registros", limpiar_hoja=True):
        """Escribe un DataFrame completo a una hoja"""
        try:
            # Preparar datos para Google Sheets
            # Convertir DataFrame a lista de listas
            if df.empty:
                values = [df.columns.tolist()]  # Solo headers
            else:
                # Reemplazar NaN y None con cadenas vacías
                df_clean = df.fillna('')
                df_clean = df_clean.astype(str)
                df_clean = df_clean.replace('nan', '')
                df_clean = df_clean.replace('None', '')
                
                values = [df_clean.columns.tolist()] + df_clean.values.tolist()
            
            # Limpiar la hoja si se solicita
            # Limpiar la hoja si se solicita Y es la hoja Registros
            if limpiar_hoja and nombre_hoja == "Registros":
                self.limpiar_hoja(nombre_hoja)
            elif limpiar_hoja and nombre_hoja != "Registros":
                st.error(f"🚨 BLOQUEADO: Intento de limpiar hoja '{nombre_hoja}' - Solo se permite limpiar 'Registros'")
                return False
            
            # Escribir datos
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{nombre_hoja}!A1",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            rows_updated = result.get('updatedRows', 0)
            st.success(f"✅ {rows_updated} filas actualizadas en '{nombre_hoja}'")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error al escribir en Google Sheets: {str(e)}")
            return False
    
    def actualizar_fila(self, df, numero_fila, nombre_hoja="Registros"):
        """Actualiza una fila específica (número_fila empezando desde 1 para headers)"""
        try:
            if numero_fila < 2:  # Fila 1 son los headers
                st.error("No se puede actualizar la fila de headers")
                return False
            
            # Preparar datos de la fila
            fila_datos = df.iloc[numero_fila - 2].fillna('').astype(str).tolist()  # -2 porque fila 2 = índice 0
            
            # Reemplazar valores problemáticos
            fila_datos = [str(val).replace('nan', '').replace('None', '') for val in fila_datos]
            
            rango = f"{nombre_hoja}!A{numero_fila}:{self._get_column_letter(len(fila_datos))}{numero_fila}"
            
            body = {
                'values': [fila_datos]
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=rango,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error al actualizar fila: {str(e)}")
            return False
    
    def agregar_filas(self, df, nombre_hoja="Registros"):
        """Agrega nuevas filas al final de la hoja"""
        try:
            # Leer datos existentes para saber dónde agregar
            df_existente = self.leer_hoja(nombre_hoja)
            
            if df_existente.empty:
                # Si no hay datos, escribir todo incluyendo headers
                return self.escribir_hoja(df, nombre_hoja, limpiar_hoja=True)
            
            # Preparar nuevas filas
            if df.empty:
                return True
            
            df_clean = df.fillna('').astype(str)
            df_clean = df_clean.replace('nan', '').replace('None', '')
            nuevas_filas = df_clean.values.tolist()
            
            # Calcular el rango para agregar
            fila_inicio = len(df_existente) + 2  # +2 porque: +1 por headers, +1 por siguiente fila disponible
            
            body = {
                'values': nuevas_filas
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{nombre_hoja}!A{fila_inicio}",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            rows_updated = result.get('updatedRows', 0)
            st.success(f"✅ {rows_updated} filas agregadas en '{nombre_hoja}'")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error al agregar filas: {str(e)}")
            return False
    
    def limpiar_hoja(self, nombre_hoja="Registros"):
        """Limpia completamente una hoja"""
        try:
            # Obtener información de la hoja
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            # Buscar el sheet_id
            sheet_id = None
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == nombre_hoja:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                # Si no existe la hoja, crearla
                self.crear_hoja(nombre_hoja)
                return True
            
            # Limpiar contenido
            # Limpiar contenido SOLO si es la hoja Registros
            if nombre_hoja == "Registros":
                self.service.spreadsheets().values().clear(
                    spreadsheetId=self.spreadsheet_id,
                    range=nombre_hoja
                ).execute()
            else:
                # Para cualquier otra hoja, NO limpiar
                return False
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error al limpiar hoja: {str(e)}")
            return False
    
    def crear_hoja(self, nombre_hoja):
        """Crea una nueva hoja si no existe"""
        try:
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': nombre_hoja
                        }
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            st.success(f"✅ Hoja '{nombre_hoja}' creada exitosamente")
            return True
            
        except Exception as e:
            st.error(f"❌ Error al crear hoja: {str(e)}")
            return False
    
    def listar_hojas(self):
        """Lista todas las hojas disponibles en el spreadsheet"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            hojas = []
            for sheet in spreadsheet['sheets']:
                hojas.append(sheet['properties']['title'])
            
            return hojas
            
        except Exception as e:
            st.error(f"❌ Error al listar hojas: {str(e)}")
            return []
    
    def _get_column_letter(self, col_num):
        """Convierte número de columna a letra (1=A, 2=B, etc.)"""
        string = ""
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            string = chr(65 + remainder) + string
        return string
    
    def crear_backup(self, nombre_hoja="Registros"):
        """Crea una copia de respaldo con timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_backup = f"{nombre_hoja}_backup_{timestamp}"
            
            # Leer datos originales
            df = self.leer_hoja(nombre_hoja)
            
            if not df.empty:
                # Escribir en nueva hoja de backup
                self.escribir_hoja(df, nombre_backup, limpiar_hoja=True)
                st.info(f"📋 Backup creado: '{nombre_backup}'")
                return nombre_backup
            else:
                st.warning("No hay datos para respaldar")
                return None
                
        except Exception as e:
            st.error(f"❌ Error al crear backup: {str(e)}")
            return None

# Instancia global del manager
sheets_manager = None

def get_sheets_manager():
    """Obtiene o crea la instancia del manager"""
    global sheets_manager
    if sheets_manager is None:
        sheets_manager = GoogleSheetsManager()
    return sheets_manager

def test_connection():
    """Función para probar la conexión"""
    try:
        manager = get_sheets_manager()
        hojas = manager.listar_hojas()
        st.success(f"✅ Conexión exitosa. Hojas disponibles: {', '.join(hojas)}")
        return True
    except Exception as e:
        st.error(f"❌ Test de conexión falló: {str(e)}")
        return False
