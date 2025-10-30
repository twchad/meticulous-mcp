"""Main MCP server entry point.

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
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from meticulous.profile import Profile

from .api_client import MeticulousAPIClient
from .profile_builder import profile_to_dict, dict_to_profile
from .profile_validator import ProfileValidator
from .tools import (
    initialize_tools,
    create_profile_tool,
    list_profiles_tool,
    get_profile_tool,
    update_profile_tool,
    duplicate_profile_tool,
    delete_profile_tool,
    validate_profile_tool,
    run_profile_tool,
    ProfileCreateInput,
    ProfileUpdateInput,
)

# Initialize FastMCP server
mcp = FastMCP("Meticulous Espresso Profile Server")

# Global instances
_api_client: Optional[MeticulousAPIClient] = None
_validator: Optional[ProfileValidator] = None


def _ensure_initialized() -> None:
    """Ensure server is initialized."""
    global _api_client, _validator
    if _api_client is None or _validator is None:
        # Initialize on first use
        base_url = os.getenv("METICULOUS_API_URL", "http://meticulousmodelalmondmilklatte.local")
        _api_client = MeticulousAPIClient(base_url=base_url)
        
        # Find schema file
        current_dir = Path(__file__).parent.parent.parent
        schema_path = current_dir / "espresso-profile-schema" / "schema.json"
        if not schema_path.exists():
            # Try alternative location
            schema_path = Path(__file__).parent.parent.parent.parent / "espresso-profile-schema" / "schema.json"
        
        _validator = ProfileValidator(schema_path=str(schema_path))
        initialize_tools(_api_client, _validator)


# Register tools
@mcp.tool()
def create_profile(input_data: ProfileCreateInput) -> Dict[str, Any]:
    """Create a new espresso profile with structured parameters."""
    _ensure_initialized()
    return create_profile_tool(input_data)


@mcp.tool()
def list_profiles() -> List[Dict[str, Any]]:
    """List all available profiles."""
    _ensure_initialized()
    return list_profiles_tool()


@mcp.tool()
def get_profile(profile_id: str) -> Dict[str, Any]:
    """Get full profile details by ID."""
    _ensure_initialized()
    return get_profile_tool(profile_id)


@mcp.tool()
def update_profile(input_data: ProfileUpdateInput) -> Dict[str, Any]:
    """Update an existing profile."""
    _ensure_initialized()
    return update_profile_tool(input_data)


@mcp.tool()
def duplicate_profile(
    profile_id: str, new_name: str, modify_temperature: Optional[float] = None
) -> Dict[str, Any]:
    """Duplicate a profile and optionally modify it."""
    _ensure_initialized()
    return duplicate_profile_tool(profile_id, new_name, modify_temperature)


@mcp.tool()
def delete_profile(profile_id: str) -> Dict[str, Any]:
    """Delete a profile permanently. 
    
    ⚠️ WARNING: This is a destructive operation that cannot be undone.
    
    IMPORTANT: Before calling this tool, you MUST:
    1. First retrieve the profile using get_profile to see its details
    2. Confirm with the user that they want to delete this specific profile
    3. Only proceed if the user explicitly confirms the deletion
    
    Do NOT delete profiles without explicit user confirmation.
    """
    _ensure_initialized()
    return delete_profile_tool(profile_id)


@mcp.tool()
def validate_profile(profile_json: str) -> Dict[str, Any]:
    """Validate a profile JSON against the schema."""
    _ensure_initialized()
    return validate_profile_tool(profile_json)


@mcp.tool()
def run_profile(profile_id: str) -> Dict[str, Any]:
    """Load and execute a profile (without saving)."""
    _ensure_initialized()
    return run_profile_tool(profile_id)


# Register resources
@mcp.resource("espresso://knowledge")
def espresso_knowledge() -> str:
    """Get comprehensive espresso profiling knowledge for the Meticulous machine."""
    return """# Advanced Espresso Profiling Guide for the Meticulous Machine

