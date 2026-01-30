# 📊 Tablero de Control Datos Temáticos - Ideca

Sistema web de gestión y seguimiento de proyectos de datos temáticos desarrollado con Streamlit. Permite el monitoreo en tiempo real del avance de proyectos a través de múltiples etapas: acuerdos, análisis, estándares y publicación.

## 🌟 Características Principales

- **Dashboard Interactivo**: Visualización en tiempo real del estado de proyectos con métricas clave y gráficos
- **Gestión de Registros**: Editor completo para crear, modificar y eliminar registros de proyectos
- **Seguimiento Trimestral**: Comparación de avances contra metas programadas
- **Sistema de Alertas**: Notificaciones automáticas de fechas vencidas y próximas a vencer
- **Generación de Reportes**: Reportes personalizables con múltiples filtros
- **Integración Google Sheets**: Persistencia de datos en tiempo real con Google Sheets API
- **Sistema de Respaldos**: Protección automática de datos con backups antes de cada modificación
- **Autenticación**: Control de acceso para operaciones de edición

## 📋 Requisitos Previos

- Python 3.13 o superior
- Cuenta de Google Cloud con API de Google Sheets habilitada
- Service Account de Google con permisos de editor en el spreadsheet

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd DTEM
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

### Configuración de Google Sheets

#### 1. Crear Service Account

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Sheets
4. Ve a "Credenciales" → "Crear credenciales" → "Cuenta de servicio"
5. Descarga el archivo JSON de credenciales

#### 2. Configurar Credenciales Localmente

Crea un archivo `credentials.json` en la raíz del proyecto con el contenido del archivo descargado:

```json
{
  "type": "service_account",
  "project_id": "tu-project-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

Crea un archivo `config.json`:

```json
{
  "spreadsheet_id": "tu-spreadsheet-id-aqui"
}
```

**⚠️ Importante**: Nunca subas estos archivos al repositorio. Ya están en `.gitignore`.

#### 3. Configurar para Streamlit Cloud

Si despliegas en Streamlit Cloud, agrega las credenciales en "Secrets":

```toml
# .streamlit/secrets.toml
[google_sheets]
type = "service_account"
project_id = "tu-project-id"
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
spreadsheet_id = "tu-spreadsheet-id"
```

#### 4. Compartir Spreadsheet

Comparte tu Google Spreadsheet con el email del service account (client_email) con permisos de **Editor**.

### Inicializar el Sistema

Ejecuta el script de inicialización para verificar la configuración:

```bash
python init_script.py
```

Este script verifica:
- ✅ Dependencias instaladas
- ✅ Credenciales configuradas correctamente
- ✅ Conexión con Google Sheets
- ✅ Estructura de hojas (Registros y Metas)

## 🎯 Uso

### Iniciar la Aplicación

```bash
streamlit run app1.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

### Credenciales de Administrador

Para acceder a funciones de edición:
- **Usuario**: `admin`
- **Contraseña**: `qwerty`

⚠️ **Nota de Seguridad**: Cambiar estas credenciales en producción editando `auth_utils.py`

### Navegación

La aplicación tiene 5 pestañas principales:

1. **Dashboard** 📊
   - Métricas generales del proyecto
   - Gráficos de avance por entidad
   - Distribución de proyectos por funcionario
   - Cumplimiento de metas

2. **Edición** ✏️
   - Crear nuevos registros
   - Editar registros existentes
   - Eliminar registros
   - Requiere autenticación administrativa

3. **Seguimiento Trimestral** 📈
   - Comparación de metas vs. avances
   - Visualización trimestral
   - Análisis de cumplimiento por tipo de dato

4. **Alertas** 🔔
   - Fechas vencidas
   - Próximas a vencer (30 días)
   - Registros en retraso
   - Alertas por funcionario

5. **Reportes** 📄
   - Filtros múltiples (entidad, tipo, estado)
   - Exportación de datos
   - Visualizaciones personalizadas

## 📁 Estructura del Proyecto

```
DTEM/
├── app1.py                      # Aplicación principal
├── dashboard.py                 # Dashboard y visualizaciones
├── editor.py                    # Editor de registros
├── trimestral.py                # Seguimiento trimestral
├── alertas.py                   # Sistema de alertas
├── reportes.py                  # Generación de reportes
├── sheets_utils.py              # Integración Google Sheets
├── data_utils.py                # Procesamiento de datos
├── backup_utils.py              # Sistema de respaldos
├── auth_utils.py                # Autenticación
├── validaciones_utils.py        # Reglas de negocio
├── fecha_utils.py               # Cálculo de plazos
├── plazo_utils.py               # Lógica de plazos
├── visualization.py             # Gráficos y visualizaciones
├── config.py                    # Configuración Streamlit
├── constants.py                 # Constantes del sistema
├── init_script.py               # Script de inicialización
├── requirements.txt             # Dependencias Python
├── README.md                    # Este archivo
├── CLAUDE.md                    # Guía para desarrollo
└── gitignore_file.txt           # Archivos a ignorar
```

