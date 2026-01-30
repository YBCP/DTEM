# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **DTEM (Datos Temáticos)** - a Streamlit-based dashboard system for tracking thematic data projects at Ideca. The system manages project workflows through multiple stages: agreements, analysis, standards, and publication. It integrates with Google Sheets for data persistence and provides real-time tracking of project progress, deadlines, and team assignments.

## Running the Application

### Development
```bash
# Install dependencies (Python 3.13+ required)
pip install -r requirements.txt

# Run the application
streamlit run app1.py

# Initialize/verify system configuration
python init_script.py
```

### Access
- Application runs on: http://localhost:8501
- Admin credentials: username=`admin`, password=`qwerty` (see auth_utils.py)

## Architecture

### Core Flow
1. **app1.py** - Main entry point that orchestrates the entire application
2. **Data loading** - cargar_datos() retrieves data from Google Sheets (Registros + Metas sheets)
3. **Authentication** - auth_utils.py manages admin access for editing operations
4. **Tab-based navigation** - Dashboard, Editor, Trimestral, Alertas, Reportes

### Key Architectural Patterns

**Google Sheets as Database**
- Primary data storage is Google Sheets (not local CSV)
- `sheets_utils.py` provides GoogleSheetsManager singleton for all sheet operations
- Two critical sheets: "Registros" (project records) and "Metas" (goals/targets)
- Backup system in `backup_utils.py` automatically protects data during edits

**Data Protection Layer**
- Metas sheet is protected from accidental deletion during Registros updates
- All write operations include automatic Metas verification and restoration
- Functions like `guardar_datos_editados()` and `sincronizar_con_google_sheets()` have built-in protection

**Date Handling**
- `procesar_fecha()` in data_utils.py ALWAYS returns datetime objects (never date objects)
- This prevents datetime/date comparison errors throughout the codebase
- All date comparisons use datetime.now() as the reference

**Progress Calculation**
- Projects have 4 stages with weighted contributions:
  - Acuerdo de compromiso: 25%
  - Análisis y cronograma: 25%
  - Estándares: 25%
  - Publicación: 25%
- Special rule: If "Fecha de oficio de cierre" exists, progress = 100% automatically
- See `calcular_porcentaje_avance()` in data_utils.py

**Validation Pipeline**
- `validaciones_utils.py` applies business rules to records
- `fecha_utils.py` automatically calculates deadline fields (Plazo de análisis, Plazo de cronograma, Plazo de oficio de cierre)
- Pipeline runs automatically on data load in app1.py:main()

## Module Organization

### Primary Modules
- **app1.py** - Application orchestration, tab management, main loop
- **dashboard.py** - Metrics visualization, charts, progress tracking
- **editor.py** - Record editing interface (requires authentication)
- **trimestral.py** - Quarterly tracking and goal comparison
- **alertas.py** - Deadline alerts and overdue notifications
- **reportes.py** - Report generation and filtering

### Utilities
- **sheets_utils.py** - Google Sheets API wrapper (GoogleSheetsManager class)
- **data_utils.py** - Data loading, processing, date handling, save operations
- **backup_utils.py** - Automatic backup system (cargar_datos_con_respaldo, crear_respaldo_automatico)
- **auth_utils.py** - Authentication system for admin operations
- **validaciones_utils.py** - Business rule validation
- **fecha_utils.py** - Deadline calculations (plazo calculations)
- **plazo_utils.py** - Specific deadline logic helpers
- **visualization.py** - Chart creation (Gantt, comparisons)

### Configuration
- **config.py** - Streamlit page config, CSS styles
- **constants.py** - Business constants (HITOS weights, VALORES_POSITIVOS, date alert thresholds)

## Critical Patterns to Follow

### Always Read Before Writing
```python
# CORRECT - Read file first
df = sheets_manager.leer_hoja("Registros")
# Make modifications
sheets_manager.escribir_hoja(df, "Registros")

# INCORRECT - Writing without reading
sheets_manager.escribir_hoja(new_df, "Registros")  # Don't do this
```

### Protected Save Operations
```python
# Use the protected save functions that include Metas verification
from data_utils import guardar_datos_editados
exito, mensaje = guardar_datos_editados(df, crear_backup=True)

# OR for individual row updates
from data_utils import guardar_datos_editados_rapido
exito, mensaje = guardar_datos_editados_rapido(df, numero_fila=5)
```

### Date Processing
```python
# ALWAYS use procesar_fecha() for date parsing
from data_utils import procesar_fecha, formatear_fecha

fecha = procesar_fecha(row['Fecha de entrega de información'])  # Returns datetime or None
fecha_str = formatear_fecha(fecha)  # Returns "DD/MM/YYYY" string

# For comparisons
if fecha and fecha < datetime.now():  # Safe comparison
    # Handle overdue
```

