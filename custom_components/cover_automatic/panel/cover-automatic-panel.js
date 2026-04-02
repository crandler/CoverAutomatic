/**
 * CoverAutomatic Config Panel
 * Home Assistant custom panel for intelligent cover/shutter automation.
 * Vanilla web component with Shadow DOM -- no external dependencies.
 */

/* ============================================================
 * i18n translations
 * ============================================================ */
const I18N = {
  en: {
    title: "CoverAutomatic",
    tabs: { covers: "Covers", facades: "Facades", rules: "Rules", scenarios: "Scenarios", settings: "Settings", log: "Log" },
    loading: "Loading configuration...",
    error_load: "Failed to load configuration.",
    retry: "Retry",
    saved: "Saved",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    confirm_delete: "Really delete?",
    add: "Add",
    edit: "Edit",
    close: "Close",
    none: "None",
    enabled: "Enabled",
    disabled: "Disabled",
    active: "Active",
    activate: "Activate",
    name: "Name",
    yes: "Yes",
    no: "No",
    // Covers
    cover_facade: "Facade",
    cover_facade_hint: "Determines which facade rules apply to this cover.",
    cover_status: "Status",
    cover_pause_duration: "Pause duration (min)",
    cover_pause_duration_hint: "How long automation pauses after manual operation. Empty = use global default.",
    cover_indoor_temp: "Indoor temperature sensor",
    cover_indoor_temp_hint: "Per-cover sensor for comfort mode. Overrides global sensor.",
    cover_lock_sensor: "Lock sensor",
    cover_lock_sensor_hint: "Window contact sensor. When open, cover moves to lock position (safety).",
    cover_lock_position: "Lock position",
    cover_lock_position_hint: "Target position when window is open. Empty = use global default.",
    cover_vent_sensor: "Vent sensor",
    cover_vent_sensor_hint: "Tilt contact sensor. When tilted, cover moves to vent position.",
    cover_vent_position: "Vent position",
    cover_vent_position_hint: "Target position when window is tilted. Empty = use global default.",
    cover_comfort_min: "Comfort temp min",
    cover_comfort_max: "Comfort temp max",
    cover_comfort_hint: "Per-room comfort range. Empty = use global values from settings.",
    cover_inverted: "Inverted",
    cover_inverted_hint: "Enable if 100% means closed (reversed motor direction).",
    cover_supports_tilt: "Supports tilt",
    cover_lock_tilt: "Lock tilt position",
    cover_vent_tilt: "Vent tilt position",
    cover_inverted_tilt: "Inverted tilt",
    cover_min_pos_change: "Min. position change",
    cover_min_pos_change_hint: "Minimum position difference to trigger a move. Empty = use global default.",
    cover_min_time: "Min. time between changes (s)",
    cover_min_time_hint: "Minimum seconds between position changes. Empty = use global default.",
    cover_section_base: "General",
    cover_section_sensors: "Sensors",
    cover_section_advanced: "Advanced",
    cover_section_tilt: "Tilt",
    cover_auto_enabled: "Automation enabled",
    cover_temp: "Temp",
    cover_current_pos: "Current",
    cover_target_pos: "Target",
    cover_hysteresis_position: "Position change too small",
    cover_hysteresis_time: "Too soon since last change",
    cover_rule: "Rule",
    cover_no_rule: "–",
    cover_resume: "Resume",
    cover_last_change: "Last change",
    cover_just_now: "just now",
    cover_minutes_ago: "min ago",
    cover_hours_ago: "h ago",
    comfort_cooling: "Cooling",
    comfort_heating: "Heating",
    comfort_neutral: "Neutral",
    cover_add: "Add covers",
    // Facades
    facade_direction: "Direction",
    facade_direction_hint: "Presets azimuth values with house rotation applied.",
    facade_azimuth_start: "Azimuth start",
    facade_azimuth_end: "Azimuth end",
    facade_azimuth_hint: "Real compass bearings where sun enters/exits this facade.",
    facade_min_elevation: "Min. elevation",
    facade_min_elevation_hint: "Minimum sun elevation for this facade to count as sun-exposed.",
    facade_covers: "Assigned covers",
    facade_add: "Add facade",
    facade_no_covers: "No covers assigned",
    facade_sun_active: "Sun on facade",
    facade_sun_inactive: "No sun",
    facade_sun_position: "Sun position",
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
    rule_facades: "Facades",
    rule_covers: "Covers",
    rule_assignment_hint: "Limit this rule to specific facades/covers. Empty = applies to all covers.",
    rule_add: "Add rule",
    rule_add_condition: "Add condition",
    rule_no_conditions: "No conditions",
    rule_reorder_hint: "Drag to reorder. Top rule wins when multiple rules match.",
    // Condition types
    cond_sun_on_facade: "Sun on facade",
    cond_sun_elevation_above: "Sun elevation above",
    cond_sun_elevation_below: "Sun elevation below",
    cond_temperature_above: "Outdoor temperature above",
    cond_temperature_below: "Outdoor temperature below",
    cond_temperature_comfort: "Temperature comfort",
    cond_time_between: "Time between",
    cond_time_after_sunrise: "Time after sunrise",
    cond_time_after_sunset: "Time after sunset",
    cond_state_is: "State is",
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
    param_state: "State",
    param_weather: "Weather condition",
    param_mode: "Mode",
    param_days: "Days",
    param_select_type: "Select condition type",
    day_mon: "Mon", day_tue: "Tue", day_wed: "Wed", day_thu: "Thu", day_fri: "Fri", day_sat: "Sat", day_sun: "Sun",
    opt_on: "On (workday)", opt_off: "Off (non-workday)",
    opt_cooling: "Cooling", opt_heating: "Heating",
    // Scenarios
    scenario_add: "Add scenario",
    scenario_icon: "Icon (mdi:...)",
    scenario_rules_disabled: "Disabled rules",
    scenario_active: "Active scenario",
    scenario_no_rules: "No rules configured",
    // Settings
    settings_outdoor_temp: "Outdoor temperature sensor",
    settings_outdoor_temp_hint: "Used for temperature-based rule conditions (temperature above/below).",
    settings_indoor_temp: "Indoor temperature sensor (global)",
    settings_indoor_temp_hint: "Fallback for covers without their own indoor sensor. Used for comfort mode and shading decisions.",
    settings_weather: "Weather entity",
    settings_weather_hint: "Used for weather-based rule conditions (e.g. only shade when sunny).",
    settings_comfort_min: "Comfort temp min",
    settings_comfort_max: "Comfort temp max",
    settings_comfort_hint: "Defines the comfort range. Below min = heating mode (shading off, use solar heat). Above max = cooling mode (shading active). Between = neutral (keep current position).",
    settings_comfort_hysteresis: "Hysteresis",
    settings_comfort_hysteresis_hint: "Temperature buffer at comfort boundaries to prevent oscillation between modes (e.g. 1.0 = mode only changes 1 degree past threshold).",
    settings_house_rotation: "House rotation (degrees)",
    settings_house_rotation_hint: "Offset from true north (-180 to 180, positive = clockwise). Applied automatically when selecting a facade direction.",
    settings_section_house: "House",
    settings_section_sensors: "Sensors",
    settings_section_comfort: "Comfort",
    settings_section_automation: "Automation",
    settings_pause_duration: "Default pause duration (min)",
    settings_pause_duration_hint: "How long automation pauses after manual cover operation. Can be overridden per cover.",
    settings_lock_position: "Default lock position",
    settings_lock_position_hint: "Target position when window is open (100 = fully open). Can be overridden per cover.",
    settings_lock_tilt_position: "Default lock tilt",
    settings_lock_tilt_position_hint: "Tilt position when window is open. Leave empty to skip tilt control.",
    settings_vent_position: "Default vent position",
    settings_vent_position_hint: "Target position when window is tilted (e.g. 30 for ventilation gap). Can be overridden per cover.",
    settings_vent_tilt_position: "Default vent tilt",
    settings_vent_tilt_position_hint: "Tilt position when window is tilted. Leave empty to skip tilt control.",
    settings_min_position_change: "Default min. position change",
    settings_min_position_change_hint: "Minimum position difference to trigger a move. Can be overridden per cover.",
    settings_min_time: "Default min. time between changes (s)",
    settings_min_time_hint: "Minimum seconds between position changes (motor protection). Can be overridden per cover.",
    settings_entity_placeholder: "e.g. sensor.outdoor_temperature",
    settings_current_value: "Current",
    settings_validation_min_max: "Min must be less than max",
    settings_section_workday: "Workday sensor",
    settings_workday_sensor: "Workday sensor",
    settings_workday_hint: "Binary sensor for workday detection (e.g. HA Workday integration). Used by the 'workday' condition type in rules.",
    settings_section_wind: "Wind protection",
    settings_wind_hint: "Safety feature: raises all covers when wind speed exceeds the threshold. Deactivates when speed drops below threshold minus hysteresis.",
    settings_wind_sensor: "Wind speed sensor",
    settings_wind_threshold: "Threshold (activation)",
    settings_wind_hysteresis: "Hysteresis (deactivation difference)",
    status_auto: "Auto",
    status_paused: "Paused",
    status_manual: "Manual",
    status_locked: "Locked",
    status_venting: "Venting",
    status_wind_protected: "Wind protected",
    rule_active_for: "Active for",
    rule_covers_count: "cover(s)",
    rule_inactive: "Not matching",
    master_enabled: "Automation",
    master_enabled_hint: "Lock and vent protection remain active even when automation is disabled.",
    log_time: "Time",
    log_event: "Event",
    log_cover: "Cover",
    log_message: "Details",
    log_type_position: "Position",
    log_type_status: "Status",
    log_type_rule: "Rule",
    log_type_wind: "Wind",
    log_loading: "Loading log...",
    log_empty: "No log entries in the last 3 days.",
    log_filter_all: "All",
    settings_section_backup: "Backup",
    settings_backup_hint: "Export the complete configuration as a JSON file. Import replaces all settings, covers, facades, rules, and scenarios.",
    settings_export: "Export configuration",
    settings_import: "Import configuration",
    settings_import_confirm: "This will replace the entire configuration. Continue?",
    settings_import_success: "Configuration imported successfully.",
    settings_import_error: "Import failed",
    settings_export_error: "Export failed",
  },
  de: {
    title: "CoverAutomatic",
    tabs: { covers: "Behänge", facades: "Fassaden", rules: "Regeln", scenarios: "Szenarien", settings: "Einstellungen", log: "Protokoll" },
    loading: "Konfiguration wird geladen...",
    error_load: "Konfiguration konnte nicht geladen werden.",
    retry: "Erneut versuchen",
    saved: "Gespeichert",
    save: "Speichern",
    cancel: "Abbrechen",
    delete: "Löschen",
    confirm_delete: "Wirklich löschen?",
    add: "Hinzufügen",
    edit: "Bearbeiten",
    close: "Schließen",
    none: "Keine",
    enabled: "Aktiviert",
    disabled: "Deaktiviert",
    active: "Aktiv",
    activate: "Aktivieren",
    name: "Name",
    yes: "Ja",
    no: "Nein",
    cover_facade: "Fassade",
    cover_facade_hint: "Bestimmt, welche Fassadenregeln für diesen Behang gelten.",
    cover_status: "Status",
    cover_pause_duration: "Pausendauer (Min.)",
    cover_pause_duration_hint: "Wie lange die Automatik nach manueller Bedienung pausiert. Leer = globaler Standard.",
    cover_indoor_temp: "Innentemperatur-Sensor",
    cover_indoor_temp_hint: "Sensor für den Komfortmodus dieses Behangs. Überschreibt den globalen Sensor.",
    cover_lock_sensor: "Sperr-Sensor",
    cover_lock_sensor_hint: "Fensterkontakt. Bei geöffnetem Fenster fährt der Behang auf Sperrposition (Sicherheit).",
    cover_lock_position: "Sperrposition",
    cover_lock_position_hint: "Zielposition bei geöffnetem Fenster. Leer = globaler Standard.",
    cover_vent_sensor: "Lüftungssensor",
    cover_vent_sensor_hint: "Kippkontakt. Bei gekipptem Fenster fährt der Behang auf Lüftungsposition.",
    cover_vent_position: "Lüftungsposition",
    cover_vent_position_hint: "Zielposition bei gekipptem Fenster. Leer = globaler Standard.",
    cover_comfort_min: "Komfort-Temp. min",
    cover_comfort_max: "Komfort-Temp. max",
    cover_comfort_hint: "Komfortbereich pro Raum. Leer = globale Werte aus Einstellungen.",
    cover_inverted: "Invertiert",
    cover_inverted_hint: "Aktivieren, wenn 100 % geschlossen bedeutet (umgekehrte Motorrichtung).",
    cover_supports_tilt: "Unterstützt Tilt",
    cover_lock_tilt: "Sperr-Tiltposition",
    cover_vent_tilt: "Lüftungs-Tiltposition",
    cover_inverted_tilt: "Invertierter Tilt",
    cover_min_pos_change: "Min. Positionsänderung",
    cover_min_pos_change_hint: "Mindestabweichung für eine Fahrt. Leer = globaler Standard.",
    cover_min_time: "Min. Zeit zwischen Änderungen (s)",
    cover_min_time_hint: "Mindestabstand in Sekunden zwischen Positionsänderungen. Leer = globaler Standard.",
    cover_section_base: "Allgemein",
    cover_section_sensors: "Sensoren",
    cover_section_advanced: "Erweitert",
    cover_section_tilt: "Tilt",
    cover_auto_enabled: "Automatik aktiviert",
    cover_temp: "Temp",
    cover_current_pos: "Ist",
    cover_target_pos: "Soll",
    cover_hysteresis_position: "Positionsänderung zu gering",
    cover_hysteresis_time: "Zu kurz seit letzter Änderung",
    cover_rule: "Regel",
    cover_no_rule: "–",
    cover_resume: "Fortsetzen",
    cover_last_change: "Letzte Änderung",
    cover_just_now: "gerade",
    cover_minutes_ago: "Min.",
    cover_hours_ago: "Std.",
    comfort_cooling: "Kühlen",
    comfort_heating: "Heizen",
    comfort_neutral: "Neutral",
    cover_add: "Behänge hinzufügen",
    facade_direction: "Richtung",
    facade_direction_hint: "Setzt Azimutwerte mit Hausrotation automatisch.",
    facade_azimuth_start: "Azimut Start",
    facade_azimuth_end: "Azimut Ende",
    facade_azimuth_hint: "Echte Kompasspeilungen, an denen die Sonne die Fassade erreicht/verlässt.",
    facade_min_elevation: "Min. Elevation",
    facade_min_elevation_hint: "Minimale Sonnenhöhe, damit diese Fassade als besonnt gilt.",
    facade_covers: "Zugewiesene Behänge",
    facade_add: "Fassade hinzufügen",
    facade_no_covers: "Keine Behänge zugewiesen",
    facade_sun_active: "Sonne auf Fassade",
    facade_sun_inactive: "Keine Sonne",
    facade_sun_position: "Sonnenposition",
    facade_dir_north: "Norden",
    facade_dir_east: "Osten",
    facade_dir_south: "Süden",
    facade_dir_west: "Westen",
    rule_priority: "Priorität",
    rule_target_pos: "Zielposition",
    rule_target_pos_hint: "Position bei Regelübereinstimmung (0 = geschlossen, 100 = offen).",
    rule_target_tilt: "Ziel-Tiltposition",
    rule_operator: "Bedingungsoperator",
    rule_operator_hint: "UND = alle Bedingungen müssen zutreffen. ODER = eine reicht.",
    rule_operator_and: "UND (alle müssen zutreffen)",
    rule_operator_or: "ODER (eine muss zutreffen)",
    rule_conditions: "Bedingungen",
    rule_facades: "Fassaden",
    rule_covers: "Behänge",
    rule_assignment_hint: "Regel auf bestimmte Fassaden/Behänge beschränken. Leer = gilt für alle.",
    rule_add: "Regel hinzufügen",
    rule_add_condition: "Bedingung hinzufügen",
    rule_no_conditions: "Keine Bedingungen",
    rule_reorder_hint: "Ziehen zum Sortieren. Obere Regel gewinnt bei Überschneidung.",
    cond_sun_on_facade: "Sonne auf Fassade",
    cond_sun_elevation_above: "Sonnenhöhe über",
    cond_sun_elevation_below: "Sonnenhöhe unter",
    cond_temperature_above: "Außentemperatur über",
    cond_temperature_below: "Außentemperatur unter",
    cond_temperature_comfort: "Temperatur Komfort",
    cond_time_between: "Zeit zwischen",
    cond_time_after_sunrise: "Zeit nach Sonnenaufgang",
    cond_time_after_sunset: "Zeit nach Sonnenuntergang",
    cond_state_is: "Status ist",
    cond_weather_is: "Wetter ist",
    cond_day_of_week: "Wochentag",
    cond_workday: "Arbeitstag-Sensor",
    param_elevation: "Elevation",
    param_temperature: "Temperatur",
    param_start_time: "Startzeit",
    param_end_time: "Endzeit",
    param_offset: "Offset (Min.)",
    param_entity_id: "Entity-ID",
    param_state: "Status",
    param_weather: "Wetterbedingung",
    param_mode: "Modus",
    param_days: "Tage",
    param_select_type: "Bedingungstyp wählen",
    day_mon: "Mo", day_tue: "Di", day_wed: "Mi", day_thu: "Do", day_fri: "Fr", day_sat: "Sa", day_sun: "So",
    opt_on: "An (Arbeitstag)", opt_off: "Aus (kein Arbeitstag)",
    opt_cooling: "Kühlung", opt_heating: "Heizung",
    scenario_add: "Szenario hinzufügen",
    scenario_icon: "Icon (mdi:...)",
    scenario_rules_disabled: "Deaktivierte Regeln",
    scenario_active: "Aktives Szenario",
    scenario_no_rules: "Keine Regeln konfiguriert",
    settings_outdoor_temp: "Außentemperatur-Sensor",
    settings_outdoor_temp_hint: "Wird für temperaturbasierte Regelbedingungen verwendet (Außentemperatur über/unter).",
    settings_indoor_temp: "Innentemperatur-Sensor (global)",
    settings_indoor_temp_hint: "Fallback für Behänge ohne eigenen Innensensor. Wird für Komfortmodus und Beschattungsentscheidungen verwendet.",
    settings_weather: "Wetter-Entität",
    settings_weather_hint: "Wird für wetterbasierte Regelbedingungen verwendet (z. B. nur beschatten bei Sonne).",
    settings_comfort_min: "Komfort-Temp. min",
    settings_comfort_max: "Komfort-Temp. max",
    settings_comfort_hint: "Definiert den Komfortbereich. Unter min = Heizmodus (keine Beschattung, Sonnenwärme nutzen). Über max = Kühlmodus (Beschattung aktiv). Dazwischen = Neutral (Position beibehalten).",
    settings_comfort_hysteresis: "Hysterese",
    settings_comfort_hysteresis_hint: "Temperaturpuffer an Komfortgrenzen, um Pendeln zwischen Modi zu verhindern (z. B. 1,0 = Moduswechsel erst 1 Grad jenseits des Schwellwerts).",
    settings_house_rotation: "Hausrotation (Grad)",
    settings_house_rotation_hint: "Abweichung von exakt Nord (-180 bis 180, positiv = im Uhrzeigersinn). Wird automatisch bei der Fassaden-Richtungswahl angewendet.",
    settings_section_house: "Haus",
    settings_section_sensors: "Sensoren",
    settings_section_comfort: "Komfort",
    settings_section_automation: "Automatik",
    settings_pause_duration: "Standard-Pausendauer (Min.)",
    settings_pause_duration_hint: "Wie lange die Automatik nach manueller Bedienung pausiert. Kann pro Behang überschrieben werden.",
    settings_lock_position: "Standard-Sperrposition",
    settings_lock_position_hint: "Zielposition bei geöffnetem Fenster (100 = offen). Kann pro Behang überschrieben werden.",
    settings_lock_tilt_position: "Standard-Sperr-Lamelle",
    settings_lock_tilt_position_hint: "Lamellenposition bei geöffnetem Fenster. Leer lassen = keine Lamellensteuerung.",
    settings_vent_position: "Standard-Lüftungsposition",
    settings_vent_position_hint: "Zielposition bei gekipptem Fenster (z. B. 30). Kann pro Behang überschrieben werden.",
    settings_vent_tilt_position: "Standard-Lüftungs-Lamelle",
    settings_vent_tilt_position_hint: "Lamellenposition bei gekipptem Fenster. Leer lassen = keine Lamellensteuerung.",
    settings_min_position_change: "Standard min. Positionsänderung",
    settings_min_position_change_hint: "Mindestabweichung für eine Fahrt. Kann pro Behang überschrieben werden.",
    settings_min_time: "Standard min. Zeit zwischen Änderungen (s)",
    settings_min_time_hint: "Mindestabstand in Sekunden zwischen Positionsänderungen (Motorschutz). Kann pro Behang überschrieben werden.",
    settings_entity_placeholder: "z. B. sensor.außentemperatur",
    settings_current_value: "Aktuell",
    settings_validation_min_max: "Min muss kleiner als Max sein",
    settings_section_workday: "Arbeitstag-Sensor",
    settings_workday_sensor: "Arbeitstag-Sensor",
    settings_workday_hint: "Binärsensor zur Arbeitstag-Erkennung (z. B. HA Workday-Integration). Wird vom Bedingungstyp 'Arbeitstag-Sensor' in Regeln verwendet.",
    settings_section_wind: "Windschutz",
    settings_wind_hint: "Sicherheitsfeature: Fährt alle Behänge hoch, wenn die Windgeschwindigkeit den Schwellwert überschreitet. Deaktiviert sich, wenn die Geschwindigkeit unter Schwellwert minus Hysterese fällt.",
    settings_wind_sensor: "Windgeschwindigkeits-Sensor",
    settings_wind_threshold: "Schwellwert (Aktivierung)",
    settings_wind_hysteresis: "Hysterese (Deaktivierungsdifferenz)",
    status_auto: "Auto",
    status_paused: "Pausiert",
    status_manual: "Manuell",
    status_locked: "Gesperrt",
    status_venting: "Lüften",
    status_wind_protected: "Windschutz",
    rule_active_for: "Aktiv für",
    rule_covers_count: "Behang/Behänge",
    rule_inactive: "Nicht aktiv",
    master_enabled: "Automatik",
    master_enabled_hint: "Sperr- und Lüftungsschutz bleiben auch bei deaktivierter Automatik aktiv.",
    log_time: "Zeit",
    log_event: "Ereignis",
    log_cover: "Behang",
    log_message: "Details",
    log_type_position: "Position",
    log_type_status: "Status",
    log_type_rule: "Regel",
    log_type_wind: "Wind",
    log_loading: "Protokoll wird geladen...",
    log_empty: "Keine Einträge in den letzten 3 Tagen.",
    log_filter_all: "Alle",
    settings_section_backup: "Backup",
    settings_backup_hint: "Exportiere die gesamte Konfiguration als JSON-Datei. Der Import ersetzt alle Einstellungen, Behänge, Fassaden, Regeln und Szenarien.",
    settings_export: "Konfiguration exportieren",
    settings_import: "Konfiguration importieren",
    settings_import_confirm: "Die gesamte Konfiguration wird ersetzt. Fortfahren?",
    settings_import_success: "Konfiguration erfolgreich importiert.",
    settings_import_error: "Import fehlgeschlagen",
    settings_export_error: "Export fehlgeschlagen",
  }
};