## 🛠️ Tecnologías Utilizadas

- **[Streamlit](https://streamlit.io/)** - Framework web para aplicaciones de datos
- **[Pandas](https://pandas.pydata.org/)** - Análisis y manipulación de datos
- **[Plotly](https://plotly.com/)** - Visualizaciones interactivas
- **[Google Sheets API](https://developers.google.com/sheets/api)** - Persistencia de datos
- **[ReportLab](https://www.reportlab.com/)** - Generación de PDFs
- **[openpyxl](https://openpyxl.readthedocs.io/)** - Procesamiento de archivos Excel

## 📊 Flujo de Datos

```
┌─────────────────┐
│  Google Sheets  │
│  (Registros +   │
│     Metas)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  sheets_utils   │
│ GoogleSheets    │
│    Manager      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   data_utils    │
│ cargar_datos()  │
│ + validaciones  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     app1.py     │
│  (Main Loop)    │
└────────┬────────┘
         │
         ├──────────┬──────────┬──────────┬──────────┐
         ▼          ▼          ▼          ▼          ▼
    Dashboard   Editor   Trimestral  Alertas   Reportes
```

## 🔒 Seguridad y Permisos

### Niveles de Acceso

- **Lectura** (Sin autenticación):
  - Dashboard
  - Visualizaciones
  - Reportes
  - Alertas

- **Escritura** (Requiere autenticación):
  - Crear registros
  - Editar registros
  - Eliminar registros
  - Modificar configuraciones

### Protección de Datos

- Backups automáticos antes de cada modificación
- Protección de la hoja "Metas" durante operaciones de escritura
- Verificación y restauración automática en caso de errores
- Sistema de respaldo en hoja "Respaldo_Registros"

## 🧪 Testing y Desarrollo

### Verificar Configuración

```bash
python init_script.py
```

### Probar Conexión Google Sheets

Dentro de la aplicación, en la barra lateral:
1. Expandir "Configuración"
2. Hacer clic en "Probar Conexión"

### Modo Desarrollo

Para desarrollo local con datos de prueba, el sistema incluye datos de ejemplo en `constants.py`.

## 📈 Cálculo de Avances

El sistema calcula el porcentaje de avance de cada proyecto basado en 4 etapas:

| Etapa | Peso |
|-------|------|
| Acuerdo de compromiso | 25% |
| Análisis y cronograma | 25% |
| Estándares | 25% |
| Publicación | 25% |

**Regla especial**: Si existe "Fecha de oficio de cierre", el avance es automáticamente 100%.

## 🐛 Solución de Problemas

### Error de Conexión a Google Sheets

```
❌ Error: No se puede conectar a Google Sheets
```

**Solución**:
1. Verifica que `credentials.json` existe y es válido
2. Confirma que `spreadsheet_id` en `config.json` es correcto
3. Verifica que el service account tiene permisos de Editor
4. Confirma que Google Sheets API está habilitada

### Error de Fechas

```
❌ TypeError: can't compare datetime.date to datetime.datetime
```

**Solución**: Este error ya está corregido en la versión actual. Si aparece, ejecuta:

```python
from data_utils import diagnosticar_errores_datetime, reparar_fechas_automaticamente
```

### Tabla Metas Vacía o Borrada

El sistema incluye recuperación automática. Si persiste:

```python
from data_utils import reparar_sistema_automatico
exito, mensajes = reparar_sistema_automatico()
```

## 📝 Notas de Desarrollo

- Consulta `CLAUDE.md` para guías detalladas de desarrollo
- Los nombres de columnas pueden tener espacios finales (ej: "Nivel Información ")
- Siempre usa `procesar_fecha()` para parsing de fechas
- Las funciones de guardado incluyen protección automática de Metas
- Session state de Streamlit se usa para persistencia temporal

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de uso interno de Ideca.

## 👥 Contacto

Para soporte o preguntas sobre el sistema, contacta al equipo de desarrollo de Ideca.

---

Desarrollado con ❤️ para Ideca - Instituto Distrital de Gestión de Riesgos y Cambio Climático
