from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.plausibility_assessment import PlausibilityAssessment


def create_plausibility_assessment(db: Session, assessment: PlausibilityAssessment) -> PlausibilityAssessment:
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def list_plausibility_assessments(db: Session) -> list[PlausibilityAssessment]:
    statement = select(PlausibilityAssessment).order_by(PlausibilityAssessment.assessed_at.desc())
    return list(db.scalars(statement))


def get_plausibility_assessment_by_claim(db: Session, claim_id: str) -> PlausibilityAssessment | None:
    statement = select(PlausibilityAssessment).where(PlausibilityAssessment.claim_id == claim_id)
    return db.scalar(statement)
