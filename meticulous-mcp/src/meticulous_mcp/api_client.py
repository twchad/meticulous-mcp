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
from typing import List, Optional, Union

from meticulous.api import Api, APIError, Profile, PartialProfile, ActionResponse, ActionType, ChangeProfileResponse


class MeticulousAPIClient:
    """Wrapper around pyMeticulous Api with consistent error handling."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize the API client.
        
        Args:
            base_url: Base URL for the Meticulous API. If not provided, reads from
                     METICULOUS_API_URL environment variable. Defaults to
                     http://meticulousmodelalmondmilklatte.local
        """
        if base_url is None:
            base_url = os.getenv(
                "METICULOUS_API_URL", 
                "http://meticulousmodelalmondmilklatte.local"
            )
        self._api = Api(base_url=base_url)

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

    def get_last_profile(self) -> Union[Profile, APIError]:
        """Get the last loaded profile.
        
        Returns:
            Profile or APIError on failure
        """
        result = self._api.get_last_profile()
        if isinstance(result, APIError):
            return result
        return result.profile

