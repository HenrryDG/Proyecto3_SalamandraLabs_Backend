import re
import unicodedata

def limpiar_texto(texto):
    """Normaliza el texto, elimina tildes y caracteres especiales."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")  # quita tildes
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)  # deja solo letras y números
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def extraer_direccion_ocr(texto):
    # Buscar línea que contenga "DIRECCIÓN" o "DIR:" (ignorando mayúsculas)
    match = re.search(r'DIRECCIÓN[:\s]*(.*)', texto, re.IGNORECASE)
    if match:
        # Tomamos solo esa línea, eliminando posibles saltos de línea
        direccion = match.group(1).split('\n')[0].strip()
        return direccion
    return ''