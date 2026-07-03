import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Defaulting to local Postgres, easily overridden by environment variables in Docker/AWS
DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

# Configure explicit connection pooling to fulfill architectural criteria
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Maintain up to 10 persistent connections
    max_overflow=20,       # Allow bursting up to 20 additional connections under load
    pool_timeout=30,       # Seconds to wait for a free connection before throwing an error
    pool_recycle=1800,     # Recycle connections after 30 minutes to prevent staleness
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to yield database sessions safely to API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
