import os
import json
import amaas.grpc

SCANNER_HOST = os.getenv(
    "FILE_SECURITY_HOST",
    "my-release-visionone-filesecurity-scanner:50051"
)

FILE_SECURITY_API_KEY = os.getenv("FILE_SECURITY_API_KEY")


def scan_file(file_path: str) -> dict:
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

        # El SDK devuelve string; intentamos parsear JSON si aplica
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