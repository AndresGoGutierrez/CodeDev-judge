from src.core.db_postgres import engine
from src.models.baseModel import Base

# Import the models so that SQLAlchemy registers them
from src.models.problemModel import Problem
from src.models.testcaseModel import TestCase
from src.models.submissionModel import Submission
from src.models.testresultModel import TestResult

# Create the tables in the database
Base.metadata.create_all(engine)
