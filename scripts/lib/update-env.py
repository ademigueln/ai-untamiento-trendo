"""Actualiza una variable shell sin pasar su valor como argumento de proceso."""
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile

path = Path(sys.argv[1])
key = sys.argv[2]
if not re.fullmatch(r"[A-Z_][A-Z_0-9]*", key):
    raise ValueError("Nombre de variable no válido")
value = sys.stdin.read()
line = key + "=" + shlex.quote(value)
lines = path.read_text().splitlines()
updated = []
found = False
for original in lines:
    if original.startswith(key + "="):
        if not found:
            updated.append(line)
            found = True
    else:
        updated.append(original)
if not found:
    updated.append(line)
fd, temporary = tempfile.mkstemp(prefix=".env-update-", dir=path.parent)
try:
    with os.fdopen(fd, "w") as stream:
        stream.write("\n".join(updated) + "\n")
    os.replace(temporary, path)
finally:
    Path(temporary).unlink(missing_ok=True)