This reference is designed for creating and executing precise espresso profiles using the Meticulous Home Espresso machine, a digitally controlled robotic lever system that offers unparalleled control over flow, pressure, and temperature.

## 1. Core Concepts: A Deeper Dive

To build precise profiles, a granular understanding of the key variables and their interplay is essential. The Meticulous machine controls these variables directly, rather than through manual approximation.

### Variable Control

**Flow Rate (ml/s)** - The Primary Driver of Extraction
- Controls the speed of water delivery to the puck
- Higher flow rate increases extraction speed and highlights acidity and clarity
- Lower flow rate allows longer contact time, building body and sweetness
- Meticulous Control: Digital motor controls lever descent, allowing direct flow rate programming

**Pressure (bar)** - The Result of Flow vs. Resistance
- Pressure builds as water flow meets puck resistance
- Crucial for creating texture, mouthfeel, and crema
- High pressure increases body but risks channeling if not managed
- Meticulous Control: Can target specific pressure with sensors measuring force and motor adjusting lever

**Temperature (°C)** - The Catalyst for Solubility
- Dictates which flavor compounds dissolve from coffee grounds
- Lighter roasts: Higher temperatures (92-96°C) needed for sweetness
- Darker roasts: Lower temperatures (84-92°C) reduce bitterness
- Meticulous Control: High-precision PID temperature control for boiler and heated grouphead

### Understanding Puck Dynamics

The coffee puck evolves throughout extraction:

1. **Initial Saturation**: Dry grounds swell and release CO2. Uneven wetting causes channeling.
2. **Peak Resistance**: Early in shot, puck offers maximum resistance.
3. **Puck Erosion**: As compounds dissolve, puck integrity weakens, resistance decreases.
4. **Fines Migration**: Microscopic particles can clog filter, temporarily increasing resistance.

A flat, static profile fails to account for this evolution. Dynamic profiles adapt to the puck's changing state.

## 2. A Phased Approach to Profile Building

Break down every shot into four distinct, controllable phases:

### Phase 1: Pre-infusion
- **Goal**: Gently and evenly saturate entire puck to prevent channeling
- **Control**: Flow Rate
- **Target Flow**: 2-4 ml/s
- **Target Pressure Limit**: ~2 bar
- **Duration**: Until first drops appear, or specific volume (5-8 ml) delivered

### Phase 2: Bloom (Dwell) - Optional
- **Goal**: Allow saturated puck to rest, releasing CO2, enabling deeper penetration
- **Control**: Time (zero flow)
- **Holding Pressure**: 0.5-1.5 bar (prevents puck unseating)
- **Duration**: 5-30 seconds (fresher coffee = longer bloom)

### Phase 3: Infusion (Ramp & Hold)
- **Goal**: Extract core body, sweetness, and desired acidity
- **Control**: Pressure or Flow Rate
- **Pressure Target**: Ramp to 6-9 bar, hold until desired extraction ratio
- **Flow Target**: 1.5-3 ml/s, let pressure be variable
- **Most critical phase for flavor development**

### Phase 4: Tapering (Ramp Down)
- **Goal**: Gently finish extraction, minimizing bitterness and astringency
- **Control**: Pressure or Flow Rate
- **Action**: Gradually decrease pressure (e.g., 9 bar to 4 bar) or reduce flow (e.g., 2 ml/s to 1 ml/s)
- **Duration**: Final 1/3 of shot's volume

## 3. Espresso Profile Blueprints

### Blueprint 1: The "Classic Lever"
**Best for**: Medium to Medium-Dark Roasts
**Goal**: Balanced, full-bodied shot with rich crema and chocolate/caramel notes

**Profile Steps**:
1. Pre-infusion: Flow @ 3 ml/s, end when pressure reaches 2.0 bar
2. Infusion: Pressure @ 9.0 bar, end when 25g yielded
3. Tapering: Linearly decrease pressure 9.0 bar to 5.0 bar, end when 36g total

### Blueprint 2: The "Turbo Shot"
**Best for**: Light Roasts, Single Origins
**Goal**: Bright, clear, acidic shot highlighting floral and fruit notes

