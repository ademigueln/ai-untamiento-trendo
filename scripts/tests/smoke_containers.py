"""Prueba real de las imágenes, aislada de Kubernetes y sin credenciales."""
import json
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4


def docker(*args, **kwargs):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True, **kwargs).stdout.strip()


def main():
    root = Path(__file__).resolve().parents[2]
    images = json.loads((root / ".runtime/images.json").read_text())
    name = "trendo-test-" + uuid4().hex[:12]
    network = name + "-net"
    containers = []
    docker("network", "create", network)
    try:
        backend = docker("run", "-d", "--network", network, "--network-alias", "backend-service", "-e", "OPENAI_API_KEY=", "-e", "TREND_API_KEY=", "-e", "FILE_SECURITY_API_KEY=", "-e", "UPLOAD_DIR=/data/uploads", images["backend"])
        containers.append(backend)
        frontend = docker("run", "-d", "--network", network, images["frontend"])
        containers.append(frontend)
        last_error = None
        for _ in range(20):
            try:
                page = docker("exec", frontend, "wget", "-qO-", "http://127.0.0.1:8080/")
                assert "AI-untamiento de Trendo" in page
                result = json.loads(docker("exec", frontend, "wget", "-qO-", "http://127.0.0.1:8080/api/stats"))
                assert result["portal_status"] == "Degradado"
                ready = docker("exec", backend, "python", "-c", "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8007/health/ready').read().decode())")
                assert json.loads(ready)["status"] == "ready"
                assert docker("exec", backend, "id", "-u") != "0"
                assert docker("exec", frontend, "id", "-u") != "0"
                print("Contenedores OK: usuarios sin privilegios, persistencia escribible, frontend, proxy API y readiness.")
                return
            except (subprocess.CalledProcessError, ValueError, AssertionError) as error:
                last_error = error
                time.sleep(0.5)
        for container in containers:
            logs = subprocess.run(["docker", "logs", container], capture_output=True, text=True)
            print(logs.stdout + logs.stderr, file=sys.stderr)
        raise RuntimeError("Falló la prueba de contenedores") from last_error
    finally:
        for container in reversed(containers):
            subprocess.run(["docker", "rm", "-f", container], capture_output=True)
        subprocess.run(["docker", "network", "rm", network], capture_output=True)


if __name__ == "__main__":
    main()
