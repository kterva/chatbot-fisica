import subprocess

from app.config import PROJECT_ROOT


def _read_version() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


# Se calcula una sola vez al arrancar el proceso (ver docs/ARCHITECTURE.md): la versión
# desplegada no cambia mientras el proceso está corriendo, así que no hace falta
# recalcularla en cada consulta.
VERSION = _read_version()