**Profile Steps**:
1. Pre-infusion: Flow @ 6 ml/s, end when pressure reaches 1.5 bar
2. Infusion: Pressure @ 6.0 bar, end after 15 seconds total
3. Tapering: Linearly decrease pressure 6.0 bar to 3.0 bar, end when 54g total (1:3 ratio)

### Blueprint 3: The "Soup" Shot (Allongé)
**Best for**: Very Light / Experimental Roasts (high-acidity Geshas)
**Goal**: Tea-like, highly clarified extraction with no bitterness

**Profile Steps**:
1. Pre-wet: Flow @ 4 ml/s, end when 10g yielded
2. Infusion: Flow @ 8 ml/s, end when 72g total (1:4 ratio)
Note: No pressure target, entirely flow-controlled

### Blueprint 4: The "Bloom & Extract"
**Best for**: Very Freshly Roasted Coffee (<7 days from roast)
**Goal**: Manage excess CO2 for even extraction and sweetness

**Profile Steps**:
1. Pre-infusion: Flow @ 3 ml/s, end when pressure reaches 2.0 bar
2. Bloom: Hold lever position (zero flow) for 20 seconds
3. Infusion: Pressure @ 8.0 bar, end when 30g yielded
4. Tapering: Linearly decrease pressure 8.0 bar to 4.0 bar, end when 38g total

## 4. Advanced Troubleshooting & Adaptation

### Sour, thin, salty (Under-extracted)
**Likely Cause**: Insufficient contact time or energy
**Solutions**:
1. Increase Infusion Pressure/Flow: 8 bar → 9 bar, or 2 ml/s → 2.5 ml/s
2. Extend Infusion Time: Increase yield before tapering begins
3. Increase Temperature: 92°C → 94°C

### Bitter, astringent, dry (Over-extracted)
**Likely Cause**: Puck channeled or too much extraction at end
**Solutions**:
1. Lower Infusion Pressure: 9 bar → 8 bar
2. Taper Earlier/Aggressively: Start ramp-down sooner or decrease to lower final pressure
3. Lower Temperature: 94°C → 92°C

### Shot starts too fast (gushing)
**Likely Cause**: Grind too coarse, or pre-infusion too aggressive
**Solutions**:
1. Grind Finer (primary fix)
2. Decrease Pre-infusion Flow: 4 ml/s → 2 ml/s

### Shot chokes (starts too slow)
**Likely Cause**: Grind too fine
**Solutions**:
1. Grind Coarser
2. Add bloom phase to help water penetrate
3. Increase initial infusion pressure to push through resistance

## 5. Profile Design Principles & Best Practices

Based on analysis of successful profile patterns, here are key principles for creating well-designed profiles:

### Control Strategy: Flow vs Pressure

**Flow-Controlled Profiles**:
- More adaptive to puck resistance - automatically adjusts to grind variations
- Better for consistent results across different coffees
- Flow rate determines extraction speed directly
- Use when: Working with variable beans, different grinders, or seeking adaptability
- Example pattern: Set flow rate (e.g., 2-4 ml/s), let pressure vary naturally

**Pressure-Controlled Profiles**:
- More predictable pressure curves, traditional espresso approach
- Requires precise grind matching for optimal results
- Better for: Specific flavor profile targeting, traditional lever machine emulation
- Use when: You have dialed-in grind and want precise control over texture/body
- Example pattern: Set pressure target (e.g., 9 bar), monitor flow as feedback

**Hybrid Approach**:
- Use pressure control with flow limits (safety bounds)
- Use flow control with pressure limits (prevent channeling)
- Best of both worlds: responsive with safety guards

### Stage Transition Design

**Pre-infusion Exit Strategy**:
- Use pressure threshold (<= 2 bar) OR flow threshold (>= 0.2 ml/s) OR weight threshold (>= 0.3g)
- Multiple triggers ensure stage exits when saturation achieved, not on exact timing
- Logical OR prevents getting stuck in pre-infusion if one sensor is slow

