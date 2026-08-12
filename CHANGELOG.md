# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.58.0] - 2026-08-12

### Added

- Privacy: opt-out for the panel's update check. New setting "Check for updates" (Settings -> Automation, default on). When disabled, the panel never contacts the GitHub API — no outbound request leaves Home Assistant.

## [1.57.2] - 2026-08-12

### Fixed

- Manifest: removed invalid keys `description` and `homeassistant` (the minimum Home Assistant version remains declared in `hacs.json`) and declared `logbook` as an after-dependency — all flagged by hassfest validation.
- Integration: added `CONFIG_SCHEMA = config_entry_only_config_schema` to make explicit that CoverAutomatic is set up exclusively via config entries (hassfest warning).

### CI

- Added a hassfest validation job (required for HACS default repository inclusion).

## [1.57.1] - 2026-08-12

### Fixed

- Manifest: `documentation` and `issue_tracker` URLs pointed to a non-existent repository slug (`cover_automatic` instead of `CoverAutomatic`), breaking the documentation and issue links shown in the Home Assistant UI.

## [1.57.0] - 2026-07-21

### Changed

- Panel: visual refinement of the house compass in settings. The sun now has a soft radial glow and its light cone fades as a directional gradient toward the facade; facade arcs render in two layers (wide faint underlay, crisp core, round caps); north is marked with a filled accent triangle and an accent-colored "N" as the rotation reference; cardinal letters use quieter secondary-text styling; the house gets a softer drop shadow, a subtle top sheen and finer stroke weights; the inner ring is a fine dotted circle. Drag-rotation behaviour and all interaction paths are unchanged.

## [1.56.0] - 2026-07-21

### Added

- Panel: toast notifications now show a slim countdown bar indicating how long the toast stays visible; rapid consecutive saves restart the countdown. The toast is also announced to screen readers via `role="status"`.
- Panel accessibility: Escape closes the cover slide-out and the confirm dialog; focus moves into the slide-out/dialog when opened. Cover table rows and sortable column headers are keyboard-focusable and activatable via Enter/Space (`aria-sort` on the active sort column). ARIA landmarks (banner/navigation/main) and dialog roles added.

### Changed

- Panel: the horizontal tab bar and the mobile settings pill strip use CSS scroll snapping for cleaner scroll stops on touch devices.
- Panel: the log tab shows a proper spinner while entries are loading instead of a plain text notice.

## [1.55.0] - 2026-06-28

### Added

- Rule editor: live condition preview. Each context-independent condition (sun elevation, time, sun-relative time, `state_is`, weather, day of week, workday) now shows a status dot ("applies" / "doesn't apply") plus its current actual value, polled every 10 s while a rule is expanded. Context-dependent conditions (`sun_on_facade`, `temperature_comfort`) are labelled "context-dependent" since they require a specific cover. New WS command `rule/preview_conditions` evaluates the editor's (unsaved) conditions via the engine — the single source of truth, no frontend logic duplication.

### Fixed

- Rule and scenario changes (add/update/delete/reorder, scenario activate) now trigger an immediate coordinator re-evaluation instead of waiting up to one scan interval (60 s). Mirrors the existing behaviour of settings/resume/import handlers.

## [1.54.1] - 2026-06-28

### Changed

- Panel: the `state_is` entity picker is now a searchable input backed by a `<datalist>` instead of one long `<select>`. Typing filters suggestions by friendly name or entity id; free text stays allowed for entities that are not loaded yet.

## [1.54.0] - 2026-06-28

### Added

- Panel: the entity field of the `state_is` rule condition is now a dropdown picker instead of a free-text field. Entities are grouped by domain via optgroups and sorted by friendly name; a previously stored entity stays selectable even when currently unavailable. Falls back to a text input if entity states are not yet loaded.

## [1.53.10] - 2026-06-22

### Fixed

