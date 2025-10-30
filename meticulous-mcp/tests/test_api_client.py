"""Tests for API client wrapper."""

import os
from unittest.mock import Mock, patch

import pytest
from meticulous.api import APIError, Profile, PartialProfile
from meticulous.api_types import ActionResponse, ActionType, ChangeProfileResponse, LastProfile

from meticulous_mcp.api_client import MeticulousAPIClient


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    with patch("meticulous_mcp.api_client.Api") as mock_api_class:
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        yield mock_api


@pytest.fixture
def api_client(mock_api):
    """Create an API client instance."""
    return MeticulousAPIClient(base_url="http://test.local")


def test_default_url():
    """Test that default URL is used when not provided."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("meticulous_mcp.api_client.Api") as mock_api_class:
            mock_api_instance = Mock()
            mock_api_instance.base_url = "http://meticulousmodelalmondmilklatte.local"
            mock_api_class.return_value = mock_api_instance
            client = MeticulousAPIClient()
            assert client.base_url == "http://meticulousmodelalmondmilklatte.local"


def test_custom_url():
    """Test that custom URL is used."""
    client = MeticulousAPIClient(base_url="http://custom.local")
    assert client.base_url == "http://custom.local"


def test_env_var_url():
    """Test that environment variable URL is used."""
    with patch.dict(os.environ, {"METICULOUS_API_URL": "http://env.local"}):
        client = MeticulousAPIClient()
        assert client.base_url == "http://env.local"


def test_list_profiles_success(api_client, mock_api):
    """Test successful profile listing."""
    expected_profiles = [
        PartialProfile(id="1", name="Test Profile"),
        PartialProfile(id="2", name="Another Profile"),
    ]
    mock_api.list_profiles.return_value = expected_profiles

    result = api_client.list_profiles()
    assert result == expected_profiles
    mock_api.list_profiles.assert_called_once()


def test_list_profiles_error(api_client, mock_api):
    """Test profile listing with API error."""
    error = APIError(error="Failed to fetch profiles")
    mock_api.list_profiles.return_value = error

    result = api_client.list_profiles()
    assert isinstance(result, APIError)
    assert result.error == "Failed to fetch profiles"


def test_get_profile_success(api_client, mock_api):
    """Test successful profile retrieval."""
    expected_profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    mock_api.get_profile.return_value = expected_profile

    result = api_client.get_profile("test-id")
    assert result == expected_profile
    mock_api.get_profile.assert_called_once_with("test-id")


def test_execute_action_success(api_client, mock_api):
    """Test successful action execution."""
    expected_response = ActionResponse(status="success", action="start")
    mock_api.execute_action.return_value = expected_response

    result = api_client.execute_action(ActionType.START)
    assert result == expected_response
    mock_api.execute_action.assert_called_once_with(ActionType.START)


def test_execute_action_error(api_client, mock_api):
    """Test action execution with API error."""
    error = APIError(error="Failed to execute action")
    mock_api.execute_action.return_value = error

    result = api_client.execute_action(ActionType.START)
    assert isinstance(result, APIError)
    assert result.error == "Failed to execute action"


def test_fetch_all_profiles_success(api_client, mock_api):
    """Test successful fetching of all profiles."""
    expected_profiles = [
        Profile(
            id="1",
            name="Profile 1",
            author="Author 1",
            author_id="author-1",
            temperature=90.0,
            final_weight=40.0,
            stages=[],
        ),
        Profile(
            id="2",
            name="Profile 2",
            author="Author 2",
            author_id="author-2",
            temperature=92.0,
            final_weight=42.0,
            stages=[],
        ),
    ]
    mock_api.fetch_all_profiles.return_value = expected_profiles

    result = api_client.fetch_all_profiles()
    assert result == expected_profiles
    mock_api.fetch_all_profiles.assert_called_once()


def test_fetch_all_profiles_error(api_client, mock_api):
    """Test fetching all profiles with API error."""
    error = APIError(error="Failed to fetch profiles")
    mock_api.fetch_all_profiles.return_value = error

    result = api_client.fetch_all_profiles()
    assert isinstance(result, APIError)
    assert result.error == "Failed to fetch profiles"


def test_get_profile_error(api_client, mock_api):
    """Test profile retrieval with API error."""
    error = APIError(error="Profile not found")
    mock_api.get_profile.return_value = error

    result = api_client.get_profile("nonexistent-id")
    assert isinstance(result, APIError)
    assert result.error == "Profile not found"


def test_save_profile_success(api_client, mock_api):
    """Test successful profile saving."""
    profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    expected_response = ChangeProfileResponse(change_id="change-1", profile=profile)
    mock_api.save_profile.return_value = expected_response

    result = api_client.save_profile(profile)
    assert result == expected_response
    mock_api.save_profile.assert_called_once_with(profile)


def test_save_profile_error(api_client, mock_api):
    """Test profile saving with API error."""
    profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    error = APIError(error="Failed to save profile")
    mock_api.save_profile.return_value = error

    result = api_client.save_profile(profile)
    assert isinstance(result, APIError)
    assert result.error == "Failed to save profile"


def test_load_profile_by_id_success(api_client, mock_api):
    """Test successful profile loading by ID."""
    expected_profile = PartialProfile(id="test-id", name="Test Profile")
    mock_api.load_profile_by_id.return_value = expected_profile

    result = api_client.load_profile_by_id("test-id")
    assert result == expected_profile
    mock_api.load_profile_by_id.assert_called_once_with("test-id")


def test_load_profile_by_id_error(api_client, mock_api):
    """Test profile loading by ID with API error."""
    error = APIError(error="Profile not found")
    mock_api.load_profile_by_id.return_value = error

    result = api_client.load_profile_by_id("nonexistent-id")
    assert isinstance(result, APIError)
    assert result.error == "Profile not found"


def test_load_profile_from_json_success(api_client, mock_api):
    """Test successful profile loading from JSON."""
    profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    expected_profile = PartialProfile(id="test-id", name="Test Profile")
    mock_api.load_profile_from_json.return_value = expected_profile

    result = api_client.load_profile_from_json(profile)
    assert result == expected_profile
    mock_api.load_profile_from_json.assert_called_once_with(profile)


def test_load_profile_from_json_error(api_client, mock_api):
    """Test profile loading from JSON with API error."""
    profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    error = APIError(error="Failed to load profile")
    mock_api.load_profile_from_json.return_value = error

    result = api_client.load_profile_from_json(profile)
    assert isinstance(result, APIError)
    assert result.error == "Failed to load profile"


def test_delete_profile_success(api_client, mock_api):
    """Test successful profile deletion."""
    # The API actually returns PartialProfile, not ChangeProfileResponse
    profile = PartialProfile(id="test-id", name="Test Profile")
    mock_api.delete_profile.return_value = profile

    result = api_client.delete_profile("test-id")
    assert result == profile
    mock_api.delete_profile.assert_called_once_with("test-id")


def test_delete_profile_error(api_client, mock_api):
    """Test profile deletion with API error."""
    error = APIError(error="Failed to delete profile")
    mock_api.delete_profile.return_value = error

    result = api_client.delete_profile("test-id")
    assert isinstance(result, APIError)
    assert result.error == "Failed to delete profile"


def test_get_last_profile_success(api_client, mock_api):
    """Test successful retrieval of last profile."""
    profile = Profile(
        id="test-id",
        name="Test Profile",
        author="Test Author",
        author_id="author-id",
        temperature=90.0,
        final_weight=40.0,
        stages=[],
    )
    last_profile = LastProfile(load_time=1234567890, profile=profile)
    mock_api.get_last_profile.return_value = last_profile

    result = api_client.get_last_profile()
    assert result == profile
    mock_api.get_last_profile.assert_called_once()


def test_get_last_profile_error(api_client, mock_api):
    """Test retrieval of last profile with API error."""
    error = APIError(error="No profile loaded")
    mock_api.get_last_profile.return_value = error

    result = api_client.get_last_profile()
    assert isinstance(result, APIError)
    assert result.error == "No profile loaded"


def test_base_url_property(api_client, mock_api):
    """Test base_url property."""
    mock_api.base_url = "http://test.local"
    assert api_client.base_url == "http://test.local"


def test_api_error_with_status(api_client, mock_api):
    """Test API error handling when status is provided instead of error."""
    error = APIError(status="404 Not Found")
    mock_api.get_profile.return_value = error

    result = api_client.get_profile("test-id")
    assert isinstance(result, APIError)
    assert result.status == "404 Not Found"


def test_api_error_with_both_status_and_error(api_client, mock_api):
    """Test API error handling when both status and error are provided."""
    error = APIError(error="Custom error", status="500 Internal Server Error")
    mock_api.list_profiles.return_value = error

    result = api_client.list_profiles()
    assert isinstance(result, APIError)
    assert result.error == "Custom error"
    assert result.status == "500 Internal Server Error"

