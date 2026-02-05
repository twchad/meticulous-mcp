"""Tests for profile validator."""

import json
import tempfile
from pathlib import Path

import pytest

from meticulous_mcp.profile_validator import ProfileValidationError, ProfileValidator


@pytest.fixture
def sample_schema():
    """Create a sample schema file."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "id": {"type": "string"},
            "temperature": {"type": "number", "minimum": 0, "maximum": 100},
        },
        "required": ["name", "id", "temperature"],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        schema_path = f.name
    
    # File is closed but not deleted, yield the path
    yield schema_path
    # Clean up after test
    if Path(schema_path).exists():
        Path(schema_path).unlink()


@pytest.fixture
def validator(sample_schema):
    """Create a validator instance."""
    return ProfileValidator(schema_path=sample_schema)


def test_valid_profile(validator):
    """Test validation of a valid profile."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
    }
    is_valid, errors = validator.validate(profile)
    assert is_valid
    assert len(errors) == 0


def test_invalid_profile_missing_field(validator):
    """Test validation of profile with missing required field."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        # Missing temperature
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert len(errors) > 0


def test_invalid_profile_wrong_type(validator):
    """Test validation of profile with wrong type."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": "not-a-number",  # Should be number
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert len(errors) > 0


def test_validate_and_raise_valid(validator):
    """Test validate_and_raise with valid profile."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
    }
    # Should not raise
    validator.validate_and_raise(profile)


def test_validate_and_raise_invalid(validator):
    """Test validate_and_raise with invalid profile."""
    profile = {
        "name": "Test Profile",
        # Missing required fields
    }
    with pytest.raises(ProfileValidationError) as exc_info:
        validator.validate_and_raise(profile)
    assert len(exc_info.value.errors) > 0


def test_lint_valid_profile(validator):
    """Test linting of a valid profile."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [{"name": "Stage 1", "exit_triggers": [{"type": "time", "value": 30}]}],
    }
    warnings = validator.lint(profile)
    # Should have no warnings for a well-formed profile
    assert isinstance(warnings, list)


def test_lint_profile_no_stages(validator):
    """Test linting of profile without stages."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [],
    }
    warnings = validator.lint(profile)
    assert any("no stages" in w.lower() for w in warnings)


def test_lint_profile_unusual_temperature(validator):
    """Test linting of profile with unusual temperature."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 150.0,  # Too high
    }
    warnings = validator.lint(profile)
    assert any("temperature" in w.lower() for w in warnings)


def test_validator_init_with_path(sample_schema):
    """Test validator initialization with explicit path."""
    validator = ProfileValidator(schema_path=sample_schema)
    assert validator is not None


def test_validator_init_no_schema():
    """Test validator initialization without schema file."""
    with pytest.raises(FileNotFoundError):
        ProfileValidator(schema_path="/nonexistent/path/schema.json")


