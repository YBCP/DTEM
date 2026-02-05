# Plan de Datos (PDDATOS) - Reglas de Negocio

## 1. Un Registro = Una Etapa
Cada registro está en UNA SOLA ETAPA a la vez.

## 2. Secuencialidad
Las actividades deben completarse en orden. Para iniciar una actividad, la anterior debe estar "Completa" o "No aplica".

## 3. Estados
- Sin iniciar: 0% avance
- Iniciada: 0% avance
- Completa: 100% avance
- No aplica: no cuenta para el cálculo

## 4. Cálculo de Avance
Avance = (Completas / (Total - No aplica)) × 100

## 5. Actividades Excluyentes
Grupos como 3.3.1, 3.3.2, 3.3.3: solo una puede completarse. Las demás se marcan "No aplica" automáticamente.
