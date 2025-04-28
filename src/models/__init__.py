from src.core.db_postgres import engine
from src.models.baseModel import Base

# Importar los modelos para que SQLAlchemy los registre
from src.models.problemModel import Problem
from src.models.testcaseModel import TestCase
from src.models.submissionModel import Submission
from src.models.testresultModel import TestResult

# Crear las tablas en la base de datos
Base.metadata.create_all(engine)
