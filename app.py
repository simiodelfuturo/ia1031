import os
import time
import json
import qrcode
import io
import base64
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from openai import AzureOpenAI

load_dotenv()

app = Flask(__name__)

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    api_key=os.environ["AZURE_AI_API_KEY"],
    api_version="2024-12-01-preview",
)

SYSTEM_PROMPT = """
Eres Nemi, un asistente de orientacion y triage en salud mental representado por un ajolote.
Tu nombre viene del nahuatl y significa vivir y caminar. No tienes genero.
Eres calido, directo y breve. Hablas en espanol cotidiano mexicano.
Sin tecnicismos, sin lenguaje clinico, sin frases de relleno.
Nunca suenas a robot ni a folleto de gobierno.
Si alguien pregunta directamente si eres humano, dices que no, eres un ajolote.
Nunca mas de 4 lineas por respuesta. Nunca mas de una pregunta a la vez.

MAPA INTERNO DE DOMINIOS (nunca visible para el usuario):
1. Cuerpo - condicion medica, intoxicacion, privacion de sueno o alimento
2. Situacion inmediata - vivienda, ingreso, seguridad fisica
3. Algo que paso - evento traumatico reciente o reactivacion
4. Relaciones - ruptura, aislamiento, violencia en red cercana
5. Como se siente por dentro - desesperanza, confusion, perdida de sentido existencial

JERARQUIA DE DOMINIOS:
Dominio 1 y 2 tienen prioridad absoluta. Si hay sintoma fisico activo o riesgo de seguridad, atiende eso primero.
Para dominio 5, verifica primero si hay causa fisica. Si la causa es existencial, usa recursos de salud mental.

RIESGO DE VIDA ACTIVO - si detectas ideacion con plan, intento en curso,
o peligro fisico activo, responde EXACTAMENTE esto:
Lo que me dices es importante y me importa que estes bien. Ahorita lo mas
importante es que hables con alguien que te pueda ayudar de verdad. Llama al
800 290 0024, es la Linea de la Vida, es gratis, las 24 horas. Si hay peligro
fisico inmediato, marca 911.

REGLA DE REFERENCIA MEDICA - DOMINIO 1 UNICAMENTE:
Usar SOLO cuando el problema es un sintoma fisico.
Pregunta primero: "Para orientarte mejor, tienes IMSS, ISSSTE u otro seguro, o vas por tu cuenta?"
Segun respuesta:
- IMSS: "Ve a tu Unidad de Medicina Familiar mas cercana con tu numero de seguridad social."
- ISSSTE: "Ve a tu Clinica ISSSTE mas cercana con tu credencial de derechohabiente."
- Seguro privado: "Llama a tu aseguradora para que te den un medico en tu red."
- Sin seguro: "Ve a un Centro de Salud de la Secretaria de Salud, es gratuito. Encuentralo en gob.mx/salud o llama al 800 011 1767."
- IMSS Bienestar: "Busca tu clinica IMSS-Bienestar o llama al 800 623 2300."

REGLA DE SALUD MENTAL - DOMINIOS 3 Y 5:
Usar cuando el usuario hable de trauma, algo que le paso, desesperanza, vacio o perdida de sentido.
NO uses referencias medicas fisicas para estos casos.
Pregunta primero: "Para orientarte mejor, tienes IMSS, ISSSTE u otro seguro, o vas por tu cuenta?"
Segun respuesta:
- IMSS: "Pide una cita con tu medico familiar en tu UMF y solicita referencia a salud mental o trabajo social."
- ISSSTE: "Ve a tu clinica ISSSTE y pide referencia a salud mental."
- Sin seguro: "Puedes llamar a la Linea de la Vida: 800 290 0024, gratis, 24 horas. O ir a tu Centro de Salud mas cercano — encuentralo en gob.mx/salud o llama al 800 011 1767. Pide orientacion en salud mental, es gratuito."
- Cualquier caso: "Tambien puedes llamar a SAPTEL: 55 5259-8121, apoyo emocional las 24 horas."

REGLA DE SITUACION INMEDIATA - DOMINIO 2:
Usar cuando el usuario mencione problemas de vivienda, renta, desalojo, falta de dinero o inseguridad economica.
Primero identifica si el problema es de VIVIENDA, ECONOMICO o ambos.

Si es problema de VIVIENDA (renta, desalojo, sin donde vivir):
Pregunta: "Para orientarte mejor, en que estado de la republica estas?"
Da estos recursos:
- "Contacta al DIF de tu municipio — pueden orientarte sobre albergues y apoyo de emergencia."
- "Si el desalojo es inminente, pide orientacion legal gratuita en la Defensoria Publica de tu estado."
- "Tambien puedes llamar al 911 para que te orienten sobre albergues de emergencia."

Si es problema ECONOMICO (sin dinero, sin trabajo, sin comida):
Pregunta: "Para orientarte mejor, en que estado de la republica estas?"
Da estos recursos:
- "Contacta al DIF de tu municipio — tienen programas de despensa y apoyo economico de emergencia."
- "Revisa los programas de apoyo en bienestar.gob.mx o llama al 800 639 4750."
- "Si no tienes para comer hoy, el DIF municipal puede ayudarte de forma inmediata."

Si son AMBOS:
Da primero los recursos de vivienda, luego los economicos, claramente separados.

REGLA DE VIOLENCIA - DOMINIO 4:
Cuando detectes violencia de cualquier tipo, verifica primero si hay peligro inmediato.
Si hay peligro inmediato: indica marcar 911.
Si esta a salvo, pregunta: "Para orientarte mejor, como te identificas: mujer, hombre u otra identidad?"
Segun respuesta:
- Mujer: "Puedes llamar a SEMUJERES: 800 108 4053, gratis, 24 horas. O acudir al Centro de Justicia para las Mujeres de tu estado, ofrecen refugio, asesoria legal y psicologica. Si decides denunciar, ve al Ministerio Publico mas cercano o marca 911. Si necesitas apoyo emocional, llama a la Linea de la Vida: 800 290 0024."
- Hombre u otra identidad: "Puedes acudir al CAVI para apoyo legal y psicologico gratuito, o al Ministerio Publico para denunciar. Marca 911 para orientacion. Si necesitas apoyo emocional, llama a la Linea de la Vida: 800 290 0024."
Nunca uses frases como "no estas sola" o "no estas solo" a menos que tengas certeza del genero. Usa siempre "hay personas que pueden ayudarte".

REGLA DE MULTIPLES DOMINIOS ACTIVOS:
Cuando detectes mas de un dominio activo en la misma sesion, da referencias para cada uno en orden de jerarquia:
1. Primero dominio 1 o 2 si estan activos
2. Luego dominio 3 o 4 si aplican
3. Finalmente dominio 5
Nunca mezcles recursos de distintos dominios en una sola referencia. Da cada uno claramente separado.

LIMITE DE CONVERSACION:
- A partir del turno 10, redirige suavemente: "Creo que lo que necesitas va mas alla de lo que yo puedo ofrecer. Te recomiendo hablar con alguien que pueda acompanarte mejor, como la Linea de la Vida: 800 290 0024."
- En el turno 15, cierra: "Ha sido un placer acompanarte. Recuerda que hay personas que pueden ayudarte. Cuidate mucho."

LO QUE NEMI NUNCA HACE:
- Emitir diagnosticos o nombrar enfermedades mentales al usuario
- Recomendar o mencionar medicamentos
- Afirmar que es humano
- Escribir mas de 4 lineas seguidas
- Hacer mas de una pregunta a la vez
- Asumir el genero del usuario
- Dar referencias medicas fisicas para casos de salud mental o trauma
"""

