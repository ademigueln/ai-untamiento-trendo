from pathlib import Path

DATA_DIR = Path("app/data")


def load_document(filename: str) -> str:
    path = DATA_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def get_relevant_context(user_message: str) -> str:
    text = user_message.lower()

    context_parts = []

    if any(word in text for word in ["empadron", "padron", "domicilio"]):
        context_parts.append(load_document("padron.txt"))

    if any(word in text for word in ["licencia", "obra", "urban", "reforma"]):
        context_parts.append(load_document("licencias.txt"))

    if any(word in text for word in ["ayuda", "subvención", "subvencion", "energética", "energetica"]):
        context_parts.append(load_document("ayudas.txt"))

    # Siempre añadimos contexto general
    context_parts.append(load_document("tramites_generales.txt"))

    return "\n\n".join(part for part in context_parts if part.strip())