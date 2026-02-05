"""Profile validator using JSON schema.

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

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
from jsonschema import ValidationError


class ProfileValidationError(Exception):
    """Raised when profile validation fails."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        """Initialize validation error.
        
        Args:
            message: Error message
            errors: List of detailed validation errors
        """
        self.message = message
        self.errors = errors or []
        
        # Include all errors in the exception message so they're visible when raised
        if self.errors:
            error_lines = [message, ""]
            for i, error in enumerate(self.errors, 1):
                error_lines.append(f"{i}. {error}")
            full_message = "\n".join(error_lines)
        else:
            full_message = message
        
        super().__init__(full_message)


class ProfileValidator:
    """Validates espresso profiles against JSON schema."""

    def __init__(self, schema_path: Optional[str] = None):
        """Initialize the validator.
        
        Args:
            schema_path: Path to schema.json file. If not provided, attempts to find
                        it relative to this file or in espresso-profile-schema repo.
        """
        possible_paths = []
        if schema_path is None:
            # Try to find schema relative to this file
            current_dir = Path(__file__).parent.parent.parent
            possible_paths = [
                current_dir / "espresso-profile-schema" / "schema.json",
                Path(__file__).parent / "schema.json",
            ]
            for path in possible_paths:
                if path.exists():
                    schema_path = str(path)
                    break
        
        if schema_path is None or not os.path.exists(schema_path):
            paths_str = ", ".join(str(p) for p in possible_paths) if possible_paths else "none"
            raise FileNotFoundError(
                f"Schema file not found. Path given: {schema_path}. Tried: {paths_str}. "
                "Please provide schema_path or ensure espresso-profile-schema is available."
            )

        with open(schema_path, "r", encoding="utf-8") as f:
            self._schema = json.load(f)
        
        # Create validator instance
        self._validator = jsonschema.Draft7Validator(self._schema)

    def validate(self, profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a profile against the schema.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        try:
            self._validator.validate(profile)
        except ValidationError as e:
            errors.append(self._format_error(e))
            
            # Collect all validation errors
            for error in self._validator.iter_errors(profile):
                if error != e:  # Don't duplicate the first error
                    errors.append(self._format_error(error))
        
        # Add custom validation for pressure limits (15 bar max)
        pressure_errors = self._validate_pressure_limits(profile)
        errors.extend(pressure_errors)
        
        # Add custom validation for interpolation values
        interpolation_errors = self._validate_interpolation(profile)
        errors.extend(interpolation_errors)
        
        # Add custom validation for dynamics.over values
        dynamics_over_errors = self._validate_dynamics_over(profile)
        errors.extend(dynamics_over_errors)
        
        # Add custom validation for stage types
        stage_type_errors = self._validate_stage_types(profile)
        errors.extend(stage_type_errors)
        
        # Add custom validation for exit triggers
        exit_trigger_errors = self._validate_exit_triggers(profile)
        errors.extend(exit_trigger_errors)
        
        # Add custom validation for limits
        limit_errors = self._validate_limits(profile)
        errors.extend(limit_errors)
        
        # Add validation for exit trigger type matching stage type (paradox check)
        exit_stage_match_errors = self._validate_exit_trigger_matches_stage_type(profile)
        errors.extend(exit_stage_match_errors)
        
        # Add validation for backup exit triggers (failsafe check)
        backup_trigger_errors = self._validate_backup_exit_triggers(profile)
        errors.extend(backup_trigger_errors)
        
        # Add validation for required safety limits
        required_limit_errors = self._validate_required_limits(profile)
        errors.extend(required_limit_errors)
        
        # Add validation for absolute weight trigger consistency across stages
        weight_trigger_errors = self._validate_absolute_weight_triggers(profile)
        errors.extend(weight_trigger_errors)
        
        # Add validation for variable naming and usage
        variable_errors = self._validate_variables(profile)
        errors.extend(variable_errors)
        
        return len(errors) == 0, errors

    def validate_and_raise(self, profile: Dict[str, Any]) -> None:
        """Validate a profile and raise ProfileValidationError if invalid.
        
        Args:
            profile: Profile dictionary to validate
            
        Raises:
            ProfileValidationError: If validation fails (includes all errors in message)
        """
        is_valid, errors = self.validate(profile)
        if not is_valid:
            message = f"Profile validation failed with {len(errors)} error(s)"
            # The ProfileValidationError will automatically include all errors in its message
            raise ProfileValidationError(message, errors)

    def _validate_pressure_limits(self, profile: Dict[str, Any]) -> List[str]:
        """Validate pressure limits (15 bar max) in profile.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of pressure-related validation errors
        """
        errors = []
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            
            # Check pressure in dynamics points (only for pressure-type stages)
            if stage.get("type") == "pressure":
                dynamics = stage.get("dynamics", {})
                points = dynamics.get("points", [])
                for point_idx, point in enumerate(points):
                    if isinstance(point, list) and len(point) >= 2:
                        pressure_val = point[1]
                        if isinstance(pressure_val, (int, float)):
                            if pressure_val > 15:
                                errors.append(f"Stage '{stage_name}' dynamics point {point_idx+1} has pressure {pressure_val} bar which exceeds the 15 bar limit. Please reduce pressure to 15 bar or below.")
                            elif pressure_val < 0:
                                errors.append(f"Stage '{stage_name}' dynamics point {point_idx+1} has negative pressure {pressure_val} bar. Pressure must be non-negative.")
            
            # Check pressure in exit triggers
            exit_triggers = stage.get("exit_triggers", [])
            for trigger_idx, trigger in enumerate(exit_triggers):
                if isinstance(trigger, dict) and trigger.get("type") == "pressure":
                    pressure_val = trigger.get("value")
                    if isinstance(pressure_val, (int, float)):
                        if pressure_val > 15:
                            errors.append(f"Stage '{stage_name}' exit trigger {trigger_idx+1} has pressure {pressure_val} bar which exceeds the 15 bar limit. Please reduce pressure to 15 bar or below.")
                        elif pressure_val < 0:
                            errors.append(f"Stage '{stage_name}' exit trigger {trigger_idx+1} has negative pressure {pressure_val} bar. Pressure must be non-negative.")
        
        return errors

    def _validate_interpolation(self, profile: Dict[str, Any]) -> List[str]:
        """Validate interpolation values in profile dynamics.
        
        The Meticulous machine only supports 'linear' and 'curve' interpolation.
        The value 'none' is not supported and will cause the machine to stall.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of interpolation-related validation errors
        """
        errors = []
        valid_interpolations = {"linear", "curve"}
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            dynamics = stage.get("dynamics", {})
            
            if isinstance(dynamics, dict):
                interpolation = dynamics.get("interpolation")
                if interpolation is not None and interpolation not in valid_interpolations:
                    errors.append(
                        f"Stage '{stage_name}' has invalid interpolation value '{interpolation}'. "
                        f"Only 'linear' and 'curve' are supported. "
                        f"The value 'none' is not supported by the Meticulous machine and will cause it to stall."
                    )
                
                # Check that 'curve' interpolation has at least 2 points
                points = dynamics.get("points", [])
                if interpolation == "curve" and len(points) < 2:
                    errors.append(
                        f"Stage '{stage_name}' uses 'curve' interpolation but has only {len(points)} point(s). "
                        f"Curve interpolation requires at least 2 points. Use 'linear' for single-point dynamics."
                    )
        
        return errors

    def _validate_dynamics_over(self, profile: Dict[str, Any]) -> List[str]:
        """Validate dynamics.over values in profile.
        
        The 'over' field must be one of: 'time', 'weight', 'piston_position'.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of dynamics.over validation errors
        """
        errors = []
        valid_over_values = {"time", "weight", "piston_position"}
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            dynamics = stage.get("dynamics", {})
            
            if isinstance(dynamics, dict):
                over = dynamics.get("over")
                if over is not None and over not in valid_over_values:
                    errors.append(
                        f"Stage '{stage_name}' has invalid dynamics.over value '{over}'. "
                        f"Must be one of: 'time', 'weight', 'piston_position'."
                    )
        
        return errors

    def _validate_stage_types(self, profile: Dict[str, Any]) -> List[str]:
        """Validate stage type values in profile.
        
        Stage type must be one of: 'power', 'flow', 'pressure'.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of stage type validation errors
        """
        errors = []
        valid_stage_types = {"power", "flow", "pressure"}
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            stage_type = stage.get("type")
            
            if stage_type is not None and stage_type not in valid_stage_types:
                errors.append(
                    f"Stage '{stage_name}' has invalid type '{stage_type}'. "
                    f"Must be one of: 'power', 'flow', 'pressure'."
                )
        
        return errors

    def _validate_exit_triggers(self, profile: Dict[str, Any]) -> List[str]:
        """Validate exit trigger values in profile.
        
        Exit trigger type must be one of: 'weight', 'pressure', 'flow', 'time', 
        'piston_position', 'power', 'user_interaction'.
        Comparison must be one of: '>=', '<='.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of exit trigger validation errors
        """
        errors = []
        valid_trigger_types = {"weight", "pressure", "flow", "time", "piston_position", "power", "user_interaction"}
        valid_comparisons = {">=", "<="}
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            exit_triggers = stage.get("exit_triggers", [])
            
            for trigger_idx, trigger in enumerate(exit_triggers):
                if not isinstance(trigger, dict):
                    continue
                
                trigger_type = trigger.get("type")
                if trigger_type is not None and trigger_type not in valid_trigger_types:
                    errors.append(
                        f"Stage '{stage_name}' exit trigger {trigger_idx+1} has invalid type '{trigger_type}'. "
                        f"Must be one of: {', '.join(sorted(valid_trigger_types))}."
                    )
                
                comparison = trigger.get("comparison")
                if comparison is not None and comparison not in valid_comparisons:
                    errors.append(
                        f"Stage '{stage_name}' exit trigger {trigger_idx+1} has invalid comparison '{comparison}'. "
                        f"Must be one of: '>=', '<='."
                    )
        
        return errors

    def _validate_limits(self, profile: Dict[str, Any]) -> List[str]:
        """Validate limit values in profile.
        
        Limit type must be one of: 'pressure', 'flow'.
        Additionally, a limit cannot have the same type as the stage control type,
        as this is redundant and the Meticulous app will reject it.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of limit validation errors
        """
        errors = []
        valid_limit_types = {"pressure", "flow"}
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            stage_type = stage.get("type")
            limits = stage.get("limits", [])
            
            if not isinstance(limits, list):
                continue
            
            for limit_idx, limit in enumerate(limits):
                if not isinstance(limit, dict):
                    continue
                
                limit_type = limit.get("type")
                if limit_type is not None and limit_type not in valid_limit_types:
                    errors.append(
                        f"Stage '{stage_name}' limit {limit_idx+1} has invalid type '{limit_type}'. "
                        f"Must be one of: 'pressure', 'flow'."
                    )
                
                # Check for redundant limit (same type as stage control)
                if limit_type is not None and stage_type is not None and limit_type == stage_type:
                    errors.append(
                        f"Stage '{stage_name}' has a '{limit_type}' limit but is a '{stage_type}' control stage. "
                        f"This is redundant - you cannot limit {limit_type} when you're already controlling {stage_type}. "
                        f"Use a '{('pressure' if limit_type == 'flow' else 'flow')}' limit instead, or remove the limit."
                    )
        
        return errors

    def _validate_exit_trigger_matches_stage_type(self, profile: Dict[str, Any]) -> List[str]:
        """Validate that exit trigger types don't match the stage control type.
        
        If a stage controls flow, it should not have a flow exit trigger as the primary trigger.
        If a stage controls pressure, it should not have a pressure exit trigger.
        This creates a paradox where grind variations mean the trigger may never fire.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            stage_type = stage.get("type")
            exit_triggers = stage.get("exit_triggers", [])
            
            if not stage_type or not exit_triggers:
                continue
            
            # Check if any exit trigger has the same type as the stage control
            for trigger_idx, trigger in enumerate(exit_triggers):
                if not isinstance(trigger, dict):
                    continue
                
                trigger_type = trigger.get("type")
                
                # Check for matching types (flow stage with flow trigger, pressure stage with pressure trigger)
                if trigger_type == stage_type and stage_type in ("flow", "pressure"):
                    errors.append(
                        f"Stage '{stage_name}' is a '{stage_type}' control stage but has a '{trigger_type}' exit trigger. "
                        f"This is problematic - if you're controlling {stage_type}, you can't reliably exit based on {trigger_type} "
                        f"since it's what you're already controlling. Use a different trigger type like 'time', 'weight', or "
                        f"'{('pressure' if stage_type == 'flow' else 'flow')}'."
                    )
        
        return errors

    def _validate_backup_exit_triggers(self, profile: Dict[str, Any]) -> List[str]:
        """Validate that every stage has a backup/failsafe exit trigger.
        
        Every stage should have either:
        - Multiple exit triggers (OR logic provides failsafe)
        - At least one time-based trigger (universal failsafe)
        
        This prevents shots from stalling indefinitely if grind is wrong.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            exit_triggers = stage.get("exit_triggers", [])
            
            if not exit_triggers:
                # Already caught by other validation
                continue
            
            # Count valid triggers and check for time trigger
            valid_triggers = [t for t in exit_triggers if isinstance(t, dict) and t.get("type")]
            has_time_trigger = any(t.get("type") == "time" for t in valid_triggers)
            
            # Must have either multiple triggers OR a time trigger
            if len(valid_triggers) == 1 and not has_time_trigger:
                trigger_type = valid_triggers[0].get("type", "unknown")
                errors.append(
                    f"Stage '{stage_name}' has only one exit trigger ('{trigger_type}') with no time-based failsafe. "
                    f"Every stage must have a backup exit condition to prevent indefinite stalls. "
                    f"Add a time-based trigger (e.g., 'time >= 45s') as a failsafe, or add a second trigger like 'weight'."
                )
        
        return errors

    def _validate_required_limits(self, profile: Dict[str, Any]) -> List[str]:
        """Validate that every stage has required safety limits.
        
        Flow stages must have a pressure limit to prevent machine stall at high pressure.
        Pressure stages must have a flow limit to prevent gusher shots.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        for i, stage in enumerate(profile["stages"]):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            stage_type = stage.get("type")
            limits = stage.get("limits", [])
            
            if not stage_type:
                continue
            
            # Get limit types present
            limit_types = set()
            if isinstance(limits, list):
                for limit in limits:
                    if isinstance(limit, dict) and limit.get("type"):
                        limit_types.add(limit.get("type"))
            
            # Determine if this is a pre-infusion stage (for different pressure limit recommendations)
            stage_name_lower = stage_name.lower()
            is_preinfusion = any(term in stage_name_lower for term in 
                                 ["pre-infusion", "preinfusion", "fill", "bloom", "soak", "pre infusion"])
            
            # Flow stages need pressure limits
            if stage_type == "flow" and "pressure" not in limit_types:
                recommended_limit = "3 bar" if is_preinfusion else "10 bar"
                errors.append(
                    f"Stage '{stage_name}' is a 'flow' control stage but has no pressure limit. "
                    f"This is dangerous - if the grind is too fine, pressure could spike to 12+ bar and stall. "
                    f"Add a pressure limit (recommended: {recommended_limit} for {'pre-infusion' if is_preinfusion else 'extraction'} stages)."
                )
            
            # Pressure stages need flow limits
            if stage_type == "pressure" and "flow" not in limit_types:
                errors.append(
                    f"Stage '{stage_name}' is a 'pressure' control stage but has no flow limit. "
                    f"This can cause gusher shots if the grind is too coarse. "
                    f"Add a flow limit (recommended: 5 ml/s)."
                )
        
        return errors

    def _validate_absolute_weight_triggers(self, profile: Dict[str, Any]) -> List[str]:
        """Validate that absolute weight triggers are strictly increasing across stages.
        
        If Stage N exits at absolute weight X, and Stage N+1 has absolute weight trigger Y,
        then Y must be > X, otherwise the trigger will fire immediately.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if "stages" not in profile or not isinstance(profile["stages"], list):
            return errors
        
        stages = profile["stages"]
        
        # Track the maximum absolute weight trigger seen so far
        max_absolute_weight = 0.0
        max_weight_stage_name = None
        
        for i, stage in enumerate(stages):
            if not isinstance(stage, dict):
                continue
            
            stage_name = stage.get("name", f"Stage {i+1}")
            exit_triggers = stage.get("exit_triggers", [])
            
            # Find absolute weight triggers in this stage
            for trigger in exit_triggers:
                if not isinstance(trigger, dict):
                    continue
                
                trigger_type = trigger.get("type")
                trigger_value = trigger.get("value")
                is_relative = trigger.get("relative", False)
                
                if trigger_type == "weight" and not is_relative and isinstance(trigger_value, (int, float)):
                    # This is an absolute weight trigger
                    if trigger_value <= max_absolute_weight and max_weight_stage_name is not None:
                        errors.append(
                            f"Stage '{stage_name}' has absolute weight trigger ({trigger_value}g) that is <= "
                            f"the previous stage '{max_weight_stage_name}' weight trigger ({max_absolute_weight}g). "
                            f"This trigger will fire immediately since the scale already shows >= {max_absolute_weight}g. "
                            f"Use 'relative: true' for stage-specific weight tracking, or increase the weight threshold."
                        )
                    
                    # Update max for next stages
                    if trigger_value > max_absolute_weight:
                        max_absolute_weight = trigger_value
                        max_weight_stage_name = stage_name
        
        return errors

    def _validate_variables(self, profile: Dict[str, Any]) -> List[str]:
        """Validate variable definitions and usage in profile.
        
        Rules:
        1. Info variables (displayed but not adjustable) MUST have emoji prefix in name
        2. Adjustable variables (user can change) must NOT have emoji prefix
        3. Variables should be used in at least one stage dynamics
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            List of variable validation errors
        """
        errors = []
        
        variables = profile.get("variables", [])
        if not variables:
            return errors
        
        # Regex to detect emoji at start of string
        import re
        emoji_pattern = re.compile(
            r'^['
            r'\U0001F300-\U0001F9FF'  # Miscellaneous Symbols and Pictographs, Emoticons, etc.
            r'\U00002600-\U000027BF'  # Misc symbols, Dingbats
            r'\U00002100-\U0000214F'  # Letterlike Symbols (includes ℹ️ U+2139)
            r'\U0001F000-\U0001F02F'  # Mahjong tiles
            r'\U0001FA00-\U0001FAFF'  # Extended-A symbols
            r'\uFE00-\uFE0F'          # Variation Selectors (emoji presentation)
            r']'
        )
        
        # Collect all variable keys for usage tracking
        var_keys = {}
        for var in variables:
            if not isinstance(var, dict):
                continue
            key = var.get("key")
            name = var.get("name", "")
            is_info = not var.get("adjustable", True)  # Default to adjustable if not specified
            
            if key:
                var_keys[key] = {"name": name, "is_info": is_info, "used": False}
                
                has_emoji = bool(emoji_pattern.match(name))
                
                # Rule 1: Info variables must have emoji prefix
                if is_info and not has_emoji:
                    errors.append(
                        f"Info variable '{key}' ({name}) must have an emoji prefix in its name. "
                        f"Info variables are displayed to help the user understand the profile but "
                        f"cannot be adjusted. Add an emoji like ℹ️, 📊, or 💡 at the start."
                    )
                
                # Rule 2: Adjustable variables must NOT have emoji prefix  
                if not is_info and has_emoji:
                    errors.append(
                        f"Adjustable variable '{key}' ({name}) should not have an emoji prefix. "
                        f"Emoji prefixes are reserved for info (non-adjustable) variables to "
                        f"visually distinguish them in the UI."
                    )
        
        # Track variable usage in stage dynamics
        if "stages" in profile:
            for stage in profile["stages"]:
                if not isinstance(stage, dict):
                    continue
                dynamics = stage.get("dynamics", {})
                points = dynamics.get("points", [])
                for point in points:
                    if isinstance(point, list):
                        for val in point:
                            if isinstance(val, str) and val.startswith("$"):
                                var_key = val[1:]  # Remove $
                                if var_key in var_keys:
                                    var_keys[var_key]["used"] = True
        
        # Rule 3: Check for unused adjustable variables (error, not warning)
        for key, info in var_keys.items():
            if not info["used"] and not info["is_info"]:
                errors.append(
                    f"Adjustable variable '{key}' ({info['name']}) is defined but never used in any "
                    f"stage dynamics. Either use it with ${key} in a dynamics point, mark it as "
                    f"info-only (adjustable: false), or remove it."
                )
        
        return errors

    def _format_error(self, error: ValidationError) -> str:
        """Format a validation error into a readable message.
        
        Args:
            error: The ValidationError instance
            
        Returns:
            Formatted error message with helpful context
        """
        path = " -> ".join(str(p) for p in error.path)
        message = error.message
        
        # Add helpful context for common errors
        if "required" in message.lower() or "missing" in message.lower():
            if "stages" in path.lower():
                message += " (each stage must have: name, key, type, dynamics, exit_triggers)"
            elif "dynamics" in path.lower():
                message += " (dynamics must have: points, over, interpolation)"
            elif "exit_triggers" in path.lower():
                message += " (each exit trigger must have: type, value)"
        
        if "Field required" in message:
            # Extract field name from path
            field_name = path.split(" -> ")[-1] if path else "unknown"
            message = f"Missing required field '{field_name}'"
        
        if path:
            return f"Field '{path}': {message}"
        return f"Root level: {message}"

    def lint(self, profile: Dict[str, Any]) -> List[str]:
        """Lint a profile and return warnings/suggestions.
        
        Args:
            profile: Profile dictionary to lint
            
        Returns:
            List of linting warnings/suggestions
        """
        warnings = []
        
        # Check for common issues
        if "stages" in profile:
            stages = profile["stages"]
            if not isinstance(stages, list):
                warnings.append("'stages' should be a list")
            elif len(stages) == 0:
                warnings.append("Profile has no stages")
            else:
                # Check stage ordering and naming
                for i, stage in enumerate(stages):
                    if not isinstance(stage, dict):
                        continue
                    
                    stage_name = stage.get("name", f"Stage {i+1}")
                    stage_key = stage.get("key", f"stage_{i+1}")
                    
                    # Check exit triggers
                    exit_triggers = stage.get("exit_triggers", [])
                    if not exit_triggers:
                        warnings.append(f"Stage '{stage_name}' has no exit triggers - stages should have at least one exit trigger")
                    else:
                        # Check exit trigger types
                        has_weight_trigger = any(et.get("type") == "weight" for et in exit_triggers if isinstance(et, dict))
                        has_time_trigger = any(et.get("type") == "time" for et in exit_triggers if isinstance(et, dict))
                        if not has_weight_trigger and not has_time_trigger:
                            warnings.append(f"Stage '{stage_name}' has exit triggers but none are weight or time-based - consider adding a weight/time trigger")
                        
                        # Check for missing 'relative' field in exit triggers
                        # The machine requires 'relative' to always be present (defaults to false)
                        for idx, trigger in enumerate(exit_triggers):
                            if isinstance(trigger, dict):
                                if "relative" not in trigger or trigger.get("relative") is None:
                                    warnings.append(f"Stage '{stage_name}' exit trigger {idx+1} ({trigger.get('type', 'unknown')}) is missing 'relative' field - will be normalized to false. The machine requires 'relative' to always be present in exit triggers.")
                    
                    # Check dynamics
                    dynamics = stage.get("dynamics")
                    if dynamics:
                        points = dynamics.get("points", [])
                        if not points:
                            warnings.append(f"Stage '{stage_name}' has empty dynamics points - dynamics should define pressure/flow changes")
                        elif len(points) == 1:
                            warnings.append(f"Stage '{stage_name}' has only one dynamics point - consider adding more points for smoother transitions")
                        
                        over = dynamics.get("over", "")
                        if over not in ["time", "weight", "piston_position"]:
                            warnings.append(f"Stage '{stage_name}' has invalid dynamics.over value '{over}' - should be 'time', 'weight', or 'piston_position'")
                        
                        # Check interpolation value
                        interpolation = dynamics.get("interpolation", "")
                        if interpolation not in ["linear", "curve"]:
                            warnings.append(f"Stage '{stage_name}' has invalid interpolation '{interpolation}' - should be 'linear' or 'curve'. The value 'none' is not supported.")
                    
                    # Check stage type
                    stage_type = stage.get("type", "")
                    if stage_type not in ["power", "flow", "pressure"]:
                        warnings.append(f"Stage '{stage_name}' has invalid type '{stage_type}' - should be 'power', 'flow', or 'pressure'")
                    
                    # Check for missing or None 'limits' field
                    # The machine requires 'limits' to always be present as an array (even if empty)
                    if "limits" not in stage:
                        warnings.append(f"Stage '{stage_name}' is missing 'limits' field - will be normalized to empty array []. The machine requires 'limits' to always be present as an array in stages.")
                    elif stage.get("limits") is None:
                        warnings.append(f"Stage '{stage_name}' has 'limits' set to null - will be normalized to empty array []. The machine requires 'limits' to always be an array, not null.")
                    
                    # Check for duplicate keys
                    if i > 0:
                        prev_keys = [s.get("key") for s in stages[:i] if isinstance(s, dict)]
                        if stage_key in prev_keys:
                            warnings.append(f"Stage '{stage_name}' has duplicate key '{stage_key}' - stage keys should be unique")
                    
                    # Check limit values for sensible bounds
                    limits = stage.get("limits", [])
                    if isinstance(limits, list):
                        for limit in limits:
                            if not isinstance(limit, dict):
                                continue
                            limit_type = limit.get("type")
                            limit_value = limit.get("value")
                            if isinstance(limit_value, (int, float)):
                                if limit_type == "pressure":
                                    if limit_value < 0:
                                        warnings.append(f"Stage '{stage_name}' has negative pressure limit ({limit_value} bar) - should be >= 0")
                                    elif limit_value > 12:
                                        warnings.append(f"Stage '{stage_name}' has very high pressure limit ({limit_value} bar) - consider lowering to 10-12 bar for safety")
                                elif limit_type == "flow":
                                    if limit_value < 0:
                                        warnings.append(f"Stage '{stage_name}' has negative flow limit ({limit_value} ml/s) - should be >= 0")
                                    elif limit_value > 8:
                                        warnings.append(f"Stage '{stage_name}' has very high flow limit ({limit_value} ml/s) - consider lowering to 5-6 ml/s for better control")
                    
                    # Pre-infusion specific recommendations
                    stage_name_lower = stage_name.lower()
                    is_preinfusion = any(term in stage_name_lower for term in 
                                         ["pre-infusion", "preinfusion", "fill", "bloom", "soak", "pre infusion"])
                    if is_preinfusion:
                        # Check for high pressure limits on pre-infusion stages
                        if isinstance(limits, list):
                            for limit in limits:
                                if isinstance(limit, dict) and limit.get("type") == "pressure":
                                    limit_value = limit.get("value")
                                    if isinstance(limit_value, (int, float)) and limit_value > 4:
                                        warnings.append(f"Stage '{stage_name}' is a pre-infusion stage with pressure limit of {limit_value} bar - consider lowering to 3-4 bar for gentler saturation")
                        
                        # Check for weight-based early exit (adaptive pre-infusion)
                        has_weight_trigger = any(et.get("type") == "weight" for et in exit_triggers if isinstance(et, dict))
                        if not has_weight_trigger:
                            warnings.append(f"Stage '{stage_name}' is a pre-infusion stage without a weight-based exit trigger. Consider adding 'weight >= 3-5g' to detect early dripping and adapt to grind variations.")
                    
                    # Check for bloom/soak/hold stages that should use relative triggers
                    is_bloom_stage = any(term in stage_name_lower for term in 
                                         ["bloom", "soak", "hold", "rest", "pause", "wait"])
                    if is_bloom_stage and i > 0:  # Only warn for non-first stages
                        # Check if any exit triggers are absolute (relative=false)
                        has_absolute_trigger = False
                        for trigger in exit_triggers:
                            if isinstance(trigger, dict):
                                if not trigger.get("relative", False):
                                    has_absolute_trigger = True
                                    break
                        if has_absolute_trigger:
                            warnings.append(
                                f"Stage '{stage_name}' appears to be a bloom/rest stage but uses absolute exit triggers. "
                                f"Consider using 'relative: true' for exit triggers so the stage duration is independent of previous stages."
                            )
                    
                    # Check for low absolute weight triggers in non-first stages
                    if i > 0:  # Not the first stage
                        for trigger in exit_triggers:
                            if isinstance(trigger, dict):
                                trigger_type = trigger.get("type")
                                trigger_value = trigger.get("value")
                                is_relative = trigger.get("relative", False)
                                if trigger_type == "weight" and not is_relative and isinstance(trigger_value, (int, float)):
                                    if trigger_value < 10:
                                        warnings.append(
                                            f"Stage '{stage_name}' (stage {i+1}) has a low absolute weight trigger ({trigger_value}g). "
                                            f"If preceding stages have weight-based exits, this may fire immediately. "
                                            f"Consider using 'relative: true' for stage-specific weight tracking."
                                        )
        
        # Check temperature range
        if "temperature" in profile:
            temp = profile["temperature"]
            if isinstance(temp, (int, float)):
                if temp < 80 or temp > 100:
                    warnings.append(f"Temperature {temp}°C is outside typical range (80-100°C) - consider adjusting for your roast level")
                elif temp < 85:
                    warnings.append(f"Temperature {temp}°C is on the lower end - suitable for dark roasts")
                elif temp > 95:
                    warnings.append(f"Temperature {temp}°C is on the higher end - suitable for light roasts")

        # Check final_weight
        if "final_weight" in profile:
            weight = profile["final_weight"]
            if isinstance(weight, (int, float)):
                if weight < 10 or weight > 100:
                    warnings.append(f"Final weight {weight}g is outside typical range (10-100g) - verify this is intentional")
                elif weight < 20:
                    warnings.append(f"Final weight {weight}g is quite low - typical espresso shots are 25-45g")
                elif weight > 60:
                    warnings.append(f"Final weight {weight}g is quite high - this approaches lungo/ristretto territory")
        
        # Check variables - the variables array should always exist for app compatibility
        # Handle three cases: missing key, empty array, or populated array
        if "variables" not in profile:
            # Case 1: Key missing entirely - most critical, affects app compatibility
            warnings.append(
                "Profile is missing 'variables' array - this field must be present (even if empty) "
                "for Meticulous app compatibility. The app may crash when trying to add variables."
            )
        else:
            variables = profile.get("variables", [])
            if not variables:
                # Case 2: Empty array - valid but could be more useful
                warnings.append(
                    "Profile has no variables defined - consider adding variables (e.g., target pressure, "
                    "bloom flow rate) for easier adjustments during brewing. Variables allow you to tweak "
                    "profile parameters without editing individual stage dynamics."
                )
            else:
                # Case 3: Has variables - check for undefined references and unused variables
                var_keys = [v.get("key") for v in variables if isinstance(v, dict)]
                
                # Check for undefined variable references in stages
                if "stages" in profile:
                    stages = profile["stages"]
                    variables_used = set()
                    for stage in stages:
                        if not isinstance(stage, dict):
                            continue
                        # Check dynamics points for variable references
                        dynamics = stage.get("dynamics", {})
                        points = dynamics.get("points", [])
                        for point in points:
                            if isinstance(point, list) and len(point) >= 2:
                                for val in point:
                                    if isinstance(val, str) and val.startswith("$"):
                                        var_key = val[1:]  # Remove $
                                        variables_used.add(var_key)
                                        if var_key not in var_keys:
                                            warnings.append(f"Stage '{stage.get('name', 'unknown')}' references variable '${var_key}' but it's not defined in variables")
                    
                    # Check for unused variables
                    unused_vars = set(var_keys) - variables_used
                    for unused in unused_vars:
                        warnings.append(f"Variable '{unused}' is defined but never used in any stage dynamics")

        return warnings

