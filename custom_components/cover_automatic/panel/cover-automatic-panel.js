/**
 * CoverAutomatic Config Panel
 * Home Assistant custom panel for intelligent cover/shutter automation.
 * Vanilla web component with Shadow DOM -- no external dependencies.
 */

/* ============================================================
 * Curated scenario icon choices (Material Design Icons)
 * ============================================================ */
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
    active: "Active",
    activate: "Activate",
    name: "Name",
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
    cover_preemptive_shading: "Preemptive shading enabled",
    cover_preemptive_shading_hint: "When enabled, the global solar sensor can trigger shading inside the comfort zone. Disable for rooms where fast warm-up is desired (e.g. bathroom).",
    cover_inverted: "Inverted",
    cover_inverted_hint: "Enable if 100% means closed (reversed motor direction).",
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
    cover_position: "Position",
    cover_position_target_label: "Target",
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
    cond_time_before_sunrise: "Time before sunrise",
    cond_time_before_sunset: "Time before sunset",
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
    scenario_icon: "Icon",
    scenario_icon_custom: "Custom MDI icon",
    scenario_icon_custom_hint: "Enter any Material Design Icon name (e.g. mdi:lightbulb). See materialdesignicons.com for the full list.",
    scenario_no_rules: "No rules configured",
    // Settings
    settings_outdoor_temp: "Outdoor temperature sensor",
    settings_outdoor_temp_short: "Outdoor:",
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
    settings_house_rotation_hint: "Offset from true north (-180 to 180, positive = clockwise). Applied automatically when selecting a facade direction. Drag the house in the compass, hold Shift to snap to 45°.",
    settings_house_rotation_reset: "Reset",
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
    settings_min_position_change: "Default min. position change (%)",
    settings_min_position_change_hint: "Minimum position difference in percent to trigger a move. Can be overridden per cover.",
    settings_min_time: "Default min. time between changes (s)",
    settings_min_time_hint: "Minimum seconds between position changes (motor protection). Can be overridden per cover.",
    settings_command_stagger: "Command stagger delay (s)",
    settings_command_stagger_hint: "Delay in seconds between commands when multiple covers move simultaneously. Recommended 0.3-0.5 for radio-based systems (Z-Wave, Zigbee). 0 = no delay.",
    settings_logbook_enabled: "Write logbook entries",
    settings_logbook_enabled_hint: "Record cover movements, lock/unlock, pause/resume and wind protection in Home Assistant's logbook.",
    settings_current_value: "Current",
    settings_validation_min_max: "Min must be less than max",
    settings_workday_sensor: "Workday sensor",
    settings_workday_hint: "Binary sensor for workday detection (e.g. HA Workday integration). Used by the 'workday' condition type in rules.",
    settings_section_wind: "Wind protection",
    settings_wind_hint: "Safety feature: raises all covers when wind speed exceeds the threshold. Deactivates when speed drops below threshold minus hysteresis.",
    settings_wind_sensor: "Wind speed sensor",
    settings_wind_threshold: "Threshold (activation)",
    settings_wind_hysteresis: "Hysteresis (deactivation difference)",
    settings_section_solar: "Preemptive shading",
    settings_solar_hint: "Sensor for solar radiation (e.g. PV power in W, solar irradiance in W/m\u00B2, or illuminance in lux). When the threshold is exceeded, shading starts within the comfort zone.",
    settings_solar_sensor: "Solar intensity sensor",
    settings_solar_threshold: "Solar intensity threshold",
    settings_solar_threshold_hint: "Shading starts within the comfort zone when this value is exceeded.",
    settings_solar_short: "Solar:",
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
    info_solar_exceeded_title: "Solar above threshold - preemptive shading active",
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
    log_clear: "Clear log",
    log_clear_confirm: "Delete all log entries?",
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
    version_link_title: "Release Notes auf GitHub öffnen",
    update_badge_title: "Update verfügbar – Release Notes auf GitHub öffnen",
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
    active: "Aktiv",
    activate: "Aktivieren",
    name: "Name",
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
    cover_preemptive_shading: "Präventive Beschattung aktiv",
    cover_preemptive_shading_hint: "Wenn aktiv, kann der globale Solarsensor innerhalb der Komfortzone beschatten. Für Räume deaktivieren, in denen die Komforttemperatur schnell erreicht werden soll (z. B. Bad).",
    cover_inverted: "Invertiert",
    cover_inverted_hint: "Aktivieren, wenn 100 % geschlossen bedeutet (umgekehrte Motorrichtung).",
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
    cover_position: "Position",
    cover_position_target_label: "Soll",
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
    cond_time_before_sunrise: "Zeit vor Sonnenaufgang",
    cond_time_before_sunset: "Zeit vor Sonnenuntergang",
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
    scenario_icon: "Icon",
    scenario_icon_custom: "Eigenes MDI-Icon",
    scenario_icon_custom_hint: "Beliebigen Material-Design-Icon-Namen eingeben (z. B. mdi:lightbulb). Vollständige Liste auf materialdesignicons.com.",
    scenario_no_rules: "Keine Regeln konfiguriert",
    settings_outdoor_temp: "Außentemperatur-Sensor",
    settings_outdoor_temp_short: "Außen:",
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
    settings_house_rotation_hint: "Abweichung von exakt Nord (-180 bis 180, positiv = im Uhrzeigersinn). Wird automatisch bei der Fassaden-Richtungswahl angewendet. Haus im Kompass ziehen, mit Shift auf 45° einrasten.",
    settings_house_rotation_reset: "Zurücksetzen",
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
    settings_min_position_change: "Standard min. Positionsänderung (%)",
    settings_min_position_change_hint: "Mindestabweichung in Prozent für eine Fahrt. Kann pro Behang überschrieben werden.",
    settings_min_time: "Standard min. Zeit zwischen Änderungen (s)",
    settings_min_time_hint: "Mindestabstand in Sekunden zwischen Positionsänderungen (Motorschutz). Kann pro Behang überschrieben werden.",
    settings_command_stagger: "Kommando-Verzögerung (s)",
    settings_command_stagger_hint: "Verzögerung in Sekunden zwischen Kommandos, wenn mehrere Behänge gleichzeitig fahren. Empfohlen 0,3-0,5 für Funksysteme (Z-Wave, Zigbee). 0 = keine Verzögerung.",
    settings_logbook_enabled: "Logbuch-Einträge schreiben",
    settings_logbook_enabled_hint: "Bewegungen, Sperren, Pausen und Windschutz im Home-Assistant-Logbuch protokollieren.",
    settings_current_value: "Aktuell",
    settings_validation_min_max: "Min muss kleiner als Max sein",
    settings_workday_sensor: "Arbeitstag-Sensor",
    settings_workday_hint: "Binärsensor zur Arbeitstag-Erkennung (z. B. HA Workday-Integration). Wird vom Bedingungstyp 'Arbeitstag-Sensor' in Regeln verwendet.",
    settings_section_wind: "Windschutz",
    settings_wind_hint: "Sicherheitsfeature: Fährt alle Behänge hoch, wenn die Windgeschwindigkeit den Schwellwert überschreitet. Deaktiviert sich, wenn die Geschwindigkeit unter Schwellwert minus Hysterese fällt.",
    settings_wind_sensor: "Windgeschwindigkeits-Sensor",
    settings_wind_threshold: "Schwellwert (Aktivierung)",
    settings_wind_hysteresis: "Hysterese (Deaktivierungsdifferenz)",
    settings_section_solar: "Pr\u00E4ventive Beschattung",
    settings_solar_hint: "Sensor f\u00FCr Sonneneinstrahlung (z.\u00A0B. PV-Leistung in W, Solarstrahlung in W/m\u00B2 oder Helligkeit in Lux). Bei \u00DCberschreitung des Schwellwerts wird bereits innerhalb der Komfortzone beschattet.",
    settings_solar_sensor: "Solarintensit\u00E4ts-Sensor",
    settings_solar_threshold: "Solarintensit\u00E4ts-Schwellwert",
    settings_solar_threshold_hint: "Beschattung beginnt innerhalb der Komfortzone, wenn dieser Wert \u00FCberschritten wird.",
    settings_solar_short: "Solar:",
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
    info_solar_exceeded_title: "Solar über Schwellwert – präventive Beschattung aktiv",
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
    log_clear: "Protokoll leeren",
    log_clear_confirm: "Alle Protokolleinträge löschen?",
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
  "time_before_sunrise", "time_before_sunset",
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
  time_before_sunrise: [{ key: "offset", type: "number", default: 0 }],
  time_before_sunset: [{ key: "offset", type: "number", default: -60 }],
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
  #compass-house:hover rect { stroke-width: 2.5; }
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
  .pos-bar-track {
    position: relative;
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
  }
  .section {
    border-top: 1px solid var(--ca-border);
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

  /* Compass */
  .compass-svg-root {
    display: block;
  }

  /* Hysteresis badge size tweak */
  .hysteresis-badge {
    font-size: 11px;
  }

  /* Temperature cell -- mode color is still inline because it's dynamic, but weight is consistent */
  .data-table td.temp-mode {
    font-weight: 600;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .panel-container { padding: 8px; }
    .card-grid { grid-template-columns: 1fr; }
    .slide-panel { width: 100vw; }
    .form-row { grid-template-columns: 1fr; }
    .tab-bar button { padding: 10px 14px; font-size: 13px; }
    .data-table th, .data-table td { padding: 10px 12px; font-size: 13px; }
    .data-table td.row-chevron { display: none; }
    .data-table th.row-chevron-head { display: none; }
    /* Settings: sidebar collapses to horizontal scrollable pill strip */
    .settings-shell {
      flex-direction: column;
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
    }
    .settings-nav::-webkit-scrollbar { display: none; }
    .settings-nav-btn {
      flex: 0 0 auto;
      padding: 8px 12px;
      font-size: 13px;
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
    this._coverSort = { key: "name", dir: "asc" };
    this._liveRefreshTimer = null;
    this._eventUnsub = null;
    this._eventDebounce = null;
    this._expandedSections = { base: true, sensors: true, advanced: false, tilt: false };
    this._activeSettingsSection = "house";


    this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    const prevLang = this._hass && this._hass.language;
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
      return;
    }
    if (hass && hass.language !== prevLang) {
      this._render();
      return;
    }
    if (this._config) {
      const shell = this.shadowRoot ? this.shadowRoot.querySelector(".panel-container") : null;
      if (shell) this._updateRegion(shell, "header", this._renderHeaderContent());
      if (this._activeTab === "covers") this._updateLiveCells();
    }
  }

  set panel(panel) {
    this._panel = panel;
  }

  disconnectedCallback() {
    this._stopLiveRefresh();
    this._unsubscribeUpdates();
    this._removeHouseDragListeners();
    if (this._saveTimers) {
      Object.values(this._saveTimers).forEach(t => clearTimeout(t));
      this._saveTimers = {};
    }
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
    if (this._eventUnsub || !this._hass) return;
    this._hass.connection.subscribeEvents((ev) => {
      if (this._activeTab !== "covers" || !this._config) return;
      if (this._eventDebounce) clearTimeout(this._eventDebounce);
      this._eventDebounce = setTimeout(() => {
        this._eventDebounce = null;
        this._refreshLiveCovers();
      }, 500);
    }, "cover_automatic_updated").then((unsub) => {
      this._eventUnsub = unsub;
    }).catch((err) => {
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
    const key = `${entityId}.${field}`;
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
    const el = shell.querySelector(`[data-region="${name}"]`);
    if (el) el.innerHTML = html;
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

    html += `<div class="panel-header" data-region="header">${this._renderHeaderContent()}</div>`;
    html += `<div class="tab-bar" data-region="tabs">${this._renderTabsContent()}</div>`;
    html += `<div class="tab-content" data-region="content">${this._renderContent()}</div>`;
    html += `<div data-region="slideout">${this._renderSlideOut()}</div>`;
    html += `<div data-region="confirm">${this._renderConfirmDialog()}</div>`;
    html += '</div>';
    html += `<div class="toast">${this._t("saved")}</div>`;

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
    html += this._renderInfoBarInline();
    if (activeScenario) {
      html += '<span class="scenario-badge">' + (activeScenario.icon ? '<ha-icon icon="' + this._esc(activeScenario.icon) + '" class="scenario-badge-icon"></ha-icon>' : '') + this._esc(activeScenario.name) + '</span>';
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

  _renderInfoBarInline() {
    const sunState = this._hass && this._hass.states ? this._hass.states["sun.sun"] : null;
    const settings = this._config ? this._config.settings || {} : {};
    const tempEntity = settings.outdoor_temp_sensor;
    const tempState = tempEntity && this._hass && this._hass.states ? this._hass.states[tempEntity] : null;
    const tempVal = tempState && tempState.state !== "unavailable" && tempState.state !== "unknown" ? parseFloat(tempState.state) : null;
    const az = sunState && sunState.attributes ? sunState.attributes.azimuth : null;
    const el = sunState && sunState.attributes ? sunState.attributes.elevation : null;
    const weatherEntity = settings.weather_entity;
    const weatherState = weatherEntity && this._hass && this._hass.states ? this._hass.states[weatherEntity] : null;
    const weatherVal = weatherState && weatherState.state !== "unavailable" && weatherState.state !== "unknown" ? weatherState.state : null;
    const solarEntity = settings.solar_sensor;
    const solarState = solarEntity && this._hass && this._hass.states ? this._hass.states[solarEntity] : null;
    const solarVal = solarState && solarState.state !== "unavailable" && solarState.state !== "unknown" ? parseFloat(solarState.state) : null;
    if (az == null && el == null && tempVal == null && weatherVal == null && solarVal == null) return '';
    const belowHorizon = el != null && el < 0;
    const sunIcon = belowHorizon
      ? '<svg class="info-bar-icon" width="14" height="14" viewBox="0 0 24 24"><path d="M12 2a9.9 9.9 0 00-3.24.53A7 7 0 0015 9a7 7 0 01-6.47 6.97A9.98 9.98 0 0012 22c5.52 0 10-4.48 10-10S17.52 2 12 2z" fill="currentColor" opacity="0.65"/></svg>'
      : this._sunIconSvg(14);
    let widgets = [];
    if (az != null && el != null) {
      const sunTitle = this._t("info_sun_title") || "Sonnenposition";
      widgets.push('<span class="info-widget" title="' + this._esc(sunTitle) + '">' + sunIcon + '<span class="info-widget-value">' + Number(az).toFixed(1) + '\u00B0 / ' + Number(el).toFixed(1) + '\u00B0</span></span>');
    }
    if (tempVal != null) {
      const tempTitle = this._t("info_outdoor_title") || "Au\u00DFentemperatur";
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
      const threshold = settings.solar_threshold != null ? settings.solar_threshold : 0;
      const exceeded = threshold > 0 && solarVal > threshold;
      const unit = solarState.attributes && solarState.attributes.unit_of_measurement ? ' ' + solarState.attributes.unit_of_measurement : '';
      const solarTitle = exceeded ? (this._t("info_solar_exceeded_title") || "Solar \u00FCber Schwellwert \u2013 Beschattung aktiv") : (this._t("info_solar_title") || "Solarintensit\u00E4t");
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

  // Combined position bar: single column shows current + target with a marker when they differ
  _posBarCombined(current, target) {
    if (current == null && target == null) return '\u2013';
    const diverges = current != null && target != null && Math.abs(current - target) >= 1;
    if (!diverges) {
      const p = current != null ? current : target;
      return this._posBar(p);
    }
    // Two-stop fill: solid up to min(current,target), striped from min to max, empty beyond.
    // The solid portion is the position that is "guaranteed" reached; the striped portion is the delta in flux.
    const c = Math.max(0, Math.min(100, current));
    const t = Math.max(0, Math.min(100, target));
    const lo = Math.min(c, t);
    const hi = Math.max(c, t);
    const rangeWidth = hi - lo;
    const title = this._t("cover_position_target_label") + ": " + target + "%";
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
      sliders: '<line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/><line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/><line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/>',
      move_vertical: '<polyline points="8 18 12 22 16 18"/><polyline points="8 6 12 2 16 6"/><line x1="12" x2="12" y1="2" y2="22"/>',
      activity: '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.5.5 0 0 1-.96 0L9.24 2.18a.5.5 0 0 0-.96 0l-2.35 8.36A2 2 0 0 1 4 12H2"/>',
      sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>'
    };
    return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="' + a + '">' + (paths[name] || '') + '</svg>';
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
      return `<th class="sortable${active ? " sorted" : ""}" data-action="cover-sort" data-sort="${key}">${label}<span class="sort-arrow">${arrow}</span></th>`;
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
          const ta = sa && this._hass && this._hass.states && this._hass.states[sa] ? parseFloat(this._hass.states[sa].state) : -999;
          const tb = sb && this._hass && this._hass.states && this._hass.states[sb] ? parseFloat(this._hass.states[sb].state) : -999;
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
      const haState = this._hass && this._hass.states ? this._hass.states[c.entity_id] : null;
      const currentPos = haState && haState.attributes ? haState.attributes.current_position : null;
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
      const ruleName = live.rule_name || this._t("cover_no_rule");
      const ruleCellHtml = this._renderRuleCell(live);
      // Sun on facade
      const liveFacade = c.facade_id ? ((this._config.live_facades || {})[c.facade_id] || {}) : {};
      const sunIcon = liveFacade.sun_on_facade ? ' <span class="live-icon-sun" title="' + this._esc(this._t("facade_sun_active")) + '">' + this._sunIconSvg(12) + '</span>' : '';
      // Last change
      const lastChange = live.last_change ? this._formatTimeAgo(live.last_change) : "";
      // Pause info
      const pauseLeft = (c.status === "paused" && live.pause_until) ? this._formatPauseRemaining(live.pause_until) : "";
      const resumeBtn = c.status === "paused" ? '<button class="btn-icon resume-x" data-action="cover-resume" data-id="' + this._esc(c.entity_id) + '" title="' + this._esc(this._t("cover_resume")) + '">&#10005;</button>' : '';
      html += `<tr class="${selected}" data-action="select-cover" data-id="${this._esc(c.entity_id)}">`;
      html += `<td data-live-name="${this._esc(c.entity_id)}">${this._esc(c.name)}</td>`;
      html += `<td class="nowrap" data-live-facade="${this._esc(c.entity_id)}">${this._esc(facadeName)}${sunIcon}</td>`;
      html += `<td class="nowrap" data-live-status="${this._esc(c.entity_id)}"><span class="status-badge ${statusClass}">${this._esc(this._t("status_" + (c.status || "auto")) || c.status || "auto")}</span>${pauseLeft ? '<span class="pause-remaining">' + pauseLeft + '</span>' : ''}${resumeBtn}</td>`;
      const tempSensor = c.indoor_temp_sensor || (this._config.settings || {}).indoor_temp_sensor;
      const tempState = tempSensor && this._hass && this._hass.states ? this._hass.states[tempSensor] : null;
      const tempVal = tempState && tempState.state !== "unavailable" && tempState.state !== "unknown" ? parseFloat(tempState.state) : null;
      const tempColor = cm === "cooling" ? "var(--ca-info)" : cm === "heating" ? "var(--ca-danger)" : "";
      const tempTitle = cm ? this._t("comfort_" + cm) : "";
      html += `<td class="nowrap${tempColor ? ' temp-mode' : ''}" data-live-temp="${this._esc(c.entity_id)}"${tempColor ? ' style="color:' + tempColor + '"' : ''}${tempTitle ? ' title="' + this._esc(tempTitle) + '"' : ''}>${tempVal != null ? tempVal.toFixed(1) + " °C" : "–"}</td>`;
      html += `<td class="pos-cell" data-live-position="${this._esc(c.entity_id)}">${this._posBarCombined(currentPos, targetPos)}${infoIcon}</td>`;
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
        const globalPause = (this._config.settings || {}).pause_duration != null ? this._config.settings.pause_duration : 10;
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
        const preemptiveOn = cover.preemptive_shading !== false;
        s += this._renderToggle("cover_preemptive_shading", preemptiveOn, "cover-toggle", cover.entity_id, "preemptive_shading");
        s += this._hint("cover_preemptive_shading_hint");
        s += `<div class="form-group">
          <label>${this._t("cover_lock_sensor")}</label>
          ${this._renderCoverEntitySelect("lock_sensor", cover.lock_sensor, cover.entity_id, "binary_sensor", null)}
          ${this._hint("cover_lock_sensor_hint")}
        </div>`;
        const globalLockPos = (this._config.settings || {}).lock_position != null ? this._config.settings.lock_position : 100;
        s += `<div class="form-group">
          <label>${this._t("cover_lock_position")}</label>
          <input type="number" min="0" max="100" value="${cover.lock_position != null ? cover.lock_position : ""}" placeholder="${globalLockPos}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="lock_position">
          ${this._hint("cover_lock_position_hint")}
        </div>`;
        s += `<div class="form-group">
          <label>${this._t("cover_vent_sensor")}</label>
          ${this._renderCoverEntitySelect("vent_sensor", cover.vent_sensor, cover.entity_id, "binary_sensor", null)}
          ${this._hint("cover_vent_sensor_hint")}
        </div>`;
        const globalVentPos = (this._config.settings || {}).vent_position != null ? this._config.settings.vent_position : 30;
        s += `<div class="form-group">
          <label>${this._t("cover_vent_position")}</label>
          <input type="number" min="0" max="100" value="${cover.vent_position != null ? cover.vent_position : ""}" placeholder="${globalVentPos}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="vent_position">
          ${this._hint("cover_vent_position_hint")}
        </div>`;
        return s;
      });

      // Section: Advanced
      html += this._renderSection("advanced", this._t("cover_section_advanced"), () => {
        let s = '';
        s += this._renderToggle("cover_inverted", cover.inverted, "cover-toggle", cover.entity_id, "inverted");
        s += this._hint("cover_inverted_hint");
        const globalMinChange = (this._config.settings || {}).min_position_change != null ? this._config.settings.min_position_change : 5;
        s += `<div class="form-group">
          <label>${this._t("cover_min_pos_change")}</label>
          <input type="number" min="1" max="50" value="${cover.min_position_change != null ? cover.min_position_change : ""}" placeholder="${globalMinChange}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="min_position_change">
          ${this._hint("cover_min_pos_change_hint")}
        </div>`;
        const globalMinTime = (this._config.settings || {}).min_time_between_changes != null ? this._config.settings.min_time_between_changes : 300;
        s += `<div class="form-group">
          <label>${this._t("cover_min_time")}</label>
          <input type="number" min="60" max="3600" value="${cover.min_time_between_changes != null ? cover.min_time_between_changes : ""}" placeholder="${globalMinTime}" data-action="cover-input" data-id="${this._esc(cover.entity_id)}" data-field="min_time_between_changes">
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

      html += `<div class="slide-delete-wrap">
        <button class="btn btn-danger" data-action="cover-delete" data-id="${this._esc(cover.entity_id)}">${this._t("cover_remove")}</button>
      </div>`;
      html += '</div>'; // slide-body
    }

    html += '</div>'; // slide-panel
    return html;
  }

  _renderSection(id, title, contentFn) {
    const expanded = this._expandedSections[id];
    const arrowClass = expanded ? "arrow expanded" : "arrow";
    const iconMap = { base: "info", sensors: "gauge", advanced: "sliders", tilt: "move_vertical" };
    const iconName = iconMap[id];
    const icon = iconName ? `<span class="section-icon">${this._lucideIcon(iconName, 16)}</span>` : "";
    return `<div class="section">
      <div class="section-header" data-action="toggle-section" data-section="${id}">
        ${icon}<span class="section-title">${this._esc(title)}</span>
        <span class="${arrowClass}">&#9654;</span>
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
          <span>${this._t("facade_azimuth_start")}: ${f.azimuth_start}&#176;</span>
          <span>${this._t("facade_azimuth_end")}: ${f.azimuth_end}&#176;</span>
        </div>
        <div class="facade-covers-intro">
          ${this._t("facade_min_elevation")}: ${f.min_elevation}&#176;
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
    const sorted = Object.values(rules).sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));

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
      html += `<span class="drag-handle" title="Drag">&#9783;</span>`;
      html += `<div class="rule-info" data-action="rule-expand" data-id="${this._esc(r.id)}">`;
      html += `<div class="rule-name">`;
      html += `<span class="rule-active-dot ${isActive ? "active" : ""}" title="${isActive ? this._t("rule_active_for") + " " + matchedCovers.length + " " + this._t("rule_covers_count") : this._t("rule_inactive")}"></span>`;
      html += `${this._esc(r.name)}</div>`;
      html += '<div class="rule-meta">';
      html += `<span class="priority-badge">#${idx + 1}</span>`;
      html += `<span>${r.condition_operator === "or" ? "OR" : "AND"}</span>`;
      html += `<span class="rule-target">${this._t("rule_target_pos")}:${this._posBar(r.target_position, "compact")}</span>`;
      if (r.target_tilt_position != null) {
        html += `<span class="rule-target">${this._t("rule_target_tilt")}:${this._posBar(r.target_tilt_position, "compact")}</span>`;
      }
      html += '</div>';
      // Condition chips
      if (r.conditions && r.conditions.length > 0) {
        html += '<div class="chip-group mt-6">';
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
      html += `<button class="btn btn-primary mt-16" data-action="rule-add-start">+ ${this._t("rule_add")}</button>`;
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
    html += `<div class="rule-conditions-label">${this._t("rule_conditions")}</div>`;

    if (rule.conditions && rule.conditions.length > 0) {
      for (let i = 0; i < rule.conditions.length; i++) {
        html += this._renderConditionCard(rule, i);
      }
    } else {
      html += `<div class="rule-no-conditions">${this._t("rule_no_conditions")}</div>`;
    }

    // Add condition
    html += `<div class="rule-condition-add">
      <select class="rule-condition-type-select" data-action="rule-add-condition-type" data-rule="${this._esc(rule.id)}">
        <option value="">${this._t("rule_add_condition")}...</option>
        ${CONDITION_TYPES.map(t => `<option value="${t}">${this._t("cond_" + t)}</option>`).join("")}
      </select>
    </div>`;

    // Save button
    html += `<div class="rule-editor-actions">
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
    let html = `<div class="inline-form mt-16">
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
      html += `<div class="scenario-no-rules">${this._t("scenario_no_rules")}</div>`;
    } else {
      for (const r of ruleEntries) {
        const disabled = (sc.rules_disabled || []).includes(r.id);
        html += `<div class="sc-rule-row">
          <span${disabled ? ' class="sc-rule-disabled"' : ""}>${this._esc(r.name)}</span>
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
    return '<div class="sensor-current-value">' + this._t("settings_current_value") + ': ' + this._esc(val) + this._esc(u) + '</div>';
  }

  _renderCompassSVG(rotation) {
    const cx = 140, cy = 140, r = 88, hr = 28;
    const sunState = this._hass ? this._hass.states["sun.sun"] : null;
    const sunAz = sunState ? parseFloat(sunState.attributes.azimuth) : null;
    const sunEl = sunState ? parseFloat(sunState.attributes.elevation) : null;
    const belowHorizon = sunEl != null && sunEl < 0;

    // Facade arcs -- muted, harmonized palette (same saturation, varying hue)
    const facades = this._config ? Object.values(this._config.facades || {}) : [];
    let facadeArcs = "";
    const facadeColors = ["#7da7c8", "#7fb89e", "#c4a979", "#c98969", "#b878a1", "#8a7eb5"];
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
      facadeArcs += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="central" font-size="9" fill="${facadeColors[i % facadeColors.length]}" font-weight="600">${this._esc(f.name.substring(0, 8))}</text>`;
    });

    // Sun position
    let sunMarker = "";
    let sunBeams = "";
    if (sunAz != null && !isNaN(sunAz) && !belowHorizon) {
      const sunRad = (sunAz - 90) * Math.PI / 180;
      const sr = r + 28;
      const sx = cx + sr * Math.cos(sunRad), sy = cy + sr * Math.sin(sunRad);
      // Sun symbol rays (radiating outward)
      const symbolRays = [0,45,90,135,180,225,270,315].map(d => {
        const rr = d * Math.PI / 180;
        const x1 = sx + 10 * Math.cos(rr), y1 = sy + 10 * Math.sin(rr);
        const x2 = sx + 15 * Math.cos(rr), y2 = sy + 15 * Math.sin(rr);
        return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--ca-sun)" stroke-width="2" stroke-linecap="round"/>`;
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
      sunBeams = `<polygon points="${sx + perpX * sunW},${sy + perpY * sunW} ${sx - perpX * sunW},${sy - perpY * sunW} ${fx - perpX * facadeW},${fy - perpY * facadeW} ${fx + perpX * facadeW},${fy + perpY * facadeW}" fill="var(--ca-sun)" opacity="0.08"/>`;
      sunMarker = `${symbolRays}<circle cx="${sx}" cy="${sy}" r="8" fill="var(--ca-sun)" stroke="var(--ca-sun-outline)" stroke-width="1.5"/>
        <text x="${sx}" y="${sy + 26}" text-anchor="middle" font-size="9" fill="var(--ca-sun)" font-weight="700">\u2220${Math.round(sunEl)}\u00B0</text>`;
    }

    // Outdoor temperature info text at bottom of SVG
    let infoText = "";
    const settings = this._config ? this._config.settings || {} : {};
    const tempEntity = settings.outdoor_temp_sensor;
    if (tempEntity && this._hass && this._hass.states[tempEntity]) {
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
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.45"/>
        </filter>
      </defs>
      <!-- Compass circle -->
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--divider-color)" stroke-width="1.5"/>
      <circle cx="${cx}" cy="${cy}" r="${r - 20}" fill="none" stroke="var(--divider-color)" stroke-width="0.5" stroke-dasharray="3,3"/>
      <!-- Cardinal directions (fixed) -->
      <text x="${cx}" y="${cy - r - 6}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--primary-text-color)">N</text>
      <text x="${cx}" y="${cy + r + 18}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--primary-text-color)">S</text>
      <text x="${cx + r + 10}" y="${cy + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--primary-text-color)">E</text>
      <text x="${cx - r - 10}" y="${cy + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--primary-text-color)">W</text>
      <!-- Tick marks -->
      ${[0,45,90,135,180,225,270,315].map(d => { const rad=(d-90)*Math.PI/180; const i=d%90===0?10:6; return `<line x1="${cx+(r-i)*Math.cos(rad)}" y1="${cy+(r-i)*Math.sin(rad)}" x2="${cx+r*Math.cos(rad)}" y2="${cy+r*Math.sin(rad)}" stroke="var(--primary-text-color)" stroke-width="${d%90===0?2:1}" opacity="${d%90===0?0.8:0.4}"/>`; }).join("")}
      <!-- Sun beams (behind house) -->
      ${sunBeams}
      <!-- House (rotated, on top of beams) -->
      <g id="compass-house" transform="rotate(${rotation}, ${cx}, ${cy})" data-action="house-drag-start" filter="url(#ca-house-shadow)">
        <rect x="${cx - hr}" y="${cy - hr}" width="${hr * 2}" height="${hr * 2}" rx="3" fill="var(--primary-background-color, #1c1c1c)" stroke="var(--primary-color)" stroke-width="2"/>
        <rect x="${cx - hr + 1.5}" y="${cy - hr + 1.5}" width="${hr * 2 - 3}" height="${hr * 2 - 3}" rx="2" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1" pointer-events="none"/>
        <!-- Roof indicator (front = south of house before rotation) -->
        <line x1="${cx - hr + 6}" y1="${cy + hr}" x2="${cx + hr - 6}" y2="${cy + hr}" stroke="var(--primary-color)" stroke-width="2" stroke-linecap="round" pointer-events="none"/>
        <text id="compass-degree-label" x="${cx}" y="${cy + 4}" text-anchor="middle" font-size="11" fill="var(--primary-text-color)" opacity="0.6" pointer-events="none">${rotation}°</text>
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
    const active = this._activeSettingsSection || "house";

    const sections = [
      { id: "house", labelKey: "settings_section_house", icon: this._lucideIcon("house", 16) },
      { id: "sensors", labelKey: "settings_section_sensors", icon: this._lucideIcon("gauge", 16) },
      { id: "comfort", labelKey: "settings_section_comfort", icon: this._lucideIcon("thermometer", 16) },
      { id: "wind", labelKey: "settings_section_wind", icon: this._lucideIcon("wind", 16) },
      { id: "solar", labelKey: "settings_section_solar", icon: this._lucideIcon("sun", 16) },
      { id: "automation", labelKey: "settings_section_automation", icon: this._lucideIcon("cog", 16) },
      { id: "backup", labelKey: "settings_section_backup", icon: this._lucideIcon("archive", 16) }
    ];

    let html = '<div class="settings-shell">';

    // Sidebar navigation
    html += '<aside class="settings-nav" role="tablist" aria-label="' + this._esc(this._t("tabs") && typeof this._t("tabs") === "object" ? "Settings" : "Settings") + '">';
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
      const rot = s.house_rotation != null ? s.house_rotation : 0;
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
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_outdoor_temp")}</label>
            ${this._renderEntitySelect("outdoor_temp_sensor", s.outdoor_temp_sensor, "sensor", "temperature")}
            ${this._renderSensorValue(s.outdoor_temp_sensor, "\u00B0")}
            ${hint(this._t("settings_outdoor_temp_hint"))}
          </div>
          <div class="form-group">
            <label>${this._t("settings_indoor_temp")}</label>
            ${this._renderEntitySelect("indoor_temp_sensor", s.indoor_temp_sensor, "sensor", "temperature")}
            ${this._renderSensorValue(s.indoor_temp_sensor, "\u00B0")}
            ${hint(this._t("settings_indoor_temp_hint"))}
          </div>
        </div>
        <div class="form-row">
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
        </div>
      </div>
    </div>`;
    }

    // Comfort section
    if (active === "comfort") {
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("thermometer")} ${this._t("settings_section_comfort")}</div>
      <div class="card-body">
        ${hintIntro(this._t("settings_comfort_hint"))}
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_comfort_min")}</label>
            <input type="number" step="0.5" value="${s.comfort_temp_min != null ? s.comfort_temp_min : 21}" data-settings-field="comfort_temp_min">
          </div>
          <div class="form-group">
            <label>${this._t("settings_comfort_max")}</label>
            <input type="number" step="0.5" value="${s.comfort_temp_max != null ? s.comfort_temp_max : 25}" data-settings-field="comfort_temp_max">
          </div>
        </div>
        <div class="form-group">
          <label>${this._t("settings_comfort_hysteresis")}</label>
          <input type="number" step="0.1" min="0.1" max="5" value="${s.comfort_hysteresis != null ? s.comfort_hysteresis : 1}" data-settings-field="comfort_hysteresis">
          ${hint(this._t("settings_comfort_hysteresis_hint"))}
        </div>
      </div>
    </div>`;
    }

    // Wind section
    if (active === "wind") {
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("wind")} ${this._t("settings_section_wind")}</div>
      <div class="card-body">
        ${hintIntro(this._t("settings_wind_hint"))}
        <div class="form-group">
          <label>${this._t("settings_wind_sensor")}</label>
          ${this._renderEntitySelect("wind_sensor", s.wind_sensor, "sensor", "wind_speed")}
          ${this._renderSensorValue(s.wind_sensor, " km/h")}
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_wind_threshold")}</label>
            <input type="number" step="1" min="0" value="${s.wind_speed_threshold != null ? s.wind_speed_threshold : 0}" data-settings-field="wind_speed_threshold">
          </div>
          <div class="form-group">
            <label>${this._t("settings_wind_hysteresis")}</label>
            <input type="number" step="1" min="0" value="${s.wind_speed_hysteresis != null ? s.wind_speed_hysteresis : 0}" data-settings-field="wind_speed_hysteresis">
          </div>
        </div>
      </div>
    </div>`;
    }

    // Solar section
    if (active === "solar") {
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("sun", 18)} ${this._t("settings_section_solar")}</div>
      <div class="card-body">
        ${hintIntro(this._t("settings_solar_hint"))}
        <div class="form-group">
          <label>${this._t("settings_solar_sensor")}</label>
          ${this._renderEntitySelect("solar_sensor", s.solar_sensor, "sensor")}
          ${this._renderSensorValue(s.solar_sensor)}
        </div>
        <div class="form-group">
          <label>${this._t("settings_solar_threshold")}</label>
          <input type="number" step="100" min="0" value="${s.solar_threshold != null ? s.solar_threshold : 0}" data-settings-field="solar_threshold">
          ${hint(this._t("settings_solar_threshold_hint"))}
        </div>
      </div>
    </div>`;
    }

    // Automation section
    if (active === "automation") {
      html += `<div class="card">
      <div class="card-header">${this._lucideIcon("cog")} ${this._t("settings_section_automation")}</div>
      <div class="card-body">
        <div class="form-group">
          <label>${this._t("settings_pause_duration")}</label>
          <input type="number" min="1" max="480" value="${s.pause_duration != null ? s.pause_duration : 10}" data-settings-field="pause_duration">
          ${hint(this._t("settings_pause_duration_hint"))}
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_lock_position")}</label>
            <input type="number" min="0" max="100" value="${s.lock_position != null ? s.lock_position : 100}" data-settings-field="lock_position">
            ${hint(this._t("settings_lock_position_hint"))}
          </div>
          <div class="form-group">
            <label>${this._t("settings_vent_position")}</label>
            <input type="number" min="0" max="100" value="${s.vent_position != null ? s.vent_position : 30}" data-settings-field="vent_position">
            ${hint(this._t("settings_vent_position_hint"))}
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_lock_tilt_position")}</label>
            <input type="number" min="0" max="100" value="${s.lock_tilt_position != null ? s.lock_tilt_position : ""}" data-settings-field="lock_tilt_position">
            ${hint(this._t("settings_lock_tilt_position_hint"))}
          </div>
          <div class="form-group">
            <label>${this._t("settings_vent_tilt_position")}</label>
            <input type="number" min="0" max="100" value="${s.vent_tilt_position != null ? s.vent_tilt_position : ""}" data-settings-field="vent_tilt_position">
            ${hint(this._t("settings_vent_tilt_position_hint"))}
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>${this._t("settings_min_position_change")}</label>
            <input type="number" min="1" max="50" value="${s.min_position_change != null ? s.min_position_change : 5}" data-settings-field="min_position_change">
            ${hint(this._t("settings_min_position_change_hint"))}
          </div>
          <div class="form-group">
            <label>${this._t("settings_min_time")}</label>
            <input type="number" min="60" max="3600" value="${s.min_time_between_changes != null ? s.min_time_between_changes : 300}" data-settings-field="min_time_between_changes">
            ${hint(this._t("settings_min_time_hint"))}
          </div>
        </div>
        <div class="form-group">
          <label>${this._t("settings_command_stagger")}</label>
          <input type="number" step="0.1" min="0" max="2" value="${s.command_stagger != null ? s.command_stagger : 0}" data-settings-field="command_stagger">
          ${hint(this._t("settings_command_stagger_hint"))}
        </div>
        <div class="form-group">
          <label class="checkbox-row">
            <input type="checkbox" data-settings-field="logbook_enabled" ${s.logbook_enabled !== false ? "checked" : ""}>
            <span>${this._t("settings_logbook_enabled")}</span>
          </label>
          ${hint(this._t("settings_logbook_enabled_hint"))}
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
    if (this._logEntries === null) {
      this._loadLog();
      return '<div class="empty-state">' + this._t("log_loading") + '</div>';
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
      const time = new Date(e.ts * 1000).toLocaleString();
      const typeLabel = this._t("log_type_" + e.type) || e.type;
      const coverName = e.entity_id ? this._getCoverName(e.entity_id) : "–";
      const typeClass = e.type === "wind" ? "status-wind_protected" : e.type === "status" ? "status-paused" : "";
      html += '<tr>';
      html += '<td class="nowrap">' + this._esc(time) + '</td>';
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
      // Combined position cell: current + target with optional divergence marker, plus hysteresis badge
      const haState = this._hass && this._hass.states ? this._hass.states[eid] : null;
      const curPos = haState && haState.attributes ? haState.attributes.current_position : null;
      const live = liveCvrs[eid] || {};
      const tgtPos = live.target_position;
      const hyst = live.hysteresis;
      const posCell = root.querySelector('[data-live-position="' + eid + '"]');
      if (posCell) {
        let barHtml = this._posBarCombined(curPos, tgtPos);
        if (hyst === "position" || hyst === "time") {
          barHtml += ' <span class="status-badge status-paused hysteresis-badge" title="' + this._esc(this._t(hyst === "position" ? "cover_hysteresis_position" : "cover_hysteresis_time")) + '">' + (hyst === "position" ? "\u2195" : "\u23F2") + '</span>';
        }
        posCell.innerHTML = barHtml;
      }
      // Status + pause remaining + resume button
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
      const nCell = root.querySelector('[data-live-name="' + eid + '"]');
      if (nCell && c) {
        nCell.textContent = c.name;
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
          sun.className = "live-icon-sun";
          sun.title = this._t("facade_sun_active");
          // SVG from internal _sunIconSvg() - no user input
          sun.innerHTML = this._sunIconSvg(12);
          fCell.appendChild(document.createTextNode(" "));
          fCell.appendChild(sun);
        }
      }
      // Rule name -- preserve clickable rule-link markup via DOM API (avoids innerHTML)
      const rCell = root.querySelector('[data-live-rule="' + eid + '"]');
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
      const tempCell = root.querySelector('[data-live-temp="' + eid + '"]');
      if (tempCell) {
        const c2 = covers[eid];
        const ts = (c2 && c2.indoor_temp_sensor) || ((this._config.settings || {}).indoor_temp_sensor);
        const tst = ts && this._hass && this._hass.states ? this._hass.states[ts] : null;
        const tv = tst && tst.state !== "unavailable" && tst.state !== "unknown" ? parseFloat(tst.state) : null;
        tempCell.textContent = tv != null ? tv.toFixed(1) + " \u00B0C" : "\u2013";
        const cm2 = live.comfort_mode;
        tempCell.style.color = cm2 === "cooling" ? "var(--ca-info)" : cm2 === "heating" ? "var(--ca-danger)" : "";
        tempCell.style.fontWeight = (cm2 === "cooling" || cm2 === "heating") ? "600" : "";
        tempCell.title = cm2 ? this._t("comfort_" + cm2) : "";
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
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
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
    root.addEventListener("pointerdown", (e) => this._handleHouseDragStart(e));
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
      case "toggle-menu": {
        const ha = document.querySelector("home-assistant");
        const drawer = ha?.shadowRoot?.querySelector("home-assistant-main")?.shadowRoot?.querySelector("ha-drawer");
        if (drawer) { drawer.open = !drawer.open; } else { window.history.back(); }
        break;
      }
      case "retry": this._loadConfig(); break;
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
        this._expandedSections = { base: true, sensors: true, advanced: false, tilt: false };
        this._render();
        break;
      case "goto-rule": {
        e.preventDefault();
        e.stopPropagation();
        const ruleId = actionEl.dataset.ruleId;
        this._activeTab = "rules";
        this._slideOpen = false;
        this._selectedCover = null;
        this._expandedRule = null;
        this._stopLiveRefresh();
        this._render();
        // Scroll-to + highlight after the new tab has rendered
        setTimeout(() => {
          if (!ruleId) return;
          const rEl = this.shadowRoot.querySelector('.rule-row[data-rule-id="' + CSS.escape(ruleId) + '"]');
          if (!rEl) return;
          rEl.scrollIntoView({ behavior: "smooth", block: "center" });
          rEl.classList.add("rule-highlight");
          setTimeout(() => rEl.classList.remove("rule-highlight"), 2000);
        }, 60);
        break;
      }
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
      case "settings-section":
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
      case "scenario-icon-pick": this._onScenarioIconPick(actionEl); break;
      case "settings-save": this._onSettingsSave(); break;
      case "backup-export": this._onBackupExport(); break;
      case "backup-import": { const fi = this.shadowRoot.querySelector('[data-action="backup-file"]'); if (fi) fi.click(); break; }
      case "backup-file": this._onBackupFileSelected(actionEl); break;
      case "log-filter":
        this._logFilter = actionEl.dataset.filter || null;
        this._render();
        break;
      case "log-clear":
        this._showConfirm(this._t("log_clear_confirm"), async () => {
          await this._ws("cover_automatic/log/clear");
          this._logEntries = [];
          this._render();
        });
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

    // Cover input fields (debounced save)
    if (el.matches('[data-action="cover-input"]')) {
      let value = el.value;
      if (el.type === "number") {
        const n = value === "" ? NaN : Number(value);
        value = Number.isFinite(n) ? n : null;
      }
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
      const sorted = Object.values(rules).sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));
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
    const minElev = (() => { const v = (form.querySelector('[data-facade-field="min_elevation"]') || {}).value; return v !== "" && v != null ? parseFloat(v) : 0; })();
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
    const minElev = (() => { const v = (form.querySelector('[data-facade-field="min_elevation"]') || {}).value; return v !== "" && v != null ? parseFloat(v) : 0; })();
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
    // Build next conditions locally; mutate _config only after successful WS call
    const nextConditions = [...(rule.conditions || []), { type: condType, params: params }];
    const data = this._collectRuleEditorData(this.shadowRoot, ruleId, nextConditions);
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
    if (!rule || !rule.conditions) return;
    const idxInt = parseInt(idx, 10);
    if (!Number.isFinite(idxInt)) return;
    // Build next conditions locally; mutate _config only after successful WS call
    const nextConditions = rule.conditions.filter((_, i) => i !== idxInt);
    const data = this._collectRuleEditorData(this.shadowRoot, ruleId, nextConditions);
    if (data) {
      try {
        const result = await this._ws("cover_automatic/rule/update", data);
        this._updateConfigFromResult(result);
      } catch (e) { console.error(e); }
    } else {
      this._render();
    }
  }

  async _onRuleAddSave(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = (form.querySelector('[data-rule-new-field="name"]') || {}).value || "";
    if (!name.trim()) return;
    const tp = (() => { const v = (form.querySelector('[data-rule-new-field="target_position"]') || {}).value; return v !== "" && v != null ? parseInt(v, 10) : 0; })();
    const ttp = (form.querySelector('[data-rule-new-field="target_tilt_position"]') || {}).value;
    try {
      const data = { name: name.trim(), target_position: tp };
      if (ttp !== "" && ttp != null) {
        const n = parseInt(ttp, 10);
        if (Number.isFinite(n)) data.target_tilt_position = n;
      }
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
    const custom = (form.querySelector('[data-scenario-icon-custom]') || {}).value || "";
    if (custom.trim()) return custom.trim();
    const picked = (form.querySelector('[data-scenario-field="icon"]') || {}).value || "";
    return picked.trim() || fallback;
  }

  async _onScenarioAddSave(btn) {
    const form = btn.closest(".inline-form");
    if (!form) return;
    const name = (form.querySelector('[data-scenario-field="name"]') || {}).value || "";
    if (!name.trim()) return;
    const icon = this._readScenarioIcon(form, "mdi:home");
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
    const icon = this._readScenarioIcon(form, "mdi:home");
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
      let val;
      if (input.type === "checkbox") {
        val = input.checked;
      } else if (input.type === "number") {
        val = input.value === "" ? null : parseFloat(input.value);
      } else {
        val = input.value.trim() || null;
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
        this._showToast();
        alert(this._t("settings_import_success"));
      } catch (e) {
        console.error(e);
        alert(this._t("settings_import_error") + ": " + e.message);
      }
    };
    reader.readAsText(file);
  }

  _collectRuleEditorData(root, ruleId, overrideConditions = null) {
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
    const ttp = (() => {
      if (ttpVal === "" || ttpVal == null) return null;
      const n = parseInt(ttpVal, 10);
      return Number.isFinite(n) ? n : null;
    })();
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

    // Conditions from override (pending add/delete) or local state
    const source = overrideConditions != null ? overrideConditions : (rule.conditions || []);
    const conditions = source.map(c => ({ type: c.type, params: c.params || {} }));

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
