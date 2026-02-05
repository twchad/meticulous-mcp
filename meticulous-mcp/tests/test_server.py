"""Tests for MCP server."""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

import meticulous_mcp.server as server_module
from meticulous_mcp.server import (
    espresso_knowledge,
    espresso_schema,
    get_profile_resource,
    create_espresso_profile,
    modify_espresso_profile,
    troubleshoot_profile,
)


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    return Mock()


@pytest.fixture
def mock_validator():
    """Create a mock validator."""
    return Mock()


@pytest.fixture
def reset_server_state():
    """Reset server global state before each test."""
    import meticulous_mcp.server as server_module
    server_module._api_client = None
    server_module._validator = None
    yield
    server_module._api_client = None
    server_module._validator = None


def setup_path_mocks(schema_exists=True):
    """
    Helper to set up Path mocks that support division operator.
    
    Args:
        schema_exists: Whether the schema file should exist
        
    Returns:
        tuple: (mock_path_class callable, mock_server_path)
    """
    def create_path_mock(exists_result=False):
        """Create a mock Path object that supports / operator"""
        path_mock = Mock()
        
        def truediv_handler(self, other):
            # Create another mock for the result of division
            result_mock = Mock()
            result_mock.exists.return_value = exists_result
            result_mock.__truediv__ = truediv_handler
            return result_mock
        
        path_mock.__truediv__ = truediv_handler
        path_mock.exists.return_value = exists_result
        return path_mock
    
    # Create the mock for the server file path
    mock_server_path = Mock()
    mock_server_path.resolve.return_value = mock_server_path
    
    # Create parent chain with proper division support
    # parent.parent.parent / "espresso-profile-schema" / "schema.json" should return schema_exists
    mock_parent3 = Mock()
    mock_parent3.__truediv__ = lambda self, name: create_path_mock(exists_result=schema_exists) if name == "espresso-profile-schema" else create_path_mock(exists_result=False)
    
    mock_parent4 = Mock()
    mock_parent4.__truediv__ = lambda self, name: create_path_mock(exists_result=False)
    mock_parent3.parent = mock_parent4
    
    mock_parent2 = Mock()
    mock_parent2.parent = mock_parent3
    
    mock_parent1 = Mock()
    mock_parent1.parent = mock_parent2
    
    mock_server_path.parent = mock_parent1
    
    # Mock Path() constructor to return appropriate mocks
    def path_constructor(path_arg=None):
        # For server.py file, return the mock with proper parent chain
        if path_arg and hasattr(path_arg, 'endswith') and path_arg.endswith('server.py'):
            return mock_server_path
        # For any other path string, return a path that doesn't exist
        return create_path_mock(exists_result=False)
    
    return path_constructor, mock_server_path


def test_ensure_initialized_first_call(reset_server_state, mock_api_client, mock_validator):
    """Test _ensure_initialized on first call."""
    with patch("meticulous_mcp.server.MeticulousAPIClient") as mock_client_class, \
         patch("meticulous_mcp.server.ProfileValidator") as mock_validator_class, \
         patch("meticulous_mcp.server.initialize_tools") as mock_init_tools, \
         patch("meticulous_mcp.server.Path") as mock_path_class:
        
        mock_client_class.return_value = mock_api_client
        mock_validator_class.return_value = mock_validator
        
        # Setup path mocks with schema existing
        path_constructor, _ = setup_path_mocks(schema_exists=True)
        mock_path_class.side_effect = path_constructor
        
        # Test initialization through public function
        server_module._ensure_initialized()
        
        # Verify initialization happened
        assert server_module._api_client is not None
        assert server_module._validator is not None


