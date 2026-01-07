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
        
        # Check variables
        if "variables" in profile:
            variables = profile["variables"]
            if variables:
                var_keys = [v.get("key") for v in variables if isinstance(v, dict)]
                # Check for variables referenced in stages but not defined
                if "stages" in profile:
                    stages = profile["stages"]
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
                                        if var_key not in var_keys:
                                            warnings.append(f"Stage '{stage.get('name', 'unknown')}' references variable '${var_key}' but it's not defined in variables")

        return warnings

