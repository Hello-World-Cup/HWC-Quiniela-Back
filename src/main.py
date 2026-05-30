from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.admin.routers import router as admin_router
from src.auth.routers import router as auth_router
from src.leaderboard.routers import router as leaderboard_router
from src.matches.routers import router as matches_router
from src.predictions.routers import router as predictions_router
from src.teams.routers import router as teams_router
from src.users.routers import router as users_router

DESCRIPTION = """
## HWC Quiniela API

Backend para la quiniela del **Mundial FIFA 2026**. Permite a los usuarios registrarse vía Google,
hacer pronósticos de partidos y ver la tabla de posiciones en tiempo real.

### Flujo de autenticación

1. El frontend obtiene un **Google ID Token** via NextAuth.js
2. Envía ese token a `POST /auth/google`
3. El backend valida el token y devuelve un **JWT propio**
4. Ese JWT se envía como `Authorization: Bearer <token>` en las rutas protegidas

### Sistema de puntos

| Resultado | Puntos |
|-----------|--------|
| Marcador exacto | 3 pts |
| Resultado correcto (G/E/P) | 1 pt |
| Incorrecto | 0 pts |
"""

TAGS_METADATA = [
    {
        "name": "auth",
        "description": "Autenticación con Google OAuth2. Devuelve un JWT para usar en el resto de endpoints.",
    },
    {
        "name": "matches",
        "description": "Consulta de partidos del Mundial 2026. Soporta filtros por fase, grupo, fechas y estado.",
    },
    {
        "name": "teams",
        "description": "Información de los 48 equipos participantes. Los IDs son códigos ISO alpha-2 (ej: `mx`, `ar`, `gb-eng`).",
    },
    {
        "name": "predictions",
        "description": "Pronósticos de marcador. Un usuario puede crear o actualizar su pronóstico hasta que cierre el plazo del partido.",
    },
    {
        "name": "leaderboard",
        "description": "Tabla de posiciones global. Se actualiza cuando un partido es finalizado por el admin.",
    },
    {
        "name": "users",
        "description": "Consulta de pronósticos por usuario (útil para ver el detalle de otro participante).",
    },
    {
        "name": "admin",
        "description": "Endpoints de administración. Permiten finalizar partidos y disparar el cálculo de puntos. Requieren autenticación.",
    },
    {
        "name": "health",
        "description": "Estado del servicio.",
    },
]

app = FastAPI(
    title="HWC Quiniela API",
    description=DESCRIPTION,
    version="0.2.0",
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "HWC Quiniela",
        "email": "jg@plusteam.tech",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(matches_router)
app.include_router(predictions_router)
app.include_router(teams_router)
app.include_router(leaderboard_router)
app.include_router(users_router)
app.include_router(admin_router)


@app.get("/health", tags=["health"], summary="Health check")
async def health_check() -> dict[str, str]:
    """Verifica que el servidor esté en línea."""
    return {"status": "ok"}
