"""Profile builder helpers for creating espresso profiles.

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

import uuid
from typing import Any, Dict, List, Optional, Union

from meticulous.profile import (
    Profile,
    Stage,
    Dynamics,
    ExitTrigger,
    Limit,
    Variable,
    Display,
    PreviousAuthor,
)


def create_variable(
    name: str,
    key: str,
    var_type: str,
    value: float,
) -> Variable:
    """Create a profile variable.
    
    Args:
        name: Variable name
        key: Variable key (used for references)
        var_type: Type: "power", "flow", "pressure", "weight", "time", "piston_position"
        value: Variable value
        
    Returns:
        Variable object
    """
    return Variable(name=name, key=key, type=var_type, value=value)


def create_exit_trigger(
    trigger_type: str,
    value: Union[float, str],
    relative: Optional[bool] = None,
    comparison: Optional[str] = None,
) -> ExitTrigger:
    """Create an exit trigger.
    
    Args:
        trigger_type: Type: "weight", "pressure", "flow", "time", "piston_position", "power", "user_interaction"
        value: Trigger value (number or variable reference like "$pressure_1")
        relative: Whether the value is relative
        comparison: Comparison operator: ">=" or "<="
        
    Returns:
        ExitTrigger object
    """
    return ExitTrigger(
        type=trigger_type,
        value=value,
        relative=relative,
        comparison=comparison,
    )


def create_limit(
    limit_type: str,
    value: Union[float, str],
) -> Limit:
    """Create a limit.
    
    Args:
        limit_type: Type: "pressure" or "flow"
        value: Limit value (number or variable reference like "$pressure_1")
        
    Returns:
        Limit object
    """
    return Limit(type=limit_type, value=value)


def create_dynamics(
    points: List[List[Union[float, str]]],
    over: str,
    interpolation: str = "linear",
) -> Dynamics:
    """Create dynamics configuration.
    
    Args:
        points: List of [x, y] points where values can be numbers or variable references
        over: What to interpolate over: "piston_position", "time", or "weight"
        interpolation: Interpolation method: "linear" or "curve". Note: "none" is not supported.
        
    Returns:
        Dynamics object
        
    Raises:
        ValueError: If interpolation is "none" (not supported by the machine)
    """
    if interpolation == "none":
        raise ValueError(
            "Interpolation 'none' is not supported by the Meticulous machine. "
            "Use 'linear' for straight-line interpolation or 'curve' for smooth curves."
        )
    return Dynamics(points=points, over=over, interpolation=interpolation)


def create_stage(
    name: str,
    key: str,
    stage_type: str,
    dynamics: Dynamics,
    exit_triggers: List[ExitTrigger],
    limits: Optional[List[Limit]] = None,
) -> Stage:
    """Create a stage.
    
    Args:
        name: Stage name
        key: Stage key
        stage_type: Type: "power", "flow", or "pressure"
        dynamics: Dynamics configuration
        exit_triggers: List of exit triggers
        limits: Optional list of limits
        
    Returns:
        Stage object
    """
    return Stage(
        name=name,
        key=key,
        type=stage_type,
        dynamics=dynamics,
        exit_triggers=exit_triggers,
        limits=limits,
    )


def create_profile(
    name: str,
    author: str,
    author_id: Optional[str] = None,
    temperature: float = 90.0,
    final_weight: float = 40.0,
    stages: Optional[List[Stage]] = None,
    variables: Optional[List[Variable]] = None,
    display: Optional[Display] = None,
    previous_authors: Optional[List[PreviousAuthor]] = None,
    profile_id: Optional[str] = None,
    last_changed: Optional[float] = None,
) -> Profile:
    """Create a complete profile.
    
    Args:
        name: Profile name
        author: Author name
        author_id: Author ID (UUID). If not provided, generates a new UUID.
        temperature: Brew temperature in Celsius
        final_weight: Target final weight in grams
        stages: List of stages. If not provided, creates empty list.
        variables: Optional list of variables
        display: Optional display configuration
        previous_authors: Optional list of previous authors
        profile_id: Profile ID (UUID). If not provided, generates a new UUID.
        last_changed: Optional timestamp of last change
        
    Returns:
        Profile object
    """
    if profile_id is None:
        profile_id = str(uuid.uuid4())
    
    if author_id is None:
        author_id = str(uuid.uuid4())
    
    if stages is None:
        stages = []
    
    # Variables array must always be present (even if empty) for Meticulous app compatibility
    # The app crashes when trying to add variables to a profile without the variables array
    if variables is None:
        variables = []
    
    return Profile(
        name=name,
        id=profile_id,
        author=author,
        author_id=author_id,
        temperature=temperature,
        final_weight=final_weight,
        stages=stages,
        variables=variables,
        display=display,
        previous_authors=previous_authors,
        last_changed=last_changed,
    )


def profile_to_dict(profile: Profile, normalize: bool = True) -> Dict[str, Any]:
    """Convert a Profile object to a dictionary.
    
    Args:
        profile: Profile object
        normalize: If True, normalizes fields (limits, relative) for machine compatibility.
                   If False, returns raw dict without normalization (useful for linting).
        
    Returns:
        Dictionary representation of the profile
    """
    profile_dict = profile.model_dump(exclude_none=True)
    
    if normalize:
        # Ensure variables array is always present (even if empty) for Meticulous app compatibility
        # The app crashes when trying to add variables to a profile without the variables array
        if "variables" not in profile_dict or profile_dict.get("variables") is None:
            profile_dict["variables"] = []
        
        # Ensure limits is always present as an empty array if None or missing
        # The machine expects limits to always be an array, not missing/null
        if "stages" in profile_dict:
            for stage in profile_dict["stages"]:
                if "limits" not in stage or stage.get("limits") is None:
                    # Set to empty array if missing or None
                    stage["limits"] = []
                elif isinstance(stage["limits"], list) and len(stage["limits"]) == 0:
                    # Keep as empty array (don't convert to None)
                    stage["limits"] = []
                
                # Ensure exit_triggers have required fields
                if "exit_triggers" in stage:
                    for trigger in stage["exit_triggers"]:
                        # Ensure relative is always present (default to False if None/missing)
                        # The machine expects relative to always be present
                        if "relative" not in trigger or trigger.get("relative") is None:
                            # Default relative to True for time triggers (stage duration), False for others (absolute value)
                            if trigger.get("type") == "time":
                                trigger["relative"] = True
                            else:
                                trigger["relative"] = False
    
    return profile_dict


def dict_to_profile(data: Dict[str, Any]) -> Profile:
    """Create a Profile object from a dictionary.
    
    Args:
        data: Dictionary containing profile data
        
    Returns:
        Profile object
    """
    return Profile(**data)


def normalize_profile(profile: Profile) -> Profile:
    """Normalize a Profile object to ensure it's ready for saving.
    
    This function ensures that:
    - Missing or None limits in stages are converted to empty arrays []
    - Missing or None relative in exit_triggers are set to False
    - The machine expects these fields to always be present
    
    Args:
        profile: Profile object to normalize
        
    Returns:
        Normalized Profile object (may be the same object if no changes needed)
    """
    # Check if any stage needs normalization
    needs_normalization = False
    normalized_stages = []
    
    for stage in profile.stages:
        stage_normalized = False
        stage_dict = stage.model_dump(exclude_none=False)  # Don't exclude None so we can see what needs fixing
        
        # If limits is None or missing, ensure it's an empty array
        if not hasattr(stage, 'limits') or stage.limits is None:
            stage_dict['limits'] = []
            stage_normalized = True
        
        # Normalize exit_triggers - ensure relative is always present
        if 'exit_triggers' in stage_dict:
            for trigger in stage_dict['exit_triggers']:
                # Ensure relative is always present (default to False if None/missing)
                if 'relative' not in trigger or trigger.get('relative') is None:
                    # Default relative to True for time triggers (stage duration), False for others (absolute value)
                    if trigger.get('type') == 'time':
                        trigger['relative'] = True
                    else:
                        trigger['relative'] = False
                    stage_normalized = True
        
        if stage_normalized:
            needs_normalization = True
            # Create new Stage with normalized values
            normalized_stages.append(Stage(**stage_dict))
        else:
            normalized_stages.append(stage)
    
    # If normalization was needed, create a new Profile with normalized stages
    if needs_normalization:
        profile_dict = profile.model_dump()
        profile_dict['stages'] = normalized_stages
        return Profile(**profile_dict)
    
    return profile

