import os
import json
import amaas.grpc

SCANNER_HOST = os.getenv(
    "FILE_SECURITY_HOST",
    "my-release-visionone-filesecurity-scanner:50051"
)

FILE_SECURITY_API_KEY = os.getenv("FILE_SECURITY_API_KEY")

# -------------------------------------------------------------------
# Este módulo encapsula la integración técnica con Trend File Security.
# El resto del backend no debería conocer detalles de:
# - host gRPC
# - init del canal
# - scan_file del SDK
# - parseo del resultado raw
#
# Este servicio es invocado desde:
# - storage.py -> scan_file(...)
# -------------------------------------------------------------------

def scan_file(file_path: str) -> dict:

 # -------------------------------------------------------------------
    # Llamada real al scanner gRPC desplegado en Kubernetes.
    #
    # Flujo:
    # 1. init del canal gRPC
    # 2. scan_file(...) del SDK
    # 3. cierre del canal
    # 4. parseo del resultado
    #
    # Si algo falla, se devuelve status=error para que storage.py decida
    # dejar el fichero en incoming.
    # -------------------------------------------------------------------

    print(f"[FILE_SECURITY] scan_file() llamado con: {file_path}")
    print(f"[FILE_SECURITY] Scanner host: {SCANNER_HOST}")

    try:
        channel = amaas.grpc.init(
            SCANNER_HOST,
            api_key=FILE_SECURITY_API_KEY,
            enable_tls=False,
        )

        result = amaas.grpc.scan_file(
            channel,
            file_path,
            verbose=True
        )

        amaas.grpc.quit(channel)

        print(f"[FILE_SECURITY] Resultado raw SDK: {result}")


         # -------------------------------------------------------------------
        # El SDK devuelve texto. En el flujo real esperamos JSON serializado.
        # Si se puede parsear, devolvemos el diccionario completo.
        # Si no, devolvemos un wrapper indicando raw_result.
        # -------------------------------------------------------------------
        try:
            parsed = json.loads(result)
            print(f"[FILE_SECURITY] Resultado parseado JSON: {parsed}")
            return parsed
        except Exception:
            return {
                "status": "raw_result",
                "details": result
            }

    except Exception as e:
        print(f"[FILE_SECURITY] ERROR SDK: {str(e)}")
        return {
            "status": "error",
            "details": str(e)
        }