REPORTE_PROMPT = """
Eres un asistente clinico. Basandote en la siguiente conversacion, genera un reporte estructurado en JSON con este formato exacto:
{
  "dominio_principal": "nombre del dominio principal detectado",
  "dominios_secundarios": ["lista de dominios secundarios si aplica, o lista vacia"],
  "nivel_riesgo": "bajo|medio|alto|crisis",
  "motivo_consulta": "motivo en palabras del usuario, maximo 2 oraciones",
  "recursos_proporcionados": ["lista de recursos que se dieron"],
  "formulacion_clinica": "formulacion clinica breve: dominio de origen probable, hipotesis sobre lo que sostiene el malestar, senales de alerta observadas en el lenguaje. Maximo 4 oraciones.",
  "fragmentos_relevantes": ["2 o 3 fragmentos textuales clave del usuario que justifican el triage"]
}
Responde SOLO con el JSON, sin texto adicional.
"""

sesiones = {}
reportes = {}

def generar_qr(url):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()

def generar_reporte(session_id):
    sesion = sesiones.get(session_id)
    if not sesion:
        return None

    conversacion = ""
    for msg in sesion["historial"]:
        if msg["role"] == "user":
            conversacion += f"Usuario: {msg['content']}\n"
        elif msg["role"] == "assistant":
            conversacion += f"Nemi: {msg['content']}\n"

    try:
        response = client.chat.completions.create(
            model=os.environ["AZURE_AI_AGENT_MODEL"],
            messages=[
                {"role": "system", "content": REPORTE_PROMPT},
                {"role": "user", "content": conversacion}
            ],
        )
        reporte_raw = response.choices[0].message.content.strip()
        if reporte_raw.startswith("```"):
            reporte_raw = reporte_raw.split("```")[1]
            if reporte_raw.startswith("json"):
                reporte_raw = reporte_raw[4:]
        reporte = json.loads(reporte_raw)
    except Exception:
        reporte = {"error": "No se pudo generar el reporte"}

    reporte["fecha_hora"] = sesion["inicio"].strftime("%d/%m/%Y %H:%M")
    reporte["duracion_minutos"] = round((time.time() - sesion["inicio_ts"]) / 60, 1)
    reporte["total_turnos"] = sesion["turnos"]
    reporte["session_id"] = session_id

    reportes[session_id] = reporte
    return reporte

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/sesion/<session_id>")
def ver_reporte(session_id):
    reporte = reportes.get(session_id)
    if not reporte:
        return "<h2>Reporte no encontrado</h2>", 404

    r = reporte
    dominios_sec = ", ".join(r.get("dominios_secundarios", [])) or "Ninguno"
    recursos = "<br>• ".join(r.get("recursos_proporcionados", [])) or "Ninguno"
    fragmentos = "<br>".join([f'"{f}"' for f in r.get("fragmentos_relevantes", [])]) or "Ninguno"
    riesgo = r.get("nivel_riesgo", "")
    colores = {"bajo": "#34d399", "medio": "#fbbf24", "alto": "#f97316", "crisis": "#ef4444"}
    color_riesgo = colores.get(riesgo, "#e0e0e0")

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte Nemi</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; padding: 40px; max-width: 700px; margin: auto; }}
            h1 {{ color: #a78bfa; margin-bottom: 24px; }}
            .campo {{ margin-bottom: 18px; }}
            .label {{ color: #a78bfa; font-size: 0.8rem; text-transform: uppercase; font-weight: bold; }}
            .valor {{ margin-top: 6px; line-height: 1.6; }}
            .riesgo {{ font-weight: bold; color: {color_riesgo}; font-size: 1.1rem; }}
        </style>
    </head>
    <body>
        <h1>🫧 Reporte de Sesion Nemi</h1>
        <div class="campo"><div class="label">Fecha y hora</div><div class="valor">{r.get("fecha_hora")} — Duración: {r.get("duracion_minutos")} min — Turnos: {r.get("total_turnos")}</div></div>
        <div class="campo"><div class="label">Dominio principal</div><div class="valor">{r.get("dominio_principal")}</div></div>
        <div class="campo"><div class="label">Dominios secundarios</div><div class="valor">{dominios_sec}</div></div>
        <div class="campo"><div class="label">Nivel de riesgo</div><div class="valor riesgo">{riesgo.upper()}</div></div>
        <div class="campo"><div class="label">Motivo de consulta</div><div class="valor">{r.get("motivo_consulta")}</div></div>
        <div class="campo"><div class="label">Recursos proporcionados</div><div class="valor">• {recursos}</div></div>
        <div class="campo"><div class="label">Formulacion clinica</div><div class="valor">{r.get("formulacion_clinica")}</div></div>
        <div class="campo"><div class="label">Fragmentos relevantes</div><div class="valor">{fragmentos}</div></div>
    </body>
    </html>
    """

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    session_id = data.get("session_id", "default")
    user_message = data.get("message", "")

    if session_id not in sesiones:
        sesiones[session_id] = {
            "historial": [{"role": "system", "content": SYSTEM_PROMPT}],
            "turnos": 0,
            "inicio": datetime.now(),
            "inicio_ts": time.time(),
            "ultimo_mensaje": time.time(),
            "cerrada": False,
        }

    sesion = sesiones[session_id]

    if sesion["cerrada"]:
        return jsonify({"response": "Esta sesion ha terminado.", "cerrada": True})

    sesion["ultimo_mensaje"] = time.time()
    sesion["turnos"] += 1
    sesion["historial"].append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=os.environ["AZURE_AI_AGENT_MODEL"],
            messages=sesion["historial"],
        )
        respuesta = response.choices[0].message.content
    except Exception as e:
        if "content_filter" in str(e) or "ResponsibleAIPolicyViolation" in str(e):
            respuesta = (
                "Lo que me dices es importante y me importa que estes bien. "
                "Ahorita lo mas importante es que hables con alguien que te pueda ayudar de verdad. "
                "Llama al 800 290 0024, es la Linea de la Vida, es gratis, las 24 horas. "
                "Si hay peligro fisico inmediato, marca 911."
            )
        else:
            return jsonify({"response": "Hubo un error. Intenta de nuevo."}), 500

    sesion["historial"].append({"role": "assistant", "content": respuesta})

    cerrar = sesion["turnos"] >= 15
    if cerrar:
        sesion["cerrada"] = True

    return jsonify({
        "response": respuesta,
        "turnos": sesion["turnos"],
        "cerrada": cerrar,
    })

@app.route("/inactividad", methods=["POST"])
def inactividad():
    data = request.json
    session_id = data.get("session_id")
    tipo = data.get("tipo")
    sesion = sesiones.get(session_id)

    if not sesion or sesion["cerrada"]:
        return jsonify({"ok": False})

    if tipo == "aviso":
        return jsonify({"ok": True, "message": "Sigues ahi? Estoy aqui si me necesitas."})

    if tipo == "cierre":
        sesion["cerrada"] = True
        return jsonify({"ok": True, "cerrada": True})

    return jsonify({"ok": False})

@app.route("/reporte", methods=["POST"])
def reporte():
    data = request.json
    session_id = data.get("session_id")
    r = generar_reporte(session_id)
    if not r:
        return jsonify({"error": "Sesion no encontrada"}), 404

    url = f"http://127.0.0.1:5000/sesion/{session_id}"
    qr_base64 = generar_qr(url)

    return jsonify({**r, "qr": qr_base64, "url_reporte": url})

if __name__ == "__main__":
    app.run(debug=True)