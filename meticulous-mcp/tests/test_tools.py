"""Tests for MCP tools."""

from unittest.mock import Mock, patch

import pytest
from meticulous.api_types import APIError, ChangeProfileResponse, ActionResponse, ActionType
from meticulous.profile import Profile

from meticulous_mcp.api_client import MeticulousAPIClient
from meticulous_mcp.profile_validator import ProfileValidator
from meticulous_mcp.tools import (
    initialize_tools,
    create_profile_tool,
    list_profiles_tool,
    get_profile_tool,
    update_profile_tool,
    delete_profile_tool,
    validate_profile_tool,
    run_profile_tool,
    ProfileCreateInput,
    StageInput,
)


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    return Mock(spec=MeticulousAPIClient)


@pytest.fixture
def mock_validator():
    """Create a mock validator."""
    validator = Mock(spec=ProfileValidator)
    validator.validate_and_raise = Mock()
    validator.validate = Mock(return_value=(True, []))
    validator.lint = Mock(return_value=[])
    return validator


@pytest.fixture
def initialized_tools(mock_api_client, mock_validator):
    """Initialize tools with mocked dependencies."""
    initialize_tools(mock_api_client, mock_validator)
    yield mock_api_client, mock_validator


def test_create_profile_success(initialized_tools):
    """Test successful profile creation."""
    mock_api_client, mock_validator = initialized_tools
    
    # Create mock profile
    mock_profile = Profile(
        id="new-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    
    # Mock save response
    save_response = ChangeProfileResponse(change_id="change-1", profile=mock_profile)
    mock_api_client.save_profile.return_value = save_response
    
    # Create input
    stage_input = StageInput(
        name="Stage 1",
        key="stage_1",
        type="flow",  # Use 'type' not 'stage_type' (alias)
        dynamics_points=[[0, 4]],
        dynamics_over="time",
        exit_triggers=[{"type": "time", "value": 30.0}],
    )
    input_data = ProfileCreateInput(
        name="Test Profile",
        author="Test Author",
        stages=[stage_input],
    )
    
    result = create_profile_tool(input_data)
    assert result["profile_id"] == "new-id"
    assert result["profile_name"] == "Test Profile"
    mock_api_client.save_profile.assert_called_once()
    mock_validator.validate_and_raise.assert_called_once()


def test_list_profiles_success(initialized_tools):
    """Test successful profile listing."""
    mock_api_client, _ = initialized_tools
    
    from meticulous.api_types import PartialProfile
    mock_profiles = [
        PartialProfile(id="1", name="Profile 1"),
        PartialProfile(id="2", name="Profile 2"),
    ]
    mock_api_client.list_profiles.return_value = mock_profiles
    
    result = list_profiles_tool()
    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[0]["name"] == "Profile 1"


def test_list_profiles_error(initialized_tools):
    """Test profile listing with API error."""
    mock_api_client, _ = initialized_tools
    
    error = APIError(error="Failed to list profiles")
    mock_api_client.list_profiles.return_value = error
    
    with pytest.raises(Exception) as exc_info:
        list_profiles_tool()
    assert "Failed to list profiles" in str(exc_info.value)


def test_get_profile_success(initialized_tools):
    """Test successful profile retrieval."""
    mock_api_client, _ = initialized_tools
    
    mock_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = mock_profile
    
    result = get_profile_tool("test-id")
    assert result["id"] == "test-id"
    assert result["name"] == "Test Profile"
    mock_api_client.get_profile.assert_called_once_with("test-id")


def test_delete_profile_success(initialized_tools):
    """Test successful profile deletion."""
    mock_api_client, _ = initialized_tools
    
    from meticulous.api_types import PartialProfile
    
    # The API actually returns PartialProfile, but the wrapper expects ChangeProfileResponse
    # The tool gets the profile name via get_profile first
    mock_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = mock_profile
    mock_api_client.delete_profile.return_value = PartialProfile(id="test-id", name="Test Profile")
    
    result = delete_profile_tool("test-id")
    assert result["profile_id"] == "test-id"
    assert result["profile_name"] == "Test Profile"


def test_validate_profile_valid(initialized_tools):
    """Test validation of valid profile."""
    _, mock_validator = initialized_tools
    
    profile_json = '{"name": "Test", "id": "test-id", "temperature": 90.0}'
    result = validate_profile_tool(profile_json)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_profile_invalid(initialized_tools):
    """Test validation of invalid profile."""
    _, mock_validator = initialized_tools
    mock_validator.validate.return_value = (False, ["Error 1", "Error 2"])
    
    profile_json = '{"name": "Test"}'
    result = validate_profile_tool(profile_json)
    assert result["valid"] is False
    assert len(result["errors"]) == 2


def test_run_profile_success(initialized_tools):
    """Test successful profile execution."""
    mock_api_client, _ = initialized_tools
    
    from meticulous.api_types import PartialProfile
    mock_profile = PartialProfile(id="test-id", name="Test Profile")
    mock_api_client.load_profile_by_id.return_value = mock_profile
    
    action_response = ActionResponse(status="success", action="start")
    mock_api_client.execute_action.return_value = action_response
    
    result = run_profile_tool("test-id")
    assert result["profile_id"] == "test-id"
    assert result["status"] == "success"
    mock_api_client.load_profile_by_id.assert_called_once_with("test-id")
    mock_api_client.execute_action.assert_called_once_with(ActionType.START)


def test_run_profile_load_error(initialized_tools):
    """Test profile execution with load error."""
    mock_api_client, _ = initialized_tools
    
    error = APIError(error="Failed to load profile")
    mock_api_client.load_profile_by_id.return_value = error
    
    with pytest.raises(Exception) as exc_info:
        run_profile_tool("test-id")
    assert "Failed to load profile" in str(exc_info.value)


def test_run_profile_start_error(initialized_tools):
    """Test profile execution with start action error."""
    mock_api_client, _ = initialized_tools
    
    from meticulous.api_types import PartialProfile
    mock_profile = PartialProfile(id="test-id", name="Test Profile")
    mock_api_client.load_profile_by_id.return_value = mock_profile
    
    error = APIError(error="Failed to start")
    mock_api_client.execute_action.return_value = error
    
    with pytest.raises(Exception) as exc_info:
        run_profile_tool("test-id")
    assert "Failed to start profile" in str(exc_info.value)


def test_create_profile_with_warnings(initialized_tools):
    """Test profile creation with linting warnings."""
    mock_api_client, mock_validator = initialized_tools
    
    mock_profile = Profile(
        id="new-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    
    save_response = ChangeProfileResponse(change_id="change-1", profile=mock_profile)
    mock_api_client.save_profile.return_value = save_response
    mock_validator.lint.return_value = ["Warning: Low temperature"]
    
    stage_input = StageInput(
        name="Stage 1",
        key="stage_1",
        type="flow",  # Use 'type' not 'stage_type' (alias)
        dynamics_points=[[0, 4]],
        dynamics_over="time",
        exit_triggers=[{"type": "time", "value": 30.0}],
    )
    input_data = ProfileCreateInput(
        name="Test Profile",
        author="Test Author",
        stages=[stage_input],
    )
    
    result = create_profile_tool(input_data)
    assert result["profile_id"] == "new-id"
    assert "warnings" in result
    assert len(result["warnings"]) == 1


def test_create_profile_validation_error(initialized_tools):
    """Test profile creation with validation error."""
    mock_api_client, mock_validator = initialized_tools
    
    from meticulous_mcp.profile_validator import ProfileValidationError
    mock_validator.validate_and_raise.side_effect = ProfileValidationError(
        "Validation failed", ["Error 1", "Error 2"]
    )
    
    stage_input = StageInput(
        name="Stage 1",
        key="stage_1",
        type="flow",  # Use 'type' not 'stage_type' (alias)
        dynamics_points=[[0, 4]],
        dynamics_over="time",
        exit_triggers=[{"type": "time", "value": 30.0}],
    )
    input_data = ProfileCreateInput(
        name="Test Profile",
        author="Test Author",
        stages=[stage_input],
    )
    
    with pytest.raises(Exception) as exc_info:
        create_profile_tool(input_data)
    assert "validation failed" in str(exc_info.value).lower()


def test_create_profile_save_error(initialized_tools):
    """Test profile creation with save error."""
    mock_api_client, mock_validator = initialized_tools
    
    error = APIError(error="Failed to save")
    mock_api_client.save_profile.return_value = error
    
    stage_input = StageInput(
        name="Stage 1",
        key="stage_1",
        type="flow",  # Use 'type' not 'stage_type' (alias)
        dynamics_points=[[0, 4]],
        dynamics_over="time",
        exit_triggers=[{"type": "time", "value": 30.0}],
    )
    input_data = ProfileCreateInput(
        name="Test Profile",
        author="Test Author",
        stages=[stage_input],
    )
    
    with pytest.raises(Exception) as exc_info:
        create_profile_tool(input_data)
    assert "Failed to save profile" in str(exc_info.value)


def test_create_profile_with_variables(initialized_tools):
    """Test profile creation with variables."""
    mock_api_client, mock_validator = initialized_tools
    
    mock_profile = Profile(
        id="new-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    
    save_response = ChangeProfileResponse(change_id="change-1", profile=mock_profile)
    mock_api_client.save_profile.return_value = save_response
    
    from meticulous_mcp.tools import VariableInput
    variable_input = VariableInput(
        name="Pressure",
        key="pressure_1",
        type="pressure",  # Use 'type' not 'var_type' (alias)
        value=8.0,
    )
    
    stage_input = StageInput(
        name="Stage 1",
        key="stage_1",
        type="flow",  # Use 'type' not 'stage_type' (alias)
        dynamics_points=[[0, 4]],
        dynamics_over="time",
        exit_triggers=[{"type": "time", "value": 30.0}],
    )
    input_data = ProfileCreateInput(
        name="Test Profile",
        author="Test Author",
        stages=[stage_input],
        variables=[variable_input],
    )
    
    result = create_profile_tool(input_data)
    assert result["profile_id"] == "new-id"


def test_create_profile_with_accent_color(initialized_tools):
    """Test profile creation with accent color."""
    mock_api_client, mock_validator = initialized_tools
    
    mock_profile = Profile(
        id="new-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    
    save_response = ChangeProfileResponse(change_id="change-1", profile=mock_profile)
    mock_api_client.save_profile.return_value = save_response
    
    stage_input = StageInput(
        name="Stage 1",
        key="stage_1",
        type="flow",  # Use 'type' not 'stage_type' (alias)
        dynamics_points=[[0, 4]],
        dynamics_over="time",
        exit_triggers=[{"type": "time", "value": 30.0}],
    )
    input_data = ProfileCreateInput(
        name="Test Profile",
        author="Test Author",
        stages=[stage_input],
        accent_color="#FF5733",
    )
    
    result = create_profile_tool(input_data)
    assert result["profile_id"] == "new-id"


def test_create_profile_stage_error(initialized_tools):
    """Test profile creation with stage creation error."""
    mock_api_client, mock_validator = initialized_tools
    
    stage_input = StageInput(
        name="Stage 1",
        key="stage_1",
        type="flow",  # Use 'type' not 'stage_type' (alias)
        dynamics_points=[[0, 4]],
        dynamics_over="time",
        exit_triggers=[{"type": "invalid_type"}],  # Invalid trigger
    )
    input_data = ProfileCreateInput(
        name="Test Profile",
        author="Test Author",
        stages=[stage_input],
    )
    
    # Should raise exception during stage creation
    with pytest.raises(Exception):
        create_profile_tool(input_data)


def test_get_profile_error(initialized_tools):
    """Test profile retrieval with API error."""
    mock_api_client, _ = initialized_tools
    
    error = APIError(error="Profile not found")
    mock_api_client.get_profile.return_value = error
    
    with pytest.raises(Exception) as exc_info:
        get_profile_tool("nonexistent-id")
    assert "Failed to get profile" in str(exc_info.value)


def test_delete_profile_error(initialized_tools):
    """Test profile deletion with API error."""
    mock_api_client, _ = initialized_tools
    
    error = APIError(error="Failed to delete")
    mock_api_client.delete_profile.return_value = error
    
    with pytest.raises(Exception) as exc_info:
        delete_profile_tool("test-id")
    assert "Failed to delete profile" in str(exc_info.value)


def test_delete_profile_get_error(initialized_tools):
    """Test profile deletion when get_profile fails (should still delete)."""
    mock_api_client, _ = initialized_tools
    
    # get_profile fails but delete should still work
    get_error = APIError(error="Profile not found")
    mock_api_client.get_profile.return_value = get_error
    
    from meticulous.api_types import PartialProfile
    # API returns PartialProfile, not ChangeProfileResponse
    mock_api_client.delete_profile.return_value = PartialProfile(id="test-id", name="Test Profile")
    
    result = delete_profile_tool("test-id")
    assert result["profile_id"] == "test-id"
    assert result["profile_name"] == "test-id"  # Falls back to ID when get_profile fails


def test_validate_profile_invalid_json(initialized_tools):
    """Test validation with invalid JSON."""
    _, _ = initialized_tools
    
    with pytest.raises(Exception) as exc_info:
        validate_profile_tool("not valid json")
    assert "Invalid JSON" in str(exc_info.value)


def test_validate_profile_with_warnings(initialized_tools):
    """Test validation with warnings."""
    _, mock_validator = initialized_tools
    
    mock_validator.validate.return_value = (True, [])
    mock_validator.lint.return_value = ["Warning 1", "Warning 2"]
    
    profile_json = '{"name": "Test", "id": "test-id", "temperature": 90.0}'
    result = validate_profile_tool(profile_json)
    assert result["valid"] is True
    assert len(result["warnings"]) == 2


def test_validate_profile_with_errors_and_warnings(initialized_tools):
    """Test validation with both errors and warnings."""
    _, mock_validator = initialized_tools
    
    mock_validator.validate.return_value = (False, ["Error 1"])
    mock_validator.lint.return_value = ["Warning 1"]
    
    profile_json = '{"name": "Test"}'
    result = validate_profile_tool(profile_json)
    assert result["valid"] is False
    assert len(result["errors"]) == 1
    assert len(result["warnings"]) == 1


def test_update_profile_success(initialized_tools):
    """Test successful profile update."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="test-id",
        name="Old Name",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    updated_profile = Profile(
        id="test-id",
        name="New Name",
        author="Test Author",
        author_id="author-id",
        temperature=92.0,
        final_weight=42.0,
        stages=[],
    )
    save_response = ChangeProfileResponse(change_id="change-1", profile=updated_profile)
    mock_api_client.save_profile.return_value = save_response
    
    from meticulous_mcp.tools import ProfileUpdateInput
    input_data = ProfileUpdateInput(
        profile_id="test-id",
        name="New Name",
        temperature=92.0,
        final_weight=42.0,
    )
    
    result = update_profile_tool(input_data)
    assert result["profile_id"] == "test-id"
    assert result["profile_name"] == "New Name"


def test_update_profile_get_error(initialized_tools):
    """Test profile update with get error."""
    mock_api_client, _ = initialized_tools
    
    error = APIError(error="Profile not found")
    mock_api_client.get_profile.return_value = error
    
    from meticulous_mcp.tools import ProfileUpdateInput
    input_data = ProfileUpdateInput(profile_id="nonexistent-id", name="New Name")
    
    with pytest.raises(Exception) as exc_info:
        update_profile_tool(input_data)
    assert "Failed to get profile" in str(exc_info.value)


def test_update_profile_update_stages(initialized_tools):
    """Test profile update with stage updates."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    updated_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    save_response = ChangeProfileResponse(change_id="change-1", profile=updated_profile)
    mock_api_client.save_profile.return_value = save_response
    
    from meticulous_mcp.tools import ProfileUpdateInput
    input_data = ProfileUpdateInput(
        profile_id="test-id",
        stages=[
            {
                "name": "New Stage",
                "key": "stage_1",
                "type": "flow",
                "dynamics": {"points": [[0, 4]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [{"type": "time", "value": 30}],
            }
        ],
    )
    
    result = update_profile_tool(input_data)
    assert result["profile_id"] == "test-id"


def test_update_profile_stages_json(initialized_tools):
    """Test profile update with stages_json."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    updated_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    save_response = ChangeProfileResponse(change_id="change-1", profile=updated_profile)
    mock_api_client.save_profile.return_value = save_response
    
    from meticulous_mcp.tools import ProfileUpdateInput
    import json
    stages_json = json.dumps([
        {
            "name": "New Stage",
            "key": "stage_1",
            "type": "flow",
            "dynamics": {"points": [[0, 4]], "over": "time", "interpolation": "linear"},
            "exit_triggers": [{"type": "time", "value": 30}],
        }
    ])
    input_data = ProfileUpdateInput(
        profile_id="test-id",
        stages_json=stages_json,
    )
    
    result = update_profile_tool(input_data)
    assert result["profile_id"] == "test-id"


def test_update_profile_stages_json_invalid(initialized_tools):
    """Test profile update with invalid stages_json."""
    mock_api_client, _ = initialized_tools
    
    existing_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    from meticulous_mcp.tools import ProfileUpdateInput
    input_data = ProfileUpdateInput(
        profile_id="test-id",
        stages_json="invalid json {",
    )
    
    with pytest.raises(Exception) as exc_info:
        update_profile_tool(input_data)
    assert "Invalid JSON" in str(exc_info.value) or "JSONDecodeError" in str(type(exc_info.value).__name__)


def test_update_profile_variables_json(initialized_tools):
    """Test profile update with variables_json."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    updated_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    save_response = ChangeProfileResponse(change_id="change-1", profile=updated_profile)
    mock_api_client.save_profile.return_value = save_response
    
    from meticulous_mcp.tools import ProfileUpdateInput
    import json
    variables_json = json.dumps([
        {"name": "Pressure", "key": "pressure_1", "type": "pressure", "value": 8.0}
    ])
    input_data = ProfileUpdateInput(
        profile_id="test-id",
        variables_json=variables_json,
    )
    
    result = update_profile_tool(input_data)
    assert result["profile_id"] == "test-id"


def test_update_profile_validation_error(initialized_tools):
    """Test profile update with validation error."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    from meticulous_mcp.profile_validator import ProfileValidationError
    mock_validator.validate_and_raise.side_effect = ProfileValidationError(
        "Validation failed", ["Error 1"]
    )
    
    from meticulous_mcp.tools import ProfileUpdateInput
    input_data = ProfileUpdateInput(profile_id="test-id", name="New Name")
    
    with pytest.raises(Exception) as exc_info:
        update_profile_tool(input_data)
    assert "validation failed" in str(exc_info.value).lower()


def test_update_profile_save_error(initialized_tools):
    """Test profile update with save error."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    error = APIError(error="Failed to save")
    mock_api_client.save_profile.return_value = error
    
    from meticulous_mcp.tools import ProfileUpdateInput
    input_data = ProfileUpdateInput(profile_id="test-id", name="New Name")
    
    with pytest.raises(Exception) as exc_info:
        update_profile_tool(input_data)
    assert "Failed to update profile" in str(exc_info.value)


def test_duplicate_profile_success(initialized_tools):
    """Test successful profile duplication."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="old-id",
        name="Old Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    new_profile = Profile(
        id="new-id",
        name="New Profile",
        author="Test Author",
        author_id="author-id",
        temperature=92.0,
        final_weight=40.0,
        stages=[],
    )
    save_response = ChangeProfileResponse(change_id="change-1", profile=new_profile)
    mock_api_client.save_profile.return_value = save_response
    
    from meticulous_mcp.tools import duplicate_profile_tool
    result = duplicate_profile_tool("old-id", "New Profile", modify_temperature=92.0)
    assert result["profile_id"] == "new-id"
    assert result["profile_name"] == "New Profile"


def test_duplicate_profile_get_error(initialized_tools):
    """Test profile duplication with get error."""
    mock_api_client, _ = initialized_tools
    
    error = APIError(error="Profile not found")
    mock_api_client.get_profile.return_value = error
    
    from meticulous_mcp.tools import duplicate_profile_tool
    with pytest.raises(Exception) as exc_info:
        duplicate_profile_tool("nonexistent-id", "New Profile")
    assert "Failed to get profile" in str(exc_info.value)


def test_duplicate_profile_save_error(initialized_tools):
    """Test profile duplication with save error."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="old-id",
        name="Old Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    error = APIError(error="Failed to save")
    mock_api_client.save_profile.return_value = error
    
    from meticulous_mcp.tools import duplicate_profile_tool
    with pytest.raises(Exception) as exc_info:
        duplicate_profile_tool("old-id", "New Profile")
    assert "Failed to save duplicated profile" in str(exc_info.value)


def test_duplicate_profile_without_temperature_modification(initialized_tools):
    """Test profile duplication without temperature modification."""
    mock_api_client, mock_validator = initialized_tools
    
    existing_profile = Profile(
        id="old-id",
        name="Old Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api_client.get_profile.return_value = existing_profile
    
    new_profile = Profile(
        id="new-id",
        name="New Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,  # Same temperature
        final_weight=40.0,
        stages=[],
    )
    save_response = ChangeProfileResponse(change_id="change-1", profile=new_profile)
    mock_api_client.save_profile.return_value = save_response
    
    from meticulous_mcp.tools import duplicate_profile_tool
    result = duplicate_profile_tool("old-id", "New Profile")
    assert result["profile_id"] == "new-id"


def test_ensure_initialized_not_called():
    """Test that _ensure_initialized raises when tools not initialized."""
    from meticulous_mcp.tools import initialize_tools, _ensure_initialized
    from meticulous_mcp.api_client import MeticulousAPIClient
    from meticulous_mcp.profile_validator import ProfileValidator
    
    # Reset global state
    import meticulous_mcp.tools as tools_module
    tools_module._api_client = None
    tools_module._validator = None
    
    with pytest.raises(RuntimeError) as exc_info:
        _ensure_initialized()
    assert "Tools not initialized" in str(exc_info.value)
    
    # Re-initialize for other tests
    mock_api = Mock(spec=MeticulousAPIClient)
    mock_validator = Mock(spec=ProfileValidator)
    initialize_tools(mock_api, mock_validator)


def test_list_profiles_partial_profile_missing_attrs(initialized_tools):
    """Test list_profiles handles PartialProfile without direct attributes."""
    mock_api_client, _ = initialized_tools
    
    from meticulous.api_types import PartialProfile
    from unittest.mock import Mock
    
    # Create a mock that uses model_dump
    mock_profile = Mock(spec=PartialProfile)
    mock_profile.model_dump.return_value = {"id": "1", "name": "Profile 1"}
    
    mock_api_client.list_profiles.return_value = [mock_profile]
    
    result = list_profiles_tool()
    assert len(result) == 1
    assert result[0]["id"] == "1"
    assert result[0]["name"] == "Profile 1"