def test_validation_error_message_formatting(validator):
    """Test that validation errors are properly formatted."""
    profile = {
        "name": "Test Profile",
        # Missing id and temperature
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert len(errors) > 0
    # Check that errors are formatted strings
    for error in errors:
        assert isinstance(error, str)
        assert len(error) > 0


def test_validate_multiple_errors(validator):
    """Test that multiple validation errors are collected."""
    profile = {
        "name": "Test Profile",
        # Missing id and temperature
        "temperature": "not-a-number",  # Wrong type
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert len(errors) >= 2  # At least 2 errors


def test_validate_and_raise_error_message(validator):
    """Test that validate_and_raise includes all errors in message."""
    profile = {
        "name": "Test Profile",
        # Missing id and temperature
    }
    with pytest.raises(ProfileValidationError) as exc_info:
        validator.validate_and_raise(profile)
    
    error = exc_info.value
    assert len(error.errors) > 0
    # Check that the exception message includes all errors
    assert str(error)
    assert len(str(error)) > len(error.message)  # Should include formatted errors


def test_lint_stage_no_exit_triggers(validator):
    """Test linting of stage without exit triggers."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [],  # No exit triggers
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("no exit triggers" in w.lower() for w in warnings)


def test_lint_stage_no_weight_or_time_trigger(validator):
    """Test linting of stage without weight or time triggers."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [{"type": "pressure", "value": 9.0}],  # No weight/time
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("none are weight or time-based" in w.lower() for w in warnings)


def test_lint_stage_empty_dynamics_points(validator):
    """Test linting of stage with empty dynamics points."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [], "over": "time"},
                "exit_triggers": [{"type": "time", "value": 30}],
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("empty dynamics points" in w.lower() for w in warnings)


def test_lint_stage_single_dynamics_point(validator):
    """Test linting of stage with only one dynamics point."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [{"type": "time", "value": 30}],
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("only one dynamics point" in w.lower() for w in warnings)


def test_lint_stage_invalid_dynamics_over(validator):
    """Test linting of stage with invalid dynamics.over value."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "invalid"},
                "exit_triggers": [{"type": "time", "value": 30}],
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("invalid dynamics.over" in w.lower() for w in warnings)


def test_lint_stage_invalid_type(validator):
    """Test linting of stage with invalid type."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "invalid_type",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [{"type": "time", "value": 30}],
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("invalid type" in w.lower() for w in warnings)


def test_lint_duplicate_stage_keys(validator):
    """Test linting of profile with duplicate stage keys."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [{"type": "time", "value": 30}],
            },
            {
                "name": "Stage 2",
                "key": "stage_1",  # Duplicate key
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [{"type": "time", "value": 30}],
            },
        ],
    }
    warnings = validator.lint(profile)
    assert any("duplicate key" in w.lower() for w in warnings)


def test_lint_temperature_low(validator):
    """Test linting of profile with low temperature."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 82.0,  # Low
    }
    warnings = validator.lint(profile)
    assert any("lower end" in w.lower() for w in warnings)


def test_lint_temperature_high(validator):
    """Test linting of profile with high temperature."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 97.0,  # High
    }
    warnings = validator.lint(profile)
    assert any("higher end" in w.lower() for w in warnings)


def test_lint_final_weight_low(validator):
    """Test linting of profile with low final weight."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "final_weight": 15.0,  # Low
    }
    warnings = validator.lint(profile)
    assert any("quite low" in w.lower() for w in warnings)


def test_lint_final_weight_high(validator):
    """Test linting of profile with high final weight."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "final_weight": 75.0,  # High
    }
    warnings = validator.lint(profile)
    assert any("quite high" in w.lower() for w in warnings)


def test_lint_final_weight_out_of_range(validator):
    """Test linting of profile with final weight out of typical range."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "final_weight": 150.0,  # Way too high
    }
    warnings = validator.lint(profile)
    assert any("outside typical range" in w.lower() for w in warnings)


def test_lint_undefined_variable_reference(validator):
    """Test linting of profile with undefined variable reference."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {
                    "points": [[0, "$undefined_var"]],  # Undefined variable
                    "over": "time",
                },
                "exit_triggers": [{"type": "time", "value": 30}],
            }
        ],
        "variables": [{"name": "Other", "key": "other_var", "type": "pressure", "value": 8.0}],  # Different variable defined
    }
    warnings = validator.lint(profile)
    # Check that undefined variable reference is detected
    assert any("references variable" in w.lower() and "undefined_var" in w.lower() for w in warnings)


def test_lint_stages_not_list(validator):
    """Test linting when stages is not a list."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": "not-a-list",  # Wrong type
    }
    warnings = validator.lint(profile)
    assert any("should be a list" in w.lower() for w in warnings)


def test_lint_variables_not_list(validator):
    """Test linting when variables is not a list (should handle gracefully)."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "variables": "not-a-list",
        "stages": [],
    }
    # Should not crash, warnings may or may not be generated
    warnings = validator.lint(profile)
    assert isinstance(warnings, list)


def test_lint_stage_not_dict(validator):
    """Test linting when stage is not a dict (should handle gracefully)."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": ["not-a-dict", {"name": "Valid Stage", "exit_triggers": []}],
    }
    warnings = validator.lint(profile)
    assert isinstance(warnings, list)


def test_validation_error_exception_properties(validator):
    """Test ProfileValidationError exception properties."""
    profile = {
        "name": "Test Profile",
        # Missing id and temperature
    }
    with pytest.raises(ProfileValidationError) as exc_info:
        validator.validate_and_raise(profile)
    
    error = exc_info.value
    assert hasattr(error, 'message')
    assert hasattr(error, 'errors')
    assert isinstance(error.errors, list)
    assert len(error.errors) > 0


