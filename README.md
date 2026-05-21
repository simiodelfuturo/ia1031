# Nemi — Asistente de Orientación y Triage en Salud Mental

## ¿Qué es Nemi?
Nemi es un asistente conversacional de orientación y triage en salud mental para público general en México. Está representado por un ajolote y su nombre viene del náhuatl: "vivir y caminar".

## ¿Por qué usamos AI?
La inteligencia artificial permite que Nemi procese lenguaje natural para identificar el dominio de malestar predominante, orientar hacia recursos de apoyo y generar un reporte estructurado para el profesionista que atienda después.

Nemi no sustituye la atención profesional ni toma decisiones clínicas. Su función es reducir la barrera de acceso a orientación inicial y facilitar la derivación al recurso adecuado. Como toda herramienta de IA, puede cometer errores y debe ser supervisada por profesionistas de salud.

## ¿Para qué usamos AI?
- Identificar el dominio de origen del malestar según el Modelo RADAR 5 (Biológico, Material, Trauma, Relacional, Psicológico/Significado)
- Orientar al usuario hacia recursos específicos según su situación (tipo de seguro médico, género, tipo de crisis)
- Detectar riesgo de vida y activar protocolo de crisis con recursos de emergencia
- Generar un reporte clínico con formulación breve, nivel de riesgo y fragmentos relevantes
- Producir un código QR descargable que el usuario puede mostrar al profesionista que lo atienda

## Guardrails implementados
- Bloqueo de diagnósticos y nombres de enfermedades mentales
- Prohibición de recomendar medicamentos
- Protocolo obligatorio ante riesgo de vida (Línea de la Vida 800 290 0024)
- Límite de 15 turnos por sesión
- Cierre automático por inactividad (10 minutos)
- Manejo de filtro de contenido de Azure para contenido sensible

## Stack técnico
- Python + Flask
- Azure OpenAI (gpt-4o)
- HTML / CSS / JavaScript vanilla

## Configuración
1. Clona el repositorio
2. Crea un archivo `.env` basado en `.env.example`
3. Instala dependencias: `pip install -r requirements.txt`
4. Corre el servidor: `python app.py`
5. Abre `http://127.0.0.1:5000` en el navegador

## Demo
1. https://youtu.be/AYxVRBBQKk4
2. https://youtu.be/sP_iVRdht80