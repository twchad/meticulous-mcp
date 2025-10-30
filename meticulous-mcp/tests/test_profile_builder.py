"""Tests for profile builder."""

import uuid

import pytest
from meticulous.profile import Profile, Stage, Dynamics, ExitTrigger

from meticulous_mcp.profile_builder import (
    create_profile,
    create_stage,
    create_dynamics,
    create_exit_trigger,
    create_limit,
    create_variable,
    profile_to_dict,
    dict_to_profile,
)


def test_create_exit_trigger():
    """Test exit trigger creation."""
    trigger = create_exit_trigger("time", 30.0, relative=True, comparison=">=")
    assert trigger.type == "time"
    assert trigger.value == 30.0
    assert trigger.relative is True
    assert trigger.comparison == ">="


def test_create_dynamics():
    """Test dynamics creation."""
    dynamics = create_dynamics(
        points=[[0, 4], [10, 8]],
        over="time",
        interpolation="linear",
    )
    assert dynamics.over == "time"
    assert dynamics.interpolation == "linear"
    assert len(dynamics.points) == 2


def test_create_stage():
    """Test stage creation."""
    dynamics = create_dynamics(points=[[0, 4]], over="time")
    exit_triggers = [create_exit_trigger("time", 30.0)]
    
    stage = create_stage(
        name="Preinfusion",
        key="stage_1",
        stage_type="flow",
        dynamics=dynamics,
        exit_triggers=exit_triggers,
    )
    assert stage.name == "Preinfusion"
    assert stage.key == "stage_1"
    assert stage.type == "flow"
    assert len(stage.exit_triggers) == 1


def test_create_variable():
    """Test variable creation."""
    variable = create_variable("Pressure", "pressure_1", "pressure", 8.0)
    assert variable.name == "Pressure"
    assert variable.key == "pressure_1"
    assert variable.type == "pressure"
    assert variable.value == 8.0


def test_create_profile_minimal():
    """Test minimal profile creation."""
    profile = create_profile(
        name="Test Profile",
        author="Test Author",
        stages=[],
    )
    assert profile.name == "Test Profile"
    assert profile.author == "Test Author"
    assert profile.temperature == 90.0  # Default
    assert profile.final_weight == 40.0  # Default
    assert len(profile.stages) == 0
    assert uuid.UUID(profile.id)  # Should be valid UUID
    assert uuid.UUID(profile.author_id)  # Should be valid UUID


def test_create_profile_full():
    """Test full profile creation."""
    dynamics = create_dynamics(points=[[0, 4]], over="time")
    exit_triggers = [create_exit_trigger("time", 30.0)]
    stage = create_stage(
        name="Stage 1",
        key="stage_1",
        stage_type="flow",
        dynamics=dynamics,
        exit_triggers=exit_triggers,
    )
    variable = create_variable("Pressure", "pressure_1", "pressure", 8.0)
    
    profile = create_profile(
        name="Test Profile",
        author="Test Author",
        temperature=92.0,
        final_weight=42.0,
        stages=[stage],
        variables=[variable],
        profile_id="custom-id",
        author_id="custom-author-id",
    )
    assert profile.temperature == 92.0
    assert profile.final_weight == 42.0
    assert len(profile.stages) == 1
    assert len(profile.variables) == 1
    assert profile.id == "custom-id"
    assert profile.author_id == "custom-author-id"


def test_profile_to_dict():
    """Test profile to dictionary conversion."""
    profile = create_profile(
        name="Test Profile",
        author="Test Author",
        stages=[],
    )
    profile_dict = profile_to_dict(profile)
    assert isinstance(profile_dict, dict)
    assert profile_dict["name"] == "Test Profile"
    assert profile_dict["author"] == "Test Author"


def test_dict_to_profile():
    """Test dictionary to profile conversion."""
    profile_dict = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test Author",
        "author_id": "author-id",
        "temperature": 90.0,
        "final_weight": 40.0,
        "stages": [],
    }
    profile = dict_to_profile(profile_dict)
    assert isinstance(profile, Profile)
    assert profile.name == "Test Profile"
    assert profile.id == "test-id"


