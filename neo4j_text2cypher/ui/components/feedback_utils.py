# feedback_utils.py
from datetime import datetime
from neo4j_text2cypher.ui.components.feedback_model import SessionLocal, CypherFeedback

def save_feedback(question: str, cypher: str, response: str, validation: str, reason: str = None) -> None:
    with SessionLocal() as session:
        feedback = CypherFeedback(
            question=question,
            cypher=cypher,
            response=response,
            validation=validation,
            feedback_reason=reason,
            timestamp=datetime.utcnow()
        )
        session.add(feedback)
        session.commit()