### Google Sheets Manager
```python
# Get singleton instance
from sheets_utils import get_sheets_manager
manager = get_sheets_manager()

# Read operations
df = manager.leer_hoja("Registros")
hojas = manager.listar_hojas()

# Write operations (use data_utils wrappers instead for safety)
manager.escribir_hoja(df, "Registros", limpiar_hoja=True)
```

### Authentication Requirements
```python
# Editor operations require authentication
from auth_utils import verificar_autenticacion, requiere_autenticacion

if verificar_autenticacion():
    # Allow editing
else:
    st.warning("Se requiere autenticación")

# Or use decorator
@requiere_autenticacion
def operacion_sensible():
    # This function requires admin authentication
```

## Data Structure

### Registros Sheet Columns
Key columns (44+ total):
- **Identity**: Cod, Funcionario, Entidad, Nivel Información, Frecuencia actualizacion, TipoDato
- **Stages**: Acuerdo de compromiso, Análisis y cronograma, Estándares, Publicación
- **Dates**: Fecha de entrega de información, Análisis y cronograma (fecha programada), Estándares (fecha programada), Fecha de publicación programada, Fecha de oficio de cierre
- **Calculated**: Plazo de análisis, Plazo de cronograma, Plazo de oficio de cierre, Porcentaje Avance, Estado Fechas
- **Status**: Estado, Observación

### Metas Sheet Structure
- Column 0: Dates (fechas)
- Columns 1-4: Nuevo records (Acuerdo, Análisis, Estándares, Publicación)
- Column 5: Separator
- Columns 6-9: Actualizar records (Acuerdo, Análisis, Estándares, Publicación)

Processed by `procesar_metas()` in data_utils.py into separate DataFrames for nuevos and actualizar.

## Common Operations

### Adding a New Record
Edit operations happen through editor.py, which:
1. Checks authentication
2. Presents form with all fields
3. Validates input
4. Saves to Google Sheets using protected save functions
5. Updates session state

### Modifying Dashboard Visualizations
1. Locate visualization in dashboard.py or visualization.py
2. Modify using Plotly (plotly.express or plotly.graph_objects)
3. Test with various data filters
4. Ensure responsive layout (st.columns for side-by-side)

### Adding New Validation Rules
1. Add rule function to validaciones_utils.py
2. Call from main validation pipeline: `validar_reglas_negocio()`
3. Validation runs automatically on data load in app1.py

### Deadline Calculation Modifications
1. Locate logic in fecha_utils.py (actualizar_plazo_* functions)
2. Modify calculation based on business rules
3. Plazo calculations run automatically on data load

## Important Notes

### Security
- Credentials stored in credentials.json (local) or st.secrets (cloud)
- Never commit credentials.json (see gitignore_file.txt)
- Authentication system in auth_utils.py with hardcoded credentials (production should use secure storage)

### Data Integrity
- Metas sheet is automatically protected during all Registros write operations
- Backup system creates automatic backups before writes
- System includes reparar_sistema_automatico() function for recovery

### Session State Usage
- `st.session_state['registros_df']` stores current data
- `st.session_state['autenticado']` tracks auth status
- Data persists across tab switches within same session

### Performance
- Data loads once at app start in main()
- Caching via @st.cache_data is minimal (deliberate choice for real-time updates)
- Google Sheets API has rate limits (handled in sheets_utils.py)

### Field Naming Conventions
- Many column names have trailing spaces (e.g., "Nivel Información ", "Frecuencia actualizacion ")
- COLUMNAS_REALES mapping in editor.py documents exact column names
- Use exact names from COLUMNAS_REALES when referencing columns

## Testing Connection

```bash
# Run initialization script to verify setup
python init_script.py

# This checks:
# - Dependencies installation
# - Credentials configuration
# - Google Sheets connection
# - Sheet structure
```

## Troubleshooting

**Google Sheets Connection Errors**
- Verify credentials.json has all required fields
- Check spreadsheet_id in config.json or st.secrets
- Ensure service account has editor access to the spreadsheet
- Confirm Google Sheets API is enabled in Google Cloud Console

**Date Comparison Errors**
- Always use `procesar_fecha()` which returns datetime (never date)
- Use `datetime.now()` for current time comparisons
- See diagnosticar_errores_datetime() in data_utils.py for debugging

**Metas Sheet Deleted/Empty**
- System has auto-recovery: verificar_integridad_metas() and reparar_sistema_automatico()
- Backup copies exist in "Respaldo_Registros" sheet
- Use crear_estructura_metas_inicial() to recreate structure

**Authentication Issues**
- Default credentials in auth_utils.py: admin/qwerty
- Session expires after 8 hours (see verificar_sesion_activa)
- Clear browser cookies if stuck in bad auth state
