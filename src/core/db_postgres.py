from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# Cargar variables del .env usando decouple
url = URL.create(
    drivername="postgresql",
    username=config("PG_USER"),
    password=config("PG_PASSWORD"),
    host=config("PG_HOST"),
    database=config("PG_DB"),
    port=config("PG_PORT", cast=int, default=5432)
)

# Crear motor de SQLAlchemy
engine = create_engine(url, echo=True)  # echo=True muestra las consultas en consola (útil para debug)

# Crear una fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Función para obtener la sesión (útil en FastAPI, Flask, etc.)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
