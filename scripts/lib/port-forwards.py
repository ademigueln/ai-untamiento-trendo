"""Gestiona únicamente los port-forwards registrados por esta copia de la demo."""
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time


def process_command(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def matches(record):
    try:
        current = shlex.split(process_command(record["pid"]))
        expected = record["argv"]
        return any(Path(arg).name == "kubectl" and current[index + 1:] == expected[1:] for index, arg in enumerate(current))
    except (KeyError, ValueError, TypeError):
        return False


def stop_owned(state):
    if not state.exists():
        return
    records = json.loads(state.read_text())
    for record in records:
        if matches(record):
            os.kill(record["pid"], signal.SIGTERM)
            for _ in range(40):
                if not matches(record):
                    break
                time.sleep(0.05)
            else:
                raise RuntimeError("Un port-forward no se ha detenido; revisa su proceso antes de continuar.")
    state.unlink(missing_ok=True)


def main():
    action, directory, context, namespace, backend_port, frontend_port = sys.argv[1:]
    root = Path(directory)
    state = root / "port-forwards.json"
    stop_owned(state)
    if action == "stop":
        return
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    logs = root / "logs"
    logs.mkdir(exist_ok=True)
    records = []
    try:
        for name, remote, local in (("backend", "8007", backend_port), ("frontend", "80", frontend_port)):
            argv = ["kubectl", "--context", context, "port-forward", "-n", namespace, f"service/{name}-service", f"{local}:{remote}"]
            with (logs / f"{name}-portforward.log").open("w") as stream:
                process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            records.append({"pid": process.pid, "argv": argv})
            state.write_text(json.dumps(records))
            state.chmod(0o600)
            time.sleep(0.3)
            if process.poll() is not None:
                raise RuntimeError(f"No se ha iniciado el acceso de {name}. Revisa {logs}; un proceso antiguo puede ocupar el puerto.")
    except Exception:
        stop_owned(state)
        raise


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