def test_ensure_initialized_schema_path_not_found(reset_server_state):
    """Test _ensure_initialized when schema path is not found."""
    with patch("meticulous_mcp.server.MeticulousAPIClient") as mock_client_class, \
         patch("meticulous_mcp.server.Path") as mock_path_class, \
         patch("os.getenv", return_value="http://test.local"):
        
        mock_client_class.return_value = Mock()
        
        # Setup path mocks with schema NOT existing
        path_constructor, _ = setup_path_mocks(schema_exists=False)
        mock_path_class.side_effect = path_constructor
        
        # Should still initialize (validator will handle missing schema)
        with patch("meticulous_mcp.server.ProfileValidator") as mock_validator_class:
            mock_validator_class.side_effect = FileNotFoundError("Schema not found")
            with pytest.raises(FileNotFoundError):
                server_module._ensure_initialized()


def test_espresso_knowledge():
    """Test espresso_knowledge resource returns string."""
    result = espresso_knowledge()
    assert isinstance(result, str)
    assert len(result) > 0
    assert "espresso" in result.lower() or "profiling" in result.lower()


def test_espresso_schema_success(reset_server_state):
    """Test espresso_schema resource returns schema JSON."""
    with patch("meticulous_mcp.server._ensure_initialized"), \
         patch("meticulous_mcp.server.Path") as mock_path_class, \
         patch("builtins.open", create=True) as mock_open:
        
        # Setup path mocks with schema existing
        path_constructor, mock_server_path = setup_path_mocks(schema_exists=True)
        mock_path_class.side_effect = path_constructor
        
        # Set the _schema_path module variable to a mock path that exists
        mock_schema_path = Mock()
        mock_schema_path.exists.return_value = True
        server_module._schema_path = mock_schema_path
        
        # Mock file content
        schema_data = {"type": "object", "properties": {"name": {"type": "string"}}}
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(schema_data)
        
        result = espresso_schema()
        assert isinstance(result, str)
        assert "name" in result


def test_espresso_schema_file_not_found(reset_server_state):
    """Test espresso_schema when schema file not found."""
    with patch("meticulous_mcp.server._ensure_initialized"), \
         patch("meticulous_mcp.server.Path") as mock_path_class:
        mock_schema_path = Mock()
        mock_schema_path.exists.return_value = False
        
        def mock_path_div(path_str):
            if path_str == "espresso-profile-schema":
                inner_path = Mock()
                inner_path.__truediv__ = Mock(return_value=mock_schema_path)
                return inner_path
            return mock_schema_path
        
        mock_path_instance = Mock()
        mock_path_instance.parent.parent.parent = Mock()
        mock_path_instance.parent.parent.parent.__truediv__ = Mock(side_effect=mock_path_div)
        mock_path_class.return_value = mock_path_instance
        
        result = espresso_schema()
        assert isinstance(result, str)
        assert "Error" in result or "not found" in result.lower()


def test_espresso_schema_exception(reset_server_state):
    """Test espresso_schema when exception occurs."""
    with patch("meticulous_mcp.server._ensure_initialized"), \
         patch("meticulous_mcp.server.Path") as mock_path_class:
        mock_path_instance = Mock()
        mock_path_instance.parent.parent.parent = Mock()
        mock_path_instance.parent.parent.parent.__truediv__ = Mock(side_effect=Exception("Test error"))
        mock_path_class.return_value = mock_path_instance
        
        result = espresso_schema()
        assert isinstance(result, str)
        assert "Error" in result


def test_get_profile_resource_success(reset_server_state):
    """Test get_profile_resource returns profile JSON."""
    with patch("meticulous_mcp.server._ensure_initialized"), \
         patch.object(server_module, "_api_client") as mock_api:
        
        from meticulous.profile import Profile
        profile = Profile(
            id="test-id",
            name="Test Profile",
            author="Test Author",
            author_id="author-id",
            temperature=90.0,
            final_weight=40.0,
            stages=[],
        )
        mock_api.get_profile.return_value = profile
        
        result = get_profile_resource("test-id")
        assert isinstance(result, str)
        profile_dict = json.loads(result)
        assert profile_dict["id"] == "test-id"
        assert profile_dict["name"] == "Test Profile"


