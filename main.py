from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import routeproblem, routesubmission
from src.core.config import settings
from src.core.db_postgres import engine
from src.models.baseModel import Base

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Judge Microservice",
    description="Microservicio para evaluación de código usando Judge0",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(routeproblem.router, prefix="/api/problems", tags=["problems"])
app.include_router(routesubmission.router, prefix="/api/submissions", tags=["submissions"])

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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)