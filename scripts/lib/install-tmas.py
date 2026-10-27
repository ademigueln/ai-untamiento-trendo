"""Instala el CLI fijado y verifica el archivo oficial antes de ejecutarlo."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://ast-cli.xdr.trendmicro.com/tmas-cli"


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def install(root=ROOT):
    pin = json.loads((root / "security/ai-scanner/tmas-cli.json").read_text())
    architecture = {"aarch64": "arm64", "AMD64": "x86_64"}.get(platform.machine(), platform.machine())
    system = platform.system() + "/" + architecture
    if system not in pin["platforms"]:
        raise RuntimeError("Plataforma no soportada por esta instalación: " + system)
    artifact = pin["platforms"][system]
    cache = root / ".runtime/ai-scanner" / pin["version"] / system.replace("/", "-")
    binary = cache / "tmas"
    stamp = cache / "installed.json"
    if binary.is_file() and stamp.is_file():
        installed = json.loads(stamp.read_text())
        if installed.get("archive_sha256") == artifact["sha256"] and installed.get("binary_sha256") == digest(binary):
            return binary
    cache.mkdir(parents=True, exist_ok=True)
    print("Instalando TMAS " + pin["version"] + " para " + system, file=sys.stderr)
    with tempfile.TemporaryDirectory(prefix="download-", dir=cache) as temporary:
        directory = Path(temporary)
        archive = directory / artifact["filename"]
        url = f"{BASE_URL}/{pin['version']}/{artifact['filename']}"
        request = urllib.request.Request(url, headers={"User-Agent": "trendo-demo-installer"})
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as stream:
            shutil.copyfileobj(response, stream, length=1024 * 1024)
        if digest(archive) != artifact["sha256"]:
            raise RuntimeError("El checksum de TMAS no coincide con la versión fijada.")
        executable = directory / "tmas"
        # Extraer únicamente el ejecutable, sin ejecutar rutas del archivo recibido.
        if archive.name.endswith(".zip"):
            with zipfile.ZipFile(archive) as package, package.open("tmas") as source, executable.open("wb") as output:
                shutil.copyfileobj(source, output)
        else:
            with tarfile.open(archive, "r:gz") as package:
                member = package.getmember("tmas")
                if not member.isfile():
                    raise RuntimeError("El archivo no contiene un ejecutable regular.")
                with package.extractfile(member) as source, executable.open("wb") as output:
                    shutil.copyfileobj(source, output)
        executable.chmod(0o755)
        os.replace(executable, binary)
        stamp.write_text(json.dumps({"archive_sha256": artifact["sha256"], "binary_sha256": digest(binary)}))
    return binary


if __name__ == "__main__":
    try:
        print(install())
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print("No se ha podido instalar TMAS: " + str(error), file=sys.stderr)
        sys.exit(1)