**Infusion/Hold Exit Strategy**:
- Always use weight threshold with >= comparison for target yield
- Always include time-based safety timeout (prevents infinite extraction)
- Weight should be primary trigger, time is backup
- Example: [{'type': 'weight', 'value': 30, 'comparison': '>='}, {'type': 'time', 'value': 30}]

**Tapering Exit Strategy**:
- Use final target weight with >= comparison
- Include time limit to prevent over-extraction
- Often final weight is higher than infusion target (e.g., infusion ends at 30g, taper ends at 36g)

### Dynamics Point Design

**Minimum Points Required**:
- Start point: [0, initial_value]
- End point: [duration, final_value]
- More points = smoother transitions but more complex

**Interpolation Strategy**:
- "linear": Predictable, easy to understand, good for most cases
- "curve": Smoother transitions, can feel more natural, good for lever-style profiles
- "none": Instant transitions (rarely needed)

**Pressure Ramp Design**:
- Gentle ramps (3-4 seconds) prevent channeling
- Aggressive ramps (<2 seconds) can cause channeling but faster extraction
- Consider: Slow ramp = more even extraction, fast ramp = faster shot

**Pressure Decline Design**:
- Gradual decline (over 10-15 seconds) = smoother finish
- Steep decline (over 3-5 seconds) = faster finish, may extract more fines
- No decline (flat) = traditional flat profile, may over-extract at end

### Exit Trigger Best Practices

**Always Use Comparison Operators**:
- Use >= for weight thresholds (responsive, exits when reached)
- Use >= for flow thresholds (responsive, exits when achieved)
- Use <= for pressure thresholds when pressure should drop
- Never rely on exact matches - they're unreliable and slow

**Multiple Triggers = Safety & Responsiveness**:
- Primary trigger: The main goal (weight, flow, etc.)
- Secondary trigger: Safety timeout (time-based)
- Tertiary trigger: Early exit condition (pressure drops, flow increases, etc.)
- Logical OR ensures the stage exits on the FIRST condition met

**Relative vs Absolute Values**:
- Relative weight: Value relative to stage start (useful for multi-stage recipes)
- Absolute weight: Total weight from shot start (easier to understand)
- Use absolute for clarity, relative only when needed for complex recipes

### Temperature Considerations

**Roast Level Matching**:
- Light roasts: Higher temp (92-96°C) needed for proper extraction
- Medium roasts: Balanced temp (90-93°C)
- Dark roasts: Lower temp (84-92°C) prevents over-extraction bitterness

**Profile-Specific Temperature**:
- Flow profiles: Can use slightly higher temp (compensates for faster extraction)
- Pressure profiles: Traditional temp ranges work well
- Long extraction (Soup/Filter): Higher temp helps maintain extraction rate

### Yield Target Design

**Espresso Range** (25-40g):
- Classic espresso: 30-36g yield
- Ristretto: 20-25g yield
- Lungo: 40-50g yield

**Extended Range** (40-100g):
- Sprover: 40-60g (hybrid espresso/pour-over)
- Soup/Allongé: 60-100g+ (tea-like extraction)
- Filter-style: 100g+ (very light roasts)

**Yield Distribution Across Stages**:
- Pre-infusion: 5-10% of total yield (5-8g for 40g shot)
- Infusion: 60-75% of total yield (25-30g for 40g shot)
- Tapering: Remaining 20-30% (8-12g for 40g shot)

### Stage Naming & Organization

**Clear Stage Names**:
- "Preinfusion" - clearly indicates purpose
- "Ramp" - indicates pressure/flow increase
- "Hold" - indicates steady state
- "Decline" - indicates decrease phase
- Avoid generic names like "Stage 1", "Stage 2"

**Stage Key Naming**:
- Use descriptive keys: "preinfusion", "ramp", "hold", "decline"
- Make keys unique and meaningful
- Helps with debugging and profile understanding

### Profile Iteration & Refinement

**Version Tracking**:
- Use version numbers (v1, v2, v2.5) to track iterations
- Document what changed between versions
- Helps identify what works and what doesn't