def test_get_profile_resource_error(reset_server_state):
    """Test get_profile_resource handles API error."""
    with patch("meticulous_mcp.server._ensure_initialized"), \
         patch.object(server_module, "_api_client") as mock_api:
        
        from meticulous.api_types import APIError
        error = APIError(error="Profile not found")
        mock_api.get_profile.return_value = error
        
        result = get_profile_resource("nonexistent-id")
        assert isinstance(result, str)
        assert "Error" in result


def test_create_espresso_profile_basic():
    """Test create_espresso_profile prompt with basic parameters."""
    messages = create_espresso_profile()
    assert isinstance(messages, list)
    assert len(messages) >= 2  # System and user messages
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_create_espresso_profile_with_coffee_type():
    """Test create_espresso_profile with coffee type."""
    messages = create_espresso_profile(coffee_type="Colombian")
    assert isinstance(messages, list)
    content = messages[1]["content"]["text"]
    assert "Colombian" in content


def test_create_espresso_profile_with_roast_level_light():
    """Test create_espresso_profile with light roast."""
    messages = create_espresso_profile(roast_level="light")
    content = messages[1]["content"]["text"]
    assert "light" in content.lower()
    assert "higher temperature" in content.lower() or "92-96" in content


def test_create_espresso_profile_with_roast_level_dark():
    """Test create_espresso_profile with dark roast."""
    messages = create_espresso_profile(roast_level="dark")
    content = messages[1]["content"]["text"]
    assert "dark" in content.lower()
    assert "lower temperature" in content.lower() or "82-90" in content


def test_create_espresso_profile_with_coffee_age():
    """Test create_espresso_profile with fresh coffee."""
    messages = create_espresso_profile(coffee_age_days=3)
    content = messages[1]["content"]["text"]
    assert "fresh" in content.lower() or "3 days" in content
    assert "bloom" in content.lower()


def test_create_espresso_profile_with_style():
    """Test create_espresso_profile with style."""
    messages = create_espresso_profile(style="turbo")
    content = messages[1]["content"]["text"]
    assert "turbo" in content.lower() or "Turbo Shot" in content


def test_create_espresso_profile_with_target_weight():
    """Test create_espresso_profile with target weight."""
    messages = create_espresso_profile(target_weight=50.0)
    content = messages[1]["content"]["text"]
    assert "50" in content or "50.0" in content


def test_create_espresso_profile_with_all_params():
    """Test create_espresso_profile with all parameters."""
    messages = create_espresso_profile(
        coffee_type="Ethiopian",
        roast_level="light",
        style="turbo",
        target_weight=45.0,
        coffee_age_days=5,
    )
    content = messages[1]["content"]["text"]
    assert "Ethiopian" in content
    assert "light" in content.lower()
    assert "turbo" in content.lower()


def test_modify_espresso_profile_basic():
    """Test modify_espresso_profile prompt with basic parameters."""
    messages = modify_espresso_profile(profile_id="test-id")
    assert isinstance(messages, list)
    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "test-id" in messages[1]["content"]["text"]


def test_modify_espresso_profile_with_taste_issue_sour():
    """Test modify_espresso_profile with sour taste issue."""
    messages = modify_espresso_profile(profile_id="test-id", taste_issue="sour")
    content = messages[1]["content"]["text"]
    assert "under-extraction" in content.lower()


def test_modify_espresso_profile_with_taste_issue_bitter():
    """Test modify_espresso_profile with bitter taste issue."""
    messages = modify_espresso_profile(profile_id="test-id", taste_issue="bitter")
    content = messages[1]["content"]["text"]
    assert "over-extraction" in content.lower()


def test_modify_espresso_profile_with_taste_issue_gushing():
    """Test modify_espresso_profile with gushing issue."""
    messages = modify_espresso_profile(profile_id="test-id", taste_issue="gushing")
    content = messages[1]["content"]["text"]
    assert "gushing" in content.lower()


