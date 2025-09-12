# feedback_model.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# Replace these connection details for Azure, will move to .env file in future

# Customer's Azure SQL Database (comment out for local testing)
# server = 'your-server'
# database = 'database-name'
# username = 'user-name'
# password = 'password'
# connection_string = (
#     "your-connection-string"
# )

# Local SQLite for testing (use forward slashes for cross-platform compatibility)
connection_string = "sqlite:///C:/Users/Yancarlo Perez/Documents/feedback.db"
print(f"Using SQLite database at: {connection_string}")

engine = create_engine(connection_string, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CypherFeedback(Base):
    __tablename__ = 'cypher_feedback'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    cypher = Column(String)
    response = Column(String)
    validation = Column(String)  # 'correct' or 'incorrect'
    feedback_reason = Column(String, nullable=True)  # Reason for negative feedback (optional)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)