- Cover status sensor now shows distinct icons for the `VENTING` and `WIND_PROTECTED` states instead of a generic help-circle fallback.
- Removing a cover now cleans up all of its per-cover runtime state (hysteresis info, matching/move-rule tracking, pending-settle and protective-exit sets), not just the position/status dicts -- prevents a slow state leak on repeated cover deletion.
- Panel re-subscribes to the real-time update event and restarts the live refresh on reconnect. HA caches custom panels and detaches/re-attaches them on navigation; previously both went silent after the first disconnect, leaving the covers tab without live updates.
- Vent sensor closing on a cover with automation disabled now returns it to `MANUAL` instead of `AUTO`, mirroring the status-sync path, so no `AUTO` apply cycle runs on a disabled cover before the next sync corrects it.

### Security

- WebSocket API now validates rule references in `scenario/add`, `scenario/update` (`rules_disabled`) and `rule/reorder` (`rule_ids`), rejecting unknown ids with `not_found`. Closes the reference-validation gap left open relative to v1.53.7. +5 regression tests.

### Changed

- Panel: number condition-parameter inputs are coerced through the `_num()` helper like every other numeric field (defense-in-depth; no behavior change for valid values).
- Internal cleanups (no behavior change): removed a dead i18n ternary, a dead variable and three duplicate CSS rules in the panel, dropped an unused event-callback parameter, and simplified a nested ternary in the rule model.

## [1.53.9] - 2026-06-22

### Security

- Config import path validation now confines paths to the real HA config directory (`hass.config.config_dir`) only, instead of a hardcoded `/config` + `/homeassistant` list that silently tolerated non-existent bases (reduces attack surface).
- Panel: storage-derived numeric form fields are coerced through a `_num()` helper before HTML-attribute interpolation (defense-in-depth against hand-edited `.storage` files; the WebSocket schema already enforces numerics on write).

### Changed

- `read_text()` calls now pass `encoding="utf-8"` explicitly (PEP 597), avoiding locale-dependent decoding.
- Data model dataclasses use `slots=True` for a smaller memory footprint and faster attribute access.

### Documentation

- README: added a Privacy section documenting the anonymous GitHub update check and the personal-reference potential of exported entity IDs.

## [1.53.8] - 2026-06-22

### Changed

- Panel internals modernized (no behavior change): optional chaining (`this._hass?.states`), nullish coalescing (`?? default` in place of `x != null ? x : default`), object spread, `for...of`, and `?.value` element access in form readers. Empty-string-to-default semantics on form fields were deliberately preserved (kept `|| default`, not switched to `??`).

## [1.53.7] - 2026-06-22

### Security

- WebSocket API now validates entity references against existing config: `cover/update` (`facade_id`), `facade/add` + `facade/update` (`cover_ids`), and `rule/add` + `rule/update` (`facade_ids`, `cover_ids`) reject unknown IDs with a `not_found` error instead of silently storing ghost references. Prevents rules/covers/facades from pointing at deleted or never-existing entities. +8 regression tests.

## [1.53.6] - 2026-06-18

### Fixed

- Disabling a cover's automation via the panel toggle now persists the `MANUAL` status, so the status table no longer keeps showing "Auto" after `auto_enabled` is turned off. The panel toggle now routes through the same coordinator status transitions as the HA switch entity (`set_cover_manual` / `resume_cover`), which also fixes covers staying `MANUAL` after re-enabling automation from the panel. `_sync_cover_statuses` additionally persists `MANUAL` so the status survives a restart (which resets all statuses to `AUTO`). +5 regression tests.

## [1.53.5] - 2026-06-09

### Fixed

- A pending protective-exit hysteresis bypass (`_post_protective_exit`) is now cancelled when the cover leaves AUTO/VENTING (e.g. a manual override pauses it) before the next apply cycle consumed it. Previously the stale flag survived the status change and skipped `min_time_between_changes` once on an unrelated move much later. +1 regression test.
- Panel: the window-level `pointermove`/`pointerup`/`pointercancel` listeners attached during compass house-drag are now also removed in `disconnectedCallback`. Previously they leaked if the panel was removed from the DOM mid-drag.