def test_variable_references():
    """Test that variable references (strings starting with $) work correctly."""
    # Test exit trigger with variable reference
    trigger = create_exit_trigger("pressure", "$pressure_1", relative=False, comparison=">=")
    assert trigger.type == "pressure"
    assert trigger.value == "$pressure_1"
    assert isinstance(trigger.value, str)
    
    # Test dynamics with variable reference
    dynamics = create_dynamics(
        points=[[0, "$pressure_1"], [10, 7]],
        over="time",
        interpolation="linear",
    )
    assert dynamics.points[0][1] == "$pressure_1"
    assert isinstance(dynamics.points[0][1], str)
    assert dynamics.points[1][1] == 7
    assert isinstance(dynamics.points[1][1], (int, float))
    
    # Test limit with variable reference
    limit = create_limit("flow", "$flow_1")
    assert limit.value == "$flow_1"
    assert isinstance(limit.value, str)
    
    # Test full profile with variable references
    exit_triggers = [create_exit_trigger("pressure", "$pressure_1")]
    stage = create_stage(
        name="Infusion",
        key="stage_1",
        stage_type="pressure",
        dynamics=dynamics,
        exit_triggers=exit_triggers,
        limits=[limit],
    )
    
    profile = create_profile(
        name="Test Profile",
        author="Test Author",
        stages=[stage],
    )
    
    # Verify serialization preserves variable references
    profile_dict = profile_to_dict(profile)
    assert profile_dict["stages"][0]["exit_triggers"][0]["value"] == "$pressure_1"
    assert profile_dict["stages"][0]["dynamics"]["points"][0][1] == "$pressure_1"
    assert profile_dict["stages"][0]["limits"][0]["value"] == "$flow_1"


def test_create_exit_trigger_optional_fields():
    """Test exit trigger creation with optional fields."""
    # Test with all fields
    trigger = create_exit_trigger("weight", 30.0, relative=True, comparison=">=")
    assert trigger.type == "weight"
    assert trigger.value == 30.0
    assert trigger.relative is True
    assert trigger.comparison == ">="
    
    # Test with minimal fields
    trigger = create_exit_trigger("time", 30.0)
    assert trigger.type == "time"
    assert trigger.value == 30.0
    assert trigger.relative is None
    assert trigger.comparison is None


def test_create_limit_types():
    """Test limit creation with different types."""
    pressure_limit = create_limit("pressure", 9.0)
    assert pressure_limit.type == "pressure"
    assert pressure_limit.value == 9.0
    
    flow_limit = create_limit("flow", "$flow_1")
    assert flow_limit.type == "flow"
    assert flow_limit.value == "$flow_1"


def test_create_dynamics_interpolation_types():
    """Test dynamics creation with different interpolation types."""
    linear = create_dynamics(points=[[0, 4], [10, 8]], over="time", interpolation="linear")
    assert linear.interpolation == "linear"
    
    curve = create_dynamics(points=[[0, 4], [10, 8]], over="time", interpolation="curve")
    assert curve.interpolation == "curve"
    
    none = create_dynamics(points=[[0, 4]], over="time", interpolation="none")
    assert none.interpolation == "none"


def test_create_stage_with_limits():
    """Test stage creation with limits."""
    dynamics = create_dynamics(points=[[0, 4]], over="time")
    exit_triggers = [create_exit_trigger("time", 30.0)]
    limits = [
        create_limit("pressure", 9.0),
        create_limit("flow", "$flow_1"),
    ]
    
    stage = create_stage(
        name="Stage 1",
        key="stage_1",
        stage_type="flow",
        dynamics=dynamics,
        exit_triggers=exit_triggers,
        limits=limits,
    )
    assert len(stage.limits) == 2
    assert stage.limits[0].type == "pressure"
    assert stage.limits[1].type == "flow"


def test_create_stage_without_limits():
    """Test stage creation without limits."""
    dynamics = create_dynamics(points=[[0, 4]], over="time")
    exit_triggers = [create_exit_trigger("time", 30.0)]
    
    stage = create_stage(
        name="Stage 1",
        key="stage_1",
        stage_type="flow",
        dynamics=dynamics,
        exit_triggers=exit_triggers,
        limits=None,
    )
    assert stage.limits is None


