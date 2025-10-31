"""Test CRUD operations."""

import pytest
from app import crud


def test_create_template(db_session, sample_template):
    """Test template creation."""
    template = crud.create_template(db_session, sample_template)
    assert template.template_id == sample_template["template_id"]
    assert template.name == sample_template["name"]
    assert template.id is not None


def test_get_templates(db_session, sample_template):
    """Test retrieving all templates."""
    crud.create_template(db_session, sample_template)
    templates = crud.get_templates(db_session)
    assert len(templates) >= 1
    assert templates[0].template_id == sample_template["template_id"]


def test_get_template_by_id(db_session, sample_template):
    """Test retrieving template by ID."""
    crud.create_template(db_session, sample_template)
    template = crud.get_template_by_template_id(
        db_session, sample_template["template_id"]
    )
    assert template is not None
    assert template.template_id == sample_template["template_id"]


def test_get_nonexistent_template(db_session):
    """Test retrieving nonexistent template returns None."""
    template = crud.get_template_by_template_id(db_session, "nonexistent")
    assert template is None


def test_create_exercise(db_session, sample_template, sample_exercise):
    """Test exercise creation."""
    # Create template first
    crud.create_template(db_session, sample_template)

    # Create exercise
    exercise = crud.create_exercise(db_session, sample_exercise)
    assert exercise.exercise_id == sample_exercise["exercise_id"]
    assert exercise.template == sample_exercise["template"]
    assert exercise.state == sample_exercise["state"]
    assert exercise.id is not None


def test_get_exercises(db_session, sample_template, sample_exercise):
    """Test retrieving all exercises."""
    crud.create_template(db_session, sample_template)
    crud.create_exercise(db_session, sample_exercise)

    exercises = crud.get_exercises(db_session)
    assert len(exercises) >= 1
    assert exercises[0].exercise_id == sample_exercise["exercise_id"]


def test_create_exercise_with_pagination(db_session, sample_template):
    """Test pagination of exercises."""
    crud.create_template(db_session, sample_template)

    # Create multiple exercises
    for i in range(5):
        exercise_data = {
            "exercise_id": f"ex-test-{i:03d}",
            "template": sample_template["template_id"],
            "state": "draft",
            "progress": 0.0,
            "start_date": "2025-01-01",
            "owner": "testuser",
        }
        crud.create_exercise(db_session, exercise_data)

    # Test pagination
    exercises_page1 = crud.get_exercises(db_session, skip=0, limit=2)
    exercises_page2 = crud.get_exercises(db_session, skip=2, limit=2)

    assert len(exercises_page1) == 2
    assert len(exercises_page2) == 2
    assert exercises_page1[0].exercise_id != exercises_page2[0].exercise_id