## [1.53.4] - 2026-06-09

### Security

- The `export_config` service can no longer overwrite arbitrary files in the HA config directory (e.g. `configuration.yaml`). Export targets are now confined to `<config>/cover_automatic/` and must use a `.yaml`/`.yml` extension; relative paths resolve inside that folder, which is created on demand. The default export path moved from `/config/cover_automatic_backup.yaml` to `/config/cover_automatic/cover_automatic_backup.yaml`. Import is unchanged (read-only). +8 tests.

## [1.53.3] - 2026-06-09

### Fixed

- `hacs.json` now declares the same minimum Home Assistant version as `manifest.json` (`2026.3.0`, previously `2025.1.0`). HACS checks `hacs.json`, so installations on older HA versions were possible even though the integration cannot start there (Python 3.14 / `StaticPathConfig` required).

## [1.53.2] - 2026-06-08

### Fixed

- Covers are no longer falsely paused while physically travelling. For a long move whose travel time exceeds `SETTLE_TIME` (30 s), the apply-cycle override check (`async_apply_positions`) read the still-stale pre-move position reported by HmIP-style actuators (which only update `current_position` once travel finishes), compared it against the target and treated the difference as a manual override — pausing the cover for the full `pause_duration` (e.g. 120 min) and blocking later rules (a night rule due at 19:00 would not run until the pause expired). The state-change handler already guarded against `opening`/`closing`; the apply cycle now does too, leaving `_pending_settle` intact so the post-settle sync runs after travel. +1 regression test.

## [1.53.1] - 2026-06-07

### Fixed

- Brief indoor temperature sensor outages (e.g. a Zigbee bridge restart making all MQTT sensors unavailable for ~2 minutes) no longer drop the `sun_on_facade` rule. Previously `_get_comfort_mode()` returned None on unavailable, `sun_on_facade` evaluated False, a lower-priority day rule won and the covers moved up — only to shade again 2 minutes later once the sensor recovered (the rule-change bypass skips `min_time_between_changes`, so both movements executed immediately). The engine now holds the last known comfort mode for a 900 s grace period (`COMFORT_SENSOR_GRACE_PERIOD`); beyond that, or without any prior reading, behavior is unchanged. Also applies to the `temperature_comfort` condition. +4 regression tests.

## [1.53.0] - 2026-05-18

### Added

- New rule conditions `time_before_sunrise` and `time_before_sunset` (engine + panel). Mirror semantics of the existing `time_after_*` conditions but evaluate "current time is before (event + offset)". Use case: bound an open-during-day rule with `time_before_sunset offset=-60` to keep it inactive in the last 60 minutes before sunset, so the shutter is not lifted briefly between the shade rule deactivating and the night rule kicking in. Defaults: `time_before_sunrise offset=0`, `time_before_sunset offset=-60`. 7 new engine tests.

## [1.52.1] - 2026-05-17

### Fixed

- Removed `number.*_pause_duration` entities are now cleaned up from the HA entity registry on startup. After upgrading to 1.52.0 the entity stayed visible as an unavailable / greyed-out field on every cover device because HA keeps orphaned entries until something explicitly removes them. `_cleanup_removed_entities()` runs in `async_setup_entry` and prunes any `cover_automatic` number entity whose unique_id ends with `_pause_duration`.

## [1.52.0] - 2026-05-17

### Removed

- **Breaking:** per-cover `number.*_pause_duration` entity has been removed. Pause duration is now configured exclusively via the sidebar panel (per-cover field with global fallback). Any HA automation or script referencing the entity must switch to the panel or the global `storage.pause_duration` setting. The underlying `CoverConfig.pause_duration` field, panel UI, and engine logic are unchanged — only the HA entity surface is gone.

## [1.51.3] - 2026-04-27

### Fixed