def test_modify_espresso_profile_with_taste_issue_choking():
    """Test modify_espresso_profile with choking issue."""
    messages = modify_espresso_profile(profile_id="test-id", taste_issue="choking")
    content = messages[1]["content"]["text"]
    assert "choking" in content.lower()


def test_modify_espresso_profile_with_modification_goal():
    """Test modify_espresso_profile with modification goal."""
    messages = modify_espresso_profile(
        profile_id="test-id",
        modification_goal="increase sweetness"
    )
    content = messages[1]["content"]["text"]
    assert "increase sweetness" in content


def test_troubleshoot_profile_basic():
    """Test troubleshoot_profile prompt with basic parameters."""
    messages = troubleshoot_profile(profile_id="test-id", symptom="sour taste")
    assert isinstance(messages, list)
    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "test-id" in messages[1]["content"]["text"]
    assert "sour taste" in messages[1]["content"]["text"]


def test_troubleshoot_profile_with_duration():
    """Test troubleshoot_profile with shot duration."""
    messages = troubleshoot_profile(
        profile_id="test-id",
        symptom="bitter",
        shot_duration=45.0
    )
    content = messages[1]["content"]["text"]
    assert "45" in content or "45.0" in content


def test_troubleshoot_profile_with_yield():
    """Test troubleshoot_profile with yield weight."""
    messages = troubleshoot_profile(
        profile_id="test-id",
        symptom="under-extracted",
        yield_weight=25.0
    )
    content = messages[1]["content"]["text"]
    assert "25" in content or "25.0" in content


def test_troubleshoot_profile_with_all_params():
    """Test troubleshoot_profile with all parameters."""
    messages = troubleshoot_profile(
        profile_id="test-id",
        symptom="channeling",
        shot_duration=30.0,
        yield_weight=35.0
    )
    content = messages[1]["content"]["text"]
    assert "test-id" in content
    assert "channeling" in content
    assert "30" in content or "30.0" in content
    assert "35" in content or "35.0" in content


def test_ensure_initialized_uses_env_var(reset_server_state):
    """Test _ensure_initialized uses environment variable for API URL."""
    with patch("meticulous_mcp.server.MeticulousAPIClient") as mock_client_class, \
         patch("meticulous_mcp.server.ProfileValidator") as mock_validator_class, \
         patch("meticulous_mcp.server.initialize_tools"), \
         patch("meticulous_mcp.server.Path") as mock_path_class, \
         patch.dict(os.environ, {"METICULOUS_API_URL": "http://custom.local"}):
        
        mock_client_class.return_value = Mock()
        mock_validator_class.return_value = Mock()
        
        # Setup path mocks with schema existing
        path_constructor, _ = setup_path_mocks(schema_exists=True)
        mock_path_class.side_effect = path_constructor
        
        server_module._ensure_initialized()
        
        # Verify API client was initialized with environment variable
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args
        assert call_args[1]["base_url"] == "http://custom.local"


def test_ensure_initialized_default_url(reset_server_state):
    """Test _ensure_initialized uses default URL when env var not set."""
    with patch("meticulous_mcp.server.MeticulousAPIClient") as mock_client_class, \
         patch("meticulous_mcp.server.ProfileValidator") as mock_validator_class, \
         patch("meticulous_mcp.server.initialize_tools"), \
         patch("meticulous_mcp.server.Path") as mock_path_class, \
         patch.dict(os.environ, {}, clear=True), \
         patch("os.getenv", side_effect=lambda key, default=None: default if key == "METICULOUS_API_URL" else None):
        
        mock_client_class.return_value = Mock()
        mock_validator_class.return_value = Mock()
        
        # Setup path mocks with schema existing
        path_constructor, _ = setup_path_mocks(schema_exists=True)
        mock_path_class.side_effect = path_constructor
        
        server_module._ensure_initialized()
        
        # Verify API client was initialized with default URL
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args
        assert "meticulousmodelalmondmilklatte.local" in call_args[1]["base_url"]

