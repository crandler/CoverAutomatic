/**
 * CoverAutomatic Config Panel
 * Home Assistant custom panel for intelligent cover/shutter automation.
 * Vanilla web component with Shadow DOM -- no external dependencies.
 */

/* ============================================================
 * Curated scenario icon choices (Material Design Icons)
 * ============================================================ */
// Keep in sync with MAX_CONDITION_GROUPS in models.py
const MAX_CONDITION_GROUPS = 10;

const SCENARIO_ICON_CHOICES = [
  "mdi:home", "mdi:home-variant",
  "mdi:white-balance-sunny", "mdi:weather-sunny",
  "mdi:weather-night", "mdi:moon-waning-crescent",
  "mdi:weather-sunset", "mdi:weather-sunset-up",
  "mdi:snowflake", "mdi:weather-partly-cloudy",
  "mdi:airplane", "mdi:beach",
  "mdi:car", "mdi:office-building",
  "mdi:television", "mdi:movie-open",
  "mdi:gamepad-variant", "mdi:music",
  "mdi:sofa", "mdi:bed",
  "mdi:silverware-fork-knife", "mdi:coffee",
  "mdi:account-group", "mdi:party-popper",
  "mdi:sleep", "mdi:shield-home",
  "mdi:fire", "mdi:weather-windy",
  "mdi:gesture-tap", "mdi:cog",
  "mdi:star", "mdi:heart",
];

/* ============================================================
 * i18n translations
 * ============================================================ */
const I18N = {
  en: {
    title: "CoverAutomatic",
    version_link_title: "Open release notes on GitHub",
    update_badge_title: "Update available - open release notes on GitHub",
    tabs: { covers: "Covers", facades: "Facades", rules: "Rules", scenarios: "Scenarios", settings: "Settings", log: "Log" },
    nav_label: "Sections",
    loading: "Loading configuration...",
    error_load: "Failed to load configuration.",
    retry: "Retry",
    saved: "Saved",
    cond_time_after_dawn: "Time after dawn",
    cond_time_before_dawn: "Time before dawn",
    cond_time_after_dusk: "Time after dusk",
    cond_time_before_dusk: "Time before dusk",
    cond_time_after_dawn_hint: "From dawn (+ offset) until dusk. Complement: “{other}”.",
    cond_time_before_dawn_hint: "From dusk until the next dawn (+ offset). Complement: “{other}”.",
    cond_time_after_dusk_hint: "From dusk (+ offset) until the next dawn. Complement: “{other}”.",
    cond_time_before_dusk_hint: "From dawn until dusk (+ offset). Complement: “{other}”.",
    cond_time_after_sunrise_hint: "From sunrise (+ offset) until sunset. Complement: “{other}”.",
    cond_time_before_sunrise_hint: "From sunset until the next sunrise (+ offset). Complement: “{other}”.",
    cond_time_after_sunset_hint: "From sunset (+ offset) until the next sunrise. Complement: “{other}”.",
    cond_time_before_sunset_hint: "From sunrise until sunset (+ offset). Complement: “{other}”.",
    cover_travel_auto_default: "default: {s} s",
    cover_travel_not_measured: "Measured: not yet (on the next move of at least 20 %).",
    cover_travel_used: "Used: {s} s ({src}) · wait before detecting a manual move: {wait} s",
    cover_travel_used_none: "Used: none · wait before detecting a manual move: {wait} s",
    cover_travel_src_manual: "entered",
    cover_travel_src_measured: "measured",
    cover_travel_src_default: "global default",
    cover_travel_src_none: "none",
    settings_default_travel_time: "Default travel time (s)",
    settings_default_travel_time_placeholder: "none (30 s wait)",
    settings_default_travel_time_hint: "Travel time used for covers with no value entered and none measured yet. Order: value entered on the cover, then measured value, then this default. Empty = 30 s wait.",
    cover_travel_time: "Travel time (s)",
    cover_travel_auto: "auto (measured on the first moves)",
    cover_travel_auto_measured: "auto: {s} s measured",
    cover_travel_measured: "Measured: {s} s for a full travel.",
    cover_travel_reset: "Reset",
    cover_travel_time_hint: "Time for a full 0 → 100 % travel. After its own command, the integration waits this long (plus 5 s, at least 30 s) before treating a position change as a manual action. Leave empty to use the measured value, or else the default travel time from Settings.",
    scenario_rule_off: "disabled in Rules",
    scenario_rule_off_hint: "This rule is switched off in the Rules tab, so it never runs. The setting below applies again once the rule is enabled.",
    ha_ctype_and: "and",
    ha_ctype_or: "or",
    ha_ctype_not: "not",
    ha_ctype_template: "template",
    ha_ctype_state: "state",
    ha_ctype_numeric_state: "numeric value",
    ha_ctype_zone: "zone",
    ha_ctype_time: "time",
    ha_ctype_sun: "sun",
    ha_ctype_device: "device",
    ha_ctype_trigger: "trigger",
    cond_group_sun: "Sun",
    cond_group_temperature: "Temperature",
    cond_group_time: "Time",
    cond_group_weather: "Weather",
    cond_group_entities: "Entities",
    cond_menu_ha_state: "Entity state",
    cond_menu_ha_numeric: "Entity numeric value",
    cond_menu_ha_yaml: "Home Assistant condition (YAML)",
    cond_ha_condition: "Home Assistant condition",
    cond_ha_state: "Entity state",
    cond_ha_numeric: "Entity numeric value",
    ha_tab_form: "Form",
    ha_tab_yaml: "YAML",
    ha_kind: "Type",
    ha_kind_state: "State",
    ha_kind_numeric: "Numeric value",
    ha_entity: "Entity",
    ha_current: "currently",
    ha_attribute: "Attribute",
    ha_attribute_none: "— entity state —",
    ha_compare: "Comparison",
    ha_is: "is",
    ha_is_not: "is not",
    ha_for: "For at least (min)",
    ha_for_negate_hint: "Not available with “is not”.",
    ha_states: "States",
    ha_state_other: "Other value…",
    ha_state_add: "Add",
    ha_operator: "Operator",
    ha_op_above: "above",
    ha_op_below: "below",
    ha_op_between: "between",
    ha_value: "Value",
    ha_min: "Minimum",
    ha_max: "Maximum",
    ha_form_unsupported: "This condition cannot be shown as a form (template, zone, nested conditions…). It stays editable in YAML.",
    ha_yaml_label: "Condition",
    ha_yaml_placeholder: "condition: state\nentity_id: person.me\nstate: not_home\nfor: \"00:15:00\"",
    ha_yaml_help: "Same format as the “condition” section of a Home Assistant automation. A list of conditions is combined with AND.",
    ha_valid: "Valid condition",
    ha_entities: "Watched entities",
    ha_unknown_entities: "Entities not found (check the id)",
    ha_err_yaml: "YAML syntax error at line {line}, column {column}",
    ha_err_not_mapping: "The YAML must describe one condition (e.g. “condition: state”).",
    ha_err_invalid: "Invalid condition",
    ha_err_empty: "Empty condition",
    ha_checking: "Checking…",
    ha_incomplete_entity: "Choose an entity.",
    ha_incomplete_states: "Choose at least one state.",
    ha_incomplete_value: "Enter a value.",
    cond_convert: "Convert to enhanced condition",
    cond_convert_hint: "Adds attribute, “is not”, duration and state choices. Applied when the rule is saved.",
    ha_chip_is: "{entity} is {states}",
    ha_chip_is_not: "{entity} is not {states}",
    ha_chip_for: " for {min} min",
    ha_chip_or: " or ",
    ha_chip_above: "{entity} > {value}",
    ha_chip_below: "{entity} < {value}",
    ha_chip_between: "{entity} between {min} and {max}",
    ha_chip_other: "HA condition: {type}",
    rule_op_short_and: "AND", rule_op_short_or: "OR",
    compass_n: "N", compass_e: "E", compass_s: "S", compass_w: "W",
    error_generic: "Could not save the change",
    error_not_found: "Item not found (it may have been deleted meanwhile)",
    error_invalid_format: "Invalid value",
    error_invalid_conditions: "Invalid rule condition",
    error_invalid_data: "Invalid configuration data",
    error_too_large: "Import file is too large",
    error_unauthorized: "Administrator rights required",
    error_invalid_comfort_range: "The cold setpoint must be lower than the hot setpoint",
    error_invalid_wind_hysteresis: "The wind hysteresis must be lower than the wind threshold",
    rule_priority_up: "Raise priority",
    rule_priority_down: "Lower priority",
    rule_enabled_aria: "Rule {name} enabled",
    rule_invalid_fields: "Fix the fields marked in red (empty or invalid value) before saving",
    ha_err_request: "Check failed",
    error_not_loaded: "CoverAutomatic is not loaded (reload the integration or restart Home Assistant)",
    error_invalid_solar_hysteresis: "The sunshine hysteresis must be lower than the sunshine threshold",
    error_invalid_value: "Invalid number",
    drag_handle: "Drag to reorder",
    settings_nav_label: "Settings",
    import_invalid_json: "Invalid JSON",
    status_unlocked: "Unlocked",
    log_msg_wind_activated: "Activated ({speed} ≥ {threshold})",
    log_msg_wind_deactivated: "Deactivated ({speed} ≤ {threshold})",
    log_msg_wind_disabled: "Deactivated (disabled in settings)",
    log_msg_status_change: "{from} → {to}",
    log_msg_rule: "{rule} → {position} %",
    log_msg_position: "{from} % → {to} %",
    log_msg_safety_takeover: "Safety rule {rule} takes over ({status}) → {position} %",
    log_msg_safety_release: "Safety rule {rule} released ({status})",
    log_msg_sensor_unavailable: "{status} kept: sensor {sensor} unavailable",
    log_msg_lock_sensor_missing: "Window sensor {sensor} not found: ignored",
    log_msg_move_blocked_window_unknown: "Move to {position} % held: window state unknown ({sensor})",
    log_msg_wind_restore_dropped: "Wind protection restore dropped: sensor {sensor} missing or without value",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    rule_duplicate: "Duplicate (the copy is created right below)",
    rule_copy_suffix: "copy",
    settings_wind_off_note: "Choose a wind sensor to enable wind protection.",
    settings_solar_off_note: "Choose a sensor to set the threshold and hysteresis.",
    settings_solar_nested_off: "Only used by the option “Only with strong sunshine” (here or on a cover).",
    cover_lock_box_title: "Window open",
    cover_lock_off_note: "Choose a window sensor to enable these settings.",
    cover_vent_box_title: "Window tilted (ventilation)",
    cover_vent_off_note: "Choose a tilt sensor to set the ventilation position.",
    confirm_delete: "Really delete?",
    add: "Add",
    edit: "Edit",
    close: "Close",
    none: "None",
    enabled: "Enabled",
    active: "Active",
    activate: "Activate",
    name: "Name",
    // Covers
    cover_facade: "Facade",
    cover_facade_hint: "Determines which facade rules apply to this cover.",
    cover_status: "Status",
    cover_pause_duration: "Pause duration (min)",
    cover_pause_duration_hint: "How long automation pauses after manual operation. Empty = use global default.",
    cover_indoor_temp: "Indoor temperature sensor (°C)",
    cover_indoor_temp_hint: "Sensor of this cover's room, for the setpoints and “Sun on facade”. Replaces the global sensor.",
    cover_lock_sensor: "Open window sensor",
    cover_lock_sensor_hint: "Window contact sensor. When open, cover moves to lock position (safety).",
    cover_lock_hold: "Keep current position when the window opens",
    cover_lock_hold_hint: "On: the cover stays where it is while the window is open (locked, no command). Off: it moves to the lock position below (only upwards, never closer).",
    cover_lock_position: "Lock position",
    cover_lock_position_hint: "Target position when window is open. Empty = use global default.",
    cover_vent_sensor: "Tilted window sensor",
    cover_vent_sensor_hint: "Tilt contact sensor. When tilted, cover moves to vent position.",
    cover_vent_position: "Vent position",
    cover_vent_position_hint: "Target position when window is tilted. Empty = use global default.",
    cover_comfort_min: "Cold temperature setpoint (°C)",
    cover_comfort_max: "Hot temperature setpoint (°C)",
    cover_comfort_hint: "Setpoints for this room. Empty = global values from settings.",
    cover_comfort_global: "Empty = global value: {v} °C ({src})",
    cover_default_note: "Empty = default value: {v} (Settings)",
    unit_sensor: "sensor unit",
    cover_comfort_src_settings: "Settings",
    cover_sun_switches_hint: "Settings for this cover only; “Global” = value from Settings › Sun exposure.",
    tristate_global: "Global ({value})",
    settings_sun_facade_hint: "These settings only change the answer of the “Sun on facade” condition, for covers with an indoor temperature sensor (own or global). They are meant for rules that close when the sun is out: close only when it helps. Leave everything off if a rule opens the covers when the sun is out.",
    sun_heating_label: "Action at the cold setpoint: let the sun warm the room",
    sun_heating_hint: "The condition answers “no sun”: rules that close in the sun don't close and the sun warms the room. Avoid it if a rule opens the covers when the sun is out (it would no longer apply).",
    sun_below: "≤ {t} °C",
    sun_above: "≥ {t} °C",
    sun_between: "between {min} and {max} °C",
    settings_comfort_range_title: "Indoor temperature setpoints",
    settings_indoor_reminder: "Applies according to each room's indoor temperature (Sensors tab: global sensor {name}, setpoints {min} and {max} °C). A cover can have its own sensor and setpoints.",
    settings_indoor_none: "not set",
    sun_explain_title: "How does it work?",
    sun_explain_intro: "Example: a “close if sun” rule with the sun on the facade. Highlighted rows match your settings.",
    sun_explain_col_room: "Room",
    sun_explain_col_answer: "“Sun on facade” answers",
    sun_explain_col_effect: "Effect",
    sun_explain_room_cold_on: "Cold, “let the sun warm it” checked",
    sun_explain_room_cold_off: "Cold, box unchecked",
    sun_explain_room_position: "Comfortable, “As soon as the sun is on the facade”",
    sun_explain_room_ignore: "Comfortable, “Never”",
    sun_explain_room_preemptive: "Comfortable, “Only with strong sunshine”",
    sun_explain_room_hot: "Too hot",
    sun_explain_sun: "“sun”",
    sun_explain_no_sun: "“no sun”",
    sun_explain_sun_always: "always “sun”",
    sun_explain_sun_if_strong: "“sun” if the sensor exceeds the threshold, otherwise “no sun”",
    sun_explain_eff_warm: "Does not close: the cover stays open and the room warms up.",
    sun_explain_eff_close: "Closes.",
    sun_explain_eff_close_as_hot: "Closes, as if the room were hot.",
    sun_explain_eff_wait: "Does not close; will close once the room gets too hot.",
    sun_explain_eff_strong: "Only closes in bright sunshine, before the room heats up.",
    sun_explain_so: "So",
    sun_explain_cold: "Cold room: the box does not open the cover, it prevents closing because of the sun. If the cover is already open (by a daytime opening rule, for example), it stays open.",
    sun_explain_hot: "Room too hot: the cover only closes if a “close if sun” rule applies to this cover and to the active scenario.",
    sun_explain_comfort: "Comfortable room: the in-between, where you choose when the sun should count.",
    sun_comfort_label: "Action between the setpoints: behaviour depending on the sun",
    sun_comfort_position: "As soon as the sun is on the facade",
    sun_comfort_position_hint: "The condition is true as soon as the sun is on the facade.",
    sun_comfort_ignore: "Never (wait until the room gets too hot)",
    sun_comfort_ignore_hint: "Answers “no sun”: the cover only closes once the room gets too hot.",
    sun_comfort_preemptive: "Only with strong sunshine",
    sun_comfort_preemptive_hint: "Answers “sun” as soon as the sunshine sensor exceeds its threshold: the cover closes before the room heats up.",
    sun_comfort_hint: "Behaviour of “Sun on facade” while the room is between the setpoints. Global = value set in Settings › Sun exposure.",
    sun_hot_note: "Room too hot (≥ {t} °C): the sun always counts as soon as it is on the facade.",
    solar_used_by: "Used by the option “Only with strong sunshine”: {n} cover(s).",
    solar_unused: "Only used by the option “Only with strong sunshine” (no cover uses it at the moment).",
    tristate_on: "Enabled",
    tristate_off: "Disabled",
    cover_inverted: "Reverse open/close direction",
    cover_inverted_hint: "Enable if 100% means closed (reversed motor direction).",
    cover_lock_tilt: "Lock tilt position",
    cover_vent_tilt: "Vent tilt position",
    cover_inverted_tilt: "Inverted tilt",
    cover_min_pos_change: "Min. position change (%)",
    cover_min_pos_change_hint: "Minimum position difference to trigger a move. Empty = use global default.",
    cover_min_time: "Min. time between changes (s)",
    cover_min_time_hint: "Minimum seconds between position changes. Empty = use global default.",
    cover_section_base: "General",
    cover_section_sensors: "Sensors",
    cover_section_advanced: "Advanced",
    cover_section_tilt: "Tilt",
    cover_section_window: "Window",
    cover_section_automation: "Automation",
    cover_section_room: "Room",
    cover_inverted_short: "Reversed",
    cover_lock_hold_short: "Keep position",
    sun_heating_label_short: "Cold: let it warm",
    sun_comfort_label_short: "Between setpoints",
    settings_comfort_min_short: "Cold setpoint (°C)",
    settings_comfort_max_short: "Hot setpoint (°C)",
    cover_comfort_min_short: "Cold setpoint (°C)",
    cover_comfort_max_short: "Hot setpoint (°C)",
    settings_indoor_temp_short: "Indoor sensor (°C)",
    cover_indoor_temp_short: "Indoor sensor (°C)",
    settings_comfort_hysteresis_short: "Setpoint hysteresis (°C)",
    settings_threshold_hysteresis_short: "Outdoor hysteresis (°C)",
    settings_solar_hysteresis_short: "Sunshine hysteresis",
    settings_wind_hysteresis_short: "Wind hysteresis",
    settings_solar_threshold_short: "Strong sunshine threshold",
    settings_sun_facade_title_short: "Sun on facade",
    cover_min_time_short: "Min. delay (s)",
    cover_min_pos_change_short: "Min. change (%)",
    cover_expand_all: "Expand all",
    cover_collapse_all: "Collapse all",
    cover_sum_auto_on: "Automatic",
    cover_sum_auto_off: "Automation disabled",
    cover_sum_no_facade: "no facade",
    cover_sum_open: "Open: {v}",
    cover_sum_hold: "keep position",
    cover_sum_tilted: "Tilted: {v}",
    cover_sum_no_window: "No window sensor",
    cover_sum_pause: "Pause {n} min",
    cover_sum_travel: "Travel {n} s",
    cover_sum_own: "{n} own setting(s)",
    cover_sum_all_global: "default values",
    cover_sum_global: "global",
    cover_sum_no_indoor: "No indoor sensor",
    cover_sum_sun_heat_on: "Cold: let the sun warm",
    cover_sum_sun_heat_off: "Cold: sun counts",
    cover_sum_sun_between: "Between: {v}",
    cover_sum_mode_position: "as soon as the sun is there",
    cover_sum_mode_ignore: "never",
    cover_sum_mode_preemptive: "strong sunshine",
    cover_auto_enabled: "Automation enabled",
    cover_temp: "Temp",
    cover_current_pos: "Current",
    cover_target_pos: "Target",
    cover_position: "Position",
    cover_position_target_label: "Target",
    cover_position_inverted_tip: "Inverted cover: HA reports {raw}% (shown here on the rules' scale)",
    cover_hysteresis_position: "Position change too small",
    cover_hysteresis_time: "Too soon since last change",
    cover_rule: "Rule",
    cover_no_rule: "–",
    cover_resume: "Resume",
    cover_goto_rule: "Open rule",
    cover_remove: "Remove cover",
    cover_last_change: "Last change",
    cover_just_now: "just now",
    time_ago_min: "{n} min ago",
    time_ago_h: "{n} h ago",
    time_ago_h_m: "{h} h {m} min ago",
    show_hint: "Show hint",
    settings_temp_color: "Room temperature colours (cover list)",
    settings_temp_color_action: "By action needed",
    settings_temp_color_action_hint: "Cold room in red (to heat), hot room in blue (to cool).",
    settings_temp_color_thermometer: "By temperature",
    settings_temp_color_thermometer_hint: "Cold room in blue, hot room in red, like a thermometer.",
    comfort_cooling: "Hot – to cool",
    comfort_heating: "Cold – to heat",
    comfort_neutral: "Comfort",
    cover_add: "Add covers",
    // Facades
    facade_direction: "Direction",
    facade_direction_hint: "Presets azimuth values with house rotation applied.",
    facade_azimuth_start: "Azimuth start",
    facade_azimuth_end: "Azimuth end",
    facade_azimuth_hint: "Real compass bearings where sun enters/exits this facade. Start = end: full circle.",
    facade_min_elevation: "Min. elevation",
    facade_min_elevation_hint: "Minimum sun elevation for this facade to count as sun-exposed. Values below 0 are treated as 0.",
    facade_covers: "Assigned covers",
    facade_add: "Add facade",
    facade_no_covers: "No covers assigned",
    facade_sun_active: "Sun on facade",
    facade_dir_north: "North",
    facade_dir_east: "East",
    facade_dir_south: "South",
    facade_dir_west: "West",
    // Rules
    rule_priority: "Priority",
    rule_target_pos: "Target position",
    rule_target_pos_hint: "Cover position when this rule matches (0 = closed, 100 = fully open).",
    rule_target_tilt: "Target tilt position",
    rule_operator: "Condition operator",
    rule_operator_hint: "AND = all conditions must match. OR = any condition is enough.",
    rule_operator_and: "AND (all must match)",
    rule_operator_or: "OR (any must match)",
    rule_conditions: "Conditions",
    rule_scenarios: "Scenarios",
    rule_scenarios_hint: "Scenarios in which this rule applies. In each scenario it can still be switched off temporarily from the Scenarios tab.",
    rule_safety: "Safety rule",
    rule_safety_hint: "Acts even when the cover is paused after a manual move, in manual mode, wind-protected or with automation disabled. Does not override the lock (window open). Between rules, priority decides: put it at the top of the list. Reserve it for emergencies, e.g. the fire alarm.",
    rule_safety_badge: "Safety",
    scenario_no_member_rules: "No rule belongs to this scenario (select it in the rule editor).",
    rule_groups_operator: "Groups are joined by",
    rule_groups_hint: "AND = every group must match. OR = one group is enough. Inside a group, its own operator applies.",
    rule_group: "Group",
    rule_group_joined_by: "conditions joined by",
    rule_group_add: "Add a group",
    rule_group_add_hint: "Groups allow e.g. (A OR B) AND (C OR D), or (A AND B) OR (C AND D).",
    rule_group_delete: "Delete the group and its conditions",
    rule_group_delete_confirm: "Delete this group and its conditions?",
    rule_unsaved_confirm: "Discard unsaved changes to this rule?",
    discard: "Discard",
    input_invalid_range: "Enter a whole number between {min} and {max}",
    input_not_integer: "Enter a whole number",
    input_invalid_number: "Enter a valid number",
    rule_group_empty: "No condition in this group yet (empty groups are ignored).",
    rule_cond_move: "Move to another group",
    rule_cond_up: "Move up",
    rule_cond_down: "Move down",
    rule_group_up: "Move group up",
    rule_group_down: "Move group down",
    rule_cond_not: "NOT",
    rule_cond_not_hint: "Invert this condition (NOT). If its sensor is unavailable, the condition is not met.",
    rule_groups_count: "{n} groups",
    cond_collapse: "Collapse",
    cond_expand: "Expand",
    cond_collapse_all: "Collapse all",
    cond_expand_all: "Expand all",
    rule_facades: "Facades",
    rule_covers: "Covers",
    rule_assignment_hint: "Limit this rule to specific facades/covers. Empty = applies to all covers.",
    rule_add: "Add rule",
    rule_duplicate: "Duplicate",
    rule_copy_suffix: "(copy)",
    rule_add_condition: "Add condition",
    rule_no_conditions: "No conditions",
    rule_reorder_hint: "Drag or use ▲▼ to reorder. Top rule wins when multiple rules match.",
    // Condition types
    cond_sun_on_facade: "Sun on facade",
    cond_sun_elevation_above: "Sun elevation above",
    cond_sun_elevation_below: "Sun elevation below",
    cond_temperature_above: "Outdoor temperature above",
    cond_temperature_below: "Outdoor temperature below",
    cond_temperature_comfort: "Room temperature",
    cond_outdoor_vs_indoor: "Outdoor air compared to the room",
    cond_room_occupied: "Room occupied",
    cond_group_presence: "Presence",
    opt_cooler: "cooler than the room",
    opt_warmer: "warmer than the room",
    param_delta: "Minimum difference (°C)",
    cover_occupancy_box_title: "Room occupancy",
    cover_occupancy_sensor: "Occupancy sensor",
    cover_occupancy_sensor_hint: "Used by the “Room occupied” rule condition. With NOT it lets a rule, for example, only open when the room is free. Unavailable sensor: neither “occupied” nor “free” is met.",
    cover_occupancy_off_note: "Choose a sensor to tell when the room is occupied.",
    cover_occupancy_states: "States = room occupied",
    cover_occupancy_states_placeholder: "Present, on, home…",
    cover_occupancy_states_hint: "Click the states that mean “room occupied” (several allowed). A state missing from the list can be added.",
    cover_occupancy_default_note: "No state chosen: default states apply (on, home, Présent, occupied, detected).",
    cover_occupancy_reset: "Back to the default states",
    cond_time_between: "Time between",
    cond_time_after_sunrise: "Time after sunrise",
    cond_time_after_sunset: "Time after sunset",
    cond_time_before_sunrise: "Time before sunrise",
    cond_time_before_sunset: "Time before sunset",
    cond_state_is: "State is",
    cond_numeric_state: "Numeric value",
    cond_weather_is: "Weather is",
    cond_day_of_week: "Day of week",
    cond_workday: "Workday sensor",
    // Condition params
    param_elevation: "Elevation",
    param_temperature: "Temperature",
    param_start_time: "Start time",
    param_end_time: "End time",
    param_offset: "Offset (min)",
    param_entity_id: "Entity ID",
    param_entity_search: "Search name or entity ID…",
    param_state: "State",
    param_operator: "Comparison",
    param_value: "Value",
    param_hysteresis: "Hysteresis",
    opt_above: "above",
    opt_below: "below",
    param_weather: "Weather condition",
    param_mode: "Mode",
    param_days: "Days",
    param_select_type: "Select condition type",
    cond_preview_active: "applies",
    cond_preview_inactive: "doesn't apply",
    cond_preview_context: "context-dependent",
    day_mon: "Mon", day_tue: "Tue", day_wed: "Wed", day_thu: "Thu", day_fri: "Fri", day_sat: "Sat", day_sun: "Sun",
    opt_on: "On (workday)", opt_off: "Off (non-workday)",
    opt_cooling: "Hot (≥ hot setpoint)", opt_heating: "Cold (≤ cold setpoint)", opt_neutral: "Between the setpoints",
    // Scenarios
    scenario_add: "Add scenario",
    scenario_icon: "Icon",
    scenario_icon_custom: "Custom MDI icon",
    scenario_icon_custom_hint: "Enter any Material Design Icon name (e.g. mdi:lightbulb). See materialdesignicons.com for the full list.",
    scenario_no_rules: "No rules configured",
    // Settings
    settings_outdoor_temp: "Outdoor temperature sensor",
    settings_outdoor_temp_short: "Outdoor:",
    settings_outdoor_temp_hint: "Used for temperature-based rule conditions (temperature above/below).",
    settings_indoor_temp: "Indoor temperature sensor (global) (°C)",
    settings_indoor_temp_hint: "Used for covers without their own indoor sensor. Used by the setpoints and by “Sun on facade”.",
    settings_weather: "Weather entity",
    settings_weather_hint: "Used for weather-based rule conditions (e.g. only shade when sunny).",
    settings_comfort_min: "Cold temperature setpoint (°C)",
    settings_comfort_max: "Hot temperature setpoint (°C)",
    settings_comfort_hint: "Temperature range in which a room is considered comfortable. At or below the cold setpoint: cold room; at or above the hot setpoint: room too hot. Used by the “Room temperature” condition and by “Sun on facade” (Sun exposure tab).",
    settings_comfort_hysteresis: "Hysteresis – between the setpoints (°C)",
    settings_comfort_hysteresis_hint: "Prevents a room close to a setpoint from changing state with every reading: it only becomes comfortable again once it has moved away from the setpoint by this value.",
    settings_threshold_hysteresis: "Hysteresis – on outdoor temperature in rules (°C)",
    settings_threshold_hysteresis_hint: "Prevents an “outdoor temperature above/below” or “Outdoor air compared to the room” condition from flipping with every reading while the temperature stays close to the threshold. 0 = no hysteresis.",
    settings_house_rotation: "House rotation (degrees)",
    settings_house_rotation_hint: "Offset from true north (-180 to 180, positive = clockwise). Applied when selecting a facade direction; changing it rotates existing facades too. Drag the house in the compass, hold Shift to snap to 45°.",
    settings_house_rotation_reset: "Reset",
    settings_section_house: "House",
    settings_section_sensors: "Sensors",
    settings_outdoor_box_title: "Outdoor temperature",
    settings_outdoor_off_note: "Choose an outdoor temperature sensor to set the hysteresis.",
    settings_other_sensors_title: "Other sensors",
    settings_section_comfort: "Sun exposure",
    settings_section_automation: "Automation",
    settings_auto_box_pause: "Pause after a manual command",
    settings_auto_box_window: "Window positions",
    settings_auto_box_moves: "Movements",
    settings_auto_box_misc: "Logbook and updates",
    settings_pause_duration: "Default pause duration (min)",
    pause_resume_on_match: "Resume when the position matches the rule",
    pause_resume_on_match_hint: "Ends the pause after a manual move as soon as the cover is back at the position its rule asks for: put back by hand, or the rule changed and now wants the position it was left at. Checked once the cover is still, at least 1 min after the pause started. The pause duration stays the maximum.",
    settings_pause_duration_hint: "How long automation pauses after manual cover operation. Can be overridden per cover.",
    settings_lock_position: "Default lock position",
    settings_lock_position_hint: "Target position when window is open (100 = fully open). Can be overridden per cover.",
    settings_lock_tilt_position: "Default lock tilt",
    settings_lock_tilt_position_hint: "Tilt position when window is open. Leave empty to skip tilt control.",
    settings_vent_position: "Default vent position",
    settings_vent_position_hint: "Target position when window is tilted (e.g. 30 for ventilation gap). Can be overridden per cover.",
    settings_vent_tilt_position: "Default vent tilt",
    settings_vent_tilt_position_hint: "Tilt position when window is tilted. Leave empty to skip tilt control.",
    settings_min_position_change: "Default min. position change (%)",
    settings_min_position_change_hint: "Minimum position difference in percent to trigger a move. Can be overridden per cover.",
    settings_min_time: "Default min. time between changes (s)",
    settings_min_time_hint: "Minimum seconds between position changes (motor protection). Can be overridden per cover.",
    settings_command_stagger: "Command stagger delay (s)",
    settings_command_stagger_hint: "Delay in seconds between commands when multiple covers move simultaneously. Recommended 0.3-0.5 for radio-based systems (Z-Wave, Zigbee). 0 = no delay.",
    settings_logbook_enabled: "Write logbook entries",
    settings_logbook_enabled_hint: "Record cover movements, lock/unlock, pause/resume and wind protection in Home Assistant's logbook.",
    settings_update_check_enabled: "Check for updates",
    settings_update_check_enabled_hint: "When the panel opens, query the public GitHub API once for the latest release and show an update hint. Disable to prevent any outbound request to GitHub.",
    settings_current_value: "Current",
    settings_validation_min_max: "Min must be less than max",
    settings_workday_sensor: "Workday sensor",
    settings_workday_hint: "Binary sensor for workday detection (e.g. HA Workday integration). Used by the 'workday' condition type in rules.",
    settings_section_wind: "Wind protection",
    settings_wind_hint: "Safety feature: when the wind speed exceeds the threshold, all covers move to the wind protection position (100 = open, e.g. to protect awnings and slats; 0 = closed, e.g. to protect the windows). Deactivates when the speed drops below the threshold minus the hysteresis.",
    settings_wind_sensor: "Wind speed sensor",
    settings_wind_threshold: "Activation threshold",
    settings_wind_hysteresis: "Hysteresis – protection release",
    settings_wind_hysteresis_hint: "Protection is only released once the wind has dropped this much below the threshold.",
    hyst_title_comfort: "How does it work? – hysteresis between the setpoints",
    hyst_title_rules: "How does it work? – outdoor temperature hysteresis",
    hyst_title_solar: "How does it work? – sunshine hysteresis",
    hyst_title_wind: "How does it work? – wind hysteresis",
    hyst_with_values: "With your values",
    hyst_example: "Example",
    hyst_between: "between {a} and {b}",
    hyst_above: "above {a}",
    hyst_below: "below {a}",
    hyst_keep: "Keeps its previous state",
    hyst_comfort_intro: "{w}: setpoints {a} and {b} °C, hysteresis {h} °C.",
    hyst_col_room_temp: "Room temperature",
    hyst_col_state: "State",
    hyst_cold: "Cold",
    hyst_hot: "Hot",
    hyst_comfortable: "Comfortable",
    hyst_stay_cold: "Stays cold if it was, otherwise comfortable",
    hyst_stay_hot: "Stays hot if it was, otherwise comfortable",
    hyst_comfort_so1: "Hysteresis does not move the setpoints: the room becomes cold at {a} °C and hot at {b} °C.",
    hyst_comfort_so2: "It only acts on the way back: a cold room must warm up to {ah} °C to be comfortable again, a hot room must cool down to {bh} °C.",
    hyst_comfort_so3: "Example: the room drops to {a} °C → cold. It rises to {mid} °C → still cold. At {ah} °C → comfortable. If it drops back to {mid} °C → it stays comfortable (it only becomes cold again at {a} °C).",
    hyst_comfort_so4: "Without hysteresis, a room hovering around a setpoint would change state with every reading, and the covers with it.",
    hyst_rules_intro: "Example (none of your rules has this condition yet): a condition “outdoor temperature above {t} °C”, hysteresis {h} °C.",
    hyst_rules_scope: "This hysteresis only applies to the “Outdoor temperature above / below” conditions (each with its own threshold) and “Outdoor air compared to the room” (on the outdoor – room difference) of your rules. It has no effect on the indoor temperature setpoints.",
    hyst_rules_intro_real: "Example from your rules: “{rule}” has the condition “outdoor temperature {op} {t} °C”, hysteresis {h} °C.",
    hyst_op_above: "above",
    hyst_op_below: "below",
    hyst_rules_so1_below: "The threshold entered in the rule is the middle of the band: the condition becomes true below {tl} °C and only becomes false again above {th} °C.",
    hyst_rules_so2_below: "For “above” it is the other way round: true above {th} °C, false again below {tl} °C.",
    hyst_rules_so3_below: "For it to become true below {t} °C, enter {th} °C in the rule.",
    hyst_col_temp: "Temperature",
    hyst_col_condition: "Condition",
    hyst_true: "True",
    hyst_false: "False",
    hyst_rules_so1: "The threshold entered in the rule is the middle of the band: the condition becomes true above {th} °C and only becomes false again below {tl} °C.",
    hyst_rules_so2: "For “below” it is the other way round: true below {tl} °C, false again above {th} °C.",
    hyst_rules_so3: "For it to become true above {t} °C, enter {tl} °C in the rule.",
    hyst_zero: "With 0 there is no hysteresis: the state changes exactly at the threshold, every time.",
    hyst_solar_intro: "{w}: threshold {t}, hysteresis {h}.",
    hyst_col_sensor: "Sunshine sensor",
    hyst_col_strong: "Strong sunshine",
    hyst_strong_yes: "Yes: the condition answers “sun”",
    hyst_strong_no: "No",
    hyst_solar_so1: "The threshold is the middle of the band: strong sunshine starts above {th} and only stops below {tl}. A passing cloud therefore does not reopen the covers.",
    hyst_solar_so2: "Only concerns covers set to “Only with strong sunshine”.",
    hyst_wind_intro: "{w}: threshold {t}, hysteresis {h}.",
    hyst_col_wind: "Wind",
    hyst_col_protection: "Protection",
    hyst_wind_on: "Active",
    hyst_wind_stay: "Stays active if it was, otherwise inactive",
    hyst_wind_off: "Released",
    hyst_wind_so1: "As for comfort, hysteresis only acts on the way back: protection activates at {t} and is only released once the wind has dropped to {tl}.",
    hyst_wind_so2: "A gust falling just below the threshold therefore does not move the covers back. A hysteresis greater than or equal to the threshold is ignored.",
    settings_wind_position: "Wind protection position",
    settings_wind_position_hint: "Position all covers move to while wind protection is active (0-100). 100 = open (protects awnings and slats), 0 = closed (protects the windows).",
    settings_section_solar: "Sunshine",
    settings_solar_hint: "Sensor measuring sunshine (light in lux, solar production in W, irradiance in W/m²). Above its threshold, the option “Only with strong sunshine” closes the covers.",
    settings_solar_sensor: "Sunshine sensor",
    settings_solar_threshold: "Strong sunshine above",
    settings_solar_threshold_hint: "Above this threshold, the option “Only with strong sunshine” answers “sun”.",
    threshold_entity: "or entity",
    threshold_entity_hint: "If an entity is selected, its value is used; the number entered serves as a fallback if the entity is unavailable.",
    threshold_entity_current: "Current",
    threshold_entity_unavailable: "unavailable, the number entered is used",
    threshold_fallback: "Entity value. If it is unavailable: {v}",
    settings_solar_hysteresis: "Hysteresis – sunshine threshold",
    settings_solar_hysteresis_hint: "Prevents strong sunshine from flipping with every reading while the sensor stays close to the threshold. 0 = no hysteresis.",
    settings_solar_short: "Solar:",
    settings_sun_facade_title: "Sun on facade – depending on indoor temperature",
    status_auto: "Auto",
    status_paused: "Paused",
    status_manual: "Manual",
    status_locked: "Locked",
    status_venting: "Venting",
    status_wind_protected: "Wind protected",
    weather_sunny: "Sunny",
    weather_cloudy: "Cloudy",
    weather_partlycloudy: "Partly cloudy",
    weather_rainy: "Rainy",
    weather_pouring: "Heavy rain",
    weather_snowy: "Snowy",
    weather_snowy_rainy: "Sleet",
    weather_windy: "Windy",
    weather_windy_variant: "Windy & cloudy",
    weather_fog: "Foggy",
    weather_hail: "Hail",
    weather_lightning: "Lightning",
    weather_lightning_rainy: "Thunderstorm",
    weather_exceptional: "Severe weather",
    weather_clear_night: "Clear night",
    weather_unknown: "Unknown",
    info_sun_title: "Sun position (azimuth / elevation)",
    info_outdoor_title: "Outdoor temperature",
    info_solar_title: "Solar intensity",
    info_solar_exceeded_title: "Strong sunshine: threshold exceeded",
    rule_active_for: "Active for",
    rule_covers_count: "cover(s)",
    rule_inactive: "Not matching",
    master_enabled: "Automation",
    master_enabled_hint: "Lock and vent protection as well as safety rules remain active even when automation is disabled.",
    log_time: "Time",
    log_event: "Event",
    log_cover: "Cover",
    cover_show_log: "Show this cover's log",
    log_message: "Details",
    log_type_position: "Position",
    log_type_status: "Status",
    log_type_rule: "Rule",
    log_type_wind: "Wind",
    log_loading: "Loading log...",
    log_empty: "No log entries in the last 3 days.",
    log_filter_all: "All",
    log_filter_cover: "Cover:",
    log_filter_all_covers: "All covers",
    log_filter_cover_note: "Global events (wind) are also shown.",
    log_clear: "Clear log",
    log_clear_confirm: "Delete all log entries?",
    log_clear_confirm_all: "Clear the whole log (all covers)?",
    settings_section_backup: "Backup",
    settings_backup_hint: "Export the complete configuration as a JSON file. Import replaces all settings, covers, facades, rules, and scenarios.",
    settings_export: "Export configuration",
    settings_import: "Import configuration",
    settings_import_confirm: "This will replace the entire configuration. Continue?",
    settings_import_success: "Configuration imported successfully.",
    settings_import_error: "Import failed",
    settings_export_error: "Export failed",
    settings_unsaved_confirm: "Discard unsaved settings changes?",
    settings_unsaved_warning: "Some settings were changed but not saved: they are not in the export.",
    settings_export_unsaved_confirm: "Some settings were changed but not saved. Save them before exporting?",
    settings_save_and_export: "Save and export",
  },
  de: {
    title: "CoverAutomatic",
    version_link_title: "Release Notes auf GitHub öffnen",
    update_badge_title: "Update verfügbar – Release Notes auf GitHub öffnen",
    tabs: { covers: "Behänge", facades: "Fassaden", rules: "Regeln", scenarios: "Szenarien", settings: "Einstellungen", log: "Protokoll" },
    nav_label: "Bereiche",
    loading: "Konfiguration wird geladen...",
    error_load: "Konfiguration konnte nicht geladen werden.",
    retry: "Erneut versuchen",
    saved: "Gespeichert",
    cond_time_after_dawn: "Zeit nach Morgendämmerung",
    cond_time_before_dawn: "Zeit vor Morgendämmerung",
    cond_time_after_dusk: "Zeit nach Abenddämmerung",
    cond_time_before_dusk: "Zeit vor Abenddämmerung",
    cond_time_after_dawn_hint: "Von der Morgendämmerung (+ Offset) bis zur Abenddämmerung. Gegenstück: „{other}“.",
    cond_time_before_dawn_hint: "Von der Abenddämmerung bis zur nächsten Morgendämmerung (+ Offset). Gegenstück: „{other}“.",
    cond_time_after_dusk_hint: "Von der Abenddämmerung (+ Offset) bis zur nächsten Morgendämmerung. Gegenstück: „{other}“.",
    cond_time_before_dusk_hint: "Von der Morgendämmerung bis zur Abenddämmerung (+ Offset). Gegenstück: „{other}“.",
    cond_time_after_sunrise_hint: "Vom Sonnenaufgang (+ Offset) bis zum Sonnenuntergang. Gegenstück: „{other}“.",
    cond_time_before_sunrise_hint: "Vom Sonnenuntergang bis zum nächsten Sonnenaufgang (+ Offset). Gegenstück: „{other}“.",
    cond_time_after_sunset_hint: "Vom Sonnenuntergang (+ Offset) bis zum nächsten Sonnenaufgang. Gegenstück: „{other}“.",
    cond_time_before_sunset_hint: "Vom Sonnenaufgang bis zum Sonnenuntergang (+ Offset). Gegenstück: „{other}“.",
    cover_travel_auto_default: "Standard: {s} s",
    cover_travel_not_measured: "Gemessen: noch nicht (bei der nächsten Fahrt von mindestens 20 %).",
    cover_travel_used: "Verwendet: {s} s ({src}) · Wartezeit vor Erkennung manueller Bedienung: {wait} s",
    cover_travel_used_none: "Verwendet: keine · Wartezeit vor Erkennung manueller Bedienung: {wait} s",
    cover_travel_src_manual: "eingegeben",
    cover_travel_src_measured: "gemessen",
    cover_travel_src_default: "globaler Standard",
    cover_travel_src_none: "keine",
    settings_default_travel_time: "Standard-Laufzeit (s)",
    settings_default_travel_time_placeholder: "keine (30 s Wartezeit)",
    settings_default_travel_time_hint: "Laufzeit für Behänge ohne eingegebenen und noch ohne gemessenen Wert. Reihenfolge: Wert am Behang, dann gemessener Wert, dann dieser Standard. Leer = 30 s Wartezeit.",
    cover_travel_time: "Laufzeit (s)",
    cover_travel_auto: "automatisch (wird bei den ersten Fahrten gemessen)",
    cover_travel_auto_measured: "automatisch: {s} s gemessen",
    cover_travel_measured: "Gemessen: {s} s für eine volle Fahrt.",
    cover_travel_reset: "Zurücksetzen",
    cover_travel_time_hint: "Dauer einer vollen Fahrt von 0 bis 100 %. Nach einem eigenen Befehl wartet die Integration so lange (plus 5 s, mindestens 30 s), bevor sie eine Positionsänderung als manuelle Bedienung wertet. Leer lassen, um den gemessenen Wert bzw. sonst die Standard-Laufzeit aus den Einstellungen zu verwenden.",
    scenario_rule_off: "in Regeln deaktiviert",
    scenario_rule_off_hint: "Diese Regel ist im Tab „Regeln“ ausgeschaltet und wird daher nie ausgeführt. Die Einstellung hier gilt wieder, sobald die Regel aktiviert ist.",
    ha_ctype_and: "und",
    ha_ctype_or: "oder",
    ha_ctype_not: "nicht",
    ha_ctype_template: "Template",
    ha_ctype_state: "Zustand",
    ha_ctype_numeric_state: "Zahlenwert",
    ha_ctype_zone: "Zone",
    ha_ctype_time: "Zeit",
    ha_ctype_sun: "Sonne",
    ha_ctype_device: "Gerät",
    ha_ctype_trigger: "Auslöser",
    cond_group_sun: "Sonne",
    cond_group_temperature: "Temperatur",
    cond_group_time: "Zeit",
    cond_group_weather: "Wetter",
    cond_group_entities: "Entitäten",
    cond_menu_ha_state: "Zustand einer Entität",
    cond_menu_ha_numeric: "Zahlenwert einer Entität",
    cond_menu_ha_yaml: "Home-Assistant-Bedingung (YAML)",
    cond_ha_condition: "Home-Assistant-Bedingung",
    cond_ha_state: "Zustand einer Entität",
    cond_ha_numeric: "Zahlenwert einer Entität",
    ha_tab_form: "Formular",
    ha_tab_yaml: "YAML",
    ha_kind: "Typ",
    ha_kind_state: "Zustand",
    ha_kind_numeric: "Zahlenwert",
    ha_entity: "Entität",
    ha_current: "aktuell",
    ha_attribute: "Attribut",
    ha_attribute_none: "— Zustand der Entität —",
    ha_compare: "Vergleich",
    ha_is: "ist",
    ha_is_not: "ist nicht",
    ha_for: "Seit mindestens (min)",
    ha_for_negate_hint: "Mit „ist nicht“ nicht verfügbar.",
    ha_states: "Zustände",
    ha_state_other: "Anderer Wert…",
    ha_state_add: "Hinzufügen",
    ha_operator: "Operator",
    ha_op_above: "über",
    ha_op_below: "unter",
    ha_op_between: "zwischen",
    ha_value: "Wert",
    ha_min: "Minimum",
    ha_max: "Maximum",
    ha_form_unsupported: "Diese Bedingung kann nicht als Formular angezeigt werden (Template, Zone, verschachtelte Bedingungen…). Sie bleibt in YAML bearbeitbar.",
    ha_yaml_label: "Bedingung",
    ha_yaml_placeholder: "condition: state\nentity_id: person.ich\nstate: not_home\nfor: \"00:15:00\"",
    ha_yaml_help: "Gleiches Format wie der Abschnitt „condition“ einer Home-Assistant-Automatisierung. Eine Liste von Bedingungen wird mit UND verknüpft.",
    ha_valid: "Bedingung gültig",
    ha_entities: "Überwachte Entitäten",
    ha_unknown_entities: "Entitäten nicht gefunden (ID prüfen)",
    ha_err_yaml: "YAML-Syntaxfehler in Zeile {line}, Spalte {column}",
    ha_err_not_mapping: "Das YAML muss eine Bedingung beschreiben (z. B. „condition: state“).",
    ha_err_invalid: "Ungültige Bedingung",
    ha_err_empty: "Leere Bedingung",
    ha_checking: "Wird geprüft…",
    ha_incomplete_entity: "Wähle eine Entität.",
    ha_incomplete_states: "Wähle mindestens einen Zustand.",
    ha_incomplete_value: "Gib einen Wert ein.",
    cond_convert: "In erweiterte Bedingung umwandeln",
    cond_convert_hint: "Ergänzt Attribut, „ist nicht“, Dauer und Zustandsauswahl. Wird beim Speichern der Regel übernommen.",
    ha_chip_is: "{entity} ist {states}",
    ha_chip_is_not: "{entity} ist nicht {states}",
    ha_chip_for: " seit {min} min",
    ha_chip_or: " oder ",
    ha_chip_above: "{entity} > {value}",
    ha_chip_below: "{entity} < {value}",
    ha_chip_between: "{entity} zwischen {min} und {max}",
    ha_chip_other: "HA-Bedingung: {type}",
    rule_op_short_and: "UND", rule_op_short_or: "ODER",
    compass_n: "N", compass_e: "O", compass_s: "S", compass_w: "W",
    error_generic: "Die Änderung konnte nicht gespeichert werden",
    error_not_found: "Element nicht gefunden (evtl. zwischenzeitlich gelöscht)",
    error_invalid_format: "Ungültiger Wert",
    error_invalid_conditions: "Ungültige Regelbedingung",
    error_invalid_data: "Ungültige Konfigurationsdaten",
    error_too_large: "Importdatei ist zu groß",
    error_unauthorized: "Administratorrechte erforderlich",
    error_invalid_comfort_range: "Der Kalt-Sollwert muss unter dem Warm-Sollwert liegen",
    error_invalid_wind_hysteresis: "Die Wind-Hysterese muss kleiner als der Windschwellwert sein",
    rule_priority_up: "Priorität erhöhen",
    rule_priority_down: "Priorität senken",
    rule_enabled_aria: "Regel {name} aktiv",
    rule_invalid_fields: "Rot markierte Felder korrigieren (leerer oder ungültiger Wert), dann speichern",
    ha_err_request: "Prüfung fehlgeschlagen",
    error_not_loaded: "CoverAutomatic ist nicht geladen (Integration neu laden oder Home Assistant neu starten)",
    error_invalid_solar_hysteresis: "Die Sonnenschein-Hysterese muss kleiner als die Sonnenscheinschwelle sein",
    error_invalid_value: "Ungültige Zahl",
    drag_handle: "Zum Sortieren ziehen",
    settings_nav_label: "Einstellungen",
    import_invalid_json: "Ungültiges JSON",
    status_unlocked: "Entsperrt",
    log_msg_wind_activated: "Aktiviert ({speed} ≥ {threshold})",
    log_msg_wind_deactivated: "Deaktiviert ({speed} ≤ {threshold})",
    log_msg_wind_disabled: "Deaktiviert (in den Einstellungen ausgeschaltet)",
    log_msg_status_change: "{from} → {to}",
    log_msg_rule: "{rule} → {position} %",
    log_msg_position: "{from} % → {to} %",
    log_msg_safety_takeover: "Sicherheitsregel {rule} übernimmt ({status}) → {position} %",
    log_msg_safety_release: "Sicherheitsregel {rule} beendet ({status})",
    log_msg_sensor_unavailable: "{status} beibehalten: Sensor {sensor} nicht verfügbar",
    log_msg_lock_sensor_missing: "Fenstersensor {sensor} nicht gefunden: ignoriert",
    log_msg_move_blocked_window_unknown: "Fahrt auf {position} % zurückgehalten: Fensterzustand unbekannt ({sensor})",
    log_msg_wind_restore_dropped: "Wiederherstellung des Windschutzes verworfen: Sensor {sensor} fehlt oder ohne Wert",
    save: "Speichern",
    cancel: "Abbrechen",
    delete: "Löschen",
    rule_duplicate: "Duplizieren (die Kopie wird direkt darunter erstellt)",
    rule_copy_suffix: "Kopie",
    settings_wind_off_note: "Wählen Sie einen Windsensor, um den Windschutz zu aktivieren.",
    settings_solar_off_note: "Wählen Sie einen Sensor, um Schwelle und Hysterese einzustellen.",
    settings_solar_nested_off: "Nur von der Option „Nur bei starkem Sonnenschein“ verwendet (hier oder bei einem Behang).",
    cover_lock_box_title: "Fenster offen",
    cover_lock_off_note: "Wählen Sie einen Fenstersensor, um diese Einstellungen zu aktivieren.",
    cover_vent_box_title: "Fenster gekippt (Lüftung)",
    cover_vent_off_note: "Wählen Sie einen Kippsensor, um die Lüftungsposition einzustellen.",
    confirm_delete: "Wirklich löschen?",
    add: "Hinzufügen",
    edit: "Bearbeiten",
    close: "Schließen",
    none: "Keine",
    enabled: "Aktiviert",
    active: "Aktiv",
    activate: "Aktivieren",
    name: "Name",
    cover_facade: "Fassade",
    cover_facade_hint: "Bestimmt, welche Fassadenregeln für diesen Behang gelten.",
    cover_status: "Status",
    cover_pause_duration: "Pausendauer (Min.)",
    cover_pause_duration_hint: "Wie lange die Automatik nach manueller Bedienung pausiert. Leer = globaler Standard.",
    cover_indoor_temp: "Innentemperatur-Sensor (°C)",
    cover_indoor_temp_hint: "Sensor des Raums dieses Behangs, für die Sollwerte und „Sonne auf Fassade“. Ersetzt den globalen Sensor.",
    cover_lock_sensor: "Sensor Fenster offen",
    cover_lock_sensor_hint: "Fensterkontakt. Bei geöffnetem Fenster fährt der Behang auf Sperrposition (Sicherheit).",
    cover_lock_hold: "Aktuelle Position beim Öffnen des Fensters halten",
    cover_lock_hold_hint: "Ein: Der Behang bleibt bei geöffnetem Fenster, wo er ist (gesperrt, kein Befehl). Aus: Er fährt auf die Sperrposition unten (nur nach oben, nie weiter zu).",
    cover_lock_position: "Sperrposition",
    cover_lock_position_hint: "Zielposition bei geöffnetem Fenster. Leer = globaler Standard.",
    cover_vent_sensor: "Sensor Fenster gekippt",
    cover_vent_sensor_hint: "Kippkontakt. Bei gekipptem Fenster fährt der Behang auf Lüftungsposition.",
    cover_vent_position: "Lüftungsposition",
    cover_vent_position_hint: "Zielposition bei gekipptem Fenster. Leer = globaler Standard.",
    cover_comfort_min: "Temperatursollwert kalt (°C)",
    cover_comfort_max: "Temperatursollwert warm (°C)",
    cover_comfort_hint: "Sollwerte für diesen Raum. Leer = globale Werte aus den Einstellungen.",
    cover_comfort_global: "Leer = globaler Wert: {v} °C ({src})",
    cover_default_note: "Leer = Standardwert: {v} (Einstellungen)",
    unit_sensor: "Sensoreinheit",
    cover_comfort_src_settings: "Einstellungen",
    cover_sun_switches_hint: "Einstellungen nur für diesen Behang; „Global“ = Wert aus Einstellungen › Sonnenexposition.",
    tristate_global: "Global ({value})",
    settings_sun_facade_hint: "Diese Einstellungen ändern nur die Antwort der Bedingung „Sonne auf Fassade“, für Behänge mit Innentemperatursensor (eigener oder globaler). Sie dienen Regeln, die bei Sonne schließen: nur schließen, wenn es nützt. Alles aus lassen, wenn eine Regel die Behänge bei Sonne öffnet.",
    sun_heating_label: "Aktion beim Kalt-Sollwert: Sonne wärmen lassen",
    sun_heating_hint: "Die Bedingung meldet „keine Sonne“: Regeln, die bei Sonne schließen, schließen nicht und die Sonne wärmt den Raum. Vermeiden, wenn eine Regel die Behänge bei Sonne öffnet (sie würde nicht mehr greifen).",
    sun_below: "≤ {t} °C",
    sun_above: "≥ {t} °C",
    sun_between: "zwischen {min} und {max} °C",
    settings_comfort_range_title: "Innentemperatur-Sollwerte",
    settings_indoor_reminder: "Gilt je nach Innentemperatur jedes Raums (Reiter Sensoren: globaler Sensor {name}, Sollwerte {min} und {max} °C). Ein Behang kann eigenen Sensor und eigene Sollwerte haben.",
    settings_indoor_none: "nicht festgelegt",
    sun_explain_title: "Wie funktioniert das?",
    sun_explain_intro: "Beispiel: eine Regel „schließen bei Sonne“ und Sonne auf der Fassade. Hervorgehobene Zeilen entsprechen Ihren Einstellungen.",
    sun_explain_col_room: "Raum",
    sun_explain_col_answer: "Antwort von „Sonne auf Fassade“",
    sun_explain_col_effect: "Wirkung",
    sun_explain_room_cold_on: "Kalt, „Sonne wärmen lassen“ aktiviert",
    sun_explain_room_cold_off: "Kalt, Kästchen deaktiviert",
    sun_explain_room_position: "Angenehm, „Sobald die Sonne auf der Fassade steht“",
    sun_explain_room_ignore: "Angenehm, „Nie“",
    sun_explain_room_preemptive: "Angenehm, „Nur bei starkem Sonnenschein“",
    sun_explain_room_hot: "Zu warm",
    sun_explain_sun: "„Sonne“",
    sun_explain_no_sun: "„keine Sonne“",
    sun_explain_sun_always: "immer „Sonne“",
    sun_explain_sun_if_strong: "„Sonne“, wenn der Sensor die Schwelle überschreitet, sonst „keine Sonne“",
    sun_explain_eff_warm: "Schließt nicht: der Behang bleibt offen und der Raum erwärmt sich.",
    sun_explain_eff_close: "Schließt.",
    sun_explain_eff_close_as_hot: "Schließt, als wäre der Raum warm.",
    sun_explain_eff_wait: "Schließt nicht; schließt, sobald der Raum zu warm wird.",
    sun_explain_eff_strong: "Schließt nur bei starkem Sonnenschein, bevor der Raum warm wird.",
    sun_explain_so: "Also",
    sun_explain_cold: "Kalter Raum: das Kästchen öffnet den Behang nicht, es verhindert das Schließen wegen der Sonne. Ist der Behang bereits offen (z. B. durch eine Öffnungsregel am Tag), bleibt er offen.",
    sun_explain_hot: "Zu warmer Raum: der Behang schließt nur, wenn eine Regel „schließen bei Sonne“ für diesen Behang und das aktive Szenario gilt.",
    sun_explain_comfort: "Angenehmer Raum: der Zwischenbereich, in dem Sie wählen, wann die Sonne zählt.",
    sun_comfort_label: "Aktion zwischen den Sollwerten: Verhalten je nach Sonne",
    sun_comfort_position: "Sobald die Sonne auf der Fassade steht",
    sun_comfort_position_hint: "Die Bedingung ist wahr, sobald die Sonne auf der Fassade steht.",
    sun_comfort_ignore: "Nie (warten, bis der Raum zu warm wird)",
    sun_comfort_ignore_hint: "Meldet „keine Sonne“: der Behang schließt erst, wenn der Raum zu warm wird.",
    sun_comfort_preemptive: "Nur bei starkem Sonnenschein",
    sun_comfort_preemptive_hint: "Meldet „Sonne“, sobald der Sonnenscheinsensor seine Schwelle überschreitet: der Behang schließt, bevor der Raum warm wird.",
    sun_comfort_hint: "Verhalten von „Sonne auf Fassade“, solange der Raum zwischen den Sollwerten liegt. Global = Wert aus Einstellungen › Sonnenexposition.",
    sun_hot_note: "Raum zu warm (≥ {t} °C): die Sonne zählt immer, sobald sie auf der Fassade steht.",
    solar_used_by: "Verwendet von der Option „Nur bei starkem Sonnenschein“: {n} Behang/Behänge.",
    solar_unused: "Nur von der Option „Nur bei starkem Sonnenschein“ verwendet (derzeit kein Behang).",
    tristate_on: "Aktiviert",
    tristate_off: "Deaktiviert",
    cover_inverted: "Öffnungs-/Schließrichtung umkehren",
    cover_inverted_hint: "Aktivieren, wenn 100 % geschlossen bedeutet (umgekehrte Motorrichtung).",
    cover_lock_tilt: "Sperr-Neigung",
    cover_vent_tilt: "Lüftungs-Neigung",
    cover_inverted_tilt: "Umgekehrte Neigung",
    cover_min_pos_change: "Min. Positionsänderung (%)",
    cover_min_pos_change_hint: "Mindestabweichung für eine Fahrt. Leer = globaler Standard.",
    cover_min_time: "Min. Zeit zwischen Änderungen (s)",
    cover_min_time_hint: "Mindestabstand in Sekunden zwischen Positionsänderungen. Leer = globaler Standard.",
    cover_section_base: "Allgemein",
    cover_section_sensors: "Sensoren",
    cover_section_advanced: "Erweitert",
    cover_section_tilt: "Neigung",
    cover_section_window: "Fenster",
    cover_section_automation: "Automatisierung",
    cover_section_room: "Raum",
    cover_inverted_short: "Umgekehrt",
    cover_lock_hold_short: "Position halten",
    sun_heating_label_short: "Kalt: wärmen lassen",
    sun_comfort_label_short: "Zwischen den Sollwerten",
    settings_comfort_min_short: "Sollwert kalt (°C)",
    settings_comfort_max_short: "Sollwert warm (°C)",
    cover_comfort_min_short: "Sollwert kalt (°C)",
    cover_comfort_max_short: "Sollwert warm (°C)",
    settings_indoor_temp_short: "Innensensor (°C)",
    cover_indoor_temp_short: "Innensensor (°C)",
    settings_comfort_hysteresis_short: "Hysterese Sollwerte (°C)",
    settings_threshold_hysteresis_short: "Hysterese außen (°C)",
    settings_solar_hysteresis_short: "Hysterese Sonnenschein",
    settings_wind_hysteresis_short: "Hysterese Wind",
    settings_solar_threshold_short: "Schwelle starker Sonnenschein",
    settings_sun_facade_title_short: "Sonne auf Fassade",
    cover_min_time_short: "Min. Verzögerung (s)",
    cover_min_pos_change_short: "Min. Änderung (%)",
    cover_expand_all: "Alle aufklappen",
    cover_collapse_all: "Alle zuklappen",
    cover_sum_auto_on: "Automatisch",
    cover_sum_auto_off: "Automatisierung aus",
    cover_sum_no_facade: "keine Fassade",
    cover_sum_open: "Offen: {v}",
    cover_sum_hold: "Position halten",
    cover_sum_tilted: "Gekippt: {v}",
    cover_sum_no_window: "Kein Fenstersensor",
    cover_sum_pause: "Pause {n} min",
    cover_sum_travel: "Laufzeit {n} s",
    cover_sum_own: "{n} eigene Einstellung(en)",
    cover_sum_all_global: "Standardwerte",
    cover_sum_global: "global",
    cover_sum_no_indoor: "Kein Innensensor",
    cover_sum_sun_heat_on: "Kalt: Sonne wärmen lassen",
    cover_sum_sun_heat_off: "Kalt: Sonne zählt",
    cover_sum_sun_between: "Dazwischen: {v}",
    cover_sum_mode_position: "sobald die Sonne da ist",
    cover_sum_mode_ignore: "nie",
    cover_sum_mode_preemptive: "starker Sonnenschein",
    cover_auto_enabled: "Automatik aktiviert",
    cover_temp: "Temp",
    cover_current_pos: "Ist",
    cover_target_pos: "Soll",
    cover_position: "Position",
    cover_position_target_label: "Soll",
    cover_position_inverted_tip: "Invertierter Behang: HA meldet {raw} % (hier in der Skala der Regeln angezeigt)",
    cover_hysteresis_position: "Positionsänderung zu gering",
    cover_hysteresis_time: "Zu kurz seit letzter Änderung",
    cover_rule: "Regel",
    cover_no_rule: "–",
    cover_resume: "Fortsetzen",
    cover_goto_rule: "Regel öffnen",
    cover_remove: "Behang entfernen",
    cover_last_change: "Letzte Änderung",
    cover_just_now: "gerade eben",
    time_ago_min: "vor {n} Min.",
    time_ago_h: "vor {n} Std.",
    time_ago_h_m: "vor {h} Std. {m} Min.",
    show_hint: "Hilfe anzeigen",
    settings_temp_color: "Farben der Raumtemperatur (Behangliste)",
    settings_temp_color_action: "Nach nötiger Aktion",
    settings_temp_color_action_hint: "Kalter Raum rot (heizen), warmer Raum blau (kühlen).",
    settings_temp_color_thermometer: "Nach Temperatur",
    settings_temp_color_thermometer_hint: "Kalter Raum blau, warmer Raum rot, wie ein Thermometer.",
    comfort_cooling: "Warm – kühlen",
    comfort_heating: "Kalt – heizen",
    comfort_neutral: "Komfort",
    cover_add: "Behänge hinzufügen",
    facade_direction: "Richtung",
    facade_direction_hint: "Setzt Azimutwerte mit Hausrotation automatisch.",
    facade_azimuth_start: "Azimut Start",
    facade_azimuth_end: "Azimut Ende",
    facade_azimuth_hint: "Echte Kompasspeilungen, an denen die Sonne die Fassade erreicht/verlässt. Start = Ende: voller Kreis.",
    facade_min_elevation: "Min. Elevation",
    facade_min_elevation_hint: "Minimale Sonnenhöhe, damit diese Fassade als besonnt gilt. Werte unter 0 gelten als 0.",
    facade_covers: "Zugewiesene Behänge",
    facade_add: "Fassade hinzufügen",
    facade_no_covers: "Keine Behänge zugewiesen",
    facade_sun_active: "Sonne auf Fassade",
    facade_dir_north: "Norden",
    facade_dir_east: "Osten",
    facade_dir_south: "Süden",
    facade_dir_west: "Westen",
    rule_priority: "Priorität",
    rule_target_pos: "Zielposition",
    rule_target_pos_hint: "Position bei Regelübereinstimmung (0 = geschlossen, 100 = offen).",
    rule_target_tilt: "Ziel-Neigung",
    rule_operator: "Bedingungsoperator",
    rule_operator_hint: "UND = alle Bedingungen müssen zutreffen. ODER = eine reicht.",
    rule_operator_and: "UND (alle müssen zutreffen)",
    rule_operator_or: "ODER (eine muss zutreffen)",
    rule_conditions: "Bedingungen",
    rule_scenarios: "Szenarien",
    rule_scenarios_hint: "Szenarien, in denen diese Regel gilt. In jedem Szenario kann sie im Tab „Szenarien“ weiterhin vorübergehend ausgeschaltet werden.",
    rule_safety: "Sicherheitsregel",
    rule_safety_hint: "Wirkt auch während der Pause nach manueller Bedienung, im manuellen Modus des Behangs, bei Windschutz und bei deaktivierter Automatik. Setzt die Sperre (Fenster offen) nicht außer Kraft. Zwischen Regeln entscheidet die Priorität: oben in der Liste platzieren. Nur für Notfälle verwenden, z. B. den Feueralarm.",
    rule_safety_badge: "Sicherheit",
    scenario_no_member_rules: "Diesem Szenario ist keine Regel zugeordnet (im Regeleditor auswählen).",
    rule_groups_operator: "Gruppen verknüpft mit",
    rule_groups_hint: "UND = alle Gruppen müssen zutreffen. ODER = eine Gruppe reicht. Innerhalb einer Gruppe gilt ihr eigener Operator.",
    rule_group: "Gruppe",
    rule_group_joined_by: "Bedingungen verknüpft mit",
    rule_group_add: "Gruppe hinzufügen",
    rule_group_add_hint: "Gruppen erlauben z. B. (A ODER B) UND (C ODER D) oder (A UND B) ODER (C UND D).",
    rule_group_delete: "Gruppe und ihre Bedingungen löschen",
    rule_group_delete_confirm: "Diese Gruppe und ihre Bedingungen löschen?",
    rule_unsaved_confirm: "Ungespeicherte Änderungen an dieser Regel verwerfen?",
    discard: "Verwerfen",
    input_invalid_range: "Ganze Zahl zwischen {min} und {max} eingeben",
    input_not_integer: "Ganze Zahl eingeben",
    input_invalid_number: "Gültige Zahl eingeben",
    rule_group_empty: "Noch keine Bedingung in dieser Gruppe (leere Gruppen werden ignoriert).",
    rule_cond_move: "In andere Gruppe verschieben",
    rule_cond_up: "Nach oben",
    rule_cond_down: "Nach unten",
    rule_group_up: "Gruppe nach oben",
    rule_group_down: "Gruppe nach unten",
    rule_cond_not: "NICHT",
    rule_cond_not_hint: "Bedingung umkehren (NICHT). Ist ihr Sensor nicht verfügbar, gilt sie als nicht erfüllt.",
    rule_groups_count: "{n} Gruppen",
    cond_collapse: "Einklappen",
    cond_expand: "Ausklappen",
    cond_collapse_all: "Alle einklappen",
    cond_expand_all: "Alle ausklappen",
    rule_facades: "Fassaden",
    rule_covers: "Behänge",
    rule_assignment_hint: "Regel auf bestimmte Fassaden/Behänge beschränken. Leer = gilt für alle.",
    rule_add: "Regel hinzufügen",
    rule_duplicate: "Duplizieren",
    rule_copy_suffix: "(Kopie)",
    rule_add_condition: "Bedingung hinzufügen",
    rule_no_conditions: "Keine Bedingungen",
    rule_reorder_hint: "Ziehen oder ▲▼ zum Sortieren. Obere Regel gewinnt bei Überschneidung.",
    cond_sun_on_facade: "Sonne auf Fassade",
    cond_sun_elevation_above: "Sonnenhöhe über",
    cond_sun_elevation_below: "Sonnenhöhe unter",
    cond_temperature_above: "Außentemperatur über",
    cond_temperature_below: "Außentemperatur unter",
    cond_temperature_comfort: "Raumtemperatur",
    cond_outdoor_vs_indoor: "Außenluft im Vergleich zum Raum",
    cond_room_occupied: "Raum belegt",
    cond_group_presence: "Anwesenheit",
    opt_cooler: "kühler als der Raum",
    opt_warmer: "wärmer als der Raum",
    param_delta: "Mindestdifferenz (°C)",
    cover_occupancy_box_title: "Raumbelegung",
    cover_occupancy_sensor: "Belegungssensor",
    cover_occupancy_sensor_hint: "Wird von der Regelbedingung „Raum belegt“ verwendet. Mit NICHT kann eine Regel z. B. nur öffnen, wenn der Raum frei ist. Sensor nicht verfügbar: weder „belegt“ noch „frei“ ist erfüllt.",
    cover_occupancy_off_note: "Wählen Sie einen Sensor, der angibt, wann der Raum belegt ist.",
    cover_occupancy_states: "Zustände = Raum belegt",
    cover_occupancy_states_placeholder: "Präsent, on, home…",
    cover_occupancy_states_hint: "Klicken Sie auf die Zustände, die „Raum belegt“ bedeuten (mehrere möglich). Ein fehlender Zustand kann hinzugefügt werden.",
    cover_occupancy_default_note: "Kein Zustand gewählt: Standardzustände gelten (on, home, Présent, occupied, detected).",
    cover_occupancy_reset: "Zurück zu den Standardzuständen",
    cond_time_between: "Zeit zwischen",
    cond_time_after_sunrise: "Zeit nach Sonnenaufgang",
    cond_time_after_sunset: "Zeit nach Sonnenuntergang",
    cond_time_before_sunrise: "Zeit vor Sonnenaufgang",
    cond_time_before_sunset: "Zeit vor Sonnenuntergang",
    cond_state_is: "Status ist",
    cond_numeric_state: "Zahlenwert",
    cond_weather_is: "Wetter ist",
    cond_day_of_week: "Wochentag",
    cond_workday: "Arbeitstag-Sensor",
    param_elevation: "Sonnenhöhe",
    param_temperature: "Temperatur",
    param_start_time: "Startzeit",
    param_end_time: "Endzeit",
    param_offset: "Offset (Min.)",
    param_entity_id: "Entity-ID",
    param_entity_search: "Name oder Entity-ID suchen…",
    param_state: "Status",
    param_operator: "Vergleich",
    param_value: "Wert",
    param_hysteresis: "Hysterese",
    opt_above: "über",
    opt_below: "unter",
    param_weather: "Wetterbedingung",
    param_mode: "Modus",
    param_days: "Tage",
    param_select_type: "Bedingungstyp wählen",
    cond_preview_active: "greift",
    cond_preview_inactive: "greift nicht",
    cond_preview_context: "kontextabhängig",
    day_mon: "Mo", day_tue: "Di", day_wed: "Mi", day_thu: "Do", day_fri: "Fr", day_sat: "Sa", day_sun: "So",
    opt_on: "An (Arbeitstag)", opt_off: "Aus (kein Arbeitstag)",
    opt_cooling: "Warm (≥ Warm-Sollwert)", opt_heating: "Kalt (≤ Kalt-Sollwert)", opt_neutral: "Zwischen den Sollwerten",
    scenario_add: "Szenario hinzufügen",
    scenario_icon: "Symbol",
    scenario_icon_custom: "Eigenes MDI-Icon",
    scenario_icon_custom_hint: "Beliebigen Material-Design-Icon-Namen eingeben (z. B. mdi:lightbulb). Vollständige Liste auf materialdesignicons.com.",
    scenario_no_rules: "Keine Regeln konfiguriert",
    settings_outdoor_temp: "Außentemperatur-Sensor",
    settings_outdoor_temp_short: "Außen:",
    settings_outdoor_temp_hint: "Wird für temperaturbasierte Regelbedingungen verwendet (Außentemperatur über/unter).",
    settings_indoor_temp: "Innentemperatur-Sensor (global) (°C)",
    settings_indoor_temp_hint: "Für Behänge ohne eigenen Innensensor. Wird von den Sollwerten und von „Sonne auf Fassade“ verwendet.",
    settings_weather: "Wetter-Entität",
    settings_weather_hint: "Wird für wetterbasierte Regelbedingungen verwendet (z. B. nur beschatten bei Sonne).",
    settings_comfort_min: "Temperatursollwert kalt (°C)",
    settings_comfort_max: "Temperatursollwert warm (°C)",
    settings_comfort_hint: "Temperaturbereich, in dem ein Raum als angenehm gilt. Bis zum Kalt-Sollwert: kalter Raum; ab dem Warm-Sollwert: zu warmer Raum. Verwendet von der Bedingung „Raumtemperatur“ und von „Sonne auf Fassade“ (Reiter Sonnenexposition).",
    settings_comfort_hysteresis: "Hysterese – zwischen den Sollwerten (°C)",
    settings_comfort_hysteresis_hint: "Verhindert, dass ein Raum nahe einem Sollwert bei jedem Messwert den Zustand wechselt: er wird erst wieder angenehm, wenn er sich um diesen Wert vom Sollwert entfernt hat.",
    settings_threshold_hysteresis: "Hysterese – Außentemperatur in Regeln (°C)",
    settings_threshold_hysteresis_hint: "Verhindert, dass eine Bedingung „Außentemperatur über/unter“ oder „Außenluft im Vergleich zum Raum“ bei jedem Messwert kippt, solange die Temperatur nahe der Schwelle bleibt. 0 = keine Hysterese.",
    settings_house_rotation: "Hausrotation (Grad)",
    settings_house_rotation_hint: "Abweichung von exakt Nord (-180 bis 180, positiv = im Uhrzeigersinn). Wird bei der Fassaden-Richtungswahl angewendet; eine Änderung dreht bestehende Fassaden mit. Haus im Kompass ziehen, mit Shift auf 45° einrasten.",
    settings_house_rotation_reset: "Zurücksetzen",
    settings_section_house: "Haus",
    settings_section_sensors: "Sensoren",
    settings_outdoor_box_title: "Außentemperatur",
    settings_outdoor_off_note: "Wählen Sie einen Außentemperatursensor, um die Hysterese einzustellen.",
    settings_other_sensors_title: "Weitere Sensoren",
    settings_section_comfort: "Sonnenexposition",
    settings_section_automation: "Automatik",
    settings_auto_box_pause: "Pause nach manuellem Befehl",
    settings_auto_box_window: "Fensterpositionen",
    settings_auto_box_moves: "Bewegungen",
    settings_auto_box_misc: "Logbuch und Updates",
    settings_pause_duration: "Standard-Pausendauer (Min.)",
    pause_resume_on_match: "Fortsetzen, wenn die Position der Regel entspricht",
    pause_resume_on_match_hint: "Beendet die Pause nach manueller Bedienung, sobald der Behang wieder an der Position steht, die seine Regel verlangt: von Hand zurückgestellt oder die Regel hat gewechselt und verlangt nun diese Position. Geprüft, wenn der Behang stillsteht, frühestens 1 Min. nach Beginn der Pause. Die Pausendauer bleibt das Maximum.",
    settings_pause_duration_hint: "Wie lange die Automatik nach manueller Bedienung pausiert. Kann pro Behang überschrieben werden.",
    settings_lock_position: "Standard-Sperrposition",
    settings_lock_position_hint: "Zielposition bei geöffnetem Fenster (100 = offen). Kann pro Behang überschrieben werden.",
    settings_lock_tilt_position: "Standard-Sperr-Lamelle",
    settings_lock_tilt_position_hint: "Lamellenposition bei geöffnetem Fenster. Leer lassen = keine Lamellensteuerung.",
    settings_vent_position: "Standard-Lüftungsposition",
    settings_vent_position_hint: "Zielposition bei gekipptem Fenster (z. B. 30). Kann pro Behang überschrieben werden.",
    settings_vent_tilt_position: "Standard-Lüftungs-Lamelle",
    settings_vent_tilt_position_hint: "Lamellenposition bei gekipptem Fenster. Leer lassen = keine Lamellensteuerung.",
    settings_min_position_change: "Standard min. Positionsänderung (%)",
    settings_min_position_change_hint: "Mindestabweichung in Prozent für eine Fahrt. Kann pro Behang überschrieben werden.",
    settings_min_time: "Standard min. Zeit zwischen Änderungen (s)",
    settings_min_time_hint: "Mindestabstand in Sekunden zwischen Positionsänderungen (Motorschutz). Kann pro Behang überschrieben werden.",
    settings_command_stagger: "Kommando-Verzögerung (s)",
    settings_command_stagger_hint: "Verzögerung in Sekunden zwischen Kommandos, wenn mehrere Behänge gleichzeitig fahren. Empfohlen 0,3-0,5 für Funksysteme (Z-Wave, Zigbee). 0 = keine Verzögerung.",
    settings_logbook_enabled: "Logbuch-Einträge schreiben",
    settings_logbook_enabled_hint: "Bewegungen, Sperren, Pausen und Windschutz im Home-Assistant-Logbuch protokollieren.",
    settings_update_check_enabled: "Auf Updates prüfen",
    settings_update_check_enabled_hint: "Beim Öffnen des Panels einmalig die öffentliche GitHub-API nach dem neuesten Release abfragen und einen Update-Hinweis anzeigen. Deaktivieren, um jegliche Anfrage an GitHub zu unterbinden.",
    settings_current_value: "Aktuell",
    settings_validation_min_max: "Min muss kleiner als Max sein",
    settings_workday_sensor: "Arbeitstag-Sensor",
    settings_workday_hint: "Binärsensor zur Arbeitstag-Erkennung (z. B. HA Workday-Integration). Wird vom Bedingungstyp 'Arbeitstag-Sensor' in Regeln verwendet.",
    settings_section_wind: "Windschutz",
    settings_wind_hint: "Sicherheitsfunktion: Überschreitet die Windgeschwindigkeit den Schwellwert, fahren alle Behänge auf die Windschutz-Position (100 = offen, z. B. zum Schutz von Markisen und Lamellen; 0 = geschlossen, z. B. zum Schutz der Scheiben). Deaktiviert sich, wenn die Geschwindigkeit unter Schwellwert minus Hysterese fällt.",
    settings_wind_sensor: "Windgeschwindigkeits-Sensor",
    settings_wind_threshold: "Aktivierungsschwelle",
    settings_wind_hysteresis: "Hysterese – Aufhebung des Schutzes",
    settings_wind_hysteresis_hint: "Der Schutz wird erst aufgehoben, wenn der Wind um diesen Wert unter die Schwelle gefallen ist.",
    hyst_title_comfort: "Wie funktioniert das? – Hysterese zwischen den Sollwerten",
    hyst_title_rules: "Wie funktioniert das? – Außentemperatur-Hysterese",
    hyst_title_solar: "Wie funktioniert das? – Sonnenschein-Hysterese",
    hyst_title_wind: "Wie funktioniert das? – Wind-Hysterese",
    hyst_with_values: "Mit Ihren Werten",
    hyst_example: "Beispiel",
    hyst_between: "zwischen {a} und {b}",
    hyst_above: "über {a}",
    hyst_below: "unter {a}",
    hyst_keep: "Behält den vorherigen Zustand",
    hyst_comfort_intro: "{w}: Sollwerte {a} und {b} °C, Hysterese {h} °C.",
    hyst_col_room_temp: "Raumtemperatur",
    hyst_col_state: "Zustand",
    hyst_cold: "Kalt",
    hyst_hot: "Warm",
    hyst_comfortable: "Angenehm",
    hyst_stay_cold: "Bleibt kalt, wenn er es war, sonst angenehm",
    hyst_stay_hot: "Bleibt warm, wenn er es war, sonst angenehm",
    hyst_comfort_so1: "Die Hysterese verschiebt die Sollwerte nicht: der Raum wird ab {a} °C kalt und ab {b} °C warm.",
    hyst_comfort_so2: "Sie wirkt nur auf dem Rückweg: ein kalter Raum muss auf {ah} °C steigen, um wieder angenehm zu sein, ein warmer Raum auf {bh} °C fallen.",
    hyst_comfort_so3: "Beispiel: der Raum fällt auf {a} °C → kalt. Er steigt auf {mid} °C → noch kalt. Bei {ah} °C → angenehm. Fällt er wieder auf {mid} °C → bleibt angenehm (kalt erst wieder bei {a} °C).",
    hyst_comfort_so4: "Ohne Hysterese würde ein Raum nahe einem Sollwert bei jedem Messwert den Zustand wechseln, und die Behänge mit ihm.",
    hyst_rules_intro: "Beispiel (noch keine Ihrer Regeln hat diese Bedingung): eine Bedingung „Außentemperatur über {t} °C“, Hysterese {h} °C.",
    hyst_rules_scope: "Diese Hysterese gilt nur für die Bedingungen „Außentemperatur über / unter“ (jeweils mit eigener Schwelle) und „Außenluft im Vergleich zum Raum“ (auf die Differenz außen – Raum) Ihrer Regeln. Sie wirkt sich nicht auf die Innentemperatur-Sollwerte aus.",
    hyst_rules_intro_real: "Beispiel aus Ihren Regeln: „{rule}“ enthält die Bedingung „Außentemperatur {op} {t} °C“, Hysterese {h} °C.",
    hyst_op_above: "über",
    hyst_op_below: "unter",
    hyst_rules_so1_below: "Die in der Regel eingegebene Schwelle ist die Mitte des Bereichs: die Bedingung wird unter {tl} °C wahr und erst über {th} °C wieder falsch.",
    hyst_rules_so2_below: "Bei „über“ umgekehrt: wahr über {th} °C, wieder falsch unter {tl} °C.",
    hyst_rules_so3_below: "Damit sie unter {t} °C wahr wird, geben Sie {th} °C in der Regel ein.",
    hyst_col_temp: "Temperatur",
    hyst_col_condition: "Bedingung",
    hyst_true: "Wahr",
    hyst_false: "Falsch",
    hyst_rules_so1: "Die in der Regel eingegebene Schwelle ist die Mitte des Bereichs: die Bedingung wird über {th} °C wahr und erst unter {tl} °C wieder falsch.",
    hyst_rules_so2: "Bei „unter“ umgekehrt: wahr unter {tl} °C, wieder falsch über {th} °C.",
    hyst_rules_so3: "Damit sie über {t} °C wahr wird, geben Sie {tl} °C in der Regel ein.",
    hyst_zero: "Mit 0 keine Hysterese: der Zustand wechselt genau an der Schwelle, jedes Mal.",
    hyst_solar_intro: "{w}: Schwelle {t}, Hysterese {h}.",
    hyst_col_sensor: "Sonnenscheinsensor",
    hyst_col_strong: "Starker Sonnenschein",
    hyst_strong_yes: "Ja: die Bedingung meldet „Sonne“",
    hyst_strong_no: "Nein",
    hyst_solar_so1: "Die Schwelle ist die Mitte des Bereichs: starker Sonnenschein beginnt über {th} und endet erst unter {tl}. Eine vorbeiziehende Wolke öffnet die Behänge also nicht wieder.",
    hyst_solar_so2: "Betrifft nur Behänge mit „Nur bei starkem Sonnenschein“.",
    hyst_wind_intro: "{w}: Schwelle {t}, Hysterese {h}.",
    hyst_col_wind: "Wind",
    hyst_col_protection: "Schutz",
    hyst_wind_on: "Aktiv",
    hyst_wind_stay: "Bleibt aktiv, wenn er es war, sonst inaktiv",
    hyst_wind_off: "Aufgehoben",
    hyst_wind_so1: "Wie beim Komfort wirkt die Hysterese nur auf dem Rückweg: der Schutz aktiviert sich ab {t} und wird erst aufgehoben, wenn der Wind auf {tl} gefallen ist.",
    hyst_wind_so2: "Eine Böe, die knapp unter die Schwelle fällt, bewegt die Behänge also nicht zurück. Eine Hysterese größer oder gleich der Schwelle wird ignoriert.",
    settings_wind_position: "Windschutz-Position",
    settings_wind_position_hint: "Position, auf die alle Behänge bei aktivem Windschutz fahren (0-100). 100 = offen (schützt Markisen und Lamellen), 0 = geschlossen (schützt die Scheiben).",
    settings_section_solar: "Sonnenschein",
    settings_solar_hint: "Sensor für die Sonneneinstrahlung (Helligkeit in lx, Solarproduktion in W, Einstrahlung in W/m²). Über seiner Schwelle schließt die Option „Nur bei starkem Sonnenschein“ die Behänge.",
    settings_solar_sensor: "Sonnenscheinsensor",
    settings_solar_threshold: "Starker Sonnenschein über",
    settings_solar_threshold_hint: "Über dieser Schwelle meldet die Option „Nur bei starkem Sonnenschein“ „Sonne“.",
    threshold_entity: "oder Entität",
    threshold_entity_hint: "Ist eine Entität gewählt, wird ihr Wert verwendet; die eingegebene Zahl dient als Rückfallwert, wenn die Entität nicht verfügbar ist.",
    threshold_entity_current: "Aktuell",
    threshold_entity_unavailable: "nicht verfügbar, die eingegebene Zahl wird verwendet",
    threshold_fallback: "Wert der Entität. Falls nicht verfügbar: {v}",
    settings_solar_hysteresis: "Hysterese – Sonnenscheinschwelle",
    settings_solar_hysteresis_hint: "Verhindert, dass starker Sonnenschein bei jedem Messwert kippt, solange der Sensor nahe der Schwelle bleibt. 0 = keine Hysterese.",
    settings_solar_short: "Sonne:",
    settings_sun_facade_title: "Sonne auf Fassade – je nach Innentemperatur",
    status_auto: "Auto",
    status_paused: "Pausiert",
    status_manual: "Manuell",
    status_locked: "Gesperrt",
    status_venting: "Lüften",
    status_wind_protected: "Windschutz",
    weather_sunny: "Sonnig",
    weather_cloudy: "Bewölkt",
    weather_partlycloudy: "Teils bewölkt",
    weather_rainy: "Regen",
    weather_pouring: "Starkregen",
    weather_snowy: "Schnee",
    weather_snowy_rainy: "Schneeregen",
    weather_windy: "Windig",
    weather_windy_variant: "Windig & bewölkt",
    weather_fog: "Nebel",
    weather_hail: "Hagel",
    weather_lightning: "Gewitter",
    weather_lightning_rainy: "Gewitter mit Regen",
    weather_exceptional: "Extremwetter",
    weather_clear_night: "Klare Nacht",
    weather_unknown: "Unbekannt",
    info_sun_title: "Sonnenposition (Azimut / Elevation)",
    info_outdoor_title: "Außentemperatur",
    info_solar_title: "Solarintensität",
    info_solar_exceeded_title: "Starker Sonnenschein: Schwelle überschritten",
    rule_active_for: "Aktiv für",
    rule_covers_count: "Behang/Behänge",
    rule_inactive: "Nicht aktiv",
    master_enabled: "Automatik",
    master_enabled_hint: "Sperr- und Lüftungsschutz sowie Sicherheitsregeln bleiben auch bei deaktivierter Automatik aktiv.",
    log_time: "Zeit",
    log_event: "Ereignis",
    log_cover: "Behang",
    cover_show_log: "Protokoll dieses Behangs",
    log_message: "Details",
    log_type_position: "Position",
    log_type_status: "Status",
    log_type_rule: "Regel",
    log_type_wind: "Wind",
    log_loading: "Protokoll wird geladen...",
    log_empty: "Keine Einträge in den letzten 3 Tagen.",
    log_filter_all: "Alle",
    log_filter_cover: "Behang:",
    log_filter_all_covers: "Alle Behänge",
    log_filter_cover_note: "Globale Ereignisse (Wind) werden ebenfalls angezeigt.",
    log_clear: "Protokoll leeren",
    log_clear_confirm: "Alle Protokolleinträge löschen?",
    log_clear_confirm_all: "Gesamtes Protokoll löschen (alle Behänge)?",
    settings_section_backup: "Sicherung",
    settings_backup_hint: "Exportiere die gesamte Konfiguration als JSON-Datei. Der Import ersetzt alle Einstellungen, Behänge, Fassaden, Regeln und Szenarien.",
    settings_export: "Konfiguration exportieren",
    settings_import: "Konfiguration importieren",
    settings_import_confirm: "Die gesamte Konfiguration wird ersetzt. Fortfahren?",
    settings_import_success: "Konfiguration erfolgreich importiert.",
    settings_import_error: "Import fehlgeschlagen",
    settings_export_error: "Export fehlgeschlagen",
    settings_unsaved_confirm: "Ungespeicherte Einstellungen verwerfen?",
    settings_unsaved_warning: "Einige Einstellungen wurden geändert, aber nicht gespeichert: Sie fehlen im Export.",
    settings_export_unsaved_confirm: "Einige Einstellungen wurden geändert, aber nicht gespeichert. Vor dem Export speichern?",
    settings_save_and_export: "Speichern und exportieren",
  },
  fr: {
    title: "CoverAutomatic",
    version_link_title: "Ouvrir les notes de version sur GitHub",
    update_badge_title: "Mise à jour disponible - ouvrir les notes de version sur GitHub",
    tabs: { covers: "Volets", facades: "Façades", rules: "Règles", scenarios: "Scénarios", settings: "Paramètres", log: "Journal" },
    nav_label: "Sections",
    loading: "Chargement de la configuration...",
    error_load: "Échec du chargement de la configuration.",
    retry: "Réessayer",
    saved: "Enregistré",
    cond_time_after_dawn: "Après l'aube",
    cond_time_before_dawn: "Avant l'aube",
    cond_time_after_dusk: "Après le crépuscule",
    cond_time_before_dusk: "Avant le crépuscule",
    cond_time_after_dawn_hint: "De l'aube (+ décalage) jusqu'au crépuscule. Complément : « {other} ».",
    cond_time_before_dawn_hint: "Du crépuscule jusqu'à l'aube suivante (+ décalage). Complément : « {other} ».",
    cond_time_after_dusk_hint: "Du crépuscule (+ décalage) jusqu'à l'aube suivante. Complément : « {other} ».",
    cond_time_before_dusk_hint: "De l'aube jusqu'au crépuscule (+ décalage). Complément : « {other} ».",
    cond_time_after_sunrise_hint: "Du lever du soleil (+ décalage) jusqu'au coucher. Complément : « {other} ».",
    cond_time_before_sunrise_hint: "Du coucher du soleil jusqu'au lever suivant (+ décalage). Complément : « {other} ».",
    cond_time_after_sunset_hint: "Du coucher du soleil (+ décalage) jusqu'au lever suivant. Complément : « {other} ».",
    cond_time_before_sunset_hint: "Du lever du soleil jusqu'au coucher (+ décalage). Complément : « {other} ».",
    cover_travel_auto_default: "défaut : {s} s",
    cover_travel_not_measured: "Mesurée : pas encore (au prochain déplacement d'au moins 20 %).",
    cover_travel_used: "Utilisée : {s} s ({src}) · attente avant détection d'une commande manuelle : {wait} s",
    cover_travel_used_none: "Utilisée : aucune · attente avant détection d'une commande manuelle : {wait} s",
    cover_travel_src_manual: "saisie",
    cover_travel_src_measured: "mesurée",
    cover_travel_src_default: "défaut global",
    cover_travel_src_none: "aucune",
    settings_default_travel_time: "Durée de course par défaut (s)",
    settings_default_travel_time_placeholder: "aucune (attente de 30 s)",
    settings_default_travel_time_hint: "Durée de course utilisée pour les volets sans valeur saisie et pas encore mesurés. Ordre : valeur saisie sur le volet, puis valeur mesurée, puis ce défaut. Vide = attente de 30 s.",
    cover_travel_time: "Durée de course (s)",
    cover_travel_auto: "auto (mesurée aux premiers déplacements)",
    cover_travel_auto_measured: "auto : {s} s mesurées",
    cover_travel_measured: "Mesurée : {s} s pour une course complète.",
    cover_travel_reset: "Réinitialiser",
    cover_travel_time_hint: "Temps d'une course complète de 0 à 100 %. Après avoir envoyé une commande, l'intégration attend cette durée (plus 5 s, au moins 30 s) avant de considérer un changement de position comme une commande manuelle. Laissez vide pour utiliser la valeur mesurée, ou à défaut la durée de course par défaut des Paramètres.",
    scenario_rule_off: "désactivée dans Règles",
    scenario_rule_off_hint: "Cette règle est désactivée dans l'onglet Règles : elle ne s'applique jamais. Le réglage ci-contre reprendra effet dès qu'elle sera réactivée.",
    ha_ctype_and: "et",
    ha_ctype_or: "ou",
    ha_ctype_not: "non",
    ha_ctype_template: "modèle",
    ha_ctype_state: "état",
    ha_ctype_numeric_state: "valeur numérique",
    ha_ctype_zone: "zone",
    ha_ctype_time: "heure",
    ha_ctype_sun: "soleil",
    ha_ctype_device: "appareil",
    ha_ctype_trigger: "déclencheur",
    cond_group_sun: "Soleil",
    cond_group_temperature: "Température",
    cond_group_time: "Horaires",
    cond_group_weather: "Météo",
    cond_group_entities: "Entités",
    cond_menu_ha_state: "État d'une entité",
    cond_menu_ha_numeric: "Valeur numérique d'une entité",
    cond_menu_ha_yaml: "Condition Home Assistant (YAML)",
    cond_ha_condition: "Condition Home Assistant",
    cond_ha_state: "État d'une entité",
    cond_ha_numeric: "Valeur numérique d'une entité",
    ha_tab_form: "Formulaire",
    ha_tab_yaml: "YAML",
    ha_kind: "Type",
    ha_kind_state: "État",
    ha_kind_numeric: "Valeur numérique",
    ha_entity: "Entité",
    ha_current: "actuellement",
    ha_attribute: "Attribut",
    ha_attribute_none: "— état de l'entité —",
    ha_compare: "Comparaison",
    ha_is: "est",
    ha_is_not: "n'est pas",
    ha_for: "Depuis au moins (min)",
    ha_for_negate_hint: "Non disponible avec « n'est pas ».",
    ha_states: "États",
    ha_state_other: "Autre valeur…",
    ha_state_add: "Ajouter",
    ha_operator: "Opérateur",
    ha_op_above: "au-dessus de",
    ha_op_below: "en dessous de",
    ha_op_between: "entre",
    ha_value: "Valeur",
    ha_min: "Minimum",
    ha_max: "Maximum",
    ha_form_unsupported: "Cette condition ne peut pas être affichée sous forme de formulaire (modèle, zone, conditions imbriquées…). Elle reste modifiable en YAML.",
    ha_yaml_label: "Condition",
    ha_yaml_placeholder: "condition: state\nentity_id: person.moi\nstate: not_home\nfor: \"00:15:00\"",
    ha_yaml_help: "Même format que la section « condition » d'une automatisation Home Assistant. Une liste de conditions est combinée avec ET.",
    ha_valid: "Condition valide",
    ha_entities: "Entités surveillées",
    ha_unknown_entities: "Entités introuvables (vérifiez l'identifiant)",
    ha_err_yaml: "Erreur de syntaxe YAML ligne {line}, colonne {column}",
    ha_err_not_mapping: "Le YAML doit décrire une condition (ex. « condition: state »).",
    ha_err_invalid: "Condition invalide",
    ha_err_empty: "Condition vide",
    ha_checking: "Vérification…",
    ha_incomplete_entity: "Choisissez une entité.",
    ha_incomplete_states: "Choisissez au moins un état.",
    ha_incomplete_value: "Indiquez une valeur.",
    cond_convert: "Convertir en condition enrichie",
    cond_convert_hint: "Ajoute attribut, « n'est pas », durée et choix des états. Appliqué à l'enregistrement de la règle.",
    ha_chip_is: "{entity} est {states}",
    ha_chip_is_not: "{entity} n'est pas {states}",
    ha_chip_for: " depuis {min} min",
    ha_chip_or: " ou ",
    ha_chip_above: "{entity} > {value}",
    ha_chip_below: "{entity} < {value}",
    ha_chip_between: "{entity} entre {min} et {max}",
    ha_chip_other: "Condition HA : {type}",
    rule_op_short_and: "ET", rule_op_short_or: "OU",
    compass_n: "N", compass_e: "E", compass_s: "S", compass_w: "O",
    error_generic: "Impossible d'enregistrer la modification",
    error_not_found: "Élément introuvable (il a peut-être été supprimé entre-temps)",
    error_invalid_format: "Valeur invalide",
    error_invalid_conditions: "Condition de règle invalide",
    error_invalid_data: "Données de configuration invalides",
    error_too_large: "Le fichier d'import est trop volumineux",
    error_unauthorized: "Droits administrateur requis",
    error_invalid_comfort_range: "La consigne froide doit être inférieure à la consigne chaude",
    error_invalid_wind_hysteresis: "L'hystérésis du vent doit être inférieure au seuil de vent",
    rule_priority_up: "Monter la priorité",
    rule_priority_down: "Baisser la priorité",
    rule_enabled_aria: "Règle {name} active",
    rule_invalid_fields: "Corrigez les champs en rouge (valeur vide ou invalide) avant d'enregistrer",
    ha_err_request: "Vérification impossible",
    error_not_loaded: "CoverAutomatic n'est pas chargé (rechargez l'intégration ou redémarrez Home Assistant)",
    error_invalid_solar_hysteresis: "L'hystérésis d'ensoleillement doit être inférieure au seuil d'ensoleillement",
    error_invalid_value: "Nombre invalide",
    drag_handle: "Glisser pour réordonner",
    settings_nav_label: "Réglages",
    import_invalid_json: "JSON invalide",
    status_unlocked: "Déverrouillé",
    log_msg_wind_activated: "Activée ({speed} ≥ {threshold})",
    log_msg_wind_deactivated: "Désactivée ({speed} ≤ {threshold})",
    log_msg_wind_disabled: "Désactivée (désactivée dans les réglages)",
    log_msg_status_change: "{from} → {to}",
    log_msg_rule: "{rule} → {position} %",
    log_msg_position: "{from} % → {to} %",
    log_msg_safety_takeover: "Règle de sécurité {rule} prend la main ({status}) → {position} %",
    log_msg_safety_release: "Règle de sécurité {rule} terminée ({status})",
    log_msg_sensor_unavailable: "{status} conservé : capteur {sensor} indisponible",
    log_msg_lock_sensor_missing: "Capteur de fenêtre {sensor} introuvable : ignoré",
    log_msg_move_blocked_window_unknown: "Mouvement vers {position} % retenu : état de la fenêtre inconnu ({sensor})",
    log_msg_wind_restore_dropped: "Protection vent restaurée abandonnée : capteur {sensor} introuvable ou sans valeur",
    save: "Enregistrer",
    cancel: "Annuler",
    delete: "Supprimer",
    rule_duplicate: "Dupliquer (la copie est créée juste en dessous)",
    rule_copy_suffix: "copie",
    settings_wind_off_note: "Choisissez un capteur de vent pour activer la protection.",
    settings_solar_off_note: "Choisissez un capteur pour régler le seuil et l'hystérésis.",
    settings_solar_nested_off: "Utilisé seulement par l'option « Seulement en cas de fort ensoleillement » (ici ou sur un volet).",
    cover_lock_box_title: "Fenêtre ouverte",
    cover_lock_off_note: "Choisissez un capteur d'ouverture pour activer ces réglages.",
    cover_vent_box_title: "Fenêtre basculée (aération)",
    cover_vent_off_note: "Choisissez un capteur d'oscillo-battant pour régler la position d'aération.",
    confirm_delete: "Vraiment supprimer ?",
    add: "Ajouter",
    edit: "Modifier",
    close: "Fermer",
    none: "Aucun",
    enabled: "Activé",
    active: "Actif",
    activate: "Activer",
    name: "Nom",
    // Covers
    cover_facade: "Façade",
    cover_facade_hint: "Détermine quelles règles de façade s'appliquent à ce volet.",
    cover_status: "Statut",
    cover_pause_duration: "Durée de pause (min)",
    cover_pause_duration_hint: "Durée de mise en pause de l'automatisation après une commande manuelle. Vide = valeur globale par défaut.",
    cover_indoor_temp: "Capteur de température intérieure (°C)",
    cover_indoor_temp_hint: "Capteur de la pièce de ce volet, pour les consignes et « Soleil sur la façade ». Remplace le capteur global.",
    cover_lock_sensor: "Capteur de fenêtre ouverte",
    cover_lock_sensor_hint: "Capteur d'ouverture de fenêtre. Fenêtre ouverte : le volet se place en position de verrouillage (sécurité).",
    cover_lock_hold: "Garder la position actuelle à l'ouverture de la fenêtre",
    cover_lock_hold_hint: "Activé : le volet reste où il est tant que la fenêtre est ouverte (verrouillé, aucune commande). Désactivé : il se place sur la position de verrouillage ci-dessous (uniquement vers le haut, jamais plus fermé).",
    cover_lock_position: "Position de verrouillage",
    cover_lock_position_hint: "Position cible lorsque la fenêtre est ouverte. Vide = valeur globale par défaut.",
    cover_vent_sensor: "Capteur de fenêtre basculée",
    cover_vent_sensor_hint: "Capteur de fenêtre en oscillo-battant. Fenêtre basculée : le volet se place en position d'aération.",
    cover_vent_position: "Position d'aération",
    cover_vent_position_hint: "Position cible lorsque la fenêtre est basculée. Vide = valeur globale par défaut.",
    cover_comfort_min: "Consigne de température froide (°C)",
    cover_comfort_max: "Consigne de température chaude (°C)",
    cover_comfort_hint: "Consignes propres à la pièce. Vide = valeurs globales des paramètres.",
    cover_comfort_global: "Vide = valeur globale : {v} °C ({src})",
    cover_default_note: "Vide = valeur par défaut : {v} (Paramètres)",
    unit_sensor: "unité du capteur",
    cover_comfort_src_settings: "Paramètres",
    cover_sun_switches_hint: "Réglages propres à ce volet ; « Global » = valeur de Paramètres › Exposition au soleil.",
    tristate_global: "Global ({value})",
    settings_sun_facade_hint: "Ces réglages ne changent que la réponse de la condition « Soleil sur la façade », pour les volets ayant un capteur de température intérieure (propre ou global). Ils servent aux règles de fermeture au soleil : ne fermer que lorsque c'est utile. Laissez tout désactivé si une règle ouvre les volets quand il y a du soleil.",
    sun_heating_label: "Action sur consigne de température froide : laisser le soleil chauffer",
    sun_heating_hint: "La condition répond « pas de soleil » : les règles de fermeture au soleil ne ferment pas et le soleil chauffe la pièce. À éviter si une règle ouvre les volets quand il y a du soleil (elle ne s'appliquerait plus).",
    sun_below: "≤ {t} °C",
    sun_above: "≥ {t} °C",
    sun_between: "entre {min} et {max} °C",
    settings_comfort_range_title: "Consignes de température intérieure",
    settings_indoor_reminder: "S'applique selon la température intérieure de chaque pièce (onglet Capteurs : capteur global {name}, consignes {min} et {max} °C). Un volet peut avoir son propre capteur et ses propres consignes.",
    settings_indoor_none: "non défini",
    sun_explain_title: "Comment ça marche ?",
    sun_explain_intro: "Exemple : une règle « fermer si soleil » et le soleil sur la façade. Les lignes surlignées correspondent à vos réglages.",
    sun_explain_col_room: "Pièce",
    sun_explain_col_answer: "Réponse de « Soleil sur la façade »",
    sun_explain_col_effect: "Effet",
    sun_explain_room_cold_on: "Froide, « laisser le soleil chauffer » coché",
    sun_explain_room_cold_off: "Froide, case décochée",
    sun_explain_room_position: "Confortable, « Dès que le soleil est sur la façade »",
    sun_explain_room_ignore: "Confortable, « Jamais »",
    sun_explain_room_preemptive: "Confortable, « Seulement en cas de fort ensoleillement »",
    sun_explain_room_hot: "Trop chaude",
    sun_explain_sun: "« soleil »",
    sun_explain_no_sun: "« pas de soleil »",
    sun_explain_sun_always: "toujours « soleil »",
    sun_explain_sun_if_strong: "« soleil » si le capteur dépasse le seuil, sinon « pas de soleil »",
    sun_explain_eff_warm: "Ne ferme pas : le volet reste ouvert et la pièce se réchauffe.",
    sun_explain_eff_close: "Ferme.",
    sun_explain_eff_close_as_hot: "Ferme, comme si la pièce était chaude.",
    sun_explain_eff_wait: "Ne ferme pas ; fermera quand la pièce deviendra trop chaude.",
    sun_explain_eff_strong: "Ne ferme que par grand soleil, avant que la pièce chauffe.",
    sun_explain_so: "Donc",
    sun_explain_cold: "Pièce froide : la case n'ouvre pas le volet, elle empêche la fermeture au soleil. Si le volet est déjà ouvert (par une règle d'ouverture le jour, par exemple), il le reste.",
    sun_explain_hot: "Pièce trop chaude : le volet ne ferme que si une règle « fermer si soleil » s'applique à ce volet et au scénario actif.",
    sun_explain_comfort: "Pièce confortable : c'est l'entre-deux, où vous choisissez quand le soleil doit compter.",
    sun_comfort_label: "Action entre les consignes : comportement suivant le soleil",
    sun_comfort_position: "Dès que le soleil est sur la façade",
    sun_comfort_position_hint: "La condition est vraie dès que le soleil est sur la façade.",
    sun_comfort_ignore: "Jamais (attendre que la pièce devienne trop chaude)",
    sun_comfort_ignore_hint: "Répond « pas de soleil » : le volet ne ferme que lorsque la pièce devient trop chaude.",
    sun_comfort_preemptive: "Seulement en cas de fort ensoleillement",
    sun_comfort_preemptive_hint: "Répond « soleil » dès que le capteur d'ensoleillement dépasse son seuil : le volet ferme avant que la pièce ne chauffe.",
    sun_comfort_hint: "Comportement de « Soleil sur la façade » quand la pièce est entre les consignes. Global = valeur de Paramètres › Exposition au soleil.",
    sun_hot_note: "Pièce trop chaude (≥ {t} °C) : le soleil est toujours pris en compte dès qu'il est sur la façade.",
    solar_used_by: "Utilisé par l'option « Seulement en cas de fort ensoleillement » : {n} volet(s).",
    solar_unused: "Utilisé uniquement par l'option « Seulement en cas de fort ensoleillement » (aucun volet ne l'utilise actuellement).",
    tristate_on: "Activé",
    tristate_off: "Désactivé",
    cover_inverted: "Inverser le sens ouverture/fermeture",
    cover_inverted_hint: "À activer si 100 % signifie fermé (sens moteur inversé).",
    cover_lock_tilt: "Inclinaison de verrouillage",
    cover_vent_tilt: "Inclinaison d'aération",
    cover_inverted_tilt: "Inclinaison inversée",
    cover_min_pos_change: "Variation de position min. (%)",
    cover_min_pos_change_hint: "Écart de position minimal pour déclencher un mouvement. Vide = valeur globale par défaut.",
    cover_min_time: "Délai min. entre changements (s)",
    cover_min_time_hint: "Nombre minimal de secondes entre deux changements de position. Vide = valeur globale par défaut.",
    cover_section_base: "Général",
    cover_section_sensors: "Capteurs",
    cover_section_advanced: "Avancé",
    cover_section_tilt: "Inclinaison",
    cover_section_window: "Fenêtre",
    cover_section_automation: "Automatisation",
    cover_section_room: "Pièce",
    cover_inverted_short: "Sens inversé",
    cover_lock_hold_short: "Garder la position",
    sun_heating_label_short: "Froide : laisser chauffer",
    sun_comfort_label_short: "Entre les consignes",
    settings_comfort_min_short: "Consigne froide (°C)",
    settings_comfort_max_short: "Consigne chaude (°C)",
    cover_comfort_min_short: "Consigne froide (°C)",
    cover_comfort_max_short: "Consigne chaude (°C)",
    settings_indoor_temp_short: "Capteur intérieur (°C)",
    cover_indoor_temp_short: "Capteur intérieur (°C)",
    settings_comfort_hysteresis_short: "Hystérésis consignes (°C)",
    settings_threshold_hysteresis_short: "Hystérésis extérieure (°C)",
    settings_solar_hysteresis_short: "Hystérésis ensoleillement",
    settings_wind_hysteresis_short: "Hystérésis vent",
    settings_solar_threshold_short: "Seuil fort ensoleillement",
    settings_sun_facade_title_short: "Soleil sur la façade",
    cover_min_time_short: "Délai min. (s)",
    cover_min_pos_change_short: "Variation min. (%)",
    cover_expand_all: "Tout déplier",
    cover_collapse_all: "Tout replier",
    cover_sum_auto_on: "Automatique",
    cover_sum_auto_off: "Automatisation désactivée",
    cover_sum_no_facade: "sans façade",
    cover_sum_open: "Ouverte : {v}",
    cover_sum_hold: "garder la position",
    cover_sum_tilted: "Basculée : {v}",
    cover_sum_no_window: "Aucun capteur de fenêtre",
    cover_sum_pause: "Pause {n} min",
    cover_sum_travel: "Course {n} s",
    cover_sum_own: "{n} réglage(s) propre(s)",
    cover_sum_all_global: "valeurs par défaut",
    cover_sum_global: "global",
    cover_sum_no_indoor: "Aucun capteur intérieur",
    cover_sum_sun_heat_on: "Froide : laisser chauffer",
    cover_sum_sun_heat_off: "Froide : soleil pris en compte",
    cover_sum_sun_between: "Entre : {v}",
    cover_sum_mode_position: "dès que le soleil est là",
    cover_sum_mode_ignore: "jamais",
    cover_sum_mode_preemptive: "fort ensoleillement",
    cover_auto_enabled: "Automatisation activée",
    cover_temp: "Temp.",
    cover_current_pos: "Actuelle",
    cover_target_pos: "Cible",
    cover_position: "Position",
    cover_position_target_label: "Cible",
    cover_position_inverted_tip: "Volet inversé : HA indique {raw} % (affiché ici dans l'échelle des règles)",
    cover_hysteresis_position: "Changement de position trop faible",
    cover_hysteresis_time: "Trop tôt depuis le dernier changement",
    cover_rule: "Règle",
    cover_no_rule: "–",
    cover_resume: "Reprendre",
    cover_goto_rule: "Ouvrir la règle",
    cover_remove: "Retirer le volet",
    cover_last_change: "Dernier changement",
    cover_just_now: "à l'instant",
    time_ago_min: "il y a {n} min",
    time_ago_h: "il y a {n} h",
    time_ago_h_m: "il y a {h} h {m} min",
    show_hint: "Afficher l'aide",
    settings_temp_color: "Couleurs de la température (liste des volets)",
    settings_temp_color_action: "Selon l'action à faire",
    settings_temp_color_action_hint: "Pièce froide en rouge (à chauffer), pièce chaude en bleu (à refroidir).",
    settings_temp_color_thermometer: "Selon la température",
    settings_temp_color_thermometer_hint: "Pièce froide en bleu, pièce chaude en rouge, comme un thermomètre.",
    comfort_cooling: "Chaud – à refroidir",
    comfort_heating: "Froid – à chauffer",
    comfort_neutral: "Confort",
    cover_add: "Ajouter des volets",
    // Facades
    facade_direction: "Orientation",
    facade_direction_hint: "Préremplit les valeurs d'azimut en tenant compte de la rotation de la maison.",
    facade_azimuth_start: "Azimut début",
    facade_azimuth_end: "Azimut fin",
    facade_azimuth_hint: "Relèvements réels (boussole) où le soleil arrive sur cette façade et la quitte. Début = fin : cercle complet.",
    facade_min_elevation: "Élévation min.",
    facade_min_elevation_hint: "Élévation solaire minimale pour que cette façade soit considérée comme ensoleillée. Une valeur inférieure à 0 compte comme 0.",
    facade_covers: "Volets associés",
    facade_add: "Ajouter une façade",
    facade_no_covers: "Aucun volet associé",
    facade_sun_active: "Soleil sur la façade",
    facade_dir_north: "Nord",
    facade_dir_east: "Est",
    facade_dir_south: "Sud",
    facade_dir_west: "Ouest",
    // Rules
    rule_priority: "Priorité",
    rule_target_pos: "Position cible",
    rule_target_pos_hint: "Position du volet lorsque cette règle s'applique (0 = fermé, 100 = entièrement ouvert).",
    rule_target_tilt: "Inclinaison cible",
    rule_operator: "Opérateur des conditions",
    rule_operator_hint: "ET = toutes les conditions doivent être remplies. OU = une seule condition suffit.",
    rule_operator_and: "ET (toutes requises)",
    rule_operator_or: "OU (une seule suffit)",
    rule_conditions: "Conditions",
    rule_scenarios: "Scénarios",
    rule_scenarios_hint: "Scénarios dans lesquels cette règle s'applique. Dans chaque scénario, elle peut encore être désactivée temporairement depuis l'onglet Scénarios.",
    rule_safety: "Règle de sécurité",
    rule_safety_hint: "Agit même si le volet est en pause après un mouvement manuel, en mode manuel, en protection vent ou avec l'automatisation désactivée. Ne passe pas outre le verrouillage (fenêtre ouverte). Entre règles, c'est la priorité qui décide : placez-la en haut de la liste. À réserver aux urgences, par exemple l'alarme incendie.",
    rule_safety_badge: "Sécurité",
    scenario_no_member_rules: "Aucune règle n'appartient à ce scénario (à cocher dans l'éditeur de règle).",
    rule_groups_operator: "Les groupes sont reliés par",
    rule_groups_hint: "ET = tous les groupes doivent être remplis. OU = un seul groupe suffit. À l'intérieur d'un groupe, c'est son propre opérateur qui s'applique.",
    rule_group: "Groupe",
    rule_group_joined_by: "conditions reliées par",
    rule_group_add: "Ajouter un groupe",
    rule_group_add_hint: "Les groupes permettent par exemple (A OU B) ET (C OU D), ou (A ET B) OU (C ET D).",
    rule_group_delete: "Supprimer le groupe et ses conditions",
    rule_group_delete_confirm: "Supprimer ce groupe et ses conditions ?",
    rule_unsaved_confirm: "Abandonner les modifications non enregistrées de cette règle ?",
    discard: "Abandonner",
    input_invalid_range: "Saisissez un nombre entier entre {min} et {max}",
    input_not_integer: "Saisissez un nombre entier",
    input_invalid_number: "Saisissez un nombre valide",
    rule_group_empty: "Aucune condition dans ce groupe pour le moment (un groupe vide est ignoré).",
    rule_cond_move: "Déplacer vers un autre groupe",
    rule_cond_up: "Monter",
    rule_cond_down: "Descendre",
    rule_group_up: "Monter le groupe",
    rule_group_down: "Descendre le groupe",
    rule_cond_not: "NON",
    rule_cond_not_hint: "Inverser cette condition (NON). Si son capteur est indisponible, la condition n'est pas remplie.",
    rule_groups_count: "{n} groupes",
    cond_collapse: "Replier",
    cond_expand: "Développer",
    cond_collapse_all: "Tout replier",
    cond_expand_all: "Tout développer",
    rule_facades: "Façades",
    rule_covers: "Volets",
    rule_assignment_hint: "Limite cette règle à certaines façades/volets. Vide = s'applique à tous les volets.",
    rule_add: "Ajouter une règle",
    rule_add_condition: "Ajouter une condition",
    rule_no_conditions: "Aucune condition",
    rule_reorder_hint: "Glisser ou utiliser ▲▼ pour réordonner. La règle la plus haute l'emporte si plusieurs règles s'appliquent.",
    // Condition types
    cond_sun_on_facade: "Soleil sur la façade",
    cond_sun_elevation_above: "Élévation solaire supérieure à",
    cond_sun_elevation_below: "Élévation solaire inférieure à",
    cond_temperature_above: "Température extérieure supérieure à",
    cond_temperature_below: "Température extérieure inférieure à",
    cond_temperature_comfort: "Température de la pièce",
    cond_outdoor_vs_indoor: "Air extérieur comparé à la pièce",
    cond_room_occupied: "Pièce occupée",
    cond_group_presence: "Présence",
    opt_cooler: "plus frais que la pièce",
    opt_warmer: "plus chaud que la pièce",
    param_delta: "Écart minimum (°C)",
    cover_occupancy_box_title: "Occupation de la pièce",
    cover_occupancy_sensor: "Capteur d'occupation",
    cover_occupancy_sensor_hint: "Utilisé par la condition « Pièce occupée » des règles. Avec NON, elle permet par exemple de n'ouvrir que si la pièce est libre. Capteur indisponible : ni « occupée » ni « libre » n'est rempli.",
    cover_occupancy_off_note: "Choisissez un capteur pour indiquer quand la pièce est occupée.",
    cover_occupancy_states: "États = pièce occupée",
    cover_occupancy_states_placeholder: "Présent, on, home…",
    cover_occupancy_states_hint: "Cliquez sur les états qui veulent dire « pièce occupée » (plusieurs possibles). Un état absent de la liste peut être ajouté.",
    cover_occupancy_default_note: "Aucun état choisi : états reconnus par défaut (on, home, Présent, occupied, detected).",
    cover_occupancy_reset: "Revenir aux états par défaut",
    cond_time_between: "Heure comprise entre",
    cond_time_after_sunrise: "Après le lever du soleil",
    cond_time_after_sunset: "Après le coucher du soleil",
    cond_time_before_sunrise: "Avant le lever du soleil",
    cond_time_before_sunset: "Avant le coucher du soleil",
    cond_state_is: "L'état est",
    cond_numeric_state: "Valeur numérique",
    cond_weather_is: "La météo est",
    cond_day_of_week: "Jour de la semaine",
    cond_workday: "Capteur jour ouvré",
    // Condition params
    param_elevation: "Élévation",
    param_temperature: "Température",
    param_start_time: "Heure de début",
    param_end_time: "Heure de fin",
    param_offset: "Décalage (min)",
    param_entity_id: "ID d'entité",
    param_entity_search: "Rechercher un nom ou un ID d'entité…",
    param_state: "État",
    param_operator: "Comparaison",
    param_value: "Valeur",
    param_hysteresis: "Hystérésis",
    opt_above: "supérieur à",
    opt_below: "inférieur à",
    param_weather: "Condition météo",
    param_mode: "Mode",
    param_days: "Jours",
    param_select_type: "Choisir le type de condition",
    cond_preview_active: "remplie",
    cond_preview_inactive: "non remplie",
    cond_preview_context: "dépend du contexte",
    day_mon: "Lun", day_tue: "Mar", day_wed: "Mer", day_thu: "Jeu", day_fri: "Ven", day_sat: "Sam", day_sun: "Dim",
    opt_on: "Activé (jour ouvré)", opt_off: "Désactivé (jour non ouvré)",
    opt_cooling: "Chaude (≥ consigne chaude)", opt_heating: "Froide (≤ consigne froide)", opt_neutral: "Entre les consignes",
    // Scenarios
    scenario_add: "Ajouter un scénario",
    scenario_icon: "Icône",
    scenario_icon_custom: "Icône MDI personnalisée",
    scenario_icon_custom_hint: "Saisissez un nom d'icône Material Design (ex. mdi:lightbulb). Liste complète sur materialdesignicons.com.",
    scenario_no_rules: "Aucune règle configurée",
    // Settings
    settings_outdoor_temp: "Capteur de température extérieure",
    settings_outdoor_temp_short: "Ext. :",
    settings_outdoor_temp_hint: "Utilisé pour les conditions de règle basées sur la température (supérieure/inférieure à).",
    settings_indoor_temp: "Capteur de température intérieure (global) (°C)",
    settings_indoor_temp_hint: "Utilisé pour les volets sans capteur intérieur propre. Sert aux consignes et à « Soleil sur la façade ».",
    settings_weather: "Entité météo",
    settings_weather_hint: "Utilisée pour les conditions de règle basées sur la météo (ex. n'ombrer que par temps ensoleillé).",
    settings_comfort_min: "Consigne de température froide (°C)",
    settings_comfort_max: "Consigne de température chaude (°C)",
    settings_comfort_hint: "Plage de température où la pièce est jugée confortable. Jusqu'à la consigne froide : pièce froide ; à partir de la consigne chaude : pièce trop chaude. Utilisée par la condition « Température de la pièce » et par « Soleil sur la façade » (onglet Exposition au soleil).",
    settings_comfort_hysteresis: "Hystérésis – entre les consignes (°C)",
    settings_comfort_hysteresis_hint: "Évite qu'une pièce proche d'une consigne change d'état à chaque mesure : elle ne redevient confortable qu'après s'être éloignée de la consigne de cette valeur.",
    settings_threshold_hysteresis: "Hystérésis – sur température extérieure dans les règles (°C)",
    settings_threshold_hysteresis_hint: "Évite qu'une condition « température extérieure supérieure/inférieure à » ou « Air extérieur comparé à la pièce » bascule à chaque mesure quand la température reste proche du seuil. 0 = pas d'hystérésis.",
    settings_house_rotation: "Rotation de la maison (degrés)",
    settings_house_rotation_hint: "Décalage par rapport au nord géographique (-180 à 180, positif = sens horaire). Appliqué lors du choix d'une orientation de façade ; une modification fait aussi pivoter les façades existantes. Faites glisser la maison sur la boussole, maintenez Maj pour aligner par pas de 45°.",
    settings_house_rotation_reset: "Réinitialiser",
    settings_section_house: "Maison",
    settings_section_sensors: "Capteurs",
    settings_outdoor_box_title: "Température extérieure",
    settings_outdoor_off_note: "Choisissez un capteur de température extérieure pour régler l'hystérésis.",
    settings_other_sensors_title: "Autres capteurs",
    settings_section_comfort: "Exposition au soleil",
    settings_section_automation: "Automatisation",
    settings_auto_box_pause: "Pause après une commande manuelle",
    settings_auto_box_window: "Positions de fenêtre",
    settings_auto_box_moves: "Mouvements",
    settings_auto_box_misc: "Journal et mises à jour",
    settings_pause_duration: "Durée de pause par défaut (min)",
    pause_resume_on_match: "Reprendre quand la position correspond à la règle",
    pause_resume_on_match_hint: "Termine la pause après une commande manuelle dès que le volet est revenu à la position demandée par sa règle : remis en place à la main, ou la règle a changé et demande la position où il a été laissé. Vérifié une fois le volet immobile, au moins 1 min après le début de la pause. La durée de pause reste le maximum.",
    settings_pause_duration_hint: "Durée de mise en pause de l'automatisation après une commande manuelle d'un volet. Modifiable par volet.",
    settings_lock_position: "Position de verrouillage par défaut",
    settings_lock_position_hint: "Position cible lorsque la fenêtre est ouverte (100 = entièrement ouvert). Modifiable par volet.",
    settings_lock_tilt_position: "Inclinaison de verrouillage par défaut",
    settings_lock_tilt_position_hint: "Inclinaison lorsque la fenêtre est ouverte. Laisser vide pour ne pas piloter l'inclinaison.",
    settings_vent_position: "Position d'aération par défaut",
    settings_vent_position_hint: "Position cible lorsque la fenêtre est basculée (ex. 30 pour un espace d'aération). Modifiable par volet.",
    settings_vent_tilt_position: "Inclinaison d'aération par défaut",
    settings_vent_tilt_position_hint: "Inclinaison lorsque la fenêtre est basculée. Laisser vide pour ne pas piloter l'inclinaison.",
    settings_min_position_change: "Variation de position min. par défaut (%)",
    settings_min_position_change_hint: "Écart de position minimal en pourcentage pour déclencher un mouvement. Modifiable par volet.",
    settings_min_time: "Délai min. entre changements par défaut (s)",
    settings_min_time_hint: "Nombre minimal de secondes entre deux changements de position (protection moteur). Modifiable par volet.",
    settings_command_stagger: "Délai entre commandes (s)",
    settings_command_stagger_hint: "Délai en secondes entre les commandes lorsque plusieurs volets bougent en même temps. Recommandé : 0,3-0,5 pour les systèmes radio (Z-Wave, Zigbee). 0 = aucun délai.",
    settings_logbook_enabled: "Écrire dans le journal de bord",
    settings_logbook_enabled_hint: "Enregistre les mouvements des volets, verrouillages/déverrouillages, pauses/reprises et la protection contre le vent dans le journal de bord de Home Assistant.",
    settings_update_check_enabled: "Vérifier les mises à jour",
    settings_update_check_enabled_hint: "À l'ouverture du panneau, interroge une fois l'API publique GitHub pour connaître la dernière version et afficher un avis de mise à jour. Désactiver pour empêcher toute requête sortante vers GitHub.",
    settings_current_value: "Actuel",
    settings_validation_min_max: "Le min. doit être inférieur au max.",
    settings_workday_sensor: "Capteur jour ouvré",
    settings_workday_hint: "Capteur binaire de détection des jours ouvrés (ex. intégration Workday de HA). Utilisé par le type de condition « jour ouvré » dans les règles.",
    settings_section_wind: "Protection contre le vent",
    settings_wind_hint: "Fonction de sécurité : quand la vitesse du vent dépasse le seuil, tous les volets se placent sur la position de protection vent (100 = ouverts, par exemple pour protéger stores et lames ; 0 = fermés, par exemple pour protéger les vitres). Se désactive lorsque la vitesse repasse sous le seuil moins l'hystérésis.",
    settings_wind_sensor: "Capteur de vitesse du vent",
    settings_wind_threshold: "Seuil d'activation",
    settings_wind_hysteresis: "Hystérésis – levée de la protection",
    settings_wind_hysteresis_hint: "La protection n'est levée qu'une fois le vent redescendu de cette valeur sous le seuil.",
    hyst_title_comfort: "Comment ça marche ? – hystérésis entre les consignes",
    hyst_title_rules: "Comment ça marche ? – hystérésis sur température extérieure",
    hyst_title_solar: "Comment ça marche ? – hystérésis d'ensoleillement",
    hyst_title_wind: "Comment ça marche ? – hystérésis du vent",
    hyst_with_values: "Avec vos valeurs",
    hyst_example: "Exemple",
    hyst_between: "entre {a} et {b}",
    hyst_above: "au-dessus de {a}",
    hyst_below: "en dessous de {a}",
    hyst_keep: "Garde son état précédent",
    hyst_comfort_intro: "{w} : consignes {a} et {b} °C, hystérésis {h} °C.",
    hyst_col_room_temp: "Température de la pièce",
    hyst_col_state: "État",
    hyst_cold: "Froide",
    hyst_hot: "Chaude",
    hyst_comfortable: "Confortable",
    hyst_stay_cold: "Reste froide si elle l'était, sinon confortable",
    hyst_stay_hot: "Reste chaude si elle l'était, sinon confortable",
    hyst_comfort_so1: "L'hystérésis ne déplace pas les consignes : la pièce devient froide dès {a} °C et chaude dès {b} °C.",
    hyst_comfort_so2: "Elle n'agit qu'au retour : une pièce froide doit remonter à {ah} °C pour redevenir confortable, une pièce chaude doit redescendre à {bh} °C.",
    hyst_comfort_so3: "Exemple : la pièce descend à {a} °C → froide. Elle remonte à {mid} °C → toujours froide. À {ah} °C → confortable. Si elle redescend à {mid} °C → elle reste confortable (elle ne redevient froide qu'à {a} °C).",
    hyst_comfort_so4: "Sans hystérésis, une pièce qui hésite autour d'une consigne changerait d'état à chaque mesure, et les volets avec elle.",
    hyst_rules_intro: "Exemple (aucune de vos règles n'a encore cette condition) : une condition « température extérieure supérieure à {t} °C », hystérésis {h} °C.",
    hyst_rules_scope: "Cette hystérésis s'applique uniquement aux conditions « Température extérieure supérieure à / inférieure à » (chacune avec son propre seuil) et « Air extérieur comparé à la pièce » (sur l'écart extérieur – pièce) de vos règles. Elle n'a aucun effet sur les consignes de température intérieure.",
    hyst_rules_intro_real: "Exemple tiré de vos règles : « {rule} » contient la condition « température extérieure {op} {t} °C », hystérésis {h} °C.",
    hyst_op_above: "supérieure à",
    hyst_op_below: "inférieure à",
    hyst_rules_so1_below: "Le seuil saisi dans la règle est le milieu de la zone : la condition devient vraie en dessous de {tl} °C et ne redevient fausse qu'au-dessus de {th} °C.",
    hyst_rules_so2_below: "Pour « supérieure à », c'est l'inverse : vraie au-dessus de {th} °C, fausse à nouveau en dessous de {tl} °C.",
    hyst_rules_so3_below: "Pour qu'elle devienne vraie en dessous de {t} °C, saisissez {th} °C dans la règle.",
    hyst_col_temp: "Température",
    hyst_col_condition: "Condition",
    hyst_true: "Vraie",
    hyst_false: "Fausse",
    hyst_rules_so1: "Le seuil saisi dans la règle est le milieu de la zone : la condition devient vraie au-dessus de {th} °C et ne redevient fausse qu'en dessous de {tl} °C.",
    hyst_rules_so2: "Pour « inférieure à », c'est l'inverse : vraie en dessous de {tl} °C, fausse à nouveau au-dessus de {th} °C.",
    hyst_rules_so3: "Pour qu'elle devienne vraie au-dessus de {t} °C, saisissez {tl} °C dans la règle.",
    hyst_zero: "Avec 0, pas d'hystérésis : l'état change exactement au seuil, à chaque passage.",
    hyst_solar_intro: "{w} : seuil {t}, hystérésis {h}.",
    hyst_col_sensor: "Capteur d'ensoleillement",
    hyst_col_strong: "Fort ensoleillement",
    hyst_strong_yes: "Oui : la condition répond « soleil »",
    hyst_strong_no: "Non",
    hyst_solar_so1: "Le seuil est le milieu de la zone : le fort ensoleillement commence au-dessus de {th} et ne s'arrête qu'en dessous de {tl}. Un nuage passager ne rouvre donc pas les volets.",
    hyst_solar_so2: "Ne concerne que les volets réglés sur « Seulement en cas de fort ensoleillement ».",
    hyst_wind_intro: "{w} : seuil {t}, hystérésis {h}.",
    hyst_col_wind: "Vent",
    hyst_col_protection: "Protection",
    hyst_wind_on: "Activée",
    hyst_wind_stay: "Reste activée si elle l'était, sinon non activée",
    hyst_wind_off: "Levée",
    hyst_wind_so1: "Comme pour le confort, l'hystérésis n'agit qu'au retour : la protection s'active dès {t} et n'est levée qu'une fois le vent redescendu à {tl}.",
    hyst_wind_so2: "Une rafale qui retombe juste sous le seuil ne relance donc pas les volets. Une hystérésis supérieure ou égale au seuil est ignorée.",
    settings_wind_position: "Position de protection vent",
    settings_wind_position_hint: "Position prise par tous les volets pendant la protection vent (0-100). 100 = ouverts (protège stores et lames), 0 = fermés (protège les vitres).",
    settings_section_solar: "Ensoleillement",
    settings_solar_hint: "Capteur mesurant l'ensoleillement (luminosité en lux, production solaire en W, irradiance en W/m²). Au-dessus de son seuil, l'option « Seulement en cas de fort ensoleillement » ferme les volets.",
    settings_solar_sensor: "Capteur d'ensoleillement",
    settings_solar_threshold: "Fort ensoleillement au-dessus de",
    settings_solar_threshold_hint: "Au-dessus de ce seuil, l'option « Seulement en cas de fort ensoleillement » répond « soleil ».",
    threshold_entity: "ou entité",
    threshold_entity_hint: "Si une entité est choisie, sa valeur est utilisée ; le nombre saisi sert de secours si l'entité est indisponible.",
    threshold_entity_current: "Actuel",
    threshold_entity_unavailable: "indisponible, le nombre saisi est utilisé",
    threshold_fallback: "Valeur de l'entité. Si elle est indisponible : {v}",
    settings_solar_hysteresis: "Hystérésis – seuil d'ensoleillement",
    settings_solar_hysteresis_hint: "Évite que le fort ensoleillement bascule à chaque mesure quand le capteur reste proche du seuil. 0 = pas d'hystérésis.",
    settings_solar_short: "Soleil :",
    settings_sun_facade_title: "Soleil sur la façade – selon la température intérieure",
    status_auto: "Auto",
    status_paused: "En pause",
    status_manual: "Manuel",
    status_locked: "Verrouillé",
    status_venting: "Aération",
    status_wind_protected: "Protection vent",
    weather_sunny: "Ensoleillé",
    weather_cloudy: "Nuageux",
    weather_partlycloudy: "Partiellement nuageux",
    weather_rainy: "Pluvieux",
    weather_pouring: "Forte pluie",
    weather_snowy: "Neigeux",
    weather_snowy_rainy: "Neige fondue",
    weather_windy: "Venteux",
    weather_windy_variant: "Venteux et nuageux",
    weather_fog: "Brouillard",
    weather_hail: "Grêle",
    weather_lightning: "Éclairs",
    weather_lightning_rainy: "Orage",
    weather_exceptional: "Temps exceptionnel",
    weather_clear_night: "Nuit claire",
    weather_unknown: "Inconnu",
    info_sun_title: "Position du soleil (azimut / élévation)",
    info_outdoor_title: "Température extérieure",
    info_solar_title: "Intensité solaire",
    info_solar_exceeded_title: "Fort ensoleillement : seuil dépassé",
    rule_active_for: "Active pour",
    rule_covers_count: "volet(s)",
    rule_inactive: "Non remplie",
    master_enabled: "Automatisation",
    master_enabled_hint: "Les protections de verrouillage et d'aération ainsi que les règles de sécurité restent actives même lorsque l'automatisation est désactivée.",
    log_time: "Heure",
    log_event: "Événement",
    log_cover: "Volet",
    cover_show_log: "Voir le journal de ce volet",
    log_message: "Détails",
    log_type_position: "Position",
    log_type_status: "Statut",
    log_type_rule: "Règle",
    log_type_wind: "Vent",
    log_loading: "Chargement du journal...",
    log_empty: "Aucune entrée de journal sur les 3 derniers jours.",
    log_filter_all: "Tout",
    log_filter_cover: "Volet :",
    log_filter_all_covers: "Tous les volets",
    log_filter_cover_note: "Les événements globaux (vent) sont aussi affichés.",
    log_clear: "Vider le journal",
    log_clear_confirm: "Supprimer toutes les entrées du journal ?",
    log_clear_confirm_all: "Vider tout le journal (tous les volets) ?",
    settings_section_backup: "Sauvegarde",
    settings_backup_hint: "Exporte l'ensemble de la configuration dans un fichier JSON. L'import remplace tous les paramètres, volets, façades, règles et scénarios.",
    settings_export: "Exporter la configuration",
    settings_import: "Importer la configuration",
    settings_import_confirm: "La configuration entière va être remplacée. Continuer ?",
    settings_import_success: "Configuration importée avec succès.",
    settings_import_error: "Échec de l'import",
    settings_export_error: "Échec de l'export",
    settings_unsaved_confirm: "Abandonner les réglages non enregistrés ?",
    settings_unsaved_warning: "Des réglages ont été modifiés sans être enregistrés : ils ne sont pas dans l'export.",
    settings_export_unsaved_confirm: "Des réglages ont été modifiés sans être enregistrés. Les enregistrer avant l'export ?",
    settings_save_and_export: "Enregistrer et exporter",
  }
};

/* ============================================================
 * Condition type metadata
 * ============================================================ */
const CONDITION_TYPES = [
  "sun_on_facade", "sun_elevation_above", "sun_elevation_below",
  "temperature_above", "temperature_below", "temperature_comfort", "outdoor_vs_indoor",
  "room_occupied",
  "time_between", "time_after_sunrise", "time_after_sunset",
  "time_before_sunrise", "time_before_sunset",
  "time_after_dawn", "time_before_dawn", "time_after_dusk", "time_before_dusk",
  "state_is", "numeric_state", "weather_is", "day_of_week", "workday"
];

const CONDITION_PARAMS = {
  sun_on_facade: [],
  sun_elevation_above: [{ key: "elevation", type: "number", default: 10, step: 0.5 }],
  sun_elevation_below: [{ key: "elevation", type: "number", default: 60, step: 0.5 }],
  temperature_above: [{ key: "temperature", type: "number", default: 25 }],
  temperature_below: [{ key: "temperature", type: "number", default: 15 }],
  temperature_comfort: [{ key: "mode", type: "select", options: ["heating", "neutral", "cooling"], default: "cooling" }],
  outdoor_vs_indoor: [
    { key: "operator", type: "select", options: ["cooler", "warmer"], default: "cooler" },
    { key: "delta", type: "number", default: 0, step: 0.5 }
  ],
  room_occupied: [],
  time_between: [
    { key: "start_time", type: "time", default: "08:00" },
    { key: "end_time", type: "time", default: "20:00" }
  ],
  time_after_sunrise: [{ key: "offset", type: "number", default: 0 }],
  time_after_sunset: [{ key: "offset", type: "number", default: 0 }],
  time_before_sunrise: [{ key: "offset", type: "number", default: 0 }],
  time_before_sunset: [{ key: "offset", type: "number", default: -60 }],
  time_after_dawn: [{ key: "offset", type: "number", default: 0 }],
  time_before_dawn: [{ key: "offset", type: "number", default: 0 }],
  time_after_dusk: [{ key: "offset", type: "number", default: 0 }],
  time_before_dusk: [{ key: "offset", type: "number", default: 0 }],
  state_is: [
    { key: "entity_id", type: "entity", default: "" },
    { key: "state", type: "text", default: "on" }
  ],
  numeric_state: [
    { key: "entity_id", type: "entity", default: "" },
    { key: "operator", type: "select", options: ["above", "below"], default: "above" },
    { key: "value", type: "number", default: 0 },
    { key: "hysteresis", type: "number", default: 0, step: 0.1 }
  ],
  weather_is: [{ key: "weather", type: "multiselect", options: ["sunny", "clear-night", "partlycloudy", "cloudy", "fog", "rainy", "pouring", "lightning", "lightning-rainy", "hail", "snowy", "snowy-rainy", "windy", "windy-variant", "exceptional"], default: ["sunny"] }],
  day_of_week: [{ key: "days", type: "dayselect", default: ["mon","tue","wed","thu","fri"] }],
  workday: [{ key: "state", type: "select", options: ["on", "off"], default: "on" }]
};

// "Add condition" menu, grouped by theme. The legacy "state_is" and
// "numeric_state" types are no longer offered (existing ones keep working and
// can be converted): the "Entités" group creates native HA conditions.
const CONDITION_MENU = [
  { label: "cond_group_sun", items: ["sun_on_facade", "sun_elevation_above", "sun_elevation_below"].map(t => ({ value: t, label: "cond_" + t })) },
  { label: "cond_group_temperature", items: ["temperature_above", "temperature_below", "temperature_comfort", "outdoor_vs_indoor"].map(t => ({ value: t, label: "cond_" + t })) },
  { label: "cond_group_presence", items: [{ value: "room_occupied", label: "cond_room_occupied" }] },
  { label: "cond_group_time", items: ["time_between", "time_after_dawn", "time_before_dawn", "time_after_sunrise", "time_before_sunrise", "time_after_sunset", "time_before_sunset", "time_after_dusk", "time_before_dusk", "day_of_week", "workday"].map(t => ({ value: t, label: "cond_" + t })) },
  { label: "cond_group_weather", items: [{ value: "weather_is", label: "cond_weather_is" }] },
  { label: "cond_group_entities", items: [
    { value: "ha:state", label: "cond_menu_ha_state" },
    { value: "ha:numeric", label: "cond_menu_ha_numeric" },
    { value: "ha:yaml", label: "cond_menu_ha_yaml" },
  ] },
];

// Condition types that depend on a cover/facade context and cannot be
// evaluated in the editor preview (mirrors engine _CONTEXT_DEPENDENT_TYPES).
const CONTEXT_DEPENDENT_TYPES = ["sun_on_facade", "temperature_comfort", "outdoor_vs_indoor", "room_occupied"];

const FACADE_PRESETS = {
  north: { start: 315, end: 45 },
  east: { start: 45, end: 135 },
  south: { start: 135, end: 225 },
  west: { start: 225, end: 315 }
};

const DIRECTION_ARROWS = {
  north: "\u2191",
  east: "\u2192",
  south: "\u2193",
  west: "\u2190"
};

/* ============================================================
 * Styles
 * ============================================================ */
const PANEL_STYLES = `
  :host {
    display: block;
    font-family: var(--paper-font-body1_-_font-family, Roboto, Noto, sans-serif);
    color: var(--primary-text-color, #212121);
    background: var(--primary-background-color, #fafafa);
    --ca-primary: var(--primary-color, #03a9f4);
    /* Semantic role aliases (do not change values, just clarify intent at call site):
       --ca-action  = interactive UI (buttons, tabs, toggles, links) -> follows HA theme primary
       --ca-active  = "this is running right now" status (active rule, active scenario) -> green
       --ca-warning = transient warning (paused, threshold exceeded) -> orange
       --ca-danger  = blocked/protective state (locked, wind protection) -> red
       --ca-info    = neutral info / cool indicator (manual, venting, cooling) -> blue */
    --ca-action: var(--ca-primary);
    --ca-active: var(--ca-success-strong, #4caf50);
    --ca-card-bg: var(--ha-card-background, var(--card-background-color, #fff));
    --ca-border: var(--divider-color, #e0e0e0);
    --ca-box-border: color-mix(in srgb, var(--primary-text-color, #212121) 25%, transparent);
    --ca-sep: color-mix(in srgb, var(--primary-text-color, #212121) 45%, transparent);
    --ca-secondary-text: var(--secondary-text-color, #727272);
    --ca-error: var(--error-color, #db4437);
    --ca-success: var(--success-color, #43a047);
    --ca-success-strong: #4caf50;
    --ca-warning: var(--warning-color, #e67e22);
    --ca-info: var(--info-color, #2196f3);
    --ca-danger: var(--state-icon-error-color, #c62828);
    --ca-danger-bg: #fce4ec;
    --ca-sun: var(--ca-sun-color, #f9a825);
    --ca-sun-outline: var(--ca-sun-outline-color, #F57F17);
    --ca-radius: 12px;
    --ca-shadow: 0 2px 8px rgba(0,0,0,0.08);
    --ca-transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }
  *, *::before, *::after { box-sizing: border-box; }

  /* Layout */
  .panel-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 16px;
  }

  /* Header */
  .menu-btn {
    display: none;
    background: none;
    border: none;
    color: var(--primary-text-color);
    cursor: pointer;
    padding: 8px;
    margin: -8px 4px -8px -8px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .menu-btn:hover { background: rgba(128,128,128,0.2); }
  .menu-btn svg { display: block; }
  @media (max-width: 870px) {
    .menu-btn { display: flex; align-items: center; justify-content: center; }
  }
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0 8px;
    margin-bottom: 8px;
    gap: 12px;
  }
  .panel-header h1 {
    font-size: 24px;
    font-weight: 500;
    margin: 0;
    letter-spacing: -0.5px;
  }
  .header-left {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
  }
  .info-bar-slot { display: contents; }
  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  .info-bar {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--ca-secondary-text);
    flex-wrap: wrap;
  }
  .info-widget {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--primary-text-color) 6%, transparent);
    border: 1px solid color-mix(in srgb, var(--primary-text-color) 8%, transparent);
    white-space: nowrap;
    line-height: 1.3;
    transition: background var(--ca-transition), border-color var(--ca-transition), color var(--ca-transition);
  }
  .info-widget:hover {
    background: color-mix(in srgb, var(--primary-text-color) 10%, transparent);
  }
  .info-widget-value {
    color: var(--primary-text-color);
    font-weight: 500;
  }
  .info-widget.info-widget-highlight {
    background: color-mix(in srgb, var(--ca-warning) 18%, transparent);
    border-color: color-mix(in srgb, var(--ca-warning) 40%, transparent);
    color: var(--ca-warning);
  }
  .info-widget.info-widget-highlight .info-widget-value {
    color: var(--ca-warning);
    font-weight: 600;
  }
  .info-bar-icon {
    flex-shrink: 0;
  }
  .sun-icon-svg {
    color: var(--ca-sun);
    vertical-align: -2px;
  }
  .scenario-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--ca-primary);
    color: #fff;
    padding: 4px 14px;
    border-radius: 16px;
    font-size: 13px;
    font-weight: 500;
  }
  .scenario-badge-icon {
    --mdc-icon-size: 16px;
    margin-right: 4px;
  }
  .version-info {
    font-size: 12px;
    color: var(--ca-secondary-text);
    opacity: 0.7;
    margin-left: 8px;
    text-decoration: none;
  }
  a.version-info:hover {
    opacity: 1;
    text-decoration: underline;
  }
  .update-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #4CAF50;
    color: #fff;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    margin-left: 8px;
  }
  .update-badge:hover { opacity: 0.85; }

  /* Tabs */
  .tab-bar {
    display: flex;
    gap: 2px;
    border-bottom: 2px solid var(--ca-border);
    margin-bottom: 20px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scroll-snap-type: x proximity;
  }
  .tab-bar button {
    scroll-snap-align: start;
    flex: 0 0 auto;
    background: none;
    border: none;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
    color: var(--ca-secondary-text);
    cursor: pointer;
    position: relative;
    transition: color var(--ca-transition);
    white-space: nowrap;
    font-family: inherit;
  }
  .tab-bar button:hover { color: var(--primary-text-color); }
  .tab-bar button.active {
    color: var(--ca-primary);
  }
  .tab-bar button.active::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--ca-primary);
    border-radius: 2px 2px 0 0;
  }

  /* Cards */
  .card {
    background: var(--ca-card-bg);
    border-radius: var(--ca-radius);
    box-shadow: var(--ca-shadow);
    border: 1px solid var(--ca-border);
    overflow: hidden;
    transition: box-shadow var(--ca-transition);
  }
  .card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
  .card-header {
    padding: 16px 20px;
    font-weight: 500;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  .card-body { padding: 0 20px 20px; }

  /* Card grid */
  .card-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  /* Table */
  .table-scroll {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .data-table {
    width: 100%;
    border-collapse: collapse;
  }
  .data-table td.last-change {
    font-size: 12px;
    color: var(--ca-secondary-text);
    white-space: nowrap;
  }
  /* Inline rule link inside cover table -- jumps to Rules tab and highlights the rule */
  .data-table .rule-link {
    color: var(--ca-action);
    text-decoration: none;
    border-bottom: 1px dashed color-mix(in srgb, var(--ca-action) 40%, transparent);
    cursor: pointer;
    transition: color var(--ca-transition), border-bottom-color var(--ca-transition);
  }
  .data-table .rule-link:hover,
  .data-table .rule-link:focus-visible {
    color: var(--ca-action);
    border-bottom-color: var(--ca-action);
    outline: none;
  }
  .data-table th.row-chevron-head {
    width: 24px;
    padding-left: 0;
    padding-right: 12px;
  }
  .data-table th, .data-table td {
    text-align: left;
    padding: 12px 16px;
    border-bottom: 1px solid var(--ca-border);
  }
  .data-table th {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--ca-secondary-text);
    background: var(--ca-card-bg);
    position: sticky;
    top: 0;
    z-index: 1;
    white-space: nowrap;
  }
  .data-table th.sortable {
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }
  .data-table th.sortable:hover {
    color: var(--primary-text-color);
  }
  /* Keyboard focus for row/header activation (tabindex targets) */
  .data-table th.sortable:focus-visible,
  .data-table tr[data-action]:focus-visible {
    outline: 2px solid var(--ca-primary);
    outline-offset: -2px;
  }
  .data-table th .sort-arrow {
    display: inline-block;
    margin-left: 4px;
    font-size: 10px;
    opacity: 0;
    color: var(--ca-primary);
    transition: opacity var(--ca-transition);
  }
  .data-table th.sortable:hover .sort-arrow {
    opacity: 0.35;
    color: var(--ca-secondary-text);
  }
  .data-table th.sorted .sort-arrow {
    opacity: 1;
    color: var(--ca-primary);
  }
  .data-table tr {
    cursor: pointer;
    transition: background var(--ca-transition);
  }
  .data-table tbody tr:hover {
    background: color-mix(in srgb, var(--ca-primary) 10%, transparent);
  }
  .data-table tbody tr.selected {
    background: color-mix(in srgb, var(--ca-primary) 16%, transparent);
  }
  .data-table td.row-chevron {
    width: 24px;
    padding-left: 8px;
    padding-right: 12px;
    text-align: right;
    color: var(--ca-secondary-text);
    opacity: 0.35;
    transition: opacity var(--ca-transition), transform var(--ca-transition), color var(--ca-transition);
  }
  .data-table tbody tr:hover td.row-chevron {
    opacity: 1;
    transform: translateX(2px);
    color: var(--ca-primary);
  }
  .data-table td.row-chevron svg {
    display: block;
    margin-left: auto;
  }

  /* Status badge */
  .status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 500;
    text-transform: capitalize;
  }
  .status-auto {
    background: color-mix(in srgb, var(--ca-active) 14%, transparent);
    color: var(--ca-active);
  }
  .status-paused {
    background: color-mix(in srgb, var(--ca-warning) 16%, transparent);
    color: var(--ca-warning);
  }
  .status-manual {
    background: color-mix(in srgb, var(--ca-info) 14%, transparent);
    color: var(--ca-info);
  }
  .status-locked {
    background: color-mix(in srgb, var(--ca-danger) 14%, transparent);
    color: var(--ca-danger);
  }
  .status-venting {
    background: color-mix(in srgb, var(--ca-info) 12%, transparent);
    color: var(--ca-info);
  }
  .status-wind_protected {
    background: color-mix(in srgb, var(--ca-danger) 14%, transparent);
    color: var(--ca-danger);
  }

  /* Slide-out panel */
  .slide-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.3);
    z-index: 100;
    opacity: 0;
    visibility: hidden;
    transition: opacity var(--ca-transition), visibility var(--ca-transition);
  }
  .slide-overlay.open { opacity: 1; visibility: visible; }
  .slide-panel {
    position: fixed;
    top: 0;
    right: 0;
    width: 420px;
    max-width: 100vw;
    height: 100%;
    background: var(--primary-background-color, #1c1c1c);
    z-index: 101;
    transform: translateX(100%);
    transition: transform var(--ca-transition);
    display: flex;
    flex-direction: column;
    box-shadow: -4px 0 24px rgba(0,0,0,0.15);
  }
  .slide-panel.open { transform: translateX(0); }
  .slide-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid var(--ca-border);
    flex-shrink: 0;
  }
  .slide-header .slide-back { display: none; }
  /* Cover sheet: the help icon sits on the label line instead of its own line */
  .slide-body .form-group { position: relative; }
  .slide-body .form-group > .field-hint > summary { position: absolute; top: 0; right: 0; }
  .slide-body .form-group:has(> .field-hint) > label { padding-right: 24px; }
  .slide-body .sep-item, .slide-body .threshold-entity, .slide-body .opt-box { position: relative; }
  .slide-body .sep-item > .field-hint > summary,
  .slide-body .threshold-entity > .field-hint > summary { position: absolute; top: 0; right: 0; }
  .slide-body .opt-box-body > .field-hint > summary { position: absolute; top: 12px; right: 14px; }
  .toggle-row .toggle-label { display: block; flex: 1; min-width: 0; }
  .toggle-row .toggle-label .field-hint { display: inline; margin: 0 0 0 2px; }
  .toggle-row .toggle-label .field-hint > summary { display: inline-flex; vertical-align: middle; padding: 0 4px; }
  .toggle-row .toggle-label .field-hint[open] .hint-body { display: block; }
  .lbl-short { display: none; }
  @media (max-width: 600px) {
    .lbl-long { display: none; }
    .lbl-short { display: inline; }
  }
  .slide-expand-bar { display: flex; justify-content: flex-end; margin: -8px 0 4px; }
  .slide-header .btn-icon:focus:not(:focus-visible) { outline: none; }
  .slide-close-bottom { display: none; }
  .slide-header h2 {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin: 0;
    font-size: 18px;
    font-weight: 500;
  }
  .slide-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  /* Form elements */
  .form-group {
    margin-bottom: 16px;
  }
  .form-group label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--ca-secondary-text);
    margin-bottom: 4px;
  }
  .form-group input[type="text"],
  .form-group input[type="number"],
  .form-group input[type="time"],
  .form-group select,
  .form-group textarea {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--ca-border);
    border-radius: 8px;
    background: var(--primary-background-color, #fafafa);
    color: var(--primary-text-color);
    font-size: 14px;
    font-family: inherit;
    outline: none;
    transition: border-color var(--ca-transition);
  }
  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    border-color: var(--ca-primary);
  }
  .form-group input.input-invalid,
  input.input-invalid {
    border-color: var(--ca-danger);
    box-shadow: 0 0 0 1px var(--ca-danger);
  }
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    align-items: start;
  }

  /* Settings shell: sidebar + content */
  .settings-shell {
    display: flex;
    gap: 24px;
    align-items: flex-start;
  }
  .settings-nav {
    flex: 0 0 220px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    position: sticky;
    top: 16px;
    padding: 8px;
    background: var(--ca-card-bg);
    border: 1px solid var(--ca-border);
    border-radius: var(--ca-radius);
  }
  .settings-nav-btn {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: var(--ca-secondary-text);
    font-size: 14px;
    font-family: inherit;
    font-weight: 500;
    cursor: pointer;
    text-align: left;
    transition: background var(--ca-transition), color var(--ca-transition);
  }
  .settings-nav-btn:hover {
    background: color-mix(in srgb, var(--primary-text-color) 6%, transparent);
    color: var(--primary-text-color);
  }
  .settings-nav-btn.active {
    background: color-mix(in srgb, var(--ca-primary) 14%, transparent);
    color: var(--ca-primary);
  }
  .settings-nav-btn .settings-nav-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
  .settings-nav-btn .settings-nav-icon svg {
    width: 18px;
    height: 18px;
  }
  .settings-nav-btn .settings-nav-label {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .settings-content {
    flex: 1;
    min-width: 0;
  }

  /* Settings card stack */
  .settings-stack {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .settings-stack .card-header {
    font-size: 13px;
    font-weight: 600;
    color: var(--ca-secondary-text);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 12px 20px 8px;
    border-bottom: 1px solid var(--ca-border);
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
  }
  .settings-stack .card-header svg {
    flex-shrink: 0;
    opacity: 0.7;
  }
  /* Hint text below a field (legacy, still used in a few places) */
  .settings-hint {
    font-size: 12px;
    color: var(--ca-secondary-text);
    margin-top: 4px;
    line-height: 1.4;
  }
  /* Intro hint at top of a card section */
  .settings-hint-intro {
    font-size: 12px;
    color: var(--ca-secondary-text);
    margin-bottom: 12px;
    line-height: 1.4;
  }
  /* Field-level collapsible hint */
  .field-hint {
    margin-top: 4px;
  }
  .field-hint summary {
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 6px;
    border-radius: 6px;
    color: var(--ca-secondary-text);
    list-style: none;
    user-select: none;
    transition: background var(--ca-transition), color var(--ca-transition);
  }
  .field-hint summary::-webkit-details-marker { display: none; }
  .field-hint summary::marker { content: ""; }
  .field-hint summary:hover {
    background: color-mix(in srgb, var(--primary-text-color) 8%, transparent);
    color: var(--ca-primary);
  }
  .field-hint[open] summary {
    color: var(--ca-primary);
  }
  .field-hint .hint-body {
    padding: 8px 10px;
    margin-top: 4px;
    background: color-mix(in srgb, var(--primary-text-color) 4%, transparent);
    border-left: 2px solid color-mix(in srgb, var(--ca-primary) 50%, transparent);
    border-radius: 4px;
    font-size: 12px;
    color: var(--ca-secondary-text);
    line-height: 1.5;
  }
  /* Sensor live value */
  .sensor-current-value {
    font-size: 12px;
    color: var(--ca-primary);
    margin-top: 3px;
  }
  /* Optional entity providing a threshold (number = fallback) */
  input.entity-driven { display: none; }
  .entity-shadow-value {
    padding: 10px 12px; border-radius: 8px; font-size: 14px;
    border: 1px solid var(--ca-border);
    background: color-mix(in srgb, var(--primary-text-color, #212121) 6%, transparent);
    color: var(--ca-secondary-text);
    max-width: 200px;
  }
  .entity-shadow-note { font-size: 12px; color: var(--ca-secondary-text); margin-top: 4px; }
  .threshold-entity {
    margin-top: 10px;
    padding-left: 10px;
    border-left: 2px solid var(--ca-border);
  }
  .threshold-entity-label {
    font-size: 12px;
    color: var(--ca-secondary-text);
    margin-bottom: 4px;
  }
  .threshold-entity-value {
    font-size: 12px;
    color: var(--ca-primary);
    margin-top: 4px;
    min-height: 0;
  }
  .threshold-entity-value:empty { display: none; }
  .threshold-entity-unavail { color: var(--ca-warning, var(--ca-secondary-text)); }

  /* Settings page: roomier layout (settings tab only) */
  .settings-stack { gap: 20px; }
  .settings-stack .card-header {
    font-size: 15px;
    font-weight: 600;
    color: var(--primary-text-color);
    text-transform: none;
    letter-spacing: 0;
    padding: 16px 24px 14px;
    margin-bottom: 0;
  }
  .settings-stack .card-header svg { color: var(--ca-primary); opacity: 1; }
  .settings-stack .card-body { padding: 20px 24px 24px; }
  .settings-stack .form-group { margin-bottom: 24px; }
  .settings-stack .card-body > .form-group:last-child,
  .settings-stack .card-body > .form-row:last-child { margin-bottom: 0; }
  .settings-stack .form-row > .form-group { margin-bottom: 0; }
  .settings-stack .form-group > label:not(.checkbox-row) { margin-bottom: 6px; }
  .settings-stack .form-row {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 24px 28px;
    margin-bottom: 24px;
  }
  .settings-stack .form-group input[type="number"] { max-width: 220px; }
  .settings-stack .form-group select,
  .settings-stack .form-group input[type="text"] { max-width: 480px; }
  .settings-stack .settings-hint { margin-top: 6px; line-height: 1.5; }
  .settings-stack .field-hint { margin-top: 6px; }
  .settings-stack .settings-hint-intro {
    font-size: 13px;
    line-height: 1.55;
    margin-bottom: 24px;
    padding: 10px 14px;
    border-radius: 8px;
    border-left: 3px solid color-mix(in srgb, var(--ca-primary) 55%, transparent);
    background: color-mix(in srgb, var(--ca-primary) 6%, transparent);
  }
  .settings-stack .sensor-current-value { margin-top: 6px; }
  .settings-stack .checkbox-row {
    font-size: 14px;
    text-transform: none;
    letter-spacing: 0;
    color: var(--primary-text-color);
    margin-bottom: 0;
  }
  .settings-stack .checkbox-row input { width: 18px; height: 18px; margin: 0; }
  .settings-save-bar { padding-top: 4px; }
  .pos-inverted { display: inline-flex; align-items: center; gap: 4px; }
  .pos-inverted-mark { font-size: 12px; color: var(--secondary-text-color, #727272); cursor: help; }
  .radio-group { display: flex; flex-direction: column; gap: 10px; margin-top: 6px; }
  .form-group .radio-row, .form-group .radio-row * { text-transform: none; letter-spacing: normal; }
  .form-group .radio-row { display: flex; align-items: flex-start; gap: 10px; cursor: pointer; font-weight: normal; font-size: 14px; color: var(--primary-text-color); margin: 0; }
  .form-group .radio-row b { font-weight: 500; }
  .radio-row input { margin-top: 3px; width: 16px; height: 16px; flex: none; }
  .sun-explain { margin-top: 12px; border: 1px solid var(--ca-box-border); border-radius: 8px; }
  .sun-explain summary { cursor: pointer; padding: 8px 12px; font-size: 13px; font-weight: 500; color: var(--primary-color); }
  .sun-explain-body { padding: 0 12px 12px; }
  .sun-explain-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }
  .sun-explain-table th { text-align: left; font-weight: 500; font-size: 12px; color: var(--secondary-text-color, #727272); padding: 6px 8px; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
  .sun-explain-table td { padding: 6px 8px; vertical-align: top; border-bottom: 1px solid var(--divider-color, #e0e0e0); color: var(--primary-text-color); }
  .sun-explain-table tr.current td { background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.12); }
  .sun-explain-table tr.current td:first-child { box-shadow: inset 3px 0 0 var(--primary-color); font-weight: 500; }
  .sun-explain-so { margin-top: 10px; font-size: 13px; color: var(--primary-text-color); }
  .sun-explain-so ul { margin: 4px 0 0; padding-left: 20px; }
  .sun-explain-so li { margin: 3px 0; line-height: 1.45; }
  .radio-hint { font-size: 12px; color: var(--secondary-text-color, #727272); font-weight: normal; text-transform: none; letter-spacing: normal; }
  .opt-box { border: 1px solid var(--ca-box-border); border-radius: 10px; padding: 12px 14px; margin: 0 0 14px;
    background: color-mix(in srgb, var(--primary-text-color, #212121) 2%, transparent); }
  .opt-box > .opt-box-title { padding-bottom: 8px; border-bottom: 1px solid var(--ca-box-border); }
  .sep-list > * + * { border-top: 1px solid var(--ca-sep); margin-top: 12px; padding-top: 12px; }
  .opt-box > .form-group:last-child, .opt-box > .form-row:last-child .form-group { margin-bottom: 0; }
  .sep-list > .form-group:last-child, .sep-list > .sep-item > .form-group:last-child { margin-bottom: 0; }
  .opt-box .opt-box { margin: 10px 0 0; }
  .opt-box.opt-box-flat { border: 0; padding: 0; margin: 0; background: none; }
  .opt-box.opt-box-nested { margin: 8px 0 4px 26px; background: var(--ca-card-bg); }
  .opt-box-body > .form-group:last-child, .opt-box-body > .form-row:last-child .form-group { margin-bottom: 0; }
  .opt-box-title { font-weight: 600; margin-bottom: 10px; }
  .opt-box-offnote { display: none; font-size: 12px; color: var(--secondary-text-color, #727272); margin: 2px 0 8px; font-style: italic; }
  .opt-box.opt-off > .opt-box-offnote { display: block; }
  .opt-box.opt-off > .opt-box-body { opacity: 0.45; }
  /* Only the outermost disabled box fades and explains why */
  .opt-box.opt-off .opt-box.opt-off > .opt-box-body { opacity: 1; }
  .opt-box.opt-off .opt-box .opt-box-offnote { display: none; }
  .opt-box.opt-off > .opt-box-body * { cursor: not-allowed; }
  .settings-unsaved-warning { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; padding: 8px 12px; border-radius: 8px; background: rgba(255, 152, 0, 0.12); color: var(--warning-color, #ff9800); }
  .settings-unsaved-warning .btn { margin-left: auto; }

  /* House card: rotation input + compass side by side */
  .settings-house-layout {
    display: flex;
    gap: 24px;
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .settings-house-input {
    flex: 1;
    min-width: 160px;
  }
  .settings-house-compass {
    flex: 0 0 auto;
  }
  /* Quick rotate buttons next to the rotation input */
  .rotation-quick {
    display: flex;
    gap: 6px;
    margin-top: 8px;
    flex-wrap: wrap;
  }
  .rotation-quick-btn {
    background: color-mix(in srgb, var(--primary-text-color) 5%, transparent);
    border: 1px solid color-mix(in srgb, var(--primary-text-color) 10%, transparent);
    color: var(--primary-text-color);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
    cursor: pointer;
    font-family: inherit;
    transition: background var(--ca-transition), border-color var(--ca-transition), color var(--ca-transition);
  }
  .rotation-quick-btn:hover {
    background: color-mix(in srgb, var(--ca-action) 12%, transparent);
    border-color: color-mix(in srgb, var(--ca-action) 35%, transparent);
    color: var(--ca-action);
  }
  .rotation-quick-btn.rotation-quick-reset {
    color: var(--ca-secondary-text);
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.6px;
  }
  /* House SVG: ensure the house group has a proper drag affordance */
  #compass-house { transition: filter var(--ca-transition); cursor: grab; touch-action: none; }
  #compass-house:hover rect { stroke-width: 2; }
  /* Save action bar below all config cards */
  .settings-save-bar {
    display: flex;
    justify-content: flex-end;
  }
  /* Backup button row */
  .settings-backup-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  /* Inline checkbox label (icon + text on one row) */
  .checkbox-row {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
  }

  /* Position bar */
  .pos-bar {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-width: 90px;
  }
  .pos-bar-track {
    width: 60px;
    height: 6px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    overflow: hidden;
    flex-shrink: 0;
    outline: 1px solid rgba(255,255,255,0.15);
    position: relative;
  }
  .pos-bar-fill {
    display: block;
    height: 100%;
    border-radius: 3px;
    background: #5bb8f5;
    transition: width 0.3s ease;
  }
  .pos-bar-label {
    font-size: 12px;
    min-width: 32px;
  }
  .pos-bar.pos-bar-diverges {
    min-width: 110px;
  }
  .pos-bar.pos-bar-diverges .pos-bar-track {
    width: 70px;
  }
  .pos-bar-range {
    position: absolute;
    top: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      135deg,
      var(--ca-primary) 0,
      var(--ca-primary) 3px,
      transparent 3px,
      transparent 6px
    );
    opacity: 0.7;
    pointer-events: none;
    transition: left var(--ca-transition), width var(--ca-transition);
  }
  .pos-bar-diverges .pos-bar-label {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 11px;
    min-width: 0;
  }
  .pos-bar-diverges .pos-bar-current-val {
    color: var(--primary-text-color);
    font-weight: 500;
  }
  .pos-bar-diverges .pos-bar-arrow,
  .pos-bar-diverges .pos-bar-target-val {
    color: var(--ca-primary);
    font-weight: 600;
  }
  .data-table .pos-cell {
    white-space: nowrap;
  }
  .pos-bar.pos-bar-compact {
    min-width: 0;
    gap: 6px;
    vertical-align: middle;
  }
  .pos-bar.pos-bar-compact .pos-bar-track {
    width: 44px;
    height: 4px;
  }
  .pos-bar.pos-bar-compact .pos-bar-label {
    font-size: 11px;
    min-width: 0;
    color: var(--ca-secondary-text);
  }
  .rule-meta .rule-target {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .resume-x {
    display: inline;
    font-size: 13px;
    padding: 2px 4px;
    margin-left: 2px;
    vertical-align: middle;
    color: var(--ca-secondary-text);
    background: none;
    border: none;
    cursor: pointer;
    line-height: 1;
  }
  .resume-x:hover {
    color: #e65100;
  }

  /* Inline live-update elements in covers table */
  .pause-remaining {
    font-size: 11px;
    color: var(--ca-secondary-text);
    margin-left: 4px;
  }
  .hysteresis-badge {
    font-size: 11px;
    margin-left: 4px;
    vertical-align: middle;
  }
  .live-icon {
    font-size: 12px;
    margin-left: 2px;
  }
  .live-icon-sun {
    font-size: 14px;
    margin-left: 4px;
    color: var(--ca-sun);
  }

  /* Toggle switch */
  .toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
  }
  .toggle-row span { font-size: 14px; }
  .toggle {
    position: relative;
    width: 44px;
    height: 24px;
    flex-shrink: 0;
  }
  .toggle input {
    opacity: 0;
    width: 0;
    height: 0;
    position: absolute;
  }
  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background: var(--ca-border);
    border-radius: 12px;
    transition: background var(--ca-transition);
  }
  .toggle-slider::before {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    left: 3px;
    bottom: 3px;
    background: #fff;
    border-radius: 50%;
    transition: transform var(--ca-transition);
  }
  .toggle input:checked + .toggle-slider {
    background: var(--ca-primary);
  }
  .toggle input:checked + .toggle-slider::before {
    transform: translateX(20px);
  }

  /* Master switch in header */
  .master-switch {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: default;
  }
  .master-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--ca-secondary-text);
    user-select: none;
  }
  .master-toggle {
    position: relative;
    width: 44px;
    height: 24px;
    flex-shrink: 0;
    cursor: pointer;
  }
  .master-toggle input {
    opacity: 0;
    width: 0;
    height: 0;
    position: absolute;
  }
  .master-toggle .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background: var(--ca-border);
    border-radius: 12px;
    transition: background var(--ca-transition);
  }
  .master-toggle .toggle-slider::before {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    left: 3px;
    bottom: 3px;
    background: #fff;
    border-radius: 50%;
    transition: transform var(--ca-transition);
  }
  .master-toggle input:checked + .toggle-slider {
    background: var(--ca-primary);
  }
  .master-toggle input:checked + .toggle-slider::before {
    transform: translateX(20px);
  }

  /* Section */
  .section {
    margin-bottom: 8px;
    border-top: 1px solid var(--ca-sep);
  }
  .section:first-child {
    border-top: none;
  }
  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 0 10px;
    cursor: pointer;
    user-select: none;
    font-size: 14px;
    font-weight: 600;
    color: var(--primary-text-color);
    letter-spacing: 0.2px;
  }
  .section-header:hover {
    color: var(--ca-primary);
  }
  .section-header .section-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: color-mix(in srgb, var(--ca-primary) 12%, transparent);
    color: var(--ca-primary);
    flex-shrink: 0;
  }
  .section-header .section-title {
    flex: 1;
    min-width: 0;
  }
  .section-header .section-summary {
    display: block;
    margin-top: 2px;
    font-size: 12px;
    font-weight: normal;
    letter-spacing: normal;
    color: var(--ca-secondary-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .section-header .arrow {
    font-size: 10px;
    color: var(--ca-secondary-text);
    transition: transform var(--ca-transition);
    display: inline-block;
  }
  .section-header .arrow.expanded { transform: rotate(90deg); }
  .section-body {
    overflow: hidden;
    max-height: 0;
    transition: max-height 0.35s ease;
  }
  .section-body.expanded { max-height: 6000px; padding-bottom: 8px; }
  /* Cover sheet: the slide background is the page grey, so framed boxes
     take the card colour and a stronger border to stand out */
  .slide-body .opt-box:not(.opt-box-flat) {
    background: var(--ca-card-bg);
    border-color: color-mix(in srgb, var(--primary-text-color, #212121) 35%, transparent);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  }
  .slide-body .opt-box .opt-box:not(.opt-box-flat) { box-shadow: none; }

  /* Buttons */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--ca-transition);
    font-family: inherit;
  }
  .btn-primary {
    background: var(--ca-primary);
    color: #fff;
  }
  .btn-primary:hover { filter: brightness(1.1); }
  .btn-secondary {
    background: transparent;
    color: var(--ca-primary);
    border: 1px solid var(--ca-primary);
  }
  .btn-secondary:hover { background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08); }
  .btn-danger {
    background: transparent;
    color: var(--ca-error);
    border: 1px solid var(--ca-error);
  }
  .btn-danger:hover { background: rgba(219, 68, 55, 0.08); }
  .btn-icon {
    background: none;
    border: none;
    padding: 6px;
    cursor: pointer;
    color: var(--ca-secondary-text);
    font-size: 18px;
    border-radius: 50%;
    transition: all var(--ca-transition);
    line-height: 1;
    font-family: inherit;
  }
  .btn-icon:hover {
    background: rgba(0,0,0,0.06);
    color: var(--primary-text-color);
  }
  /* SVG icon buttons: drop the inline baseline gap */
  .btn-icon svg { display: block; }
  .btn-sm { padding: 4px 10px; font-size: 12px; }
  .btn-sm.active { background: var(--ca-primary); color: #fff; }

  /* Chips */
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
    color: var(--ca-primary);
    font-weight: 500;
  }
  .chip-group { display: flex; flex-wrap: wrap; gap: 6px; }

  /* Drag & drop */
  .drag-handle {
    cursor: grab;
    color: var(--ca-secondary-text);
    font-size: 16px;
    padding: 4px;
    user-select: none;
    line-height: 1;
  }
  .drag-handle:active { cursor: grabbing; }
  .rule-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border: 1px solid var(--ca-border);
    border-left: 3px solid transparent;
    border-radius: var(--ca-radius);
    margin-bottom: 8px;
    background: var(--ca-card-bg);
    transition: all var(--ca-transition);
  }
  .rule-row.rule-active {
    border-left-color: var(--ca-active);
    background: color-mix(in srgb, var(--ca-active) 6%, var(--ca-card-bg));
  }
  .rule-row:hover { box-shadow: var(--ca-shadow); }
  /* Pulsing highlight when a rule is opened from the cover table */
  .rule-row.rule-highlight {
    animation: ca-rule-pulse 1.6s ease-out;
  }
  @keyframes ca-rule-pulse {
    0%   { box-shadow: 0 0 0 0 color-mix(in srgb, var(--ca-action) 60%, transparent); }
    40%  { box-shadow: 0 0 0 6px color-mix(in srgb, var(--ca-action) 30%, transparent); }
    100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--ca-action) 0%, transparent); }
  }
  .rule-row.drag-over {
    border-color: var(--ca-primary);
    box-shadow: 0 0 0 2px rgba(var(--rgb-primary-color, 3, 169, 244), 0.3);
  }
  .rule-row.dragging { opacity: 0.4; }
  .rule-info { flex: 1; min-width: 0; }
  .rule-name { font-weight: 500; font-size: 15px; display: flex; align-items: center; gap: 6px; }
  .rule-active-dot {
    width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
    background: var(--ca-divider, #e0e0e0);
    transition: background 0.2s, box-shadow 0.2s;
  }
  .rule-active-dot.active { background: var(--ca-active); box-shadow: 0 0 6px color-mix(in srgb, var(--ca-active) 50%, transparent); }
  .rule-meta {
    font-size: 12px;
    color: var(--ca-secondary-text);
    margin-top: 2px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .rule-safety-badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 1px 7px 1px 5px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2px;
    color: var(--ca-danger);
    background: color-mix(in srgb, var(--ca-danger) 12%, transparent);
    border: 1px solid color-mix(in srgb, var(--ca-danger) 30%, transparent);
    white-space: nowrap;
  }
  .rule-safety-badge svg { flex-shrink: 0; }
  .rule-safety-group .toggle-row { margin-bottom: 0; }
  .priority-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 28px;
    padding: 2px 6px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.12);
    color: var(--ca-primary);
  }

  /* Inline editor for rules */
  .rule-editor {
    overflow: hidden;
    max-height: 0;
    transition: max-height 0.4s ease, padding 0.3s ease;
    padding: 0 16px;
  }
  .rule-editor.expanded {
    max-height: 2000px;
    padding: 16px;
    border-top: 1px solid var(--ca-border);
  }

  /* Condition card */
  .condition-card {
    background: var(--primary-background-color, #fafafa);
    border: 1px solid var(--ca-border);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    position: relative;
  }
  .condition-card .cond-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  .condition-card .cond-type {
    font-weight: 500;
    font-size: 13px;
    color: var(--ca-primary);
  }
  .condition-card .cond-params {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .condition-card .cond-params .form-group { margin-bottom: 0; }
  .cond-head-left { display: flex; align-items: center; gap: 8px; min-width: 0; flex-wrap: wrap; }
  .cond-preview {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 12px; color: var(--ca-secondary-text); white-space: nowrap;
  }
  .cond-preview-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--ca-border); flex-shrink: 0;
  }
  .cond-preview-on { color: var(--ca-text); }
  .cond-preview-on .cond-preview-dot { background: var(--ca-active, var(--ca-success-strong)); }
  .cond-preview-context { font-style: italic; opacity: 0.65; }
  .day-select { display: flex; gap: 4px; flex-wrap: wrap; }
  /* Native Home Assistant condition card */
  .ha-seg { display: inline-flex; border: 1px solid var(--ca-border); border-radius: 8px; overflow: hidden; margin: 8px 0 4px; }
  .ha-seg button { border: 0; background: var(--ca-card-bg); color: var(--ca-secondary-text); padding: 6px 14px; font: inherit; font-size: 13px; cursor: pointer; }
  .ha-seg button + button { border-left: 1px solid var(--ca-border); }
  .ha-seg button.on { background: var(--ca-primary); color: #fff; }
  .condition-card .cond-params.ha-params { grid-template-columns: 1fr; }
  .ha-params .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  textarea.ha-yaml { width: 100%; box-sizing: border-box; font: 13px/1.5 ui-monospace, Menlo, Consolas, monospace; padding: 10px 12px; border-radius: 8px; border: 1px solid var(--ca-border); background: var(--code-editor-background-color, #1e1e1e); color: var(--code-editor-color, #d4d4d4); resize: vertical; tab-size: 2; }
  .btn-link { background: none; border: 0; padding: 0 0 0 6px; color: var(--ca-primary); font: inherit; cursor: pointer; text-decoration: underline; }
  .ha-help { font-size: 12px; color: var(--ca-secondary-text); margin-top: 4px; }
  .ha-current { font-size: 12px; color: var(--ca-secondary-text); margin-top: 4px; }
  .ha-add-state { display: flex; gap: 8px; margin-top: 8px; max-width: 420px; }
  .ha-add-state input { flex: 1; }
  .ha-status { display: grid; gap: 6px; margin-top: 10px; }
  .ha-status:empty { display: none; }
  .ha-msg { font-size: 13px; padding: 6px 10px; border-radius: 6px; overflow-wrap: anywhere; }
  .ha-msg-ok { color: var(--ca-success); background: color-mix(in srgb, var(--ca-success) 12%, transparent); }
  .ha-msg-err { color: var(--ca-error); background: color-mix(in srgb, var(--ca-error) 12%, transparent); }
  .ha-msg-warn { color: var(--ca-warning); background: color-mix(in srgb, var(--ca-warning) 12%, transparent); }
  .ha-msg-info { color: var(--ca-secondary-text); background: color-mix(in srgb, var(--ca-secondary-text) 10%, transparent); }
  .ha-convert { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 8px 0 10px; }
  .chip.chip-error { color: var(--ca-error); background: color-mix(in srgb, var(--ca-error) 12%, transparent); }
  @media (max-width: 600px) { .ha-params .form-row { grid-template-columns: 1fr; } }
  .day-btn {
    padding: 4px 8px; border: 1px solid var(--ca-border); border-radius: 4px;
    background: var(--ca-card-bg); color: var(--ca-text); cursor: pointer;
    font-size: 13px; min-width: 36px; text-align: center;
    transition: background 0.15s, border-color 0.15s;
  }
  .day-btn:hover { border-color: var(--ca-primary); }
  .day-btn.selected { background: var(--ca-primary); color: #fff; border-color: var(--ca-primary); }

  /* Scenario card */
  .scenario-card {
    background: var(--ca-card-bg);
    border: 2px solid var(--ca-border);
    border-radius: var(--ca-radius);
    padding: 20px;
    transition: all var(--ca-transition);
  }
  .scenario-card.active-scenario {
    border-color: var(--ca-active);
    background: color-mix(in srgb, var(--ca-active) 6%, var(--ca-card-bg));
    box-shadow:
      0 0 0 2px color-mix(in srgb, var(--ca-active) 35%, transparent),
      0 4px 16px color-mix(in srgb, var(--ca-active) 18%, transparent);
  }
  .scenario-card.active-scenario .sc-name {
    color: var(--ca-active);
  }
  .scenario-card .sc-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .scenario-card .sc-name {
    font-weight: 500;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .scenario-card .sc-rules { margin-top: 12px; }
  .scenario-card .sc-rule-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid var(--ca-border);
    font-size: 14px;
  }
  .scenario-card .sc-rule-row:last-child { border-bottom: none; }
  .scenario-card .sc-rule-label { display: inline-flex; align-items: center; gap: 8px; min-width: 0; }
  .scenario-card .sc-rule-off .sc-rule-label > span:not(.sc-rule-off-badge),
  .scenario-card .sc-rule-off .priority-badge { opacity: 0.45; }
  .scenario-card .sc-rule-off .toggle { opacity: 0.55; }
  .sc-rule-off-badge { font-size: 11px; padding: 1px 8px; border-radius: 10px; color: var(--ca-secondary-text); border: 1px dashed var(--ca-border); white-space: nowrap; }

  /* Toast */
  .toast {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(80px);
    background: var(--ca-success);
    color: #fff;
    padding: 10px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    z-index: 200;
    opacity: 0;
    transition: all 0.3s ease;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    overflow: hidden;
  }
  .toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
  .toast-progress {
    position: absolute;
    left: 0;
    bottom: 0;
    height: 3px;
    width: 100%;
    background: rgba(255,255,255,0.55);
    transform: scaleX(0);
    transform-origin: left;
  }
  /* duration must match the timeout in _showToast() */
  .toast.show .toast-progress {
    animation: ca-toast-countdown 2s linear forwards;
  }
  .toast.toast-error {
    background: var(--error-color, #db4437);
  }
  .toast.toast-error.show .toast-progress {
    animation-duration: 5s;
  }
  @keyframes ca-toast-countdown {
    from { transform: scaleX(1); }
    to { transform: scaleX(0); }
  }

  /* Loading / Error */
  .state-msg {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 20px;
    text-align: center;
    color: var(--ca-secondary-text);
  }
  .spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--ca-border);
    border-top-color: var(--ca-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 16px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Add card */
  .add-card {
    border: 2px dashed var(--ca-border);
    border-radius: var(--ca-radius);
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 120px;
    cursor: pointer;
    transition: all var(--ca-transition);
    color: var(--ca-secondary-text);
    font-size: 15px;
    font-weight: 500;
    gap: 8px;
    background: transparent;
    width: 100%;
    font-family: inherit;
  }
  .add-card:hover {
    border-color: var(--ca-primary);
    color: var(--ca-primary);
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.04);
  }

  /* Inline form */
  .inline-form {
    background: var(--ca-card-bg);
    border: 2px solid var(--ca-primary);
    border-radius: var(--ca-radius);
    padding: 20px;
  }
  .inline-form .form-actions {
    display: flex;
    gap: 8px;
    margin-top: 16px;
    justify-content: flex-end;
  }

  /* Confirm dialog */
  .confirm-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.6);
    z-index: 300;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .confirm-dialog {
    background: var(--primary-background-color, #1c1c1c);
    border-radius: var(--ca-radius);
    padding: 24px;
    min-width: 300px;
    max-width: 90vw;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  }
  .confirm-dialog p {
    margin: 0 0 20px;
    font-size: 16px;
  }
  .confirm-dialog .actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  /* Multi-select */
  .multi-select {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 4px;
  }
  .multi-select .ms-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border: 1px solid var(--ca-border);
    border-radius: 16px;
    font-size: 13px;
    cursor: pointer;
    transition: all var(--ca-transition);
    background: transparent;
    color: var(--primary-text-color);
    font-family: inherit;
  }
  .multi-select .ms-item.selected {
    background: var(--ca-primary);
    color: #fff;
    border-color: var(--ca-primary);
  }
  .multi-select .ms-item:hover { border-color: var(--ca-primary); }

  /* Empty state */
  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: var(--ca-secondary-text);
    font-size: 14px;
  }

  /* Utilities */
  .nowrap { white-space: nowrap; }
  .mt-6 { margin-top: 6px; }
  .mt-8 { margin-top: 8px; }
  .mt-16 { margin-top: 16px; }
  .mb-12 { margin-bottom: 12px; }
  .mb-16 { margin-bottom: 16px; }

  /* State/error message icon */
  .state-msg-icon {
    font-size: 32px;
    margin-bottom: 12px;
  }

  /* Add-cover form */
  .add-cover-select {
    width: 100%;
    min-height: 80px;
    padding: 8px;
    border: 1px solid var(--divider-color);
    border-radius: 6px;
    background: var(--ha-card-background, var(--card-background-color));
    color: var(--primary-text-color);
  }

  /* Slide-out delete block */
  .slide-delete-wrap {
    padding: 16px 0;
    border-top: 1px solid var(--ca-border);
    margin-top: 16px;
  }

  /* Facade card */
  .facade-dir-label {
    font-size: 12px;
    color: var(--ca-secondary-text);
  }
  .facade-meta-row {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
    font-size: 13px;
    color: var(--ca-secondary-text);
  }
  .facade-covers-intro {
    font-size: 13px;
    color: var(--ca-secondary-text);
    margin-bottom: 8px;
  }
  .facade-covers-list-wrap {
    margin-bottom: 12px;
  }
  .facade-covers-label {
    font-size: 12px;
    color: var(--ca-secondary-text);
    margin-bottom: 4px;
  }
  .facade-no-covers {
    font-size: 12px;
    color: var(--ca-secondary-text);
  }
  .facade-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  /* Rules */
  .rule-reorder-hint {
    margin-bottom: 12px;
    font-size: 12px;
    color: var(--ca-secondary-text);
  }
  .slide-out input:disabled, .form-group input:disabled { opacity: .5; cursor: not-allowed; }
  .cond-group { border: 1px solid var(--ca-border); border-left: 3px solid var(--ca-primary, #03a9f4); border-radius: 8px; padding: 10px 10px 2px; margin-bottom: 4px; }
  .cond-group-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
  .cond-group-title { font-weight: 600; font-size: 13px; }
  .cond-group-op { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--ca-secondary-text); }
  .cond-group-op select { width: auto; padding: 4px 8px; font-size: 12px; }
  .cond-group-head > .btn-icon { margin-left: auto; }
  .cond-group-head > .move-btns { margin-left: auto; }
  .cond-group-head > .move-btns + .btn-icon { margin-left: 0; }
  .move-btns { display: inline-flex; align-items: center; flex: none; }
  .move-btns.move-btns-v { flex-direction: column; gap: 2px; margin: -4px 0; }
  .move-btns.move-btns-v .btn-move { padding: 3px 6px; }
  /* Touch screens cannot drag rows: the arrows replace the handle */
  @media (max-width: 600px) {
    .rule-row > .drag-handle { display: none; }
    .rule-row { gap: 8px; padding-left: 8px; }
  }
  .btn-icon.btn-move { font-size: 11px; padding: 5px 6px; border-radius: 6px; }
  .btn-icon.btn-move:disabled { opacity: .3; cursor: default; background: none; color: var(--ca-secondary-text); }
  .cond-group-sep { text-align: center; font-weight: 700; font-size: 12px; letter-spacing: .05em; color: var(--ca-primary, #03a9f4); margin: 6px 0; }
  .cond-group-add { margin: 6px 0 4px; }
  .cond-head-right { display: inline-flex; align-items: center; gap: 6px; }
  .cond-chevron { border: none; background: transparent; color: var(--ca-secondary-text); cursor: pointer; font-size: 12px; padding: 0 6px 0 0; transition: transform .15s; }
  .condition-card.collapsed .cond-chevron { transform: rotate(-90deg); }
  .condition-card .cond-type[data-action] { cursor: pointer; }
  .condition-card.collapsed > :not(.cond-header) { display: none; }
  .condition-card.collapsed .cond-header { margin-bottom: 0; }
  .cond-summary { display: none; font-size: 12px; color: var(--primary-text-color); margin-left: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 45ch; }
  .condition-card.collapsed .cond-summary:not(:empty) { display: inline; }
  .rule-conditions-label { display: flex; align-items: center; justify-content: space-between; }
  .cond-collapse-all { border: none; background: transparent; color: var(--ca-primary); cursor: pointer; font-size: 12px; text-transform: none; font-weight: 500; letter-spacing: normal; padding: 0; }
  .cond-group-move { width: auto; padding: 2px 6px; font-size: 12px; }
  .cond-not { border: 1px solid var(--ca-border); background: transparent; color: var(--ca-secondary-text); border-radius: 10px; padding: 1px 8px; font-size: 11px; font-weight: 600; cursor: pointer; margin-right: 6px; }
  .cond-not.active { background: var(--error-color, #db4437); border-color: var(--error-color, #db4437); color: #fff; }
  .condition-card.negated { border-left: 3px solid var(--error-color, #db4437); }
  .chip-block { display: inline-flex; flex-wrap: wrap; align-items: center; gap: 4px; padding: 2px 6px; border: 1px dashed var(--ca-border); border-radius: 12px; }
  .chip-op { font-size: 11px; color: var(--ca-secondary-text); }
  .chip-op-between { font-weight: 700; color: var(--ca-primary, #03a9f4); margin: 0 4px; }
  .chip-not { color: var(--error-color, #db4437); font-size: 11px; }
  .rule-conditions-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--ca-secondary-text);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 16px 0 8px;
  }
  .rule-no-conditions {
    font-size: 13px;
    color: var(--ca-secondary-text);
    margin-bottom: 8px;
  }
  .rule-condition-add {
    margin-top: 8px;
  }
  .rule-condition-type-select {
    padding: 8px;
    border: 1px solid var(--ca-border);
    border-radius: 8px;
    background: var(--primary-background-color, #fafafa);
    color: var(--primary-text-color);
    font-size: 13px;
    font-family: inherit;
  }
  .rule-editor-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  /* Scenario card extras */
  .scenario-card-icon {
    --mdc-icon-size: 20px;
    margin-right: 6px;
  }
  .sc-actions {
    display: flex;
    gap: 6px;
  }
  .scenario-no-rules {
    font-size: 13px;
    color: var(--ca-secondary-text);
  }
  .sc-rule-disabled {
    text-decoration: line-through;
    opacity: 0.5;
  }

  /* Scenario icon picker */
  .icon-picker-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(44px, 1fr));
    gap: 6px;
    padding: 8px;
    border: 1px solid var(--ca-border);
    border-radius: 8px;
    background: var(--primary-background-color, #fafafa);
    max-height: 220px;
    overflow-y: auto;
  }
  .icon-picker-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    aspect-ratio: 1 / 1;
    padding: 0;
    border: 1px solid transparent;
    border-radius: 6px;
    background: transparent;
    color: var(--primary-text-color);
    cursor: pointer;
    transition: background 0.12s ease, border-color 0.12s ease;
    --mdc-icon-size: 22px;
  }
  .icon-picker-btn:hover {
    background: color-mix(in srgb, var(--ca-primary) 10%, transparent);
    border-color: color-mix(in srgb, var(--ca-primary) 30%, transparent);
  }
  .icon-picker-btn.selected {
    background: color-mix(in srgb, var(--ca-primary) 18%, transparent);
    border-color: var(--ca-primary);
    color: var(--ca-primary);
  }
  .icon-picker-custom {
    margin-top: 8px;
  }
  .icon-picker-custom > summary {
    cursor: pointer;
    font-size: 12px;
    color: var(--ca-secondary-text);
    padding: 4px 0;
    list-style: none;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .icon-picker-custom > summary::-webkit-details-marker { display: none; }
  .icon-picker-custom[open] > summary { color: var(--ca-primary); }
  .icon-picker-custom-body {
    margin-top: 6px;
  }
  .icon-picker-custom-body input {
    width: 100%;
    padding: 8px;
    border: 1px solid var(--ca-border);
    border-radius: 6px;
    background: var(--primary-background-color, #fafafa);
    color: var(--primary-text-color);
    font-size: 13px;
    font-family: inherit;
  }
  .icon-picker-custom-hint {
    font-size: 11px;
    color: var(--ca-secondary-text);
    margin-top: 4px;
    line-height: 1.4;
  }

  /* Log filter bar */
  .log-filter-bar {
    margin-bottom: 12px;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .log-cover-filter {
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .log-cover-filter label { font-size: 13px; color: var(--ca-secondary-text); }
  .log-cover-filter select {
    min-width: 220px; max-width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--ca-border);
    border-radius: 8px;
    background: var(--primary-background-color, #fafafa);
    color: var(--primary-text-color);
    font-size: 14px;
    font-family: inherit;
  }
  .log-cover-filter select:focus { border-color: var(--ca-primary); outline: none; }
  .log-cover-note { font-size: 12px; color: var(--ca-secondary-text); }
  .slide-log-link { margin: 16px 0 4px; }

  /* Compass */
  .compass-svg-root {
    display: block;
  }

  /* Temperature cell -- mode color is still inline because it's dynamic, but weight is consistent */
  .data-table td.temp-mode {
    font-weight: 600;
  }
  .temp-icon { display: inline-flex; vertical-align: -2px; margin-right: 3px; }

  /* Responsive */
  @media (max-width: 768px) {
    .panel-container { padding: 8px; }
    .card-grid { grid-template-columns: 1fr; }
    .slide-panel { width: 100vw; }
    /* Full-screen sheet on phones: room for the status bar / notch, big
       close targets on both sides and a close button at the bottom */
    .slide-header {
      padding-top: calc(12px + env(safe-area-inset-top, 0px));
      gap: 8px;
    }
    .slide-header .slide-back { display: inline-flex; }
    .slide-header .btn-icon { min-width: 44px; min-height: 44px; font-size: 22px; align-items: center; justify-content: center; }
    .slide-body { padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px)); }
    .slide-close-bottom { display: flex; justify-content: center; margin: 16px 0 8px; }
    .slide-close-bottom .btn { min-width: 160px; justify-content: center; }
    .form-row { grid-template-columns: 1fr; }
    .tab-bar button { padding: 10px 14px; font-size: 13px; }
    .data-table th, .data-table td { padding: 10px 12px; font-size: 13px; }
    .data-table td.row-chevron { display: none; }
    .data-table th.row-chevron-head { display: none; }
    /* Settings: sidebar collapses to horizontal scrollable pill strip */
    .settings-shell {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
    }
    .settings-nav {
      flex: 0 0 auto;
      flex-direction: row;
      position: static;
      padding: 6px;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      gap: 4px;
      /* Edge fade so users see there is more content to the side */
      -webkit-mask-image: linear-gradient(
        to right,
        transparent 0,
        black 18px,
        black calc(100% - 28px),
        transparent 100%
      );
      mask-image: linear-gradient(
        to right,
        transparent 0,
        black 18px,
        black calc(100% - 28px),
        transparent 100%
      );
      scrollbar-width: none;
      scroll-snap-type: x proximity;
    }
    .settings-nav::-webkit-scrollbar { display: none; }
    .settings-stack { gap: 16px; }
    .settings-stack .card-header { padding: 14px 16px 12px; }
    .settings-stack .card-body { padding: 16px 16px 20px; }
    .settings-stack .form-group { margin-bottom: 20px; }
    .settings-stack .form-row { grid-template-columns: 1fr; gap: 20px; margin-bottom: 20px; }
    .settings-stack .form-group input[type="number"],
    .settings-stack .form-group select,
    .settings-stack .form-group input[type="text"] { max-width: none; }
    .settings-nav-btn {
      flex: 0 0 auto;
      padding: 8px 12px;
      font-size: 13px;
      scroll-snap-align: start;
    }
    .settings-nav-btn .settings-nav-label {
      overflow: visible;
      text-overflow: unset;
    }
    /* Sticky first column so the cover name stays visible when scrolling horizontally */
    .data-table th:first-child,
    .data-table td:first-child {
      position: sticky;
      left: 0;
      z-index: 1;
      background: var(--ca-card-bg);
      box-shadow: 2px 0 4px rgba(0, 0, 0, 0.15);
    }
    .data-table thead th:first-child {
      z-index: 2;
    }
    .data-table tbody tr:hover td:first-child,
    .data-table tbody tr.selected td:first-child {
      background: color-mix(in srgb, var(--ca-primary) 12%, var(--ca-card-bg));
    }
    .condition-card .cond-params { grid-template-columns: 1fr; }
    .panel-header {
      flex-direction: column;
      align-items: stretch;
      gap: 6px;
      padding: 12px 0 6px;
    }
    .header-left {
      justify-content: flex-start;
    }
    .header-right {
      justify-content: space-between;
      row-gap: 8px;
      padding-top: 6px;
      border-top: 1px solid var(--ca-border);
    }
    .info-bar {
      flex-basis: 100%;
      order: -1;
      font-size: 11px;
    }
  }
`;

// Integer cover settings and their range (cover/update schema: plain int).
const COVER_INT_LIMITS = {
  pause_duration: [1, 480],
  lock_position: [0, 100],
  vent_position: [0, 100],
  lock_tilt_position: [0, 100],
  vent_tilt_position: [0, 100],
  min_position_change: [1, 50],
  min_time_between_changes: [60, 3600],
  travel_time: [1, 300],
};

/* ============================================================
 * Main panel component
 * ============================================================ */
class CoverAutomaticPanel extends HTMLElement {
  constructor() {
    super();
    this._initialized = false;
    this._delegationBound = false;
    this._hass = null;
    this._panel = null;
    this._config = null;
    this._activeTab = "covers";
    this._selectedCover = null;
    this._slideOpen = false;
    this._expandedRule = null;
    this._editingFacade = null;
    this._addingFacade = false;
    this._addingRule = false;
    this._addingCover = false;
    this._addingScenario = false;
    this._editingScenario = null;
    this._confirmCallback = null;
    this._confirmMessage = "";
    this._toastTimer = null;
    this._saveTimers = {};
    this._dragRuleId = null;
    this._dragOverId = null;
    this._error = null;
    this._latestVersion = null;
    this._logEntries = null;
    this._logFilter = null;
    this._logCover = null;
    this._coverSort = { key: "name", dir: "asc" };
    this._liveRefreshTimer = null;
    this._condPreviewTimer = null;
    this._eventUnsub = null;
    this._eventDebounce = null;
    this._expandedSections = { base: true };
    this._activeSettingsSection = "house";
    this._keydownListener = (e) => this._handleKeyDown(e);
    // Warn before closing/reloading the page with unsaved rule or settings edits
    this._beforeUnloadListener = (e) => {
      let dirty = false;
      try { dirty = this._ruleDraftDirty() || this._settingsDirty(); } catch (err) { dirty = false; }
      // Debounced cover edits not sent yet: send them now and warn
      // (the page may still close before they reach the server).
      if (this._saveTimers && Object.keys(this._saveTimers).length) {
        dirty = true;
        try { this._flushCoverSaves(); } catch (err) { /* ignore */ }
      }
      if (!dirty) return;
      e.preventDefault();
      e.returnValue = "";
    };
    // Working copy of the rule open in the editor ({ id, rule }); every editor
    // change goes here and only reaches _config once saved.
    this._ruleDraft = null;
    // Unsaved settings inputs (field -> { kind, value }), kept across sections.
    this._settingsDraft = null;
    this._haTimers = {};
    this._haInflight = {};
    this._previewSeq = 0;
    this._subscribing = null;
    this._confirmOkLabel = null;


    this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    const prevHass = this._hass;
    const prevLang = prevHass?.language;
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
      return;
    }
    if (hass && hass.language !== prevLang) {
      this._render();
      return;
    }
    // HA assigns a new hass object on every state change anywhere in the
    // system. Only re-render when an entity this panel displays changed.
    if (!this._relevantStatesChanged(prevHass, hass)) return;
    if (this._config) {
      const shell = this.shadowRoot ? this.shadowRoot.querySelector(".panel-container") : null;
      // Only the info bar depends on HA states: patch it alone so the rest
      // of the header (master switch, focus) is not rebuilt.
      if (shell) this._patchInfoBar(shell);
      if (this._activeTab === "covers") this._updateLiveCells();
    }
  }

  _relevantEntityIds() {
    const ids = new Set(["sun.sun"]);
    const cfg = this._config;
    if (!cfg) return ids;
    const s = cfg.settings || {};
    for (const key of ["outdoor_temp_sensor", "indoor_temp_sensor", "weather_entity", "solar_sensor", "wind_sensor", "workday_sensor",
      "comfort_temp_min_entity", "comfort_temp_max_entity", "solar_threshold_entity"]) {
      if (s[key]) ids.add(s[key]);
    }
    for (const [eid, c] of Object.entries(cfg.covers || {})) {
      ids.add(eid);
      for (const key of ["lock_sensor", "vent_sensor", "indoor_temp_sensor", "comfort_temp_min_entity", "comfort_temp_max_entity", "occupancy_sensor"]) {
        if (c && c[key]) ids.add(c[key]);
      }
    }
    return ids;
  }

  _relevantStatesChanged(prevHass, hass) {
    if (!prevHass || !hass || !prevHass.states || !hass.states) return true;
    for (const id of this._relevantEntityIds()) {
      if (prevHass.states[id] !== hass.states[id]) return true;
    }
    return false;
  }

  set panel(panel) {
    this._panel = panel;
  }

  connectedCallback() {
    // Window-level so Escape works regardless of where focus sits
    window.addEventListener("keydown", this._keydownListener);
    window.addEventListener("beforeunload", this._beforeUnloadListener);
    // Re-attach subscriptions when the element is re-inserted (HA caches
    // custom panels and detaches/re-attaches them on navigation). _initialize
    // only runs once, so without this the real-time event push and the live
    // refresh stay dead after the first disconnect. Both calls are idempotent.
    if (this._initialized) {
      this._subscribeUpdates();
      if (this._activeTab === "covers") this._startLiveRefresh();
      if (this._activeTab === "rules" && this._expandedRule) this._startCondPreview();
    }
  }

  disconnectedCallback() {
    window.removeEventListener("keydown", this._keydownListener);
    window.removeEventListener("beforeunload", this._beforeUnloadListener);
    this._stopLiveRefresh();
    this._stopCondPreview();
    this._unsubscribeUpdates();
    this._removeHouseDragListeners();
    // Send pending debounced cover edits now instead of dropping them.
    this._flushCoverSaves();
    // Pending HA-condition validations only refresh the (now hidden) editor.
    for (const t of Object.values(this._haTimers || {})) clearTimeout(t);
    this._haTimers = {};
    if (this._toastTimer) { clearTimeout(this._toastTimer); this._toastTimer = null; }
  }

  /* ---------- i18n helper ---------- */
  _t(key) {
    const lang = (this._hass?.language) || "en";
    const dict = I18N[lang] || I18N.en;
    return dict[key] !== undefined ? dict[key] : (I18N.en[key] !== undefined ? I18N.en[key] : key);
  }

  // Label separator: French typography puts a (narrow no-break) space before ":"
  _colon() {
    const lang = (this._hass?.language) || "en";
    return lang.startsWith("fr") ? "\u202F: " : ": ";
  }

  _tt(section, key) {
    const lang = (this._hass?.language) || "en";
    const dict = I18N[lang] || I18N.en;
    const s = dict[section] || I18N.en[section] || {};
    return s[key] !== undefined ? s[key] : ((I18N.en[section] || {})[key] || key);
  }

  _hint(key) {
    const text = this._t(key);
    if (text === key) return "";
    return `<details class="field-hint"><summary title="${this._t("show_hint")}" aria-label="${this._t("show_hint")}">${this._lucideIcon("info", 14)}</summary><div class="hint-body">${this._esc(text)}</div></details>`;
  }

  /* ---------- Lifecycle ---------- */
  _initialize() {
    this._initialized = true;
    this._subscribeUpdates();
    this._loadConfig();
  }

  _subscribeUpdates() {
    // _subscribing: a subscription request is in flight (a quick
    // disconnect/reconnect must not open a second one).
    if (this._eventUnsub || this._subscribing || !this._hass) return;
    // Dedicated WebSocket subscription (no bus event, so nothing is written
    // to the recorder database on every update cycle).
    const pending = this._hass.connection.subscribeMessage(() => {
      if (!this.isConnected || this._activeTab !== "covers" || !this._config) return;
      // Debounce 500 ms, but refresh at least every 3 s while events keep coming
      const now = Date.now();
      if (!this._eventDebounceStart) this._eventDebounceStart = now;
      if (this._eventDebounce) clearTimeout(this._eventDebounce);
      const wait = Math.max(0, Math.min(500, this._eventDebounceStart + 3000 - now));
      this._eventDebounce = setTimeout(() => {
        this._eventDebounce = null;
        this._eventDebounceStart = null;
        this._refreshLiveCovers();
      }, wait);
    }, { type: "cover_automatic/subscribe" });
    this._subscribing = pending;
    Promise.resolve(pending).then((unsub) => {
      if (this._subscribing === pending) this._subscribing = null;
      // Disconnected while the request was pending (or already subscribed):
      // release it right away instead of leaking it.
      if (!this.isConnected || this._eventUnsub) {
        try { const r = unsub(); if (r && r.catch) r.catch(() => {}); } catch (e) { /* ignore */ }
        return;
      }
      this._eventUnsub = unsub;
    }).catch((err) => {
      if (this._subscribing === pending) this._subscribing = null;
      console.warn("CoverAutomatic: failed to subscribe to update events", err);
    });
  }

  _unsubscribeUpdates() {
    if (this._eventUnsub) {
      this._eventUnsub();
      this._eventUnsub = null;
    }
    if (this._eventDebounce) {
      clearTimeout(this._eventDebounce);
      this._eventDebounce = null;
    }
    this._eventDebounceStart = null;
  }

  /* ---------- WebSocket calls ---------- */
  async _ws(type, data) {
    if (!this._hass) return null;
    try {
      const msg = { type, ...(data ?? {}) };
      const result = await this._hass.callWS(msg);
      return result;
    } catch (err) {
      console.error("CoverAutomatic WS error:", type, err);
      throw err;
    }
  }

  async _loadConfig() {
    this._error = null;
    this._render();
    try {
      this._config = await this._ws("cover_automatic/config");
      this._cfgEpoch = (this._cfgEpoch || 0) + 1;
      if (this._activeTab === "covers") this._startLiveRefresh();
      this._render();
      this._checkForUpdate();
    } catch (e) {
      this._error = e.message || String(e);
      this._render();
    }
  }

  async _checkForUpdate() {
    if (!this._config || !this._config.version) return;
    if (this._config.settings && this._config.settings.update_check_enabled === false) return;
    try {
      const resp = await fetch("https://api.github.com/repos/crandler/CoverAutomatic/releases/latest", { headers: { Accept: "application/vnd.github.v3+json" } });
      if (!resp.ok) return;
      const data = await resp.json();
      const latest = (data.tag_name || "").replace(/^v/, "");
      if (latest && this._compareVersions(latest, this._config.version) > 0) {
        this._latestVersion = latest;
        this._updateRegion(this.shadowRoot.querySelector(".panel-container"), "header", this._renderHeaderContent());
      }
    } catch (e) { /* silent */ }
  }

  // Compare dotted numeric versions: >0 if a is newer than b, <0 if older.
  _compareVersions(a, b) {
    const pa = String(a).split(/[.-]/).map(x => parseInt(x, 10));
    const pb = String(b).split(/[.-]/).map(x => parseInt(x, 10));
    for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
      const x = Number.isFinite(pa[i]) ? pa[i] : 0;
      const y = Number.isFinite(pb[i]) ? pb[i] : 0;
      if (x !== y) return x > y ? 1 : -1;
    }
    return 0;
  }

  // Apply a configuration returned by a WebSocket call.
  //   opts.resetDraft: the open rule was just saved -> restart its draft from
  //                    the saved version.
  //   opts.render:     false = update the data only (caller patches the DOM).
  //   opts.haLive:     with resetDraft, live HA validation results to keep for
  //                    the open rule, keyed by condition index.
  _updateConfigFromResult(result, opts = {}) {
    if (!result) return;
    // Capture unsaved DOM-only editor fields before the editor is rebuilt.
    if (!opts.resetDraft) this._syncRuleDraftFromDom();
    // The backend renamed the rule id after a name change: the open editor
    // and its per-rule state follow the new id.
    const renamed = result.renamed_rule;
    if (renamed && renamed.from && renamed.to && renamed.from !== renamed.to
      && (result.rules || {})[renamed.to]) {
      this._followRuleRename(renamed.from, renamed.to);
    }
    this._config = result;
    // Live refreshes started before this config are outdated (see _refreshLiveCovers)
    this._cfgEpoch = (this._cfgEpoch || 0) + 1;
    // Settings changed on the server (import, other window): keep only the
    // inputs really edited here, the others show the new stored values.
    this._captureSettingsDraft();
    if (this._settingsDraft) {
      // The settings inputs still show the old values until the next render:
      // do not capture them again (they would overwrite the new ones).
      this._settingsDomStale = true;
      for (const [field, d] of Object.entries(this._settingsDraft)) {
        if (this._draftSame(d)) delete this._settingsDraft[field];
        else d.initial = undefined; // re-read from the next render
      }
    }
    // The open rule no longer exists (deleted or renamed elsewhere)
    if (this._expandedRule && !(result.rules || {})[this._expandedRule]) this._expandedRule = null;
    const d = this._ruleDraft;
    let keepLive = false;
    if (d) {
      const saved = (result.rules || {})[d.id];
      if (!saved || this._expandedRule !== d.id) {
        this._discardRuleDraft();
      } else if (opts.resetDraft) {
        this._ruleDraft = { id: d.id, rule: this._clone(saved) };
      } else {
        keepLive = true; // unrelated change: the open rule keeps its draft
      }
    }
    // Live validation results belong to the draft's conditions; keep them
    // only while that draft is kept as is.
    const live = {};
    if (keepLive && this._haLive) {
      const pre = d.id + ":";
      for (const [k, v] of Object.entries(this._haLive)) if (k.startsWith(pre)) live[k] = v;
    }
    if (opts.haLive && this._ruleDraft) {
      for (const [i, v] of Object.entries(opts.haLive)) live[this._ruleDraft.id + ":" + i] = v;
    }
    this._haLive = live;
    this._showToast();
    if (opts.render === false) return;
    this._noDomSync = !!opts.resetDraft;
    try { this._render(); } finally { this._noDomSync = false; }
  }

  // Move every piece of per-rule editor state from one rule id to another.
  _followRuleRename(from, to) {
    const moveKey = (k) => (k.startsWith(from + ":") ? to + k.slice(from.length) : k);
    if (this._expandedRule === from) this._expandedRule = to;
    if (this._ruleDraft && this._ruleDraft.id === from) {
      this._ruleDraft.id = to;
      if (this._ruleDraft.rule) this._ruleDraft.rule.id = to;
    }
    if (this._collapsedConds) this._collapsedConds = new Set([...this._collapsedConds].map(moveKey));
    if (this._haLive) {
      const next = {};
      for (const [k, v] of Object.entries(this._haLive)) next[moveKey(k)] = v;
      this._haLive = next;
    }
    const restart = [];
    // Running validations were started for the old id: their results are
    // dropped (see _runHaValidate), so they run again for the new id.
    for (const k of Object.keys(this._haInflight || {})) {
      if (k.startsWith(from + ":")) restart.push(parseInt(k.slice(from.length + 1), 10));
    }
    for (const [k, t] of Object.entries(this._haTimers || {})) {
      if (!k.startsWith(from + ":")) continue;
      clearTimeout(t);
      delete this._haTimers[k];
      restart.push(parseInt(k.slice(from.length + 1), 10));
    }
    // Scheduled (not run yet): they run once the new config is in place.
    for (const idx of new Set(restart)) if (Number.isFinite(idx)) this._scheduleHaValidate(to, idx);
    if (this._dragRuleId === from) this._dragRuleId = to;
    if (this._dragOverId === from) this._dragOverId = to;
  }

  _clone(o) {
    return o == null ? o : JSON.parse(JSON.stringify(o));
  }

  /* ---------- Debounced save for covers ---------- */
  // field may be an object { field: value, ... } to save several at once
  //   hooks.onSettled(ok): called once the save finished (not when a newer
  //   edit of the same fields replaced it).
  _debouncedCoverSave(entityId, field, value, hooks = null) {
    const fields = typeof field === "object" && field !== null ? field : { [field]: value };
    const key = `${entityId}.${Object.keys(fields).join("+")}`;
    this._cancelCoverSave(key);
    const fn = async () => {
      try {
        const data = { entity_id: entityId, ...fields };
        const result = await this._ws("cover_automatic/cover/update", data);
        if (this._slideHasFocus()) {
          // The user is still typing in the slide-out: rebuilding it would
          // drop focus and keystrokes. Update the data, refresh everything
          // around it and patch the derived texts inside it.
          this._updateConfigFromResult(result, { render: false });
          this._refreshAroundSlideOut();
        } else {
          this._updateConfigFromResult(result);
        }
        if (hooks && hooks.onSettled) hooks.onSettled(true);
      } catch (e) {
        console.error("Save error:", e);
        this._showError(e);
        if (hooks && hooks.onSettled) hooks.onSettled(false);
      }
    };
    const timer = setTimeout(() => {
      if (this._saveTimers[key] && this._saveTimers[key].timer === timer) delete this._saveTimers[key];
      fn();
    }, 500);
    this._saveTimers[key] = { timer, fn };
  }

  _cancelCoverSave(key) {
    const pending = this._saveTimers[key];
    if (!pending) return;
    clearTimeout(pending.timer);
    delete this._saveTimers[key];
  }

  // Send every pending debounced cover edit right away.
  _flushCoverSaves() {
    const pending = Object.values(this._saveTimers || {});
    this._saveTimers = {};
    for (const p of pending) {
      clearTimeout(p.timer);
      p.fn();
    }
  }

  _slideHasFocus() {
    const a = this.shadowRoot && this.shadowRoot.activeElement;
    return !!(this._slideOpen && a && a.closest && a.closest(".slide-panel"));
  }

  // Re-render everything except the slide-out, then update the texts inside
  // the slide-out that derive from the saved values (focus stays intact).
  _refreshAroundSlideOut() {
    const shell = this.shadowRoot.querySelector(".panel-container");
    if (!shell || !shell.querySelector("[data-region]")) return;
    this._updateRegion(shell, "header", this._renderHeaderContent());
    this._updateRegion(shell, "content", this._renderContent());
    const cover = (this._config.covers || {})[this._selectedCover];
    if (!cover) { this._render(); return; }
    const info = this._travelInfo(cover);
    const id = CSS.escape(cover.entity_id);
    const input = shell.querySelector(`[data-action="cover-input"][data-id="${id}"][data-field="travel_time"]`);
    if (input) input.placeholder = info.placeholder;
    const used = shell.querySelector(`[data-travel-used="${id}"]`);
    if (used) used.textContent = info.usedTxt;
  }

  // Travel-time texts of a cover: placeholder, measured value, effective value.
  _travelInfo(cover) {
    const num = (v) => (typeof v === "number" && v > 0 ? v : null);
    const measured = num(cover.measured_travel_time);
    const manual = num(cover.travel_time);
    const globalTravel = num(this._config.settings?.default_travel_time);
    const fmtS = (v) => String(Math.round(v));
    const placeholder = measured != null
      ? this._t("cover_travel_auto_measured").replace("{s}", fmtS(measured))
      : (globalTravel != null ? this._t("cover_travel_auto_default").replace("{s}", fmtS(globalTravel)) : this._t("cover_travel_auto"));
    // Effective value, same order as the integration: entered > measured > default
    let used = null, usedSrc = "none";
    if (manual != null) { used = manual; usedSrc = "manual"; }
    else if (measured != null) { used = measured; usedSrc = "measured"; }
    else if (globalTravel != null) { used = globalTravel; usedSrc = "default"; }
    const settle = used != null ? Math.max(30, used + 5) : 30;
    const usedTxt = (used != null
      ? this._t("cover_travel_used").replace("{s}", fmtS(used)).replace("{src}", this._t("cover_travel_src_" + usedSrc))
      : this._t("cover_travel_used_none")).replace("{wait}", fmtS(settle));
    return { measured, placeholder, usedTxt, fmtS };
  }

  /* ---------- Toast ---------- */
  _showToast(message, isError = false) {
    if (this._toastTimer) clearTimeout(this._toastTimer);
    const toast = this.shadowRoot.querySelector(".toast");
    if (!toast) return;
    const msg = toast.querySelector(".toast-msg");
    // Setting the text on show (not statically) makes role="status" announce it
    if (msg) msg.textContent = message || this._t("saved");
    // Force reflow so the countdown animation restarts on rapid re-shows
    toast.classList.remove("show");
    toast.classList.toggle("toast-error", !!isError);
    void toast.offsetWidth;
    toast.classList.add("show");
    this._toastTimer = setTimeout(() => {
      toast.classList.remove("show");
      if (msg) msg.textContent = "";
    }, isError ? 5000 : 2000);
  }

  // Show a localized error toast for a failed WebSocket call. The backend
  // sends a stable error code; its message text is English-only.
  _showError(err) {
    const code = err && err.code ? String(err.code) : "";
    const key = "error_" + code;
    const text = code ? this._t(key) : key;
    let msg = text !== key ? text : this._t("error_generic");
    // Which condition is wrong is only in the backend message: show it too
    if (code === "invalid_conditions" && err.message) msg += " — " + String(err.message);
    this._showToast(msg, true);
  }

  /* ---------- Confirm dialog ---------- */
  _showConfirm(message, callback, okLabel = null) {
    this._confirmMessage = message;
    this._confirmCallback = callback;
    this._confirmOkLabel = okLabel;
    this._render();
    // Move focus into the dialog so keyboard users can act on it
    setTimeout(() => this.shadowRoot.querySelector(".confirm-dialog .btn-secondary")?.focus(), 0);
  }

  _hideConfirm() {
    this._confirmMessage = "";
    this._confirmCallback = null;
    this._confirmOkLabel = null;
    this._render();
  }

  /* ---------- Main render ---------- */
  _render() {
    const root = this.shadowRoot;
    // Unsaved inputs that live only in the DOM survive the rebuild.
    this._syncRuleDraftFromDom();
    this._captureSettingsDraft();

    // Full render when no shell exists, loading/error, or shell has no regions yet
    const shell = root.querySelector(".panel-container");
    if (!shell || !this._config || this._error || !shell.querySelector("[data-region]")) {
      this._fullRender();
    } else {
      // Partial render: update regions individually
      this._updateRegion(shell, "header", this._renderHeaderContent());
      this._updateRegion(shell, "tabs", this._renderTabsContent());
      this._updateRegion(shell, "content", this._renderContent());
      this._updateRegion(shell, "slideout", this._renderSlideOut());
      this._updateRegion(shell, "confirm", this._renderConfirmDialog());
    }
    this._applySettingsDraft();
    this._syncSettingsRadios();
    this._settingsDomStale = false;
    this._refreshDeps();
  }

  _patchInfoBar(shell) {
    const slot = shell.querySelector('[data-region="header"] .info-bar-slot');
    if (!slot) { this._updateRegion(shell, "header", this._renderHeaderContent()); return; }
    const html = this._renderInfoBarInline();
    // Compare with the last generated HTML (innerHTML serialization, SVG
    // included, never matches it exactly and would rewrite every time).
    if (slot._caHtml === html) return;
    slot._caHtml = html;
    slot.innerHTML = html;
  }

  _updateRegion(shell, name, html) {
    const el = shell.querySelector(`[data-region="${name}"]`);
    if (!el) return;
    if (name === "slideout") { this._updateSlideOutRegion(el, html); return; }
    el.innerHTML = html;
  }

  /* ---------- Slide-out: keep scroll position and focus ---------- */
  // Structure of the slide-out HTML without the parts that are patched in
  // place (control values, placeholders, section summaries, travel text).
  _slideSig(html) {
    return String(html)
      .replace(/\s(?:value|placeholder)="[^"]*"/g, "")
      .replace(/\s(?:checked|selected|disabled)(?=[\s>])/g, "")
      .replace(/(<span class="section-summary">)[^<]*(<\/span>)/g, "$1$2")
      .replace(/(data-travel-used="[^"]*">)[^<]*(<\/div>)/g, "$1$2");
  }

  // Selector finding "the same" element again after a rebuild.
  _slideElKey(el) {
    if (!el || !el.tagName) return null;
    const attrs = ["data-action", "data-id", "data-field", "data-section", "data-val", "data-occ-other", "data-ids", "id", "name"];
    let sel = el.tagName.toLowerCase();
    let any = false;
    for (const a of attrs) {
      const v = el.getAttribute(a);
      if (v != null) { sel += `[${a}="${CSS.escape(v)}"]`; any = true; }
    }
    if (el.type === "radio" && el.value) sel += `[value="${CSS.escape(el.value)}"]`;
    return any ? sel : null;
  }

  _updateSlideOutRegion(el, html) {
    const prevHtml = this._slideHtml;
    this._slideHtml = html;
    const oldPanel = el.querySelector(".slide-panel");
    const oldCover = oldPanel && oldPanel.classList.contains("open") ? oldPanel.dataset.cover : null;
    const sameCover = !!(oldCover && this._slideOpen && this._selectedCover === oldCover);
    if (!sameCover) { el.innerHTML = html; return; }
    if (prevHtml === html) return; // nothing changed: keep the DOM as is
    if (prevHtml != null && this._slideSig(prevHtml) === this._slideSig(html)) {
      this._patchSlideOut(el, prevHtml, html);
      return;
    }
    // Structural change: rebuild, then restore scroll and focus.
    const body = el.querySelector(".slide-body");
    const scroll = body ? body.scrollTop : 0;
    const active = this.shadowRoot.activeElement;
    let key = null, selStart = null, selEnd = null;
    if (active && el.contains(active)) {
      key = this._slideElKey(active);
      try { selStart = active.selectionStart; selEnd = active.selectionEnd; } catch (e) { /* not a text field */ }
    } else if (this._slideClick && Date.now() - this._slideClick.t < 2000) {
      // iOS Safari does not focus clicked buttons: use the last click instead
      key = this._slideClick.key;
    }
    el.innerHTML = html;
    const nbody = el.querySelector(".slide-body");
    if (nbody) nbody.scrollTop = scroll;
    if (key) {
      let target = null;
      try { target = el.querySelector(key); } catch (e) { target = null; }
      if (target) {
        try { target.focus({ preventScroll: true }); } catch (e) { target.focus(); }
        if (selStart != null) { try { target.setSelectionRange(selStart, selEnd); } catch (e) { /* ignore */ } }
        if (nbody) nbody.scrollTop = scroll;
      }
    }
  }

  // Same structure: update only what differs between the previous and the
  // new HTML. Controls the user is editing (focused, pending save, invalid)
  // keep their value.
  _patchSlideOut(el, prevHtml, html) {
    const parse = (h) => { const t = document.createElement("template"); t.innerHTML = h; return t.content; };
    const oldT = parse(prevHtml), newT = parse(html);
    const active = this.shadowRoot.activeElement;
    const pendingKeys = Object.keys(this._saveTimers || {});
    const pending = (id, field) => pendingKeys.some(k => k.startsWith(id + ".") && k.slice(id.length + 1).split("+").includes(field));
    const ctrlState = (c) => {
      if (!c) return null;
      if (c.tagName === "SELECT") {
        const o = c.querySelector("option[selected]") || c.querySelector("option");
        return o ? (o.getAttribute("value") ?? o.textContent) : "";
      }
      if (c.type === "checkbox" || c.type === "radio") return c.hasAttribute("checked");
      return c.getAttribute("value") ?? "";
    };
    for (const nc of newT.querySelectorAll("input, select, textarea")) {
      const key = this._slideElKey(nc);
      if (!key) continue;
      const oc = oldT.querySelector(key);
      const live = el.querySelector(key);
      if (!oc || !live) continue;
      const ph = nc.getAttribute("placeholder");
      if (ph !== oc.getAttribute("placeholder")) { if (ph == null) live.removeAttribute("placeholder"); else live.setAttribute("placeholder", ph); }
      const nv = ctrlState(nc);
      if (nv === ctrlState(oc)) continue;
      if (live === active) {
        // Focused control keeps what it shows; the new server value is
        // applied on blur if the user did not change it (_onSlideFocusOut).
        const dom = typeof nv === "boolean" ? live.checked : live.value;
        live._caStale = { value: nv, dom: live._caStale ? live._caStale.dom : dom };
        continue;
      }
      if (live.classList.contains("input-invalid")) continue;
      if (live.dataset.id && live.dataset.field && pending(live.dataset.id, live.dataset.field)) continue;
      delete live._caStale;
      if (typeof nv === "boolean") live.checked = nv; else live.value = nv;
    }
    for (const ns of newT.querySelectorAll(".section-header[data-section]")) {
      const sel = `.section-header[data-section="${CSS.escape(ns.dataset.section)}"] .section-summary`;
      const n = ns.querySelector(".section-summary");
      const live = el.querySelector(sel);
      if (n && live && live.textContent !== n.textContent) live.textContent = n.textContent;
    }
    for (const nt of newT.querySelectorAll("[data-travel-used]")) {
      const live = el.querySelector(`[data-travel-used="${CSS.escape(nt.dataset.travelUsed)}"]`);
      if (live && live.textContent !== nt.textContent) live.textContent = nt.textContent;
    }
  }

  // A slide-out control skipped by _patchSlideOut while focused: once blurred,
  // show the server value unless the user changed it meanwhile.
  _onSlideFocusOut(e) {
    const el = e.target;
    if (!el || !el._caStale) return;
    const stale = el._caStale;
    delete el._caStale;
    if (!el.isConnected || !el.closest || !el.closest(".slide-panel")) return;
    if (el.classList.contains("input-invalid")) return;
    const pendingKeys = Object.keys(this._saveTimers || {});
    const id = el.dataset.id, field = el.dataset.field;
    if (id && field && pendingKeys.some(k => k.startsWith(id + ".") && k.slice(id.length + 1).split("+").includes(field))) return;
    if (typeof stale.value === "boolean") {
      if (el.checked === stale.dom) el.checked = stale.value;
    } else if (el.value === stale.dom) {
      el.value = stale.value;
    }
  }

  _fullRender() {
    const root = this.shadowRoot;

    let html = `<style>${PANEL_STYLES}</style>`;
    html += '<div class="panel-container">';

    if (!this._config && !this._error) {
      html += `<div class="state-msg"><div class="spinner"></div><div>${this._t("loading")}</div></div>`;
      html += '</div>';
      root.innerHTML = html;
      this._setupDelegation();
      return;
    }

    if (this._error) {
      html += '<div class="state-msg">';
      html += '<div class="state-msg-icon">!</div>';
      html += `<div>${this._t("error_load")}</div>`;
      html += `<button class="btn btn-primary mt-16" data-action="retry">${this._t("retry")}</button>`;
      html += '</div></div>';
      root.innerHTML = html;
      this._setupDelegation();
      return;
    }

    html += `<div class="panel-header" data-region="header" role="banner">${this._renderHeaderContent()}</div>`;
    html += `<div class="tab-bar" data-region="tabs" role="navigation" aria-label="${this._t("nav_label")}">${this._renderTabsContent()}</div>`;
    html += `<div class="tab-content" data-region="content" role="main">${this._renderContent()}</div>`;
    this._slideHtml = this._renderSlideOut();
    html += `<div data-region="slideout">${this._slideHtml}</div>`;
    html += `<div data-region="confirm">${this._renderConfirmDialog()}</div>`;
    html += '</div>';
    html += `<div class="toast" role="status"><span class="toast-msg"></span><span class="toast-progress"></span></div>`;

    root.innerHTML = html;
    this._setupDelegation();
  }

  _renderHeaderContent() {
    const activeScenario = this._getActiveScenario();
    const version = this._config ? this._config.version : "";
    const enabled = this._config ? this._config.enabled !== false : true;
    let html = '<div class="header-left">';
    html += '<button class="menu-btn" data-action="toggle-menu" aria-label="' + this._t("title") + '">' + this._lucideIcon("menu", 24) + '</button>';
    html += '<h1>' + this._t("title") + '</h1>';
    if (this._latestVersion) {
      const v = this._esc(version);
      const latest = this._esc(this._latestVersion);
      html += ' <a class="update-badge" href="https://github.com/crandler/CoverAutomatic/releases/tag/v' + latest + '" target="_blank" rel="noopener noreferrer" title="' + this._t("update_badge_title") + '">v' + v + ' → v' + latest + '</a>';
    } else if (version) {
      const v = this._esc(version);
      html += ' <a class="version-info" href="https://github.com/crandler/CoverAutomatic/releases/tag/v' + v + '" target="_blank" rel="noopener noreferrer" title="' + this._t("version_link_title") + '">v' + v + '</a>';
    }
    html += '</div><div class="header-right">';
    html += '<span class="info-bar-slot">' + this._renderInfoBarInline() + '</span>';
    if (activeScenario) {
      html += '<span class="scenario-badge">' + (activeScenario.icon ? '<ha-icon icon="' + this._esc(activeScenario.icon) + '" class="scenario-badge-icon"></ha-icon>' : '') + this._esc(activeScenario.name) + '</span>';
    }
    html += '<div class="master-switch" title="' + this._t("master_enabled_hint") + '">';
    html += '<span class="master-label">' + this._t("master_enabled") + '</span>';
    html += '<label class="master-toggle">';
    html += '<input type="checkbox" ' + (enabled ? 'checked ' : '') + 'data-action="master-toggle" aria-label="' + this._esc(this._t("master_enabled")) + '">';
    html += '<span class="toggle-slider"></span>';
    html += '</label>';
    html += '</div>';
    html += '</div>';
    return html;
  }

  _renderTabsContent() {
    const tabs = ["covers", "facades", "rules", "scenarios", "settings", "log"];
    let html = '';
    for (const tab of tabs) {
      const isActive = this._activeTab === tab;
      html += '<button class="' + (isActive ? " active" : "") + '" data-tab="' + tab + '"' + (isActive ? ' aria-current="true"' : '') + '>' + this._tt("tabs", tab) + '</button>';
    }
    return html;
  }

  _renderInfoBarInline() {
    const sunState = this._hass?.states ? this._hass.states["sun.sun"] : null;
    const settings = this._config ? this._config.settings || {} : {};
    const tempEntity = settings.outdoor_temp_sensor;
    const tempState = tempEntity && this._hass?.states ? this._hass.states[tempEntity] : null;
    const tempVal = tempState && tempState.state !== "unavailable" && tempState.state !== "unknown" ? parseFloat(tempState.state) : null;
    const az = sunState && sunState.attributes ? sunState.attributes.azimuth : null;
    const el = sunState && sunState.attributes ? sunState.attributes.elevation : null;
    const weatherEntity = settings.weather_entity;
    const weatherState = weatherEntity && this._hass?.states ? this._hass.states[weatherEntity] : null;
    const weatherVal = weatherState && weatherState.state !== "unavailable" && weatherState.state !== "unknown" ? weatherState.state : null;
    const solarEntity = settings.solar_sensor;
    const solarState = solarEntity && this._hass?.states ? this._hass.states[solarEntity] : null;
    const solarVal = solarState && solarState.state !== "unavailable" && solarState.state !== "unknown" ? parseFloat(solarState.state) : null;
    if (az == null && el == null && tempVal == null && weatherVal == null && solarVal == null) return '';
    const belowHorizon = el != null && el < 0;
    const sunIcon = belowHorizon
      ? '<svg class="info-bar-icon" width="14" height="14" viewBox="0 0 24 24"><path d="M12 2a9.9 9.9 0 00-3.24.53A7 7 0 0015 9a7 7 0 01-6.47 6.97A9.98 9.98 0 0012 22c5.52 0 10-4.48 10-10S17.52 2 12 2z" fill="currentColor" opacity="0.65"/></svg>'
      : this._sunIconSvg(14);
    let widgets = [];
    if (az != null && el != null) {
      const sunTitle = this._t("info_sun_title");
      widgets.push('<span class="info-widget" title="' + this._esc(sunTitle) + '">' + sunIcon + '<span class="info-widget-value">' + Number(az).toFixed(1) + '\u00B0 / ' + Number(el).toFixed(1) + '\u00B0</span></span>');
    }
    if (tempVal != null) {
      const tempTitle = this._t("info_outdoor_title");
      const thermoIcon = '<svg class="info-bar-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/></svg>';
      widgets.push('<span class="info-widget" title="' + this._esc(tempTitle) + '">' + thermoIcon + '<span class="info-widget-value">' + tempVal.toFixed(1) + ' \u00B0C</span></span>');
    }
    if (weatherVal != null) {
      const weatherKey = "weather_" + String(weatherVal).replace(/-/g, "_");
      const translated = this._t(weatherKey);
      const weatherLabel = translated && translated !== weatherKey ? translated : String(weatherVal);
      widgets.push('<span class="info-widget" title="' + this._esc(weatherLabel) + '">' + this._weatherIconSvg(weatherVal) + '<span class="info-widget-value">' + this._esc(weatherLabel) + '</span></span>');
    }
    if (solarVal != null) {
      const threshold = settings.solar_threshold ?? 0;
      const exceeded = threshold > 0 && solarVal > threshold;
      const unit = solarState.attributes && solarState.attributes.unit_of_measurement ? ' ' + solarState.attributes.unit_of_measurement : '';
      const solarTitle = exceeded ? this._t("info_solar_exceeded_title") : this._t("info_solar_title");
      const activityIcon = '<svg class="info-bar-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.5.5 0 0 1-.96 0L9.24 2.18a.5.5 0 0 0-.96 0l-2.35 8.36A2 2 0 0 1 4 12H2"/></svg>';
      const cls = exceeded ? 'info-widget info-widget-highlight' : 'info-widget';
      widgets.push('<span class="' + cls + '" title="' + this._esc(solarTitle) + '">' + activityIcon + '<span class="info-widget-value">' + solarVal.toFixed(0) + this._esc(unit) + (exceeded ? ' \u25B2' : '') + '</span></span>');
    }
    return '<span class="info-bar">' + widgets.join('') + '</span>';
  }

  _posBar(pos, variant) {
    if (pos == null) return '\u2013';
    const p = Math.max(0, Math.min(100, pos));
    const cls = variant ? ' pos-bar-' + variant : '';
    return '<span class="pos-bar' + cls + '"><span class="pos-bar-track"><span class="pos-bar-fill" style="width:' + p + '%"></span></span><span class="pos-bar-label">' + pos + '%</span></span>';
  }

  // Current position in the rules' (logical) frame: inverted covers are
  // mirrored like the coordinator does. Returns { pos, raw } (raw = HA value).
  _coverCurrentPos(cover, haState) {
    let v = haState && haState.attributes ? haState.attributes.current_position : null;
    // Open/close-only covers: read the position from the state
    if (v == null && haState) v = { open: 100, closed: 0 }[haState.state] ?? null;
    const raw = v == null || v === "" || isNaN(Number(v)) ? null : Number(v);
    if (raw == null) return { pos: null, raw: null };
    return { pos: cover && cover.inverted ? 100 - raw : raw, raw };
  }

  // Position cell: current (logical) vs target, with the raw HA value in a
  // tooltip for inverted covers.
  _posCellHtml(cover, haState, target) {
    const { pos, raw } = this._coverCurrentPos(cover, haState);
    // Unknown current position (cover unavailable): don't draw the target
    // as if it were the current position.
    if (pos == null) return '\u2013';
    const bar = this._posBarCombined(pos, target);
    if (!(cover && cover.inverted) || raw == null) return bar;
    const tip = this._t("cover_position_inverted_tip").replace("{raw}", raw);
    return `<span class="pos-inverted" title="${this._esc(tip)}">${bar}<span class="pos-inverted-mark" aria-label="${this._esc(tip)}">\u21C5</span></span>`;
  }

  // Combined position bar: single column shows current + target with a marker when they differ
  _posBarCombined(current, target) {
    if (current == null && target == null) return '\u2013';
    const diverges = current != null && target != null && Math.abs(current - target) >= 1;
    if (!diverges) {
      const p = current ?? target;
      return this._posBar(p);
    }
    // Two-stop fill: solid up to min(current,target), striped from min to max, empty beyond.
    // The solid portion is the position that is "guaranteed" reached; the striped portion is the delta in flux.
    const c = Math.max(0, Math.min(100, current));
    const t = Math.max(0, Math.min(100, target));
    const lo = Math.min(c, t);
    const hi = Math.max(c, t);
    const rangeWidth = hi - lo;
    const title = this._t("cover_position_target_label") + this._colon() + target + "%";
    return '<span class="pos-bar pos-bar-diverges" title="' + this._esc(title) + '">'
      + '<span class="pos-bar-track">'
        + '<span class="pos-bar-fill" style="width:' + lo + '%"></span>'
        + '<span class="pos-bar-range" style="left:' + lo + '%;width:' + rangeWidth + '%"></span>'
      + '</span>'
      + '<span class="pos-bar-label"><span class="pos-bar-current-val">' + current + '%</span><span class="pos-bar-arrow">\u2192</span><span class="pos-bar-target-val">' + target + '%</span></span>'
    + '</span>';
  }

  _renderRuleCell(live) {
    const ruleId = live && live.rule_id;
    const ruleName = (live && live.rule_name) || this._t("cover_no_rule");
    if (ruleId && this._config && this._config.rules && this._config.rules[ruleId]) {
      return '<a class="rule-link" data-action="goto-rule" data-rule-id="' + this._esc(ruleId) + '" title="' + this._esc(this._t("cover_goto_rule")) + '">' + this._esc(ruleName) + '</a>';
    }
    return this._esc(ruleName);
  }

  _sunIconSvg(size = 14) {
    return '<svg class="sun-icon-svg" width="' + size + '" height="' + size + '" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5" fill="currentColor"/><g stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></g></svg>';
  }

  // Lucide-based weather icon by HA weather state
  _weatherIconSvg(state, size = 14) {
    const a = 'none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round';
    const paths = {
      sunny: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
      clear_night: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
      cloudy: '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
      partlycloudy: '<path d="M12 2v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="M20 12h2"/><path d="m19.07 4.93-1.41 1.41"/><path d="M15.947 12.65a4 4 0 0 0-5.925-4.128"/><path d="M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6Z"/>',
      rainy: '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/>',
      pouring: '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/>',
      snowy: '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M8 15h.01"/><path d="M8 19h.01"/><path d="M12 17h.01"/><path d="M12 21h.01"/><path d="M16 15h.01"/><path d="M16 19h.01"/>',
      snowy_rainy: '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M11 20v2"/><path d="M8 18h.01"/><path d="M16 18h.01"/>',
      fog: '<path d="M3 5h18"/><path d="M3 10h18"/><path d="M3 15h18"/><path d="M3 20h18"/>',
      windy: '<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
      windy_variant: '<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
      lightning: '<path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><path d="m13 12-3 5h4l-3 5"/>',
      lightning_rainy: '<path d="M16 14v6"/><path d="M8 14v6"/><path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><path d="m13 12-3 5h4l-3 5"/>',
      hail: '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v2"/><path d="M8 14v2"/><path d="M16 20h.01"/><path d="M8 20h.01"/><path d="M12 16v2"/><path d="M12 22h.01"/>',
      exceptional: '<path d="M12 9v4"/><path d="M12 17h.01"/><circle cx="12" cy="12" r="10"/>'
    };
    const key = String(state || "").replace(/-/g, "_");
    const p = paths[key] || paths.cloudy;
    return '<svg class="info-bar-icon" width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="' + a + '">' + p + '</svg>';
  }

  // Lucide-style inline SVG icons for settings sections
  _lucideIcon(name, size = 16) {
    const a = 'none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round';
    const paths = {
      house: '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
      gauge: '<path d="M12 16v-4"/><path d="M12 8h.01"/><circle cx="12" cy="12" r="10"/>',
      thermometer: '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
      wind: '<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
      cog: '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
      archive: '<rect width="20" height="5" x="2" y="3" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>',
      menu: '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
      info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
      app_window: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M10 4v4"/><path d="M2 8h20"/><path d="M6 4v4"/>',
      sliders: '<line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/><line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/><line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/>',
      copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
      move_vertical: '<polyline points="8 18 12 22 16 18"/><polyline points="8 6 12 2 16 6"/><line x1="12" x2="12" y1="2" y2="22"/>',
      activity: '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.5.5 0 0 1-.96 0L9.24 2.18a.5.5 0 0 0-.96 0l-2.35 8.36A2 2 0 0 1 4 12H2"/>',
      copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
      shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
      thermometer_snowflake: '<path d="m10 20-1.25-2.5L6 18"/><path d="M10 4 8.75 6.5 6 6"/><path d="M10.585 15H10"/><path d="M2 12h6.5L10 9"/><path d="M20 14.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0z"/><path d="m4 10 1.5 2L4 14"/><path d="m7 21 3-6-1.5-3"/><path d="m7 3 3 6h2"/>',
      thermometer_sun: '<path d="M12 2v2"/><path d="M12 8a4 4 0 0 0-1.645 7.647"/><path d="M2 12h2"/><path d="M20 14.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0z"/><path d="m4.93 4.93 1.41 1.41"/><path d="m6.34 17.66-1.41 1.41"/>',
      sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>'
    };
    return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="' + a + '">' + (paths[name] || '') + '</svg>';
  }

  // Room temperature cell of the cover list: text colour, icon and tooltip
  // for the comfort mode. The icon (snowflake / sun thermometer) carries the
  // meaning; the colours follow the chosen convention: "action" (default:
  // cold room red = to heat, hot room blue = to cool) or thermometer (cold
  // blue, hot red).
  _tempCellParts(cm, tempVal) {
    const cold = cm === "heating", hot = cm === "cooling";
    const thermo = (this._config?.settings || {}).temp_color_thermometer === true;
    const red = "var(--ca-danger)", blue = "var(--ca-info)";
    const color = cold ? (thermo ? blue : red) : hot ? (thermo ? red : blue) : "";
    const icon = cold || hot
      ? '<span class="temp-icon" aria-hidden="true">' + this._lucideIcon(cold ? "thermometer_snowflake" : "thermometer_sun", 14) + '</span>'
      : "";
    const text = tempVal != null ? tempVal.toFixed(1) + " \u00B0C" : "\u2013";
    return { color, html: icon + this._esc(text), title: cm ? this._t("comfort_" + cm) : "" };
  }

  _renderContent() {
    switch (this._activeTab) {
      case "covers": return this._renderCovers();
      case "facades": return this._renderFacades();
      case "rules": return this._renderRules();
      case "scenarios": return this._renderScenarios();
      case "settings": return this._renderSettings();
      case "log": return this._renderLog();
      default: return '';
    }
  }

  _renderConfirmDialog() {
    if (!this._confirmCallback) return '';
    return '<div class="confirm-overlay" data-action="confirm-cancel">'
      + '<div class="confirm-dialog" role="alertdialog" aria-modal="true" aria-label="' + this._esc(this._confirmMessage) + '">'
      + '<p>' + this._esc(this._confirmMessage) + '</p>'
      + '<div class="actions">'
      + '<button class="btn btn-secondary" data-action="confirm-cancel">' + this._t("cancel") + '</button>'
      + '<button class="btn btn-danger" data-action="confirm-ok">' + this._esc(this._confirmOkLabel || this._t("delete")) + '</button>'
      + '</div></div></div>';
  }

  /* ============================================================
   * TAB: Covers
   * ============================================================ */
  _renderCovers() {
    const covers = this._config.covers || {};
    const entries = Object.values(covers);
    const available = this._config.available_covers || [];

    let html = '';

    // Collapsible add covers section
    if (available.length > 0) {
      if (this._addingCover) {
        html += '<div class="card mb-16"><div class="card-header">';
        html += `<span>${this._t("cover_add")}</span>`;
        html += `<button class="btn-icon" data-action="cover-add-cancel" title="${this._t("cancel")}">&#10005;</button>`;
        html += '</div>';
        html += '<div class="card-body"><div class="form-row">';
        html += `<select id="cover-add-select" class="add-cover-select" multiple>`;
        for (const a of available) {
          html += `<option value="${this._esc(a.entity_id)}">${this._esc(a.name)} (${this._esc(a.entity_id)})</option>`;
        }
        html += '</select></div>';
        html += `<div class="form-row mt-8"><button class="btn btn-primary" data-action="cover-add">${this._t("add")}</button></div>`;
        html += '</div></div>';
      } else {
        html += `<div class="mb-12"><button class="btn btn-sm" data-action="cover-add-start">+ ${this._t("cover_add")}</button></div>`;
      }
    }

    if (entries.length === 0 && !this._addingCover) {
      return html + `<div class="empty-state">${this._t("none")}</div>`;
    }

    html += '<div class="card"><div class="table-scroll"><table class="data-table">';
    html += '<thead><tr>';
    const sk = this._coverSort.key, sd = this._coverSort.dir;
    const sth = (key, label) => {
      const active = sk === key;
      const arrow = active ? (sd === "asc" ? "\u25B2" : "\u25BC") : "\u2195";
      const ariaSort = active ? ` aria-sort="${sd === "asc" ? "ascending" : "descending"}"` : "";
      return `<th class="sortable${active ? " sorted" : ""}" data-action="cover-sort" data-sort="${key}" tabindex="0"${ariaSort}>${label}<span class="sort-arrow">${arrow}</span></th>`;
    };
    html += sth("name", this._t("name"));
    html += sth("facade", this._t("cover_facade"));
    html += sth("status", this._t("cover_status"));
    html += sth("temp", this._t("cover_temp"));
    html += `<th>${this._t("cover_position")}</th>`;
    html += `<th>${this._t("cover_rule")}</th>`;
    html += `<th>${this._t("cover_last_change")}</th>`;
    html += '<th class="row-chevron-head" aria-hidden="true"></th>';
    html += '</tr></thead><tbody>';

    // Sort entries
    const sorted = [...entries].sort((a, b) => {
      let va, vb;
      switch (sk) {
        case "name": va = a.name || ""; vb = b.name || ""; break;
        case "facade": va = this._getFacadeName(a.facade_id); vb = this._getFacadeName(b.facade_id); break;
        case "status": va = a.status || "auto"; vb = b.status || "auto"; break;
        case "temp": {
          const sa = a.indoor_temp_sensor || (this._config.settings || {}).indoor_temp_sensor;
          const sb = b.indoor_temp_sensor || (this._config.settings || {}).indoor_temp_sensor;
          const ta = sa && this._hass?.states && this._hass.states[sa] ? parseFloat(this._hass.states[sa].state) : -999;
          const tb = sb && this._hass?.states && this._hass.states[sb] ? parseFloat(this._hass.states[sb].state) : -999;
          va = isNaN(ta) ? -999 : ta; vb = isNaN(tb) ? -999 : tb;
          return sd === "asc" ? va - vb : vb - va;
        }
        default: va = a.name || ""; vb = b.name || "";
      }
      const cmp = String(va).localeCompare(String(vb), "de", { sensitivity: "base" });
      return sd === "asc" ? cmp : -cmp;
    });

    for (const c of sorted) {
      const facadeName = this._getFacadeName(c.facade_id);
      const selected = this._selectedCover === c.entity_id ? " selected" : "";
      const statusClass = "status-" + (c.status || "auto");
      const haState = this._hass?.states ? this._hass.states[c.entity_id] : null;
      const live = (this._config.live_covers || {})[c.entity_id] || {};
      const targetPos = live.target_position;
      const hysteresis = live.hysteresis;
      let infoIcon = '';
      if (hysteresis === "position") {
        infoIcon = ' <span class="status-badge status-paused hysteresis-badge" title="' + this._esc(this._t("cover_hysteresis_position")) + '">&#8597;</span>';
      } else if (hysteresis === "time") {
        infoIcon = ' <span class="status-badge status-paused hysteresis-badge" title="' + this._esc(this._t("cover_hysteresis_time")) + '">&#9202;</span>';
      }
      const cm = live.comfort_mode;
      // Rule name -- if a rule is matching, render as link to Rules tab
      const ruleCellHtml = this._renderRuleCell(live);
      // Sun on facade
      const liveFacade = c.facade_id ? ((this._config.live_facades || {})[c.facade_id] || {}) : {};
      const sunIcon = liveFacade.sun_on_facade ? ' <span class="live-icon-sun" title="' + this._esc(this._t("facade_sun_active")) + '">' + this._sunIconSvg(12) + '</span>' : '';
      // Last change
      const lastChange = live.last_change ? this._formatTimeAgo(live.last_change) : "";
      // Pause info
      const pauseLeft = (c.status === "paused" && live.pause_until) ? this._formatPauseRemaining(live.pause_until) : "";
      const resumeBtn = c.status === "paused" ? '<button class="btn-icon resume-x" data-action="cover-resume" data-id="' + this._esc(c.entity_id) + '" title="' + this._esc(this._t("cover_resume")) + '">&#10005;</button>' : '';
      html += `<tr class="${selected}" data-action="select-cover" data-id="${this._esc(c.entity_id)}" tabindex="0">`;
      html += `<td data-live-name="${this._esc(c.entity_id)}">${this._esc(c.name)}</td>`;
      html += `<td class="nowrap" data-live-facade="${this._esc(c.entity_id)}">${this._esc(facadeName)}${sunIcon}</td>`;
      html += `<td class="nowrap" data-live-status="${this._esc(c.entity_id)}"><span class="status-badge ${statusClass}">${this._esc(this._t("status_" + (c.status || "auto")) || c.status || "auto")}</span>${pauseLeft ? '<span class="pause-remaining">' + pauseLeft + '</span>' : ''}${resumeBtn}</td>`;
      const tempSensor = c.indoor_temp_sensor || (this._config.settings || {}).indoor_temp_sensor;
      const tempState = tempSensor && this._hass?.states ? this._hass.states[tempSensor] : null;
      const tempVal = tempState && tempState.state !== "unavailable" && tempState.state !== "unknown" ? parseFloat(tempState.state) : null;
      const tp = this._tempCellParts(cm, tempVal);
      html += `<td class="nowrap${tp.color ? ' temp-mode' : ''}" data-live-temp="${this._esc(c.entity_id)}"${tp.color ? ' style="color:' + tp.color + '"' : ''}${tp.title ? ' title="' + this._esc(tp.title) + '"' : ''}>${tp.html}</td>`;
      html += `<td class="pos-cell" data-live-position="${this._esc(c.entity_id)}">${this._posCellHtml(c, haState, targetPos)}${infoIcon}</td>`;
      html += `<td data-live-rule="${this._esc(c.entity_id)}">${ruleCellHtml}</td>`;
      html += `<td class="last-change" data-live-lastchange="${this._esc(c.entity_id)}">${lastChange}</td>`;
      html += '<td class="row-chevron" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg></td>';
      html += '</tr>';
    }

    html += '</tbody></table></div></div>';
    return html;
  }

  /* ---------- Slide-out for cover editing ---------- */
  _renderSlideOut() {
    const open = this._slideOpen && this._selectedCover;
    const cover = open ? (this._config.covers || {})[this._selectedCover] : null;

    let html = `<div class="slide-overlay${open ? " open" : ""}" data-action="close-slide" aria-hidden="true"></div>`;
    html += `<div class="slide-panel${open ? " open" : ""}"${cover ? ` data-cover="${this._esc(cover.entity_id)}"` : ""}${cover ? ` role="dialog" aria-modal="true" aria-label="${this._esc(cover.name)}"` : ' aria-hidden="true"'}>`;

    if (cover) {
      html += `<div class="slide-header">
        <button class="btn-icon slide-back" data-action="close-slide" title="${this._t("close")}" aria-label="${this._t("close")}">&#8592;</button>
        <h2>${this._esc(cover.name)}</h2>
        <button class="btn-icon slide-close" data-action="close-slide" title="${this._t("close")}" aria-label="${this._t("close")}">&#10005;</button>
      </div>`;
      html += '<div class="slide-body">';

      const cid = this._esc(cover.entity_id);
      const cs = this._config.settings || {};
      const ctl = (field) => `[data-field="${field}"][data-id="${cover.entity_id.replace(/["\\]/g, "\\$&")}"]`;
      const sum = this._coverSectionSummaries(cover);
      const allIds = ["base", "window", "room", "sun", "automation"];
      const allOpen = allIds.every(id => this._expandedSections[id]);
      html += `<div class="slide-expand-bar"><button type="button" class="btn-link" data-action="sections-toggle-all" data-ids="${allIds.join(",")}">${
        this._t(allOpen ? "cover_collapse_all" : "cover_expand_all")}</button></div>`;

      // Section: General
      html += this._renderSection("base", this._t("cover_section_base"), () => {
        const items = [
          this._renderToggle("cover_auto_enabled", cover.auto_enabled, "cover-toggle", cover.entity_id, "auto_enabled"),
          this._renderFacadeDropdown(cover) + this._hint("cover_facade_hint"),
          this._renderToggle("cover_inverted", cover.inverted, "cover-toggle", cover.entity_id, "inverted", "cover_inverted_hint"),
        ];
        if (cover.supports_tilt) {
          items.push(this._renderToggle("cover_inverted_tilt", cover.inverted_tilt, "cover-toggle", cover.entity_id, "inverted_tilt"));
        }
        return this._sepList(items);
      }, sum.base);

      // Section: Window (open = lock, tilted = ventilation)
      html += this._renderSection("window", this._t("cover_section_window"), () => {
        let s = '';
        const globalLockPos = cs.lock_position ?? 100;
        const lockTilt = cover.supports_tilt ? `<div class="form-group">
                <label>${this._t("cover_lock_tilt")}</label>
                <input type="number" min="0" max="100" value="${this._num(cover.lock_tilt_position, "")}" placeholder="${this._t("none")}" data-action="cover-input" data-id="${cid}" data-field="lock_tilt_position">
              </div>` : "";
        s += this._optBox({
          title: this._t("cover_lock_box_title"),
          dep: ctl("lock_sensor"), mode: "value",
          head: `<div class="form-group">
            <label>${this._t("cover_lock_sensor")}</label>
            ${this._renderCoverEntitySelect("lock_sensor", cover.lock_sensor, cover.entity_id, "binary_sensor", null)}
            ${this._renderSensorValue(cover.lock_sensor)}
            ${this._hint("cover_lock_sensor_hint")}
          </div>`,
          offNote: this._t("cover_lock_off_note"),
          body: `${this._renderToggle("cover_lock_hold", !!cover.lock_hold_position, "cover-toggle", cover.entity_id, "lock_hold_position", "cover_lock_hold_hint")}
            ${this._optBox({
              cls: "opt-box-flat",
              dep: ctl("lock_hold_position"), mode: "unchecked",
              body: `<div class="form-group">
                <label>${this._t("cover_lock_position")}</label>
                <input type="number" min="0" max="100" value="${this._num(cover.lock_position, "")}" placeholder="${globalLockPos}" data-action="cover-input" data-id="${cid}" data-field="lock_position">
                ${this._hint("cover_lock_position_hint")}
              </div>${lockTilt}`,
            })}`,
        });
        const globalVentPos = cs.vent_position ?? 30;
        const ventTilt = cover.supports_tilt ? `<div class="form-group">
            <label>${this._t("cover_vent_tilt")}</label>
            <input type="number" min="0" max="100" value="${this._num(cover.vent_tilt_position, "")}" placeholder="${this._t("none")}" data-action="cover-input" data-id="${cid}" data-field="vent_tilt_position">
          </div>` : "";
        s += this._optBox({
          title: this._t("cover_vent_box_title"),
          dep: ctl("vent_sensor"), mode: "value",
          head: `<div class="form-group">
            <label>${this._t("cover_vent_sensor")}</label>
            ${this._renderCoverEntitySelect("vent_sensor", cover.vent_sensor, cover.entity_id, "binary_sensor", null)}
            ${this._renderSensorValue(cover.vent_sensor)}
            ${this._hint("cover_vent_sensor_hint")}
          </div>`,
          offNote: this._t("cover_vent_off_note"),
          body: `<div class="form-group">
            <label>${this._t("cover_vent_position")}</label>
            <input type="number" min="0" max="100" value="${this._num(cover.vent_position, "")}" placeholder="${globalVentPos}" data-action="cover-input" data-id="${cid}" data-field="vent_position">
            ${this._hint("cover_vent_position_hint")}
          </div>${ventTilt}`,
        });
        return s;
      }, sum.window);

      // Section: Room (indoor temperature setpoints + occupancy)
      html += this._renderSection("room", this._t("cover_section_room"), () => {
        let s = '';
        // Global setpoints actually used (entity from Settings when readable)
        const globalMin = this._effectiveThreshold(cs.comfort_temp_min_entity, cs.comfort_temp_min ?? 21);
        const globalMax = this._effectiveThreshold(cs.comfort_temp_max_entity, cs.comfort_temp_max ?? 25);
        const globalNote = (entity, value) => `<div class="ha-help global-note">${this._esc(this._t("cover_comfort_global")
          .replace("{v}", value).replace("{src}", entity ? this._haEntityName(entity) : this._t("cover_comfort_src_settings")))}</div>`;
        s += this._optBox({
          title: this._t("settings_comfort_range_title"),
          body: `<div class="form-group">
            <label>${this._L("cover_indoor_temp")}</label>
            ${this._renderCoverEntitySelect("indoor_temp_sensor", cover.indoor_temp_sensor, cover.entity_id, "sensor", "temperature")}
            ${this._renderSensorValue(cover.indoor_temp_sensor)}
            ${this._hint("cover_indoor_temp_hint")}
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>${this._L("cover_comfort_min")}</label>
              <input type="number" step="0.5" value="${this._num(cover.comfort_temp_min, "")}" placeholder="${globalMin}" data-action="cover-input" data-id="${cid}" data-field="comfort_temp_min">
              ${globalNote(cs.comfort_temp_min_entity, globalMin)}
              ${this._renderThresholdEntity(`data-action="cover-input" data-id="${cid}" data-field="comfort_temp_min_entity"`, cover.comfort_temp_min_entity, "temperature")}
            </div>
            <div class="form-group">
              <label>${this._L("cover_comfort_max")}</label>
              <input type="number" step="0.5" value="${this._num(cover.comfort_temp_max, "")}" placeholder="${globalMax}" data-action="cover-input" data-id="${cid}" data-field="comfort_temp_max">
              ${globalNote(cs.comfort_temp_max_entity, globalMax)}
              ${this._renderThresholdEntity(`data-action="cover-input" data-id="${cid}" data-field="comfort_temp_max_entity"`, cover.comfort_temp_max_entity, "temperature")}
            </div>
          </div>
          ${this._hint("cover_comfort_hint")}`,
        });
        s += this._optBox({
          title: this._t("cover_occupancy_box_title"),
          dep: ctl("occupancy_sensor"), mode: "value",
          head: `<div class="form-group">
            <label>${this._t("cover_occupancy_sensor")}</label>
            ${this._renderCoverEntitySelect("occupancy_sensor", cover.occupancy_sensor, cover.entity_id,
              ["binary_sensor", "input_boolean", "input_select", "person", "device_tracker"], null)}
            ${this._renderSensorValue(cover.occupancy_sensor)}
            ${this._hint("cover_occupancy_sensor_hint")}
          </div>`,
          offNote: this._t("cover_occupancy_off_note"),
          body: this._renderOccupancyStates(cover),
        });
        return s;
      }, sum.room);

      // Section: Sun exposure (null = follow the global setting)
      html += this._renderSection("sun", this._t("settings_section_comfort"), () => {
        return `<div class="settings-hint-intro">${this._esc(this._t("cover_sun_switches_hint"))}</div>`
          + this._sepList([
            this._renderCoverTristate(cover, "sun_heating_ignore", "sun_heating_label", "sun_heating_hint"),
            this._renderCoverSunComfort(cover),
          ]);
      }, sum.sun);

      // Section: Automation (per-cover overrides of Settings › Automation)
      html += this._renderSection("automation", this._t("cover_section_automation"), () => {
        let s = '';
        const globalPause = cs.pause_duration ?? 10;
        s += `<div class="form-group">
          <label>${this._t("cover_pause_duration")}</label>
          <input type="number" min="1" max="480" value="${this._num(cover.pause_duration)}" placeholder="${globalPause}" data-action="cover-input" data-id="${cid}" data-field="pause_duration">
          <div class="ha-help">${this._esc(this._t("cover_default_note").replace("{v}", globalPause + " min"))}</div>
          ${this._hint("cover_pause_duration_hint")}
        </div>`;
        s += this._renderCoverTristate(cover, "pause_resume_on_match", "pause_resume_on_match", "pause_resume_on_match_hint");
        const globalMinChange = cs.min_position_change ?? 5;
        s += `<div class="form-group">
          <label>${this._L("cover_min_pos_change")}</label>
          <input type="number" min="1" max="50" value="${this._num(cover.min_position_change, "")}" placeholder="${globalMinChange}" data-action="cover-input" data-id="${cid}" data-field="min_position_change">
          <div class="ha-help">${this._esc(this._t("cover_default_note").replace("{v}", globalMinChange + " %"))}</div>
          ${this._hint("cover_min_pos_change_hint")}
        </div>`;
        const globalMinTime = cs.min_time_between_changes ?? 300;
        s += `<div class="form-group">
          <label>${this._L("cover_min_time")}</label>
          <input type="number" min="60" max="3600" value="${this._num(cover.min_time_between_changes, "")}" placeholder="${globalMinTime}" data-action="cover-input" data-id="${cid}" data-field="min_time_between_changes">
          <div class="ha-help">${this._esc(this._t("cover_default_note").replace("{v}", globalMinTime + " s"))}</div>
          ${this._hint("cover_min_time_hint")}
        </div>`;
        const { measured, placeholder: travelPlaceholder, usedTxt, fmtS } = this._travelInfo(cover);
        s += `<div class="form-group">
          <label>${this._t("cover_travel_time")}</label>
          <input type="number" min="1" max="300" value="${this._num(cover.travel_time, "")}" placeholder="${this._esc(travelPlaceholder)}" data-action="cover-input" data-id="${cid}" data-field="travel_time">
          <div class="ha-help">${measured != null
            ? `${this._esc(this._t("cover_travel_measured").replace("{s}", fmtS(measured)))}
               <button type="button" class="btn-link" data-action="cover-travel-reset" data-id="${cid}">${this._t("cover_travel_reset")}</button>`
            : this._esc(this._t("cover_travel_not_measured"))}</div>
          <div class="ha-help" data-travel-used="${cid}">${this._esc(usedTxt)}</div>
          ${this._hint("cover_travel_time_hint")}
        </div>`;
        return `<div class="sep-list">${s}</div>`;
      }, sum.automation);

      html += `<div class="slide-log-link">
        <button class="btn btn-secondary btn-sm" data-action="cover-show-log" data-id="${this._esc(cover.entity_id)}">${this._t("cover_show_log")}</button>
      </div>`;
      html += `<div class="slide-close-bottom">
        <button class="btn btn-secondary" data-action="close-slide">${this._t("close")}</button>
      </div>`;
      html += `<div class="slide-delete-wrap">
        <button class="btn btn-danger" data-action="cover-delete" data-id="${this._esc(cover.entity_id)}">${this._t("cover_remove")}</button>
      </div>`;
      html += '</div>'; // slide-body
    }

    html += '</div>'; // slide-panel
    return html;
  }

  _renderSection(id, title, contentFn, summary = "") {
    const expanded = this._expandedSections[id];
    const arrowClass = expanded ? "arrow expanded" : "arrow";
    const iconMap = { base: "info", window: "app_window", automation: "cog", room: "house", sun: "sun",
      sensors: "gauge", advanced: "sliders", tilt: "move_vertical" };
    const iconName = iconMap[id];
    const icon = iconName ? `<span class="section-icon">${this._lucideIcon(iconName, 16)}</span>` : "";
    return `<div class="section">
      <div class="section-header" data-action="toggle-section" data-section="${id}" tabindex="0" role="button" aria-expanded="${expanded ? "true" : "false"}">
        ${icon}<span class="section-title">${this._esc(title)}${summary && !expanded
          ? `<span class="section-summary">${this._esc(summary)}</span>` : ""}</span>
        <span class="${arrowClass}">&#9654;</span>
      </div>
      <div class="section-body${expanded ? " expanded" : ""}">
        ${contentFn()}
      </div>
    </div>`;
  }

  // Framed group of options. With `dep` (CSS selector of the controlling
  // input) the body is greyed out and its inputs disabled while the control
  // is off; values are kept and still saved. Modes: "checked", "unchecked",
  // "value" (non-empty), "tristate" ("" = follow `global`).
  _optBox({ dep = null, mode = "checked", global = null, title = "", head = "", body = "", offNote = "", cls = "", value = null, force = false } = {}) {
    const depAttrs = dep
      ? ` data-dep="${this._esc(dep)}" data-dep-mode="${mode}"${global == null ? "" : ` data-dep-global="${global ? "1" : "0"}"`}`
        + (value == null ? "" : ` data-dep-value="${this._esc(value)}"`) + (force ? ` data-dep-force="1"` : "")
      : "";
    return `<div class="opt-box${cls ? " " + cls : ""}"${depAttrs}>
      ${title ? `<div class="opt-box-title">${this._esc(title)}</div>` : ""}
      ${head}
      ${offNote ? `<div class="opt-box-offnote">${this._esc(offNote)}</div>` : ""}
      <div class="opt-box-body">${body}</div>
    </div>`;
  }

  // Apply the enabled/greyed state of every dependent option box.
  _refreshDeps() {
    const root = this.shadowRoot;
    if (!root) return;
    this._refreshSunExplain();
    this._refreshHystExplains();
    this._refreshEntityDriven();
    root.querySelectorAll(".opt-box[data-dep]").forEach(box => {
      let ctl = null;
      try { ctl = root.querySelector(box.dataset.dep); } catch (e) { ctl = null; }
      let on = !!ctl && !ctl.disabled;
      if (on) {
        const mode = box.dataset.depMode || "checked";
        if (mode === "checked") on = !!ctl.checked;
        else if (mode === "unchecked") on = !ctl.checked;
        else if (mode === "value") on = String(ctl.value || "").trim() !== "";
        else if (mode === "tristate") on = ctl.value === "" ? box.dataset.depGlobal === "1" : ctl.value === "true";
        else if (mode === "equals") on = ctl.value === box.dataset.depValue;
      }
      if (box.dataset.depForce === "1") on = true;
      box.classList.toggle("opt-off", !on);
      const body = box.querySelector(":scope > .opt-box-body");
      if (!body) return;
      body.querySelectorAll("input, select, textarea, button").forEach(el => {
        if (!on) {
          if (!el.disabled) { el.disabled = true; el.dataset.depDisabled = "1"; }
        } else if (el.dataset.depDisabled) {
          el.disabled = false;
          delete el.dataset.depDisabled;
        }
      });
    });
  }

  // "How does it work?" table of the Sun on facade card. Rows matching the
  // current (draft) choices are highlighted by _refreshSunExplain.
  // A threshold driven by an entity: the number field is replaced by a greyed
  // box with the entity's value; the number stays stored as the fallback used
  // while the entity is unavailable.
  _refreshEntityDriven() {
    const root = this.shadowRoot;
    if (!root) return;
    root.querySelectorAll("[data-threshold-entity]").forEach(sel => {
      const group = sel.closest(".form-group");
      const num = group ? group.querySelector(':scope > input[type="number"]') : null;
      if (!num) return;
      let shadow = num.nextElementSibling;
      if (!shadow || !shadow.classList.contains("entity-shadow")) {
        shadow = document.createElement("div");
        shadow.className = "entity-shadow";
        num.insertAdjacentElement("afterend", shadow);
      }
      const entity = sel.value;
      num.classList.toggle("entity-driven", !!entity);
      shadow.hidden = !entity;
      group.querySelectorAll(":scope > .global-note").forEach(n => { n.hidden = !!entity; });
      if (!entity) return;
      const st = this._hass && this._hass.states ? this._hass.states[entity] : null;
      const v = st ? parseFloat(st.state) : NaN;
      const unit = st && st.attributes.unit_of_measurement ? " " + st.attributes.unit_of_measurement : "";
      const fallback = num.value !== "" ? num.value : num.placeholder;
      const html = `<div class="entity-shadow-value">${this._esc(Number.isFinite(v) ? String(v) + unit : "—")}</div>`
        + (fallback !== "" && fallback != null
          ? `<div class="entity-shadow-note">${this._esc(this._t("threshold_fallback").replace("{v}", fallback))}</div>` : "");
      if (shadow.dataset.sig !== html) { shadow.innerHTML = html; shadow.dataset.sig = html; }
    });
  }

  // "How does it work?" blocks of the hysteresis settings. The table is
  // computed from the values currently in the form (draft included) and
  // refreshed on every input by _refreshHystExplains.
  _renderHystExplain(kind) {
    const open = this._explainOpen && this._explainOpen[kind];
    const body = this._hystBody(kind, this._hystValues(kind));
    return `<details class="sun-explain" data-hyst="${kind}"${open ? " open" : ""}>
      <summary data-action="explain-toggle" data-key="${kind}">${this._esc(this._t("hyst_title_" + kind))}</summary>
      <div class="sun-explain-body" data-hyst-body>${body}</div>
    </details>`;
  }

  _refreshHystExplains() {
    const root = this.shadowRoot;
    if (!root) return;
    root.querySelectorAll("details[data-hyst]").forEach(d => {
      const body = d.querySelector("[data-hyst-body]");
      if (!body) return;
      const html = this._hystBody(d.dataset.hyst, this._hystValues(d.dataset.hyst));
      if (body.dataset.sig !== html) { body.innerHTML = html; body.dataset.sig = html; }
    });
  }

  _hystValues(kind) {
    const s = (this._config && this._config.settings) || {};
    const root = this.shadowRoot;
    const field = (name) => root ? root.querySelector(`[data-settings-field="${name}"]`) : null;
    const str = (name) => { const el = field(name); return el ? el.value : (s[name] || ""); };
    const num = (name, def) => { const v = parseFloat(str(name)); return Number.isFinite(v) ? v : def; };
    const unitOf = (id) => {
      const st = id && this._hass && this._hass.states ? this._hass.states[id] : null;
      return (st && st.attributes.unit_of_measurement) || "";
    };
    if (kind === "comfort") {
      return {
        a: this._effectiveThreshold(str("comfort_temp_min_entity"), num("comfort_temp_min", 21)),
        b: this._effectiveThreshold(str("comfort_temp_max_entity"), num("comfort_temp_max", 25)),
        h: num("comfort_hysteresis", 1),
      };
    }
    if (kind === "rules") {
      // Real example taken from the rules when one uses the condition
      const h = num("threshold_hysteresis", 0.5);
      const rules = Object.values((this._config && this._config.rules) || {})
        .sort((x, y) => (y.enabled !== false) - (x.enabled !== false));
      for (const r of rules) {
        for (const c of r.conditions || []) {
          if (c.type !== "temperature_above" && c.type !== "temperature_below") continue;
          const p = c.params || {};
          const t = parseFloat(p.temperature != null ? p.temperature : p.value);
          if (Number.isFinite(t)) return { t, h, above: c.type === "temperature_above", rule: r.name || r.id };
        }
      }
      return { t: 18, h, above: true, rule: null };
    }
    if (kind === "solar") {
      const t = this._effectiveThreshold(str("solar_threshold_entity"), num("solar_threshold", 0));
      const h = num("solar_hysteresis", 0), u = unitOf(str("solar_sensor"));
      return t > 0 ? { t, h, u, ex: false } : { t: 30000, h: h || 5000, u: u || "lx", ex: true };
    }
    const t = num("wind_speed_threshold", 0), u = unitOf(str("wind_sensor"));
    let h = num("wind_speed_hysteresis", 0);
    if (t > 0) { if (h >= t) h = 0; return { t, h, u, ex: false }; }
    return { t: 50, h: h > 0 && h < 50 ? h : 10, u: u || "km/h", ex: true };
  }

  _hystBody(kind, v) {
    const lang = (this._hass && this._hass.language) || "en";
    const fmt = (x) => {
      const r = String(Math.round(x * 100) / 100);
      return /^(fr|de)/.test(lang) ? r.replace(".", ",") : r;
    };
    const fu = (x, u) => fmt(x) + (u ? " " + u : "");
    const tr = (key, map) => {
      let out = this._t(key);
      for (const [k, val] of Object.entries(map || {})) out = out.split("{" + k + "}").join(val);
      return out;
    };
    const between = (a, b, u) => tr("hyst_between", { a: fmt(a), b: fmt(b) }) + (u ? " " + u : "");
    const table = (cols, rows) => `<table class="sun-explain-table">
        <thead><tr>${cols.map(c => `<th>${this._esc(this._t(c))}</th>`).join("")}</tr></thead>
        <tbody>${rows.map(r => `<tr><td>${this._esc(r[0])}</td><td>${this._esc(r[1])}</td></tr>`).join("")}</tbody>
      </table>`;
    const so = (lines) => `<div class="sun-explain-so"><b>${this._esc(this._t("sun_explain_so"))}</b>
        <ul>${lines.map(l => `<li>${this._esc(l)}</li>`).join("")}</ul></div>`;
    const intro = (key, map) => `<div class="settings-hint">${this._esc(tr(key, map))}</div>`;
    const w = this._t("hyst_with_values");
    if (kind === "comfort") {
      const { a, b, h } = v, ah = a + h, bh = b - h, deg = "°C";
      const rows = [[this._t("sun_below").replace("{t}", fmt(a)), this._t("hyst_cold")]];
      if (h > 0) rows.push([between(a, ah, deg), this._t("hyst_stay_cold")]);
      if (ah < bh) rows.push([between(ah, bh, deg), this._t("hyst_comfortable")]);
      if (h > 0) rows.push([between(bh, b, deg), this._t("hyst_stay_hot")]);
      rows.push([this._t("sun_above").replace("{t}", fmt(b)), this._t("hyst_hot")]);
      const m = { a: fmt(a), b: fmt(b), ah: fmt(ah), bh: fmt(bh), mid: fmt(a + h / 2), h: fmt(h), w };
      return intro("hyst_comfort_intro", m) + table(["hyst_col_room_temp", "hyst_col_state"], rows)
        + so([tr("hyst_comfort_so1", m), tr("hyst_comfort_so2", m), tr("hyst_comfort_so3", m), tr("hyst_comfort_so4", m)]);
    }
    if (kind === "rules" || kind === "solar") {
      const { t, h } = v, u = kind === "rules" ? "°C" : v.u;
      const yes = this._t(kind === "rules" ? "hyst_true" : "hyst_strong_yes");
      const no = this._t(kind === "rules" ? "hyst_false" : "hyst_strong_no");
      const rows = h > 0
        ? [[tr("hyst_above", { a: fu(t + h, u) }), yes], [between(t - h, t + h, u), this._t("hyst_keep")], [tr("hyst_below", { a: fu(t - h, u) }), no]]
        : [[tr("hyst_above", { a: fu(t, u) }), yes], [tr("hyst_below", { a: fu(t, u) }), no]];
      const m = { t: kind === "rules" ? fmt(t) : fu(t, u), h: kind === "rules" ? fmt(h) : fu(h, u),
        th: kind === "rules" ? fmt(t + h) : fu(t + h, u), tl: kind === "rules" ? fmt(t - h) : fu(t - h, u),
        w: v.ex ? this._t("hyst_example") : w };
      if (kind === "rules") {
        const sfx = v.above ? "" : "_below";
        const rrows = v.above ? rows : rows.slice().reverse().map((r, i, arr) => [r[0], arr[arr.length - 1 - i][1]]);
        m.rule = v.rule || "";
        m.op = this._t(v.above ? "hyst_op_above" : "hyst_op_below");
        const lines = h > 0
          ? [tr("hyst_rules_so1" + sfx, m), tr("hyst_rules_so2" + sfx, m), tr("hyst_rules_so3" + sfx, m)]
          : [this._t("hyst_zero")];
        return `<div class="settings-hint" style="margin-bottom:6px"><b>${this._esc(this._t("hyst_rules_scope"))}</b></div>`
          + intro(v.rule ? "hyst_rules_intro_real" : "hyst_rules_intro", m)
          + table(["hyst_col_temp", "hyst_col_condition"], rrows) + so(lines);
      }
      const lines = h > 0 ? [tr("hyst_solar_so1", m), tr("hyst_solar_so2", m)] : [this._t("hyst_zero"), tr("hyst_solar_so2", m)];
      return intro("hyst_solar_intro", m) + table(["hyst_col_sensor", "hyst_col_strong"], rows) + so(lines);
    }
    // wind
    const { t, h, u } = v, tl = t - h;
    const rows = [["≥ " + fu(t, u), this._t("hyst_wind_on")]];
    if (h > 0) rows.push([between(tl, t, u), this._t("hyst_wind_stay")]);
    rows.push([(h > 0 ? "≤ " + fu(tl, u) : "< " + fu(t, u)), this._t("hyst_wind_off")]);
    const m = { t: fu(t, u), h: fu(h, u), tl: fu(tl, u), w: v.ex ? this._t("hyst_example") : w };
    const lines = h > 0 ? [tr("hyst_wind_so1", m), tr("hyst_wind_so2", m)] : [this._t("hyst_zero")];
    return intro("hyst_wind_intro", m) + table(["hyst_col_wind", "hyst_col_protection"], rows) + so(lines);
  }

  // Numeric state of a threshold entity when readable, else the static value
  _effectiveThreshold(entityId, fallback) {
    const st = entityId && this._hass?.states ? this._hass.states[entityId] : null;
    const v = st ? parseFloat(st.state) : NaN;
    return Number.isFinite(v) ? Math.round(v * 10) / 10 : fallback;
  }

  _renderSunExplain(cmin, cmax) {
    const t = (k) => this._esc(this._t(k));
    const sun = t("sun_explain_sun"), noSun = t("sun_explain_no_sun");
    const rows = [
      ["cold-on", "sun_explain_room_cold_on", noSun, "sun_explain_eff_warm", this._t("sun_below").replace("{t}", cmin)],
      ["cold-off", "sun_explain_room_cold_off", sun, "sun_explain_eff_close", this._t("sun_below").replace("{t}", cmin)],
      ["position", "sun_explain_room_position", sun, "sun_explain_eff_close_as_hot", this._t("sun_between").replace("{min}", cmin).replace("{max}", cmax)],
      ["ignore", "sun_explain_room_ignore", noSun, "sun_explain_eff_wait", this._t("sun_between").replace("{min}", cmin).replace("{max}", cmax)],
      ["preemptive", "sun_explain_room_preemptive", t("sun_explain_sun_if_strong"), "sun_explain_eff_strong", this._t("sun_between").replace("{min}", cmin).replace("{max}", cmax)],
      ["hot", "sun_explain_room_hot", t("sun_explain_sun_always"), "sun_explain_eff_close", this._t("sun_above").replace("{t}", cmax)],
    ];
    return `<details class="sun-explain"${this._sunExplainOpen ? " open" : ""}>
      <summary data-action="sun-explain-toggle">${t("sun_explain_title")}</summary>
      <div class="sun-explain-body">
        <div class="settings-hint">${t("sun_explain_intro")}</div>
        <table class="sun-explain-table">
          <thead><tr><th>${t("sun_explain_col_room")}</th><th>${t("sun_explain_col_answer")}</th><th>${t("sun_explain_col_effect")}</th></tr></thead>
          <tbody>${rows.map(([id, room, answer, eff, range]) => `<tr data-sun-row="${id}">
            <td>${t(room)}<br><span class="radio-hint">${this._esc(range)}</span></td><td>${answer}</td><td>${t(eff)}</td></tr>`).join("")}</tbody>
        </table>
        <div class="sun-explain-so"><b>${t("sun_explain_so")}</b>
          <ul><li>${t("sun_explain_cold")}</li><li>${t("sun_explain_hot")}</li><li>${t("sun_explain_comfort")}</li></ul>
        </div>
      </div>
    </details>`;
  }

  _refreshSunExplain() {
    const root = this.shadowRoot;
    const table = root && root.querySelector(".sun-explain-table");
    if (!table) return;
    const heat = root.querySelector('[data-settings-field="sun_heating_ignore"]');
    const mode = root.querySelector('[data-settings-field="sun_comfort_mode"]');
    const on = new Set(["hot", heat && heat.checked ? "cold-on" : "cold-off", mode ? mode.value : ""]);
    table.querySelectorAll("tr[data-sun-row]").forEach(tr => tr.classList.toggle("current", on.has(tr.dataset.sunRow)));
  }

  // Behaviour of "Sun on facade" while the room is in its comfort range,
  // stored as two flags: position (no ignore) / ignore / ignore unless
  // strong solar radiation (preemptive shading).
  _sunComfortMode(neutralIgnore, preemptive) {
    if (!neutralIgnore) return "position";
    return preemptive ? "preemptive" : "ignore";
  }

  _sunComfortFlags(mode) {
    return {
      sun_neutral_ignore: mode !== "position",
      preemptive_shading: mode === "preemptive",
    };
  }

  // Covers whose effective setting uses the sunshine sensor
  _coversUsingRadiation() {
    const s = this._config.settings || {};
    const gNeutral = s.sun_neutral_ignore !== false, gPre = s.preemptive_shading !== false;
    return Object.values(this._config.covers || {}).filter(c => {
      if (!(c.indoor_temp_sensor || s.indoor_temp_sensor)) return false;
      const n = c.sun_neutral_ignore ?? gNeutral, p = c.preemptive_shading ?? gPre;
      return n && p;
    }).length;
  }

  // Per-cover select: Global (follow settings) or one of the three modes
  // States meaning "occupied" when the cover sets none (mirror of the engine)
  static get OCCUPIED_DEFAULTS() {
    return ["on", "home", "present", "présent", "occupied", "occupé", "detected", "true", "1"];
  }

  // Occupied states of a cover: its own list, else the defaults (null)
  _occupancyOwnStates(cover) {
    // An edit not confirmed by the server yet is shown over the stored value
    const pend = this._occPending;
    const raw = pend && cover.entity_id in pend ? pend[cover.entity_id] : cover.occupancy_states;
    return raw && String(raw).trim() ? String(raw).split(",").map(x => x.trim()).filter(Boolean) : null;
  }

  // State buttons like the rule editor: the sensor's possible states, the
  // selected ones meaning "occupied".
  _renderOccupancyStates(cover) {
    const cid = this._esc(cover.entity_id);
    const stateObj = cover.occupancy_sensor && this._hass?.states ? this._hass.states[cover.occupancy_sensor] : null;
    const own = this._occupancyOwnStates(cover);
    const defaults = CoverAutomaticPanel.OCCUPIED_DEFAULTS;
    const known = this._haKnownStates(stateObj, null);
    (own || []).forEach(v => { if (!known.some(k => k.toLowerCase() === v.toLowerCase())) known.push(v); });
    const isSel = (v) => own
      ? own.some(o => o.toLowerCase() === v.toLowerCase())
      : defaults.includes(v.toLowerCase());
    let html = `<div class="form-group"><label>${this._t("cover_occupancy_states")}</label><div class="day-select">`;
    for (const v of known) {
      html += `<button type="button" class="day-btn${isSel(v) ? " selected" : ""}" data-action="cover-occ-toggle" data-id="${cid}" data-val="${this._esc(v)}" title="${this._esc(v)}">${this._esc(this._haStateLabel(stateObj, null, v))}</button>`;
    }
    html += `</div>`;
    if (!own) html += `<div class="ha-help">${this._esc(this._t("cover_occupancy_default_note"))}</div>`;
    html += `<div class="ha-add-state"><input type="text" placeholder="${this._esc(this._t("ha_state_other"))}" data-occ-other="${cid}">
        <button type="button" class="btn btn-secondary" data-action="cover-occ-add" data-id="${cid}">${this._t("ha_state_add")}</button></div>
      ${own ? `<div class="ha-help"><button type="button" class="btn-link" data-action="cover-occ-reset" data-id="${cid}">${this._t("cover_occupancy_reset")}</button></div>` : ""}
      ${this._hint("cover_occupancy_states_hint")}</div>`;
    return html;
  }

  _onOccupancyStates(entityId, update) {
    const cover = (this._config.covers || {})[entityId];
    if (!cover) return;
    const stateObj = cover.occupancy_sensor && this._hass?.states ? this._hass.states[cover.occupancy_sensor] : null;
    // Start from what is shown selected (explicit list, else the matching defaults)
    let list = this._occupancyOwnStates(cover)
      || this._haKnownStates(stateObj, null).filter(v => CoverAutomaticPanel.OCCUPIED_DEFAULTS.includes(v.toLowerCase()));
    list = update(list);
    const value = list && list.length ? list.join(", ") : null;
    // Not written into the config before the server confirms: shown through
    // _occPending, dropped (stored value shown again) if the save fails.
    if (!this._occPending) this._occPending = {};
    this._occPending[entityId] = value;
    this._render();
    this._debouncedCoverSave(entityId, "occupancy_states", value, {
      onSettled: (ok) => {
        if (!this._occPending || this._occPending[entityId] !== value) return; // newer edit pending
        delete this._occPending[entityId];
        if (!ok) this._render();
      },
    });
  }

  // Items separated by a thin line (content without framed boxes)
  _sepList(items) {
    return `<div class="sep-list">${items.filter(Boolean).map(h => `<div class="sep-item">${h}</div>`).join("")}</div>`;
  }

  // One-line summaries shown under collapsed section titles of the cover sheet
  _coverSectionSummaries(cover) {
    const s = this._config.settings || {};
    const sep = " · ";
    const facade = cover.facade_id && this._config.facades ? this._config.facades[cover.facade_id] : null;
    const base = [
      this._t(cover.auto_enabled === false ? "cover_sum_auto_off" : "cover_sum_auto_on"),
      facade ? facade.name : this._t("cover_sum_no_facade"),
    ];
    if (cover.inverted) base.push(this._t("cover_inverted"));

    const win = [];
    if (cover.lock_sensor) {
      win.push(this._t("cover_sum_open").replace("{v}", cover.lock_hold_position
        ? this._t("cover_sum_hold")
        : (cover.lock_position ?? s.lock_position ?? 100) + " %"));
    }
    if (cover.vent_sensor) {
      win.push(this._t("cover_sum_tilted").replace("{v}", (cover.vent_position ?? s.vent_position ?? 30) + " %"));
    }

    const auto = [this._t("cover_sum_pause").replace("{n}", cover.pause_duration ?? s.pause_duration ?? 10)];
    const travel = [cover.travel_time, cover.measured_travel_time, s.default_travel_time]
      .find(v => typeof v === "number" && v > 0);
    if (travel) auto.push(this._t("cover_sum_travel").replace("{n}", Math.round(travel)));
    const own = ["pause_duration", "min_position_change", "min_time_between_changes", "travel_time"]
      .filter(k => cover[k] != null).length;
    auto.push(own ? this._t("cover_sum_own").replace("{n}", own) : this._t("cover_sum_all_global"));

    const room = [];
    const indoor = cover.indoor_temp_sensor || s.indoor_temp_sensor;
    room.push(indoor
      ? this._haEntityName(indoor) + (cover.indoor_temp_sensor ? "" : " (" + this._t("cover_sum_global") + ")")
      : this._t("cover_sum_no_indoor"));
    const cmin = this._effectiveThreshold(cover.comfort_temp_min_entity || s.comfort_temp_min_entity,
      cover.comfort_temp_min ?? s.comfort_temp_min ?? 21);
    const cmax = this._effectiveThreshold(cover.comfort_temp_max_entity || s.comfort_temp_max_entity,
      cover.comfort_temp_max ?? s.comfort_temp_max ?? 25);
    room.push(cmin + " / " + cmax + " °C");
    if (cover.occupancy_sensor) room.push(this._haEntityName(cover.occupancy_sensor));

    const heat = cover.sun_heating_ignore ?? (s.sun_heating_ignore !== false);
    const mode = this._sunComfortMode(
      cover.sun_neutral_ignore ?? (s.sun_neutral_ignore !== false),
      cover.preemptive_shading ?? (s.preemptive_shading !== false));
    const followsGlobal = cover.sun_heating_ignore == null && cover.sun_neutral_ignore == null && cover.preemptive_shading == null;
    const sun = [
      this._t(heat ? "cover_sum_sun_heat_on" : "cover_sum_sun_heat_off"),
      this._t("cover_sum_sun_between").replace("{v}", this._t("cover_sum_mode_" + mode)),
    ];
    if (followsGlobal) sun.push(this._t("cover_sum_global"));

    return {
      base: base.join(sep),
      window: win.length ? win.join(sep) : this._t("cover_sum_no_window"),
      automation: auto.join(sep),
      room: room.join(sep),
      sun: sun.join(sep),
    };
  }

  _renderCoverSunComfort(cover) {
    const s = this._config.settings || {};
    const gMode = this._sunComfortMode(s.sun_neutral_ignore !== false, s.preemptive_shading !== false);
    const own = (cover.sun_neutral_ignore == null && cover.preemptive_shading == null)
      ? ""
      : this._sunComfortMode(
        cover.sun_neutral_ignore ?? (s.sun_neutral_ignore !== false),
        cover.preemptive_shading ?? (s.preemptive_shading !== false));
    const opt = (value, label) => `<option value="${value}"${own === value ? " selected" : ""}>${this._esc(label)}</option>`;
    return `<div class="form-group">
      <label>${this._L("sun_comfort_label")}</label>
      <select data-action="cover-sun-comfort" data-id="${this._esc(cover.entity_id)}" data-field="sun_comfort_mode">
        ${opt("", this._t("tristate_global").replace("{value}", this._t("sun_comfort_" + gMode)))}
        ${opt("position", this._t("sun_comfort_position"))}
        ${opt("ignore", this._t("sun_comfort_ignore"))}
        ${opt("preemptive", this._t("sun_comfort_preemptive"))}
      </select>
      ${this._hint("sun_comfort_hint")}
    </div>`;
  }

  // Select "Global (value) / On / Off" for a nullable per-cover flag
  _renderCoverTristate(cover, field, labelKey, hintKey) {
    const own = cover[field];
    const globalOn = (this._config.settings || {})[field] !== false;
    const onOff = (on) => this._t(on ? "tristate_on" : "tristate_off");
    const opt = (value, label, selected) =>
      `<option value="${value}"${selected ? " selected" : ""}>${this._esc(label)}</option>`;
    return `<div class="form-group">
      <label>${this._L(labelKey)}</label>
      <select data-action="cover-tristate" data-id="${this._esc(cover.entity_id)}" data-field="${field}">
        ${opt("", this._t("tristate_global").replace("{value}", onOff(globalOn)), own == null)}
        ${opt("true", onOff(true), own === true)}
        ${opt("false", onOff(false), own === false)}
      </select>
      ${this._hint(hintKey)}
    </div>`;
  }

  // Label with a shorter variant shown on narrow screens (key + "_short")
  _L(key) {
    const lang = (this._hass?.language) || "en";
    const dict = I18N[lang] || I18N.en;
    const sk = key + "_short";
    const long = this._esc(this._t(key));
    if (dict[sk] === undefined && I18N.en[sk] === undefined) return long;
    return `<span class="lbl-long">${long}</span><span class="lbl-short">${this._esc(this._t(sk))}</span>`;
  }

  _renderToggle(labelKey, checked, action, id, field, hintKey = null) {
    return `<div class="toggle-row">
      <span class="toggle-label">${this._L(labelKey)}${hintKey ? this._hint(hintKey) : ""}</span>
      <label class="toggle">
        <input type="checkbox" ${checked ? "checked" : ""} data-action="${action}" data-id="${this._esc(id)}" data-field="${field}">
        <span class="toggle-slider"></span>
      </label>
    </div>`;
  }

  _renderFacadeDropdown(cover) {
    const facades = this._config.facades || {};
    let html = `<div class="form-group"><label>${this._t("cover_facade")}</label><select data-action="cover-select" data-id="${this._esc(cover.entity_id)}" data-field="facade_id">`;
    html += `<option value="">${this._t("none")}</option>`;
    for (const f of Object.values(facades)) {
      const sel = cover.facade_id === f.id ? " selected" : "";
      html += `<option value="${this._esc(f.id)}"${sel}>${this._esc(f.name)}</option>`;
    }
    html += '</select></div>';
    return html;
  }

  /* ============================================================
   * TAB: Facades
   * ============================================================ */
  _renderFacades() {
    const facades = this._config.facades || {};
    const entries = Object.values(facades).sort((a, b) => (a.azimuth_start ?? 0) - (b.azimuth_start ?? 0));

    let html = '<div class="card-grid">';

    for (const f of entries) {
      if (this._editingFacade === f.id) {
        html += this._renderFacadeEditForm(f);
      } else {
        html += this._renderFacadeCard(f);
      }
    }

    // Add button or form
    if (this._addingFacade) {
      html += this._renderFacadeAddForm();
    } else {
      html += `<button class="add-card" data-action="facade-add-start">+ ${this._t("facade_add")}</button>`;
    }

    html += '</div>';
    return html;
  }

  _renderFacadeCard(f) {
    const covers = this._getFacadeCovers(f.id);
    const arrow = DIRECTION_ARROWS[f.direction] || "";
    const dirLabel = this._t("facade_dir_" + f.direction) || f.direction;
    const liveFacade = (this._config.live_facades || {})[f.id] || {};
    const sunOn = liveFacade.sun_on_facade;
    const sunBadge = sunOn
      ? '<span class="live-icon-sun" title="' + this._esc(this._t("facade_sun_active")) + '">' + this._sunIconSvg(14) + '</span>'
      : '';
    let html = `<div class="card">
      <div class="card-header">
        <span>${this._esc(f.name)}${sunBadge}</span>
        <span class="facade-dir-label">${arrow} ${this._esc(dirLabel)}</span>
      </div>
      <div class="card-body">
        <div class="facade-meta-row">
          <span>${this._t("facade_azimuth_start")}${this._colon()}${f.azimuth_start}&#176;</span>
          <span>${this._t("facade_azimuth_end")}${this._colon()}${f.azimuth_end}&#176;</span>
        </div>
        <div class="facade-covers-intro">
          ${this._t("facade_min_elevation")}${this._colon()}${f.min_elevation}&#176;
        </div>
        <div class="facade-covers-list-wrap">
          <div class="facade-covers-label">${this._t("facade_covers")}</div>
          <div class="chip-group">`;
    if (covers.length === 0) {
      html += `<span class="facade-no-covers">${this._t("facade_no_covers")}</span>`;
    } else {
      for (const c of covers) {
        html += `<span class="chip">${this._esc(c.name)}</span>`;
      }
    }
    html += `</div>
        </div>
        <div class="facade-actions">
          <button class="btn btn-secondary btn-sm" data-action="facade-edit" data-id="${this._esc(f.id)}">${this._t("edit")}</button>
          <button class="btn btn-danger btn-sm" data-action="facade-delete" data-id="${this._esc(f.id)}">${this._t("delete")}</button>
        </div>
      </div>
    </div>`;
    return html;
  }

  _renderFacadeEditForm(f) {
    const covers = this._config.covers || {};
    let html = `<div class="inline-form">
      <div class="form-group">
        <label>${this._t("name")}</label>
        <input type="text" value="${this._esc(f.name)}" data-facade-field="name">
      </div>
      <div class="form-group">
        <label>${this._t("facade_direction")}</label>
        <select data-facade-field="direction">
          ${["north","east","south","west"].map(d => `<option value="${d}"${f.direction===d?" selected":""}>${this._t("facade_dir_"+d)}</option>`).join("")}
        </select>
        ${this._hint("facade_direction_hint")}
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>${this._t("facade_azimuth_start")}</label>
          <input type="number" step="any" value="${this._num(f.azimuth_start)}" data-facade-field="azimuth_start">
        </div>
        <div class="form-group">
          <label>${this._t("facade_azimuth_end")}</label>
          <input type="number" step="any" value="${this._num(f.azimuth_end)}" data-facade-field="azimuth_end">
        </div>
      </div>
      ${this._hint("facade_azimuth_hint")}
      <div class="form-group">
        <label>${this._t("facade_min_elevation")}</label>
        <input type="number" min="0" max="90" step="0.5" value="${this._num(f.min_elevation)}" data-facade-field="min_elevation">
        ${this._hint("facade_min_elevation_hint")}
      </div>
      <div class="form-group">
        <label>${this._t("facade_covers")}</label>
        <div class="multi-select">`;
    for (const c of Object.values(covers)) {
      const assignedHere = (f.cover_ids || []).includes(c.entity_id);
      const otherFacade = !assignedHere && c.facade_id && c.facade_id !== f.id ? this._getFacadeName(c.facade_id) : null;
      const sel = assignedHere ? " selected" : "";
      const label = otherFacade ? `${this._esc(c.name)} [${this._esc(otherFacade)}]` : this._esc(c.name);
      html += `<button class="ms-item${sel}" data-action="facade-cover-toggle" data-cover="${this._esc(c.entity_id)}">${label}</button>`;
    }
    html += `</div></div>
      <div class="form-actions">
        <button class="btn btn-secondary" data-action="facade-edit-cancel">${this._t("cancel")}</button>
        <button class="btn btn-primary" data-action="facade-edit-save" data-id="${this._esc(f.id)}">${this._t("save")}</button>
      </div>
    </div>`;
    return html;
  }

  _renderFacadeAddForm() {
    const covers = this._config.covers || {};
    let html = `<div class="inline-form">
      <div class="form-group">
        <label>${this._t("name")}</label>
        <input type="text" value="" data-facade-field="name" placeholder="${this._t("name")}">
      </div>
      <div class="form-group">
        <label>${this._t("facade_direction")}</label>
        <select data-facade-field="direction">
          ${["north","east","south","west"].map(d => `<option value="${d}"${d==="south"?" selected":""}>${this._t("facade_dir_"+d)}</option>`).join("")}
        </select>
        ${this._hint("facade_direction_hint")}
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>${this._t("facade_azimuth_start")}</label>
          <input type="number" step="any" value="135" data-facade-field="azimuth_start">
        </div>
        <div class="form-group">
          <label>${this._t("facade_azimuth_end")}</label>
          <input type="number" step="any" value="225" data-facade-field="azimuth_end">
        </div>
      </div>
      ${this._hint("facade_azimuth_hint")}
      <div class="form-group">
        <label>${this._t("facade_min_elevation")}</label>
        <input type="number" min="0" max="90" step="0.5" value="0" data-facade-field="min_elevation">
        ${this._hint("facade_min_elevation_hint")}
      </div>
      <div class="form-group">
        <label>${this._t("facade_covers")}</label>
        <div class="multi-select">`;
    for (const c of Object.values(covers)) {
      const otherFacade = c.facade_id ? this._getFacadeName(c.facade_id) : null;
      const label = otherFacade ? `${this._esc(c.name)} [${this._esc(otherFacade)}]` : this._esc(c.name);
      html += `<button class="ms-item" data-action="facade-cover-toggle" data-cover="${this._esc(c.entity_id)}">${label}</button>`;
    }
    html += `</div></div>
      <div class="form-actions">
        <button class="btn btn-secondary" data-action="facade-add-cancel">${this._t("cancel")}</button>
        <button class="btn btn-primary" data-action="facade-add-save">${this._t("add")}</button>
      </div>
    </div>`;
    return html;
  }

  /* ============================================================
   * TAB: Rules
   * ============================================================ */
  _renderRules() {
    const rules = this._config.rules || {};
    const sorted = this._rulesByPriority(rules);

    let html = `<div class="rule-reorder-hint">${this._t("rule_reorder_hint")}</div>`;

    if (sorted.length === 0 && !this._addingRule) {
      html += `<div class="empty-state">${this._t("none")}</div>`;
    }

    const activeRules = this._config.active_rules || {};

    for (let idx = 0; idx < sorted.length; idx++) {
      const r = sorted[idx];
      const isExpanded = this._expandedRule === r.id;
      const dragging = this._dragRuleId === r.id ? " dragging" : "";
      const dragOver = this._dragOverId === r.id ? " drag-over" : "";
      const matchedCovers = activeRules[r.id] || [];
      const isActive = matchedCovers.length > 0;

      const activeClass = isActive ? " rule-active" : "";
      html += `<div class="rule-row${activeClass}${dragging}${dragOver}" draggable="true" data-rule-id="${this._esc(r.id)}" data-action="rule-drag">`;
      html += `<span class="drag-handle" title="${this._esc(this._t("drag_handle"))}">&#9783;</span>`;
      // Keyboard/touch alternative to drag & drop
      html += this._moveBtns(`data-id="${this._esc(r.id)}"`, "rule-prio-up", "rule-prio-down", "rule_priority_up", "rule_priority_down", idx === 0, idx === sorted.length - 1)
        .replace('class="move-btns"', 'class="move-btns move-btns-v"');
      html += `<div class="rule-info" data-action="rule-expand" data-id="${this._esc(r.id)}" tabindex="0" role="button" aria-expanded="${isExpanded ? "true" : "false"}">`;
      html += `<div class="rule-name">`;
      html += `<span class="rule-active-dot ${isActive ? "active" : ""}" title="${isActive ? this._t("rule_active_for") + " " + matchedCovers.length + " " + this._t("rule_covers_count") : this._t("rule_inactive")}"></span>`;
      html += `${this._esc(r.name)}`;
      if (r.safety) {
        html += `<span class="rule-safety-badge" title="${this._esc(this._t("rule_safety"))}">${this._lucideIcon("shield", 12)}${this._esc(this._t("rule_safety_badge"))}</span>`;
      }
      html += '</div>';
      html += '<div class="rule-meta">';
      html += `<span class="priority-badge">#${idx + 1}</span>`;
      const rg = this._ruleGroups(r);
      html += rg.n > 1
        ? `<span>${this._t("rule_groups_count").replace("{n}", rg.n)}</span>`
        : `<span>${this._t(rg.ops[0] === "or" ? "rule_op_short_or" : "rule_op_short_and")}</span>`;
      html += `<span class="rule-target">${this._t("rule_target_pos")}${this._colon()}${this._posBar(r.target_position, "compact")}</span>`;
      if (r.target_tilt_position != null) {
        html += `<span class="rule-target">${this._t("rule_target_tilt")}${this._colon()}${this._posBar(r.target_tilt_position, "compact")}</span>`;
      }
      html += '</div>';
      // Condition chips
      if (r.conditions && r.conditions.length > 0) {
        html += '<div class="chip-group mt-6">';
        const chip = (c, ci) => {
          const invalid = c.type === "ha_condition" && this._config.condition_status?.[r.id]?.[String(ci)]?.valid === false;
          const not = c.negate ? `<b class="chip-not">${this._t("rule_cond_not")}</b> ` : "";
          return `<span class="chip${invalid ? " chip-error" : ""}">${not}${this._esc(this._condChipLabel(c))}</span>`;
        };
        if (rg.n > 1) {
          // One bracketed block per group, joined by the between-groups operator
          const parts = [];
          for (let g = 0; g < rg.n; g++) {
            const members = [...r.conditions.entries()].filter(([, c]) => (parseInt(c.group, 10) || 0) === g);
            if (!members.length) continue;
            const inner = this._t(rg.ops[g] === "or" ? "rule_op_short_or" : "rule_op_short_and");
            parts.push(`<span class="chip-block">${members.map(([ci, c]) => chip(c, ci)).join(`<span class="chip-op">${inner}</span>`)}</span>`);
          }
          html += parts.join(`<span class="chip-op chip-op-between">${this._t(rg.between === "or" ? "rule_op_short_or" : "rule_op_short_and")}</span>`);
        } else {
          for (const [ci, c] of r.conditions.entries()) html += chip(c, ci);
        }
        html += '</div>';
      }
      html += '</div>'; // rule-info

      // Enable toggle
      html += `<label class="toggle">
        <input type="checkbox" ${r.enabled ? "checked" : ""} data-action="rule-toggle-enabled" data-id="${this._esc(r.id)}" aria-label="${this._esc(this._t("rule_enabled_aria").replace("{name}", r.name || r.id))}">
        <span class="toggle-slider"></span>
      </label>`;

<<<<<<< Updated upstream
      html += `<button class="btn-icon" data-action="rule-duplicate" data-id="${this._esc(r.id)}" title="${this._t("rule_duplicate")}" aria-label="${this._t("rule_duplicate")}">${this._lucideIcon("copy", 16)}</button>`;
=======
      html += `<button class="btn-icon" data-action="rule-duplicate" data-id="${this._esc(r.id)}" title="${this._esc(this._t("rule_duplicate"))}" aria-label="${this._esc(this._t("rule_duplicate"))}">${this._lucideIcon("copy", 16)}</button>`;
>>>>>>> Stashed changes
      html += `<button class="btn-icon" data-action="rule-delete" data-id="${this._esc(r.id)}" title="${this._t("delete")}">&#10005;</button>`;
      html += '</div>'; // rule-row

      // Expanded editor
      html += `<div class="rule-editor${isExpanded ? " expanded" : ""}">`;
      if (isExpanded) {
        // The editor works on the draft; the row above shows the saved rule.
        html += this._renderRuleEditor(this._edRule(r.id) || r);
      }
      html += '</div>';
    }

    // Add rule button/form
    if (this._addingRule) {
      html += this._renderRuleAddForm();
    } else {
      html += `<button class="btn btn-primary mt-16" data-action="rule-add-start">+ ${this._t("rule_add")}</button>`;
    }

    return html;
  }

  _renderRuleEditor(rule) {
    const facades = this._config.facades || {};
    const covers = this._config.covers || {};

    let html = '';

    // Scenarios this rule belongs to (null = all scenarios)
    const scenarios = Object.values(this._config.scenarios || {});
    html += `<div class="form-group">
      <label>${this._t("rule_scenarios")}</label>
      <div class="multi-select">`;
    for (const sc of scenarios) {
      const member = !Array.isArray(rule.scenario_ids) || rule.scenario_ids.includes(sc.id);
      html += `<button class="ms-item${member ? " selected" : ""}" data-action="rule-scenario-toggle" data-rule="${this._esc(rule.id)}" data-scenario="${this._esc(sc.id)}">${this._esc(sc.name)}</button>`;
    }
    html += `</div>
      ${this._hint("rule_scenarios_hint")}
    </div>`;

    // Safety rule (overrides pause, manual mode, wind protection, master switch)
    html += `<div class="form-group rule-safety-group">
      ${this._renderToggle("rule_safety", !!rule.safety, "rule-field", rule.id, "safety")}
      ${this._hint("rule_safety_hint")}
    </div>`;

    // Name
    html += `<div class="form-group">
      <label>${this._t("name")}</label>
      <input type="text" value="${this._esc(rule.name)}" data-action="rule-field" data-id="${this._esc(rule.id)}" data-field="name" maxlength="100">
    </div>`;

    // Target position + tilt
    html += '<div class="form-row">';
    html += `<div class="form-group">
      <label>${this._t("rule_target_pos")}</label>
      <input type="number" min="0" max="100" value="${this._num(rule.target_position)}" data-action="rule-field" data-id="${this._esc(rule.id)}" data-field="target_position">
      ${this._hint("rule_target_pos_hint")}
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("rule_target_tilt")}</label>
      <input type="number" min="0" max="100" value="${this._num(rule.target_tilt_position, "")}" placeholder="${this._t("none")}" data-action="rule-field" data-id="${this._esc(rule.id)}" data-field="target_tilt_position">
    </div>`;
    html += '</div>';

    // Facades multi-select
    html += `<div class="form-group">
      <label>${this._t("rule_facades")}</label>
      <div class="multi-select">`;
    for (const f of Object.values(facades)) {
      const sel = (rule.facade_ids || []).includes(f.id) ? " selected" : "";
      html += `<button class="ms-item${sel}" data-action="rule-facade-toggle" data-rule="${this._esc(rule.id)}" data-facade="${this._esc(f.id)}">${this._esc(f.name)}</button>`;
    }
    html += '</div></div>';

    // Covers multi-select
    html += `<div class="form-group">
      <label>${this._t("rule_covers")}</label>
      <div class="multi-select">`;
    for (const c of Object.values(covers)) {
      const sel = (rule.cover_ids || []).includes(c.entity_id) ? " selected" : "";
      html += `<button class="ms-item${sel}" data-action="rule-cover-toggle" data-rule="${this._esc(rule.id)}" data-cover="${this._esc(c.entity_id)}">${this._esc(c.name)}</button>`;
    }
    html += '</div></div>';
    html += this._hint("rule_assignment_hint");

    // Conditions, organised in groups
    const condCount = (rule.conditions || []).length;
    const allCollapsed = condCount > 0 && rule.conditions.every((_, i) => this._isCondCollapsed(rule.id, i));
    html += `<div class="rule-conditions-label"><span>${this._t("rule_conditions")}</span>${condCount > 1
      ? `<button class="cond-collapse-all" data-action="rule-cond-collapse-all" data-rule="${this._esc(rule.id)}">${this._t(allCollapsed ? "cond_expand_all" : "cond_collapse_all")}</button>` : ""}</div>`;
    html += this._renderConditionGroups(rule);

    // Save button
    html += `<div class="rule-editor-actions">
      <button class="btn btn-primary" data-action="rule-save" data-id="${this._esc(rule.id)}">${this._t("save")}</button>
    </div>`;

    return html;
  }

  // Operators per condition group and number of groups of a rule.
  _ruleGroups(rule) {
    const ops = Array.isArray(rule.group_operators) && rule.group_operators.length
      ? [...rule.group_operators] : [rule.condition_operator === "or" ? "or" : "and"];
    let n = ops.length;
    for (const c of rule.conditions || []) n = Math.max(n, (parseInt(c.group, 10) || 0) + 1);
    while (ops.length < n) ops.push("and");
    return { ops, n, between: rule.condition_operator === "or" ? "or" : "and" };
  }

  _opSelect(attrs, value) {
    return `<select ${attrs}>
        <option value="and"${value === "and" ? " selected" : ""}>${this._t("rule_operator_and")}</option>
        <option value="or"${value === "or" ? " selected" : ""}>${this._t("rule_operator_or")}</option>
      </select>`;
  }

  _renderConditionAdd(rule, group) {
    return `<div class="rule-condition-add">
      <select class="rule-condition-type-select" data-action="rule-add-condition-type" data-rule="${this._esc(rule.id)}" data-group="${group}">
        <option value="">${this._t("rule_add_condition")}...</option>
        ${CONDITION_MENU.map(g => `<optgroup label="${this._esc(this._t(g.label))}">${g.items.map(it => `<option value="${it.value}">${this._esc(this._t(it.label))}</option>`).join("")}</optgroup>`).join("")}
      </select>
    </div>`;
  }

  // Compact up/down buttons (reordering conditions and groups).
  _moveBtns(attrs, actUp, actDown, tipUp, tipDown, firstPos, lastPos) {
    return `<span class="move-btns">
      <button class="btn-icon btn-move" data-action="${actUp}" ${attrs} title="${this._esc(this._t(tipUp))}" aria-label="${this._esc(this._t(tipUp))}"${firstPos ? " disabled" : ""}>&#9650;</button>
      <button class="btn-icon btn-move" data-action="${actDown}" ${attrs} title="${this._esc(this._t(tipDown))}" aria-label="${this._esc(this._t(tipDown))}"${lastPos ? " disabled" : ""}>&#9660;</button>
    </span>`;
  }

  // Indices (in rule.conditions) of the conditions of one group, in order.
  _groupCondIndices(conditions, group) {
    const out = [];
    (conditions || []).forEach((c, i) => { if ((parseInt(c.group, 10) || 0) === group) out.push(i); });
    return out;
  }

  _renderConditionGroups(rule) {
    const rid = this._esc(rule.id);
    const { ops, n, between } = this._ruleGroups(rule);
    const conds = rule.conditions || [];
    let html = "";
    if (n === 1) {
      html += `<div class="form-group">
        <label>${this._t("rule_operator")}</label>
        ${this._opSelect(`data-action="rule-group-op" data-rule="${rid}" data-group="0"`, ops[0])}
        ${this._hint("rule_operator_hint")}
      </div>`;
      if (conds.length > 0) {
        for (const [i] of conds.entries()) html += this._renderConditionCard(rule, i, 1);
      } else {
        html += `<div class="rule-no-conditions">${this._t("rule_no_conditions")}</div>`;
      }
      html += this._renderConditionAdd(rule, 0);
    } else {
      html += `<div class="form-group">
        <label>${this._t("rule_groups_operator")}</label>
        ${this._opSelect(`data-action="rule-field" data-id="${rid}" data-field="condition_operator"`, between)}
        ${this._hint("rule_groups_hint")}
      </div>`;
      for (let g = 0; g < n; g++) {
        if (g > 0) html += `<div class="cond-group-sep" data-group-sep="${rid}">${this._t(between === "or" ? "rule_op_short_or" : "rule_op_short_and")}</div>`;
        html += `<div class="cond-group">
          <div class="cond-group-head">
            <span class="cond-group-title">${this._t("rule_group")} ${g + 1}</span>
            <span class="cond-group-op"><span>${this._t("rule_group_joined_by")}</span>
              ${this._opSelect(`data-action="rule-group-op" data-rule="${rid}" data-group="${g}"`, ops[g])}</span>
            <span class="cond-preview cond-group-preview" data-group-preview="${g}"></span>
            ${this._moveBtns(`data-rule="${rid}" data-group="${g}"`, "rule-group-up", "rule-group-down", "rule_group_up", "rule_group_down", g === 0, g === n - 1)}
            <button class="btn-icon" data-action="rule-group-delete" data-rule="${rid}" data-group="${g}" title="${this._esc(this._t("rule_group_delete"))}">&#10005;</button>
          </div>`;
        let count = 0;
        for (const [i, c] of conds.entries()) {
          if ((parseInt(c.group, 10) || 0) !== g) continue;
          html += this._renderConditionCard(rule, i, n);
          count++;
        }
        if (!count) html += `<div class="rule-no-conditions">${this._t("rule_group_empty")}</div>`;
        html += this._renderConditionAdd(rule, g);
        html += '</div>';
      }
    }
    if (n < MAX_CONDITION_GROUPS) {
      html += `<button class="btn btn-secondary btn-sm cond-group-add" data-action="rule-group-add" data-rule="${rid}">+ ${this._t("rule_group_add")}</button>
        ${n === 1 ? this._hint("rule_group_add_hint") : ""}`;
    }
    return html;
  }

  // Collapsed condition cards (per rule and condition index, kept while the panel is open).
  _isCondCollapsed(ruleId, idx) {
    return !!(this._collapsedConds && this._collapsedConds.has(ruleId + ":" + idx));
  }

  _setCondCollapsed(ruleId, idx, collapsed) {
    if (!this._collapsedConds) this._collapsedConds = new Set();
    const key = ruleId + ":" + idx;
    if (collapsed) this._collapsedConds.add(key); else this._collapsedConds.delete(key);
    const root = this.shadowRoot;
    const card = root && root.querySelector(`.condition-card[data-cond-card="${CSS.escape(key)}"]`);
    if (!card) return;
    card.classList.toggle("collapsed", collapsed);
    const chev = card.querySelector(".cond-chevron");
    if (chev) {
      chev.setAttribute("aria-expanded", collapsed ? "false" : "true");
      chev.title = this._t(collapsed ? "cond_expand" : "cond_collapse");
    }
    // Refresh the one-line summary with the values edited meanwhile.
    const rule = this._edRule(ruleId);
    const sum = card.querySelector(".cond-summary");
    if (sum && rule && rule.conditions && rule.conditions[idx]) sum.textContent = this._condSummary(rule.conditions[idx]);
  }

  _onCondCollapseAll(ruleId) {
    const rule = this._edRule(ruleId);
    if (!rule || !rule.conditions) return;
    const anyOpen = rule.conditions.some((_, i) => !this._isCondCollapsed(ruleId, i));
    rule.conditions.forEach((_, i) => this._setCondCollapsed(ruleId, i, anyOpen));
    const btn = this.shadowRoot && this.shadowRoot.querySelector(`[data-action="rule-cond-collapse-all"][data-rule="${CSS.escape(ruleId)}"]`);
    if (btn) btn.textContent = this._t(anyOpen ? "cond_expand_all" : "cond_collapse_all");
  }

  // Index shift after a condition is deleted (collapsed state follows its card).
  _shiftCollapsedConds(ruleId, removedIdx) {
    if (!this._collapsedConds) return;
    const next = new Set();
    for (const key of this._collapsedConds) {
      const sep = key.lastIndexOf(":");
      const rid = key.slice(0, sep);
      const i = parseInt(key.slice(sep + 1), 10);
      if (rid !== ruleId) { next.add(key); continue; }
      if (i === removedIdx) continue;
      next.add(rid + ":" + (i > removedIdx ? i - 1 : i));
    }
    this._collapsedConds = next;
  }

  // One-line summary of a condition's settings, shown when it is collapsed.
  _condSummary(c) {
    const p = c.params || {};
    const off = v => { const n = Number(v) || 0; return n === 0 ? "" : (n > 0 ? "+" : "−") + Math.abs(n) + " min"; };
    switch (c.type) {
      case "ha_condition": return this._condChipLabel(c);
      case "sun_elevation_above": return "> " + (p.elevation ?? p.value ?? "") + "°";
      case "sun_elevation_below": return "< " + (p.elevation ?? p.value ?? "") + "°";
      case "temperature_above": return "> " + (p.temperature ?? p.value ?? "") + " °C";
      case "temperature_below": return "< " + (p.temperature ?? p.value ?? "") + " °C";
      case "temperature_comfort": return this._optionLabel("mode", p.mode || "cooling");
      case "outdoor_vs_indoor": {
        const d = Math.abs(Number(p.delta) || 0);
        return this._optionLabel("operator", p.operator === "warmer" ? "warmer" : "cooler") + (d ? " (≥ " + d + " °C)" : "");
      }
      case "time_between": return (p.start_time || "") + " – " + (p.end_time || "");
      case "state_is": return (p.entity_id ? this._haEntityName(p.entity_id) : "?") + " = " + (p.state ?? "");
      case "numeric_state": return (p.entity_id ? this._haEntityName(p.entity_id) : "?") + (p.operator === "below" ? " < " : " > ") + (p.value ?? "");
      case "weather_is": {
        const w = Array.isArray(p.weather) ? p.weather : (p.weather ? [p.weather] : (p.states || []));
        return w.map(v => this._optionLabel("weather", v)).join(", ");
      }
      case "day_of_week": return (p.days || []).map(d => this._i18nOr("day_" + d, d)).join(" ");
      case "workday": return this._optionLabel("state", p.state || "on");
      default:
        return c.type && c.type.startsWith("time_") ? off(p.offset) : "";
    }
  }

  _renderConditionCard(rule, idx, groupCount = null) {
    const cond = rule.conditions[idx];
    const nGroups = groupCount ?? this._ruleGroups(rule).n;
    const negated = !!cond.negate;
    const cGroup = parseInt(cond.group, 10) || 0;
    const groupMove = nGroups > 1
      ? `<select class="cond-group-move" data-action="rule-cond-group" data-rule="${this._esc(rule.id)}" data-idx="${idx}" title="${this._esc(this._t("rule_cond_move"))}">${Array.from({ length: nGroups }, (_, g) => `<option value="${g}"${g === cGroup ? " selected" : ""}>${this._t("rule_group")} ${g + 1}</option>`).join("")}</select>`
      : "";
    const siblings = this._groupCondIndices(rule.conditions, cGroup);
    const pos = siblings.indexOf(idx);
    const moveBtns = this._moveBtns(`data-rule="${this._esc(rule.id)}" data-idx="${idx}"`, "rule-cond-up", "rule-cond-down",
      "rule_cond_up", "rule_cond_down", pos <= 0, pos === siblings.length - 1);
    const notBtn = `<button class="cond-not${negated ? " active" : ""}" data-action="rule-cond-negate" data-rule="${this._esc(rule.id)}" data-idx="${idx}" title="${this._esc(this._t("rule_cond_not_hint"))}">${this._t("rule_cond_not")}</button>`;
    const paramDefs = CONDITION_PARAMS[cond.type] || [];

    const isContextCond = CONTEXT_DEPENDENT_TYPES.includes(cond.type);
    const previewCell = isContextCond
      ? `<span class="cond-preview cond-preview-context">${this._t("cond_preview_context")}</span>`
      : `<span class="cond-preview" data-cond-preview="${idx}"></span>`;
    const isHa = cond.type === "ha_condition";
    const title = isHa ? this._haCondTitle(cond) : this._t("cond_" + cond.type);
    const collapsed = this._isCondCollapsed(rule.id, idx);
    let html = `<div class="condition-card${isHa ? " ha-card" : ""}${negated ? " negated" : ""}${collapsed ? " collapsed" : ""}" data-cond-card="${this._esc(rule.id)}:${idx}">
      <div class="cond-header">
        <span class="cond-head-left">
          <button class="cond-chevron" data-action="rule-cond-collapse" data-rule="${this._esc(rule.id)}" data-idx="${idx}" title="${this._esc(this._t(collapsed ? "cond_expand" : "cond_collapse"))}" aria-expanded="${collapsed ? "false" : "true"}">&#9662;</button>
          ${notBtn}
          <span class="cond-type" data-action="rule-cond-collapse" data-rule="${this._esc(rule.id)}" data-idx="${idx}">${this._esc(title)}</span>
          <span class="cond-summary" data-cond-summary="${idx}">${this._esc(this._condSummary(cond))}</span>
          ${previewCell}
        </span>
        <span class="cond-head-right">
          ${groupMove}
          ${moveBtns}
          <button class="btn-icon" data-action="rule-delete-condition" data-rule="${this._esc(rule.id)}" data-idx="${idx}" title="${this._t("delete")}">&#10005;</button>
        </span>
      </div>`;

    if (isHa) {
      html += this._renderHaConditionBody(rule, idx, cond);
      return html + '</div>';
    }

    // Legacy entity conditions can be converted to the richer HA condition
    const legacyHyst = cond.type === "numeric_state" && Number((cond.params || {}).hysteresis) > 0;
    if ((cond.type === "state_is" || cond.type === "numeric_state") && !legacyHyst) {
      html += `<div class="ha-convert"><button type="button" class="btn btn-secondary btn-small" data-action="cond-convert" data-rule="${this._esc(rule.id)}" data-idx="${idx}">${this._t("cond_convert")}</button>
        <span class="ha-help">${this._esc(this._t("cond_convert_hint"))}</span></div>`;
    }

    if (paramDefs.length > 0) {
      html += '<div class="cond-params">';
      for (const p of paramDefs) {
        const val = (cond.params && cond.params[p.key] != null) ? cond.params[p.key] : p.default;
        html += '<div class="form-group">';
        html += `<label>${this._t("param_" + p.key)}</label>`;
        if (p.type === "select") {
          html += `<select data-action="cond-param" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}">`;
          for (const opt of p.options) {
            const optLabel = this._t("opt_" + opt);
            html += `<option value="${opt}"${val === opt ? " selected" : ""}>${optLabel}</option>`;
          }
          html += '</select>';
        } else if (p.type === "multiselect") {
          const selected = Array.isArray(val) ? val : (val ? [val] : p.default);
          html += `<div class="day-select" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}">`;
          for (const opt of p.options) {
            const active = selected.includes(opt);
            html += `<button type="button" class="day-btn${active ? " selected" : ""}" data-action="multiselect-toggle" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}" data-val="${this._esc(opt)}">${this._esc(this._optionLabel(p.key, opt))}</button>`;
          }
          html += '</div>';
        } else if (p.type === "time") {
          html += `<input type="time" value="${this._esc(String(val))}" data-action="cond-param" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}">`;
        } else if (p.type === "dayselect") {
          const ALL_DAYS = ["mon","tue","wed","thu","fri","sat","sun"];
          const selected = Array.isArray(val) ? val : p.default;
          html += `<div class="day-select" data-action="cond-param" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}">`;
          for (const d of ALL_DAYS) {
            const active = selected.includes(d);
            html += `<button type="button" class="day-btn${active ? " selected" : ""}" data-action="day-toggle" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}" data-day="${d}">${this._t("day_" + d)}</button>`;
          }
          html += '</div>';
        } else if (p.type === "number") {
          html += `<input type="number" value="${this._num(val)}" step="${p.step ? p.step : "any"}" data-action="cond-param" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}">`;
        } else if (p.type === "entity") {
          html += this._renderCondEntitySelect(rule, idx, p.key, val);
        } else {
          html += `<input type="text" value="${this._esc(String(val))}" data-action="cond-param" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}">`;
        }
        html += '</div>';
      }
      html += '</div>';
    }

    // Sun time conditions: window covered and complementary condition
    if (/^time_(after|before)_(sunrise|sunset|dawn|dusk)$/.test(cond.type || "")) {
      const sunHint = this._t("cond_" + cond.type + "_hint");
      if (sunHint !== "cond_" + cond.type + "_hint") {
        const other = cond.type.startsWith("time_after_") ? cond.type.replace("time_after_", "time_before_") : cond.type.replace("time_before_", "time_after_");
        html += `<div class="ha-help cond-type-hint">${this._esc(sunHint.replace("{other}", this._t("cond_" + other)))}</div>`;
      }
    }

    html += '</div>';
    return html;
  }

  async _onCoverTravelReset(entityId) {
    try {
      const result = await this._ws("cover_automatic/cover/update", { entity_id: entityId, measured_travel_time: null });
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); this._showError(e); }
  }

  /* ---------- Native Home Assistant conditions (type "ha_condition") ---------- */

  // Parse a condition config into the form model, or null when the form
  // cannot represent it (templates, zones, nested and/or...).
  _haFormModel(config, opHint = null) {
    if (!config || typeof config !== "object") return null;
    let cfg = config;
    let negate = false;
    if (cfg.condition === "not") {
      const subs = Array.isArray(cfg.conditions) ? cfg.conditions : [];
      if (subs.length !== 1 || !subs[0] || subs[0].condition !== "state") return null;
      negate = true;
      cfg = subs[0];
    }
    const allowed = new Set(["condition", "entity_id", "attribute", "state", "for", "above", "below"]);
    if (Object.keys(cfg).some(k => !allowed.has(k))) return null;
    let entity = cfg.entity_id;
    if (Array.isArray(entity)) {
      if (entity.length > 1) return null;
      entity = entity[0];
    }
    if (entity != null && typeof entity !== "string") return null;
    const model = { kind: null, entity: entity || "", attribute: cfg.attribute || "", negate };
    if (cfg.condition === "state") {
      if (cfg.above != null || cfg.below != null) return null;
      model.kind = "state";
      const st = cfg.state;
      model.states = st == null ? [] : (Array.isArray(st) ? st.map(String) : [String(st)]);
      model.forMinutes = null;
      if (cfg.for != null) {
        const f = cfg.for;
        if (typeof f === "object" && !Array.isArray(f)) {
          const keys = Object.keys(f);
          if (keys.some(k => !["hours", "minutes", "seconds"].includes(k))) return null;
          model.forMinutes = (Number(f.hours) || 0) * 60 + (Number(f.minutes) || 0) + (Number(f.seconds) || 0) / 60;
        } else if (typeof f === "string" && /^\d{1,2}:\d{2}(:\d{2})?$/.test(f)) {
          const p = f.split(":").map(Number);
          model.forMinutes = p[0] * 60 + p[1] + (p[2] || 0) / 60;
        } else if (typeof f === "number") {
          model.forMinutes = f / 60;
        } else {
          return null;
        }
      }
      return model;
    }
    if (cfg.condition === "numeric_state" && !negate) {
      if (cfg.state != null || cfg.for != null) return null;
      const num = (v) => (v == null || v === "" ? null : Number(v));
      if ((cfg.above != null && !Number.isFinite(num(cfg.above))) || (cfg.below != null && !Number.isFinite(num(cfg.below)))) return null;
      model.kind = "numeric";
      model.above = num(cfg.above);
      model.below = num(cfg.below);
      model.operator = model.above != null && model.below != null ? "between" : (model.below != null ? "below" : "above");
      // The chosen operator is kept in the params while a value is missing
      // (e.g. "between" with only the minimum filled in yet).
      if (["above", "below", "between"].includes(opHint)) model.operator = opHint;
      return model;
    }
    return null;
  }

  // Build the Home Assistant condition config from the form model.
  _haFormToConfig(m) {
    if (m.kind === "numeric") {
      const cfg = { condition: "numeric_state", entity_id: m.entity || "" };
      if (m.attribute) cfg.attribute = m.attribute;
      if (m.operator !== "below" && m.above != null && Number.isFinite(m.above)) cfg.above = m.above;
      if (m.operator !== "above" && m.below != null && Number.isFinite(m.below)) cfg.below = m.below;
      return cfg;
    }
    const cfg = { condition: "state", entity_id: m.entity || "" };
    if (m.attribute) cfg.attribute = m.attribute;
    cfg.state = m.states.length === 1 ? m.states[0] : [...m.states];
    if (!m.negate && m.forMinutes != null && m.forMinutes > 0) cfg.for = { minutes: m.forMinutes };
    return m.negate ? { condition: "not", conditions: [cfg] } : cfg;
  }

  _haDefaultConfig(kind) {
    return kind === "numeric"
      ? { condition: "numeric_state", entity_id: "", above: 0 }
      : { condition: "state", entity_id: "", state: [] };
  }

  // Missing field in a form-built condition (shown instead of HA's error).
  _haFormIncomplete(m) {
    if (!m) return null;
    if (!m.entity) return "ha_incomplete_entity";
    if (m.kind === "state" && m.states.length === 0) return "ha_incomplete_states";
    if (m.kind === "numeric") {
      if (m.operator === "between" && (m.above == null || m.below == null)) return "ha_incomplete_value";
      if (m.operator === "above" && m.above == null) return "ha_incomplete_value";
      if (m.operator === "below" && m.below == null) return "ha_incomplete_value";
    }
    return null;
  }

  // Possible states of an entity, for the state buttons.
  _haKnownStates(stateObj, attribute) {
    const out = [];
    const add = (v) => { if (v != null && v !== "" && !out.includes(String(v))) out.push(String(v)); };
    if (!stateObj) return out;
    if (attribute) {
      add(stateObj.attributes[attribute]);
      return out;
    }
    const domain = stateObj.entity_id.split(".")[0];
    const a = stateObj.attributes || {};
    const ONOFF = ["on", "off"];
    const BY_DOMAIN = {
      binary_sensor: ONOFF, switch: ONOFF, light: ONOFF, input_boolean: ONOFF, fan: ONOFF,
      automation: ONOFF, script: ONOFF, remote: ONOFF, siren: ONOFF, humidifier: ONOFF,
      cover: ["open", "closed", "opening", "closing"],
      lock: ["locked", "unlocked", "locking", "unlocking", "open", "jammed"],
      alarm_control_panel: ["disarmed", "armed_home", "armed_away", "armed_night", "armed_vacation", "armed_custom_bypass", "arming", "pending", "triggered"],
      media_player: ["off", "on", "idle", "playing", "paused", "standby", "buffering"],
      sun: ["above_horizon", "below_horizon"],
      vacuum: ["cleaning", "docked", "idle", "paused", "returning", "error"],
      lawn_mower: ["mowing", "docked", "paused", "returning", "error"],
      weather: ["sunny", "clear-night", "partlycloudy", "cloudy", "fog", "rainy", "pouring", "lightning", "lightning-rainy", "hail", "snowy", "snowy-rainy", "windy", "windy-variant", "exceptional"],
    };
    if (Array.isArray(a.options)) a.options.forEach(add);
    if (domain === "climate" && Array.isArray(a.hvac_modes)) a.hvac_modes.forEach(add);
    if (domain === "water_heater" && Array.isArray(a.operation_list)) a.operation_list.forEach(add);
    if (domain === "person" || domain === "device_tracker") {
      add("home"); add("not_home");
      for (const z of Object.values(this._hass.states)) {
        if (z.entity_id.startsWith("zone.") && z.entity_id !== "zone.home") add(z.attributes.friendly_name);
      }
    }
    (BY_DOMAIN[domain] || []).forEach(add);
    add(stateObj.state);
    return out.filter(v => v !== "unavailable" && v !== "unknown");
  }

  _haStateLabel(stateObj, attribute, value) {
    try {
      if (stateObj && attribute && this._hass.formatEntityAttributeValue) {
        return this._hass.formatEntityAttributeValue(stateObj, attribute, value);
      }
      if (stateObj && !attribute && this._hass.formatEntityState) {
        return this._hass.formatEntityState(stateObj, value);
      }
    } catch (e) { /* fall through */ }
    return String(value);
  }

  _haAttributeLabel(stateObj, attribute) {
    try {
      if (stateObj && this._hass.formatEntityAttributeName) return this._hass.formatEntityAttributeName(stateObj, attribute);
    } catch (e) { /* fall through */ }
    return attribute;
  }

  _haEntityName(entityId) {
    const s = entityId && this._hass?.states ? this._hass.states[entityId] : null;
    return s ? (s.attributes.friendly_name || entityId) : (entityId || "?");
  }

  _haCondTitle(cond) {
    const p = cond.params || {};
    if ((p.ui || "form") === "form") {
      const m = this._haFormModel(p.config);
      if (m) return this._t(m.kind === "numeric" ? "cond_ha_numeric" : "cond_ha_state");
    }
    return this._t("cond_ha_condition");
  }

  // Current validation status of an ha_condition card (live result from the
  // validate command, else the status sent with the configuration).
  _haStatus(ruleId, idx) {
    const live = this._haLive && this._haLive[ruleId + ":" + idx];
    if (live) return live;
    const st = this._config?.condition_status?.[ruleId]?.[String(idx)];
    return st || null;
  }

  _renderHaConditionBody(rule, idx, cond) {
    const p = cond.params || {};
    const ui = p.ui || "form";
    const rid = this._esc(rule.id);
    const base = `data-rule="${rid}" data-idx="${idx}"`;
    let html = `<div class="ha-seg" role="tablist">
      <button type="button" class="${ui === "form" ? "on" : ""}" data-action="ha-ui" data-mode="form" ${base} aria-selected="${ui === "form"}">${this._t("ha_tab_form")}</button>
      <button type="button" class="${ui === "yaml" ? "on" : ""}" data-action="ha-ui" data-mode="yaml" ${base} aria-selected="${ui === "yaml"}">${this._t("ha_tab_yaml")}</button>
    </div>`;
    html += '<div class="cond-params ha-params">';
    if (ui === "yaml") {
      const text = p.yaml != null ? p.yaml : "";
      html += `<div class="form-group"><label>${this._t("ha_yaml_label")}</label>
        <textarea class="ha-yaml" rows="${Math.max(4, text.split("\n").length + 1)}" spellcheck="false" data-action="ha-yaml" ${base} placeholder="${this._esc(this._t("ha_yaml_placeholder"))}">${this._esc(text)}</textarea>
        <div class="ha-help">${this._esc(this._t("ha_yaml_help"))}</div></div>`;
    } else {
      const m = this._haFormModel(p.config, p.op);
      if (!m) {
        html += `<div class="ha-msg ha-msg-info">${this._esc(this._t("ha_form_unsupported"))}</div>`;
        html += '</div>';
        html += `<div class="ha-status" data-ha-status="${rid}:${idx}">${this._renderHaStatus(rule.id, idx, null)}</div>`;
        return html;
      }
      html += this._renderHaForm(rule, idx, m);
    }
    html += '</div>';
    html += `<div class="ha-status" data-ha-status="${rid}:${idx}">${this._renderHaStatus(rule.id, idx, ui === "form" ? this._haFormModel(p.config, p.op) : null)}</div>`;
    return html;
  }

  _renderHaForm(rule, idx, m) {
    const base = `data-rule="${this._esc(rule.id)}" data-idx="${idx}"`;
    const stateObj = m.entity && this._hass?.states ? this._hass.states[m.entity] : null;
    let html = '';
    // Kind + entity
    html += `<div class="form-row"><div class="form-group"><label>${this._t("ha_kind")}</label>
      <select data-action="ha-form" data-field="kind" ${base}>
        <option value="state"${m.kind === "state" ? " selected" : ""}>${this._t("ha_kind_state")}</option>
        <option value="numeric"${m.kind === "numeric" ? " selected" : ""}>${this._t("ha_kind_numeric")}</option>
      </select></div>`;
    html += `<div class="form-group"><label>${this._t("ha_entity")}</label>${this._renderHaEntityInput(rule, idx, m.entity)}`;
    if (stateObj) {
      const cur = m.attribute ? stateObj.attributes[m.attribute] : stateObj.state;
      if (cur != null) {
        const fname = stateObj.attributes.friendly_name;
        html += `<div class="ha-current">${fname ? this._esc(fname) + " · " : ""}${this._esc(this._t("ha_current"))}${this._colon()}${this._esc(this._haStateLabel(stateObj, m.attribute, cur))}</div>`;
      }
    }
    html += '</div></div>';

    // Attribute
    const SKIP = new Set(["friendly_name", "icon", "entity_picture", "supported_features", "device_class", "unit_of_measurement",
      "attribution", "assumed_state", "restored", "editable", "id", "user_id", "device_trackers", "options", "hvac_modes",
      "operation_list", "state_class", "entity_id", "source_list", "sound_mode_list", "preset_modes", "fan_modes", "swing_modes"]);
    const attrs = stateObj ? Object.keys(stateObj.attributes).filter(k => !SKIP.has(k)).filter(k => {
      const v = stateObj.attributes[k];
      if (m.kind === "numeric") return typeof v === "number" || (typeof v === "string" && v !== "" && Number.isFinite(Number(v)));
      return v == null || ["string", "number", "boolean"].includes(typeof v);
    }) : [];
    if (m.attribute && !attrs.includes(m.attribute)) attrs.unshift(m.attribute);
    html += `<div class="form-row"><div class="form-group"><label>${this._t("ha_attribute")}</label>
      <select data-action="ha-form" data-field="attribute" ${base}>
        <option value="">${this._t("ha_attribute_none")}</option>
        ${attrs.map(a => `<option value="${this._esc(a)}"${a === m.attribute ? " selected" : ""}>${this._esc(this._haAttributeLabel(stateObj, a))}</option>`).join("")}
      </select></div>`;

    if (m.kind === "state") {
      html += `<div class="form-group"><label>${this._t("ha_compare")}</label>
        <select data-action="ha-form" data-field="negate" ${base}>
          <option value="0"${!m.negate ? " selected" : ""}>${this._t("ha_is")}</option>
          <option value="1"${m.negate ? " selected" : ""}>${this._t("ha_is_not")}</option>
        </select></div></div>`;
      html += `<div class="form-row"><div class="form-group"><label>${this._t("ha_for")}</label>
        <input type="number" min="0" step="any" value="${m.forMinutes != null && !m.negate ? this._esc(String(Math.round(m.forMinutes * 100) / 100)) : ""}" placeholder="0" data-action="ha-form" data-field="for" ${base}${m.negate ? " disabled" : ""}>
        ${m.negate ? `<div class="ha-help">${this._esc(this._t("ha_for_negate_hint"))}</div>` : ""}</div><div class="form-group"></div></div>`;
      // States buttons
      const known = this._haKnownStates(stateObj, m.attribute);
      m.states.forEach(s => { if (!known.includes(s)) known.push(s); });
      html += `<div class="form-group"><label>${this._t("ha_states")}</label><div class="day-select">`;
      for (const s of known) {
        const sel = m.states.includes(s);
        html += `<button type="button" class="day-btn${sel ? " selected" : ""}" data-action="ha-state-toggle" data-val="${this._esc(s)}" ${base} title="${this._esc(s)}">${this._esc(this._haStateLabel(stateObj, m.attribute, s))}</button>`;
      }
      html += `</div><div class="ha-add-state"><input type="text" placeholder="${this._esc(this._t("ha_state_other"))}" data-ha-other="${this._esc(rule.id)}:${idx}">
        <button type="button" class="btn btn-secondary" data-action="ha-state-add" ${base}>${this._t("ha_state_add")}</button></div></div>`;
    } else {
      html += `<div class="form-group"><label>${this._t("ha_operator")}</label>
        <select data-action="ha-form" data-field="operator" ${base}>
          ${["above", "below", "between"].map(o => `<option value="${o}"${m.operator === o ? " selected" : ""}>${this._t("ha_op_" + o)}</option>`).join("")}
        </select></div></div>`;
      const num = (v) => (v == null ? "" : this._esc(String(v)));
      if (m.operator === "between") {
        html += `<div class="form-row"><div class="form-group"><label>${this._t("ha_min")}</label>
          <input type="number" step="any" value="${num(m.above)}" data-action="ha-form" data-field="above" ${base}></div>
          <div class="form-group"><label>${this._t("ha_max")}</label>
          <input type="number" step="any" value="${num(m.below)}" data-action="ha-form" data-field="below" ${base}></div></div>`;
      } else {
        const field = m.operator === "below" ? "below" : "above";
        html += `<div class="form-row"><div class="form-group"><label>${this._t("ha_value")}</label>
          <input type="number" step="any" value="${num(m[field])}" data-action="ha-form" data-field="${field}" ${base}></div><div class="form-group"></div></div>`;
      }
    }
    return html;
  }

  _renderHaEntityInput(rule, idx, value) {
    const attrs = `data-action="ha-form" data-field="entity" data-rule="${this._esc(rule.id)}" data-idx="${idx}"`;
    if (!this._hass || !this._hass.states) {
      return `<input type="text" value="${this._esc(value || "")}" ${attrs}>`;
    }
    const listId = `ca-ha-ent-${this._esc(rule.id)}-${idx}`;
    const entities = Object.values(this._hass.states)
      .sort((a, b) => (a.attributes.friendly_name || a.entity_id).localeCompare(b.attributes.friendly_name || b.entity_id));
    let html = `<input type="text" list="${listId}" value="${this._esc(value || "")}" placeholder="${this._t("param_entity_search")}" autocomplete="off" ${attrs}>`;
    html += `<datalist id="${listId}">`;
    for (const e of entities) {
      html += `<option value="${this._esc(e.entity_id)}">${this._esc(e.attributes.friendly_name || e.entity_id)}</option>`;
    }
    return html + "</datalist>";
  }

  _renderHaStatus(ruleId, idx, formModel) {
    const incomplete = this._haFormIncomplete(formModel);
    if (incomplete) return `<div class="ha-msg ha-msg-info">${this._esc(this._t(incomplete))}</div>`;
    const st = this._haStatus(ruleId, idx);
    if (!st) return "";
    if (st.pending) return `<div class="ha-msg ha-msg-info">${this._esc(this._t("ha_checking"))}</div>`;
    let html = "";
    if (st.valid) {
      html += `<div class="ha-msg ha-msg-ok">✓ ${this._esc(this._t("ha_valid"))}</div>`;
    } else if (st.error_code && st.error_code !== "pending") {
      html += `<div class="ha-msg ha-msg-err">✕ ${this._esc(this._haErrorText(st))}</div>`;
    }
    if (Array.isArray(st.entities) && st.entities.length) {
      html += `<div class="ha-msg ha-msg-info">${this._esc(this._t("ha_entities"))}${this._colon()}${this._esc(st.entities.join(", "))}</div>`;
    }
    if (Array.isArray(st.unknown_entities) && st.unknown_entities.length) {
      html += `<div class="ha-msg ha-msg-warn">${this._esc(this._t("ha_unknown_entities"))}${this._colon()}${this._esc(st.unknown_entities.join(", "))}</div>`;
    }
    return html;
  }

  _haErrorText(st) {
    const fill = (tpl, values) => tpl.replace(/\{(\w+)\}/g, (mm, n) => (values[n] != null ? String(values[n]) : mm));
    switch (st.error_code) {
      case "yaml":
        return fill(this._t("ha_err_yaml"), { line: st.error_line ?? "?", column: st.error_column ?? "?" }) + (st.error ? " — " + st.error : "");
      case "not_mapping": return this._t("ha_err_not_mapping");
      case "empty": return this._t("ha_err_empty");
      case "request": return this._t("ha_err_request") + (st.error ? this._colon() + st.error : "");
      default: return this._t("ha_err_invalid") + (st.error ? this._colon() + st.error : "");
    }
  }

  _haCond(ruleId, idx) {
    const rule = this._edRule(ruleId);
    const cond = rule && rule.conditions ? rule.conditions[idx] : null;
    if (!cond || cond.type !== "ha_condition") return null;
    if (!cond.params) cond.params = {};
    return cond;
  }

  // Re-render a single condition card (keeps the rest of the editor intact).
  _rerenderCondCard(ruleId, idx) {
    const rule = this._edRule(ruleId);
    const root = this.shadowRoot;
    const card = root && root.querySelector(`.condition-card[data-cond-card="${CSS.escape(ruleId)}:${idx}"]`);
    if (!rule || !card) { this._render(); return; }
    const tmp = document.createElement("div");
    tmp.innerHTML = this._renderConditionCard(rule, idx);
    card.replaceWith(tmp.firstElementChild);
    this._refreshCondPreview();
  }

  _refreshHaStatusBox(ruleId, idx) {
    const cond = this._haCond(ruleId, idx);
    const box = this.shadowRoot && this.shadowRoot.querySelector(`[data-ha-status="${CSS.escape(ruleId)}:${idx}"]`);
    if (!cond || !box) return;
    const model = (cond.params.ui || "form") === "form" ? this._haFormModel(cond.params.config, cond.params.op) : null;
    box.innerHTML = this._renderHaStatus(ruleId, idx, model);
  }

  // Validate the condition with Home Assistant (debounced per card).
  _scheduleHaValidate(ruleId, idx, delay = 400) {
    const key = ruleId + ":" + idx;
    this._haTimers = this._haTimers || {};
    if (this._haTimers[key]) clearTimeout(this._haTimers[key]);
    this._haTimers[key] = setTimeout(() => {
      delete this._haTimers[key];
      this._runHaValidate(ruleId, idx);
    }, delay);
  }

  // Validate one card now. The result is dropped when the card no longer
  // holds the same condition (deleted, moved, draft discarded or reset).
  _runHaValidate(ruleId, idx) {
    const key = ruleId + ":" + idx;
    const cond = this._haCond(ruleId, idx);
    if (!cond) return Promise.resolve();
    const p = cond.params;
    const req = (p.ui || "form") === "yaml" ? { yaml: p.yaml || "" } : { config: p.config || null };
    const job = (async () => {
      try {
        const res = await this._ws("cover_automatic/condition/validate", req);
        if (!res || this._haCond(ruleId, idx) !== cond) return;
        (this._haLive = this._haLive || {})[key] = res;
        // A newer edit is already queued for validation otherwise.
        if (req.yaml !== undefined && p.yaml === req.yaml) p.config = res.config || null;
        this._refreshHaStatusBox(ruleId, idx);
        this._refreshCondPreview();
      } catch (e) {
        console.error(e);
        // Show the failure instead of "Checking…" forever
        if (this._haCond(ruleId, idx) !== cond) return;
        (this._haLive = this._haLive || {})[key] = this._haRequestError(e);
        this._refreshHaStatusBox(ruleId, idx);
      }
    })();
    this._haInflight = this._haInflight || {};
    this._haInflight[key] = job;
    job.finally(() => { if (this._haInflight[key] === job) delete this._haInflight[key]; });
    return job;
  }

  // Run pending (debounced) validations of a rule right away and wait for
  // all running ones, so params.config matches params.yaml before a save.
  async _flushHaValidations(ruleId = null) {
    const pre = ruleId != null ? ruleId + ":" : "";
    const jobs = [];
    for (const [key, t] of Object.entries(this._haTimers || {})) {
      if (pre && !key.startsWith(pre)) continue;
      clearTimeout(t);
      delete this._haTimers[key];
      const sep = key.lastIndexOf(":");
      jobs.push(this._runHaValidate(key.slice(0, sep), parseInt(key.slice(sep + 1), 10)));
    }
    for (const [key, job] of Object.entries(this._haInflight || {})) {
      if (!pre || key.startsWith(pre)) jobs.push(job);
    }
    await Promise.all(jobs.map(j => Promise.resolve(j).catch(() => {})));
  }

  // Drop pending validations of a rule (structural change: indices shift).
  _cancelHaTimers(ruleId) {
    const pre = ruleId + ":";
    for (const [key, t] of Object.entries(this._haTimers || {})) {
      if (!key.startsWith(pre)) continue;
      clearTimeout(t);
      delete this._haTimers[key];
    }
  }

  // Live status of a validation call that failed (connection, backend error)
  _haRequestError(e) {
    return { valid: false, error_code: "request", error: (e && (e.message || e.code)) ? String(e.message || e.code) : "" };
  }

  async _onHaUi(el) {
    const ruleId = el.dataset.rule, idx = parseInt(el.dataset.idx, 10);
    const cond = this._haCond(ruleId, idx);
    if (!cond) return;
    const mode = el.dataset.mode;
    const p = cond.params;
    if ((p.ui || "form") === mode) return;
    if (mode === "yaml") {
      // Render the current config as YAML (server-side dump)
      try {
        const res = await this._ws("cover_automatic/condition/validate", { config: p.config || null });
        if (this._haCond(ruleId, idx) !== cond) return;
        p.yaml = res && res.yaml ? res.yaml : (p.yaml || "");
        (this._haLive = this._haLive || {})[ruleId + ":" + idx] = res;
      } catch (e) {
        // Stay in the form: an outdated YAML text would replace the condition
        console.error(e);
        if (this._haCond(ruleId, idx) !== cond) return;
        (this._haLive = this._haLive || {})[ruleId + ":" + idx] = this._haRequestError(e);
        this._refreshHaStatusBox(ruleId, idx);
        this._showError(e);
        return;
      }
    } else {
      // Only switch when the form can represent the YAML (else a notice shows)
      if (p.yaml && p.yaml.trim()) {
        try {
          const res = await this._ws("cover_automatic/condition/validate", { yaml: p.yaml });
          if (this._haCond(ruleId, idx) !== cond) return;
          if (res && res.config) p.config = res.config;
          (this._haLive = this._haLive || {})[ruleId + ":" + idx] = res;
        } catch (e) {
          // Stay in YAML: the form would show the config of the old text
          console.error(e);
          if (this._haCond(ruleId, idx) !== cond) return;
          (this._haLive = this._haLive || {})[ruleId + ":" + idx] = this._haRequestError(e);
          this._refreshHaStatusBox(ruleId, idx);
          this._showError(e);
          return;
        }
      }
    }
    p.ui = mode;
    this._rerenderCondCard(ruleId, idx);
  }

  _onHaFormChange(el, isInputEvent) {
    const ruleId = el.dataset.rule, idx = parseInt(el.dataset.idx, 10);
    const cond = this._haCond(ruleId, idx);
    if (!cond) return;
    const p = cond.params;
    const m = this._haFormModel(p.config, p.op) || this._haFormModel(this._haDefaultConfig("state"));
    const field = el.dataset.field;
    let structural = false;
    const toNum = (v) => (v === "" || v == null ? null : Number(v));
    switch (field) {
      case "kind": {
        const next = this._haFormModel(this._haDefaultConfig(el.value));
        next.entity = m.entity;
        m.above = undefined; m.below = undefined;
        Object.assign(m, next);
        structural = true;
        break;
      }
      case "entity":
        if (isInputEvent) return; // wait for the value to be committed (change)
        m.entity = el.value.trim();
        m.attribute = "";
        if (m.kind === "state") m.states = [];
        structural = true;
        break;
      case "attribute":
        m.attribute = el.value;
        if (m.kind === "state") m.states = [];
        structural = true;
        break;
      case "negate":
        m.negate = el.value === "1";
        structural = true;
        break;
      case "for":
        m.forMinutes = toNum(el.value);
        break;
      case "operator":
        m.operator = el.value;
        structural = true;
        break;
      case "above":
        m.above = toNum(el.value);
        break;
      case "below":
        m.below = toNum(el.value);
        break;
      default:
        return;
    }
    p.config = this._haFormToConfig(m);
    p.op = m.kind === "numeric" ? m.operator : undefined;
    p.yaml = ""; // regenerated from config when switching to YAML
    if (structural) this._rerenderCondCard(ruleId, idx);
    else this._refreshHaStatusBox(ruleId, idx);
    this._scheduleHaValidate(ruleId, idx);
  }

  _onHaStateToggle(el, forceAdd = null) {
    const ruleId = el.dataset.rule, idx = parseInt(el.dataset.idx, 10);
    const cond = this._haCond(ruleId, idx);
    if (!cond) return;
    const m = this._haFormModel(cond.params.config);
    if (!m || m.kind !== "state") return;
    const val = forceAdd != null ? forceAdd : el.dataset.val;
    if (!val) return;
    if (m.states.includes(val)) {
      if (forceAdd == null) m.states = m.states.filter(s => s !== val);
    } else {
      m.states.push(val);
    }
    cond.params.config = this._haFormToConfig(m);
    cond.params.yaml = "";
    this._rerenderCondCard(ruleId, idx);
    this._scheduleHaValidate(ruleId, idx);
  }

  _onHaStateAdd(el) {
    const key = el.dataset.rule + ":" + el.dataset.idx;
    const input = this.shadowRoot.querySelector(`[data-ha-other="${CSS.escape(key)}"]`);
    const val = input ? input.value.trim() : "";
    if (val) this._onHaStateToggle(el, val);
  }

  _onHaYamlInput(el) {
    const ruleId = el.dataset.rule, idx = parseInt(el.dataset.idx, 10);
    const cond = this._haCond(ruleId, idx);
    if (!cond) return;
    cond.params.yaml = el.value;
    (this._haLive = this._haLive || {})[ruleId + ":" + idx] = { pending: true };
    this._refreshHaStatusBox(ruleId, idx);
    this._scheduleHaValidate(ruleId, idx, 600);
  }

  // Convert a legacy state_is / numeric_state condition into an ha_condition.
  _onCondConvert(el) {
    const ruleId = el.dataset.rule, idx = parseInt(el.dataset.idx, 10);
    const rule = this._edRule(ruleId);
    const cond = rule && rule.conditions ? rule.conditions[idx] : null;
    if (!cond) return;
    const p = cond.params || {};
    const entity = p.entity_id || p.entity || "";
    let config;
    if (cond.type === "state_is") {
      config = { condition: "state", entity_id: entity, state: p.state != null ? String(p.state) : [] };
    } else if (cond.type === "numeric_state") {
      config = { condition: "numeric_state", entity_id: entity };
      const v = Number(p.value);
      if (Number.isFinite(v)) {
        if (String(p.operator || "above") === "below") config.below = v; else config.above = v;
      }
    } else {
      return;
    }
    const prev = rule.conditions[idx] || {};
    rule.conditions[idx] = { type: "ha_condition", params: { ui: "form", config, yaml: "" }, group: prev.group || 0, negate: !!prev.negate };
    this._rerenderCondCard(ruleId, idx);
    this._scheduleHaValidate(ruleId, idx, 0);
  }

  // Readable summary of a condition for the collapsed rule chips.
  _condChipLabel(c) {
    if (c.type !== "ha_condition") return this._t("cond_" + c.type);
    const cfg = c.params && c.params.config;
    const m = this._haFormModel(cfg, c.params && c.params.op);
    const fill = (tpl, values) => tpl.replace(/\{(\w+)\}/g, (mm, n) => (values[n] != null ? String(values[n]) : mm));
    if (m && m.entity) {
      const stateObj = this._hass?.states ? this._hass.states[m.entity] : null;
      let name = this._haEntityName(m.entity);
      if (m.attribute) name += " · " + this._haAttributeLabel(stateObj, m.attribute);
      if (m.kind === "state") {
        const states = m.states.map(s => "« " + this._haStateLabel(stateObj, m.attribute, s) + " »").join(this._t("ha_chip_or"));
        let txt = fill(this._t(m.negate ? "ha_chip_is_not" : "ha_chip_is"), { entity: name, states });
        if (!m.negate && m.forMinutes) txt += fill(this._t("ha_chip_for"), { min: Math.round(m.forMinutes * 100) / 100 });
        return txt;
      }
      if (m.operator === "between") return fill(this._t("ha_chip_between"), { entity: name, min: m.above, max: m.below });
      return fill(this._t(m.operator === "below" ? "ha_chip_below" : "ha_chip_above"), { entity: name, value: m.operator === "below" ? m.below : m.above });
    }
    if (cfg && cfg.condition) {
      let type = this._i18nOr("ha_ctype_" + cfg.condition, String(cfg.condition));
      if (Array.isArray(cfg.conditions)) type += " (" + cfg.conditions.length + ")";
      return fill(this._t("ha_chip_other"), { type });
    }
    return this._t("cond_ha_condition");
  }

  _renderRuleAddForm() {
    let html = `<div class="inline-form mt-16">
      <div class="form-group">
        <label>${this._t("name")}</label>
        <input type="text" value="" data-rule-new-field="name" maxlength="100" placeholder="${this._t("name")}">
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>${this._t("rule_target_pos")}</label>
          <input type="number" min="0" max="100" value="0" data-rule-new-field="target_position">
        </div>
        <div class="form-group">
          <label>${this._t("rule_target_tilt")}</label>
          <input type="number" min="0" max="100" value="" placeholder="${this._t("none")}" data-rule-new-field="target_tilt_position">
        </div>
      </div>
      <div class="form-actions">
        <button class="btn btn-secondary" data-action="rule-add-cancel">${this._t("cancel")}</button>
        <button class="btn btn-primary" data-action="rule-add-save">${this._t("add")}</button>
      </div>
    </div>`;
    return html;
  }

  /* ============================================================
   * TAB: Scenarios
   * ============================================================ */
  _renderScenarios() {
    const scenarios = this._config.scenarios || {};
    const rules = this._config.rules || {};
    const activeId = (this._config.settings || {}).active_scenario || this._config.active_scenario;
    const entries = Object.values(scenarios);

    let html = '<div class="card-grid">';

    for (const sc of entries) {
      const isActive = sc.id === activeId;
      const isEditing = this._editingScenario === sc.id;

      if (isEditing) {
        html += this._renderScenarioEditForm(sc, rules, isActive);
      } else {
        html += this._renderScenarioCard(sc, rules, isActive);
      }
    }

    // Add
    if (this._addingScenario) {
      html += this._renderScenarioAddForm();
    } else {
      html += `<button class="add-card" data-action="scenario-add-start">+ ${this._t("scenario_add")}</button>`;
    }

    html += '</div>';
    return html;
  }

  // Rules in the order of the Rules tab: highest priority first, ties broken
  // by rule id -- the same order the engine uses to pick the winning rule.
  _rulesByPriority(rules) {
    return Object.values(rules || {}).sort((a, b) =>
      // Same tie-break as the engine (plain code point order of the ids)
      ((b.priority ?? 0) - (a.priority ?? 0)) || (String(a.id) < String(b.id) ? -1 : String(a.id) > String(b.id) ? 1 : 0));
  }

  // Rules that belong to a scenario (scenario_ids null = every scenario).
  _ruleInScenario(rule, scenarioId) {
    return !Array.isArray(rule.scenario_ids) || rule.scenario_ids.includes(scenarioId);
  }

  _renderScenarioCard(sc, rules, isActive) {
    const ruleEntries = this._rulesByPriority(rules).filter(r => this._ruleInScenario(r, sc.id));
    let html = `<div class="scenario-card${isActive ? " active-scenario" : ""}">
      <div class="sc-header">
        <div class="sc-name">
          ${sc.icon ? `<ha-icon icon="${this._esc(sc.icon)}" class="scenario-card-icon"></ha-icon>` : ""}${this._esc(sc.name)}
          ${isActive ? `<span class="chip">${this._t("active")}</span>` : ""}
        </div>
        <div class="sc-actions">
          ${!isActive ? `<button class="btn btn-primary btn-sm" data-action="scenario-activate" data-id="${this._esc(sc.id)}">${this._t("activate")}</button>` : ""}
          <button class="btn btn-secondary btn-sm" data-action="scenario-edit" data-id="${this._esc(sc.id)}">${this._t("edit")}</button>
          <button class="btn btn-danger btn-sm" data-action="scenario-delete" data-id="${this._esc(sc.id)}">${this._t("delete")}</button>
        </div>
      </div>`;

    // Rules list with enabled/disabled toggles
    html += '<div class="sc-rules">';
    if (ruleEntries.length === 0) {
      html += `<div class="scenario-no-rules">${this._t(Object.keys(rules || {}).length ? "scenario_no_member_rules" : "scenario_no_rules")}</div>`;
    } else {
      for (const [ri, r] of ruleEntries.entries()) {
        const disabled = (sc.rules_disabled || []).includes(r.id);
        // A rule switched off in the Rules tab never runs, whatever the
        // scenario says: show it greyed out. Its scenario toggle stays usable
        // and takes effect once the rule is enabled again.
        const ruleOff = r.enabled === false;
        html += `<div class="sc-rule-row${ruleOff ? " sc-rule-off" : ""}"${ruleOff ? ` title="${this._esc(this._t("scenario_rule_off_hint"))}"` : ""}>
          <span class="sc-rule-label"><span class="priority-badge">#${ri + 1}</span><span${disabled ? ' class="sc-rule-disabled"' : ""}>${this._esc(r.name)}</span>${r.safety ? `<span class="rule-safety-badge" title="${this._esc(this._t("rule_safety"))}">${this._lucideIcon("shield", 12)}${this._esc(this._t("rule_safety_badge"))}</span>` : ""}${ruleOff ? `<span class="sc-rule-off-badge">${this._esc(this._t("scenario_rule_off"))}</span>` : ""}</span>
          <label class="toggle">
            <input type="checkbox" ${!disabled ? "checked" : ""} data-action="scenario-rule-toggle" data-scenario="${this._esc(sc.id)}" data-rule="${this._esc(r.id)}">
            <span class="toggle-slider"></span>
          </label>
        </div>`;
      }
    }
    html += '</div></div>';
    return html;
  }

  _renderScenarioIconPicker(currentIcon) {
    const selected = (currentIcon || "").trim();
    const inGrid = SCENARIO_ICON_CHOICES.includes(selected);
    const customValue = inGrid ? "" : selected;
    let grid = "";
    for (const ic of SCENARIO_ICON_CHOICES) {
      const cls = ic === selected ? "icon-picker-btn selected" : "icon-picker-btn";
      grid += `<button type="button" class="${cls}" data-action="scenario-icon-pick" data-icon="${this._esc(ic)}" title="${this._esc(ic)}"><ha-icon icon="${this._esc(ic)}"></ha-icon></button>`;
    }
    return `
      <input type="hidden" data-scenario-field="icon" value="${this._esc(selected)}">
      <div class="icon-picker-grid">${grid}</div>
      <details class="icon-picker-custom"${customValue ? " open" : ""}>
        <summary>${this._t("scenario_icon_custom")}</summary>
        <div class="icon-picker-custom-body">
          <input type="text" data-scenario-icon-custom value="${this._esc(customValue)}" placeholder="mdi:lightbulb">
          <div class="icon-picker-custom-hint">${this._t("scenario_icon_custom_hint")}</div>
        </div>
      </details>`;
  }

  _renderScenarioEditForm(sc, rules, isActive) {
    let html = `<div class="inline-form">
      <div class="form-group">
        <label>${this._t("name")}</label>
        <input type="text" value="${this._esc(sc.name)}" data-scenario-field="name">
      </div>
      <div class="form-group">
        <label>${this._t("scenario_icon")}</label>
        ${this._renderScenarioIconPicker(sc.icon || "")}
      </div>
      <div class="form-actions">
        <button class="btn btn-secondary" data-action="scenario-edit-cancel">${this._t("cancel")}</button>
        <button class="btn btn-primary" data-action="scenario-edit-save" data-id="${this._esc(sc.id)}">${this._t("save")}</button>
      </div>
    </div>`;
    return html;
  }

  _renderScenarioAddForm() {
    let html = `<div class="inline-form">
      <div class="form-group">
        <label>${this._t("name")}</label>
        <input type="text" value="" data-scenario-field="name" placeholder="${this._t("name")}">
      </div>
      <div class="form-group">
        <label>${this._t("scenario_icon")}</label>
        ${this._renderScenarioIconPicker("mdi:home")}
      </div>
      <div class="form-actions">
        <button class="btn btn-secondary" data-action="scenario-add-cancel">${this._t("cancel")}</button>
        <button class="btn btn-primary" data-action="scenario-add-save">${this._t("add")}</button>
      </div>
    </div>`;
    return html;
  }

  /* ============================================================
   * TAB: Settings
   * ============================================================ */
  _renderEntitySelect(field, currentValue, domain, deviceClass) {
    if (!this._hass || !this._hass.states) return `<input type="text" value="${this._esc(currentValue || "")}" data-settings-field="${field}">`;
    const entities = Object.values(this._hass.states)
      .filter(s => {
        if (!s.entity_id.startsWith(domain + ".")) return false;
        if (deviceClass && s.attributes.device_class !== deviceClass) return false;
        return true;
      })
      .sort((a, b) => (a.attributes.friendly_name || a.entity_id).localeCompare(b.attributes.friendly_name || b.entity_id));
    let html = `<select data-settings-field="${field}">`;
    html += `<option value="">-- ${this._t("none")} --</option>`;
    for (const e of entities) {
      const name = e.attributes.friendly_name || e.entity_id;
      const sel = e.entity_id === currentValue ? " selected" : "";
      html += `<option value="${this._esc(e.entity_id)}"${sel}>${this._esc(name)} (${this._esc(e.entity_id)})</option>`;
    }
    // A configured entity outside the filter (other device class, not loaded
    // yet) stays selected instead of being cleared by the next save.
    if (currentValue && !entities.some(e => e.entity_id === currentValue)) {
      html += `<option value="${this._esc(currentValue)}" selected>${this._esc(currentValue)}</option>`;
    }
    html += "</select>";
    return html;
  }

  _renderCoverEntitySelect(field, currentValue, coverId, domain, deviceClass) {
    if (!this._hass || !this._hass.states) return `<input type="text" value="${this._esc(currentValue || "")}" data-action="cover-input" data-id="${this._esc(coverId)}" data-field="${field}">`;
    const entities = Object.values(this._hass.states)
      .filter(s => {
        const domains = Array.isArray(domain) ? domain : [domain];
        if (!domains.some(d => s.entity_id.startsWith(d + "."))) return false;
        if (deviceClass && s.attributes.device_class !== deviceClass) return false;
        return true;
      })
      .sort((a, b) => (a.attributes.friendly_name || a.entity_id).localeCompare(b.attributes.friendly_name || b.entity_id));
    let html = `<select data-action="cover-input" data-id="${this._esc(coverId)}" data-field="${field}">`;
    html += `<option value="">-- ${this._t("none")} --</option>`;
    for (const e of entities) {
      const name = e.attributes.friendly_name || e.entity_id;
      const sel = e.entity_id === currentValue ? " selected" : "";
      html += `<option value="${this._esc(e.entity_id)}"${sel}>${this._esc(name)} (${this._esc(e.entity_id)})</option>`;
    }
    // A configured entity outside the filter (other device class, not loaded
    // yet, removed) stays shown and selected instead of reading as "none".
    if (currentValue && !entities.some(e => e.entity_id === currentValue)) {
      html += `<option value="${this._esc(currentValue)}" selected>${this._esc(currentValue)}</option>`;
    }
    html += "</select>";
    return html;
  }

  // Entity picker for rule conditions (state_is). Not domain-restricted: any
  // entity can be checked. A plain <select> grows unsearchably long, so this
  // is a text input backed by a <datalist> -- typing filters suggestions by
  // friendly name or entity id, and free text stays allowed (entities that are
  // not loaded yet, future entities).
  _renderCondEntitySelect(rule, idx, key, currentValue) {
    const attrs = `data-action="cond-param" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${this._esc(key)}"`;
    const cur = currentValue || "";
    if (!this._hass || !this._hass.states) {
      return `<input type="text" value="${this._esc(String(cur))}" ${attrs}>`;
    }
    const listId = `ca-ent-${this._esc(rule.id)}-${idx}`;
    const entities = Object.values(this._hass.states)
      .sort((a, b) => (a.attributes.friendly_name || a.entity_id).localeCompare(b.attributes.friendly_name || b.entity_id));
    let html = `<input type="text" list="${listId}" value="${this._esc(String(cur))}" placeholder="${this._t("param_entity_search")}" autocomplete="off" ${attrs}>`;
    html += `<datalist id="${listId}">`;
    for (const e of entities) {
      const name = e.attributes.friendly_name || e.entity_id;
      // value is the entity id (what gets stored); label shows the friendly name
      html += `<option value="${this._esc(e.entity_id)}">${this._esc(name)}</option>`;
    }
    html += "</datalist>";
    return html;
  }

  _renderSensorValue(entityId, unit) {
    if (!entityId || !this._hass || !this._hass.states) return "";
    const state = this._hass.states[entityId];
    if (!state || state.state === "unavailable" || state.state === "unknown") return "";
    let text;
    if (!unit && typeof this._hass.formatEntityState === "function") {
      try { text = this._hass.formatEntityState(state); } catch (e) { text = undefined; }
    }
    if (!text) text = state.state + (unit || state.attributes.unit_of_measurement || "");
    return '<div class="sensor-current-value">' + this._t("settings_current_value") + this._colon() + this._esc(text) + '</div>';
  }

  // Entities that can provide a threshold value (numbers and numeric text).
  _thresholdEntityOptions(currentValue, kind = null) {
    const states = (this._hass && this._hass.states) || {};
    const list = Object.values(states).filter(st => {
      const dom = st.entity_id.split(".")[0];
      if (kind === "temperature") {
        // Setpoints: number helpers, and sensors in degrees only
        if (dom === "input_number" || dom === "number") return true;
        const u = st.attributes.unit_of_measurement;
        return dom === "sensor" && (st.attributes.device_class === "temperature" || u === "°C" || u === "°F");
      }
      if (dom === "input_number" || dom === "number" || dom === "input_text") return true;
      // Sensors: only numeric ones (a text sensor cannot be a threshold)
      return dom === "sensor" && (st.attributes.unit_of_measurement != null || Number.isFinite(parseFloat(st.state)));
    }).sort((a, b) => (a.attributes.friendly_name || a.entity_id).localeCompare(b.attributes.friendly_name || b.entity_id));
    let html = `<option value="">-- ${this._t("none")} --</option>`;
    let found = false;
    for (const e of list) {
      const name = e.attributes.friendly_name || e.entity_id;
      const sel = e.entity_id === currentValue;
      if (sel) found = true;
      html += `<option value="${this._esc(e.entity_id)}"${sel ? " selected" : ""}>${this._esc(name)} (${this._esc(e.entity_id)})</option>`;
    }
    // Keep a configured entity selectable even when it is not loaded
    if (currentValue && !found) html += `<option value="${this._esc(currentValue)}" selected>${this._esc(currentValue)}</option>`;
    return html;
  }

  // Current value of a threshold entity, e.g. "currently: 23 °C".
  _thresholdEntityValue(entityId) {
    if (!entityId) return "";
    const st = this._hass && this._hass.states ? this._hass.states[entityId] : null;
    if (!st || st.state === "unavailable" || st.state === "unknown" || st.state === "") {
      return `<span class="threshold-entity-unavail">${this._esc(this._t("threshold_entity_unavailable"))}</span>`;
    }
    const u = st.attributes.unit_of_measurement;
    return this._esc(this._t("threshold_entity_current") + this._colon() + st.state + (u ? " " + u : ""));
  }

  // Optional entity next to a numeric threshold. attrs: the select's
  // data attributes (settings field or cover-input).
  _renderThresholdEntity(attrs, currentValue, kind = null) {
    const cur = currentValue || "";
    const control = (this._hass && this._hass.states)
      ? `<select ${attrs} data-threshold-entity>${this._thresholdEntityOptions(cur, kind)}</select>`
      : `<input type="text" value="${this._esc(cur)}" ${attrs} data-threshold-entity>`;
    return `<div class="threshold-entity">
      <div class="threshold-entity-label">${this._esc(this._t("threshold_entity"))}</div>
      ${control}
      <div class="threshold-entity-value">${this._thresholdEntityValue(cur)}</div>
      ${this._hint("threshold_entity_hint")}
    </div>`;
  }

  _renderCompassSVG(rotation) {
    const cx = 140, cy = 140, r = 88, hr = 28;
    const sunState = this._hass ? this._hass.states["sun.sun"] : null;
    const sunAz = sunState ? parseFloat(sunState.attributes.azimuth) : null;
    const sunEl = sunState ? parseFloat(sunState.attributes.elevation) : null;
    const belowHorizon = sunEl != null && sunEl < 0;

    // Facade arcs -- muted, harmonized palette (same saturation, varying hue).
    // Two layers per arc: wide faint underlay + narrow crisp core, round caps.
    const facades = this._config ? Object.values(this._config.facades || {}) : [];
    let facadeArcs = "";
    const facadeColors = ["#7da7c8", "#7fb89e", "#c4a979", "#c98969", "#b878a1", "#8a7eb5"];
    facades.forEach((f, i) => {
      const azS = this._facadeAz(f.azimuth_start, 0), azE = this._facadeAz(f.azimuth_end, 0);
      const startDeg = (azS - 90) * Math.PI / 180;
      const endDeg = (azE - 90) * Math.PI / 180;
      const arcR = r - 8;
      const col = facadeColors[i % facadeColors.length];
      if (azS === azE) {
        // start == end: full-circle facade (sun-exposed from every direction)
        facadeArcs += `<circle cx="${cx}" cy="${cy}" r="${arcR}" fill="none" stroke="${col}" stroke-width="9" opacity="0.18"/>`;
        facadeArcs += `<circle cx="${cx}" cy="${cy}" r="${arcR}" fill="none" stroke="${col}" stroke-width="3.5" opacity="0.9"/>`;
        const lRad = (azS - 90) * Math.PI / 180;
        const lx = cx + (arcR - 15) * Math.cos(lRad), ly = cy + (arcR - 15) * Math.sin(lRad);
        facadeArcs += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="central" font-size="9" letter-spacing="0.3" fill="${col}" font-weight="600">${this._esc(String(f.name || "").substring(0, 8))}</text>`;
        return;
      }
      const x1 = cx + arcR * Math.cos(startDeg), y1 = cy + arcR * Math.sin(startDeg);
      const x2 = cx + arcR * Math.cos(endDeg), y2 = cy + arcR * Math.sin(endDeg);
      let sweep = azE - azS;
      if (sweep < 0) sweep += 360;
      const large = sweep > 180 ? 1 : 0;
      const d = `M${x1},${y1} A${arcR},${arcR} 0 ${large},1 ${x2},${y2}`;
      facadeArcs += `<path d="${d}" fill="none" stroke="${col}" stroke-width="9" stroke-linecap="round" opacity="0.18"/>`;
      facadeArcs += `<path d="${d}" fill="none" stroke="${col}" stroke-width="3.5" stroke-linecap="round" opacity="0.9"/>`;
      // Label
      const midDeg = (azS + sweep / 2 - 90) * Math.PI / 180;
      const lx = cx + (arcR - 15) * Math.cos(midDeg), ly = cy + (arcR - 15) * Math.sin(midDeg);
      facadeArcs += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="central" font-size="9" letter-spacing="0.3" fill="${col}" font-weight="600">${this._esc(f.name.substring(0, 8))}</text>`;
    });

    // Sun position -- soft radial glow behind the disc, fine rays, and a
    // light cone rendered as a directional gradient fading toward the house
    let sunMarker = "";
    let sunBeams = "";
    let beamGradient = "";
    if (sunAz != null && !isNaN(sunAz) && !belowHorizon) {
      const sunRad = (sunAz - 90) * Math.PI / 180;
      const sr = r + 28;
      const sx = cx + sr * Math.cos(sunRad), sy = cy + sr * Math.sin(sunRad);
      // Sun symbol rays (radiating outward)
      const symbolRays = [0,45,90,135,180,225,270,315].map(d => {
        const rr = d * Math.PI / 180;
        const x1 = sx + 10.5 * Math.cos(rr), y1 = sy + 10.5 * Math.sin(rr);
        const x2 = sx + 14.5 * Math.cos(rr), y2 = sy + 14.5 * Math.sin(rr);
        return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--ca-sun)" stroke-width="1.5" stroke-linecap="round" opacity="0.9"/>`;
      }).join("");
      // Light cone toward house facade (trapezoid: narrow at sun, wide at house)
      const dx = cx - sx, dy = cy - sy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const ndx = dx / dist, ndy = dy / dist;
      const perpX = -ndy, perpY = ndx;
      const sunW = 4;
      const facadeW = hr + 20;
      const facadeDist = dist + hr * 0.5 + 20;
      const fx = sx + ndx * facadeDist, fy = sy + ndy * facadeDist;
      beamGradient = `<linearGradient id="ca-beam" gradientUnits="userSpaceOnUse" x1="${sx}" y1="${sy}" x2="${fx}" y2="${fy}">
          <stop offset="0" stop-color="var(--ca-sun)" stop-opacity="0.22"/>
          <stop offset="1" stop-color="var(--ca-sun)" stop-opacity="0.02"/>
        </linearGradient>`;
      sunBeams = `<polygon points="${sx + perpX * sunW},${sy + perpY * sunW} ${sx - perpX * sunW},${sy - perpY * sunW} ${fx - perpX * facadeW},${fy - perpY * facadeW} ${fx + perpX * facadeW},${fy + perpY * facadeW}" fill="url(#ca-beam)"/>`;
      sunMarker = `<circle cx="${sx}" cy="${sy}" r="20" fill="url(#ca-sun-glow)" pointer-events="none"/>
        ${symbolRays}<circle cx="${sx}" cy="${sy}" r="7" fill="var(--ca-sun)" stroke="var(--ca-sun-outline)" stroke-width="1"/>
        <text x="${sx}" y="${sy + 27}" text-anchor="middle" font-size="9" fill="var(--ca-sun)" font-weight="600">\u2220${Math.round(sunEl)}\u00B0</text>`;
    }

    // Outdoor temperature info text at bottom of SVG
    let infoText = "";
    const settings = this._config ? this._config.settings || {} : {};
    const tempEntity = settings.outdoor_temp_sensor;
    if (tempEntity && this._hass?.states[tempEntity]) {
      const tempState = this._hass.states[tempEntity];
      const tempVal = parseFloat(tempState.state);
      if (!isNaN(tempVal)) {
        infoText = `${this._t("settings_outdoor_temp_short")} ${tempVal.toFixed(1)}\u00B0C`;
      }
    }

    const svgW = 280, svgH = infoText ? 302 : 288;
    const infoSvg = infoText ? `<text x="${cx}" y="${svgH - 4}" text-anchor="middle" font-size="11" fill="var(--ca-secondary-text)">${infoText}</text>` : "";
    return `<svg id="compass-svg" class="compass-svg-root" width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}">
      <defs>
        <filter id="ca-house-shadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="1.5" stdDeviation="2.5" flood-color="#000" flood-opacity="0.3"/>
        </filter>
        <radialGradient id="ca-sun-glow">
          <stop offset="0" stop-color="var(--ca-sun)" stop-opacity="0.35"/>
          <stop offset="1" stop-color="var(--ca-sun)" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="ca-house-sheen" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#fff" stop-opacity="0.09"/>
          <stop offset="1" stop-color="#fff" stop-opacity="0"/>
        </linearGradient>
        ${beamGradient}
      </defs>
      <!-- Compass rings: quiet outer ring, fine dotted inner ring -->
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--divider-color)" stroke-width="1"/>
      <circle cx="${cx}" cy="${cy}" r="${r - 20}" fill="none" stroke="var(--divider-color)" stroke-width="1" stroke-dasharray="0.5 6" stroke-linecap="round" opacity="0.8"/>
      <!-- Cardinal directions (fixed); N carries the accent as rotation reference -->
      <text x="${cx}" y="${cy - r - 8}" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="1" fill="var(--ca-primary)">${this._esc(this._t("compass_n"))}</text>
      <text x="${cx}" y="${cy + r + 18}" text-anchor="middle" font-size="12" font-weight="600" letter-spacing="1" fill="var(--ca-secondary-text)">${this._esc(this._t("compass_s"))}</text>
      <text x="${cx + r + 11}" y="${cy + 4}" text-anchor="middle" font-size="12" font-weight="600" letter-spacing="1" fill="var(--ca-secondary-text)">${this._esc(this._t("compass_e"))}</text>
      <text x="${cx - r - 11}" y="${cy + 4}" text-anchor="middle" font-size="12" font-weight="600" letter-spacing="1" fill="var(--ca-secondary-text)">${this._esc(this._t("compass_w"))}</text>
      <!-- North marker: filled triangle pointing inward from the ring -->
      <polygon points="${cx - 3.5},${cy - r} ${cx + 3.5},${cy - r} ${cx},${cy - r + 8}" fill="var(--ca-primary)"/>
      <!-- Tick marks (north replaced by the triangle marker) -->
      ${[45,90,135,180,225,270,315].map(d => { const rad=(d-90)*Math.PI/180; const i=d%90===0?9:5; return `<line x1="${cx+(r-i)*Math.cos(rad)}" y1="${cy+(r-i)*Math.sin(rad)}" x2="${cx+r*Math.cos(rad)}" y2="${cy+r*Math.sin(rad)}" stroke="var(--primary-text-color)" stroke-width="${d%90===0?1.5:1}" opacity="${d%90===0?0.5:0.25}"/>`; }).join("")}
      <!-- Sun beams (behind house) -->
      ${sunBeams}
      <!-- House (rotated, on top of beams) -->
      <g id="compass-house" transform="rotate(${rotation}, ${cx}, ${cy})" data-action="house-drag-start" filter="url(#ca-house-shadow)">
        <rect x="${cx - hr}" y="${cy - hr}" width="${hr * 2}" height="${hr * 2}" rx="4" fill="var(--primary-background-color, #1c1c1c)" stroke="var(--primary-color)" stroke-width="1.5"/>
        <rect x="${cx - hr + 1.5}" y="${cy - hr + 1.5}" width="${hr * 2 - 3}" height="${hr * 2 - 3}" rx="3" fill="url(#ca-house-sheen)" stroke="none" pointer-events="none"/>
        <!-- Roof indicator (front = south of house before rotation) -->
        <line x1="${cx - hr + 7}" y1="${cy + hr}" x2="${cx + hr - 7}" y2="${cy + hr}" stroke="var(--primary-color)" stroke-width="2.5" stroke-linecap="round" pointer-events="none"/>
        <text id="compass-degree-label" x="${cx}" y="${cy + 4}" text-anchor="middle" font-size="12" font-weight="600" fill="var(--primary-text-color)" opacity="0.75" pointer-events="none">${rotation}°</text>
      </g>
      <!-- Facade arcs -->
      ${facadeArcs}
      <!-- Sun -->
      ${sunMarker}
      <!-- Info -->
      ${infoSvg}
    </svg>`;
  }

  _renderSettings() {
    const s = this._config.settings || {};
    const hint = (text) => `<div class="settings-hint">${text}</div>`;
    const hintIntro = (text) => `<div class="settings-hint-intro">${text}</div>`;
    let active = this._activeSettingsSection || "house";
    if (active === "solar") active = this._activeSettingsSection = "comfort";

    const sections = [
      { id: "house", labelKey: "settings_section_house", icon: this._lucideIcon("house", 16) },
      { id: "sensors", labelKey: "settings_section_sensors", icon: this._lucideIcon("gauge", 16) },
      { id: "comfort", labelKey: "settings_section_comfort", icon: this._lucideIcon("sun", 16) },
      { id: "wind", labelKey: "settings_section_wind", icon: this._lucideIcon("wind", 16) },
      { id: "automation", labelKey: "settings_section_automation", icon: this._lucideIcon("cog", 16) },
      { id: "backup", labelKey: "settings_section_backup", icon: this._lucideIcon("archive", 16) }
    ];

    let html = '<div class="settings-shell">';

    // Sidebar navigation
    html += '<aside class="settings-nav" role="tablist" aria-label="' + this._esc(this._t("settings_nav_label")) + '">';
    for (const sec of sections) {
      const isActive = sec.id === active;
      const cls = "settings-nav-btn" + (isActive ? " active" : "");
      html += '<button class="' + cls + '" role="tab" aria-selected="' + (isActive ? "true" : "false") + '" data-action="settings-section" data-section="' + sec.id + '">';
      html += '<span class="settings-nav-icon">' + sec.icon + '</span>';
      html += '<span class="settings-nav-label">' + this._esc(this._t(sec.labelKey)) + '</span>';
      html += '</button>';
    }
    html += '</aside>';

    // Content column
    html += '<div class="settings-content"><div class="settings-stack">';

    // House section
    if (active === "house") {
      const rot = this._num(s.house_rotation, 0);
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("house")} ${this._t("settings_section_house")}</div>
      <div class="card-body">
        <div class="settings-house-layout">
          <div class="form-group settings-house-input">
            <label>${this._t("settings_house_rotation")}</label>
            <input type="number" step="0.5" min="-180" max="180" value="${rot}" data-settings-field="house_rotation" id="house-rotation-input">
            <div class="rotation-quick">
              <button type="button" class="rotation-quick-btn" data-action="rotate-by" data-delta="-45">−45°</button>
              <button type="button" class="rotation-quick-btn" data-action="rotate-by" data-delta="-5">−5°</button>
              <button type="button" class="rotation-quick-btn rotation-quick-reset" data-action="rotate-by" data-set="0">${this._t("settings_house_rotation_reset")}</button>
              <button type="button" class="rotation-quick-btn" data-action="rotate-by" data-delta="5">+5°</button>
              <button type="button" class="rotation-quick-btn" data-action="rotate-by" data-delta="45">+45°</button>
            </div>
            ${hint(this._t("settings_house_rotation_hint"))}
          </div>
          <div class="settings-house-compass">${this._renderCompassSVG(rot)}</div>
        </div>
      </div>
    </div>`;
    }

    // Sensors section (outdoor/indoor/weather/workday)
    if (active === "sensors") {
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("gauge")} ${this._t("settings_section_sensors")}</div>
      <div class="card-body">
        ${this._optBox({
          title: this._t("settings_comfort_range_title"),
          head: `<div class="form-group">
            <label>${this._L("settings_indoor_temp")}</label>
            ${this._renderEntitySelect("indoor_temp_sensor", s.indoor_temp_sensor, "sensor", "temperature")}
            ${this._renderSensorValue(s.indoor_temp_sensor, "\u00B0")}
            ${hint(this._t("settings_indoor_temp_hint"))}
          </div>`,
          body: `${hintIntro(this._t("settings_comfort_hint"))}
          <div class="form-row">
            <div class="form-group">
              <label>${this._L("settings_comfort_min")}</label>
              <input type="number" step="0.5" value="${this._num(s.comfort_temp_min, 21)}" data-settings-field="comfort_temp_min">
              ${this._renderThresholdEntity('data-settings-field="comfort_temp_min_entity"', s.comfort_temp_min_entity, "temperature")}
            </div>
            <div class="form-group">
              <label>${this._L("settings_comfort_max")}</label>
              <input type="number" step="0.5" value="${this._num(s.comfort_temp_max, 25)}" data-settings-field="comfort_temp_max">
              ${this._renderThresholdEntity('data-settings-field="comfort_temp_max_entity"', s.comfort_temp_max_entity, "temperature")}
            </div>
          </div>
          <div class="form-group">
            <label>${this._L("settings_comfort_hysteresis")}</label>
            <input type="number" step="0.1" min="0.1" max="5" value="${this._num(s.comfort_hysteresis, 1)}" data-settings-field="comfort_hysteresis">
            ${hint(this._t("settings_comfort_hysteresis_hint"))}
          </div>
          ${this._renderHystExplain("comfort")}
          <div class="form-group" style="margin-top:16px">
            <label>${this._t("settings_temp_color")}</label>
            <input type="hidden" data-settings-field="temp_color_mode" value="${s.temp_color_thermometer === true ? "thermometer" : "action"}" data-initial="${s.temp_color_thermometer === true ? "thermometer" : "action"}">
            <div class="radio-group">${["action", "thermometer"].map(v => `<label class="radio-row">
              <input type="radio" name="temp_color_mode" value="${v}" data-settings-radio="temp_color_mode" ${(s.temp_color_thermometer === true ? "thermometer" : "action") === v ? "checked" : ""}>
              <span><b>${this._esc(this._t("settings_temp_color_" + v))}</b><br><span class="radio-hint">${this._esc(this._t("settings_temp_color_" + v + "_hint"))}</span></span>
            </label>`).join("")}</div>
          </div>`,
        })}
        ${this._optBox({
          title: this._t("settings_outdoor_box_title"),
          dep: '[data-settings-field="outdoor_temp_sensor"]', mode: "value",
          head: `<div class="form-group">
            <label>${this._t("settings_outdoor_temp")}</label>
            ${this._renderEntitySelect("outdoor_temp_sensor", s.outdoor_temp_sensor, "sensor", "temperature")}
            ${this._renderSensorValue(s.outdoor_temp_sensor, "\u00B0")}
            ${hint(this._t("settings_outdoor_temp_hint"))}
          </div>`,
          offNote: this._t("settings_outdoor_off_note"),
          body: `<div class="form-group">
            <label>${this._L("settings_threshold_hysteresis")}</label>
            <input type="number" step="0.1" min="0" max="5" value="${this._num(s.threshold_hysteresis, 0.5)}" data-settings-field="threshold_hysteresis">
            ${hint(this._t("settings_threshold_hysteresis_hint"))}
          </div>
          ${this._renderHystExplain("rules")}`,
        })}
        ${this._optBox({
          title: this._t("settings_other_sensors_title"),
          body: `<div class="form-row">
            <div class="form-group">
              <label>${this._t("settings_weather")}</label>
              ${this._renderEntitySelect("weather_entity", s.weather_entity, "weather", null)}
              ${this._renderSensorValue(s.weather_entity)}
              ${hint(this._t("settings_weather_hint"))}
            </div>
            <div class="form-group">
              <label>${this._t("settings_workday_sensor")}</label>
              ${this._renderEntitySelect("workday_sensor", s.workday_sensor, "binary_sensor", null)}
              ${this._renderSensorValue(s.workday_sensor)}
              ${hint(this._t("settings_workday_hint"))}
            </div>
          </div>`,
        })}
      </div>
    </div>`;
    }

    // Wind section
    if (active === "wind") {
      const windSt = s.wind_sensor && this._hass?.states ? this._hass.states[s.wind_sensor] : null;
      const windUnit = (windSt && windSt.attributes.unit_of_measurement) || "";
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("wind")} ${this._t("settings_section_wind")}</div>
      <div class="card-body">
        ${hintIntro(this._t("settings_wind_hint"))}
        ${this._optBox({
          dep: '[data-settings-field="wind_sensor"]', mode: "value",
          head: `<div class="form-group">
          <label>${this._t("settings_wind_sensor")}</label>
          ${this._renderEntitySelect("wind_sensor", s.wind_sensor, "sensor", "wind_speed")}
          ${this._renderSensorValue(s.wind_sensor)}
        </div>`,
          offNote: this._t("settings_wind_off_note"),
          body: `<div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_wind_threshold")}${windUnit ? " (" + this._esc(windUnit) + ")" : ""}</label>
            <input type="number" step="1" min="0" value="${this._num(s.wind_speed_threshold, 0)}" data-settings-field="wind_speed_threshold">
          </div>
          <div class="form-group">
            <label>${this._L("settings_wind_hysteresis")} (${this._esc(windUnit || this._t("unit_sensor"))})</label>
            <input type="number" step="1" min="0" value="${this._num(s.wind_speed_hysteresis, 0)}" data-settings-field="wind_speed_hysteresis">
            ${hint(this._t("settings_wind_hysteresis_hint"))}
          </div>
        </div>
        <div class="form-group">
          <label>${this._t("settings_wind_position")}</label>
          <input type="number" step="1" min="0" max="100" value="${this._num(s.wind_position, 100)}" data-settings-field="wind_position">
          ${hint(this._t("settings_wind_position_hint"))}
        </div>
        ${this._renderHystExplain("wind")}`,
        })}
      </div>
    </div>`;
    }

    // Solar cards (shown in the comfort & sun tab)
    if (active === "comfort") {
      const mode = this._sunComfortMode(s.sun_neutral_ignore !== false, s.preemptive_shading !== false);
      // Values actually used by the engine: a readable entity wins over the number
      const cmin = this._effectiveThreshold(s.comfort_temp_min_entity, this._num(s.comfort_temp_min, 21));
      const cmax = this._effectiveThreshold(s.comfort_temp_max_entity, this._num(s.comfort_temp_max, 25));
      const radio = (value) => `<label class="radio-row">
          <input type="radio" name="sun_comfort_mode" value="${value}" data-settings-radio="sun_comfort_mode" ${mode === value ? "checked" : ""}>
          <span><b>${this._esc(this._t("sun_comfort_" + value))}</b><br><span class="radio-hint">${this._esc(this._t("sun_comfort_" + value + "_hint"))}</span></span>
        </label>`;
      const used = this._coversUsingRadiation();
      const solarSt = s.solar_sensor && this._hass?.states ? this._hass.states[s.solar_sensor] : null;
      const solarUnit = (solarSt && solarSt.attributes.unit_of_measurement) || "";
      // Sunshine sensor, nested under the option that uses it. Enabled when
      // the global choice is "strong sunshine" or a cover uses it on its own.
      const solarInner = this._optBox({
          cls: "opt-box-flat",
          dep: '[data-settings-field="solar_sensor"]', mode: "value",
          head: `${hintIntro(this._esc(this._t("settings_solar_hint")))}
          <div class="settings-hint" style="margin-bottom:12px">${this._esc(used
            ? this._t("solar_used_by").replace("{n}", used)
            : this._t("solar_unused"))}</div>
          <div class="form-group">
            <label>${this._t("settings_solar_sensor")}</label>
            ${this._renderEntitySelect("solar_sensor", s.solar_sensor, "sensor")}
            ${this._renderSensorValue(s.solar_sensor)}
          </div>`,
          offNote: this._t("settings_solar_off_note"),
          body: `<div class="form-row">
            <div class="form-group">
              <label>${this._L("settings_solar_threshold")}${solarUnit ? " (" + this._esc(solarUnit) + ")" : ""}</label>
              <input type="number" step="100" min="0" value="${this._num(s.solar_threshold, 0)}" data-settings-field="solar_threshold">
              ${hint(this._t("settings_solar_threshold_hint"))}
              ${this._renderThresholdEntity('data-settings-field="solar_threshold_entity"', s.solar_threshold_entity)}
            </div>
            <div class="form-group">
              <label>${this._L("settings_solar_hysteresis")} (${this._esc(solarUnit || this._t("unit_sensor"))})</label>
              <input type="number" step="100" min="0" value="${this._num(s.solar_hysteresis, 0)}" data-settings-field="solar_hysteresis">
              ${hint(this._t("settings_solar_hysteresis_hint"))}
            </div>
          </div>
          ${this._renderHystExplain("solar")}`,
        });
      const solarBox = this._optBox({
        cls: "opt-box-nested",
        title: this._t("settings_section_solar"),
        dep: '[data-settings-field="sun_comfort_mode"]', mode: "equals", value: "preemptive", force: used > 0,
        offNote: this._t("settings_solar_nested_off"),
        body: solarInner,
      });
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("sun", 18)} ${this._t("settings_section_comfort")}</div>
      <div class="card-body">
        <div class="opt-box">
        <div class="opt-box-title">${this._L("settings_sun_facade_title")}</div>
        <div class="settings-hint" style="margin-bottom:10px"><b>${this._esc(this._t("settings_indoor_reminder")
          .replace("{name}", s.indoor_temp_sensor ? this._haEntityName(s.indoor_temp_sensor) : this._t("settings_indoor_none"))
          .replace("{min}", cmin).replace("{max}", cmax))}</b></div>
        ${hintIntro(this._esc(this._t("settings_sun_facade_hint")))}
        <div class="form-group">
          <label class="checkbox-row">
            <input type="checkbox" data-settings-field="sun_heating_ignore" ${s.sun_heating_ignore !== false ? "checked" : ""}>
            <span>${this._L("sun_heating_label")} <span class="radio-hint">(${this._esc(this._t("sun_below").replace("{t}", cmin))})</span></span>
          </label>
          ${hint(this._esc(this._t("sun_heating_hint")))}
        </div>
        <div class="form-group">
          <label>${this._L("sun_comfort_label")} <span class="radio-hint">(${this._esc(this._t("sun_between").replace("{min}", cmin).replace("{max}", cmax))})</span></label>
          <input type="hidden" data-settings-field="sun_comfort_mode" value="${mode}" data-initial="${mode}">
          <div class="radio-group">${radio("position")}${radio("ignore")}${radio("preemptive")}</div>
          ${solarBox}
        </div>
        <div class="settings-hint">${this._esc(this._t("sun_hot_note").replace("{t}", cmax))}</div>
        ${this._renderSunExplain(cmin, cmax)}
        </div>

      </div>
    </div>`;
    }

    // Automation section
    if (active === "automation") {
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("cog")} ${this._t("settings_section_automation")}</div>
      <div class="card-body">
        <div class="opt-box">
        <div class="opt-box-title">${this._esc(this._t("settings_auto_box_pause"))}</div>
        <div class="form-group">
          <label>${this._t("settings_pause_duration")}</label>
          <input type="number" min="1" max="480" value="${this._num(s.pause_duration, 10)}" data-settings-field="pause_duration">
          ${hint(this._t("settings_pause_duration_hint"))}
        </div>
        <div class="form-group">
          <label class="checkbox-row">
            <input type="checkbox" data-settings-field="pause_resume_on_match" ${s.pause_resume_on_match !== false ? "checked" : ""}>
            <span>${this._t("pause_resume_on_match")}</span>
          </label>
          ${hint(this._t("pause_resume_on_match_hint"))}
        </div>
        </div>
        <div class="opt-box">
        <div class="opt-box-title">${this._esc(this._t("settings_auto_box_window"))}</div>
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_lock_position")}</label>
            <input type="number" min="0" max="100" value="${this._num(s.lock_position, 100)}" data-settings-field="lock_position">
            ${hint(this._t("settings_lock_position_hint"))}
          </div>
          <div class="form-group">
            <label>${this._t("settings_vent_position")}</label>
            <input type="number" min="0" max="100" value="${this._num(s.vent_position, 30)}" data-settings-field="vent_position">
            ${hint(this._t("settings_vent_position_hint"))}
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_lock_tilt_position")}</label>
            <input type="number" min="0" max="100" value="${this._num(s.lock_tilt_position, "")}" data-settings-field="lock_tilt_position">
            ${hint(this._t("settings_lock_tilt_position_hint"))}
          </div>
          <div class="form-group">
            <label>${this._t("settings_vent_tilt_position")}</label>
            <input type="number" min="0" max="100" value="${this._num(s.vent_tilt_position, "")}" data-settings-field="vent_tilt_position">
            ${hint(this._t("settings_vent_tilt_position_hint"))}
          </div>
        </div>
        </div>
        <div class="opt-box">
        <div class="opt-box-title">${this._esc(this._t("settings_auto_box_moves"))}</div>
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_min_position_change")}</label>
            <input type="number" min="1" max="50" value="${this._num(s.min_position_change, 5)}" data-settings-field="min_position_change">
            ${hint(this._t("settings_min_position_change_hint"))}
          </div>
          <div class="form-group">
            <label>${this._t("settings_min_time")}</label>
            <input type="number" min="60" max="3600" value="${this._num(s.min_time_between_changes, 300)}" data-settings-field="min_time_between_changes">
            ${hint(this._t("settings_min_time_hint"))}
          </div>
        </div>
        <div class="form-group">
          <label>${this._t("settings_command_stagger")}</label>
          <input type="number" step="0.1" min="0" max="2" value="${this._num(s.command_stagger, 0)}" data-settings-field="command_stagger">
          ${hint(this._t("settings_command_stagger_hint"))}
        </div>
        <div class="form-group">
          <label>${this._t("settings_default_travel_time")}</label>
          <input type="number" min="1" max="300" step="1" value="${this._num(s.default_travel_time, "")}" placeholder="${this._esc(this._t("settings_default_travel_time_placeholder"))}" data-settings-field="default_travel_time">
          ${hint(this._t("settings_default_travel_time_hint"))}
        </div>
        </div>
        <div class="opt-box">
        <div class="opt-box-title">${this._esc(this._t("settings_auto_box_misc"))}</div>
        <div class="form-group">
          <label class="checkbox-row">
            <input type="checkbox" data-settings-field="logbook_enabled" ${s.logbook_enabled !== false ? "checked" : ""}>
            <span>${this._t("settings_logbook_enabled")}</span>
          </label>
          ${hint(this._t("settings_logbook_enabled_hint"))}
        </div>
        <div class="form-group">
          <label class="checkbox-row">
            <input type="checkbox" data-settings-field="update_check_enabled" ${s.update_check_enabled !== false ? "checked" : ""}>
            <span>${this._t("settings_update_check_enabled")}</span>
          </label>
          ${hint(this._t("settings_update_check_enabled_hint"))}
        </div>
        </div>
      </div>
    </div>`;
    }

    // Save bar - for all sections except backup
    if (active !== "backup") {
      html += `<div class="settings-save-bar">
      <button class="btn btn-primary" data-action="settings-save">${this._t("save")}</button>
    </div>`;
    }

    // Backup section
    if (active === "backup") {
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("archive")} ${this._t("settings_section_backup")}</div>
      <div class="card-body">
        ${hintIntro(this._t("settings_backup_hint"))}
        ${this._settingsDirty() ? `<div class="settings-unsaved-warning">${this._lucideIcon("info", 16)} ${this._esc(this._t("settings_unsaved_warning"))}
          <button class="btn btn-primary" data-action="settings-save">${this._t("save")}</button></div>` : ""}
        <div class="settings-backup-actions">
          <button class="btn" data-action="backup-export">${this._t("settings_export")}</button>
          <button class="btn" data-action="backup-import">${this._t("settings_import")}</button>
          <input type="file" accept=".json" data-action="backup-file" hidden>
        </div>
      </div>
    </div>`;
    }

    html += '</div></div></div>'; // close settings-stack, settings-content, settings-shell
    return html;
  }

  _renderLog() {
    // Filter on a cover that no longer exists: back to all covers
    if (this._logCover && this._config && !(this._config.covers || {})[this._logCover]) {
      this._logCover = null;
      this._logEntries = null;
    }
    if (this._logEntries === null) {
      this._loadLog();
      return '<div class="state-msg"><div class="spinner"></div><div>' + this._t("log_loading") + '</div></div>';
    }

    let html = '';

    // Filter buttons
    const filters = [null, "position", "status", "rule", "wind"];
    html += '<div class="log-filter-bar">';
    for (const f of filters) {
      const active = this._logFilter === f ? " active" : "";
      const label = f ? this._t("log_type_" + f) : this._t("log_filter_all");
      html += '<button class="btn btn-sm' + active + '" data-action="log-filter" data-filter="' + (f || '') + '">' + label + '</button>';
    }
    html += '<button class="btn btn-sm btn-danger" data-action="log-clear">' + this._t("log_clear") + '</button>';
    html += '</div>';

    // Cover filter: all covers, or one (its entries + global events such as wind)
    const covers = Object.values(this._config?.covers || {})
      .sort((a, b) => String(a.name || a.entity_id).localeCompare(String(b.name || b.entity_id), this._hass?.language || undefined));
    html += '<div class="log-cover-filter"><label for="log-cover-select">' + this._esc(this._t("log_filter_cover")) + '</label>'
      + '<select id="log-cover-select" data-action="log-cover">'
      + '<option value=""' + (this._logCover ? '' : ' selected') + '>' + this._esc(this._t("log_filter_all_covers")) + '</option>'
      + covers.map(c => '<option value="' + this._esc(c.entity_id) + '"' + (this._logCover === c.entity_id ? ' selected' : '') + '>'
        + this._esc(c.name || c.entity_id) + '</option>').join('')
      + '</select>'
      + (this._logCover ? '<span class="log-cover-note">' + this._esc(this._t("log_filter_cover_note")) + '</span>' : '')
      + '</div>';

    let entries = this._logEntries;
    if (this._logFilter) {
      entries = entries.filter(e => e.type === this._logFilter);
    }

    if (entries.length === 0) {
      return html + '<div class="empty-state">' + this._t("log_empty") + '</div>';
    }

    html += '<div class="card"><div class="table-scroll"><table class="data-table">';
    html += '<thead><tr>';
    html += '<th>' + this._t("log_time") + '</th>';
    html += '<th>' + this._t("log_event") + '</th>';
    html += '<th>' + this._t("log_cover") + '</th>';
    html += '<th>' + this._t("log_message") + '</th>';
    html += '</tr></thead><tbody>';

    for (const e of entries) {
      const time = new Date(e.ts * 1000).toLocaleString(this._hass?.language || undefined);
      const typeLabel = this._t("log_type_" + e.type) || e.type;
      const coverName = e.entity_id ? this._getCoverName(e.entity_id) : "–";
      const typeClass = e.type === "wind" ? "status-wind_protected" : e.type === "status" ? "status-paused" : "";
      html += '<tr>';
      html += '<td class="nowrap">' + this._esc(time) + '</td>';
      html += '<td><span class="status-badge ' + typeClass + '">' + this._esc(typeLabel) + '</span></td>';
      html += '<td>' + this._esc(coverName) + '</td>';
      html += '<td>' + this._esc(this._formatLogMessage(e)) + '</td>';
      html += '</tr>';
    }
    html += '</tbody></table></div></div>';
    return html;
  }

  // Localize an activity log entry from its structured data. Entries written
  // by versions before 1.63.0 have no data.key and keep their English text.
  _formatLogMessage(e) {
    const d = e && e.data;
    const key = d && d.key;
    if (!key) return e.message || "";
    const template = this._t("log_msg_" + key);
    if (template === "log_msg_" + key) return e.message || "";
    const status = (v) => {
      const t = this._t("status_" + v);
      return t !== "status_" + v ? t : String(v);
    };
    const values = { ...d };
    if (key === "status_change") {
      values.from = status(d.from);
      values.to = status(d.to);
    }
    if (key === "safety_takeover" || key === "safety_release" || key === "sensor_unavailable") {
      if (d.status) values.status = status(d.status);
    }
    if (Array.isArray(d.sensor)) values.sensor = d.sensor.join(", ");
    if (key === "rule" || key === "safety_takeover" || key === "safety_release") {
      const rule = this._config?.rules?.[d.rule_id];
      values.rule = rule ? rule.name : (d.rule_name || d.rule_id || "");
    }
    return template.replace(/\{(\w+)\}/g, (m, name) => (values[name] != null ? String(values[name]) : m));
  }

  async _loadLog() {
    const cover = this._logCover || null;
    // Same request already in flight: repeated renders don't refire it
    if (this._logLoading && this._logLoadingCover === cover) return;
    const seq = (this._logSeq = (this._logSeq || 0) + 1);
    this._logLoading = true;
    this._logLoadingCover = cover;
    let entries;
    try {
      const msg = cover
        ? { entity_id: cover, include_global: true, limit: 1000 }
        : {};
      const result = await this._ws("cover_automatic/log", msg);
      entries = result.entries || [];
    } catch (e) {
      entries = [];
    }
    // Stale response (filter changed, log cleared or newer request): drop it
    if (seq !== this._logSeq) return;
    this._logLoading = false;
    this._logLoadingCover = undefined;
    if ((this._logCover || null) !== cover) return;
    this._logEntries = entries;
    this._render();
  }

  _updateLiveCells() {
    const root = this.shadowRoot;
    if (!root || !this._config) return;
    const covers = this._config.covers || {};
    const liveCvrs = this._config.live_covers || {};
    for (const eid of Object.keys(covers)) {
      // Combined position cell: current + target with optional divergence marker, plus hysteresis badge
      const haState = this._hass?.states ? this._hass.states[eid] : null;
      const live = liveCvrs[eid] || {};
      const tgtPos = live.target_position;
      const hyst = live.hysteresis;
      const posCell = root.querySelector('[data-live-position="' + CSS.escape(eid) + '"]');
      if (posCell) {
        let barHtml = this._posCellHtml(covers[eid], haState, tgtPos);
        if (hyst === "position" || hyst === "time") {
          barHtml += ' <span class="status-badge status-paused hysteresis-badge" title="' + this._esc(this._t(hyst === "position" ? "cover_hysteresis_position" : "cover_hysteresis_time")) + '">' + (hyst === "position" ? "\u2195" : "\u23F2") + '</span>';
        }
        posCell.innerHTML = barHtml;
      }
      // Status + pause remaining + resume button
      const c = covers[eid];
      const sCell = root.querySelector('[data-live-status="' + CSS.escape(eid) + '"]');
      if (sCell && c) {
        const st = c.status || "auto";
        const badge = sCell.querySelector(".status-badge");
        if (badge) {
          badge.className = "status-badge status-" + st;
          badge.textContent = this._t("status_" + st) || st;
        }
        let pauseSpan = sCell.querySelector(".pause-remaining");
        let resumeBtn = sCell.querySelector(".resume-x");
        if (st === "paused") {
          if (live.pause_until) {
            const txt = this._formatPauseRemaining(live.pause_until);
            if (txt) {
              if (!pauseSpan) {
                pauseSpan = document.createElement("span");
                pauseSpan.className = "pause-remaining";
                sCell.appendChild(pauseSpan);
              }
              pauseSpan.textContent = txt;
            } else if (pauseSpan) {
              pauseSpan.remove();
            }
          }
          if (!resumeBtn) {
            resumeBtn = document.createElement("button");
            resumeBtn.className = "btn-icon resume-x";
            resumeBtn.dataset.action = "cover-resume";
            resumeBtn.dataset.id = eid;
            resumeBtn.title = this._t("cover_resume");
            resumeBtn.textContent = "\u2715";
            sCell.appendChild(resumeBtn);
          }
        } else {
          if (pauseSpan) pauseSpan.remove();
          if (resumeBtn) resumeBtn.remove();
        }
      }
      // Cover name
      const nCell = root.querySelector('[data-live-name="' + CSS.escape(eid) + '"]');
      if (nCell && c) {
        nCell.textContent = c.name;
      }
      // Facade name + sun icon
      const fCell = root.querySelector('[data-live-facade="' + CSS.escape(eid) + '"]');
      if (fCell && c) {
        const facadeName = this._getFacadeName(c.facade_id);
        const liveFacade = c.facade_id ? ((this._config.live_facades || {})[c.facade_id] || {}) : {};
        fCell.textContent = "";
        fCell.appendChild(document.createTextNode(facadeName));
        if (liveFacade.sun_on_facade) {
          const sun = document.createElement("span");
          sun.className = "live-icon-sun";
          sun.title = this._t("facade_sun_active");
          // SVG from internal _sunIconSvg() - no user input
          sun.innerHTML = this._sunIconSvg(12);
          fCell.appendChild(document.createTextNode(" "));
          fCell.appendChild(sun);
        }
      }
      // Rule name -- preserve clickable rule-link markup via DOM API (avoids innerHTML)
      const rCell = root.querySelector('[data-live-rule="' + CSS.escape(eid) + '"]');
      if (rCell) {
        rCell.textContent = "";
        const ruleId = live.rule_id;
        const ruleName = live.rule_name || this._t("cover_no_rule");
        if (ruleId && this._config && this._config.rules && this._config.rules[ruleId]) {
          const a = document.createElement("a");
          a.className = "rule-link";
          a.dataset.action = "goto-rule";
          a.dataset.ruleId = ruleId;
          a.title = this._t("cover_goto_rule");
          a.textContent = ruleName;
          rCell.appendChild(a);
        } else {
          rCell.textContent = ruleName;
        }
      }
      // Temperature with comfort color
      const tempCell = root.querySelector('[data-live-temp="' + CSS.escape(eid) + '"]');
      if (tempCell) {
        const c2 = covers[eid];
        const ts = (c2 && c2.indoor_temp_sensor) || ((this._config.settings || {}).indoor_temp_sensor);
        const tst = ts && this._hass?.states ? this._hass.states[ts] : null;
        const tv = tst && tst.state !== "unavailable" && tst.state !== "unknown" ? parseFloat(tst.state) : null;
        const tp = this._tempCellParts(live.comfort_mode, tv);
        if (tempCell.innerHTML !== tp.html) tempCell.innerHTML = tp.html;
        tempCell.style.color = tp.color;
        tempCell.classList.toggle("temp-mode", !!tp.color);
        tempCell.title = tp.title;
      }
      // Last change
      const lcCell = root.querySelector('[data-live-lastchange="' + CSS.escape(eid) + '"]');
      if (lcCell) lcCell.textContent = live.last_change ? this._formatTimeAgo(live.last_change) : "";
    }
  }

  _formatTimeAgo(ts) {
    const sec = Math.max(0, Math.round(Date.now() / 1000 - ts));
    if (sec < 60) return this._t("cover_just_now");
    const min = Math.floor(sec / 60);
    if (min < 60) return this._t("time_ago_min").replace("{n}", min);
    const h = Math.floor(min / 60);
    const m = min % 60;
    if (m === 0) return this._t("time_ago_h").replace("{n}", h);
    return this._t("time_ago_h_m").replace("{h}", h).replace("{m}", m);
  }

  _formatPauseRemaining(pauseUntil) {
    const remaining = Math.max(0, Math.round(pauseUntil - Date.now() / 1000));
    if (remaining <= 0) return "";
    const min = Math.floor(remaining / 60);
    const sec = remaining % 60;
    return "(" + min + ":" + (sec < 10 ? "0" : "") + sec + ")";
  }

  _startLiveRefresh() {
    this._stopLiveRefresh();
    this._refreshLiveCovers();
    this._liveRefreshTimer = setInterval(() => this._refreshLiveCovers(), 60000);
  }

  _stopLiveRefresh() {
    if (this._liveRefreshTimer) {
      clearInterval(this._liveRefreshTimer);
      this._liveRefreshTimer = null;
    }
  }

  async _refreshLiveCovers() {
    if (!this._config || this._activeTab !== "covers") {
      this._stopLiveRefresh();
      return;
    }
    // Drop stale answers: a newer refresh was started, or the config was
    // replaced (save, import...) while this request was running.
    const seq = this._liveSeq = (this._liveSeq || 0) + 1;
    const epoch = this._cfgEpoch || 0;
    try {
      const result = await this._ws("cover_automatic/config");
      if (seq !== this._liveSeq || epoch !== (this._cfgEpoch || 0) || !this._config) return;
      if (result) {
        if (result.live_covers) this._config.live_covers = result.live_covers;
        if (result.live_facades) this._config.live_facades = result.live_facades;
        if (result.active_rules) this._config.active_rules = result.active_rules;
        if (result.covers) this._config.covers = result.covers;
        this._updateLiveCells();
      }
    } catch (e) { /* silent */ }
  }

  /* ---------- Rule editor: live condition preview ---------- */
  _startCondPreview() {
    this._stopCondPreview();
    this._refreshCondPreview();
    this._condPreviewTimer = setInterval(() => this._refreshCondPreview(), 10000);
  }

  _stopCondPreview() {
    if (this._condPreviewTimer) {
      clearInterval(this._condPreviewTimer);
      this._condPreviewTimer = null;
    }
  }

  async _refreshCondPreview() {
    if (!this._config || this._activeTab !== "rules" || !this._expandedRule) {
      this._stopCondPreview();
      return;
    }
    const ruleId = this._expandedRule;
    const rule0 = this._edRule(ruleId);
    if (!rule0 || !rule0.conditions || rule0.conditions.length === 0) return;
    const conditions = rule0.conditions.map(c => ({ type: c.type, params: c.params || {}, group: parseInt(c.group, 10) || 0, negate: !!c.negate }));
    // Only the latest request may paint (responses can arrive out of order,
    // and structural changes bump the sequence to void older ones).
    const seq = ++this._previewSeq;
    let result;
    try {
      result = await this._ws("cover_automatic/rule/preview_conditions", { conditions });
    } catch (e) { return; }
    if (seq !== this._previewSeq) return;
    // The editor may have collapsed or switched tabs during the await.
    if (!result || !Array.isArray(result.results) || this._activeTab !== "rules" || this._expandedRule !== ruleId) return;
    // Re-read the rule: its conditions may have changed meanwhile.
    const rule = this._edRule(ruleId);
    if (!rule || !rule.conditions || rule.conditions.length !== result.results.length
      || rule.conditions.some((c, i) => c.type !== conditions[i].type)) return;
    const root = this.shadowRoot;
    if (!root) return;
    result.results.forEach((res, idx) => {
      const el = root.querySelector('.cond-preview[data-cond-preview="' + idx + '"]');
      if (el) this._applyCondPreview(el, res);
    });
    // Group results (only when every condition of the group is evaluable)
    const { ops } = this._ruleGroups(rule);
    root.querySelectorAll(".cond-group-preview[data-group-preview]").forEach(el => {
      const g = parseInt(el.dataset.groupPreview, 10);
      const res = result.results.filter((_, i) => (parseInt(rule.conditions[i]?.group, 10) || 0) === g);
      if (!res.length || res.some(r => !r || r.evaluable === false)) { el.className = "cond-preview cond-group-preview"; el.textContent = ""; return; }
      const matched = ops[g] === "or" ? res.some(r => r.matched) : res.every(r => r.matched);
      this._applyCondPreview(el, { evaluable: true, matched, actual: null });
      el.classList.add("cond-group-preview");
    });
  }

  _applyCondPreview(el, res) {
    if (!res || res.evaluable === false) {
      el.className = "cond-preview cond-preview-context";
      el.textContent = this._t("cond_preview_context");
      return;
    }
    const matched = !!res.matched;
    el.className = "cond-preview " + (matched ? "cond-preview-on" : "cond-preview-off");
    const label = this._t(matched ? "cond_preview_active" : "cond_preview_inactive");
    const actual = this._formatCondActual(res);
    // DOM API (not innerHTML) to satisfy the security hook on live updates.
    el.textContent = "";
    const dot = document.createElement("span");
    dot.className = "cond-preview-dot";
    el.appendChild(dot);
    const txt = document.createElement("span");
    txt.textContent = actual ? (label + " · " + actual) : label;
    el.appendChild(txt);
  }

  _formatCondActual(res) {
    const v = res.actual;
    if (v == null) return "";
    switch (res.kind) {
      case "temp": return v + " °C";
      case "elevation": return v + "°";
      case "weather": return this._i18nOr("weather_" + String(v).replace(/-/g, "_"), String(v));
      case "day": return this._i18nOr("day_" + v, String(v));
      case "workday": return this._i18nOr("opt_" + v, String(v));
      case "ha_reading": {
        const stateObj = this._hass?.states ? this._hass.states[v.entity_id] : null;
        return this._haStateLabel(stateObj, v.attribute, v.value);
      }
      default: return String(v);
    }
  }

  // Display label for a multiselect option; the stored value stays raw.
  _optionLabel(paramKey, opt) {
    if (paramKey === "weather") {
      return this._i18nOr("weather_" + String(opt).replace(/-/g, "_"), String(opt));
    }
    return this._i18nOr("opt_" + opt, String(opt));
  }

  _i18nOr(key, fallback) {
    const t = this._t(key);
    return (t && t !== key) ? t : fallback;
  }

  _getCoverName(entityId) {
    const covers = this._config ? (this._config.covers || {}) : {};
    const cover = covers[entityId];
    return cover ? cover.name : entityId;
  }

  /* ============================================================
   * Helpers
   * ============================================================ */
  _getActiveScenario() {
    if (!this._config) return null;
    const id = (this._config.settings || {}).active_scenario || this._config.active_scenario;
    return id ? (this._config.scenarios || {})[id] || null : null;
  }

  _getFacadeName(facadeId) {
    if (!facadeId || !this._config) return "-";
    const f = (this._config.facades || {})[facadeId];
    return f ? f.name : "-";
  }

  _getFacadeCovers(facadeId) {
    if (!this._config) return [];
    const covers = this._config.covers || {};
    return Object.values(covers).filter(c => c.facade_id === facadeId);
  }

  _esc(str) {
    if (str == null) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  // Coerce a stored numeric field for safe HTML-attribute interpolation.
  // Returns a finite number, otherwise the fallback (empty string by default).
  // Defense-in-depth against hand-edited .storage files (WS schema already
  // enforces numerics on write).
  _num(v, fallback = "") {
    if (v === null || v === undefined || v === "") return fallback;
    const n = Number(v);
    return Number.isFinite(n) ? n : fallback;
  }

  /* ============================================================
   * Event delegation (bound once, routes all events)
   * ============================================================ */
  _setupDelegation() {
    if (this._delegationBound) return;
    this._delegationBound = true;
    const root = this.shadowRoot;

    root.addEventListener("click", (e) => this._handleClick(e));
    root.addEventListener("change", (e) => { this._handleChange(e); this._refreshDeps(); });
    root.addEventListener("input", (e) => { this._handleInput(e); this._refreshDeps(); });
    root.addEventListener("dragstart", (e) => this._handleDragStart(e));
    root.addEventListener("dragend", (e) => this._handleDragEnd(e));
    root.addEventListener("dragover", (e) => this._handleDragOver(e));
    root.addEventListener("dragleave", (e) => this._handleDragLeave(e));
    root.addEventListener("drop", (e) => this._handleDrop(e));
    root.addEventListener("pointerdown", (e) => this._handleHouseDragStart(e));
    root.addEventListener("focusout", (e) => this._onSlideFocusOut(e));
    // Enter/Space activate non-native interactive elements (rows, sort headers)
    root.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      const el = e.composedPath()[0];
      if (!el || !el.closest) return;
      const target = el.closest('[data-action][tabindex]');
      if (!target || ["BUTTON", "A", "INPUT", "SELECT", "TEXTAREA", "SUMMARY"].includes(el.tagName)) return;
      e.preventDefault();
      target.click();
    });
  }

  /* ---------- Keyboard (window-level) ---------- */
  _handleKeyDown(e) {
    if (e.key !== "Escape") return;
    if (this._confirmCallback) {
      e.stopPropagation();
      this._hideConfirm();
      return;
    }
    if (this._slideOpen) {
      e.stopPropagation();
      this._slideOpen = false;
      this._render();
    }
  }

  /* ---------- Click delegation ---------- */
  _handleClick(e) {
    // Remember the last clicked control of the slide-out (focus is restored
    // to it after a rebuild; iOS does not focus clicked buttons).
    const clicked = e.target && e.target.closest ? e.target.closest("[data-action], input, select, button") : null;
    if (clicked && clicked.closest(".slide-panel")) {
      const key = this._slideElKey(clicked);
      this._slideClick = key ? { key, t: Date.now() } : null;
    }
    // Tab clicks
    const tabBtn = e.target.closest("[data-tab]");
    if (tabBtn) {
      const tab = tabBtn.dataset.tab;
      this._confirmLeaveRule(() => this._confirmLeaveSettings(() => this._switchTab(tab)));
      return;
    }
    this._handleActionClick(e);
  }

  _switchTab(tab) {
    this._activeTab = tab;
    this._selectedCover = null;
    this._slideOpen = false;
    this._setExpandedRule(null);
    this._settingsDraft = null;
    this._editingFacade = null;
    this._addingCover = false;
    this._addingFacade = false;
    this._addingRule = false;
    this._addingScenario = false;
    this._editingScenario = null;
    this._logEntries = null;
    if (this._activeTab === "covers") {
      this._startLiveRefresh();
    } else {
      this._stopLiveRefresh();
    }
    this._stopCondPreview();
    this._render();
  }

  _handleActionClick(e) {
    // Route by data-action
    const actionEl = e.target.closest("[data-action]");
    if (!actionEl) return;
    const action = actionEl.dataset.action;

    switch (action) {
      case "toggle-menu":
        // Standard HA event (like ha-menu-button): opens the sidebar/drawer
        // without navigating away (unsaved drafts stay).
        this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
        break;
      case "retry": this._loadConfig(); break;
      case "explain-toggle": {
        const d = actionEl.closest("details");
        this._explainOpen = this._explainOpen || {};
        this._explainOpen[actionEl.dataset.key] = d ? !d.open : false;
        break;
      }
      case "sun-explain-toggle": {
        // Native <details> toggles after the click: remember the new state
        const d = actionEl.closest("details");
        this._sunExplainOpen = d ? !d.open : false;
        break;
      }
      case "cover-add-start": this._addingCover = true; this._render(); break;
      case "cover-sort": {
        const key = actionEl.dataset.sort;
        if (this._coverSort.key === key) {
          this._coverSort.dir = this._coverSort.dir === "asc" ? "desc" : "asc";
        } else {
          this._coverSort = { key, dir: "asc" };
        }
        this._render();
        break;
      }
      case "cover-add-cancel": this._addingCover = false; this._render(); break;
      case "cover-add": this._onCoverAdd(); break;
      case "cover-resume": this._onCoverResume(actionEl.dataset.id); break;
      case "cover-delete": this._onCoverDelete(actionEl.dataset.id); break;
      case "select-cover":
        this._selectedCover = actionEl.dataset.id;
        this._slideOpen = true;
        this._expandedSections = { base: true };
        this._render();
        // Move focus into the slide-out so Tab order continues inside the dialog
        setTimeout(() => this.shadowRoot.querySelector(".slide-header .btn-icon")?.focus(), 0);
        break;
      case "goto-rule": {
        e.preventDefault();
        e.stopPropagation();
        const ruleId = actionEl.dataset.ruleId;
        this._activeTab = "rules";
        this._slideOpen = false;
        this._selectedCover = null;
        this._setExpandedRule(null);
        this._stopLiveRefresh();
        this._render();
        this._highlightRule(ruleId);
        break;
      }
      case "close-slide":
        if (e.target === actionEl || actionEl.classList.contains("btn-icon")) {
          this._slideOpen = false;
          this._render();
        }
        break;
      case "toggle-section":
        {
          // Accordion: opening a section closes the others -- unless
          // several are open ("expand all"): then only this one toggles.
          const id = actionEl.dataset.section;
          const open = !this._expandedSections[id];
          const openCount = Object.values(this._expandedSections).filter(Boolean).length;
          if (openCount > 1) this._expandedSections = { ...this._expandedSections, [id]: open };
          else this._expandedSections = { [id]: open };
        }
        this._render();
        break;
      case "settings-section":
        // _render() keeps the unsaved inputs of the section left (settings draft)
        this._captureSettingsDraft();
        this._activeSettingsSection = actionEl.dataset.section;
        this._render();
        break;
      case "rotate-by": {
        const input = this.shadowRoot.querySelector("#house-rotation-input");
        if (!input) break;
        const setRaw = actionEl.dataset.set;
        if (setRaw !== undefined) {
          input.value = parseFloat(setRaw);
        } else {
          const cur = parseFloat(input.value);
          const base = Number.isFinite(cur) ? cur : 0;
          const delta = parseFloat(actionEl.dataset.delta || "0");
          let next = base + delta;
          // Normalize into -180..180
          while (next > 180) next -= 360;
          while (next < -180) next += 360;
          input.value = next;
        }
        input.dispatchEvent(new Event("input", { bubbles: true }));
        break;
      }
      case "facade-add-start": this._addingFacade = true; this._render(); break;
      case "facade-add-cancel": this._addingFacade = false; this._render(); break;
      case "facade-edit": this._editingFacade = actionEl.dataset.id; this._render(); break;
      case "facade-edit-cancel": this._editingFacade = null; this._render(); break;
      case "day-toggle": this._onDayToggle(actionEl); break;
      case "multiselect-toggle": this._onMultiselectToggle(actionEl); break;
      case "ha-ui": this._onHaUi(actionEl); break;
      case "ha-state-toggle": this._onHaStateToggle(actionEl); break;
      case "ha-state-add": this._onHaStateAdd(actionEl); break;
      case "cond-convert": this._onCondConvert(actionEl); break;
      case "cover-travel-reset": this._onCoverTravelReset(actionEl.dataset.id); break;
      case "cover-occ-toggle": {
        const v = actionEl.dataset.val;
        this._onOccupancyStates(actionEl.dataset.id, (list) => list.some(x => x.toLowerCase() === v.toLowerCase())
          ? list.filter(x => x.toLowerCase() !== v.toLowerCase()) : [...list, v]);
        break;
      }
      case "cover-occ-add": {
        const input = this.shadowRoot.querySelector(`[data-occ-other="${CSS.escape(actionEl.dataset.id)}"]`);
        const v = input ? input.value.trim() : "";
        if (v) this._onOccupancyStates(actionEl.dataset.id, (list) => list.some(x => x.toLowerCase() === v.toLowerCase()) ? list : [...list, v]);
        break;
      }
      case "sections-toggle-all": {
        const ids = (actionEl.dataset.ids || "").split(",").filter(Boolean);
        const allOpen = ids.every(id => this._expandedSections[id]);
        this._expandedSections = allOpen ? {} : Object.fromEntries(ids.map(id => [id, true]));
        this._render();
        break;
      }
      case "cover-occ-reset": this._onOccupancyStates(actionEl.dataset.id, () => null); break;
      case "facade-cover-toggle": actionEl.classList.toggle("selected"); break;
      case "facade-add-save": this._onFacadeAddSave(actionEl); break;
      case "facade-edit-save": this._onFacadeEditSave(actionEl); break;
      case "facade-delete": this._onFacadeDelete(actionEl.dataset.id); break;
      case "rule-expand": {
        const next = this._expandedRule === actionEl.dataset.id ? null : actionEl.dataset.id;
        this._confirmLeaveRule(() => {
          this._setExpandedRule(next);
          this._render();
          if (this._expandedRule) this._startCondPreview(); else this._stopCondPreview();
        });
        break;
      }
      case "rule-prio-up":
      case "rule-prio-down": this._onRuleMove(actionEl.dataset.id, action === "rule-prio-up" ? -1 : 1); break;
      case "rule-delete": this._onRuleDelete(actionEl.dataset.id); break;
<<<<<<< Updated upstream
      case "rule-duplicate": this._onRuleDuplicate(actionEl.dataset.id); break;
=======
      case "rule-duplicate": {
        const id = actionEl.dataset.id;
        this._confirmLeaveRule(() => this._onRuleDuplicate(id));
        break;
      }
>>>>>>> Stashed changes
      case "rule-save": this._onRuleSave(actionEl.dataset.id); break;
      case "rule-delete-condition": this._onRuleDeleteCondition(actionEl.dataset.rule, actionEl.dataset.idx); break;
      case "rule-cond-negate": this._onRuleCondNegate(actionEl); break;
      case "rule-cond-collapse": {
        const idx = parseInt(actionEl.dataset.idx, 10);
        this._setCondCollapsed(actionEl.dataset.rule, idx, !this._isCondCollapsed(actionEl.dataset.rule, idx));
        break;
      }
      case "rule-cond-collapse-all": this._onCondCollapseAll(actionEl.dataset.rule); break;
      case "rule-group-add": this._onRuleGroupAdd(actionEl.dataset.rule); break;
      case "rule-group-delete": this._onRuleGroupDelete(actionEl.dataset.rule, actionEl.dataset.group); break;
      case "rule-cond-up":
      case "rule-cond-down":
        this._onRuleCondReorder(actionEl.dataset.rule, parseInt(actionEl.dataset.idx, 10), action === "rule-cond-up" ? -1 : 1);
        break;
      case "rule-group-up":
      case "rule-group-down":
        this._onRuleGroupReorder(actionEl.dataset.rule, parseInt(actionEl.dataset.group, 10), action === "rule-group-up" ? -1 : 1);
        break;
      case "rule-facade-toggle":
      case "rule-scenario-toggle":
      case "rule-cover-toggle":
        actionEl.classList.toggle("selected");
        this._syncRuleDraftFromDom();
        break;
      case "rule-add-start": this._addingRule = true; this._render(); break;
      case "rule-add-cancel": this._addingRule = false; this._render(); break;
      case "rule-add-save": this._onRuleAddSave(actionEl); break;
      case "scenario-add-start": this._addingScenario = true; this._render(); break;
      case "scenario-add-cancel": this._addingScenario = false; this._render(); break;
      case "scenario-edit": this._editingScenario = actionEl.dataset.id; this._render(); break;
      case "scenario-edit-cancel": this._editingScenario = null; this._render(); break;
      case "scenario-activate": this._onScenarioActivate(actionEl.dataset.id); break;
      case "scenario-add-save": this._onScenarioAddSave(actionEl); break;
      case "scenario-edit-save": this._onScenarioEditSave(actionEl); break;
      case "scenario-delete": this._onScenarioDelete(actionEl.dataset.id); break;
      case "scenario-icon-pick": this._onScenarioIconPick(actionEl); break;
      case "settings-save": this._onSettingsSave(); break;
      case "backup-export": this._onBackupExportClick(); break;
      case "backup-import": { const fi = this.shadowRoot.querySelector('[data-action="backup-file"]'); if (fi) fi.click(); break; }
      case "backup-file": this._onBackupFileSelected(actionEl); break;
      case "cover-show-log": {
        const id = actionEl.dataset.id;
        this._confirmLeaveRule(() => this._confirmLeaveSettings(() => {
          this._logCover = id || null;
          this._logFilter = null;
          this._switchTab("log");
        }));
        break;
      }
      case "log-filter":
        this._logFilter = actionEl.dataset.filter || null;
        this._render();
        break;
      case "log-clear":
        // The backend clears the whole log, even with a cover filter: say so
        this._showConfirm(this._t(this._logCover ? "log_clear_confirm_all" : "log_clear_confirm"), async () => {
          try {
            await this._ws("cover_automatic/log/clear");
            this._logSeq = (this._logSeq || 0) + 1;
            this._logLoading = false;
            this._logEntries = [];
            this._render();
          } catch (err) { console.error(err); this._showError(err); }
        });
        break;
      case "confirm-ok": {
        const cb = this._confirmCallback;
        this._hideConfirm();
        if (cb) cb();
        break;
      }
      case "confirm-cancel":
        if (e.target === actionEl) this._hideConfirm();
        break;
    }
  }

  /* ---------- Change delegation ---------- */
  _handleChange(e) {
    const el = e.target;

    // Threshold entity picked: show its current value right away
    if (el.matches("[data-threshold-entity]")) {
      const out = el.closest(".threshold-entity")?.querySelector(".threshold-entity-value");
      if (out) out.innerHTML = this._thresholdEntityValue(el.value.trim());
    }

    // Master toggle
    if (el.matches('[data-action="master-toggle"]')) {
      this._onMasterToggle(el.checked, el);
      return;
    }
    // Cover select (dropdown) changes
    if (el.matches('[data-action="cover-select"]')) {
      this._debouncedCoverSave(el.dataset.id, el.dataset.field, el.value || null);
      return;
    }

    // Cover comfort-range behaviour: two flags saved together
    if (el.matches('[data-action="cover-sun-comfort"]')) {
      const flags = el.value === ""
        ? { sun_neutral_ignore: null, preemptive_shading: null }
        : this._sunComfortFlags(el.value);
      this._debouncedCoverSave(el.dataset.id, flags);
      return;
    }

    // Activity log: one cover or all (reloaded from the backend so the
    // entry limit applies to that cover only)
    if (el.matches('[data-action="log-cover"]')) {
      this._logCover = el.value || null;
      this._logEntries = null;
      this._render();
      return;
    }

    // Settings radio group: mirrored into its hidden draft field
    if (el.matches("[data-settings-radio]")) {
      const hidden = this.shadowRoot.querySelector(`[data-settings-field="${el.dataset.settingsRadio}"]`);
      if (hidden && el.checked) hidden.value = el.value;
      return;
    }

    // Cover tri-state select: "" = follow global (null)
    if (el.matches('[data-action="cover-tristate"]')) {
      const value = el.value === "true" ? true : (el.value === "false" ? false : null);
      this._debouncedCoverSave(el.dataset.id, el.dataset.field, value);
      return;
    }

    // Cover toggle (checkbox) changes
    if (el.matches('[data-action="cover-toggle"]')) {
      this._debouncedCoverSave(el.dataset.id, el.dataset.field, el.checked);
      if (el.dataset.field === "lock_hold_position") {
        // The lock position is not used while the cover keeps its position
        const pos = this.shadowRoot.querySelector(`[data-action="cover-input"][data-id="${CSS.escape(el.dataset.id)}"][data-field="lock_position"]`);
        if (pos) pos.disabled = el.checked;
      }
      return;
    }

    // Cover input (select elements also fire change)
    if (el.matches('[data-action="cover-input"]') && el.tagName === "SELECT") {
      let value = el.value;
      if (value === "") value = null;
      this._debouncedCoverSave(el.dataset.id, el.dataset.field, value);
      return;
    }

    // Rule enabled toggle
    if (el.matches('[data-action="rule-toggle-enabled"]')) {
      this._onRuleToggleEnabled(el.dataset.id, el.checked, el);
      return;
    }

    // Add condition type selector
    if (el.matches('[data-action="rule-add-condition-type"]')) {
      this._onRuleAddCondition(el.dataset.rule, el.value, parseInt(el.dataset.group, 10) || 0, el);
      return;
    }

    // Operator inside a condition group (kept locally until saved)
    if (el.matches('[data-action="rule-group-op"]')) {
      const rule = this._edRule(el.dataset.rule);
      if (rule) {
        const { ops } = this._ruleGroups(rule);
        ops[parseInt(el.dataset.group, 10) || 0] = el.value;
        rule.group_operators = ops;
        if (ops.length === 1) rule.condition_operator = el.value;
        this._refreshCondPreview();
      }
      return;
    }

    // Operator between groups: update the separators live
    if (el.matches('[data-action="rule-field"][data-field="condition_operator"]')) {
      const rule = this._edRule(el.dataset.id);
      if (rule) rule.condition_operator = el.value;
      this.shadowRoot.querySelectorAll(".cond-group-sep").forEach(sep => {
        sep.textContent = this._t(el.value === "or" ? "rule_op_short_or" : "rule_op_short_and");
      });
      return;
    }

    // Move a condition to another group
    if (el.matches('[data-action="rule-cond-group"]')) {
      this._onRuleCondMove(el.dataset.rule, parseInt(el.dataset.idx, 10), parseInt(el.value, 10) || 0, el);
      return;
    }

    // Condition param change
    if (el.matches('[data-action="cond-param"]')) {
      this._updateConditionParam(el);
      return;
    }

    // Native HA condition form
    if (el.matches('[data-action="ha-form"]')) {
      this._onHaFormChange(el, false);
      return;
    }

    // Backup file selected
    if (el.matches('[data-action="backup-file"]')) {
      this._onBackupFileSelected(el);
      return;
    }

    // Scenario rule toggle
    if (el.matches('[data-action="scenario-rule-toggle"]')) {
      this._onScenarioRuleToggle(el.dataset.scenario, el.dataset.rule, el.checked, el);
      return;
    }

    // Facade direction preset (applies house rotation to get real compass bearings)
    if (el.matches('[data-facade-field="direction"]')) {
      const presets = FACADE_PRESETS[el.value];
      if (presets) {
        const rot = (this._config && this._config.settings && this._config.settings.house_rotation != null) ? this._config.settings.house_rotation : 0;
        const form = el.closest(".inline-form");
        if (form) {
          const startInput = form.querySelector('[data-facade-field="azimuth_start"]');
          const endInput = form.querySelector('[data-facade-field="azimuth_end"]');
          if (startInput) startInput.value = ((presets.start + rot) % 360 + 360) % 360;
          if (endInput) endInput.value = ((presets.end + rot) % 360 + 360) % 360;
        }
      }
      return;
    }
  }

  /* ---------- Input delegation ---------- */
  _handleInput(e) {
    const el = e.target;

    // Rule editor field marked invalid on save: unmark once corrected
    // (condition numbers are checked again just below).
    if (el.classList && el.classList.contains("input-invalid") && el.closest && el.closest(".rule-editor")
      && !this._fieldBadValidity(el) && !(el.dataset.field === "target_position" && el.value.trim() === "")) {
      this._setInputInvalid(el, null);
    }

    // Cover input fields (debounced save)
    if (el.matches('[data-action="cover-input"]')) {
      let value = el.value;
      if (el.type === "number") {
        const check = this._checkCoverNumber(el);
        if (!check.ok) {
          // Invalid or intermediate value: mark it and send nothing
          this._cancelCoverSave(`${el.dataset.id}.${el.dataset.field}`);
          return;
        }
        value = check.value;
      }
      if (el.type === "text" && value === "") value = null;
      this._debouncedCoverSave(el.dataset.id, el.dataset.field, value);
      return;
    }

    // Rule editor fields kept only in the DOM: mirror them into the draft
    if (el.matches('[data-action="rule-field"]')) {
      this._syncRuleDraftFromDom();
      return;
    }

    // Condition param input (live update local state)
    if (el.matches('[data-action="cond-param"]')) {
      this._updateConditionParam(el);
      return;
    }

    // Native HA condition: YAML editor and number fields (live)
    if (el.matches('[data-action="ha-yaml"]')) {
      this._onHaYamlInput(el);
      return;
    }
    if (el.matches('input[type="number"][data-action="ha-form"]')) {
      this._onHaFormChange(el, true);
      return;
    }

    // Live compass update
    if (el.id === "house-rotation-input") {
      const parsed = parseFloat(el.value);
      const val = Number.isFinite(parsed) ? parsed : 0;
      const svg = this.shadowRoot.querySelector("#compass-svg");
      if (svg && svg.parentElement) {
        svg.parentElement.innerHTML = this._renderCompassSVG(val);
      }
      return;
    }
  }

  /* ---------- Drag delegation ---------- */
  _handleDragStart(e) {
    const row = e.target.closest('[data-action="rule-drag"]');
    if (!row) return;
    this._dragRuleId = row.dataset.ruleId;
    row.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", row.dataset.ruleId);
  }

  _handleDragEnd(e) {
    const row = e.target.closest('[data-action="rule-drag"]');
    if (!row) return;
    this._dragRuleId = null;
    this._dragOverId = null;
    this.shadowRoot.querySelectorAll(".rule-row").forEach(r => {
      r.classList.remove("dragging");
      r.classList.remove("drag-over");
    });
  }

  _handleDragOver(e) {
    const row = e.target.closest('[data-action="rule-drag"]');
    if (!row) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (row.dataset.ruleId !== this._dragRuleId) {
      this._dragOverId = row.dataset.ruleId;
      this.shadowRoot.querySelectorAll(".rule-row").forEach(r => r.classList.remove("drag-over"));
      row.classList.add("drag-over");
    }
  }

  _handleDragLeave(e) {
    const row = e.target.closest('[data-action="rule-drag"]');
    if (row) row.classList.remove("drag-over");
  }

  async _handleDrop(e) {
    const row = e.target.closest('[data-action="rule-drag"]');
    if (!row) return;
    e.preventDefault();
    row.classList.remove("drag-over");
    const draggedId = e.dataTransfer.getData("text/plain");
    const targetId = row.dataset.ruleId;
    if (draggedId && targetId && draggedId !== targetId) {
      const rules = this._config.rules || {};
      const sorted = this._rulesByPriority(rules);
      const ids = sorted.map(r => r.id);
      const fromIdx = ids.indexOf(draggedId);
      const toIdx = ids.indexOf(targetId);
      if (fromIdx !== -1 && toIdx !== -1) {
        ids.splice(fromIdx, 1);
        ids.splice(toIdx, 0, draggedId);
        await this._reorderRules(ids);
      }
    }
    this._dragRuleId = null;
    this._dragOverId = null;
  }

  async _reorderRules(ids) {
    try {
      const result = await this._ws("cover_automatic/rule/reorder", { rule_ids: ids });
      this._updateConfigFromResult(result);
      return true;
    } catch (err) { console.error(err); this._showError(err); return false; }
  }

  // Up/down buttons: move a rule one step in priority.
  async _onRuleMove(ruleId, delta) {
    if (this._ruleMoving) return;
    const ids = this._rulesByPriority(this._config.rules || {}).map(r => r.id);
    const from = ids.indexOf(ruleId);
    const to = from + delta;
    if (from === -1 || to < 0 || to >= ids.length) return;
    ids.splice(from, 1);
    ids.splice(to, 0, ruleId);
    this._ruleMoving = true;
    let ok = false;
    try { ok = await this._reorderRules(ids); } finally { this._ruleMoving = false; }
    if (!ok) return;
    // Keep keyboard focus on the moved rule (fall back to the other arrow at the ends)
    const row = this.shadowRoot.querySelector(`.rule-row[data-rule-id="${CSS.escape(ruleId)}"]`);
    if (!row) return;
    const want = row.querySelector(`[data-action="${delta < 0 ? "rule-prio-up" : "rule-prio-down"}"]`);
    const other = row.querySelector(`[data-action="${delta < 0 ? "rule-prio-down" : "rule-prio-up"}"]`);
    (want && !want.disabled ? want : other)?.focus();
  }

  /* ---------- House compass drag-rotation ---------- */
  _handleHouseDragStart(e) {
    if (e.button !== 0 && e.pointerType === "mouse") return;
    const target = e.target.closest('[data-action="house-drag-start"]');
    if (!target) return;
    e.preventDefault();
    const svg = this.shadowRoot.querySelector("#compass-svg");
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const vb = (svg.getAttribute("viewBox") || "0 0 280 288").split(" ").map(parseFloat);
    const compassCxLogical = 140; // matches _renderCompassSVG cx/cy
    const compassCyLogical = 140;
    const cxPx = rect.left + (compassCxLogical / vb[2]) * rect.width;
    const cyPx = rect.top + (compassCyLogical / vb[3]) * rect.height;
    this._houseDragState = { cxPx, cyPx };
    target.style.cursor = "grabbing";
    this._houseDragMoveBound = (ev) => this._handleHouseDragMove(ev);
    this._houseDragEndBound = (ev) => this._handleHouseDragEnd(ev);
    window.addEventListener("pointermove", this._houseDragMoveBound);
    window.addEventListener("pointerup", this._houseDragEndBound);
    window.addEventListener("pointercancel", this._houseDragEndBound);
  }

  _handleHouseDragMove(e) {
    if (!this._houseDragState) return;
    e.preventDefault();
    const { cxPx, cyPx } = this._houseDragState;
    const dx = e.clientX - cxPx;
    const dy = e.clientY - cyPx;
    // SVG rotate(0) keeps the house upright (north-pointing). atan2(dy, dx)
    // returns 0 for the +x axis (east), so add 90° to align with north.
    let angle = Math.atan2(dy, dx) * 180 / Math.PI + 90;
    while (angle > 180) angle -= 360;
    while (angle < -180) angle += 360;
    if (e.shiftKey) {
      angle = Math.round(angle / 45) * 45;
    } else {
      angle = Math.round(angle * 2) / 2; // 0.5° steps
    }
    // Update transform inline (avoid full SVG re-render during drag)
    const houseG = this.shadowRoot.querySelector("#compass-house");
    if (houseG) {
      houseG.setAttribute("transform", `rotate(${angle}, 140, 140)`);
    }
    const degLabel = this.shadowRoot.querySelector("#compass-degree-label");
    if (degLabel) degLabel.textContent = `${angle}°`;
    const input = this.shadowRoot.querySelector("#house-rotation-input");
    if (input) input.value = angle;
  }

  _removeHouseDragListeners() {
    this._houseDragState = null;
    if (this._houseDragMoveBound) {
      window.removeEventListener("pointermove", this._houseDragMoveBound);
      window.removeEventListener("pointerup", this._houseDragEndBound);
      window.removeEventListener("pointercancel", this._houseDragEndBound);
      this._houseDragMoveBound = null;
      this._houseDragEndBound = null;
    }
  }

  _handleHouseDragEnd(e) {
    if (!this._houseDragState) return;
    this._removeHouseDragListeners();
    const houseG = this.shadowRoot.querySelector("#compass-house");
    if (houseG) houseG.style.cursor = "grab";
    // Trigger the existing live-update path so facade arcs etc. re-render.
    const input = this.shadowRoot.querySelector("#house-rotation-input");
    if (input) input.dispatchEvent(new Event("input", { bubbles: true }));
  }

  /* ---------- Action handlers ---------- */
  async _onCoverResume(entityId) {
    try {
      const result = await this._ws("cover_automatic/cover/resume", { entity_id: entityId });
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); this._showError(e); }
  }

  async _onCoverAdd() {
    const select = this.shadowRoot.querySelector("#cover-add-select");
    if (!select) return;
    const ids = Array.from(select.selectedOptions).map(o => o.value);
    if (ids.length === 0) return;
    try {
      const result = await this._ws("cover_automatic/cover/add", { entity_ids: ids });
      this._addingCover = false;
      this._updateConfigFromResult(result);
      this._showToast();
    } catch (e) { console.error(e); this._showError(e); }
  }

  _onCoverDelete(entityId) {
    this._showConfirm(this._t("confirm_delete"), async () => {
      try {
        const result = await this._ws("cover_automatic/cover/delete", { entity_id: entityId });
        if (this._selectedCover === entityId) { this._selectedCover = null; this._slideOpen = false; }
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); this._showError(e); }
    });
  }

  // Facade azimuth: any number, normalized to [0, 360) (-90 -> 270, 450 -> 90).
  _facadeAz(raw, def) {
    const v = raw === "" || raw == null ? NaN : parseFloat(raw);
    if (!Number.isFinite(v)) return def;
    return Math.round((((v % 360) + 360) % 360) * 1000) / 1000;
  }

  async _onFacadeAddSave(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = form.querySelector('[data-facade-field="name"]')?.value || "";
    if (!name.trim()) return;
    const direction = form.querySelector('[data-facade-field="direction"]')?.value || "south";
    const azStart = this._facadeAz(form.querySelector('[data-facade-field="azimuth_start"]')?.value, 135);
    const azEnd = this._facadeAz(form.querySelector('[data-facade-field="azimuth_end"]')?.value, 225);
    const minElev = (() => { const v = parseFloat(form.querySelector('[data-facade-field="min_elevation"]')?.value); return Number.isFinite(v) ? Math.max(0, v) : 0; })();
    const coverIds = [];
    form.querySelectorAll('[data-action="facade-cover-toggle"].selected').forEach(b => coverIds.push(b.dataset.cover));
    try {
      const result = await this._ws("cover_automatic/facade/add", {
        name: name.trim(), direction, azimuth_start: azStart, azimuth_end: azEnd, min_elevation: minElev, cover_ids: coverIds
      });
      this._addingFacade = false;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); this._showError(e); }
  }

  async _onFacadeEditSave(btn) {
    const facadeId = btn.dataset.id;
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = form.querySelector('[data-facade-field="name"]')?.value || "";
    if (!name.trim()) return;
    const direction = form.querySelector('[data-facade-field="direction"]')?.value || "south";
    const azStart = this._facadeAz(form.querySelector('[data-facade-field="azimuth_start"]')?.value, 135);
    const azEnd = this._facadeAz(form.querySelector('[data-facade-field="azimuth_end"]')?.value, 225);
    const minElev = (() => { const v = parseFloat(form.querySelector('[data-facade-field="min_elevation"]')?.value); return Number.isFinite(v) ? Math.max(0, v) : 0; })();
    const coverIds = [];
    form.querySelectorAll('[data-action="facade-cover-toggle"].selected').forEach(b => coverIds.push(b.dataset.cover));
    try {
      const result = await this._ws("cover_automatic/facade/update", {
        facade_id: facadeId, name: name.trim(), direction, azimuth_start: azStart, azimuth_end: azEnd, min_elevation: minElev, cover_ids: coverIds
      });
      this._editingFacade = null;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); this._showError(e); }
  }

  _onFacadeDelete(facadeId) {
    this._showConfirm(this._t("confirm_delete"), async () => {
      try {
        const result = await this._ws("cover_automatic/facade/delete", { facade_id: facadeId });
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); this._showError(e); }
    });
  }

  async _onRuleToggleEnabled(ruleId, checked, el = null) {
    try {
      const result = await this._ws("cover_automatic/rule/update", { rule_id: ruleId, enabled: checked });
      this._updateConfigFromResult(result);
    } catch (e) {
      console.error(e);
      if (el) el.checked = !checked;
      this._showError(e);
    }
  }

  async _onRuleDuplicate(ruleId) {
    const rule = (this._config.rules || {})[ruleId];
    if (!rule) return;
    const before = new Set(Object.keys(this._config.rules || {}));
    try {
      const result = await this._ws("cover_automatic/rule/duplicate", {
        rule_id: ruleId,
        name: `${rule.name} ${this._t("rule_copy_suffix")}`,
      });
      // Open the copy right away; it starts disabled, ready to be adapted
      const newId = Object.keys(result?.rules || {}).find(id => !before.has(id));
      if (newId) this._expandedRule = newId;
      this._updateConfigFromResult(result);
      if (newId) {
        this._startCondPreview();
        this._highlightRule(newId);
      }
    } catch (e) { console.error(e); }
  }

  // Scroll to a rule row and pulse it once the current render has settled
  _highlightRule(ruleId) {
    setTimeout(() => {
      if (!ruleId) return;
      const rEl = this.shadowRoot.querySelector('.rule-row[data-rule-id="' + CSS.escape(ruleId) + '"]');
      if (!rEl) return;
      rEl.scrollIntoView({ behavior: "smooth", block: "center" });
      rEl.classList.add("rule-highlight");
      setTimeout(() => rEl.classList.remove("rule-highlight"), 2000);
    }, 60);
  }

  _onRuleDelete(ruleId) {
    this._showConfirm(this._t("confirm_delete"), async () => {
      try {
        const result = await this._ws("cover_automatic/rule/delete", { rule_id: ruleId });
        if (this._expandedRule === ruleId) this._setExpandedRule(null);
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); this._showError(e); }
    });
  }

  // Native validity without stepMismatch: decimals like 25.5 or 0.5 min are
  // valid values even where the input has an integer step.
  _fieldBadValidity(el) {
    const v = el.validity;
    if (!v) return false;
    return !!(v.badInput || v.rangeUnderflow || v.rangeOverflow || v.valueMissing || v.typeMismatch || v.patternMismatch);
  }

  // First invalid field of the open rule editor (marked red), or null.
  // An empty/invalid number would otherwise silently keep its old value.
  _ruleEditorInvalid(ruleId) {
    const row = this.shadowRoot.querySelector(`.rule-row[data-rule-id="${CSS.escape(ruleId)}"]`);
    const editor = row && row.nextElementSibling && row.nextElementSibling.classList.contains("rule-editor") ? row.nextElementSibling : null;
    if (!editor) return null;
    let first = null;
    for (const el of editor.querySelectorAll("input, select, textarea")) {
      if (el.disabled || el.type === "hidden") continue;
      let bad = el.classList.contains("input-invalid") || this._fieldBadValidity(el);
      // The target position is required (empty = old value kept)
      if (!bad && el.dataset.field === "target_position" && el.value.trim() === "") bad = true;
      if (bad) {
        if (!el.classList.contains("input-invalid")) this._setInputInvalid(el, this._t("input_invalid_number"));
        if (!first) first = el;
      }
    }
    return first;
  }

  async _onRuleSave(ruleId) {
    const invalid = this._ruleEditorInvalid(ruleId);
    if (invalid) {
      this._showToast(this._t("rule_invalid_fields"), true);
      // Field hidden in a collapsed condition card: expand that card first
      const card = invalid.closest && invalid.closest(".condition-card.collapsed");
      if (card && card.dataset.condCard) {
        const key = card.dataset.condCard;
        const cut = key.lastIndexOf(":");
        const idx = parseInt(key.slice(cut + 1), 10);
        if (Number.isInteger(idx)) this._setCondCollapsed(key.slice(0, cut), idx, false);
      }
      if (invalid.offsetParent !== null) {
        invalid.scrollIntoView({ block: "center", behavior: "smooth" });
        invalid.focus({ preventScroll: true });
      }
      return;
    }
    // YAML conditions: wait until params.config matches the typed YAML
    await this._flushHaValidations(ruleId);
    const data = this._collectRuleEditorData(this.shadowRoot, ruleId);
    if (!data) return;
    // A valid YAML condition the form can show goes back to the form view
    // (templates and other complex conditions stay in YAML).
    (data.conditions || []).forEach((c, idx) => {
      if (!c || c.type !== "ha_condition" || !c.params || c.params.ui !== "yaml") return;
      const live = this._haLive && this._haLive[ruleId + ":" + idx];
      if (live && (live.pending || live.valid === false)) return;
      if (this._haFormModel(c.params.config, c.params.op)) c.params = { ...c.params, ui: "form" };
    });
    try {
      const result = await this._ws("cover_automatic/rule/update", data);
      this._updateConfigFromResult(result, { resetDraft: true });
      this._refreshCondPreview();
    } catch (e) { console.error(e); this._showError(e); }
  }

  // Apply a structural change (conditions/groups) to the editor draft only:
  // like every other edit it reaches the server with "Save". Callers flush
  // pending HA validations first. indexMap(oldIdx) -> newIdx | null keeps the
  // collapsed state and live HA status of each card with its condition.
  // Resolves to true when applied.
  async _saveRuleStructure(ruleId, conditions, groups, indexMap = null) {
    if (ruleId === this._expandedRule) this._syncRuleDraftFromDom();
    const rule = this._edRule(ruleId);
    if (!rule) { this._render(); return false; }
    // Indices may change: void pending validations and previews.
    this._cancelHaTimers(ruleId);
    this._previewSeq++;
    if (conditions) rule.conditions = conditions.map(c => ({ ...c }));
    if (groups) {
      rule.group_operators = [...groups.ops];
      rule.condition_operator = groups.between;
    }
    // A single group left: its own operator is the rule's operator (the
    // "between groups" one no longer applies).
    const info = this._ruleGroups(rule);
    if (info.n === 1) {
      rule.group_operators = [info.ops[0]];
      rule.condition_operator = info.ops[0];
    }
    if (indexMap) this._remapRuleIndexState(ruleId, indexMap);
    // The DOM still shows the old structure: don't read it back into the
    // draft while re-rendering (indices changed).
    this._noDomSync = true;
    try { this._render(); } finally { this._noDomSync = false; }
    this._refreshCondPreview();
    return true;
  }

  // Move per-condition editor state (collapsed cards, live HA status) to the
  // new condition indices; null drops the entry.
  _remapRuleIndexState(ruleId, indexMap) {
    const pre = ruleId + ":";
    const remap = (keys, put) => {
      for (const key of keys) {
        if (!key.startsWith(pre)) continue;
        const next = indexMap(parseInt(key.slice(pre.length), 10));
        if (next != null) put(pre + next, key);
      }
    };
    if (this._collapsedConds) {
      const old = this._collapsedConds;
      const next = new Set([...old].filter(k => !k.startsWith(pre)));
      remap(old, (k) => next.add(k));
      this._collapsedConds = next;
    }
    if (this._haLive) {
      const old = this._haLive;
      const next = {};
      for (const [k, v] of Object.entries(old)) if (!k.startsWith(pre)) next[k] = v;
      remap(Object.keys(old), (k, from) => { if (!old[from].pending) next[k] = old[from]; });
      this._haLive = next;
    }
  }

  _onRuleCondNegate(btn) {
    const rule = this._edRule(btn.dataset.rule);
    const idx = parseInt(btn.dataset.idx, 10);
    const cond = rule && rule.conditions ? rule.conditions[idx] : null;
    if (!cond) return;
    cond.negate = !cond.negate;
    btn.classList.toggle("active", cond.negate);
    btn.closest(".condition-card")?.classList.toggle("negated", cond.negate);
    this._refreshCondPreview();
  }

  async _onRuleGroupAdd(ruleId) {
    await this._flushHaValidations(ruleId);
    const rule = this._edRule(ruleId);
    if (!rule) return;
    const { ops, n, between } = this._ruleGroups(rule);
    if (n >= MAX_CONDITION_GROUPS) return;
    // From one group to two: the groups are joined by the opposite operator,
    // e.g. (A or B) and (C or D), and the new group copies the first one's.
    const nextBetween = n === 1 ? (ops[0] === "or" ? "and" : "or") : between;
    await this._saveRuleStructure(ruleId, null, { ops: [...ops, ops[n - 1]], between: nextBetween });
  }

  _onRuleGroupDelete(ruleId, group) {
    const rule = this._edRule(ruleId);
    const g = parseInt(group, 10);
    if (!rule || !Number.isFinite(g)) return;
    const inGroup = (c) => (parseInt(c.group, 10) || 0) === g;
    // Built from the draft when confirmed: the confirm dialog re-renders the
    // editor, the draft keeps every unsaved edit meanwhile.
    const run = async () => {
      await this._flushHaValidations(ruleId);
      const r = this._edRule(ruleId);
      if (!r) return false;
      const { ops, between } = this._ruleGroups(r);
      const conds = (r.conditions || [])
        .filter(c => !inGroup(c))
        .map(c => { const cg = parseInt(c.group, 10) || 0; return { ...c, group: cg > g ? cg - 1 : cg }; });
      const nextOps = ops.filter((_, i) => i !== g);
      // Old index -> new index of the kept conditions
      const kept = (r.conditions || []).map((c, i) => (inGroup(c) ? -1 : i)).filter(i => i >= 0);
      return this._saveRuleStructure(ruleId, conds, { ops: nextOps.length ? nextOps : ["and"], between },
        (i) => { const k = kept.indexOf(i); return k < 0 ? null : k; });
    };
    const removed = (rule.conditions || []).filter(inGroup).length;
    if (removed > 0) this._showConfirm(this._t("rule_group_delete_confirm"), run);
    else run();
  }

  async _onRuleCondMove(ruleId, idx, group, el = null) {
    await this._flushHaValidations(ruleId);
    const rule = this._edRule(ruleId);
    if (!rule || !rule.conditions || !rule.conditions[idx]) return;
    const prevGroup = parseInt(rule.conditions[idx].group, 10) || 0;
    const conds = rule.conditions.map((c, i) => (i === idx ? { ...c, group } : c));
    const ok = await this._saveRuleStructure(ruleId, conds, null, (i) => i);
    if (!ok && el && el.isConnected) el.value = String(prevGroup);
  }

  // Move a condition up (dir -1) or down (dir 1) within its group: it swaps
  // places with the previous/next condition of the same group; the other
  // conditions keep their positions.
  async _onRuleCondReorder(ruleId, idx, dir) {
    await this._flushHaValidations(ruleId);
    const rule = this._edRule(ruleId);
    if (!rule || !rule.conditions || !rule.conditions[idx]) return;
    const siblings = this._groupCondIndices(rule.conditions, parseInt(rule.conditions[idx].group, 10) || 0);
    const pos = siblings.indexOf(idx);
    const other = siblings[pos + dir];
    if (pos < 0 || other === undefined) return;
    const perm = rule.conditions.map((_, i) => (i === idx ? other : i === other ? idx : i));
    const conds = perm.map(i => rule.conditions[i]);
    await this._saveRuleStructure(ruleId, conds, null, (i) => perm.indexOf(i));
  }

  // Move a whole group up/down: swaps its index (conditions' group and
  // group_operators entry) with the neighbouring group.
  async _onRuleGroupReorder(ruleId, g, dir) {
    await this._flushHaValidations(ruleId);
    const rule = this._edRule(ruleId);
    if (!rule || !Number.isFinite(g)) return;
    const { ops, n, between } = this._ruleGroups(rule);
    const h = g + dir;
    if (g < 0 || g >= n || h < 0 || h >= n) return;
    const conds = (rule.conditions || []).map(c => {
      const cg = parseInt(c.group, 10) || 0;
      return cg === g ? { ...c, group: h } : cg === h ? { ...c, group: g } : c;
    });
    const nextOps = [...ops];
    [nextOps[g], nextOps[h]] = [nextOps[h], nextOps[g]];
    // Flat condition order is unchanged: per-index state stays valid.
    await this._saveRuleStructure(ruleId, conds, { ops: nextOps, between }, (i) => i);
  }

  async _onRuleAddCondition(ruleId, condType, group = 0, el = null) {
    if (!condType) return;
    await this._flushHaValidations(ruleId);
    const rule = this._edRule(ruleId);
    if (!rule) { if (el) el.value = ""; return; }
    let newCond;
    if (condType.startsWith("ha:")) {
      const kind = condType.slice(3);
      newCond = kind === "yaml"
        ? { type: "ha_condition", params: { ui: "yaml", config: null, yaml: "" } }
        : { type: "ha_condition", params: { ui: "form", config: this._haDefaultConfig(kind), yaml: "" } };
    } else {
      const paramDefs = CONDITION_PARAMS[condType] || [];
      const params = {};
      for (const p of paramDefs) params[p.key] = p.default;
      newCond = { type: condType, params: params };
    }
    newCond.group = group;
    newCond.negate = false;
    const nextConditions = [...(rule.conditions || []), newCond];
    const ok = await this._saveRuleStructure(ruleId, nextConditions, null, (i) => i);
    if (!ok && el && el.isConnected) el.value = "";
  }

  async _onRuleDeleteCondition(ruleId, idx) {
    await this._flushHaValidations(ruleId);
    const rule = this._edRule(ruleId);
    if (!rule || !rule.conditions) return;
    const idxInt = parseInt(idx, 10);
    if (!Number.isFinite(idxInt)) return;
    const nextConditions = rule.conditions.filter((_, i) => i !== idxInt);
    await this._saveRuleStructure(ruleId, nextConditions, null,
      (i) => (i === idxInt ? null : i > idxInt ? i - 1 : i));
  }

  async _onRuleAddSave(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = form.querySelector('[data-rule-new-field="name"]')?.value || "";
    if (!name.trim()) return;
    const tp = (() => { const v = form.querySelector('[data-rule-new-field="target_position"]')?.value; return v !== "" && v != null ? parseInt(v, 10) : 0; })();
    const ttp = form.querySelector('[data-rule-new-field="target_tilt_position"]')?.value;
    try {
      const data = { name: name.trim(), target_position: tp };
      if (ttp !== "" && ttp != null) {
        const n = parseInt(ttp, 10);
        if (Number.isFinite(n)) data.target_tilt_position = n;
      }
      const result = await this._ws("cover_automatic/rule/add", data);
      this._addingRule = false;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); this._showError(e); }
  }

  _setInputInvalid(el, message) {
    if (message) {
      el.classList.add("input-invalid");
      el.setAttribute("aria-invalid", "true");
      el.title = message;
    } else if (el.classList.contains("input-invalid")) {
      el.classList.remove("input-invalid");
      el.removeAttribute("aria-invalid");
      el.removeAttribute("title");
    }
  }

  // Validate a cover number input against the cover/update schema.
  // Returns { ok, value } (value null = cleared, falls back to the default).
  _checkCoverNumber(el) {
    const lim = COVER_INT_LIMITS[el.dataset.field];
    if (el.value === "" && !(el.validity && el.validity.badInput)) {
      this._setInputInvalid(el, null);
      return { ok: true, value: null };
    }
    const n = el.value === "" ? NaN : Number(el.value);
    let msg = null;
    if (!Number.isFinite(n)) msg = this._t("input_invalid_number");
    else if (lim && (!Number.isInteger(n) || n < lim[0] || n > lim[1])) {
      msg = this._t("input_invalid_range").replace("{min}", lim[0]).replace("{max}", lim[1]);
    }
    this._setInputInvalid(el, msg);
    return msg ? { ok: false, value: null } : { ok: true, value: n };
  }

  _updateConditionParam(el) {
    const ruleId = el.dataset.rule;
    const idx = parseInt(el.dataset.idx, 10);
    const key = el.dataset.key;
    const rule = this._edRule(ruleId);
    if (rule && rule.conditions && rule.conditions[idx]) {
      let val = el.value;
      if (el.type === "number") {
        // Empty or "-" while typing: keep the previous value, mark the field
        const n = val === "" ? NaN : Number(val);
        if (!Number.isFinite(n)) {
          this._setInputInvalid(el, this._t("input_invalid_number"));
          return;
        }
        this._setInputInvalid(el, null);
        val = n;
      }
      if (!rule.conditions[idx].params) rule.conditions[idx].params = {};
      rule.conditions[idx].params[key] = val;
    }
  }

  _onDayToggle(el) {
    const ruleId = el.dataset.rule;
    const idx = parseInt(el.dataset.idx, 10);
    const key = el.dataset.key;
    const day = el.dataset.day;
    const rule = this._edRule(ruleId);
    if (rule && rule.conditions && rule.conditions[idx]) {
      if (!rule.conditions[idx].params) rule.conditions[idx].params = {};
      let days = rule.conditions[idx].params[key];
      if (!Array.isArray(days)) days = [];
      if (days.includes(day)) {
        days = days.filter(d => d !== day);
      } else {
        days.push(day);
      }
      rule.conditions[idx].params[key] = days;
      el.classList.toggle("selected");
    }
  }

  _onMultiselectToggle(el) {
    const ruleId = el.dataset.rule;
    const idx = parseInt(el.dataset.idx, 10);
    const key = el.dataset.key;
    const val = el.dataset.val;
    const rule = this._edRule(ruleId);
    if (rule && rule.conditions && rule.conditions[idx]) {
      if (!rule.conditions[idx].params) rule.conditions[idx].params = {};
      let arr = rule.conditions[idx].params[key];
      if (!Array.isArray(arr)) arr = arr ? [arr] : [];
      if (arr.includes(val)) {
        arr = arr.filter(v => v !== val);
      } else {
        arr.push(val);
      }
      rule.conditions[idx].params[key] = arr;
      el.classList.toggle("selected");
    }
  }

  async _onScenarioActivate(scenarioId) {
    try {
      const result = await this._ws("cover_automatic/scenario/update", { scenario_id: scenarioId, activate: true });
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); this._showError(e); }
  }

  // Calls are serialized per scenario: each one starts from the list the
  // previous call returned, so quick successive clicks are all kept.
  _onScenarioRuleToggle(scenarioId, ruleId, checked, el = null) {
    if (!this._scRuleQueue) this._scRuleQueue = {};
    if (!this._scRuleQueueLen) this._scRuleQueueLen = {};
    this._scRuleQueueLen[scenarioId] = (this._scRuleQueueLen[scenarioId] || 0) + 1;
    const run = async () => {
      let rerender = false;
      try {
        const scenario = (this._config.scenarios || {})[scenarioId];
        if (!scenario) return;
        let disabled = [...(scenario.rules_disabled || [])];
        if (checked) {
          disabled = disabled.filter(id => id !== ruleId);
        } else if (!disabled.includes(ruleId)) {
          disabled.push(ruleId);
        }
        const result = await this._ws("cover_automatic/scenario/update", { scenario_id: scenarioId, rules_disabled: disabled });
        // More clicks queued: keep their checkboxes as clicked until the last one
        const more = this._scRuleQueueLen[scenarioId] > 1;
        this._updateConfigFromResult(result, more ? { render: false } : {});
      } catch (e) {
        console.error(e);
        if (el && el.isConnected) el.checked = !checked;
        rerender = true;
        this._showError(e);
      } finally {
        this._scRuleQueueLen[scenarioId] -= 1;
        // Last queued call failed or an earlier result was not rendered
        if (rerender && this._scRuleQueueLen[scenarioId] === 0) this._render();
      }
    };
    const prev = this._scRuleQueue[scenarioId] || Promise.resolve();
    const next = prev.then(run, run);
    this._scRuleQueue[scenarioId] = next;
    return next;
  }

  _onScenarioIconPick(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const icon = btn.dataset.icon || "";
    const hidden = form.querySelector('[data-scenario-field="icon"]');
    if (hidden) hidden.value = icon;
    const custom = form.querySelector('[data-scenario-icon-custom]');
    if (custom) custom.value = "";
    form.querySelectorAll('[data-action="scenario-icon-pick"]').forEach(el => {
      el.classList.toggle("selected", el === btn);
    });
  }

  _readScenarioIcon(form, fallback) {
    const custom = form.querySelector('[data-scenario-icon-custom]')?.value || "";
    if (custom.trim()) return custom.trim();
    const picked = form.querySelector('[data-scenario-field="icon"]')?.value || "";
    return picked.trim() || fallback;
  }

  async _onScenarioAddSave(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = form.querySelector('[data-scenario-field="name"]')?.value || "";
    if (!name.trim()) return;
    const icon = this._readScenarioIcon(form, "mdi:home");
    try {
      const result = await this._ws("cover_automatic/scenario/add", { name: name.trim(), icon: icon });
      this._addingScenario = false;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); this._showError(e); }
  }

  async _onScenarioEditSave(btn) {
    const scenarioId = btn.dataset.id;
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = form.querySelector('[data-scenario-field="name"]')?.value || "";
    if (!name.trim()) return;
    const icon = this._readScenarioIcon(form, "mdi:home");
    try {
      const result = await this._ws("cover_automatic/scenario/update", { scenario_id: scenarioId, name: name.trim(), icon: icon });
      this._editingScenario = null;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); this._showError(e); }
  }

  _onScenarioDelete(scenarioId) {
    this._showConfirm(this._t("confirm_delete"), async () => {
      try {
        const result = await this._ws("cover_automatic/scenario/delete", { scenario_id: scenarioId });
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); this._showError(e); }
    });
  }

  async _onMasterToggle(checked, el = null) {
    try {
      const result = await this._ws("cover_automatic/settings/update", { enabled: checked });
      this._updateConfigFromResult(result);
    } catch (e) {
      console.error(e);
      if (el) el.checked = !checked;
      this._showError(e);
    }
  }

  // Unsaved settings inputs survive section switches and re-renders.
  _captureSettingsDraft() {
    if (this._activeTab !== "settings" || !this.shadowRoot || this._skipSettingsCapture || this._settingsDomStale) return;
    const inputs = this.shadowRoot.querySelectorAll("[data-settings-field]");
    if (!inputs.length) return;
    const draft = this._settingsDraft || {};
    inputs.forEach(input => {
      const kind = input.type === "checkbox" ? "checkbox" : (input.type === "number" ? "number" : "text");
      const field = input.dataset.settingsField;
      const value = kind === "checkbox" ? input.checked : input.value;
      // The stored value the input was rendered with (first capture only)
      const initial = draft[field] ? draft[field].initial : this._settingsInputDefault(input);
      draft[field] = { kind, value, initial };
    });
    this._settingsDraft = draft;
  }

  // Value an input was rendered with (the stored setting), not the edited one.
  _settingsInputDefault(input) {
    // Hidden inputs change their attribute with their value: explicit initial
    if (input.dataset.initial !== undefined) return input.dataset.initial;
    if (input.type === "checkbox") return input.defaultChecked;
    if (input.tagName === "SELECT") {
      const opt = Array.from(input.options).find(o => o.defaultSelected) || input.options[0];
      return opt ? opt.value : "";
    }
    return input.defaultValue;
  }

  // True when a settings input differs from its stored value.
  _settingsDirty() {
    this._captureSettingsDraft();
    return Object.values(this._settingsDraft || {}).some(d => !this._draftSame(d));
  }

  // Draft entry unchanged? Numbers compare by value ("21.0" == "21").
  _draftSame(d) {
    if (d.kind === "number") {
      const a = String(d.value ?? "").trim(), b = String(d.initial ?? "").trim();
      if (a === "" || b === "") return a === b;
      return Number(a) === Number(b);
    }
    return d.value === d.initial;
  }

  // Run `then` after the user agreed to drop unsaved settings (if any).
  _confirmLeaveSettings(then) {
    if (this._activeTab === "settings" && this._settingsDirty()) {
      this._showConfirm(this._t("settings_unsaved_confirm"), then, this._t("discard"));
    } else then();
  }

  // Radio groups follow their hidden draft field (restored drafts)
  _syncSettingsRadios() {
    if (!this.shadowRoot) return;
    this.shadowRoot.querySelectorAll("[data-settings-radio]").forEach(r => {
      const hidden = this.shadowRoot.querySelector(`[data-settings-field="${r.dataset.settingsRadio}"]`);
      if (hidden) r.checked = r.value === hidden.value;
    });
  }

  _applySettingsDraft() {
    const draft = this._settingsDraft;
    if (!draft || this._activeTab !== "settings" || !this.shadowRoot) return;
    this.shadowRoot.querySelectorAll("[data-settings-field]").forEach(input => {
      const d = draft[input.dataset.settingsField];
      if (!d) return;
      // Stored value after a server-side change: taken from the fresh render
      if (d.initial === undefined) d.initial = this._settingsInputDefault(input);
      if (d.kind === "checkbox") input.checked = !!d.value;
      else if (input.value !== d.value) {
        input.value = d.value;
        // Compass preview follows the restored rotation
        if (input.id === "house-rotation-input") input.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });
  }

  async _onSettingsSave() {
    this._captureSettingsDraft();
    return this._saveSettingsDraft();
  }

  // Returns true once saved (false when invalid or on error).
  async _saveSettingsDraft() {
    // Only these numeric settings accept null (= unset); an empty field of
    // any other numeric setting is left out and keeps its stored value.
    const NULLABLE = new Set(["lock_tilt_position", "vent_tilt_position", "default_travel_time"]);
    const data = {};
    for (const [field, d] of Object.entries(this._settingsDraft || {})) {
      // Send only the fields really changed: an untouched field must not
      // overwrite a value changed meanwhile elsewhere (other window, import).
      if (this._draftSame(d)) continue;
      if (d.kind === "checkbox") {
        data[field] = !!d.value;
      } else if (d.kind === "number") {
        const raw = String(d.value ?? "").trim();
        const n = raw === "" ? NaN : parseFloat(raw);
        if (Number.isFinite(n)) data[field] = n;
        else if (raw === "" && NULLABLE.has(field)) data[field] = null;
      } else {
        data[field] = String(d.value ?? "").trim() || null;
      }
    }
    // Comfort-range behaviour: one choice stored as two flags
    if (data.sun_comfort_mode !== undefined) {
      if (data.sun_comfort_mode) Object.assign(data, this._sunComfortFlags(data.sun_comfort_mode));
      delete data.sun_comfort_mode;
    }
    // Temperature colours: radio choice stored as one flag
    if (data.temp_color_mode !== undefined) {
      if (data.temp_color_mode) data.temp_color_thermometer = data.temp_color_mode === "thermometer";
      delete data.temp_color_mode;
    }
    if (data.wind_position !== undefined && !(Number.isInteger(data.wind_position) && data.wind_position >= 0 && data.wind_position <= 100)) {
      alert(this._t("settings_wind_position") + this._colon() + this._t("input_invalid_range").replace("{min}", 0).replace("{max}", 100));
      return false;
    }
    // Whole-number settings: refuse decimals instead of letting the backend
    // silently truncate them (10.5 -> 10).
    const INTEGER = ["pause_duration", "lock_position", "vent_position", "lock_tilt_position",
      "vent_tilt_position", "min_position_change", "min_time_between_changes", "default_travel_time"];
    const badInt = INTEGER.find(f => data[f] != null && !Number.isInteger(data[f]));
    if (badInt) {
      const input = this.shadowRoot.querySelector(`[data-settings-field="${badInt}"]`);
      const label = input?.closest(".form-group")?.querySelector("label")?.textContent?.trim() || badInt;
      alert(label + this._colon() + this._t("input_not_integer"));
      return false;
    }
    // Validate comfort range: the static numbers only (entities are resolved
    // by the backend, the numbers stay the fallback)
    const cur = this._config.settings || {};
    const cmin = data.comfort_temp_min ?? cur.comfort_temp_min;
    const cmax = data.comfort_temp_max ?? cur.comfort_temp_max;
    if (cmin != null && cmax != null && cmin >= cmax) {
      alert(this._t("settings_validation_min_max"));
      return false;
    }
    try {
      const result = await this._ws("cover_automatic/settings/update", data);
      this._settingsDraft = null;
      this._skipSettingsCapture = true;
      try { this._updateConfigFromResult(result); } finally { this._skipSettingsCapture = false; }
      return true;
    } catch (e) { console.error(e); this._showError(e); return false; }
  }

  // Unsaved settings would be missing from the export: offer to save first.
  _onBackupExportClick() {
    if (this._settingsDirty()) {
      this._showConfirm(this._t("settings_export_unsaved_confirm"), async () => {
        if (await this._saveSettingsDraft()) await this._onBackupExport();
      }, this._t("settings_save_and_export"));
    } else this._onBackupExport();
  }

  async _onBackupExport() {
    try {
      const result = await this._ws("cover_automatic/export", {});
      const json = JSON.stringify(result.data, null, 2);
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "cover_automatic_backup.json";
      a.style.display = "none";
      // Firefox/Safari need the link in the document; revoking right away
      // can cancel the download before it starts.
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { a.remove(); URL.revokeObjectURL(url); }, 1000);
    } catch (e) {
      console.error(e);
      alert(this._t("settings_export_error") + this._colon() + e.message);
    }
  }

  _onBackupFileSelected(input) {
    const file = input.files && input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      input.value = "";
      let data;
      try {
        data = JSON.parse(reader.result);
      } catch (e) {
        alert(this._t("settings_import_error") + this._colon() + this._t("import_invalid_json"));
        return;
      }
      if (!confirm(this._t("settings_import_confirm"))) return;
      try {
        const result = await this._ws("cover_automatic/import", { data });
        // Everything shown now comes from the imported file
        this._settingsDraft = null;
        this._updateConfigFromResult(result);
        this._showToast();
        alert(this._t("settings_import_success"));
      } catch (e) {
        console.error(e);
        this._showError(e);
      }
    };
    reader.readAsText(file);
  }

  /* ---------- Rule editor draft ---------- */

  // Rule as the editor sees it: the draft of the open rule, else the saved one.
  _edRule(ruleId) {
    if (ruleId == null) return null;
    const d = this._ruleDraft;
    if (d && d.id === ruleId) return d.rule;
    const saved = (this._config && this._config.rules || {})[ruleId] || null;
    // The open editor always works on a draft (created on first use)
    if (saved && ruleId === this._expandedRule) {
      this._ruleDraft = { id: ruleId, rule: this._clone(saved) };
      return this._ruleDraft.rule;
    }
    return saved;
  }

  // Open another rule editor (or none): the previous draft is discarded.
  // Copy placed right below the original, active, and opened for editing.
  async _onRuleDuplicate(ruleId) {
    const rule = (this._config.rules || {})[ruleId];
    if (!rule) return;
    try {
      const suffix = " - " + this._t("rule_copy_suffix");
      // Rule names are limited to 100 characters (room left for " 2", " 3"...)
      const name = rule.name.slice(0, Math.max(1, 97 - suffix.length)).trimEnd() + suffix;
      const result = await this._ws("cover_automatic/rule/duplicate", { rule_id: ruleId, name });
      this._setExpandedRule(null);
      this._updateConfigFromResult(result);
      if (result.new_rule_id) {
        this._setExpandedRule(result.new_rule_id);
        this._render();
        this._startCondPreview();
        setTimeout(() => this.shadowRoot.querySelector(`.rule-row[data-rule-id="${CSS.escape(result.new_rule_id)}"]`)?.scrollIntoView({ block: "center", behavior: "smooth" }), 50);
      }
    } catch (e) { console.error(e); this._showError(e); }
  }

  _setExpandedRule(ruleId) {
    this._discardRuleDraft();
    this._expandedRule = ruleId || null;
    const saved = ruleId ? (this._config && this._config.rules || {})[ruleId] : null;
    if (saved) {
      this._ruleDraft = { id: ruleId, rule: this._clone(saved) };
      // Existing conditions open collapsed; conditions added afterwards open expanded.
      if (!this._collapsedConds) this._collapsedConds = new Set();
      const pre = ruleId + ":";
      for (const k of [...this._collapsedConds]) if (k.startsWith(pre)) this._collapsedConds.delete(k);
      (saved.conditions || []).forEach((_, i) => this._collapsedConds.add(pre + i));
    }
  }

  _discardRuleDraft() {
    const d = this._ruleDraft;
    if (!d) return;
    this._ruleDraft = null;
    // Pending validations/previews refer to the discarded conditions
    this._cancelHaTimers(d.id);
    this._previewSeq++;
    if (this._haLive) {
      const pre = d.id + ":";
      for (const k of Object.keys(this._haLive)) if (k.startsWith(pre)) delete this._haLive[k];
    }
  }

  // Copy the editor fields that live only in the DOM (name, targets,
  // scenario/facade/cover chips) into the draft.
  _syncRuleDraftFromDom() {
    const d = this._ruleDraft;
    if (!d || this._noDomSync || !this.shadowRoot) return;
    const root = this.shadowRoot;
    const id = CSS.escape(d.id);
    const field = (f) => root.querySelector(`[data-action="rule-field"][data-id="${id}"][data-field="${f}"]`);
    const nameEl = field("name");
    if (!nameEl) return; // editor not rendered
    const r = d.rule;
    r.name = nameEl.value;
    const safetyEl = field("safety");
    if (safetyEl) r.safety = !!safetyEl.checked;
    const tpEl = field("target_position");
    if (tpEl && tpEl.value !== "") {
      const n = parseInt(tpEl.value, 10);
      if (Number.isFinite(n)) r.target_position = n;
    }
    const ttpEl = field("target_tilt_position");
    if (ttpEl) {
      if (ttpEl.value === "" && !(ttpEl.validity && ttpEl.validity.badInput)) r.target_tilt_position = null;
      else {
        const n = parseInt(ttpEl.value, 10);
        if (Number.isFinite(n)) r.target_tilt_position = n;
      }
    }
    const chips = (action, attr) => [...root.querySelectorAll(`[data-action="${action}"][data-rule="${id}"].selected`)].map(el => el.dataset[attr]);
    r.scenario_ids = chips("rule-scenario-toggle", "scenario");
    r.facade_ids = chips("rule-facade-toggle", "facade");
    r.cover_ids = chips("rule-cover-toggle", "cover");
  }

  // True when the open rule's draft differs from the saved rule.
  _ruleDraftDirty() {
    const d = this._ruleDraft;
    if (!d) return false;
    const saved = (this._config && this._config.rules || {})[d.id];
    if (!saved) return false;
    this._syncRuleDraftFromDom();
    // Chip order is not meaningful
    const norm = (p) => JSON.stringify({ ...p, scenario_ids: [...p.scenario_ids].sort(), facade_ids: [...p.facade_ids].sort(), cover_ids: [...p.cover_ids].sort() });
    return norm(this._buildRulePayload(d.id, d.rule)) !== norm(this._buildRulePayload(d.id, saved));
  }

  // Run `then` after the user agreed to drop unsaved rule edits (if any).
  _confirmLeaveRule(then) {
    if (this._ruleDraftDirty()) this._showConfirm(this._t("rule_unsaved_confirm"), then, this._t("discard"));
    else then();
  }

  _buildRulePayload(ruleId, rule, overrideConditions = null, overrideGroups = null) {
    const groupInfo = this._ruleGroups(rule);
    let op = groupInfo.between;
    let groupOps = groupInfo.ops;
    if (overrideGroups) { groupOps = overrideGroups.ops; op = overrideGroups.between; }
    // scenario_ids null = member of every scenario (all chips selected)
    const scenarioIds = Array.isArray(rule.scenario_ids)
      ? [...rule.scenario_ids] : Object.values(this._config.scenarios || {}).map(sc => sc.id);
    const ttp = rule.target_tilt_position;
    // Conditions from override (pending add/delete) or the draft
    const source = overrideConditions ?? (rule.conditions || []);
    const conditions = source.map(c => ({
      type: c.type, params: c.params || {},
      group: Math.min(parseInt(c.group, 10) || 0, Math.max(groupOps.length - 1, 0)),
      negate: !!c.negate,
    }));
    return {
      rule_id: ruleId,
      name: String(rule.name ?? "").trim(),
      target_position: rule.target_position,
      target_tilt_position: Number.isFinite(ttp) ? ttp : null,
      condition_operator: op,
      group_operators: groupOps,
      scenario_ids: scenarioIds,
      facade_ids: [...(rule.facade_ids || [])],
      cover_ids: [...(rule.cover_ids || [])],
      safety: !!rule.safety,
      conditions: conditions
    };
  }

  // Payload of rule/update for the open editor (draft + DOM-only fields).
  _collectRuleEditorData(root, ruleId, overrideConditions = null, overrideGroups = null) {
    if (ruleId === this._expandedRule) this._syncRuleDraftFromDom();
    const rule = this._edRule(ruleId);
    if (!rule) return null;
    return this._buildRulePayload(ruleId, rule, overrideConditions, overrideGroups);
  }

}

customElements.define("cover-automatic-panel", CoverAutomaticPanel);