- `ws_settings_update` is now atomic: an invalid `active_scenario` rejects the entire update instead of leaving partial mutations in memory while disk still has the old values. Previous behaviour wrote each accepted field straight into in-memory state during the loop, then validated `active_scenario` at the end and returned an error -- the rejected field stayed unchanged but every prior field was already mutated and would leak to disk on the next debounced save. Validation now runs up front before any mutation. +1 regression test.

## [1.51.2] - 2026-04-27

### Fixed

- Activity log entries no longer get lost on Home Assistant restart. `ActivityLogStorage` was missing the `async_save()` method that `coordinator.async_shutdown()` was calling, so the shutdown flush silently raised `AttributeError` (swallowed by the surrounding `try/except`). Combined with `flush_pending_save()` cancelling the debounced write, any logbook entries accumulated since the last debounce window vanished. Bug existed since v1.40.0 when the activity log feature was introduced. +2 regression tests.

## [1.51.1] - 2026-04-27

- Security: solar widget now escapes the `unit_of_measurement` HA state attribute and `_esc()` covers single-quotes too (defense-in-depth against future refactors).
- Security: WS `import` rejects payloads with more than 1000 cover/rule/scenario/facade entries before the synchronous deepcopy can block the event loop.
- Hardening: CI workflow declares `permissions: contents: read` so `GITHUB_TOKEN` no longer inherits write defaults.
- Modernization: subscribeEvents promise now has a `.catch()` (no more unhandled rejections on WS reconnect), `CoverAutomaticRuntimeData` uses `slots=True`, `asyncio.Task` carries its generic parameter, and the render path uses template literals consistently.
- Cleanup: compass-house cursor/touch-action moved from inline style to the `#compass-house` selector, two unused CSS classes (`.info-widget-label`, `.mb-8`) removed.

## [1.51.0] - 2026-04-27

- Security: WebSocket API now requires admin privileges for every write, log-clear, export, import and resume command. The sidebar panel was already admin-only via `require_admin=True`, but the underlying WS endpoints accepted any authenticated HA user (including Long-Lived Tokens or non-admin household members). A non-admin user could call `cover_automatic/cover/update`, `settings/update`, `import` etc. directly and bypass the UI gate. The fix wraps `_make_handler` with `websocket_api.require_admin` for every command except the two read-only ones (`config`, `log`). Identified by an OWASP-style audit on 2026-04-27, no known exploitation in the wild but the gap was real for multi-user installations.

## [1.50.0] - 2026-04-26

- UX: settings/house compass is now drag-rotatable. Click and drag the central house square to set the rotation directly; hold Shift to snap to 45° increments. The numeric input and the existing live-preview path stay in sync.
- UX: quick-rotate buttons next to the rotation input (`−45° / −5° / Reset / +5° / +45°`) for keyboard-free fine and coarse adjustments.
- UX: facade arc palette switched from saturated rainbow to a harmonized muted hue family that no longer competes with the orange action accent. House square gets a proper SVG drop-shadow and a subtle inner stroke for depth, instead of the flat outline. View-mode stays calm — no animations, no glow — keeping the settings tab a configuration tool, not an ambient cockpit.

## [1.49.0] - 2026-04-26

- Fix: closing a window after ventilation now applies the matching rule's target position immediately, instead of waiting for `min_time_between_changes` to elapse. The bug was twofold: (a) the vent-sensor-close branch in `_handle_contact_sensor_change` only pushed an updated-data event, not an actual refresh, so the next apply cycle waited for the polling interval; and (b) the time hysteresis treated the prior vent move as a normal apply move, blocking the rule re-apply for up to `min_time_between_changes` (a 30-min config could leave covers at 15% for almost half an hour after the window closed). VENTING -> AUTO and LOCKED -> AUTO transitions now schedule an immediate refresh and grant a one-shot bypass for the time hysteresis on the next apply cycle, analogous to the existing rule-change bypass. New `_post_protective_exit` set tracks the one-shot grant. +5 tests.

## [1.48.0] - 2026-04-26

