"""Genera manifiestos JSON (admitidos por kubectl) sin interpolar YAML."""
import json
import os
import sys
from pathlib import Path


def secret(name, namespace, data):
    return {
        "apiVersion": "v1", "kind": "Secret",
        "metadata": {"name": name, "namespace": namespace},
        "type": "Opaque", "stringData": data,
    }


def write_manifest(path, items):
    # 0600 incluso si el proceso invocante no ha fijado umask.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump({"apiVersion": "v1", "kind": "List", "items": items}, stream)


def main():
    directory, app_namespace, fs_namespace, initialize_device = sys.argv[1:]
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    application = [
        secret("trendo-secret", app_namespace, {"OPENAI_API_KEY": os.environ["OPENAI_API_KEY"]}),
        secret("trendo-ai", app_namespace, {
            key: os.environ[key] for key in ("TREND_API_KEY", "TREND_AI_URL", "TREND_AI_APP_NAME")
        }),
        secret("trendo-file-security", app_namespace, {
            key: os.environ[key] for key in ("FILE_SECURITY_API_KEY", "FILE_SECURITY_HOST")
        }),
    ]
    file_security = [secret("token-secret", fs_namespace, {
        "registration-token": os.environ["FILE_SECURITY_REGISTRATION_TOKEN"],
    })]
    if initialize_device == "yes":
        file_security.append(secret("device-token-secret", fs_namespace, {}))
    write_manifest(target / "application.json", application)
    write_manifest(target / "file-security.json", file_security)


if __name__ == "__main__":
    main()