**Testing Strategy**:
- Start with template profiles (3-stage flow/pressure)
- Make small incremental changes
- Test one variable at a time (temperature, pressure, flow, yield)
- Mark experimental profiles as "WIP" until validated

**Adaptation for Equipment**:
- Grinder characteristics matter: "large delta" vs "small delta" grinders
- Grinder particle distribution affects optimal flow/pressure
- May need different profiles for different grinders
- Temperature stability affects profile consistency

### Common Anti-Patterns to Avoid

**❌ Single Exit Trigger**:
- Only weight OR only time = risky
- Always include multiple triggers for safety

**❌ Exact Match Triggers**:
- Waiting for exact weight (e.g., 30.0g) = unreliable
- Use >= comparison for responsive transitions

**❌ Too Many Stages**:
- More than 5-6 stages = overcomplicated
- Hard to tune and understand
- 3-4 stages is usually optimal

**❌ Inconsistent Naming**:
- Unclear stage names = confusion
- Use descriptive, consistent naming

**❌ No Safety Timeouts**:
- Missing time-based triggers = risk of infinite extraction
- Always include time backups

**❌ Pressure Spikes**:
- Sudden pressure jumps = channeling risk
- Use gentle ramps (3+ seconds)

**❌ Ignoring Grinder Characteristics**:
- One profile for all grinders = suboptimal
- Consider grinder particle distribution"""


@mcp.resource("espresso://schema")
def espresso_schema() -> str:
    """Get the profile schema reference."""
    _ensure_initialized()
    try:
        schema_path = Path(__file__).parent.parent.parent / "espresso-profile-schema" / "schema.json"
        if not schema_path.exists():
            schema_path = Path(__file__).parent.parent.parent.parent / "espresso-profile-schema" / "schema.json"
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f), indent=2)
    except Exception as e:
        return f"Error loading schema: {e}"


@mcp.resource("espresso://profile/{profile_id}")
def get_profile_resource(profile_id: str) -> str:
    """Get a profile as a resource."""
    _ensure_initialized()
    from meticulous.api_types import APIError
    
    result = _api_client.get_profile(profile_id)
    if isinstance(result, APIError):
        error_msg = result.error or result.status or "Unknown error"
        return f"Error: {error_msg}"
    
    return json.dumps(profile_to_dict(result), indent=2)


# Register prompts
@mcp.prompt()
def create_espresso_profile(
    coffee_type: Optional[str] = None,
    roast_level: Optional[str] = None,
    style: Optional[str] = None,
    target_weight: Optional[float] = None,
    coffee_age_days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Prompt template for creating an espresso profile with knowledge-based guidance."""
    messages = []
    
    # System context with knowledge
    system_context = """You are an expert espresso profile creator for the Meticulous machine. 

Use the four-phase approach: Pre-infusion → Bloom (optional) → Infusion → Tapering.

Guidelines:
- Pre-infusion: Flow 2-4 ml/s, end at ~2 bar or first drops
- Infusion: Most critical phase. Use pressure 6-9 bar OR flow 1.5-3 ml/s
- Tapering: Reduce pressure/flow in final 1/3 of shot to minimize bitterness

Profile Blueprints:
- Classic Lever (medium-dark roasts): Pre-infusion 3 ml/s → Infusion 9 bar → Taper 9→5 bar, 36g target
- Turbo Shot (light roasts): Pre-infusion 6 ml/s → Infusion 6 bar, 15s → Taper 6→3 bar, 54g target
- Soup Shot (very light): Flow-controlled, 4 ml/s → 8 ml/s, 72g target
- Bloom & Extract (fresh coffee <7 days): Pre-infusion → 20s bloom → Infusion → Taper

Temperature Guidelines:
- Light roasts: 92-96°C
- Medium roasts: 90-93°C  
- Dark roasts: 84-92°C

Profile Design Principles:
- Control Strategy: Flow-controlled profiles are more adaptive to grind variations. Pressure-controlled profiles offer precise control but require dialed-in grind.
- Exit Triggers: Always use comparison operators (>= for weight/flow, <= for pressure). Include multiple triggers (primary goal + safety timeout) for reliability.
- Stage Transitions: Pre-infusion should exit on pressure drop OR flow increase OR weight threshold. Infusion should exit on weight >= target with time backup. Tapering should exit on final weight >= target.
- Dynamics Design: Use at least 2 points (start and end). Gentle ramps (3-4s) prevent channeling. Gradual declines (10-15s) provide smoother finish.
- Yield Distribution: Pre-infusion 5-10%, Infusion 60-75%, Tapering 20-30% of total yield.
- Always include safety timeouts to prevent infinite extraction.
- Avoid exact match triggers - they're unreliable.

Create profiles with structured stages using exit triggers based on flow rate, weight, time, or pressure. Favor flow rate, and pressure over time. Use time in conjunction with other measures or as an or gate if something is taking too long."""
    
    messages.append({
        "role": "system",
        "content": {
            "type": "text",
            "text": system_context,
        },
    })
    
    # User request
    prompt_parts = ["Create a new espresso profile"]
    
    if coffee_type:
        prompt_parts.append(f"for {coffee_type} coffee")
    
    if roast_level:
        prompt_parts.append(f"with {roast_level} roast level")
        if roast_level.lower() in ["light", "very light"]:
            prompt_parts.append("(consider higher temperature 92-96°C and Turbo Shot or Soup Shot blueprint)")
        elif roast_level.lower() in ["dark", "medium-dark"]:
            prompt_parts.append("(consider lower temperature 84-92°C and Classic Lever blueprint)")
    
    if coffee_age_days is not None and coffee_age_days < 7:
        prompt_parts.append(f"(very fresh coffee, {coffee_age_days} days old - consider Bloom & Extract blueprint with bloom phase)")
    
    if style:
        style_map = {
            "classic": "Classic Lever blueprint",
            "turbo": "Turbo Shot blueprint",
            "soup": "Soup Shot blueprint",
            "allongé": "Soup Shot blueprint",
            "bloom": "Bloom & Extract blueprint",
        }
        blueprint = style_map.get(style.lower(), style)
        prompt_parts.append(f"using {blueprint} approach")
    
    if target_weight:
        prompt_parts.append(f"targeting {target_weight}g output")
        # Suggest extraction ratio guidance
        if target_weight >= 50:
            prompt_parts.append("(aiming for 1:3 or higher ratio - consider Turbo Shot or Soup Shot)")
        elif target_weight <= 30:
            prompt_parts.append("(traditional ratio - consider Classic Lever)")
    
    prompt_text = " ".join(prompt_parts) + "."
    
    prompt_text += "\n\nSpecify:"
    prompt_text += "\n- Temperature (based on roast level)"
    prompt_text += "\n- Pre-infusion stage (flow rate, exit trigger)"
    prompt_text += "\n- Infusion stage (pressure/flow target, exit trigger)"
    prompt_text += "\n- Tapering stage (pressure/flow reduction, exit trigger)"
    prompt_text += "\n- Any optional bloom phase if needed"
    
    messages.append({
        "role": "user",
        "content": {
            "type": "text",
            "text": prompt_text,
        },
    })
    
    return messages


