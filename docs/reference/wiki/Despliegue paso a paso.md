> Referencia histórica importada. Para operar la demo, consulta [el recorrido vigente](../../overview/OPERACION_DEMO.md).

# Guía paso a paso de integración y despliegue en código
## AI Guard + File Security en AI-untamiento de Trendo

## Objetivo de esta página

Esta página explica la integración **de forma procedural**, siguiendo el recorrido real que haría alguien que quiera reproducir este patrón en otro proyecto.

La idea es responder a preguntas de este tipo:

- “¿En qué fichero empiezo?”
- “¿Qué línea tengo que añadir?”
- “¿Qué función llama a cuál?”
- “¿Dónde se mete AI Guard?”
- “¿Dónde se mete File Security?”
- “¿Qué variables necesita cada parte?”
- “¿Qué manifiestos Kubernetes hay que tocar?”

Esta página no busca solo describir arquitectura, sino enseñar **cómo se montó**.

---

# Índice de integración

1. Integración de AI Guard en código
2. Integración de File Security en código
3. Variables de entorno necesarias
4. Despliegue Kubernetes asociado
5. Secuencia completa de ejecución

---

# 1. Integración de AI Guard en código

## 1.1 Punto de entrada funcional

La integración de AI Guard empieza realmente en el endpoint de chat.

Fichero:

- `portal-backend/app/routes/chat.py`

Aquí es donde se recibe el mensaje del usuario y donde se decide el flujo:

- validar prompt
- llamar al modelo
- validar respuesta
- devolver resultado

---

## 1.2 Estructura del endpoint de chat

El endpoint parte de una estructura como esta:

```python
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.chatbot import get_ai_reply
from app.services.ai_guard import inspect_prompt, inspect_output

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(request: ChatRequest):
    reply = get_ai_reply(request.message)
    return {"reply": reply}

Ese sería el punto de partida “sin seguridad”.

⸻

## 1.3 Qué hay que añadir en chat.py

La integración correcta consiste en envolver la llamada al modelo con dos validaciones:
	•	una antes de llamar al modelo
	•	otra después

La estructura final debería parecerse a esto:
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.chatbot import get_ai_reply
from app.services.ai_guard import inspect_prompt, inspect_output

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(request: ChatRequest):
    prompt_check = inspect_prompt(request.message)

    if not prompt_check["allowed"]:
        return {
            "reply": "Solicitud bloqueada por Trend AI Guard.",
            "guard_action": "blocked_input",
            "guard_reason": prompt_check["reason"],
            "guard_source": prompt_check["source"],
            "prompt_guard_result": prompt_check["trend_result"],
            "output_guard_result": None,
        }

    reply = get_ai_reply(request.message)

    output_check = inspect_output(reply)

    if not output_check["allowed"]:
        return {
            "reply": "La respuesta generada ha sido bloqueada por Trend AI Guard.",
            "guard_action": "blocked_output",
            "guard_reason": output_check["reason"],
            "guard_source": output_check["source"],
            "prompt_guard_result": prompt_check["trend_result"],
            "output_guard_result": output_check["trend_result"],
        }

    return {
        "reply": reply,
        "guard_action": "allowed",
        "guard_reason": None,
        "guard_source": "trend_ai_guard",
        "prompt_guard_result": prompt_check["trend_result"],
        "output_guard_result": output_check["trend_result"],
    }

1.4 Qué hace chat.py realmente

Este fichero no habla directamente con Trend ni directamente con OpenAI.

Su función es orquestar.

El orden exacto de llamadas es:
	1.	inspect_prompt(request.message)
	2.	si está permitido -> get_ai_reply(request.message)
	3.	luego -> inspect_output(reply)
	4.	luego devuelve respuesta o bloqueo

Es decir:
chat.py
 ├─ inspect_prompt(...)
 │   └─ ai_guard.py
 ├─ get_ai_reply(...)
 │   └─ chatbot.py
 └─ inspect_output(...)
     └─ ai_guard.py

## 1.5 Fichero donde vive la integración con Trend AI Guard

Fichero:
	•	portal-backend/app/services/ai_guard.py

Este es el módulo que encapsula la llamada real al endpoint de Trend.

Aquí se implementan normalmente tres funciones:
	•	call_trend_ai_guard(...)
	•	inspect_prompt(...)
	•	inspect_output(...)

⸻

## 1.6 Estructura recomendada de ai_guard.py

Una implementación típica queda así:
import os
import requests

TREND_API_KEY = os.getenv("TREND_API_KEY", "")
TREND_AI_URL = os.getenv(
    "TREND_AI_URL",
    "https://api.eu.xdr.trendmicro.com/v3.0/aiSecurity/applyGuardrails"
)
TREND_AI_APP_NAME = os.getenv("TREND_AI_APP_NAME", "ai-untamiento-trendo")


def call_trend_ai_guard(text: str, direction: str) -> dict:
    headers = {
        "Authorization": f"Bearer {TREND_API_KEY}",
        "Content-Type": "application/json",
        "TMV1-Application-Name": TREND_AI_APP_NAME,
        "Prefer": "return=representation",
    }

    payload = {
        "prompt": text
    }

    response = requests.post(
        TREND_AI_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def inspect_prompt(text: str) -> dict:
    try:
        result = call_trend_ai_guard(text, "input")
        action = result.get("action", "Allow")
        reasons = result.get("reasons", [])

        if action == "Block":
            return {
                "allowed": False,
                "reason": ", ".join(reasons) if reasons else "Blocked by Trend AI Guard",
                "source": "trend_ai_guard",
                "trend_result": {"status": "ok", "result": result},
            }

        return {
            "allowed": True,
            "reason": None,
            "source": "trend_ai_guard",
            "trend_result": {"status": "ok", "result": result},
        }

    except Exception as e:
        return {
            "allowed": True,
            "reason": None,
            "source": "trend_unavailable",
            "trend_result": {"status": "error", "details": str(e)},
        }


def inspect_output(text: str) -> dict:
    try:
        result = call_trend_ai_guard(text, "output")
        action = result.get("action", "Allow")
        reasons = result.get("reasons", [])

        if action == "Block":
            return {
                "allowed": False,
                "reason": ", ".join(reasons) if reasons else "Blocked by Trend AI Guard",
                "source": "trend_ai_guard",
                "trend_result": {"status": "ok", "result": result},
            }

        return {
            "allowed": True,
            "reason": None,
            "source": "trend_ai_guard",
            "trend_result": {"status": "ok", "result": result},
        }

    except Exception as e:
        return {
            "allowed": True,
            "reason": None,
            "source": "trend_unavailable",
            "trend_result": {"status": "error", "details": str(e)},
        }

## 1.7 Qué llamadas se producen dentro de AI Guard

La cadena real es esta:
chat.py
 ├─ inspect_prompt(text)
 │   └─ call_trend_ai_guard(text, "input")
 │       └─ requests.post(TREND_AI_URL, ...)
 │
 └─ inspect_output(reply)
     └─ call_trend_ai_guard(reply, "output")
         └─ requests.post(TREND_AI_URL, ...)

Es importante entender que:
	•	chat.py no construye headers
	•	chat.py no conoce el endpoint de Trend
	•	chat.py no parsea JSON de Trend

Todo eso queda encapsulado en ai_guard.py

## 1.8 Dónde se llama al modelo LLM

Fichero:
	•	portal-backend/app/services/chatbot.py

Este fichero encapsula la llamada al proveedor del modelo.

Ejemplo típico:
import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

client = OpenAI(api_key=OPENAI_API_KEY)


def get_ai_reply(message: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Eres el asistente virtual del AI-untamiento de Trendo."
            },
            {
                "role": "user",
                "content": message
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content

## 1.9 Secuencia completa de AI Guard + modelo
Frontend
 └─ POST /api/chat

chat.py
 ├─ inspect_prompt()
 │   └─ ai_guard.py
 │       └─ Trend AI Guard API
 │
 ├─ get_ai_reply()
 │   └─ chatbot.py
 │       └─ OpenAI API
 │
 └─ inspect_output()
     └─ ai_guard.py
         └─ Trend AI Guard API

Ese es el patrón reutilizable.

## 2. Integración de File Security en código

## 2.1 Punto de entrada funcional

La integración de File Security empieza en el endpoint de subida de archivos.

Fichero:
	•	portal-backend/app/routes/files.py

⸻

## 2.2 Estructura del endpoint de subida

La ruta se apoya normalmente en esta estructura:

from fastapi import APIRouter, UploadFile, File
from app.services.storage import store_and_classify_file

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    result = store_and_classify_file(file)

    return {
        "message": "Archivo procesado correctamente",
        "filename": result["filename"],
        "verdict": result["verdict"],
        "final_path": result["final_path"],
    }
Este endpoint no hace el scan directamente. Solo delega.

## 2.3 Qué hace realmente files.py

Cadena de llamadas:
files.py
 └─ store_and_classify_file(file)
     └─ storage.py

El endpoint solo:
	•	recibe el archivo
	•	lo entrega a la capa de negocio
	•	devuelve el resultado al frontend

⸻

## 2.4 Fichero de negocio documental

Fichero:
	•	portal-backend/app/services/storage.py

Este fichero es muy importante porque traduce el resultado del scanner en una acción de negocio.

⸻

## 2.5 Estructura de storage.py

Ejemplo representativo:
import os
import shutil
from pathlib import Path
from app.services.file_security import scan_file

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))


def store_and_classify_file(file) -> dict:
    incoming_dir = UPLOAD_DIR / "incoming"
    clean_dir = UPLOAD_DIR / "clean"
    quarantine_dir = UPLOAD_DIR / "quarantine"

    incoming_dir.mkdir(parents=True, exist_ok=True)
    clean_dir.mkdir(parents=True, exist_ok=True)
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    incoming_path = incoming_dir / file.filename

    with open(incoming_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    scan_result = scan_file(str(incoming_path))

    verdict = scan_result.get("status", "error")

    if verdict == "clean":
        final_path = clean_dir / file.filename
        shutil.move(str(incoming_path), str(final_path))
    elif verdict == "malicious":
        final_path = quarantine_dir / file.filename
        shutil.move(str(incoming_path), str(final_path))
    else:
        final_path = incoming_path

    return {
        "filename": file.filename,
        "verdict": verdict,
        "final_path": str(final_path),
        "scan_id": scan_result.get("scan_id"),
        "scanner_version": scan_result.get("scanner_version"),
        "file_sha1": scan_result.get("file_sha1"),
        "file_sha256": scan_result.get("file_sha256"),
        "file_type": scan_result.get("file_type"),
        "malware_count": scan_result.get("malware_count"),
        "malware": scan_result.get("malware"),
        "scan_error": scan_result.get("details"),
        "elapsed_time": scan_result.get("elapsed_time"),
        "data_source": scan_result.get("data_source"),
        "app_name": scan_result.get("app_name"),
    }

## 2.6 Qué llamadas se producen dentro de storage

La cadena real es esta:
files.py
 └─ store_and_classify_file(file)
     ├─ guardar fichero en incoming/
     ├─ scan_file(path)
     │   └─ file_security.py
     ├─ interpretar status
     ├─ mover fichero
     └─ devolver resultado

Aquí se ve muy bien la separación de responsabilidades:
	•	storage.py decide qué hacer con el fichero
	•	file_security.py sabe hablar con el scanner

⸻

## 2.7 Fichero donde vive la integración técnica con Trend File Security

Fichero:
	•	portal-backend/app/services/file_security.py

Este es el equivalente de ai_guard.py, pero para archivos.

Su responsabilidad es:
	•	leer configuración
	•	abrir la conexión al scanner
	•	ejecutar el scan
	•	parsear la respuesta

⸻

## 2.8 Estructura de file_security.py

Ejemplo representativo del patrón que se montó:
import os
import json
import amaas.grpc

FILE_SECURITY_API_KEY = os.getenv("FILE_SECURITY_API_KEY", "")
FILE_SECURITY_HOST = os.getenv("FILE_SECURITY_HOST", "")


def scan_file(file_path: str) -> dict:
    try:
        channel = amaas.grpc.init(
            host=FILE_SECURITY_HOST,
            api_key=FILE_SECURITY_API_KEY,
            enable_tls=False
        )

        raw_result = amaas.grpc.scan_file(channel, file_path)
        amaas.grpc.quit(channel)

        result = json.loads(raw_result)

        atse = result.get("result", {}).get("atse", {})
        malware_count = atse.get("malwareCount", 0)
        malware = atse.get("malware")
        file_type = atse.get("fileTypeName")

        status = "clean"
        if malware_count and malware_count > 0:
            status = "malicious"

        return {
            "status": status,
            "scan_id": result.get("scanId"),
            "scanner_version": result.get("scannerVersion"),
            "file_sha1": result.get("fileSHA1"),
            "file_sha256": result.get("fileSHA256"),
            "file_type": file_type,
            "malware_count": malware_count,
            "malware": malware,
            "elapsed_time": atse.get("elapsedTime"),
            "data_source": result.get("dataSource"),
            "app_name": result.get("appName"),
        }

    except Exception as e:
        return {
            "status": "error",
            "details": str(e),
        }

## 2.9 Qué llamadas se producen dentro de File Security

storage.py
 └─ scan_file(file_path)
     └─ file_security.py
         ├─ amaas.grpc.init(...)
         ├─ amaas.grpc.scan_file(...)
         ├─ json.loads(...)
         └─ return resultado normalizado
De nuevo, el patrón es el mismo:
	•	storage.py no conoce gRPC
	•	storage.py no conoce amaas.grpc
	•	storage.py solo sabe interpretar un resultado normalizado

## 2.10 Secuencia completa de File Security

Frontend
 └─ POST /api/files/upload

files.py
 └─ store_and_classify_file(file)
     └─ storage.py
         ├─ guardar en incoming/
         ├─ scan_file(path)
         │   └─ file_security.py
         │       └─ amaas.grpc -> scanner
         ├─ mover a clean/quarantine/incoming
         └─ devolver resultado

Ese es el patrón documental reutilizable.

⸻

## 3. Variables de entorno necesarias

## 3.1 Para AI Guard

Usadas en ai_guard.py:
	•	TREND_API_KEY
	•	TREND_AI_URL
	•	TREND_AI_APP_NAME

## 3.2 Para OpenAI

Usadas en chatbot.py:
	•	OPENAI_API_KEY
	•	opcionalmente OPENAI_MODEL

## 3.3 Para File Security

Usadas en file_security.py:
	•	FILE_SECURITY_API_KEY
	•	FILE_SECURITY_HOST

## 3.4 Para almacenamiento

Usadas en storage.py:
	•	UPLOAD_DIR

⸻

## 4. Cómo se inyectan estas variables en Kubernetes

## 4.1 Backend deployment

Fichero:
	•	k8s/backend.yaml

Ahí se define la inyección de variables al contenedor backend.

Ejemplo del bloque relevante:

env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: trendo-secret
        key: OPENAI_API_KEY

  - name: UPLOAD_DIR
    value: /data/uploads

  - name: FILE_SECURITY_API_KEY
    valueFrom:
      secretKeyRef:
        name: trendo-file-security
        key: FILE_SECURITY_API_KEY

  - name: FILE_SECURITY_HOST
    valueFrom:
      secretKeyRef:
        name: trendo-file-security
        key: FILE_SECURITY_HOST

  - name: TREND_API_KEY
    valueFrom:
      secretKeyRef:
        name: trendo-ai
        key: TREND_API_KEY

  - name: TREND_AI_URL
    value: https://api.eu.xdr.trendmicro.com/v3.0/aiSecurity/applyGuardrails

  - name: TREND_AI_APP_NAME
    value: ai-untamiento-trendo

## 4.2 Qué significa esto a nivel software

Esto conecta la infraestructura con el código:
	•	backend.yaml inyecta la variable
	•	ai_guard.py, chatbot.py, file_security.py, storage.py la leen con os.getenv(...)

Es decir:
k8s/backend.yaml
 └─ env vars
     └─ services/*.py

## 5. Cómo se despliega File Security como infraestructura

## 5.1 No vive dentro del backend

Esto es importante:

AI Guard se integra por llamadas REST desde el backend.

Pero File Security no.

File Security se despliega como infraestructura aparte en Kubernetes y el backend solo consume ese servicio.

⸻

## 5.2 Secrets de File Security

Generados localmente y aplicados en el namespace:
	•	visionone-filesecurity

Secrets críticos:
	•	token-secret
	•	device-token-secret

El primero contiene el registration token.

⸻

## 5.3 Helm release

Se instala con:
helm upgrade --install my-release visionone-filesecurity/visionone-filesecurity -n visionone-filesecurity

Esto crea, entre otros:
	•	scanner
	•	management-service
	•	backend-communicator
	•	scan-cache

⸻

## 5.4 Cómo consume eso el backend

Una vez desplegado el scanner, el backend no necesita conocer Helm ni el chart.

Solo necesita conocer:
	•	FILE_SECURITY_HOST
	•	FILE_SECURITY_API_KEY

y a partir de ahí file_security.py puede hablar con el scanner.

⸻

## 6. Secuencia completa, de extremo a extremo

## 6.1 Chat
App.jsx
 └─ fetch("/api/chat")

chat.py
 ├─ inspect_prompt()
 │   └─ ai_guard.py
 │       └─ Trend AI Guard REST
 ├─ get_ai_reply()
 │   └─ chatbot.py
 │       └─ OpenAI
 └─ inspect_output()
     └─ ai_guard.py
         └─ Trend AI Guard REST

## 6.2 Subida de archivos
App.jsx
 └─ fetch("/api/files/upload")

files.py
 └─ store_and_classify_file()
     └─ storage.py
         ├─ guardar en incoming
         ├─ scan_file()
         │   └─ file_security.py
         │       └─ amaas.grpc -> scanner
         ├─ mover fichero
         └─ devolver resultado

## 7. Qué tocarías en un cliente

Para reusar AI Guard

Tocarías:
	•	chat.py
	•	ai_guard.py
	•	chatbot.py

Para reusar File Security

Tocarías:
	•	files.py
	•	storage.py
	•	file_security.py

Para reusar despliegue

Tocarías:
	•	k8s/backend.yaml
	•	secrets
	•	Helm release / namespace de File Security

⸻

## 8. Idea clave final

La forma en que se ha montado esta demo sigue una regla muy útil:
	•	las rutas reciben
	•	los servicios encapsulan
	•	Kubernetes inyecta configuración
	•	los componentes externos hacen el trabajo especializado

En otras palabras:
	•	chat.py y files.py orquestan
	•	ai_guard.py, chatbot.py, file_security.py, storage.py implementan la lógica especializada
	•	backend.yaml conecta infraestructura y software
	•	Helm despliega File Security fuera del backend

Eso es exactamente lo que hace que esta demo sirva como blueprint reutilizable y no como una simple PoC improvisada.
