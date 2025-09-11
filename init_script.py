#!/usr/bin/env python3
"""
Script de inicialización para el Tablero de Control de Cronogramas
Este script verifica la configuración y prepara el entorno inicial.
"""

import os
import json
import sys
from pathlib import Path

def print_header():
    """Imprime el encabezado del script"""
    print("="*60)
    print("🚀 TABLERO DE CONTROL DE CRONOGRAMAS")
    print("📊 Script de Inicialización y Verificación")
    print("="*60)
    print()

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print("📦 Verificando dependencias...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'google-auth',
        'google-api-python-client',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print()
        print("⚠️  Dependencias faltantes encontradas!")
        print("   Ejecuta: pip install -r requirements.txt")
        print()
        return False
    
    print("   🎉 Todas las dependencias están instaladas")
    print()
    return True

def check_credentials():
    """Verifica la configuración de credenciales"""
    print("🔐 Verificando configuración de credenciales...")
    
    # Verificar credentials.json
    if os.path.exists('credentials.json'):
        print("   ✅ credentials.json encontrado")
        
        try:
            with open('credentials.json', 'r') as f:
                creds = json.load(f)
                
            required_fields = [
                'type', 'project_id', 'private_key_id', 'private_key',
                'client_email', 'client_id'
            ]
            
            missing_fields = [field for field in required_fields if field not in creds]
            
            if missing_fields:
                print(f"   ⚠️  Campos faltantes en credentials.json: {missing_fields}")
                return False
            else:
                print("   ✅ credentials.json tiene todos los campos requeridos")
                
        except json.JSONDecodeError:
            print("   ❌ credentials.json no es un JSON válido")
            return False
            
    else:
        print("   ⚠️  credentials.json no encontrado")
        print("   📋 Para desarrollo local, necesitas este archivo")
        print("   📋 Para Streamlit Cloud, usa secrets.toml")
    
    # Verificar config.json
    if os.path.exists('config.json'):
        print("   ✅ config.json encontrado")
        
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                
            if 'spreadsheet_id' in config and config['spreadsheet_id']:
                print("   ✅ spreadsheet_id configurado")
            else:
                print("   ⚠️  spreadsheet_id no configurado en config.json")
                return False
                
        except json.JSONDecodeError:
            print("   ❌ config.json no es un JSON válido")
            return False
    else:
        print("   ⚠️  config.json no encontrado")
        print("   📋 Copia config.json.example como config.json y configura tu spreadsheet_id")
    
    print()
    return True

def test_google_sheets_connection():
    """Prueba la conexión con Google Sheets"""
    print("🔗 Probando conexión con Google Sheets...")
    
    try:
        from sheets_utils import get_sheets_manager
        
        manager = get_sheets_manager()
        hojas = manager.listar_hojas()
        
        print(f"   ✅ Conexión exitosa!")
        print(f"   📊 Hojas disponibles: {', '.join(hojas)}")
        print()
        return True
        
    except Exception as e:
        print(f"   ❌ Error de conexión: {str(e)}")
        print("   📋 Verifica tu configuración de Google Sheets")
        print()
        return False

def create_initial_structure():
    """Crea la estructura inicial si no existe"""
    print("📁 Verificando estructura inicial...")
    
    try:
        from sheets_utils import get_sheets_manager
        from data_utils import crear_estructura_metas_inicial
        import pandas as pd
        
        manager = get_sheets_manager()
        hojas = manager.listar_hojas()
        
        # Verificar hoja de Registros
        if 'Registros' not in hojas:
            print("   📊 Creando hoja 'Registros'...")
            
            # Crear estructura básica de registros
            columnas_registros = [
                'Cod', 'Entidad', 'TipoDato', 'Nivel Información ',
                'Acuerdo de compromiso', 'Análisis y cronograma',
                'Estándares', 'Publicación', 'Fecha de entrega de información',
                'Plazo de análisis', 'Plazo de cronograma', 'Plazo de oficio de cierre'
            ]
            
            df_registros = pd.DataFrame(columns=columnas_registros)
            manager.escribir_hoja(df_registros, 'Registros', limpiar_hoja=True)
            print("   ✅ Hoja 'Registros' creada")
        else:
            print("   ✅ Hoja 'Registros' existe")
        
        # Verificar hoja de Metas
        if 'Metas' not in hojas:
            print("   📈 Creando hoja 'Metas'...")
            
            df_metas = crear_estructura_metas_inicial()
            manager.escribir_hoja(df_metas, 'Metas', limpiar_hoja=True)
            print("   ✅ Hoja 'Metas' creada")
        else:
            print("   ✅ Hoja 'Metas' existe")
        
        print()
        return True
        
    except Exception as e:
        print(f"   ❌ Error creando estructura: {str(e)}")
        print()
        return False

def show_next_steps():
    """Muestra los siguientes pasos"""
    print("🎯 SIGUIENTES PASOS:")
    print()
    print("1. 🚀 Ejecutar la aplicación:")
    print("   streamlit run app1.py")
    print()
    print("2. 📊 Acceder al tablero:")
    print("   http://localhost:8501")
    print()
    print("3. 📁 Cargar datos iniciales:")
    print("   - Usa el uploader de Excel en la barra lateral")
    print("   - O edita directamente en Google Sheets")
    print()
    print("4. 🔧 Configuración adicional:")
    print("   - Ajusta las metas en la hoja 'Metas'")
    print("   - Configura los funcionarios")
    print("   - Personaliza los filtros")
    print()

def show_troubleshooting():
    """Muestra información para solución de problemas"""
    print("🆘 SOLUCIÓN DE PROBLEMAS:")
    print()
    print("❌ Error de credenciales:")
    print("   - Verifica que credentials.json tenga todos los campos")
    print("   - Confirma que el service account tenga permisos")
    print("   - Revisa que el spreadsheet_id sea correcto")
    print()
    print("❌ Error de conexión:")
    print("   - Verifica tu conexión a internet")
    print("   - Confirma que Google Sheets API esté habilitada")
    print("   - Revisa que el spreadsheet esté compartido con el service account")
    print()
    print("📋 Documentación completa:")
    print("   - README.md: Guía general")
    print("   - INSTRUCCIONES_CONFIGURACION.md: Configuración Google Sheets")
    print()

def main():
    """Función principal"""
    print_header()
    
    # Lista de verificaciones
    checks = [
        ("Dependencias", check_dependencies),
        ("Credenciales", check_credentials),
        ("Conexión Google Sheets", test_google_sheets_connection),
        ("Estructura inicial", create_initial_structure),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ Error inesperado en {name}: {str(e)}")
            results.append((name, False))
    
    # Resumen de resultados
    print("📋 RESUMEN DE VERIFICACIÓN:")
    print()
    
    all_passed = True
    for name, passed in results:
        status = "✅ CORRECTO" if passed else "❌ ERROR"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 ¡CONFIGURACIÓN COMPLETA!")
        print("   Todo está listo para usar el tablero.")
        print()
        show_next_steps()
    else:
        print("⚠️  CONFIGURACIÓN INCOMPLETA")
        print("   Hay problemas que necesitan resolverse.")
        print()
        show_troubleshooting()

if __name__ == "__main__":
    main()
