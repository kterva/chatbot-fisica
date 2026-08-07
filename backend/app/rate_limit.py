from slowapi import Limiter
from slowapi.util import get_remote_address

# Limitador in-memory por IP. El límite concreto (RATE_LIMIT en .env) se aplica con
# el decorador @limiter.limit(...) en cada endpoint. Limitación conocida: no persiste
# entre reinicios ni se comparte entre múltiples workers/instancias (ver
# docs/ARCHITECTURE.md, sección Riesgos).
limiter = Limiter(key_func=get_remote_address)