def test_format_error_with_path(validator):
    """Test error formatting includes path information."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": "not-a-number",  # Wrong type
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    # Check that errors include field path information
    assert any("temperature" in error.lower() for error in errors)


def test_lint_empty_profile(validator):
    """Test linting of empty profile."""
    profile = {}
    warnings = validator.lint(profile)
    assert isinstance(warnings, list)


def test_validate_empty_profile(validator):
    """Test validation of empty profile."""
    profile = {}
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert len(errors) > 0


def test_lint_missing_limits_field(validator):
    """Test linting detects missing limits field."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [{"type": "time", "value": 30}],
                # Missing limits field
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("missing 'limits' field" in w.lower() for w in warnings)
    assert any("limits" in w.lower() for w in warnings)


def test_lint_null_limits_field(validator):
    """Test linting detects null limits field."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [{"type": "time", "value": 30}],
                "limits": None,  # null limits
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("limits" in w.lower() and "null" in w.lower() for w in warnings)


def test_lint_missing_relative_field(validator):
    """Test linting detects missing relative field in exit triggers."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [
                    {"type": "time", "value": 30},  # Missing relative field
                    {"type": "weight", "value": 40, "relative": False},  # Has relative
                ],
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("missing 'relative' field" in w.lower() for w in warnings)
    assert any("relative" in w.lower() for w in warnings)


def test_lint_null_relative_field(validator):
    """Test linting detects null relative field in exit triggers."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [
                    {"type": "time", "value": 30, "relative": None},  # null relative
                ],
            }
        ],
    }
    warnings = validator.lint(profile)
    assert any("missing 'relative' field" in w.lower() or ("relative" in w.lower() and "null" in w.lower()) for w in warnings)


def test_lint_multiple_normalization_issues(validator):
    """Test linting detects multiple normalization issues."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [
                    {"type": "time", "value": 30},  # Missing relative
                ],
                "limits": None,  # null limits
            },
            {
                "name": "Stage 2",
                "key": "stage_2",
                "type": "pressure",
                "dynamics": {"points": [[0, 8]], "over": "time"},
                "exit_triggers": [
                    {"type": "weight", "value": 40},  # Missing relative
                ],
                # Missing limits field entirely
            },
        ],
    }
    warnings = validator.lint(profile)
    # Should have warnings for both stages
    limits_warnings = [w for w in warnings if "limits" in w.lower()]
    relative_warnings = [w for w in warnings if "relative" in w.lower()]
    assert len(limits_warnings) >= 2  # At least 2 limits warnings
    assert len(relative_warnings) >= 2  # At least 2 relative warnings


def test_lint_no_warnings_when_fields_present(validator):
    """Test linting doesn't warn when fields are present with valid values."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time"},
                "exit_triggers": [
                    {"type": "time", "value": 30, "relative": False},  # Has relative
                ],
                "limits": [],  # Has limits (empty array is valid)
            }
        ],
    }
    warnings = validator.lint(profile)
    # Should not have warnings about missing limits or relative
    limits_warnings = [w for w in warnings if "missing 'limits' field" in w.lower() or ("limits" in w.lower() and "null" in w.lower())]
    relative_warnings = [w for w in warnings if "missing 'relative' field" in w.lower()]
    assert len(limits_warnings) == 0
    assert len(relative_warnings) == 0


def test_validate_pressure_exceeds_15_bar_in_dynamics(validator):
    """Test validation fails when pressure exceeds 15 bar in dynamics points."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "High Pressure Stage",
                "key": "stage_1",
                "type": "pressure",  # Pressure-type stage
                "dynamics": {
                    "points": [[0, 9], [30, 20]],  # 20 bar exceeds limit
                    "over": "time",
                },
                "exit_triggers": [{"type": "time", "value": 30, "relative": False}],
                "limits": [],
            }
        ],
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert any("pressure" in e.lower() and "20" in e and "15 bar limit" in e.lower() for e in errors)