/* ============================================================
 * Condition type metadata
 * ============================================================ */
const CONDITION_TYPES = [
  "sun_on_facade", "sun_elevation_above", "sun_elevation_below",
  "temperature_above", "temperature_below", "temperature_comfort",
  "time_between", "time_after_sunrise", "time_after_sunset",
  "state_is", "weather_is", "day_of_week", "workday"
];

const CONDITION_PARAMS = {
  sun_on_facade: [],
  sun_elevation_above: [{ key: "elevation", type: "number", default: 10, step: 0.5 }],
  sun_elevation_below: [{ key: "elevation", type: "number", default: 60, step: 0.5 }],
  temperature_above: [{ key: "temperature", type: "number", default: 25 }],
  temperature_below: [{ key: "temperature", type: "number", default: 15 }],
  temperature_comfort: [{ key: "mode", type: "select", options: ["cooling", "heating"], default: "cooling" }],
  time_between: [
    { key: "start_time", type: "time", default: "08:00" },
    { key: "end_time", type: "time", default: "20:00" }
  ],
  time_after_sunrise: [{ key: "offset", type: "number", default: 0 }],
  time_after_sunset: [{ key: "offset", type: "number", default: 0 }],
  state_is: [
    { key: "entity_id", type: "text", default: "" },
    { key: "state", type: "text", default: "on" }
  ],
  weather_is: [{ key: "weather", type: "multiselect", options: ["sunny", "cloudy", "partlycloudy", "rainy", "snowy", "windy", "fog", "clear-night"], default: ["sunny"] }],
  day_of_week: [{ key: "days", type: "dayselect", default: ["mon","tue","wed","thu","fri"] }],
  workday: [{ key: "state", type: "select", options: ["on", "off"], default: "on" }]
};

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
    --ca-card-bg: var(--ha-card-background, var(--card-background-color, #fff));
    --ca-border: var(--divider-color, #e0e0e0);
    --ca-secondary-text: var(--secondary-text-color, #727272);
    --ca-error: var(--error-color, #db4437);
    --ca-success: #43a047;
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
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0 8px;
    margin-bottom: 8px;
  }
  .panel-header h1 {
    font-size: 24px;
    font-weight: 500;
    margin: 0;
    letter-spacing: -0.5px;
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
  .version-info {
    font-size: 12px;
    color: var(--ca-secondary-text);
    opacity: 0.7;
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
  }
  .tab-bar button {
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
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
  }

  /* Table */
  .data-table {
    width: 100%;
    border-collapse: collapse;
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
  }
  .data-table tr {
    cursor: pointer;
    transition: background var(--ca-transition);
  }
  .data-table tbody tr:hover {
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.06);
  }
  .data-table tbody tr.selected {
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.12);
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
  .status-auto { background: #e8f5e9; color: #2e7d32; }
  .status-paused { background: #fff3e0; color: #e65100; }
  .status-manual { background: #e3f2fd; color: #1565c0; }
  .status-locked { background: #fce4ec; color: #c62828; }
  .status-wind_protected { background: #fce4ec; color: #c62828; }

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
    background: var(--ca-card-bg);
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
  .slide-header h2 {
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
    font-size: 12px;
    font-weight: 500;
    color: var(--ca-secondary-text);
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
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
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
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
  }
  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 0;
    cursor: pointer;
    user-select: none;
    font-size: 13px;
    font-weight: 600;
    color: var(--ca-secondary-text);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .section-header .arrow {
    font-size: 10px;
    transition: transform var(--ca-transition);
    display: inline-block;
  }
  .section-header .arrow.expanded { transform: rotate(90deg); }
  .section-body {
    overflow: hidden;
    max-height: 0;
    transition: max-height 0.35s ease;
  }
  .section-body.expanded { max-height: 800px; }

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
    border-radius: var(--ca-radius);
    margin-bottom: 8px;
    background: var(--ca-card-bg);
    transition: all var(--ca-transition);
  }
  .rule-row:hover { box-shadow: var(--ca-shadow); }
  .rule-row.drag-over {
    border-color: var(--ca-primary);
    box-shadow: 0 0 0 2px rgba(var(--rgb-primary-color, 3, 169, 244), 0.3);
  }
  .rule-row.dragging { opacity: 0.4; }
  .rule-info { flex: 1; min-width: 0; }
  .rule-name { font-weight: 500; font-size: 15px; display: flex; align-items: center; gap: 6px; }
  .rule-active-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    background: var(--ca-divider, #e0e0e0);
    transition: background 0.2s;
  }
  .rule-active-dot.active { background: #4caf50; }
  .rule-meta {
    font-size: 12px;
    color: var(--ca-secondary-text);
    margin-top: 2px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
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
  .day-select { display: flex; gap: 4px; flex-wrap: wrap; }
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
    border-color: var(--ca-primary);
    box-shadow: 0 0 0 3px rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
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
  }
  .toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
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
    background: rgba(0,0,0,0.4);
    z-index: 300;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .confirm-dialog {
    background: var(--ca-card-bg);
    border-radius: var(--ca-radius);
    padding: 24px;
    min-width: 300px;
    max-width: 90vw;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
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

  /* Responsive */
  @media (max-width: 768px) {
    .panel-container { padding: 8px; }
    .card-grid { grid-template-columns: 1fr; }
    .slide-panel { width: 100vw; }
    .form-row { grid-template-columns: 1fr; }
    .tab-bar button { padding: 10px 14px; font-size: 13px; }
    .data-table th, .data-table td { padding: 10px 12px; font-size: 13px; }
    .condition-card .cond-params { grid-template-columns: 1fr; }
  }
`;

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
    this._liveRefreshTimer = null;
    this._expandedSections = { base: true, sensors: true, advanced: false, tilt: false };


    this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
      return;
    }
    if (this._config && this._activeTab === "covers") {
      this._updateLiveCells();
    }
  }

  set panel(panel) {
    this._panel = panel;
  }

  disconnectedCallback() {
    this._stopLiveRefresh();
  }

  /* ---------- i18n helper ---------- */
  _t(key) {
    const lang = (this._hass && this._hass.language) || "en";
    const dict = I18N[lang] || I18N.en;
    return dict[key] !== undefined ? dict[key] : (I18N.en[key] !== undefined ? I18N.en[key] : key);
  }

  _tt(section, key) {
    const lang = (this._hass && this._hass.language) || "en";
    const dict = I18N[lang] || I18N.en;
    const s = dict[section] || I18N.en[section] || {};
    return s[key] !== undefined ? s[key] : ((I18N.en[section] || {})[key] || key);
  }

  _hint(key) {
    const text = this._t(key);
    return text !== key ? `<div style="font-size:12px;color:var(--ca-secondary-text);margin-top:4px">${text}</div>` : "";
  }

  /* ---------- Lifecycle ---------- */
  _initialize() {
    this._initialized = true;
    this._loadConfig();
  }

  /* ---------- WebSocket calls ---------- */
  async _ws(type, data) {
    if (!this._hass) return null;
    try {
      const msg = Object.assign({ type: type }, data || {});
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
    try {
      const resp = await fetch("https://api.github.com/repos/crandler/CoverAutomatic/releases/latest", { headers: { Accept: "application/vnd.github.v3+json" } });
      if (!resp.ok) return;
      const data = await resp.json();
      const latest = (data.tag_name || "").replace(/^v/, "");
      if (latest && latest !== this._config.version) {
        this._latestVersion = latest;
        this._updateRegion(this.shadowRoot.querySelector(".panel-container"), "header", this._renderHeaderContent());
      }
    } catch (e) { /* silent */ }
  }

  _updateConfigFromResult(result) {
    if (result) {
      this._config = result;
      this._showToast();
      this._render();
    }
  }

  /* ---------- Debounced save for covers ---------- */
  _debouncedCoverSave(entityId, field, value) {
    const key = entityId + "." + field;
    if (this._saveTimers[key]) clearTimeout(this._saveTimers[key]);
    this._saveTimers[key] = setTimeout(async () => {
      try {
        const data = { entity_id: entityId };
        data[field] = value;
        const result = await this._ws("cover_automatic/cover/update", data);
        this._updateConfigFromResult(result);
      } catch (e) {
        console.error("Save error:", e);
      }
    }, 500);
  }

  /* ---------- Toast ---------- */
  _showToast() {
    if (this._toastTimer) clearTimeout(this._toastTimer);
    const toast = this.shadowRoot.querySelector(".toast");
    if (toast) {
      toast.classList.add("show");
      this._toastTimer = setTimeout(() => toast.classList.remove("show"), 2000);
    }
  }

  /* ---------- Confirm dialog ---------- */
  _showConfirm(message, callback) {
    this._confirmMessage = message;
    this._confirmCallback = callback;
    this._render();
  }

  _hideConfirm() {
    this._confirmMessage = "";
    this._confirmCallback = null;
    this._render();
  }

  /* ---------- Main render ---------- */
  _render() {
    const root = this.shadowRoot;

    // Full render when no shell exists, loading/error, or shell has no regions yet
    const shell = root.querySelector(".panel-container");
    if (!shell || !this._config || this._error || !shell.querySelector("[data-region]")) {
      this._fullRender();
      return;
    }

    // Partial render: update regions individually
    this._updateRegion(shell, "header", this._renderHeaderContent());
    this._updateRegion(shell, "tabs", this._renderTabsContent());
    this._updateRegion(shell, "content", this._renderContent());
    this._updateRegion(shell, "slideout", this._renderSlideOut());
    this._updateRegion(shell, "confirm", this._renderConfirmDialog());
  }

  _updateRegion(shell, name, html) {
    const el = shell.querySelector('[data-region="' + name + '"]');
    if (el) el.innerHTML = html;
  }

  _fullRender() {
    const root = this.shadowRoot;

    let html = '<style>' + PANEL_STYLES + '</style>';
    html += '<div class="panel-container">';

    if (!this._config && !this._error) {
      html += '<div class="state-msg"><div class="spinner"></div><div>' + this._t("loading") + '</div></div>';
      html += '</div>';
      root.innerHTML = html;
      this._setupDelegation();
      return;
    }

    if (this._error) {
      html += '<div class="state-msg">';
      html += '<div style="font-size:32px;margin-bottom:12px">!</div>';
      html += '<div>' + this._t("error_load") + '</div>';
      html += '<button class="btn btn-primary" style="margin-top:16px" data-action="retry">' + this._t("retry") + '</button>';
      html += '</div></div>';
      root.innerHTML = html;
      this._setupDelegation();
      return;
    }

    html += '<div class="panel-header" data-region="header">' + this._renderHeaderContent() + '</div>';
    html += '<div class="tab-bar" data-region="tabs">' + this._renderTabsContent() + '</div>';
    html += '<div class="tab-content" data-region="content">' + this._renderContent() + '</div>';
    html += '<div data-region="slideout">' + this._renderSlideOut() + '</div>';
    html += '<div data-region="confirm">' + this._renderConfirmDialog() + '</div>';
    html += '</div>';
    html += '<div class="toast">' + this._t("saved") + '</div>';

    root.innerHTML = html;
    this._setupDelegation();
  }

  _renderHeaderContent() {
    const activeScenario = this._getActiveScenario();
    const version = this._config ? this._config.version : "";
    const enabled = this._config ? this._config.enabled !== false : true;
    let html = '<div><h1 style="display:inline">' + this._t("title") + '</h1>';
    if (version) html += ' <span class="version-info">v' + this._esc(version) + '</span>';
    html += '</div><div style="display:flex;align-items:center;gap:8px">';
    if (this._latestVersion) {
      html += '<a class="update-badge" href="https://github.com/crandler/CoverAutomatic/releases/tag/v' + this._esc(this._latestVersion) + '" target="_blank" rel="noopener">Update: v' + this._esc(this._latestVersion) + '</a>';
    }
    if (activeScenario) {
      html += '<span class="scenario-badge">' + (activeScenario.icon ? '<ha-icon icon="' + this._esc(activeScenario.icon) + '" style="--mdc-icon-size:16px;margin-right:4px"></ha-icon>' : '') + this._esc(activeScenario.name) + '</span>';
    }
    html += '<div class="master-switch" title="' + this._t("master_enabled_hint") + '">';
    html += '<span class="master-label">' + this._t("master_enabled") + '</span>';
    html += '<label class="master-toggle">';
    html += '<input type="checkbox" ' + (enabled ? 'checked ' : '') + 'data-action="master-toggle">';
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
      const active = this._activeTab === tab ? " active" : "";
      html += '<button class="' + active + '" data-tab="' + tab + '">' + this._tt("tabs", tab) + '</button>';
    }
    return html;
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
      + '<div class="confirm-dialog">'
      + '<p>' + this._esc(this._confirmMessage) + '</p>'
      + '<div class="actions">'
      + '<button class="btn btn-secondary" data-action="confirm-cancel">' + this._t("cancel") + '</button>'
      + '<button class="btn btn-danger" data-action="confirm-ok">' + this._t("delete") + '</button>'
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
        html += '<div class="card" style="margin-bottom:16px"><div class="card-header">';
        html += `<span>${this._t("cover_add")}</span>`;
        html += `<button class="btn-icon" data-action="cover-add-cancel" title="${this._t("cancel")}">&#10005;</button>`;
        html += '</div>';
        html += '<div class="card-body"><div class="form-row">';
        html += `<select id="cover-add-select" multiple style="width:100%;min-height:80px;padding:8px;border:1px solid var(--divider-color);border-radius:6px;background:var(--ha-card-background,var(--card-background-color));color:var(--primary-text-color)">`;
        for (const a of available) {
          html += `<option value="${this._esc(a.entity_id)}">${this._esc(a.name)} (${this._esc(a.entity_id)})</option>`;
        }
        html += '</select></div>';
        html += `<div class="form-row" style="margin-top:8px"><button class="btn btn-primary" data-action="cover-add">${this._t("add")}</button></div>`;
        html += '</div></div>';
      } else {
        html += `<div style="margin-bottom:12px"><button class="btn btn-sm" data-action="cover-add-start">+ ${this._t("cover_add")}</button></div>`;
      }
    }

    if (entries.length === 0 && !this._addingCover) {
      return html + `<div class="empty-state">${this._t("none")}</div>`;
    }

    html += '<div class="card"><div style="overflow-x:auto"><table class="data-table">';
    html += '<thead><tr>';
    html += `<th>${this._t("name")}</th>`;
    html += `<th>${this._t("cover_facade")}</th>`;
    html += `<th>${this._t("cover_status")}</th>`;
    html += `<th>${this._t("cover_temp")}</th>`;
    html += `<th>${this._t("cover_current_pos")}</th>`;
    html += `<th>${this._t("cover_target_pos")}</th>`;
    html += `<th>${this._t("cover_rule")}</th>`;
    html += `<th>${this._t("cover_last_change")}</th>`;
    html += '<th></th>';
    html += '</tr></thead><tbody>';

    for (const c of entries) {
      const facadeName = this._getFacadeName(c.facade_id);
      const selected = this._selectedCover === c.entity_id ? " selected" : "";
      const statusClass = "status-" + (c.status || "auto");
      const haState = this._hass && this._hass.states ? this._hass.states[c.entity_id] : null;
      const currentPos = haState && haState.attributes ? haState.attributes.current_position : null;
      const live = (this._config.live_covers || {})[c.entity_id] || {};
      const targetPos = live.target_position;
      const hysteresis = live.hysteresis;
      let infoIcon = '';
      if (hysteresis === "position") {
        infoIcon = ' <span class="status-badge status-paused" title="' + this._esc(this._t("cover_hysteresis_position")) + '" style="font-size:11px">&#8597;</span>';
      } else if (hysteresis === "time") {
        infoIcon = ' <span class="status-badge status-paused" title="' + this._esc(this._t("cover_hysteresis_time")) + '" style="font-size:11px">&#9202;</span>';
      }
      // Comfort mode icon
      const cm = live.comfort_mode;
      let comfortIcon = '';
      if (cm === "cooling") comfortIcon = '<span title="' + this._esc(this._t("comfort_cooling")) + '" style="font-size:12px;margin-left:2px">\u2744</span>';
      else if (cm === "heating") comfortIcon = '<span title="' + this._esc(this._t("comfort_heating")) + '" style="font-size:12px;margin-left:2px">\u2600</span>';
      else if (cm === "neutral") comfortIcon = '<span title="' + this._esc(this._t("comfort_neutral")) + '" style="font-size:12px;margin-left:2px">\u25CF</span>';
      // Rule name
      const ruleName = live.rule_name || this._t("cover_no_rule");
      // Sun on facade
      const liveFacade = c.facade_id ? ((this._config.live_facades || {})[c.facade_id] || {}) : {};
      const sunIcon = liveFacade.sun_on_facade ? ' <span title="' + this._esc(this._t("facade_sun_active")) + '" style="font-size:12px">\u2600</span>' : '';
      // Last change
      const lastChange = live.last_change ? this._formatTimeAgo(live.last_change) : "";
      // Pause info
      const pauseLeft = (c.status === "paused" && live.pause_until) ? this._formatPauseRemaining(live.pause_until) : "";
      const resumeBtn = c.status === "paused" ? ' <button class="btn-sm" data-action="cover-resume" data-id="' + this._esc(c.entity_id) + '" style="font-size:10px;padding:1px 6px">' + this._t("cover_resume") + '</button>' : '';
      html += `<tr class="${selected}">`;
      html += `<td data-action="select-cover" data-id="${this._esc(c.entity_id)}" data-live-name="${this._esc(c.entity_id)}" style="cursor:pointer">${this._esc(c.name)}${comfortIcon}</td>`;
      html += `<td data-action="select-cover" data-id="${this._esc(c.entity_id)}" data-live-facade="${this._esc(c.entity_id)}" style="cursor:pointer">${this._esc(facadeName)}${sunIcon}</td>`;
      html += `<td data-live-status="${this._esc(c.entity_id)}"><span class="status-badge ${statusClass}">${this._esc(this._t("status_" + (c.status || "auto")) || c.status || "auto")}</span>${pauseLeft ? '<span class="pause-remaining" style="font-size:11px;color:var(--ca-secondary-text);margin-left:4px">' + pauseLeft + '</span>' : ''}${resumeBtn}</td>`;
      const tempSensor = c.indoor_temp_sensor || (this._config.settings || {}).indoor_temp_sensor;
      const tempState = tempSensor && this._hass && this._hass.states ? this._hass.states[tempSensor] : null;
      const tempVal = tempState && tempState.state !== "unavailable" && tempState.state !== "unknown" ? parseFloat(tempState.state) : null;
      html += `<td data-live-temp="${this._esc(c.entity_id)}" style="white-space:nowrap">${tempVal != null ? tempVal.toFixed(1) + " °C" : "–"}</td>`;
      html += `<td data-live-current="${this._esc(c.entity_id)}">${currentPos != null ? currentPos + "%" : "–"}</td>`;
      html += `<td data-live-target="${this._esc(c.entity_id)}">${targetPos != null ? targetPos + "%" : "–"}${infoIcon}</td>`;
      html += `<td data-live-rule="${this._esc(c.entity_id)}">${this._esc(ruleName)}</td>`;
      html += `<td data-live-lastchange="${this._esc(c.entity_id)}" style="font-size:12px;color:var(--ca-secondary-text);white-space:nowrap">${lastChange}</td>`;
      html += `<td><button class="btn-icon" data-action="cover-delete" data-id="${this._esc(c.entity_id)}" title="${this._t("delete")}">&#10005;</button></td>`;
      html += '</tr>';
    }

    html += '</tbody></table></div></div>';
    return html;
  }

  /* ---------- Slide-out for cover editing ---------- */
  _renderSlideOut() {
    const open = this._slideOpen && this._selectedCover;
    const cover = open ? (this._config.covers || {})[this._selectedCover] : null;

    let html = `<div class="slide-overlay${open ? " open" : ""}" data-action="close-slide"></div>`;
    html += `<div class="slide-panel${open ? " open" : ""}">`;

    if (cover) {
      html += `<div class="slide-header">
        <h2>${this._esc(cover.name)}</h2>
        <button class="btn-icon" data-action="close-slide" title="${this._t("close")}">&#10005;</button>
      </div>`;
      html += '<div class="slide-body">';

      // Section: Base
      html += this._renderSection("base", this._t("cover_section_base"), () => {
        let s = '';
        // Auto enabled
        s += this._renderToggle("cover_auto_enabled", cover.auto_enabled, "cover-toggle", cover.entity_id, "auto_enabled");
        // Facade
        s += this._renderFacadeDropdown(cover);
        s += this._hint("cover_facade_hint");
        // Pause duration
        const globalPause = (this._config.settings || {}).pause_duration || 10;
        const coverPause = cover.pause_duration != null ? cover.pause_duration : "";
        s += `<div class="form-group">
          <label>${this._t("cover_pause_duration")}</label>
          <input type="number" min="0" max="480" value="${coverPause}" placeholder="${globalPause}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="pause_duration">
          ${this._hint("cover_pause_duration_hint")}
        </div>`;
        return s;
      });

      // Section: Sensors
      html += this._renderSection("sensors", this._t("cover_section_sensors"), () => {
        let s = '';
        s += `<div class="form-group">
          <label>${this._t("cover_indoor_temp")}</label>
          ${this._renderCoverEntitySelect("indoor_temp_sensor", cover.indoor_temp_sensor, cover.entity_id, "sensor", "temperature")}
          ${this._hint("cover_indoor_temp_hint")}
        </div>`;
        const globalMin = (this._config.settings || {}).comfort_temp_min != null ? this._config.settings.comfort_temp_min : 22;
        const globalMax = (this._config.settings || {}).comfort_temp_max != null ? this._config.settings.comfort_temp_max : 24;
        s += '<div class="form-row">';
        s += `<div class="form-group">
          <label>${this._t("cover_comfort_min")}</label>
          <input type="number" step="0.5" value="${cover.comfort_temp_min != null ? cover.comfort_temp_min : ""}" placeholder="${globalMin}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="comfort_temp_min">
        </div>`;
        s += `<div class="form-group">
          <label>${this._t("cover_comfort_max")}</label>
          <input type="number" step="0.5" value="${cover.comfort_temp_max != null ? cover.comfort_temp_max : ""}" placeholder="${globalMax}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="comfort_temp_max">
        </div>`;
        s += '</div>';
        s += this._hint("cover_comfort_hint");
        s += `<div class="form-group">
          <label>${this._t("cover_lock_sensor")}</label>
          ${this._renderCoverEntitySelect("lock_sensor", cover.lock_sensor, cover.entity_id, "binary_sensor", null)}
          ${this._hint("cover_lock_sensor_hint")}
        </div>`;
        s += `<div class="form-group">
          <label>${this._t("cover_lock_position")}</label>
          <input type="number" min="0" max="100" value="${cover.lock_position}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="lock_position">
          ${this._hint("cover_lock_position_hint")}
        </div>`;
        s += `<div class="form-group">
          <label>${this._t("cover_vent_sensor")}</label>
          ${this._renderCoverEntitySelect("vent_sensor", cover.vent_sensor, cover.entity_id, "binary_sensor", null)}
          ${this._hint("cover_vent_sensor_hint")}
        </div>`;
        s += `<div class="form-group">
          <label>${this._t("cover_vent_position")}</label>
          <input type="number" min="0" max="100" value="${cover.vent_position}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="vent_position">
          ${this._hint("cover_vent_position_hint")}
        </div>`;
        return s;
      });

      // Section: Advanced
      html += this._renderSection("advanced", this._t("cover_section_advanced"), () => {
        let s = '';
        s += this._renderToggle("cover_inverted", cover.inverted, "cover-toggle", cover.entity_id, "inverted");
        s += this._hint("cover_inverted_hint");
        s += `<div class="form-group">
          <label>${this._t("cover_min_pos_change")}</label>
          <input type="number" min="1" max="50" value="${cover.min_position_change}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="min_position_change">
          ${this._hint("cover_min_pos_change_hint")}
        </div>`;
        s += `<div class="form-group">
          <label>${this._t("cover_min_time")}</label>
          <input type="number" min="60" max="3600" value="${cover.min_time_between_changes}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="min_time_between_changes">
          ${this._hint("cover_min_time_hint")}
        </div>`;
        return s;
      });

      // Section: Tilt (only if supports_tilt)
      if (cover.supports_tilt) {
        html += this._renderSection("tilt", this._t("cover_section_tilt"), () => {
          let s = '';
          s += this._renderToggle("cover_inverted_tilt", cover.inverted_tilt, "cover-toggle", cover.entity_id, "inverted_tilt");
          s += `<div class="form-group">
            <label>${this._t("cover_lock_tilt")}</label>
            <input type="number" min="0" max="100" value="${cover.lock_tilt_position != null ? cover.lock_tilt_position : ""}" placeholder="${this._t("none")}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="lock_tilt_position">
          </div>`;
          s += `<div class="form-group">
            <label>${this._t("cover_vent_tilt")}</label>
            <input type="number" min="0" max="100" value="${cover.vent_tilt_position != null ? cover.vent_tilt_position : ""}" placeholder="${this._t("none")}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="vent_tilt_position">
          </div>`;
          return s;
        });
      }

      html += '</div>'; // slide-body
    }

    html += '</div>'; // slide-panel
    return html;
  }

  _renderSection(id, title, contentFn) {
    const expanded = this._expandedSections[id];
    const arrowClass = expanded ? "arrow expanded" : "arrow";
    return `<div class="section">
      <div class="section-header" data-action="toggle-section" data-section="${id}">
        <span class="${arrowClass}">&#9654;</span> ${this._esc(title)}
      </div>
      <div class="section-body${expanded ? " expanded" : ""}">
        ${contentFn()}
      </div>
    </div>`;
  }

  _renderToggle(labelKey, checked, action, id, field) {
    return `<div class="toggle-row">
      <span>${this._t(labelKey)}</span>
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
    const entries = Object.values(facades);

    // Sun position info bar
    let html = '';
    const sunState = this._hass && this._hass.states ? this._hass.states["sun.sun"] : null;
    if (sunState && sunState.attributes) {
      const az = sunState.attributes.azimuth;
      const el = sunState.attributes.elevation;
      if (az != null && el != null) {
        const belowHorizon = el < 0;
        html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;padding:8px 12px;border-radius:8px;background:var(--ha-card-background,var(--card-background-color));font-size:13px;color:var(--ca-secondary-text)">';
        html += '<span style="font-size:16px">' + (belowHorizon ? '\u263E' : '\u2600') + '</span>';
        html += '<span>' + this._t("facade_sun_position") + ': ' + Number(az).toFixed(1) + '\u00B0 / ' + Number(el).toFixed(1) + '\u00B0</span>';
        html += '</div>';
      }
    }

    html += '<div class="card-grid">';

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
      ? '<span style="font-size:14px;margin-left:6px" title="' + this._esc(this._t("facade_sun_active")) + '">\u2600</span>'
      : '';
    let html = `<div class="card">
      <div class="card-header">
        <span>${this._esc(f.name)}${sunBadge}</span>
        <span style="font-size:12px;color:var(--ca-secondary-text)">${arrow} ${this._esc(dirLabel)}</span>
      </div>
      <div class="card-body">
        <div style="display:flex;gap:16px;margin-bottom:12px;font-size:13px;color:var(--ca-secondary-text)">
          <span>${this._t("facade_azimuth_start")}: ${f.azimuth_start}&#176;</span>
          <span>${this._t("facade_azimuth_end")}: ${f.azimuth_end}&#176;</span>
        </div>
        <div style="font-size:13px;color:var(--ca-secondary-text);margin-bottom:8px">
          ${this._t("facade_min_elevation")}: ${f.min_elevation}&#176;
        </div>
        <div style="margin-bottom:12px">
          <div style="font-size:12px;color:var(--ca-secondary-text);margin-bottom:4px">${this._t("facade_covers")}</div>
          <div class="chip-group">`;
    if (covers.length === 0) {
      html += `<span style="font-size:12px;color:var(--ca-secondary-text)">${this._t("facade_no_covers")}</span>`;
    } else {
      for (const c of covers) {
        html += `<span class="chip">${this._esc(c.name)}</span>`;
      }
    }
    html += `</div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end">
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
          <input type="number" min="0" max="360" step="0.1" value="${f.azimuth_start}" data-facade-field="azimuth_start">
        </div>
        <div class="form-group">
          <label>${this._t("facade_azimuth_end")}</label>
          <input type="number" min="0" max="360" step="0.1" value="${f.azimuth_end}" data-facade-field="azimuth_end">
        </div>
      </div>
      ${this._hint("facade_azimuth_hint")}
      <div class="form-group">
        <label>${this._t("facade_min_elevation")}</label>
        <input type="number" min="0" max="90" step="0.5" value="${f.min_elevation}" data-facade-field="min_elevation">
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
          <input type="number" min="0" max="360" step="0.1" value="135" data-facade-field="azimuth_start">
        </div>
        <div class="form-group">
          <label>${this._t("facade_azimuth_end")}</label>
          <input type="number" min="0" max="360" step="0.1" value="225" data-facade-field="azimuth_end">
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
    const sorted = Object.values(rules).sort((a, b) => (b.priority || 0) - (a.priority || 0));

    let html = `<div style="margin-bottom:12px;font-size:12px;color:var(--ca-secondary-text)">${this._t("rule_reorder_hint")}</div>`;

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

      html += `<div class="rule-row${dragging}${dragOver}" draggable="true" data-rule-id="${this._esc(r.id)}" data-action="rule-drag">`;
      html += `<span class="drag-handle" title="Drag">&#9783;</span>`;
      html += `<div class="rule-info" data-action="rule-expand" data-id="${this._esc(r.id)}">`;
      html += `<div class="rule-name">`;
      html += `<span class="rule-active-dot ${isActive ? "active" : ""}" title="${isActive ? this._t("rule_active_for") + " " + matchedCovers.length + " " + this._t("rule_covers_count") : this._t("rule_inactive")}"></span>`;
      html += `${this._esc(r.name)}</div>`;
      html += '<div class="rule-meta">';
      html += `<span class="priority-badge">#${idx + 1}</span>`;
      html += `<span>${r.condition_operator === "or" ? "OR" : "AND"}</span>`;
      html += `<span>${this._t("rule_target_pos")}: ${r.target_position}%</span>`;
      if (r.target_tilt_position != null) {
        html += `<span>${this._t("rule_target_tilt")}: ${r.target_tilt_position}%</span>`;
      }
      html += '</div>';
      // Condition chips
      if (r.conditions && r.conditions.length > 0) {
        html += '<div class="chip-group" style="margin-top:6px">';
        for (const c of r.conditions) {
          html += `<span class="chip">${this._t("cond_" + c.type)}</span>`;
        }
        html += '</div>';
      }
      html += '</div>'; // rule-info

      // Enable toggle
      html += `<label class="toggle">
        <input type="checkbox" ${r.enabled ? "checked" : ""} data-action="rule-toggle-enabled" data-id="${this._esc(r.id)}">
        <span class="toggle-slider"></span>
      </label>`;

      html += `<button class="btn-icon" data-action="rule-delete" data-id="${this._esc(r.id)}" title="${this._t("delete")}">&#10005;</button>`;
      html += '</div>'; // rule-row

      // Expanded editor
      html += `<div class="rule-editor${isExpanded ? " expanded" : ""}">`;
      if (isExpanded) {
        html += this._renderRuleEditor(r);
      }
      html += '</div>';
    }

    // Add rule button/form
    if (this._addingRule) {
      html += this._renderRuleAddForm();
    } else {
      html += `<button class="btn btn-primary" style="margin-top:16px" data-action="rule-add-start">+ ${this._t("rule_add")}</button>`;
    }

    return html;
  }

  _renderRuleEditor(rule) {
    const facades = this._config.facades || {};
    const covers = this._config.covers || {};

    let html = '';

    // Name
    html += `<div class="form-group">
      <label>${this._t("name")}</label>
      <input type="text" value="${this._esc(rule.name)}" data-action="rule-field" data-id="${this._esc(rule.id)}" data-field="name">
    </div>`;

    // Target position + tilt
    html += '<div class="form-row">';
    html += `<div class="form-group">
      <label>${this._t("rule_target_pos")}</label>
      <input type="number" min="0" max="100" value="${rule.target_position}" data-action="rule-field" data-id="${this._esc(rule.id)}" data-field="target_position">
      ${this._hint("rule_target_pos_hint")}
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("rule_target_tilt")}</label>
      <input type="number" min="0" max="100" value="${rule.target_tilt_position != null ? rule.target_tilt_position : ""}" placeholder="${this._t("none")}" data-action="rule-field" data-id="${this._esc(rule.id)}" data-field="target_tilt_position">
    </div>`;
    html += '</div>';

    html += `<div class="form-group">
      <label>${this._t("rule_operator")}</label>
      <select data-action="rule-field" data-id="${this._esc(rule.id)}" data-field="condition_operator">
        <option value="and"${rule.condition_operator==="and"?" selected":""}>${this._t("rule_operator_and")}</option>
        <option value="or"${rule.condition_operator==="or"?" selected":""}>${this._t("rule_operator_or")}</option>
      </select>
      ${this._hint("rule_operator_hint")}
    </div>`;

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

    // Conditions
    html += `<div style="font-size:13px;font-weight:600;color:var(--ca-secondary-text);text-transform:uppercase;letter-spacing:0.5px;margin:16px 0 8px">${this._t("rule_conditions")}</div>`;

    if (rule.conditions && rule.conditions.length > 0) {
      for (let i = 0; i < rule.conditions.length; i++) {
        html += this._renderConditionCard(rule, i);
      }
    } else {
      html += `<div style="font-size:13px;color:var(--ca-secondary-text);margin-bottom:8px">${this._t("rule_no_conditions")}</div>`;
    }

    // Add condition
    html += `<div style="margin-top:8px">
      <select data-action="rule-add-condition-type" data-rule="${this._esc(rule.id)}" style="padding:8px;border:1px solid var(--ca-border);border-radius:8px;background:var(--primary-background-color,#fafafa);color:var(--primary-text-color);font-size:13px;font-family:inherit">
        <option value="">${this._t("rule_add_condition")}...</option>
        ${CONDITION_TYPES.map(t => `<option value="${t}">${this._t("cond_" + t)}</option>`).join("")}
      </select>
    </div>`;

    // Save button
    html += `<div style="display:flex;justify-content:flex-end;margin-top:16px">
      <button class="btn btn-primary" data-action="rule-save" data-id="${this._esc(rule.id)}">${this._t("save")}</button>
    </div>`;

    return html;
  }

  _renderConditionCard(rule, idx) {
    const cond = rule.conditions[idx];
    const paramDefs = CONDITION_PARAMS[cond.type] || [];

    let html = `<div class="condition-card">
      <div class="cond-header">
        <span class="cond-type">${this._t("cond_" + cond.type)}</span>
        <button class="btn-icon" data-action="rule-delete-condition" data-rule="${this._esc(rule.id)}" data-idx="${idx}" title="${this._t("delete")}">&#10005;</button>
      </div>`;

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
            html += `<button type="button" class="day-btn${active ? " selected" : ""}" data-action="multiselect-toggle" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}" data-val="${opt}">${opt}</button>`;
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
          html += `<input type="number" value="${val}"${p.step ? ' step="' + p.step + '"' : ""} data-action="cond-param" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}">`;
        } else {
          html += `<input type="text" value="${this._esc(String(val))}" data-action="cond-param" data-rule="${this._esc(rule.id)}" data-idx="${idx}" data-key="${p.key}">`;
        }
        html += '</div>';
      }
      html += '</div>';
    }

    html += '</div>';
    return html;
  }

  _renderRuleAddForm() {
    let html = `<div class="inline-form" style="margin-top:16px">
      <div class="form-group">
        <label>${this._t("name")}</label>
        <input type="text" value="" data-rule-new-field="name" placeholder="${this._t("name")}">
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

  _renderScenarioCard(sc, rules, isActive) {
    const ruleEntries = Object.values(rules);
    let html = `<div class="scenario-card${isActive ? " active-scenario" : ""}">
      <div class="sc-header">
        <div class="sc-name">
          ${sc.icon ? `<ha-icon icon="${this._esc(sc.icon)}" style="--mdc-icon-size:20px;margin-right:6px"></ha-icon>` : ""}${this._esc(sc.name)}
          ${isActive ? `<span class="chip">${this._t("active")}</span>` : ""}
        </div>
        <div style="display:flex;gap:6px">
          ${!isActive ? `<button class="btn btn-primary btn-sm" data-action="scenario-activate" data-id="${this._esc(sc.id)}">${this._t("activate")}</button>` : ""}
          <button class="btn btn-secondary btn-sm" data-action="scenario-edit" data-id="${this._esc(sc.id)}">${this._t("edit")}</button>
          <button class="btn btn-danger btn-sm" data-action="scenario-delete" data-id="${this._esc(sc.id)}">${this._t("delete")}</button>
        </div>
      </div>`;

    // Rules list with enabled/disabled toggles
    html += '<div class="sc-rules">';
    if (ruleEntries.length === 0) {
      html += `<div style="font-size:13px;color:var(--ca-secondary-text)">${this._t("scenario_no_rules")}</div>`;
    } else {
      for (const r of ruleEntries) {
        const disabled = (sc.rules_disabled || []).includes(r.id);
        html += `<div class="sc-rule-row">
          <span${disabled ? ' style="text-decoration:line-through;opacity:0.5"' : ""}>${this._esc(r.name)}</span>
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

  _renderScenarioEditForm(sc, rules, isActive) {
    let html = `<div class="inline-form">
      <div class="form-group">
        <label>${this._t("name")}</label>
        <input type="text" value="${this._esc(sc.name)}" data-scenario-field="name">
      </div>
      <div class="form-group">
        <label>${this._t("scenario_icon")}</label>
        <input type="text" value="${this._esc(sc.icon || "")}" data-scenario-field="icon" placeholder="mdi:home">
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
        <input type="text" value="mdi:home" data-scenario-field="icon" placeholder="mdi:home">
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
    html += "</select>";
    return html;
  }

  _renderCoverEntitySelect(field, currentValue, coverId, domain, deviceClass) {
    if (!this._hass || !this._hass.states) return `<input type="text" value="${this._esc(currentValue || "")}" data-action="cover-input" data-id="${this._esc(coverId)}" data-field="${field}">`;
    const entities = Object.values(this._hass.states)
      .filter(s => {
        if (!s.entity_id.startsWith(domain + ".")) return false;
        if (deviceClass && s.attributes.device_class !== deviceClass) return false;
        return true;
      })
      .sort((a, b) => (a.attributes.friendly_name || a.entity_id).localeCompare(b.attributes.friendly_name || b.entity_id));
    let html = `<select data-action="cover-input" data-id="${this._esc(coverId)}" data-field="${field}">`;
    html += `<option value="">-- ${this._t("none")} --</option>`;
    for (const e of entities) {
      const name = e.attributes.friendly_name || e.entity_id;
      const sel = e.entity_id === currentValue ? " selected" : "";
      html += `<option value="${this._esc(e.entity_id)}"${sel}>${this._esc(name)}</option>`;
    }
    html += "</select>";
    return html;
  }

  _renderSensorValue(entityId, unit) {
    if (!entityId || !this._hass || !this._hass.states) return "";
    const state = this._hass.states[entityId];
    if (!state || state.state === "unavailable" || state.state === "unknown") return "";
    const val = state.state;
    const u = unit || state.attributes.unit_of_measurement || "";
    return '<div style="font-size:12px;color:var(--ca-primary);margin-top:2px">' + this._t("settings_current_value") + ': ' + this._esc(val) + this._esc(u) + '</div>';
  }

  _renderCompassSVG(rotation) {
    const cx = 110, cy = 110, r = 95, hr = 30;
    const sunState = this._hass ? this._hass.states["sun.sun"] : null;
    const sunAz = sunState ? parseFloat(sunState.attributes.azimuth) : null;
    const sunEl = sunState ? parseFloat(sunState.attributes.elevation) : null;
    const belowHorizon = sunEl != null && sunEl < 0;

    // Facade arcs
    const facades = this._config ? Object.values(this._config.facades || {}) : [];
    let facadeArcs = "";
    const facadeColors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"];
    facades.forEach((f, i) => {
      const startDeg = (f.azimuth_start - 90) * Math.PI / 180;
      const endDeg = (f.azimuth_end - 90) * Math.PI / 180;
      const arcR = r - 8;
      const x1 = cx + arcR * Math.cos(startDeg), y1 = cy + arcR * Math.sin(startDeg);
      const x2 = cx + arcR * Math.cos(endDeg), y2 = cy + arcR * Math.sin(endDeg);
      let sweep = f.azimuth_end - f.azimuth_start;
      if (sweep < 0) sweep += 360;
      const large = sweep > 180 ? 1 : 0;
      facadeArcs += `<path d="M${x1},${y1} A${arcR},${arcR} 0 ${large},1 ${x2},${y2}" fill="none" stroke="${facadeColors[i % facadeColors.length]}" stroke-width="6" opacity="0.6"/>`;
      // Label
      const midDeg = (f.azimuth_start + sweep / 2 - 90) * Math.PI / 180;
      const lx = cx + (arcR - 14) * Math.cos(midDeg), ly = cy + (arcR - 14) * Math.sin(midDeg);
      facadeArcs += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="central" font-size="9" fill="${facadeColors[i % facadeColors.length]}" font-weight="600">${this._esc(f.name.substring(0, 6))}</text>`;
    });

    // Sun position
    let sunMarker = "";
    if (sunAz != null && !isNaN(sunAz) && !belowHorizon) {
      const sunRad = (sunAz - 90) * Math.PI / 180;
      const sr = r + 2;
      const sx = cx + sr * Math.cos(sunRad), sy = cy + sr * Math.sin(sunRad);
      sunMarker = `<circle cx="${sx}" cy="${sy}" r="8" fill="#FFC107" stroke="#F57F17" stroke-width="1.5"/>
        <text x="${sx}" y="${sy}" text-anchor="middle" dominant-baseline="central" font-size="8" fill="#F57F17" font-weight="700">${Math.round(sunEl)}°</text>`;
    }

    return `<svg id="compass-svg" width="220" height="220" viewBox="0 0 220 220" style="display:block">
      <!-- Compass circle -->
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--divider-color)" stroke-width="1.5"/>
      <circle cx="${cx}" cy="${cy}" r="${r - 20}" fill="none" stroke="var(--divider-color)" stroke-width="0.5" stroke-dasharray="3,3"/>
      <!-- Cardinal directions (fixed) -->
      <text x="${cx}" y="${cy - r - 6}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--primary-text-color)">N</text>
      <text x="${cx}" y="${cy + r + 16}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--primary-text-color)">S</text>
      <text x="${cx + r + 10}" y="${cy + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--primary-text-color)">E</text>
      <text x="${cx - r - 10}" y="${cy + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--primary-text-color)">W</text>
      <!-- Tick marks -->
      ${[0,45,90,135,180,225,270,315].map(d => { const rad=(d-90)*Math.PI/180; const i=d%90===0?10:6; return `<line x1="${cx+(r-i)*Math.cos(rad)}" y1="${cy+(r-i)*Math.sin(rad)}" x2="${cx+r*Math.cos(rad)}" y2="${cy+r*Math.sin(rad)}" stroke="var(--primary-text-color)" stroke-width="${d%90===0?2:1}" opacity="${d%90===0?0.8:0.4}"/>`; }).join("")}
      <!-- House (rotated) -->
      <g transform="rotate(${rotation}, ${cx}, ${cy})">
        <rect x="${cx - hr}" y="${cy - hr}" width="${hr * 2}" height="${hr * 2}" rx="4" fill="var(--ha-card-background, var(--card-background-color, #fff))" stroke="var(--primary-color)" stroke-width="2"/>
        <!-- Roof indicator (front = south of house before rotation) -->
        <line x1="${cx - hr + 6}" y1="${cy + hr}" x2="${cx + hr - 6}" y2="${cy + hr}" stroke="var(--primary-color)" stroke-width="4" stroke-linecap="round"/>
        <text x="${cx}" y="${cy + 4}" text-anchor="middle" font-size="11" fill="var(--primary-text-color)" opacity="0.6">${rotation}°</text>
      </g>
      <!-- Facade arcs -->
      ${facadeArcs}
      <!-- Sun -->
      ${sunMarker}
    </svg>`;
  }

  _renderSettings() {
    const s = this._config.settings || {};

    let html = '<div class="card"><div class="card-body" style="padding-top:20px">';

    // Sensors section
    const hintStyle = 'font-size:12px;color:var(--ca-secondary-text);margin-top:4px';
    html += `<div style="font-size:13px;font-weight:600;color:var(--ca-secondary-text);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px">${this._t("settings_section_sensors")}</div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_outdoor_temp")}</label>
      ${this._renderEntitySelect("outdoor_temp_sensor", s.outdoor_temp_sensor, "sensor", "temperature")}
      ${this._renderSensorValue(s.outdoor_temp_sensor, "\u00B0")}
      <div style="${hintStyle}">${this._t("settings_outdoor_temp_hint")}</div>
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_indoor_temp")}</label>
      ${this._renderEntitySelect("indoor_temp_sensor", s.indoor_temp_sensor, "sensor", "temperature")}
      ${this._renderSensorValue(s.indoor_temp_sensor, "\u00B0")}
      <div style="${hintStyle}">${this._t("settings_indoor_temp_hint")}</div>
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_weather")}</label>
      ${this._renderEntitySelect("weather_entity", s.weather_entity, "weather", null)}
      ${this._renderSensorValue(s.weather_entity)}
      <div style="${hintStyle}">${this._t("settings_weather_hint")}</div>
    </div>`;

    // Comfort section
    html += `<div style="font-size:13px;font-weight:600;color:var(--ca-secondary-text);text-transform:uppercase;letter-spacing:0.5px;margin:20px 0 12px">${this._t("settings_section_comfort")}</div>`;
    html += `<div style="${hintStyle};margin-bottom:12px">${this._t("settings_comfort_hint")}</div>`;
    html += '<div class="form-row">';
    html += `<div class="form-group">
      <label>${this._t("settings_comfort_min")}</label>
      <input type="number" step="0.5" value="${s.comfort_temp_min != null ? s.comfort_temp_min : 21}" data-settings-field="comfort_temp_min">
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_comfort_max")}</label>
      <input type="number" step="0.5" value="${s.comfort_temp_max != null ? s.comfort_temp_max : 25}" data-settings-field="comfort_temp_max">
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_comfort_hysteresis")}</label>
      <input type="number" step="0.1" min="0.1" max="5" value="${s.comfort_hysteresis != null ? s.comfort_hysteresis : 1}" data-settings-field="comfort_hysteresis">
      <div style="${hintStyle}">${this._t("settings_comfort_hysteresis_hint")}</div>
    </div>`;
    html += '</div>';

    // Automation section
    html += `<div style="font-size:13px;font-weight:600;color:var(--ca-secondary-text);text-transform:uppercase;letter-spacing:0.5px;margin:20px 0 12px">${this._t("settings_section_automation")}</div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_pause_duration")}</label>
      <input type="number" min="1" max="480" value="${s.pause_duration != null ? s.pause_duration : 10}" data-settings-field="pause_duration">
      <div style="${hintStyle}">${this._t("settings_pause_duration_hint")}</div>
    </div>`;
    html += '<div class="form-row">';
    html += `<div class="form-group">
      <label>${this._t("settings_lock_position")}</label>
      <input type="number" min="0" max="100" value="${s.lock_position != null ? s.lock_position : 100}" data-settings-field="lock_position">
      <div style="${hintStyle}">${this._t("settings_lock_position_hint")}</div>
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_vent_position")}</label>
      <input type="number" min="0" max="100" value="${s.vent_position != null ? s.vent_position : 30}" data-settings-field="vent_position">
      <div style="${hintStyle}">${this._t("settings_vent_position_hint")}</div>
    </div>`;
    html += '</div>';
    html += '<div class="form-row">';
    html += `<div class="form-group">
      <label>${this._t("settings_lock_tilt_position")}</label>
      <input type="number" min="0" max="100" value="${s.lock_tilt_position != null ? s.lock_tilt_position : ""}" data-settings-field="lock_tilt_position">
      <div style="${hintStyle}">${this._t("settings_lock_tilt_position_hint")}</div>
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_vent_tilt_position")}</label>
      <input type="number" min="0" max="100" value="${s.vent_tilt_position != null ? s.vent_tilt_position : ""}" data-settings-field="vent_tilt_position">
      <div style="${hintStyle}">${this._t("settings_vent_tilt_position_hint")}</div>
    </div>`;
    html += '</div>';
    html += '<div class="form-row">';
    html += `<div class="form-group">
      <label>${this._t("settings_min_position_change")}</label>
      <input type="number" min="1" max="50" value="${s.min_position_change != null ? s.min_position_change : 5}" data-settings-field="min_position_change">
      <div style="${hintStyle}">${this._t("settings_min_position_change_hint")}</div>
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_min_time")}</label>
      <input type="number" min="60" max="3600" value="${s.min_time_between_changes != null ? s.min_time_between_changes : 300}" data-settings-field="min_time_between_changes">
      <div style="${hintStyle}">${this._t("settings_min_time_hint")}</div>
    </div>`;
    html += '</div>';

    // Workday sensor section
    html += `<div style="font-size:13px;font-weight:600;color:var(--ca-secondary-text);text-transform:uppercase;letter-spacing:0.5px;margin:20px 0 12px">${this._t("settings_section_workday")}</div>`;
    html += `<div style="${hintStyle};margin-bottom:12px">${this._t("settings_workday_hint")}</div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_workday_sensor")}</label>
      ${this._renderEntitySelect("workday_sensor", s.workday_sensor, "binary_sensor", null)}
      ${this._renderSensorValue(s.workday_sensor)}
    </div>`;

    // Wind protection section
    html += `<div style="font-size:13px;font-weight:600;color:var(--ca-secondary-text);text-transform:uppercase;letter-spacing:0.5px;margin:20px 0 12px">${this._t("settings_section_wind")}</div>`;
    html += `<div style="${hintStyle};margin-bottom:12px">${this._t("settings_wind_hint")}</div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_wind_sensor")}</label>
      ${this._renderEntitySelect("wind_sensor", s.wind_sensor, "sensor", "wind_speed")}
      ${this._renderSensorValue(s.wind_sensor, " km/h")}
    </div>`;
    html += '<div class="form-row">';
    html += `<div class="form-group">
      <label>${this._t("settings_wind_threshold")}</label>
      <input type="number" step="1" min="0" value="${s.wind_speed_threshold != null ? s.wind_speed_threshold : 0}" data-settings-field="wind_speed_threshold">
    </div>`;
    html += `<div class="form-group">
      <label>${this._t("settings_wind_hysteresis")}</label>
      <input type="number" step="1" min="0" value="${s.wind_speed_hysteresis != null ? s.wind_speed_hysteresis : 0}" data-settings-field="wind_speed_hysteresis">
    </div>`;
    html += '</div>';

    // House section
    html += `<div style="font-size:13px;font-weight:600;color:var(--ca-secondary-text);text-transform:uppercase;letter-spacing:0.5px;margin:20px 0 12px">${this._t("settings_section_house")}</div>`;
    const rot = s.house_rotation != null ? s.house_rotation : 0;
    html += `<div style="display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap">
      <div class="form-group" style="flex:1;min-width:160px">
        <label>${this._t("settings_house_rotation")}</label>
        <input type="number" step="0.5" min="-180" max="180" value="${rot}" data-settings-field="house_rotation" id="house-rotation-input">
        <div style="font-size:12px;color:var(--ca-secondary-text);margin-top:4px">${this._t("settings_house_rotation_hint")}</div>
      </div>
      <div style="flex:0 0 auto">${this._renderCompassSVG(rot)}</div>
    </div>`;

    // Save
    html += `<div style="display:flex;justify-content:flex-end;margin-top:20px">
      <button class="btn btn-primary" data-action="settings-save">${this._t("save")}</button>
    </div>`;

    // Backup section
    html += `<div style="font-size:13px;font-weight:600;color:var(--ca-secondary-text);text-transform:uppercase;letter-spacing:0.5px;margin:20px 0 12px">${this._t("settings_section_backup")}</div>`;
    html += `<div style="${hintStyle};margin-bottom:12px">${this._t("settings_backup_hint")}</div>`;
    html += `<div style="display:flex;gap:12px;flex-wrap:wrap">
      <button class="btn" data-action="backup-export">${this._t("settings_export")}</button>
      <button class="btn" data-action="backup-import">${this._t("settings_import")}</button>
      <input type="file" accept=".json" data-action="backup-file" style="display:none">
    </div>`;

    html += '</div></div>';
    return html;
  }

  _renderLog() {
    if (this._logEntries === null) {
      this._loadLog();
      return '<div class="empty-state">' + this._t("log_loading") + '</div>';
    }

    let html = '';

    // Filter buttons
    const filters = [null, "position", "status", "rule", "wind"];
    html += '<div style="margin-bottom:12px;display:flex;gap:6px;flex-wrap:wrap">';
    for (const f of filters) {
      const active = this._logFilter === f ? " active" : "";
      const label = f ? this._t("log_type_" + f) : this._t("log_filter_all");
      html += '<button class="btn btn-sm' + active + '" data-action="log-filter" data-filter="' + (f || '') + '">' + label + '</button>';
    }
    html += '</div>';

    let entries = this._logEntries;
    if (this._logFilter) {
      entries = entries.filter(e => e.type === this._logFilter);
    }

    if (entries.length === 0) {
      return html + '<div class="empty-state">' + this._t("log_empty") + '</div>';
    }

    html += '<div class="card"><div style="overflow-x:auto"><table class="data-table">';
    html += '<thead><tr>';
    html += '<th>' + this._t("log_time") + '</th>';
    html += '<th>' + this._t("log_event") + '</th>';
    html += '<th>' + this._t("log_cover") + '</th>';
    html += '<th>' + this._t("log_message") + '</th>';
    html += '</tr></thead><tbody>';

    for (const e of entries) {
      const time = new Date(e.ts * 1000).toLocaleString();
      const typeLabel = this._t("log_type_" + e.type) || e.type;
      const coverName = e.entity_id ? this._getCoverName(e.entity_id) : "–";
      const typeClass = e.type === "wind" ? "status-wind_protected" : e.type === "status" ? "status-paused" : "";
      html += '<tr>';
      html += '<td style="white-space:nowrap">' + this._esc(time) + '</td>';
      html += '<td><span class="status-badge ' + typeClass + '">' + this._esc(typeLabel) + '</span></td>';
      html += '<td>' + this._esc(coverName) + '</td>';
      html += '<td>' + this._esc(e.message) + '</td>';
      html += '</tr>';
    }
    html += '</tbody></table></div></div>';
    return html;
  }

  async _loadLog() {
    try {
      const result = await this._ws("cover_automatic/log");
      this._logEntries = result.entries || [];
    } catch (e) {
      this._logEntries = [];
    }
    this._render();
  }

  _updateLiveCells() {
    const root = this.shadowRoot;
    if (!root || !this._config) return;
    const covers = this._config.covers || {};
    const liveCvrs = this._config.live_covers || {};
    for (const eid of Object.keys(covers)) {
      // Current position from HA state
      const haState = this._hass && this._hass.states ? this._hass.states[eid] : null;
      const curPos = haState && haState.attributes ? haState.attributes.current_position : null;
      const cell = root.querySelector('[data-live-current="' + eid + '"]');
      if (cell) cell.textContent = curPos != null ? curPos + "%" : "\u2013";
      // Target position + hysteresis from coordinator
      const live = liveCvrs[eid] || {};
      const tgtPos = live.target_position;
      const hyst = live.hysteresis;
      const tCell = root.querySelector('[data-live-target="' + eid + '"]');
      if (tCell) {
        tCell.textContent = "";
        tCell.appendChild(document.createTextNode(tgtPos != null ? tgtPos + "%" : "\u2013"));
        if (hyst === "position" || hyst === "time") {
          const badge = document.createElement("span");
          badge.className = "status-badge status-paused";
          badge.style.cssText = "font-size:11px;margin-left:4px";
          badge.textContent = hyst === "position" ? "\u2195" : "\u23F2";
          badge.title = this._t(hyst === "position" ? "cover_hysteresis_position" : "cover_hysteresis_time");
          tCell.appendChild(badge);
        }
      }
      // Status + pause remaining
      const c = covers[eid];
      const sCell = root.querySelector('[data-live-status="' + eid + '"]');
      if (sCell && c) {
        const st = c.status || "auto";
        const badge = sCell.querySelector(".status-badge");
        if (badge) {
          badge.className = "status-badge status-" + st;
          badge.textContent = this._t("status_" + st) || st;
        }
        let pauseSpan = sCell.querySelector(".pause-remaining");
        if (st === "paused" && live.pause_until) {
          const txt = this._formatPauseRemaining(live.pause_until);
          if (txt) {
            if (!pauseSpan) {
              pauseSpan = document.createElement("span");
              pauseSpan.className = "pause-remaining";
              pauseSpan.style.cssText = "font-size:11px;color:var(--ca-secondary-text);margin-left:4px";
              sCell.appendChild(pauseSpan);
            }
            pauseSpan.textContent = txt;
          } else if (pauseSpan) {
            pauseSpan.remove();
          }
        } else if (pauseSpan) {
          pauseSpan.remove();
        }
      }
      // Cover name + comfort icon
      const nCell = root.querySelector('[data-live-name="' + eid + '"]');
      if (nCell && c) {
        nCell.textContent = "";
        nCell.appendChild(document.createTextNode(c.name));
        const cm = live.comfort_mode;
        if (cm === "cooling" || cm === "heating" || cm === "neutral") {
          const ci = document.createElement("span");
          ci.title = this._t("comfort_" + cm);
          ci.style.cssText = "font-size:12px;margin-left:2px";
          ci.textContent = cm === "cooling" ? "\u2744" : cm === "heating" ? "\u2600" : "\u25CF";
          nCell.appendChild(ci);
        }
      }
      // Facade name + sun icon
      const fCell = root.querySelector('[data-live-facade="' + eid + '"]');
      if (fCell && c) {
        const facadeName = this._getFacadeName(c.facade_id);
        const liveFacade = c.facade_id ? ((this._config.live_facades || {})[c.facade_id] || {}) : {};
        fCell.textContent = "";
        fCell.appendChild(document.createTextNode(facadeName));
        if (liveFacade.sun_on_facade) {
          const sun = document.createElement("span");
          sun.title = this._t("facade_sun_active");
          sun.style.cssText = "font-size:12px";
          sun.textContent = "\u2600";
          fCell.appendChild(document.createTextNode(" "));
          fCell.appendChild(sun);
        }
      }
      // Rule name
      const rCell = root.querySelector('[data-live-rule="' + eid + '"]');
      if (rCell) rCell.textContent = live.rule_name || this._t("cover_no_rule");
      // Temperature
      const tempCell = root.querySelector('[data-live-temp="' + eid + '"]');
      if (tempCell) {
        const c2 = covers[eid];
        const ts = (c2 && c2.indoor_temp_sensor) || ((this._config.settings || {}).indoor_temp_sensor);
        const tst = ts && this._hass && this._hass.states ? this._hass.states[ts] : null;
        const tv = tst && tst.state !== "unavailable" && tst.state !== "unknown" ? parseFloat(tst.state) : null;
        tempCell.textContent = tv != null ? tv.toFixed(1) + " \u00B0C" : "\u2013";
      }
      // Last change
      const lcCell = root.querySelector('[data-live-lastchange="' + eid + '"]');
      if (lcCell) lcCell.textContent = live.last_change ? this._formatTimeAgo(live.last_change) : "";
    }
  }

  _formatTimeAgo(ts) {
    const sec = Math.max(0, Math.round(Date.now() / 1000 - ts));
    if (sec < 60) return this._t("cover_just_now");
    const min = Math.floor(sec / 60);
    if (min < 60) return min + " " + this._t("cover_minutes_ago");
    const h = Math.floor(min / 60);
    const m = min % 60;
    return h + ":" + (m < 10 ? "0" : "") + m + " " + this._t("cover_hours_ago");
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
    this._liveRefreshTimer = setInterval(() => this._refreshLiveCovers(), 30000);
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
    try {
      const result = await this._ws("cover_automatic/config");
      if (result) {
        if (result.live_covers) this._config.live_covers = result.live_covers;
        if (result.live_facades) this._config.live_facades = result.live_facades;
        if (result.active_rules) this._config.active_rules = result.active_rules;
        if (result.covers) this._config.covers = result.covers;
        this._updateLiveCells();
      }
    } catch (e) { /* silent */ }
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
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  /* ============================================================
   * Event delegation (bound once, routes all events)
   * ============================================================ */
  _setupDelegation() {
    if (this._delegationBound) return;
    this._delegationBound = true;
    const root = this.shadowRoot;

    root.addEventListener("click", (e) => this._handleClick(e));
    root.addEventListener("change", (e) => this._handleChange(e));
    root.addEventListener("input", (e) => this._handleInput(e));
    root.addEventListener("dragstart", (e) => this._handleDragStart(e));
    root.addEventListener("dragend", (e) => this._handleDragEnd(e));
    root.addEventListener("dragover", (e) => this._handleDragOver(e));
    root.addEventListener("dragleave", (e) => this._handleDragLeave(e));
    root.addEventListener("drop", (e) => this._handleDrop(e));
  }

  /* ---------- Click delegation ---------- */
  _handleClick(e) {
    // Tab clicks
    const tabBtn = e.target.closest("[data-tab]");
    if (tabBtn) {
      this._activeTab = tabBtn.dataset.tab;
      this._selectedCover = null;
      this._slideOpen = false;
      this._expandedRule = null;
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
      this._render();
      return;
    }

    // Route by data-action
    const actionEl = e.target.closest("[data-action]");
    if (!actionEl) return;
    const action = actionEl.dataset.action;

    switch (action) {
      case "retry": this._loadConfig(); break;
      case "cover-add-start": this._addingCover = true; this._render(); break;
      case "cover-add-cancel": this._addingCover = false; this._render(); break;
      case "cover-add": this._onCoverAdd(); break;
      case "cover-resume": this._onCoverResume(actionEl.dataset.id); break;
      case "cover-delete": this._onCoverDelete(actionEl.dataset.id); break;
      case "select-cover":
        this._selectedCover = actionEl.dataset.id;
        this._slideOpen = true;
        this._expandedSections = { base: true, sensors: true, advanced: false, tilt: false };
        this._render();
        break;
      case "close-slide":
        if (e.target === actionEl || actionEl.classList.contains("btn-icon")) {
          this._slideOpen = false;
          this._render();
        }
        break;
      case "toggle-section":
        this._expandedSections[actionEl.dataset.section] = !this._expandedSections[actionEl.dataset.section];
        this._render();
        break;
      case "facade-add-start": this._addingFacade = true; this._render(); break;
      case "facade-add-cancel": this._addingFacade = false; this._render(); break;
      case "facade-edit": this._editingFacade = actionEl.dataset.id; this._render(); break;
      case "facade-edit-cancel": this._editingFacade = null; this._render(); break;
      case "day-toggle": this._onDayToggle(actionEl); break;
      case "multiselect-toggle": this._onMultiselectToggle(actionEl); break;
      case "facade-cover-toggle": actionEl.classList.toggle("selected"); break;
      case "facade-add-save": this._onFacadeAddSave(actionEl); break;
      case "facade-edit-save": this._onFacadeEditSave(actionEl); break;
      case "facade-delete": this._onFacadeDelete(actionEl.dataset.id); break;
      case "rule-expand":
        this._expandedRule = this._expandedRule === actionEl.dataset.id ? null : actionEl.dataset.id;
        this._render();
        break;
      case "rule-delete": this._onRuleDelete(actionEl.dataset.id); break;
      case "rule-save": this._onRuleSave(actionEl.dataset.id); break;
      case "rule-delete-condition": this._onRuleDeleteCondition(actionEl.dataset.rule, actionEl.dataset.idx); break;
      case "rule-facade-toggle": actionEl.classList.toggle("selected"); break;
      case "rule-cover-toggle": actionEl.classList.toggle("selected"); break;
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
      case "settings-save": this._onSettingsSave(); break;
      case "backup-export": this._onBackupExport(); break;
      case "backup-import": this._shadowRoot.querySelector('[data-action="backup-file"]').click(); break;
      case "backup-file": this._onBackupFileSelected(actionEl); break;
      case "log-filter":
        this._logFilter = actionEl.dataset.filter || null;
        this._render();
        break;
      case "confirm-ok":
        if (this._confirmCallback) this._confirmCallback();
        this._hideConfirm();
        break;
      case "confirm-cancel":
        if (e.target === actionEl) this._hideConfirm();
        break;
    }
  }

  /* ---------- Change delegation ---------- */
  _handleChange(e) {
    const el = e.target;

    // Master toggle
    if (el.matches('[data-action="master-toggle"]')) {
      this._onMasterToggle(el.checked);
      return;
    }

    // Cover select (dropdown) changes
    if (el.matches('[data-action="cover-select"]')) {
      this._debouncedCoverSave(el.dataset.id, el.dataset.field, el.value || null);
      return;
    }

    // Cover toggle (checkbox) changes
    if (el.matches('[data-action="cover-toggle"]')) {
      this._debouncedCoverSave(el.dataset.id, el.dataset.field, el.checked);
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
      this._onRuleToggleEnabled(el.dataset.id, el.checked);
      return;
    }

    // Add condition type selector
    if (el.matches('[data-action="rule-add-condition-type"]')) {
      this._onRuleAddCondition(el.dataset.rule, el.value);
      return;
    }

    // Condition param change
    if (el.matches('[data-action="cond-param"]')) {
      this._updateConditionParam(el);
      return;
    }

    // Backup file selected
    if (el.matches('[data-action="backup-file"]')) {
      this._onBackupFileSelected(el);
      return;
    }

    // Scenario rule toggle
    if (el.matches('[data-action="scenario-rule-toggle"]')) {
      this._onScenarioRuleToggle(el.dataset.scenario, el.dataset.rule, el.checked);
      return;
    }

    // Facade direction preset (applies house rotation to get real compass bearings)
    if (el.matches('[data-facade-field="direction"]')) {
      const presets = FACADE_PRESETS[el.value];
      if (presets) {
        const rot = (this._config && this._config.settings) ? (this._config.settings.house_rotation || 0) : 0;
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

    // Cover input fields (debounced save)
    if (el.matches('[data-action="cover-input"]')) {
      let value = el.value;
      if (el.type === "number") value = value === "" ? null : Number(value);
      if (el.type === "text" && value === "") value = null;
      this._debouncedCoverSave(el.dataset.id, el.dataset.field, value);
      return;
    }

    // Condition param input (live update local state)
    if (el.matches('[data-action="cond-param"]')) {
      this._updateConditionParam(el);
      return;
    }

    // Live compass update
    if (el.id === "house-rotation-input") {
      const val = parseFloat(el.value) || 0;
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
      const sorted = Object.values(rules).sort((a, b) => (b.priority || 0) - (a.priority || 0));
      const ids = sorted.map(r => r.id);
      const fromIdx = ids.indexOf(draggedId);
      const toIdx = ids.indexOf(targetId);
      if (fromIdx !== -1 && toIdx !== -1) {
        ids.splice(fromIdx, 1);
        ids.splice(toIdx, 0, draggedId);
        try {
          const result = await this._ws("cover_automatic/rule/reorder", { rule_ids: ids });
          this._updateConfigFromResult(result);
        } catch (err) { console.error(err); }
      }
    }
    this._dragRuleId = null;
    this._dragOverId = null;
  }

  /* ---------- Action handlers ---------- */
  async _onCoverResume(entityId) {
    try {
      const result = await this._ws("cover_automatic/cover/resume", { entity_id: entityId });
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
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
    } catch (e) { console.error(e); }
  }

  _onCoverDelete(entityId) {
    this._showConfirm(this._t("confirm_delete"), async () => {
      try {
        const result = await this._ws("cover_automatic/cover/delete", { entity_id: entityId });
        if (this._selectedCover === entityId) { this._selectedCover = null; this._slideOpen = false; }
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); }
    });
  }

  async _onFacadeAddSave(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = (form.querySelector('[data-facade-field="name"]') || {}).value || "";
    if (!name.trim()) return;
    const direction = (form.querySelector('[data-facade-field="direction"]') || {}).value || "south";
    const azStart = (() => { const v = (form.querySelector('[data-facade-field="azimuth_start"]') || {}).value; return v !== "" && v != null ? parseFloat(v) : 135; })();
    const azEnd = (() => { const v = (form.querySelector('[data-facade-field="azimuth_end"]') || {}).value; return v !== "" && v != null ? parseFloat(v) : 225; })();
    const minElev = parseFloat((form.querySelector('[data-facade-field="min_elevation"]') || {}).value) || 0;
    const coverIds = [];
    form.querySelectorAll('[data-action="facade-cover-toggle"].selected').forEach(b => coverIds.push(b.dataset.cover));
    try {
      const result = await this._ws("cover_automatic/facade/add", {
        name: name.trim(), direction, azimuth_start: azStart, azimuth_end: azEnd, min_elevation: minElev, cover_ids: coverIds
      });
      this._addingFacade = false;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  async _onFacadeEditSave(btn) {
    const facadeId = btn.dataset.id;
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = (form.querySelector('[data-facade-field="name"]') || {}).value || "";
    if (!name.trim()) return;
    const direction = (form.querySelector('[data-facade-field="direction"]') || {}).value || "south";
    const azStart = (() => { const v = (form.querySelector('[data-facade-field="azimuth_start"]') || {}).value; return v !== "" && v != null ? parseFloat(v) : 135; })();
    const azEnd = (() => { const v = (form.querySelector('[data-facade-field="azimuth_end"]') || {}).value; return v !== "" && v != null ? parseFloat(v) : 225; })();
    const minElev = parseFloat((form.querySelector('[data-facade-field="min_elevation"]') || {}).value) || 0;
    const coverIds = [];
    form.querySelectorAll('[data-action="facade-cover-toggle"].selected').forEach(b => coverIds.push(b.dataset.cover));
    try {
      const result = await this._ws("cover_automatic/facade/update", {
        facade_id: facadeId, name: name.trim(), direction, azimuth_start: azStart, azimuth_end: azEnd, min_elevation: minElev, cover_ids: coverIds
      });
      this._editingFacade = null;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  _onFacadeDelete(facadeId) {
    this._showConfirm(this._t("confirm_delete"), async () => {
      try {
        const result = await this._ws("cover_automatic/facade/delete", { facade_id: facadeId });
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); }
    });
  }

  async _onRuleToggleEnabled(ruleId, checked) {
    try {
      const result = await this._ws("cover_automatic/rule/update", { rule_id: ruleId, enabled: checked });
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  _onRuleDelete(ruleId) {
    this._showConfirm(this._t("confirm_delete"), async () => {
      try {
        const result = await this._ws("cover_automatic/rule/delete", { rule_id: ruleId });
        this._expandedRule = null;
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); }
    });
  }

  async _onRuleSave(ruleId) {
    const data = this._collectRuleEditorData(this.shadowRoot, ruleId);
    if (!data) return;
    try {
      const result = await this._ws("cover_automatic/rule/update", data);
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  async _onRuleAddCondition(ruleId, condType) {
    if (!condType) return;
    const rule = (this._config.rules || {})[ruleId];
    if (!rule) return;
    const paramDefs = CONDITION_PARAMS[condType] || [];
    const params = {};
    for (const p of paramDefs) params[p.key] = p.default;
    if (!rule.conditions) rule.conditions = [];
    rule.conditions.push({ type: condType, params: params });
    // Auto-save immediately
    const data = this._collectRuleEditorData(this.shadowRoot, ruleId);
    if (data) {
      try {
        const result = await this._ws("cover_automatic/rule/update", data);
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); }
    } else {
      this._render();
    }
  }

  async _onRuleDeleteCondition(ruleId, idx) {
    const rule = (this._config.rules || {})[ruleId];
    if (rule && rule.conditions) {
      rule.conditions.splice(parseInt(idx, 10), 1);
      // Auto-save immediately (don't require explicit save click)
      const data = this._collectRuleEditorData(this.shadowRoot, ruleId);
      if (data) {
        try {
          const result = await this._ws("cover_automatic/rule/update", data);
          this._updateConfigFromResult(result);
        } catch (e) { console.error(e); }
      } else {
        this._render();
      }
    }
  }

  async _onRuleAddSave(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = (form.querySelector('[data-rule-new-field="name"]') || {}).value || "";
    if (!name.trim()) return;
    const tp = parseInt((form.querySelector('[data-rule-new-field="target_position"]') || {}).value, 10) || 0;
    const ttp = (form.querySelector('[data-rule-new-field="target_tilt_position"]') || {}).value;
    try {
      const data = { name: name.trim(), target_position: tp };
      if (ttp !== "" && ttp != null) data.target_tilt_position = parseInt(ttp, 10);
      const result = await this._ws("cover_automatic/rule/add", data);
      this._addingRule = false;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  _updateConditionParam(el) {
    const ruleId = el.dataset.rule;
    const idx = parseInt(el.dataset.idx, 10);
    const key = el.dataset.key;
    const rule = (this._config.rules || {})[ruleId];
    if (rule && rule.conditions && rule.conditions[idx]) {
      if (!rule.conditions[idx].params) rule.conditions[idx].params = {};
      let val = el.value;
      if (el.type === "number") val = Number(val);
      rule.conditions[idx].params[key] = val;
    }
  }

  _onDayToggle(el) {
    const ruleId = el.dataset.rule;
    const idx = parseInt(el.dataset.idx, 10);
    const key = el.dataset.key;
    const day = el.dataset.day;
    const rule = (this._config.rules || {})[ruleId];
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
    const rule = (this._config.rules || {})[ruleId];
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
    } catch (e) { console.error(e); }
  }

  async _onScenarioRuleToggle(scenarioId, ruleId, checked) {
    const scenario = (this._config.scenarios || {})[scenarioId];
    if (!scenario) return;
    let disabled = [...(scenario.rules_disabled || [])];
    if (checked) {
      disabled = disabled.filter(id => id !== ruleId);
    } else {
      if (!disabled.includes(ruleId)) disabled.push(ruleId);
    }
    try {
      const result = await this._ws("cover_automatic/scenario/update", { scenario_id: scenarioId, rules_disabled: disabled });
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  async _onScenarioAddSave(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = (form.querySelector('[data-scenario-field="name"]') || {}).value || "";
    if (!name.trim()) return;
    const icon = (form.querySelector('[data-scenario-field="icon"]') || {}).value || "mdi:home";
    try {
      const result = await this._ws("cover_automatic/scenario/add", { name: name.trim(), icon: icon });
      this._addingScenario = false;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  async _onScenarioEditSave(btn) {
    const scenarioId = btn.dataset.id;
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = (form.querySelector('[data-scenario-field="name"]') || {}).value || "";
    if (!name.trim()) return;
    const icon = (form.querySelector('[data-scenario-field="icon"]') || {}).value || "mdi:home";
    try {
      const result = await this._ws("cover_automatic/scenario/update", { scenario_id: scenarioId, name: name.trim(), icon: icon });
      this._editingScenario = null;
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  _onScenarioDelete(scenarioId) {
    this._showConfirm(this._t("confirm_delete"), async () => {
      try {
        const result = await this._ws("cover_automatic/scenario/delete", { scenario_id: scenarioId });
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); }
    });
  }

  async _onMasterToggle(checked) {
    try {
      const result = await this._ws("cover_automatic/settings/update", { enabled: checked });
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
  }

  async _onSettingsSave() {
    const data = {};
    this.shadowRoot.querySelectorAll("[data-settings-field]").forEach(input => {
      const field = input.dataset.settingsField;
      let val = input.value;
      if (input.type === "number") {
        val = val === "" ? null : parseFloat(val);
      } else {
        val = val.trim() || null;
      }
      data[field] = val;
    });
    // Validate comfort range
    if (data.comfort_temp_min != null && data.comfort_temp_max != null && data.comfort_temp_min >= data.comfort_temp_max) {
      alert(this._t("settings_validation_min_max"));
      return;
    }
    try {
      const result = await this._ws("cover_automatic/settings/update", data);
      this._updateConfigFromResult(result);
    } catch (e) { console.error(e); }
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
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      alert(this._t("settings_export_error") + ": " + e.message);
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
        alert(this._t("settings_import_error") + ": Invalid JSON");
        return;
      }
      if (!confirm(this._t("settings_import_confirm"))) return;
      try {
        const result = await this._ws("cover_automatic/import", { data });
        this._updateConfigFromResult(result);
        this._showSaved();
        alert(this._t("settings_import_success"));
      } catch (e) {
        console.error(e);
        alert(this._t("settings_import_error") + ": " + e.message);
      }
    };
    reader.readAsText(file);
  }

  _collectRuleEditorData(root, ruleId) {
    const rule = (this._config.rules || {})[ruleId];
    if (!rule) return null;

    // Collect from DOM
    const nameEl = root.querySelector(`[data-action="rule-field"][data-id="${ruleId}"][data-field="name"]`);
    const tpEl = root.querySelector(`[data-action="rule-field"][data-id="${ruleId}"][data-field="target_position"]`);
    const ttpEl = root.querySelector(`[data-action="rule-field"][data-id="${ruleId}"][data-field="target_tilt_position"]`);
    const opEl = root.querySelector(`[data-action="rule-field"][data-id="${ruleId}"][data-field="condition_operator"]`);

    const name = nameEl ? nameEl.value.trim() : rule.name;
    const tp = tpEl && tpEl.value !== "" ? parseInt(tpEl.value, 10) : rule.target_position;
    const ttpVal = ttpEl ? ttpEl.value : null;
    const ttp = (ttpVal !== "" && ttpVal != null) ? parseInt(ttpVal, 10) : null;
    const op = opEl ? opEl.value : rule.condition_operator;

    // Collect selected facades
    const facadeIds = [];
    root.querySelectorAll(`[data-action="rule-facade-toggle"][data-rule="${ruleId}"].selected`).forEach(el => {
      facadeIds.push(el.dataset.facade);
    });

    // Collect selected covers
    const coverIds = [];
    root.querySelectorAll(`[data-action="rule-cover-toggle"][data-rule="${ruleId}"].selected`).forEach(el => {
      coverIds.push(el.dataset.cover);
    });

    // Conditions from local state (updated via change handlers)
    const conditions = (rule.conditions || []).map(c => ({ type: c.type, params: c.params || {} }));

    return {
      rule_id: ruleId,
      name: name,
      target_position: tp,
      target_tilt_position: ttp,
      condition_operator: op,
      facade_ids: facadeIds,
      cover_ids: coverIds,
      conditions: conditions
    };
  }

}

customElements.define("cover-automatic-panel", CoverAutomaticPanel);
