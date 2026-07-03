import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# For Day 1, use a local PostgreSQL connection string. 
# (Tomorrow this will pull securely via environment variables or AWS Secrets)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/scribe_db")

# Setup the SQLAlchemy engine with explicit connection pooling (QueuePool)
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Keeps up to 20 permanent connections open
    max_overflow=10,       # Allows up to 10 bursting connections under heavy load
    pool_timeout=30,       # Seconds to wait for an available connection before throwing an error
    pool_recycle=1800      # Recycle connections after 30 minutes to avoid stale links
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency provider to get a DB session per request and return it safely to the pool
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
