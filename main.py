from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.middleware.auth_middleware import verify_token_middleware

from src.api import routeproblem, routesubmission
from src.api.routeuser import router as user_router
from src.api.routelanguage import router as language_router
from src.api.admin import routeproblem as admin_routeproblem
from src.api.admin import routeuser as admin_routeuser
from src.api.admin import routesubmission as admin_routesubmission
from src.core.db_postgres import engine
from src.models.baseModel import Base

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Judge Microservice",
    description="Microservicio para evaluación de código usando Judge0",
    version="1.0.0"
)

# Configurar CORS - Actualizado para incluir explícitamente el origen del frontend
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if hasattr(settings, 'CORS_ORIGINS'):
    if isinstance(settings.CORS_ORIGINS, list):
        origins.extend(settings.CORS_ORIGINS)
    else:
        origins.append(settings.CORS_ORIGINS)

# IMPORTANTE: Mover el middleware CORS antes del middleware de autenticación
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Lista actualizada de orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Exponer todos los encabezados en la respuesta
)

# Incluir routers
app.include_router(routeproblem.router, prefix="/api/problems", tags=["problems"])
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(routesubmission.router, prefix="/api/submissions", tags=["submissions"])
app.include_router(language_router, prefix="/api/languages", tags=["languages"])  # Añadir el nuevo router

# Incluir routers de administración
app.include_router(admin_routeuser.router, tags=["admin", "users"])
app.include_router(admin_routeproblem.router, tags=["admin", "problems"])
app.include_router(admin_routesubmission.router, tags=["admin", "submissions"])

# Registramos el middleware de autenticación en todas las peticiones HTTP
# IMPORTANTE: Mover esto después de la configuración CORS
app.middleware("http")(verify_token_middleware)


@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Judge Microservice API",
        "docs": "/docs",
        "status": "online"
    }

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