- UX: status badges (Auto / Paused / Manual / Locked / Venting / Wind protected) now use the panel's semantic color tokens instead of hardcoded hex values, so they follow custom Home Assistant themes consistently. Auto picks up the green "active" tone, Paused the warning orange, Locked / Wind the danger red, Manual / Venting the neutral info blue.
- UX: the active-scenario card now uses the same green accent as the active-rule highlight, making "what is running right now?" readable at a glance. Orange remains reserved for interactive controls (buttons, tabs, toggles) so action and status no longer share a color.
- UX: the Rule cell on the covers table is now a clickable link. Clicking the rule name jumps to the Rules tab and pulses the matching rule for two seconds, so you can inspect why a cover is at its current position without searching.
- UX: the Settings sub-navigation pill strip on mobile now fades out at both edges, signalling that more sections are reachable by horizontal scrolling.

## [1.47.0] - 2026-04-26

- UX: scenario icon picker. The free-text `mdi:...` field is replaced by a curated grid of 32 common scenario icons (home, sun, snowflake, plane, TV, sofa, coffee, gamepad, etc.) with a click-to-select interface. A collapsible "Custom MDI icon" section preserves the freeform input for any other Material Design Icon.
- UX: the "Preemptive shading" settings card header sun icon now uses the neutral Lucide outline (matches the other section headers) instead of the filled yellow accent sun, which was reserved for live state indicators.

## [1.46.0] - 2026-04-24

- Fix: the `min_time_between_changes` hysteresis no longer blocks position updates when the matching rule has changed since the last move. A rule transition (e.g. "Day" -> "Night") is a semantic state change, not rate-limitable noise, so the new target is applied immediately. The position-change hysteresis (`min_position_change`) remains active as a noise filter. Prevents delayed shutter closing when a high-priority night rule kicks in shortly after a daytime rule last moved the covers.

## [1.45.2] - 2026-04-23

- UX: settings sidebar sun icon for "Preemptive shading" now inherits the button text color like the other nav icons, instead of rendering in the accent sun yellow. The yellow sun remains in the header info bar, live indicators and the section card header where it carries semantic meaning.

## [1.45.1] - 2026-04-23

- UX: the position bar now uses a two-stop fill when current and target differ. The solid portion represents the position that is guaranteed reached (min of current/target), the striped portion represents the range in motion (min to max). Replaces the previous thin vertical target marker for a more honest and direction-agnostic visualization.

## [1.45.0] - 2026-04-23

- UX: Settings tab is redesigned with a vertical sidebar navigation. The seven sections (House, Sensors, Comfort, Wind, Preemptive shading, Automation, Backup) can now be selected individually without scrolling through the whole page. The active section stays sticky on the left on desktop.
- UX: on mobile (< 768px) the sidebar collapses into a horizontal scrollable pill strip above the section content.
- UX: the save button now appears at the bottom of the active section only (except Backup, which has its own export/import actions).

## [1.44.0] - 2026-04-23

- UX: the "current" and "target" position columns in the cover table are merged into a single "Position" column. When current and target differ, the bar shows the current fill, a primary-colored marker at the target position, and a compact "30% → 60%" label. When they match, a normal single bar is shown.
- UX: hardcoded accent colors (sun, warning, info, danger, success) are now CSS custom properties (`--ca-sun`, `--ca-warning`, `--ca-info`, `--ca-danger`, `--ca-success-strong`). Custom HA themes can override them.
- Chore: reduced inline `style=` attributes from 41 down to 4 (remaining ones are legitimately dynamic). Replaced with a set of utility and semantic CSS classes (`.nowrap`, `.mt-16`, `.facade-meta-row`, `.rule-conditions-label`, `.sc-actions`, etc.).

## [1.43.1] - 2026-04-23

- UX: hint texts under settings and cover fields are now collapsed behind a small info icon. Click the icon to reveal the hint. The page is much easier to scan once configured.
- UX: "last change" time is now formatted naturally ("vor 1 Std. 53 Min." / "1 h 53 min ago") instead of the previous "1:53 Std." notation.
- UX: on mobile, the first column of the cover table stays visible while scrolling horizontally, so you always see which cover a row belongs to.