def test_create_profile_with_optional_fields():
    """Test profile creation with all optional fields."""
    from meticulous.profile import Display, PreviousAuthor
    
    display = Display(accentColor="#FF5733")
    previous_authors = [PreviousAuthor(name="Previous Author", author_id="prev-id", profile_id="prev-profile-id")]
    
    profile = create_profile(
        name="Test Profile",
        author="Test Author",
        author_id="custom-author-id",
        temperature=92.0,
        final_weight=42.0,
        stages=[],
        variables=[],
        display=display,
        previous_authors=previous_authors,
        profile_id="custom-profile-id",
        last_changed=1234567890.0,
    )
    assert profile.id == "custom-profile-id"
    assert profile.author_id == "custom-author-id"
    assert profile.temperature == 92.0
    assert profile.final_weight == 42.0
    assert profile.display == display
    assert len(profile.previous_authors) == 1
    assert profile.last_changed == 1234567890.0


def test_profile_to_dict_excludes_none():
    """Test that profile_to_dict excludes None values."""
    profile = create_profile(
        name="Test Profile",
        author="Test Author",
        stages=[],
    )
    profile_dict = profile_to_dict(profile)
    # None values should be excluded
    assert "variables" not in profile_dict or profile_dict["variables"] is not None
    assert "display" not in profile_dict or profile_dict["display"] is not None


def test_dict_to_profile_with_all_fields():
    """Test dict_to_profile with all possible fields."""
    profile_dict = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test Author",
        "author_id": "author-id",
        "temperature": 90.0,
        "final_weight": 40.0,
        "stages": [
            {
                "name": "Stage 1",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [{"type": "time", "value": 30.0}],
            }
        ],
        "variables": [
            {"name": "Pressure", "key": "pressure_1", "type": "pressure", "value": 8.0}
        ],
        "last_changed": 1234567890.0,
    }
    profile = dict_to_profile(profile_dict)
    assert profile.name == "Test Profile"
    assert profile.id == "test-id"
    assert len(profile.stages) == 1
    assert len(profile.variables) == 1
    assert profile.last_changed == 1234567890.0


def test_create_profile_generates_uuid():
    """Test that create_profile generates UUIDs when not provided."""
    profile1 = create_profile(name="Profile 1", author="Author", stages=[])
    profile2 = create_profile(name="Profile 2", author="Author", stages=[])
    
    # Both should have valid UUIDs
    assert uuid.UUID(profile1.id)
    assert uuid.UUID(profile2.id)
    assert uuid.UUID(profile1.author_id)
    assert uuid.UUID(profile2.author_id)
    
    # IDs should be different
    assert profile1.id != profile2.id
    assert profile1.author_id != profile2.author_id


def test_create_stage_all_types():
    """Test stage creation with all valid types."""
    dynamics = create_dynamics(points=[[0, 4]], over="time")
    exit_triggers = [create_exit_trigger("time", 30.0)]
    
    power_stage = create_stage(
        name="Power Stage",
        key="power_1",
        stage_type="power",
        dynamics=dynamics,
        exit_triggers=exit_triggers,
    )
    assert power_stage.type == "power"
    
    flow_stage = create_stage(
        name="Flow Stage",
        key="flow_1",
        stage_type="flow",
        dynamics=dynamics,
        exit_triggers=exit_triggers,
    )
    assert flow_stage.type == "flow"
    
    pressure_stage = create_stage(
        name="Pressure Stage",
        key="pressure_1",
        stage_type="pressure",
        dynamics=dynamics,
        exit_triggers=exit_triggers,
    )
    assert pressure_stage.type == "pressure"


def test_create_dynamics_all_over_types():
    """Test dynamics creation with all valid 'over' types."""
    time_dynamics = create_dynamics(points=[[0, 4]], over="time")
    assert time_dynamics.over == "time"
    
    weight_dynamics = create_dynamics(points=[[0, 4]], over="weight")
    assert weight_dynamics.over == "weight"
    
    position_dynamics = create_dynamics(points=[[0, 4]], over="piston_position")
    assert position_dynamics.over == "piston_position"


def test_create_exit_trigger_all_types():
    """Test exit trigger creation with all valid types."""
    types = ["weight", "pressure", "flow", "time", "piston_position", "power", "user_interaction"]
    for trigger_type in types:
        trigger = create_exit_trigger(trigger_type, 30.0)
        assert trigger.type == trigger_type


def test_create_variable_all_types():
    """Test variable creation with all valid types."""
    types = ["power", "flow", "pressure", "weight", "time", "piston_position"]
    for var_type in types:
        variable = create_variable("Test", f"var_{var_type}", var_type, 10.0)
        assert variable.type == var_type
        assert variable.key == f"var_{var_type}"

