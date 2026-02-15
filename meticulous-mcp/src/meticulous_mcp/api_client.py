"""API client wrapper for Meticulous espresso machine.

Copyright (C) 2024 Meticulous MCP

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
from typing import List, Optional, Union, Dict, Any

from meticulous.api import Api, APIError, Profile, PartialProfile, ActionResponse, ActionType, ChangeProfileResponse, HistoryFile


class MeticulousAPIClient:
    """Wrapper around pyMeticulous Api with consistent error handling."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize the API client.

        Args:
            base_url: Base URL for the Meticulous API. If not provided, reads from
                     METICULOUS_API_URL environment variable.

        Raises:
            ValueError: If no base URL is provided and METICULOUS_API_URL is not set.
        """
        if base_url is None:
            base_url = os.getenv("METICULOUS_API_URL")
        if not base_url:
            raise ValueError(
                "METICULOUS_API_URL environment variable is required. "
                "Set it to your machine's address (e.g. http://meticulous.local or http://192.168.1.5)"
            )
        self._api = Api(base_url=base_url)

    def _ensure_socket(self) -> None:
        """Connect to socket.io if not already connected."""
        if not self._api.sio.connected:
            self._api.connect_to_socket()

    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return self._api.base_url

    def list_profiles(self) -> Union[List[PartialProfile], APIError]:
        """List all profiles (partial information).
        
        Returns:
            List of PartialProfile objects or APIError on failure
        """
        return self._api.list_profiles()

    def get_profile(self, profile_id: str) -> Union[Profile, APIError]:
        """Get full profile details by ID.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            Profile object or APIError on failure
        """
        return self._api.get_profile(profile_id)

    def fetch_all_profiles(self) -> Union[List[Profile], APIError]:
        """Fetch all profiles with full details.
        
        Returns:
            List of Profile objects or APIError on failure
        """
        return self._api.fetch_all_profiles()

    def save_profile(self, profile: Profile) -> Union[ChangeProfileResponse, APIError]:
        """Save a profile to the machine.
        
        Args:
            profile: The Profile object to save
            
        Returns:
            ChangeProfileResponse containing the saved profile or APIError on failure
        """
        return self._api.save_profile(profile)

    def select_profile(self, profile_id: str) -> None:
        """Select a profile on the machine without starting it.

        Sets the active profile on the machine's display via socket.io.
        The user can then manually start the shot from the machine.

        Args:
            profile_id: The profile ID to select
        """
        self._ensure_socket()
        self._api.send_profile_hover({"id": profile_id, "from": "app", "type": "focus"})

    def load_profile_by_id(self, profile_id: str) -> Union[PartialProfile, APIError]:
        """Load a profile by ID into the machine.
        
        Args:
            profile_id: The profile ID to load
            
        Returns:
            PartialProfile or APIError on failure
        """
        return self._api.load_profile_by_id(profile_id)

    def load_profile_from_json(self, profile: Profile) -> Union[PartialProfile, APIError]:
        """Load a profile from JSON into the machine (without saving).
        
        Args:
            profile: The Profile object to load
            
        Returns:
            PartialProfile or APIError on failure
        """
        return self._api.load_profile_from_json(profile)

    def delete_profile(self, profile_id: str) -> Union[ChangeProfileResponse, APIError]:
        """Delete a profile.
        
        Args:
            profile_id: The profile ID to delete
            
        Returns:
            ChangeProfileResponse or APIError on failure
        """
        return self._api.delete_profile(profile_id)

    def execute_action(self, action: ActionType) -> Union[ActionResponse, APIError]:
        """Execute an action on the machine.
        
        Args:
            action: The action to execute (start, stop, reset, tare, calibration)
            
        Returns:
            ActionResponse or APIError on failure
        """
        return self._api.execute_action(action)

    def get_machine_info(self):
        """Get machine device info (firmware, serial, name, etc.)."""
        return self._api.get_device_info()

    def get_settings(self) -> Union[Dict[str, Any], APIError]:
        """Get machine settings.
        
        Returns:
            Dictionary with settings or APIError on failure
        """
        try:
            return self._api.get_settings()
        except Exception:
            # Fallback for validation errors or other issues
            # Direct access to session to get raw JSON
            try:
                # We need to make sure the base_url is properly formatted
                base = self.base_url.rstrip('/')
                response = self._api.session.get(f"{base}/api/v1/settings")
                if response.status_code == 200:
                    return response.json()
                return APIError(status=str(response.status_code), error=response.text)
            except Exception as e:
                return APIError(status="Error", error=str(e))

    def update_setting(self, key: str, value: Any) -> Union[Dict[str, Any], APIError]:
        """Update a machine setting.
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            Dictionary with updated settings or APIError on failure
        """
        return self._api.update_setting(key, value)

    def get_last_profile(self) -> Union[Profile, APIError]:
        """Get the last loaded profile.
        
        Returns:
            Profile or APIError on failure
        """
        result = self._api.get_last_profile()
        if isinstance(result, APIError):
            return result
        return result.profile
    
    def get_history_dates(self) -> Union[List[HistoryFile], APIError]:
        """Get list of dates available in history.
        
        Returns:
            List of HistoryFile objects (directories) or APIError on failure
        """
        return self._api.get_history_dates()
        
    def get_shot_files(self, date_str: str) -> Union[List[HistoryFile], APIError]:
        """Get list of shot files for a specific date.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            
        Returns:
            List of HistoryFile objects (files) or APIError on failure
        """
        return self._api.get_shot_files(date_str)

    def get_shot_url(self, date_str: str, filename: str) -> str:
        """Get the full URL for a shot log file.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            filename: Filename (e.g. HH:MM:SS.shot.json.zst)
            
        Returns:
            Full URL string
        """
        base = self.base_url.rstrip('/')
        return f"{base}/api/v1/history/files/{date_str}/{filename}"