## [1.43.0] - 2026-04-23

- UX: redesigned the panel header info bar as a widget strip. Sun position, outdoor temperature, weather state and solar intensity each get their own pill-shaped widget with icon and tooltip, replacing the previous pipe-separated text line. Solar widget turns orange when preemptive shading is active.
- UX: individual widgets wrap cleanly on narrow viewports without breaking the layout.

## [1.42.1] - 2026-04-23

- UX: rule cards now show the target position as a small inline progress bar instead of a percent text, matching the cover table.
- UX: slide-out section headers in the cover editor now have a distinctive icon, accent color and a divider between sections for clearer hierarchy.
- UX: replaced the Material-style hamburger icon in the panel header with the matching Lucide icon for consistency with other icons.

## [1.42.0] - 2026-04-22

- UX: panel header now wraps correctly on mobile; the master switch and scenario badge are no longer pushed off-screen by the info bar.
- UX: weather state in the header is now localized (e.g. "Klare Nacht" instead of "clear-night") and paired with a Lucide weather icon.
- UX: clickable cover rows now show a chevron affordance and a stronger hover highlight so users discover the slide-out editor.
- UX: table sort arrows now only show direction on the active column; inactive columns display a neutral indicator.
- UX: active scenario card now stands out with a tinted background and colored primary glow instead of a subtle border.
- Chore: replaced several inline `style=` attributes in the panel header and info bar with reusable CSS classes.

## [1.41.2] - 2026-04-22

- UX: merged version number and update badge in the panel header into a single element to avoid duplication. When an update is available, the badge now shows both versions ("v1.41.1 -> v1.41.2") and links to the release notes of the new version.

## [1.41.1] - 2026-04-22

- UX: version number in the panel header is now a link to the release notes of the installed version on GitHub.

## [1.41.0] - 2026-04-22

- Feature: per-cover opt-out for preemptive (solar-triggered) shading. New "Preemptive shading enabled" toggle in the Sensors section of each cover. When disabled, the global solar sensor no longer triggers shading inside the comfort zone for that cover -- useful for rooms that should reach comfort temperature quickly (e.g. bathroom). Default is enabled (backward compatible).

## [1.40.0] - 2026-04-19

- Feature: write cover movements, lock/unlock, pause/resume and wind protection events to Home Assistant's built-in logbook. New setting `Write logbook entries` (default on) in the System card of the panel.

## [1.39.11] - 2026-04-19