def test_validate_negative_pressure_in_dynamics(validator):
    """Test validation fails when pressure is negative in dynamics points."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Negative Pressure Stage",
                "key": "stage_1",
                "type": "pressure",
                "dynamics": {
                    "points": [[0, 9], [30, -5]],  # Negative pressure
                    "over": "time",
                },
                "exit_triggers": [{"type": "time", "value": 30, "relative": False}],
                "limits": [],
            }
        ],
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert any("negative pressure" in e.lower() and "-5" in e for e in errors)


def test_validate_pressure_exceeds_15_bar_in_exit_trigger(validator):
    """Test validation fails when pressure exceeds 15 bar in exit triggers."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4], [30, 4]], "over": "time"},
                "exit_triggers": [
                    {"type": "pressure", "value": 18, "relative": False, "comparison": ">="}  # 18 bar exceeds limit
                ],
                "limits": [],
            }
        ],
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert any("exit trigger" in e.lower() and "pressure" in e.lower() and "18" in e and "15 bar limit" in e.lower() for e in errors)


def test_validate_negative_pressure_in_exit_trigger(validator):
    """Test validation fails when pressure is negative in exit triggers."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4], [30, 4]], "over": "time"},
                "exit_triggers": [
                    {"type": "pressure", "value": -2, "relative": False, "comparison": ">="}  # Negative pressure
                ],
                "limits": [],
            }
        ],
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    assert any("exit trigger" in e.lower() and "negative pressure" in e.lower() and "-2" in e for e in errors)


def test_validate_pressure_validation_only_for_pressure_stages(validator):
    """Test that pressure validation in dynamics only applies to pressure-type stages."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Flow Stage",
                "key": "stage_1",
                "type": "flow",  # Flow-type stage, not pressure
                "dynamics": {
                    "points": [[0, 20], [30, 25]],  # These are flow values, not pressure
                    "over": "time",
                },
                "exit_triggers": [{"type": "time", "value": 30, "relative": False}],
                "limits": [],
            }
        ],
    }
    is_valid, errors = validator.validate(profile)
    # Should be valid - no pressure errors since this is a flow stage
    pressure_errors = [e for e in errors if "15 bar limit" in e.lower()]
    assert len(pressure_errors) == 0


def test_validate_pressure_limits_not_validated(validator):
    """Test that pressure in limits is NOT validated (can be infinity)."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4], [30, 4]], "over": "time"},
                "exit_triggers": [{"type": "time", "value": 30, "relative": False}],
                "limits": [
                    {"type": "pressure", "value": 100}  # Very high pressure limit - this is OK
                ],
            }
        ],
    }
    is_valid, errors = validator.validate(profile)
    # Should NOT have errors about pressure in limits
    limits_pressure_errors = [e for e in errors if "limit" in e.lower() and "pressure" in e.lower() and "15 bar" in e.lower()]
    assert len(limits_pressure_errors) == 0


def test_validate_valid_pressure_values(validator):
    """Test that valid pressure values (within 0-15 bar) pass validation."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Valid Pressure Stage",
                "key": "stage_1",
                "type": "pressure",
                "dynamics": {
                    "points": [[0, 2], [10, 9], [20, 6]],  # All within 0-15 bar
                    "over": "time",
                },
                "exit_triggers": [
                    {"type": "pressure", "value": 8, "relative": False, "comparison": ">="},  # Within limit
                    {"type": "time", "value": 30, "relative": False},
                ],
                "limits": [],
            }
        ],
    }
    is_valid, errors = validator.validate(profile)
    # Should NOT have any pressure limit errors
    pressure_errors = [e for e in errors if "15 bar limit" in e.lower() or "negative pressure" in e.lower()]
    assert len(pressure_errors) == 0


def test_validate_multiple_pressure_violations(validator):
    """Test validation detects multiple pressure violations in different locations."""
    profile = {
        "name": "Test Profile",
        "id": "test-id",
        "temperature": 90.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "pressure",
                "dynamics": {
                    "points": [[0, 20], [30, -3]],  # Both exceed limit and negative
                    "over": "time",
                },
                "exit_triggers": [
                    {"type": "pressure", "value": 18, "relative": False, "comparison": ">="}  # Also exceeds
                ],
                "limits": [],
            }
        ],
    }
    is_valid, errors = validator.validate(profile)
    assert not is_valid
    # Should have at least 3 errors (2 from dynamics, 1 from exit trigger)
    pressure_errors = [e for e in errors if ("15 bar limit" in e.lower() or "negative pressure" in e.lower())]
    assert len(pressure_errors) >= 3

