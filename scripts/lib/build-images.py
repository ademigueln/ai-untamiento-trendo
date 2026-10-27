"""Construye imágenes locales y prepara manifiestos sin modificar k8s/."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def source_digest(root, entries):
    digest = hashlib.sha256()
    for entry in entries:
        source = root / entry
        paths = sorted(source.rglob("*")) if source.is_dir() else [source]
        for path in paths:
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(str(path.relative_to(root)).encode())
                digest.update(b"\0")
                digest.update(path.read_bytes())
                digest.update(b"\0")
    return digest.hexdigest()[:16]


def main():
    root = Path(sys.argv[1])
    output = root / ".runtime/manifests"
    output.mkdir(parents=True, exist_ok=True)
    images = {}
    for name, entries in (
        ("backend", ["Dockerfile", ".dockerignore", "requirements.lock", "main.py", "app"]),
        ("frontend", ["Dockerfile", ".dockerignore", "nginx.conf", "package.json", "package-lock.json", "index.html", "vite.config.js", "src", "public"]),
    ):
        context = root / f"portal-{name}"
        image = f"trendo-{name}:local-{source_digest(context, entries)}"
        exists = subprocess.run(["docker", "image", "inspect", image], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if not exists:
            subprocess.run(["docker", "build", "--pull", "--tag", image, str(context)], check=True)
        manifest = (root / "k8s" / f"{name}.yaml").read_text()
        manifest, count = re.subn(r"(?m)^(\s*image:) .+$", lambda m: f"{m[1]} {image}", manifest)
        if count != 1:
            raise ValueError(f"El manifiesto {name} debe contener una sola imagen")
        manifest = re.sub(r"(?m)^(\s*imagePullPolicy:) .+$", r"\1 Never", manifest)
        (output / f"{name}.yaml").write_text(manifest)
        images[name] = image
    (root / ".runtime/images.json").write_text(json.dumps(images, indent=2))
    print("Imágenes locales listas: " + ", ".join(images.values()))


if __name__ == "__main__":
    main()