@mcp.prompt()
def modify_espresso_profile(
    profile_id: str,
    taste_issue: Optional[str] = None,
    modification_goal: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Prompt template for modifying an espresso profile with troubleshooting guidance."""
    messages = []
    
    # System context with troubleshooting knowledge
    system_context = """You are an expert at troubleshooting and refining espresso profiles for the Meticulous machine.

Common Issues & Solutions:

**Sour, thin, salty (Under-extracted)**:
- Increase infusion pressure/flow (8→9 bar or 2→2.5 ml/s)
- Extend infusion time (increase yield before tapering)
- Increase temperature (92→94°C)

**Bitter, astringent, dry (Over-extracted)**:
- Lower infusion pressure (9→8 bar)
- Taper earlier/more aggressively (start ramp-down sooner, lower final pressure)
- Lower temperature (94→92°C)

**Shot starts too fast (gushing)**:
- Primary: Grind finer
- Profile fix: Decrease pre-infusion flow (4→2 ml/s)

**Shot chokes (starts too slow)**:
- Primary: Grind coarser
- Profile fix: Add bloom phase or increase initial infusion pressure

Modify profiles incrementally - adjust one parameter at a time to understand its effect."""
    
    messages.append({
        "role": "system",
        "content": {
            "type": "text",
            "text": system_context,
        },
    })
    
    # User request
    prompt_parts = [f"Modify espresso profile {profile_id}"]
    
    if taste_issue:
        issue_lower = taste_issue.lower()
        if any(word in issue_lower for word in ["sour", "thin", "salty", "under"]):
            prompt_parts.append("to address under-extraction")
            prompt_parts.append("(consider increasing infusion pressure/flow, extending infusion time, or raising temperature)")
        elif any(word in issue_lower for word in ["bitter", "astringent", "dry", "over"]):
            prompt_parts.append("to address over-extraction")
            prompt_parts.append("(consider lowering infusion pressure, tapering earlier, or reducing temperature)")
        elif any(word in issue_lower for word in ["gush", "fast", "rush"]):
            prompt_parts.append("to address gushing")
            prompt_parts.append("(consider decreasing pre-infusion flow rate)")
        elif any(word in issue_lower for word in ["choke", "slow", "stuck"]):
            prompt_parts.append("to address choking")
            prompt_parts.append("(consider adding bloom phase or increasing initial infusion pressure)")
        else:
            prompt_parts.append(f"to address: {taste_issue}")
    
    if modification_goal:
        prompt_parts.append(f"with the goal to: {modification_goal}")
    
    prompt_text = " ".join(prompt_parts) + "."
    
    prompt_text += "\n\nIdentify which stage(s) need modification:"
    prompt_text += "\n- Pre-infusion (flow rate, exit trigger)"
    prompt_text += "\n- Infusion (pressure/flow target, exit trigger)"
    prompt_text += "\n- Tapering (pressure/flow reduction, exit trigger)"
    prompt_text += "\n- Temperature adjustment"
    prompt_text += "\n- Adding/removing bloom phase"
    
    messages.append({
        "role": "user",
        "content": {
            "type": "text",
            "text": prompt_text,
        },
    })
    
    return messages


@mcp.prompt()
def troubleshoot_profile(
    profile_id: str,
    symptom: str,
    shot_duration: Optional[float] = None,
    yield_weight: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Prompt template for troubleshooting an espresso profile based on symptoms."""
    messages = []
    
    system_context = """You are an expert espresso troubleshooting specialist for the Meticulous machine.

Use the troubleshooting guide to diagnose and fix profile issues:

**Diagnosis Process**:
1. Identify the taste/texture symptom
2. Determine if it's under-extraction, over-extraction, or flow issue
3. Check shot parameters (duration, yield, pressure curve)
4. Apply targeted fixes based on the issue category

**Key Principles**:
- Make incremental changes
- One parameter at a time to understand effects
- Consider grind size first (if gushing/choking)
- Then adjust profile parameters
- Finally adjust temperature if needed"""
    
    messages.append({
        "role": "system",
        "content": {
            "type": "text",
            "text": system_context,
        },
    })
    
    prompt_parts = [
        f"Troubleshoot profile {profile_id}",
        f"with symptom: {symptom}",
    ]
    
    if shot_duration:
        prompt_parts.append(f"(shot duration: {shot_duration}s)")
    
    if yield_weight:
        prompt_parts.append(f"(yield: {yield_weight}g)")
    
    prompt_text = " ".join(prompt_parts) + "."
    prompt_text += "\n\nAnalyze the issue and recommend specific profile modifications."
    
    messages.append({
        "role": "user",
        "content": {
            "type": "text",
            "text": prompt_text,
        },
    })
    
    return messages


def main():
    """Main entry point for running the server."""
    mcp.run("stdio")


if __name__ == "__main__":
    main()

