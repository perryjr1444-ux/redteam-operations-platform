"""Test database models."""

import pytest
from app import models


def test_template_model(db_session, sample_template):
    """Test Template model creation and retrieval."""
    template = models.Template(**sample_template)
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)

    assert template.id is not None
    assert template.template_id == sample_template["template_id"]
    assert template.name == sample_template["name"]


def test_exercise_model(db_session, sample_exercise):
    """Test Exercise model creation and retrieval."""
    exercise = models.Exercise(**sample_exercise)
    db_session.add(exercise)
    db_session.commit()
    db_session.refresh(exercise)

    assert exercise.id is not None
    assert exercise.exercise_id == sample_exercise["exercise_id"]
    assert exercise.template == sample_exercise["template"]
    assert exercise.state == sample_exercise["state"]
    assert exercise.progress == sample_exercise["progress"]


def test_template_unique_constraint(db_session, sample_template):
    """Test template_id uniqueness constraint."""
    template1 = models.Template(**sample_template)
    db_session.add(template1)
    db_session.commit()

    # Try to create duplicate
    template2 = models.Template(**sample_template)
    db_session.add(template2)

    with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
        db_session.commit()


def test_exercise_unique_constraint(db_session, sample_exercise):
    """Test exercise_id uniqueness constraint."""
    exercise1 = models.Exercise(**sample_exercise)
    db_session.add(exercise1)
    db_session.commit()

    # Try to create duplicate
    exercise2 = models.Exercise(**sample_exercise)
    db_session.add(exercise2)

    with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
        db_session.commit()