- Fix: rule condition add/delete no longer mutates the panel config before the websocket call; on WS failure the local state stays in sync with the backend instead of silently diverging (#140)

## [1.39.10] - 2026-04-19

- Fix: pause duration number entity now resets to the global fallback when set to 0 instead of persisting 0 and breaking the per-cover fallback chain (#141)

## [1.39.9] - 2026-04-19

- Fix: wind protection deactivation now re-derives LOCKED/VENTING from sensors inline, preventing brief AUTO state and wrong position until next scan tick when a window is open (#134)
- Docs: CLAUDE.md WebSocket command count corrected to 20 (#129)
- CI: drop Python 3.13 matrix -- HA 2026.3 requires 3.14 (#130)

## [1.39.8] - 2026-04-17

- Fix: panel number inputs with comma or invalid content now safely resolve to null instead of NaN being sent to backend
- Fix: target_tilt_position from panel sends null instead of NaN when input is invalid
- Fix: facade sun time calculation errors are now logged at warning level with traceback instead of silently on debug
- Fix: cover/add API now rejects non-cover entity IDs (e.g. light.foo) at schema validation time

## [1.39.7] - 2026-04-17

- Fix: backup-import button was dead -- typo `this._shadowRoot` (should be `shadowRoot`), file picker never opened
- Fix: silent error after successful backup import -- call to nonexistent `_showSaved()` (now `_showToast()`)
- Fix: deleting the active scenario left `active_scenario` pointing at a dead ID; storage now falls back to first remaining scenario
- Fix: log entries from last 2 seconds were lost on HA shutdown -- log storage was cancelled without `async_save()`

## [1.39.6] - 2026-04-17

- Fix: falsy-0 patterns discarded legitimate zero values in panel sorting -- rules with priority=0, facades pointing north (azimuth=0), and house-rotation input "0" were treated as missing
- Chore: remove 10 unused i18n keys from panel translations (en/de)
- Chore: remove unused constant DEFAULT_COMMAND_STAGGER

## [1.39.5] - 2026-04-14

- Chore: README overhaul -- fix outdated version, HA requirement, setup instructions, status list, condense changelog

## [1.39.4] - 2026-04-11

- Chore: raise minimum Home Assistant version to 2026.3.0 (brand proxy API, StaticPathConfig, Python 3.14)

## [1.39.3] - 2026-04-11

- Chore: README logo uses absolute raw.githubusercontent.com URL and sharper @2x asset

## [1.39.2] - 2026-04-11

- Chore: new brand logo, regenerated all HA brand assets (icon, logo, dark variants in 1x/2x)

## [1.39.1] - 2026-04-09

- Fix: state-change handler now respects startup grace period (prevents false PAUSED from device reconnection after HA restart)
- Fix: positions re-synced from HA state at end of grace period (ensures correct tracking after sensor stabilization)
- Fix: tilt position synced alongside position in all sync paths (post-settle, hysteresis skip, no-move) to prevent false tilt mismatch overrides

## [1.39.0] - 2026-04-09

- Fix: manual override during VENTING not detected within settle time (cover was pushed back instead of pausing)
- Feat: vent/lock-to-vent moves now use _pending_settle mechanism for proper settle handling
- Feat: post-settle sync uses min_position_change threshold to distinguish actuator settling from manual overrides
- Feat: apply cycle skips covers during settle time to prevent overriding manual positions

## [1.38.3] - 2026-04-09

- Fix: resume_cover restores VENTING (not AUTO) when vent sensor is still open
- Fix: lock-to-vent transition syncs _last_positions when no move needed (prevents false override after manual move during LOCKED)

## [1.38.2] - 2026-04-09

- Fix: sync _last_positions when entering VENTING without move (prevents false override loop after PAUSED -> VENTING transition)

## [1.38.1] - 2026-04-09

- Fix: vent sensor closing while paused (from venting override) now immediately restores AUTO instead of leaving stale pause

## [1.38.0] - 2026-04-09

- Fix: manual overrides during VENTING status are now detected and respected (cover pauses instead of being reset)
- Fix: pause timer runs to completion while vent sensor is open, then resumes VENTING

## [1.37.0] - 2026-04-09

- Feat: solar sensor value displayed in header info bar with threshold indicator (orange highlight + arrow when exceeded)

## [1.36.0] - 2026-04-08

- Feat: preemptive shading -- configurable solar intensity sensor + threshold for early shading within comfort zone
- Feat: sun_on_facade shades in NEUTRAL comfort mode when solar intensity exceeds threshold (HEATING still blocks)
- Feat: weather entity state displayed in header info bar alongside outdoor temperature

## [1.35.0] - 2026-04-07

- Feat: startup grace period (120s) prevents wrong cover movements from incomplete sensor data after HA restart
- Feat: initialize cover positions from HA state on startup for correct override detection
- Fix: false manual override detection after own position commands (pending settle sync)
- Fix: pause expiry now syncs expected position to prevent immediate re-pause

### 1.34.0 - 1.34.4 (2026-04-05 - 2026-04-06)

- Lucide SVG icons for settings section headers
- Fix: stale comfort mode display, settings update triggers immediate re-evaluation
- Fix: time hysteresis badge shown when position already matches target
- Fix: settings section header alignment, sensors 2-column grid layout

### 1.33.0 - 1.33.5 (2026-04-05)

- Manual override detection in apply cycle (catches overrides missed during settle time)
- Position bar visual improvements (colors, display fix, inline badges)
- Resume button replaced with compact X icon
- Fix: cover falsely paused after HA restart, hysteresis badge persistence

### 1.32.0 - 1.32.10 (2026-04-05)

- Clickable cover table rows with slide-out panel
- Position columns with visual progress bars and percentage labels
- Delete button moved to slide-out panel (prevents accidental deletes)

### 1.31.0 - 1.31.3 (2026-04-05)

- Global info bar with sun position and outdoor temperature in header
- SVG icon system (`_sunIconSvg()` helper)
- Facade card grid limited to 2 columns

### 1.30.0 - 1.30.3 (2026-04-05)

- Real-time status updates via event push (coordinator fires `cover_automatic_updated`)
- Comfort icons, sun-on-facade icon styling, venting badge style
- Fix: language change detection, resume button persistence

### 1.29.0 - 1.29.2 (2026-04-03 - 2026-04-04)

- Command stagger delay for radio-based systems (Z-Wave, Zigbee)
- Fix: comfort mode first-evaluation hysteresis, nullable per-cover fields, falsy-0 bugs
- XSS hardening in panel, memory leak fix in disconnectedCallback

### 1.28.0 - 1.28.3 (2026-04-03)

- Sortable cover table columns, facades sorted by azimuth
- Fix: confirm dialog transparency

### 1.26.0 - 1.27.9 (2026-04-02 - 2026-04-03)

- Settings tab redesign: 6 cards (House, Sensors, Comfort, Wind, Automation, Backup)
- Live compass SVG with sun position, light cone, and facade arcs
- Hamburger menu for mobile sidebar navigation
- Cache busting via version query parameter
- Clear log button with confirmation dialog
- Remove all inline CSS, replace with CSS classes

### 1.22.0 - 1.25.2 (2026-04-02)

- Export/import configuration via panel settings (JSON)
- Workday condition type with global sensor
- Global defaults for lock/vent tilt positions
- Temperature column colored by comfort mode
- Indoor temperature in covers table with live updates

### 1.15.0 - 1.21.1 (2026-04-01)

- Covers table: position columns (Ist/Soll), hysteresis indicator, resume button, rule name, comfort icons
- Activity log tab with 3-day retention and type filter
- Rule priority by drag order, weather multi-select
- Global master switch, wind protection (WIND_PROTECTED status)
- Global defaults for lock/vent position, min position/time change
- Per-cover comfort temperature ranges
- Scenario icons via ha-icon

### 1.7.0 - 1.14.0 (2026-03-31 - 2026-04-01)

- VENTING status: vent sensor sets minimum position, automation continues
- Comfort shading with hysteresis (COOLING/NEUTRAL/HEATING modes)
- Day-of-week condition type
- Configurable comfort temperature hysteresis
- Detailed logging for all state changes

### 1.4.0 - 1.6.2 (2026-03-31)

- Panel refactored to event delegation with partial rendering
- Global default pause duration with per-cover fallback
- Auto comfort shading based on indoor temperature
- Compass bearings for facade azimuths with house rotation

### 1.1.0 - 1.3.4 (2026-03-30)

- Custom config panel as sidebar entry (replacing Options Flow)
- WebSocket API backend, drag & drop rule ordering
- Cover/facade management via panel
- House rotation setting, per-cover indoor temp sensor
- Bidirectional facade-cover sync

### 1.0.13 - 1.0.41 (2026-01-03 - 2026-03-30)

First stable release through pre-panel development. Core features: facade-based sun tracking, rule engine with 11 condition types, priority-based matching, scenario support, lock/vent sensors, comfort temperature system, tilt/slat control, inverted cover support. Extensive hardening: 182+ unit tests, storage robustness, race condition fixes, HA API compatibility updates, brand images, CI pipeline (Python 3.13/3.14, HACS validation, Ruff linting).

---

