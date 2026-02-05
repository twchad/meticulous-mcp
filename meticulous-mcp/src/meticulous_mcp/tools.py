"""MCP tools for managing espresso profiles.

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

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

from meticulous.api_types import APIError, ActionType
from meticulous.profile import Profile

from .api_client import MeticulousAPIClient
from .profile_builder import (
    create_profile,
    create_stage,
    create_dynamics,
    create_exit_trigger,
    create_limit,
    create_variable,
    profile_to_dict,
    dict_to_profile,
    normalize_profile,
)
from .profile_validator import ProfileValidationError, ProfileValidator


# Pydantic models for structured tool inputs
class StageInput(BaseModel):
    """Input model for creating a stage."""

    name: str = Field(description="Stage name")
    key: str = Field(description="Stage key (unique identifier)")
    stage_type: str = Field(description="Stage type: 'power', 'flow', or 'pressure'", alias="type")
    dynamics_points: List[List[Union[float, str]]] = Field(
        description="List of [x, y] points for dynamics curve. Values can be numbers or variable references like '$pressure_1'"
    )
    dynamics_over: str = Field(
        description="What to interpolate over: 'piston_position', 'time', or 'weight'"
    )
    dynamics_interpolation: str = Field(
        default="linear", description="Interpolation method: 'linear' or 'curve'. Note: 'none' is not supported by the machine."
    )
    exit_triggers: List[Dict[str, Any]] = Field(
        description="List of exit trigger dictionaries. Each trigger must contain 'type' and 'value'. Optional fields: 'relative' (boolean, whether value is relative to stage start), 'comparison' (string, '>=' or '<=' to transition based on sensor readings). If multiple triggers are present, the stage will exit as soon as the FIRST condition is met (logical OR). Example: [{'type': 'weight', 'value': 30, 'comparison': '>='}] exits when weight reaches or exceeds 30g."
    )
    limits: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Optional list of limit dictionaries with 'type' and 'value' (can be number or variable reference like '$flow_1')"
    )


class VariableInput(BaseModel):
    """Input model for creating a variable."""

    name: str = Field(description="Variable name")
    key: str = Field(description="Variable key (used for references)")
    var_type: str = Field(
        description="Variable type: 'power', 'flow', 'pressure', 'weight', 'time', or 'piston_position'",
        alias="type",
    )
    value: float = Field(description="Variable value")


class ProfileCreateInput(BaseModel):
    """Input model for creating a profile."""

    name: str = Field(description="Profile name")
    author: str = Field(description="Author name")
    author_id: Optional[str] = Field(default=None, description="Author ID (UUID). If not provided, generates one.")
    temperature: float = Field(default=90.0, description="Brew temperature in Celsius")
    final_weight: float = Field(default=40.0, description="Target final weight in grams")
    stages: List[StageInput] = Field(description="List of stages")
    variables: Optional[List[VariableInput]] = Field(default=None, description="Optional list of variables")
    accent_color: Optional[str] = Field(
        default=None, description="Optional accent color in hex format (e.g., '#FF5733')"
    )


class ProfileUpdateInput(BaseModel):
    """Input model for updating a profile."""

    profile_id: str = Field(description="Profile ID to update")
    name: Optional[str] = Field(default=None, description="New profile name")
    temperature: Optional[float] = Field(default=None, description="New temperature")
    final_weight: Optional[float] = Field(default=None, description="New final weight")
    # Accept stages as either a list of dicts or a JSON string
    stages: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Optional list of stage dictionaries (full replacement)"
    )
    stages_json: Optional[str] = Field(
        default=None, description="Optional JSON string for updated stages (full replacement). Alternative to 'stages' field."
    )
    variables_json: Optional[str] = Field(
        default=None, description="Optional JSON string for updated variables (full replacement)"
    )


# Global instances (will be initialized in server.py)
_api_client: Optional[MeticulousAPIClient] = None
_validator: Optional[ProfileValidator] = None


def initialize_tools(api_client: MeticulousAPIClient, validator: ProfileValidator) -> None:
    """Initialize tools with API client and validator.
    
    Args:
        api_client: The API client instance
        validator: The profile validator instance
    """
    global _api_client, _validator
    _api_client = api_client
    _validator = validator


def _ensure_initialized() -> None:
    """Ensure tools are initialized."""
    if _api_client is None or _validator is None:
        raise RuntimeError("Tools not initialized. Call initialize_tools() first.")


def _handle_api_error(result: Union[Any, APIError], operation: str) -> str:
    """Handle API error results.
    
    Args:
        result: API result (could be APIError)
        operation: Operation name for error message
        
    Returns:
        Success message or raises exception with error details
    """
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"{operation} failed: {error_msg}")
    return f"{operation} succeeded"


def _format_validation_errors(errors: List[str]) -> str:
    """Format validation errors into a clear, actionable message.
    
    Args:
        errors: List of error messages
        
    Returns:
        Formatted error message with helpful hints
    """
    error_lines = ["Profile validation failed. Please fix the following issues:"]
    error_lines.append("")
    
    for i, error in enumerate(errors, 1):
        error_lines.append(f"{i}. {error}")
    
    error_lines.append("")
    error_lines.append("Common issues and fixes:")
    error_lines.append("  - Missing required fields: Ensure all required fields are provided")
    error_lines.append("  - Invalid stage format: Each stage must have 'name', 'key', 'type', 'dynamics', and 'exit_triggers'")
    error_lines.append("  - Invalid dynamics: 'dynamics.points' must be a list of [x, y] pairs")
    error_lines.append("  - Missing exit triggers: Each stage must have at least one exit trigger")
    error_lines.append("  - Variable references: Use format '$variable_key' (e.g., '$pressure_1')")
    
    return "\n".join(error_lines)


def create_profile_tool(input_data: ProfileCreateInput) -> Dict[str, Any]:
    """Create a new espresso profile.
    
    Args:
        input_data: Profile creation input
        
    Returns:
        Dictionary with profile ID and success message
        
    Raises:
        Exception: With detailed validation errors if profile creation fails
    """
    _ensure_initialized()
    
    try:
        # Build stages
        stages = []
        for idx, stage_input in enumerate(input_data.stages, 1):
            try:
                exit_triggers = [
                    create_exit_trigger(
                        trigger_type=et["type"],
                        value=et["value"],
                        relative=et.get("relative"),
                        comparison=et.get("comparison"),
                    )
                    for et in stage_input.exit_triggers
                ]
                
                limits = None
                if stage_input.limits:
                    limits = [
                        create_limit(limit_type=limit["type"], value=limit["value"])
                        for limit in stage_input.limits
                    ]
                
                dynamics = create_dynamics(
                    points=stage_input.dynamics_points,
                    over=stage_input.dynamics_over,
                    interpolation=stage_input.dynamics_interpolation,
                )
                
                stage = create_stage(
                    name=stage_input.name,
                    key=stage_input.key,
                    stage_type=stage_input.stage_type,
                    dynamics=dynamics,
                    exit_triggers=exit_triggers,
                    limits=limits,
                )
                stages.append(stage)
            except (PydanticValidationError, KeyError, TypeError) as e:
                stage_name = stage_input.name if hasattr(stage_input, 'name') else f"Stage {idx}"
                if isinstance(e, PydanticValidationError):
                    error_details = []
                    for error in e.errors():
                        field = " -> ".join(str(x) for x in error.get("loc", []))
                        msg = error.get("msg", "Validation error")
                        error_details.append(f"{field}: {msg}")
                    raise Exception(
                        f"Error creating stage '{stage_name}':\n" + 
                        "\n".join(f"  - {detail}" for detail in error_details)
                    )
                else:
                    raise Exception(f"Error creating stage '{stage_name}': {str(e)}")
        
        # Build variables
        variables = None
        if input_data.variables:
            variables = [
                create_variable(
                    name=var.name,
                    key=var.key,
                    var_type=var.var_type,
                    value=var.value,
                )
                for var in input_data.variables
            ]
        
        # Create profile
        profile = create_profile(
            name=input_data.name,
            author=input_data.author,
            author_id=input_data.author_id,
            temperature=input_data.temperature,
            final_weight=input_data.final_weight,
            stages=stages,
            variables=variables,
        )
        
        # Add display if accent_color provided
        if input_data.accent_color:
            from meticulous.profile import Display
            profile.display = Display(accentColor=input_data.accent_color)
        
        # Lint profile BEFORE normalization to catch issues that will be auto-fixed
        # This helps agents understand what normalization will happen
        profile_dict_for_linting = profile_to_dict(profile, normalize=False)
        warnings = _validator.lint(profile_dict_for_linting)
        
        # Validate profile (use normalized version for validation)
        profile_dict = profile_to_dict(profile, normalize=True)
        
        # Run validation (will raise if invalid)
        _validator.validate_and_raise(profile_dict)
        
    except ProfileValidationError as e:
        # Get linting warnings even if validation fails
        warnings = []
        try:
            profile_dict_for_linting = profile_to_dict(profile, normalize=False)
            warnings = _validator.lint(profile_dict_for_linting)
        except Exception:
            pass  # Ignore lint errors if we can't generate them
        
        # Format errors with helpful hints
        formatted_errors = _format_validation_errors(e.errors)
        error_msg = formatted_errors
        
        # Include warnings if any
        if warnings:
            error_msg += "\n\nAdditional warnings:\n"
            for i, warning in enumerate(warnings, 1):
                error_msg += f"  {i}. {warning}\n"
        
        raise Exception(error_msg)
    except PydanticValidationError as e:
        # Handle Pydantic validation errors during profile creation
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error.get("loc", []))
            msg = error.get("msg", "Validation error")
            error_details.append(f"{field}: {msg}")
        raise Exception(
            "Profile creation failed due to validation errors:\n" + 
            "\n".join(f"  - {detail}" for detail in error_details)
        )
    
    # Normalize profile before saving (ensures empty limits lists become None)
    normalized_profile = normalize_profile(profile)
    
    # Save profile
    result = _api_client.save_profile(normalized_profile)
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to save profile: {error_msg}")
    
    # Build response with warnings if any
    response = {
        "profile_id": result.profile.id,
        "profile_name": result.profile.name,
        "message": f"Profile '{input_data.name}' created successfully",
    }
    
    # Include linting warnings in response (even on success)
    if warnings:
        response["warnings"] = warnings
        response["message"] += f" (with {len(warnings)} warning(s) - see 'warnings' field)"
    
    return response


def list_profiles_tool() -> List[Dict[str, Any]]:
    """List all available profiles.
    
    Returns:
        List of profile dictionaries with basic information
    """
    _ensure_initialized()
    
    result = _api_client.list_profiles()
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to list profiles: {error_msg}")
    
    return [
        {
            "id": profile.id if hasattr(profile, "id") else profile.model_dump().get("id"),
            "name": profile.name if hasattr(profile, "name") else profile.model_dump().get("name"),
        }
        for profile in result
    ]


def get_profile_tool(profile_id: str) -> Dict[str, Any]:
    """Get full profile details by ID.
    
    Args:
        profile_id: Profile ID
        
    Returns:
        Dictionary with full profile data
    """
    _ensure_initialized()
    
    result = _api_client.get_profile(profile_id)
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to get profile: {error_msg}")
    
    return profile_to_dict(result)


def update_profile_tool(input_data: ProfileUpdateInput) -> Dict[str, Any]:
    """Update an existing profile.
    
    Args:
        input_data: Profile update input
        
    Returns:
        Dictionary with updated profile ID and success message
    """
    _ensure_initialized()
    
    # Get existing profile
    existing = _api_client.get_profile(input_data.profile_id)
    if isinstance(existing, APIError):
        error_msg = existing.error or existing.status or "Unknown error"
        raise Exception(f"Failed to get profile: {error_msg}")
    
    # Update fields
    if input_data.name is not None:
        existing.name = input_data.name
    if input_data.temperature is not None:
        existing.temperature = input_data.temperature
    if input_data.final_weight is not None:
        existing.final_weight = input_data.final_weight
    
    # Update stages if provided (accept either 'stages' list or 'stages_json' string)
    stages_to_process = None
    if input_data.stages is not None:
        stages_to_process = input_data.stages
    elif input_data.stages_json:
        import json
        if isinstance(input_data.stages_json, str):
            stages_to_process = json.loads(input_data.stages_json)
        else:
            stages_to_process = input_data.stages_json
    
    if stages_to_process is not None:
        import json
        try:
            stages_data = stages_to_process
            
            # Transform stages from input format to Stage model format
            transformed_stages = []
            for stage_data in stages_data:
                # Make a copy to avoid mutating the original
                stage_dict = dict(stage_data)
                
                # Convert dynamics_points/dynamics_over format to dynamics object
                if "dynamics_points" in stage_dict or "dynamics_over" in stage_dict:
                    dynamics_points = stage_dict.pop("dynamics_points", [])
                    dynamics_over = stage_dict.pop("dynamics_over", "time")
                    dynamics_interpolation = stage_dict.pop("dynamics_interpolation", "linear")
                    
                    stage_dict["dynamics"] = {
                        "points": dynamics_points,
                        "over": dynamics_over,
                        "interpolation": dynamics_interpolation,
                    }
                
                # Ensure exit_triggers is a list
                if "exit_triggers" not in stage_dict:
                    stage_dict["exit_triggers"] = []
                
                # Normalize exit_triggers - ensure relative is always present
                for trigger in stage_dict["exit_triggers"]:
                    if "relative" not in trigger or trigger.get("relative") is None:
                        # Default relative to True for time triggers (stage duration), False for others (absolute value)
                        if trigger.get("type") == "time":
                            trigger["relative"] = True
                        else:
                            trigger["relative"] = False
                
                # Ensure limits is always present as an array (empty if None/missing)
                # The machine expects limits to always be an array, not None or missing
                if "limits" not in stage_dict or stage_dict.get("limits") is None:
                    stage_dict["limits"] = []
                elif isinstance(stage_dict["limits"], list) and len(stage_dict["limits"]) == 0:
                    # Keep as empty array
                    stage_dict["limits"] = []
                
                transformed_stages.append(stage_dict)
            
            # Rebuild stages from transformed data
            from meticulous.profile import Stage
            try:
                new_stages = []
                for idx, stage_dict in enumerate(transformed_stages):
                    try:
                        stage = Stage(**stage_dict)
                        new_stages.append(stage)
                    except PydanticValidationError as e:
                        stage_name = stage_dict.get("name", f"Stage {idx+1}")
                        error_details = []
                        for error in e.errors():
                            field = " -> ".join(str(x) for x in error.get("loc", []))
                            msg = error.get("msg", "Validation error")
                            error_details.append(f"{field}: {msg}")
                        raise Exception(
                            f"Invalid stage format for stage '{stage_name}':\n" + 
                            "\n".join(f"  - {detail}" for detail in error_details) +
                            f"\n\nStage data: {json.dumps(stage_dict, indent=2)}"
                        )
                
                # Only update if we successfully created all stages
                existing.stages = new_stages
                
            except Exception as e:
                # Re-raise if already formatted
                if "Invalid stage format" in str(e):
                    raise
                # Otherwise wrap it
                raise Exception(f"Error creating stages: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in stages_json: {e}")
        except Exception as e:
            # Re-raise if already formatted
            if isinstance(e, Exception) and "Invalid stage format" in str(e):
                raise
            raise Exception(f"Error processing stages: {e}")
    
    # Update variables if provided
    if input_data.variables_json:
        import json
        try:
            variables_data = json.loads(input_data.variables_json)
            from meticulous.profile import Variable
            existing.variables = [Variable(**var) for var in variables_data] if variables_data else None
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in variables_json: {e}")
        except PydanticValidationError as e:
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(x) for x in error.get("loc", []))
                msg = error.get("msg", "Validation error")
                error_details.append(f"{field}: {msg}")
            raise Exception(
                "Invalid variable format:\n" + 
                "\n".join(f"  - {detail}" for detail in error_details)
            )
    
    # Validate updated profile
    warnings = []  # Initialize warnings list
    try:
        # Lint profile BEFORE normalization to catch issues that will be auto-fixed
        # This helps agents understand what normalization will happen
        profile_dict_for_linting = profile_to_dict(existing, normalize=False)
        warnings = _validator.lint(profile_dict_for_linting)
        
        # Validate profile (use normalized version for validation)
        profile_dict = profile_to_dict(existing, normalize=True)
        
        # Run validation (will raise if invalid)
        _validator.validate_and_raise(profile_dict)
        
    except ProfileValidationError as e:
        # Get linting warnings even if validation fails (might help with context)
        try:
            profile_dict_for_linting = profile_to_dict(existing, normalize=False)
            warnings = _validator.lint(profile_dict_for_linting)
        except Exception:
            warnings = []  # Ensure warnings is initialized even if linting fails
        
        formatted_errors = _format_validation_errors(e.errors)
        error_msg = formatted_errors
        
        # Include warnings if any
        if warnings:
            error_msg += "\n\nAdditional warnings:\n"
            for i, warning in enumerate(warnings, 1):
                error_msg += f"  {i}. {warning}\n"
        
        raise Exception(error_msg)
    
    # Normalize profile before saving (ensures empty limits lists become None)
    normalized_profile = normalize_profile(existing)
    
    # Save updated profile
    result = _api_client.save_profile(normalized_profile)
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to update profile: {error_msg}")
    
    # Build response with warnings if any
    response = {
        "profile_id": result.profile.id,
        "profile_name": result.profile.name,
        "message": f"Profile '{result.profile.name}' updated successfully",
    }
    
    # Include linting warnings in response (even on success)
    if warnings:
        response["warnings"] = warnings
        response["message"] += f" (with {len(warnings)} warning(s) - see 'warnings' field)"
    
    return response


def duplicate_profile_tool(
    profile_id: str, new_name: str, modify_temperature: Optional[float] = None
) -> Dict[str, Any]:
    """Duplicate a profile and optionally modify it.
    
    Args:
        profile_id: Profile ID to duplicate
        new_name: Name for the new profile
        modify_temperature: Optional temperature to set for the new profile
        
    Returns:
        Dictionary with new profile ID and success message
    """
    _ensure_initialized()
    
    # Get existing profile
    existing = _api_client.get_profile(profile_id)
    if isinstance(existing, APIError):
        error_msg = existing.error or existing.status or "Unknown error"
        raise Exception(f"Failed to get profile: {error_msg}")
    
    # Create new profile with modifications
    import uuid
    new_profile = create_profile(
        name=new_name,
        author=existing.author,
        author_id=existing.author_id,
        temperature=modify_temperature if modify_temperature is not None else existing.temperature,
        final_weight=existing.final_weight,
        stages=existing.stages,
        variables=existing.variables,
        display=existing.display,
        previous_authors=existing.previous_authors,
        profile_id=str(uuid.uuid4()),
    )
    
    # Normalize profile before saving (ensures empty limits lists become None)
    normalized_new_profile = normalize_profile(new_profile)
    
    # Validate new profile
    profile_dict = profile_to_dict(normalized_new_profile)
    _validator.validate_and_raise(profile_dict)
    
    # Save new profile
    result = _api_client.save_profile(normalized_new_profile)
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to save duplicated profile: {error_msg}")
    
    return {
        "profile_id": result.profile.id,
        "profile_name": result.profile.name,
        "message": f"Profile '{new_name}' duplicated from '{existing.name}'",
    }


def delete_profile_tool(profile_id: str) -> Dict[str, Any]:
    """Delete a profile permanently.
    
    ⚠️ WARNING: This is a destructive operation that cannot be undone.
    
    IMPORTANT: Before calling this tool, you MUST:
    1. First retrieve the profile using get_profile to see its details
    2. Confirm with the user that they want to delete this specific profile
    3. Only proceed if the user explicitly confirms the deletion
    
    Do NOT delete profiles without explicit user confirmation.
    
    Args:
        profile_id: Profile ID to delete
        
    Returns:
        Dictionary with success message including profile name
    """
    _ensure_initialized()
    
    # First, try to get the profile to show what's being deleted
    # This helps verify the profile exists and provides better feedback
    profile_name = profile_id  # Default to ID if we can't retrieve name
    try:
        existing = _api_client.get_profile(profile_id)
        if not isinstance(existing, APIError):
            profile_name = existing.name
    except Exception:
        # If we can't retrieve it, use the ID
        pass
    
    result = _api_client.delete_profile(profile_id)
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to delete profile: {error_msg}")
    
    return {
        "profile_id": profile_id,
        "profile_name": profile_name,
        "message": f"Profile '{profile_name}' has been permanently deleted. This action cannot be undone.",
    }


def validate_profile_tool(profile_json: str) -> Dict[str, Any]:
    """Validate a profile JSON against the schema.
    
    This tool can validate both:
    1. New profiles (using create_profile input format - without id/author_id)
    2. Existing profiles (full profile format with id/author_id)
    
    Args:
        profile_json: JSON string of the profile
        
    Returns:
        Dictionary with validation results and any warnings
    """
    _ensure_initialized()
    
    import json
    import uuid
    
    try:
        profile_dict = json.loads(profile_json)
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON: {e}")
    
    # Determine if this is a new profile or existing profile
    has_id = "id" in profile_dict
    has_author_id = "author_id" in profile_dict
    is_existing_profile = has_id and has_author_id
    
    if not is_existing_profile:
        # This is a new profile in create_profile input format
        # Validate as ProfileCreateInput first
        try:
            profile_input = ProfileCreateInput(**profile_dict)
        except PydanticValidationError as e:
            # Return input validation errors
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(x) for x in error.get("loc", []))
                msg = error.get("msg", "Validation error")
                error_details.append(f"{field}: {msg}")
            
            return {
                "valid": False,
                "errors": error_details,
                "warnings": [],
                "message": f"Profile has {len(error_details)} validation error(s)",
            }
        
        # Convert to full profile format for validation
        # Build the profile using the same logic as create_profile_tool
        try:
            stages = []
            for stage_input in profile_input.stages:
                exit_triggers = [
                    create_exit_trigger(
                        trigger_type=et["type"],
                        value=et["value"],
                        relative=et.get("relative"),
                        comparison=et.get("comparison"),
                    )
                    for et in stage_input.exit_triggers
                ]
                
                limits = None
                if stage_input.limits:
                    limits = [
                        create_limit(limit_type=limit["type"], value=limit["value"])
                        for limit in stage_input.limits
                    ]
                
                dynamics = create_dynamics(
                    points=stage_input.dynamics_points,
                    over=stage_input.dynamics_over,
                    interpolation=stage_input.dynamics_interpolation,
                )
                
                stage = create_stage(
                    name=stage_input.name,
                    key=stage_input.key,
                    stage_type=stage_input.stage_type,
                    dynamics=dynamics,
                    exit_triggers=exit_triggers,
                    limits=limits,
                )
                stages.append(stage)
            
            variables = None
            if profile_input.variables:
                variables = [
                    create_variable(
                        name=var.name,
                        key=var.key,
                        var_type=var.var_type,
                        value=var.value,
                    )
                    for var in profile_input.variables
                ]
            
            # Create profile with temporary IDs for validation
            profile = create_profile(
                name=profile_input.name,
                author=profile_input.author,
                author_id=profile_input.author_id or str(uuid.uuid4()),
                temperature=profile_input.temperature,
                final_weight=profile_input.final_weight,
                stages=stages,
                variables=variables,
                profile_id=str(uuid.uuid4()),  # Temporary ID for validation
            )
            
            # Convert to dict for validation
            profile_dict = profile_to_dict(profile, normalize=True)
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Error building profile: {str(e)}"],
                "warnings": [],
                "message": "Profile has validation error(s)",
            }
    
    # Validate the full profile format
    is_valid, errors = _validator.validate(profile_dict)
    warnings = _validator.lint(profile_dict)
    
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "message": "Profile is valid" if is_valid else f"Profile has {len(errors)} validation error(s)",
    }


def run_profile_tool(profile_id: str) -> Dict[str, Any]:
    """Load and execute a profile (without saving).
    
    Args:
        profile_id: Profile ID to run
        
    Returns:
        Dictionary with success message
    """
    _ensure_initialized()
    
    # Load profile
    result = _api_client.load_profile_by_id(profile_id)
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to load profile: {error_msg}")
    
    # Execute start action
    action_result = _api_client.execute_action(ActionType.START)
    if isinstance(action_result, APIError):
        error_msg = action_result.error or action_result.status or "Unknown error"
        raise Exception(f"Failed to start profile: {error_msg}")
    
    return {
        "profile_id": profile_id,
        "message": f"Profile '{profile_id}' loaded and started",
        "action": action_result.action,
        "status": action_result.status,
    }

def list_shot_history_tool(date: Optional[str] = None) -> Dict[str, Any]:
    """List available shot history (dates or files).
    
    Args:
        date: Optional date string (YYYY-MM-DD). If provided, lists files for that date.
              If not provided, lists available dates.
    
    Returns:
        Dictionary containing list of dates or files.
    """
    _ensure_initialized()
    
    if date:
        result = _api_client.get_shot_files(date)
        if isinstance(result, APIError):
            error_msg = result.error or result.status or "Unknown error"
            raise Exception(f"Failed to list shot files for {date}: {error_msg}")
        return {"files": [f.name for f in result]}
    
    result = _api_client.get_history_dates()
    if isinstance(result, APIError):
         error_msg = result.error or result.status or "Unknown error"
         raise Exception(f"Failed to list history: {error_msg}")
         
    return {"dates": [d.name for d in result]}

def get_shot_url_tool(date: str, filename: str) -> Dict[str, str]:
    """Get the download URL for a specific shot.
    
    Args:
        date: Date string (YYYY-MM-DD).
        filename: Shot filename (e.g. HH:MM:SS.shot.json.zst).
        
    Returns:
        Dictionary containing the URL.
    """
    _ensure_initialized()
    
    url = _api_client.get_shot_url(date, filename)
    return {"url": url}


def get_machine_status_tool() -> Dict[str, Any]:
    """Get the current status of the Meticulous machine.
    
    Returns:
        Dictionary containing machine status (temperature, water level, state).
    """
    _ensure_initialized()
    
    result = _api_client.get_machine_status()
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to get machine status: {error_msg}")
    
    if result is None:
        return {
            "state": "idle",
            "message": "Machine is idle (no active shot)"
        }
    
    # If it's a Pydantic model, dump it to dict
    if hasattr(result, "model_dump"):
        return result.model_dump()
        
    return result


def get_settings_tool() -> Dict[str, Any]:
    """Get the current settings of the Meticulous machine.
    
    Returns:
        Dictionary containing settings (auto_preheat, sounds, etc).
    """
    _ensure_initialized()
    
    try:
        result = _api_client.get_settings()
        if isinstance(result, APIError):
            error_msg = result.error or result.status or "Unknown error"
            raise Exception(f"Failed to get settings: {error_msg}")
        
        # If it's a Pydantic model, dump it to dict
        if hasattr(result, "model_dump"):
            return result.model_dump()
            
        return result
    except Exception as e:
        # Fallback: if validation failed in the client wrapper, try to get raw settings
        # This handles cases where the machine firmware has new/different fields than the SDK expects
        try:
            # We access the internal API session directly to bypass strict validation
            if hasattr(_api_client, "_api") and hasattr(_api_client._api, "session") and hasattr(_api_client._api, "base_url"):
                response = _api_client._api.session.get(f"{_api_client._api.base_url}/api/v1/settings")
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass # Fallback failed, raise original error
            
        raise Exception(f"Failed to get settings: {e}")


def update_setting_tool(key: str, value: Any) -> Dict[str, Any]:
    """Update a specific setting on the Meticulous machine.
    
    Args:
        key: The setting key to update (e.g., 'auto_preheat').
        value: The new value for the setting.
        
    Returns:
        Dictionary confirming the update.
    """
    _ensure_initialized()
    
    result = _api_client.update_setting(key, value)
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        raise Exception(f"Failed to update setting '{key}': {error_msg}")
    
    return {
        "message": f"Setting '{key}' updated successfully",
        "key": key,
        "value": value,
        "settings": result
    }
