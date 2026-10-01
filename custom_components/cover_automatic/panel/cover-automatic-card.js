/*
 * CoverAutomatic dashboard card.
 *
 *   type: custom:cover-automatic-card
 *   title: Volets            # optional
 *   covers:                  # optional, default: every managed cover
 *     - cover.volet_du_salon
 *   show_rule: true          # optional
 *   show_auto: true          # optional (automation switch + resume button)
 *
 * Everything comes from the per-cover "Status" sensors of the integration
 * (their attributes carry the rule, target, pause end and the automation
 * switch), plus the live cover state for the position. No websocket calls,
 * so it works for non-admin users too.
 */
(() => {
  const CARD_TAG = "cover-automatic-card";
  const EDITOR_TAG = "cover-automatic-card-editor";
  if (customElements.get(CARD_TAG)) return;

  const I18N = {
    en: {
      no_covers: "No CoverAutomatic cover found. Is the integration set up (version 1.79 or later)?",
      no_rule: "No rule",
      resume: "Resume automation",
      auto: "Automation",
      safety: "Safety rule",
      target: "Target",
      remaining: "{m} min left",
      inverted: "Inverted cover: HA reports {raw}%",
      ed_title: "Title",
      ed_covers: "Covers (empty = all)",
      ed_show_rule: "Show the active rule",
      ed_show_auto: "Show the automation switch and the resume button",
      desc: "Covers managed by CoverAutomatic: position, active rule and status.",
      scenario: "Scenario",
      master: "Automation",
      resume_all: "Resume all",
      resume_all_title: "End every pause (covers moved by hand)",
      wind: "Wind",
      wind_active: "Wind protection",
      paused: "paused",
      manual: "manual",
      locked: "locked",
      render_error: "Display error, retrying…",
      ed_show_header: "Show the global part (scenario, automation, statuses)",
      missing: "Covers not found (not managed by CoverAutomatic?): {ids}",
    },
    de: {
      no_covers: "Kein CoverAutomatic-Rollladen gefunden. Ist die Integration eingerichtet (ab Version 1.79)?",
      no_rule: "Keine Regel",
      resume: "Automatik fortsetzen",
      auto: "Automatik",
      safety: "Sicherheitsregel",
      target: "Ziel",
      remaining: "noch {m} Min.",
      inverted: "Invertierter Rollladen: HA meldet {raw} %",
      ed_title: "Titel",
      ed_covers: "Rollläden (leer = alle)",
      ed_show_rule: "Aktive Regel anzeigen",
      ed_show_auto: "Automatik-Schalter und Fortsetzen-Knopf anzeigen",
      desc: "Von CoverAutomatic gesteuerte Rollläden: Position, aktive Regel und Status.",
      scenario: "Szenario",
      master: "Automatik",
      resume_all: "Alle fortsetzen",
      resume_all_title: "Alle Pausen beenden (von Hand bewegte Rollläden)",
      wind: "Wind",
      wind_active: "Windschutz",
      paused: "pausiert",
      manual: "manuell",
      locked: "gesperrt",
      render_error: "Anzeigefehler, neuer Versuch…",
      ed_show_header: "Globalen Teil anzeigen (Szenario, Automatik, Status)",
      missing: "Rollläden nicht gefunden (nicht von CoverAutomatic gesteuert?): {ids}",
    },
    fr: {
      no_covers: "Aucun volet CoverAutomatic trouvé. L'intégration est-elle installée (version 1.79 ou plus) ?",
      no_rule: "Aucune règle",
      resume: "Reprendre l'automatisation",
      auto: "Automatisation",
      safety: "Règle de sécurité",
      target: "Cible",
      remaining: "encore {m} min",
      inverted: "Volet inversé : HA indique {raw} %",
      ed_title: "Titre",
      ed_covers: "Volets (vide = tous)",
      ed_show_rule: "Afficher la règle active",
      ed_show_auto: "Afficher l'interrupteur d'automatisation et le bouton de reprise",
      desc: "Volets gérés par CoverAutomatic : position, règle active et statut.",
      scenario: "Scénario",
      master: "Automatisation",
      resume_all: "Tout reprendre",
      resume_all_title: "Lever toutes les pauses (volets bougés à la main)",
      wind: "Vent",
      wind_active: "Protection vent",
      paused: "en pause",
      manual: "en manuel",
      locked: "verrouillé(s)",
      render_error: "Erreur d'affichage, nouvel essai…",
      ed_show_header: "Afficher la partie globale (scénario, automatisation, statuts)",
      missing: "Volets introuvables (non gérés par CoverAutomatic\u00A0?)\u00A0: {ids}",
    },
  };

  const lang = (hass) => {
    const l = ((hass && (hass.locale?.language || hass.language)) || "en").slice(0, 2);
    return I18N[l] ? l : "en";
  };
  const t = (hass, key) => I18N[lang(hass)][key] ?? I18N.en[key] ?? key;
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const STATUS_COLORS = {
    auto: "var(--success-color, #43a047)",
    paused: "var(--warning-color, #ff9800)",
    manual: "var(--secondary-text-color, #727272)",
    locked: "var(--error-color, #db4437)",
    venting: "var(--info-color, #039be5)",
    wind_protected: "var(--info-color, #039be5)",
  };

  // Candidate sensor ids, cached per registry object (hass.entities only
  // changes when the entity registry does) instead of scanning every state
  // on every update.
  const _candidateCache = new WeakMap();
  function candidateIds(hass) {
    if (hass.entities) {
      let ids = _candidateCache.get(hass.entities);
      if (!ids) {
        ids = Object.values(hass.entities)
          .filter((e) => e && e.platform === "cover_automatic" && String(e.entity_id).startsWith("sensor."))
          .map((e) => e.entity_id);
        _candidateCache.set(hass.entities, ids);
      }
      return ids;
    }
    // Older frontends without the registry map: scan the states
    return Object.keys(hass.states).filter((eid) => eid.startsWith("sensor."));
  }

  // Status sensors of the integration, keyed by cover entity id.
  function findStatusSensors(hass) {
    const out = {};
    if (!hass || !hass.states) return out;
    for (const eid of candidateIds(hass)) {
      const st = hass.states[eid];
      const cover = st && st.attributes && st.attributes.cover_entity_id;
      if (cover) out[cover] = st;
    }
    return out;
  }

  // Global entities of the integration, keyed by their translation key
  const _globalCache = new WeakMap();
  const GLOBAL_KEYS = {
    scenario: "scenario", master_enabled: "master", wind_protection: "wind",
    covers_paused: "paused", covers_manual: "manual", covers_locked: "locked",
  };
  function findGlobals(hass) {
    if (!hass || !hass.entities) return {};
    let out = _globalCache.get(hass.entities);
    if (!out) {
      out = {};
      for (const e of Object.values(hass.entities)) {
        if (!e || e.platform !== "cover_automatic") continue;
        const key = GLOBAL_KEYS[e.translation_key];
        if (key) out[key] = e.entity_id;
      }
      _globalCache.set(hass.entities, out);
    }
    return out;
  }

  const num = (v) => (v == null || v === "" || isNaN(Number(v)) ? null : Math.round(Number(v)));

  class CoverAutomaticCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._config = {};
      this._hass = null;
      this._rowSigs = new Map();
      this._skeleton = "";
      this._timer = null;
      this.shadowRoot.addEventListener("click", (e) => this._onClick(e));
      this.shadowRoot.addEventListener("change", (e) => this._onChange(e));
    }

    static getConfigElement() {
      return document.createElement(EDITOR_TAG);
    }

    static getStubConfig() {
      return { show_header: true, show_rule: true, show_auto: true };
    }

    // Never throws on a questionable option (a thrown error shows a red
    // "Configuration error" card): odd values fall back to the defaults.
    setConfig(config) {
      const c = config && typeof config === "object" ? { ...config } : {};
      if (c.covers != null && !Array.isArray(c.covers)) c.covers = typeof c.covers === "string" ? [c.covers] : undefined;
      this._config = { show_header: true, show_rule: true, show_auto: true, ...c };
      this._skeleton = "";
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      this._render();
    }

    // A failed render (unexpected state while HA reconnects...) must not
    // leave a broken card: show a short notice and retry on the next update.
    _render() {
      try {
        this._renderInner();
      } catch (err) {
        console.error("cover-automatic-card:", err);
        this._skeleton = "";
        if (this.shadowRoot) {
          this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="rows no-title"><div class="empty">${esc(t(this._hass, "render_error"))}</div></div></ha-card>`;
        }
      }
    }

    get hass() {
      return this._hass;
    }

    connectedCallback() {
      // Pause countdown refresh: only rows whose text changes are redrawn
      this._timer = setInterval(() => this._render(), 30000);
    }

    disconnectedCallback() {
      clearInterval(this._timer);
      this._timer = null;
    }

    getCardSize() {
      return 1 + this._rows().length;
    }

    getGridOptions() {
      return { columns: 12, min_columns: 6 };
    }

    _rows() {
      return this._rowInfo().rows;
    }

    // Rows to show, plus the configured covers without a status sensor
    // (typo, cover no longer managed): listed in a warning, not hidden.
    _rowInfo() {
      const sensors = findStatusSensors(this._hass);
      const configured = Array.isArray(this._config.covers) && this._config.covers.length ? this._config.covers : null;
      const ids = configured
        ? configured.filter((id) => sensors[id])
        : Object.keys(sensors).sort((a, b) => this._name(a, sensors[a]).localeCompare(this._name(b, sensors[b])));
      const missing = configured ? configured.filter((id) => !sensors[id]) : [];
      return {
        rows: ids.map((id) => ({ id, status: sensors[id], cover: this._hass.states[id] })),
        missing,
        anySensor: Object.keys(sensors).length > 0,
      };
    }

    _name(id, status) {
      const cover = this._hass && this._hass.states[id];
      return (cover && cover.attributes.friendly_name) || status.attributes.cover_name || id;
    }

    _position(row) {
      const attrs = row.status.attributes;
      let rawVal = row.cover && row.cover.attributes ? row.cover.attributes.current_position : null;
      if (rawVal == null && row.cover) rawVal = { open: 100, closed: 0 }[row.cover.state] ?? null;
      const raw = num(rawVal);
      if (raw == null) return { pos: num(attrs.position), raw: null };
      return { pos: attrs.inverted ? 100 - raw : raw, raw };
    }

    _bar(pos, rawTarget) {
      const target = num(rawTarget);
      if (pos == null) return '<span class="dash">–</span>';
      const cur = pos ?? target;
      const diverges = pos != null && target != null && Math.abs(pos - target) >= 1;
      const width = Math.max(0, Math.min(100, cur));
      let label = `${cur}%`;
      let marker = "";
      if (diverges) {
        label = `${pos}% <span class="arrow">→</span> ${target}%`;
        marker = `<span class="marker" style="left:${Math.max(0, Math.min(100, target))}%"></span>`;
      }
      return `<span class="bar"><span class="track"><span class="fill" style="width:${width}%"></span>${marker}</span><span class="label">${label}</span></span>`;
    }

    // Keyed, incremental render: only rows whose HTML changed are replaced,
    // so an unchanged row keeps focus (keyboard users) and its state.
    _renderInner() {
      if (!this.shadowRoot) return;
      const hass = this._hass;
      const title = this._config.title || "";
      const skeleton = `${title}|${hass ? lang(hass) : ""}`;
      if (skeleton !== this._skeleton) {
        this._skeleton = skeleton;
        this._rowSigs = new Map();
        this.shadowRoot.innerHTML = `<style>${STYLE}</style>
          <ha-card${title ? ` header="${esc(title)}"` : ""}>
            <div class="globals${title ? "" : " no-title"}">
              <div class="g-line g-controls"></div>
              <div class="g-line g-status"></div>
            </div>
            <div class="missing" role="status" hidden></div>
            <div class="rows"></div>
          </ha-card>`;
        this._ctrlSig = null;
        this._statusSig = null;
        this._missingSig = null;
      }
      const container = this.shadowRoot.querySelector(".rows");
      if (!container || !hass) return;
      const globalsEl = this.shadowRoot.querySelector(".globals");
      if (globalsEl) {
        // Controls (scenario select, master switch) and status chips are
        // redrawn separately: a chip update must not close an open select.
        const g = this._config.show_header ? this._renderGlobals() : { controls: "", status: "" };
        const patch = (sel, html, sigKey) => {
          const el = globalsEl.querySelector(sel);
          if (!el || html === this[sigKey]) return;
          const focusKey = this._focusKey(el);
          el.innerHTML = html;
          el.hidden = !html;
          this[sigKey] = html;
          if (focusKey) el.querySelector(focusKey)?.focus();
        };
        patch(".g-controls", g.controls, "_ctrlSig");
        patch(".g-status", g.status, "_statusSig");
        const any = !!(g.controls || g.status);
        globalsEl.hidden = !any;
        container.classList.toggle("no-title", !any && !title);
      }
      const info = this._rowInfo();
      const rows = info.rows;
      const missingEl = this.shadowRoot.querySelector(".missing");
      if (missingEl) {
        // Only once the integration's sensors exist: at HA startup every
        // configured cover would briefly be listed as missing.
        const txt = info.missing.length && info.anySensor ? t(hass, "missing").replace("{ids}", info.missing.join(", ")) : "";
        if (txt !== this._missingSig) {
          this._missingSig = txt;
          missingEl.textContent = txt;
          missingEl.hidden = !txt;
        }
      }
      if (!rows.length) {
        this._rowSigs = new Map();
        // Configured covers all missing while the integration is there: the
        // warning above says which ones.
        container.innerHTML = info.missing.length && info.anySensor ? "" : `<div class="empty">${esc(t(hass, "no_covers"))}</div>`;
        return;
      }
      container.querySelector(".empty")?.remove();
      const wanted = new Set(rows.map((r) => r.id));
      for (const el of [...container.children]) {
        if (!wanted.has(el.dataset.row)) {
          el.remove();
          this._rowSigs.delete(el.dataset.row);
        }
      }
      let prev = null;
      for (const r of rows) {
        const html = this._renderRow(r);
        let el = [...container.children].find((c) => c.dataset.row === r.id);
        if (!el) {
          el = document.createElement("div");
          el.dataset.row = r.id;
        }
        if (this._rowSigs.get(r.id) !== html) {
          const focusKey = this._focusKey(el);
          el.innerHTML = html;
          this._rowSigs.set(r.id, html);
          if (focusKey) el.querySelector(focusKey)?.focus();
        }
        // Keep the requested order
        const expected = prev ? prev.nextSibling : container.firstChild;
        if (expected !== el) container.insertBefore(el, expected);
        prev = el;
      }
    }

    // Selector of the focused control inside a row, to restore it after a redraw.
    _focusKey(rowEl) {
      const active = this.shadowRoot.activeElement;
      if (!active || !rowEl.contains(active)) return null;
      for (const attr of ["data-auto", "data-resume", "data-more", "data-scenario", "data-master", "data-resume-all"]) {
        const v = active.getAttribute(attr);
        if (v != null) return `[${attr}="${CSS.escape(v)}"]`;
      }
      return null;
    }

    // Global part: scenario, master automation switch, statuses, resume all
    _renderGlobals() {
      const hass = this._hass;
      const g = findGlobals(hass);
      const st = (id) => (id ? hass.states[id] : null);
      const parts = [];
      const scen = st(g.scenario);
      if (scen) {
        const names = scen.attributes.scenario_names || {};
        const opts = (scen.attributes.options || []).map((o) => {
          const label = names[o] || (hass.formatEntityState ? hass.formatEntityState(scen, o) : o);
          return `<option value="${esc(o)}"${o === scen.state ? " selected" : ""}>${esc(label)}</option>`;
        }).join("");
        parts.push(`<label class="g-field"><span>${esc(t(hass, "scenario"))}</span>
          <select data-scenario="${esc(g.scenario)}" aria-label="${esc(t(hass, "scenario"))}">${opts}</select></label>`);
      }
      const master = st(g.master);
      if (master) {
        parts.push(`<label class="g-field g-switch"><span>${esc(t(hass, "master"))}</span>
          <span class="switch"><input type="checkbox" data-master="${esc(g.master)}" ${master.state === "on" ? "checked" : ""} aria-label="${esc(t(hass, "master"))}"><span class="slider"></span></span></label>`);
      }
      const chips = [];
      const wind = st(g.wind);
      if (wind && wind.attributes.wind_sensor) {
        const speed = wind.attributes.wind_speed;
        const sensor = hass.states[wind.attributes.wind_sensor];
        const unit = sensor && sensor.attributes.unit_of_measurement ? " " + sensor.attributes.unit_of_measurement : "";
        const on = wind.state === "on";
        const value = speed == null ? "–" : `${Math.round(speed)}${unit}`;
        chips.push(`<span class="chip${on ? " warn" : ""}" title="${esc(t(hass, "wind"))}"><ha-icon icon="mdi:weather-windy"></ha-icon>${esc(on ? t(hass, "wind_active") + " · " + value : t(hass, "wind") + " " + value)}</span>`);
      }
      for (const [key, icon] of [["paused", "mdi:pause-circle"], ["manual", "mdi:hand-back-right"], ["locked", "mdi:lock"]]) {
        const s = st(g[key]);
        if (!s) continue;
        const n = parseInt(s.state, 10) || 0;
        const names = (s.attributes.covers || []).join(", ");
        chips.push(`<span class="chip${n ? " on" : " zero"}"${names ? ` title="${esc(names)}"` : ""}><ha-icon icon="${icon}"></ha-icon>${n} ${esc(t(hass, key))}</span>`);
      }
      const paused = parseInt((st(g.paused) || {}).state, 10) || 0;
      const resume = `<button class="g-btn" data-resume-all ${paused ? "" : "disabled"} title="${esc(t(hass, "resume_all_title"))}"><ha-icon icon="mdi:play-circle-outline"></ha-icon>${esc(t(hass, "resume_all"))}</button>`;
      if (!parts.length && !chips.length) return { controls: "", status: "" };
      return { controls: parts.join(""), status: chips.join("") + resume };
    }

    _renderRow(r) {
      const hass = this._hass;
      const a = r.status.attributes;
      const state = r.status.state;
      const { pos, raw } = this._position(r);
      const stateLabel = hass.formatEntityState ? hass.formatEntityState(r.status) : state;
      const color = STATUS_COLORS[state] || STATUS_COLORS.manual;
      const unavailable = !r.cover || r.cover.state === "unavailable";
      let pause = "";
      if (state === "paused" && a.pause_until) {
        const mins = Math.max(0, Math.ceil((new Date(a.pause_until).getTime() - Date.now()) / 60000));
        pause = `<span class="pause">${esc(t(hass, "remaining").replace("{m}", mins))}</span>`;
      }
      const invTip = a.inverted && raw != null ? ` title="${esc(t(hass, "inverted").replace("{raw}", raw))}"` : "";
      const rule = this._config.show_rule
        ? `<div class="rule${a.rule ? "" : " none"}">${a.safety_rule ? `<ha-icon icon="mdi:shield-alert" title="${esc(t(hass, "safety"))}"></ha-icon>` : ""}${esc(a.rule || t(hass, "no_rule"))}</div>`
        : "";
      let controls = "";
      if (this._config.show_auto) {
        const sw = a.auto_switch ? hass.states[a.auto_switch] : null;
        // Screen readers: say which cover the button/switch belongs to
        const name = this._name(r.id, r.status);
        const resumeLbl = `${t(hass, "resume")} – ${name}`;
        const autoLbl = `${t(hass, "auto")} – ${name}`;
        controls = `<div class="controls">
          ${state === "paused" ? `<button class="resume" data-resume="${esc(r.id)}" title="${esc(t(hass, "resume"))}" aria-label="${esc(resumeLbl)}"><ha-icon icon="mdi:play-circle-outline"></ha-icon></button>` : ""}
          ${sw ? `<label class="switch" title="${esc(t(hass, "auto"))}"><input type="checkbox" data-auto="${esc(a.auto_switch)}" ${sw.state === "on" ? "checked" : ""} aria-label="${esc(autoLbl)}"><span class="slider"></span></label>` : ""}
        </div>`;
      }
      return `<div class="row${unavailable ? " unavailable" : ""}${this._config.show_auto ? "" : " no-auto"}">
        <div class="main">
          <button class="name" data-more="${esc(r.id)}">${esc(this._name(r.id, r.status))}</button>
          ${rule}
        </div>
        <div class="pos"${invTip}>${unavailable ? '<span class="dash">–</span>' : this._bar(pos, a.target_position)}${a.inverted ? '<span class="inv">⇅</span>' : ""}</div>
        <div class="status"><span class="pill" style="--pill:${color}">${esc(stateLabel)}</span>${pause}</div>
        ${controls}
      </div>`;
    }

    _onClick(e) {
      const more = e.target.closest("[data-more]");
      if (more) {
        const ev = new Event("hass-more-info", { bubbles: true, composed: true });
        ev.detail = { entityId: more.dataset.more };
        this.dispatchEvent(ev);
        return;
      }
      if (e.target.closest("[data-resume-all]") && this._hass) {
        Promise.resolve(this._hass.callService("cover_automatic", "resume_all", {}))
          .catch((err) => console.error("cover-automatic-card:", err));
        return;
      }
      const resume = e.target.closest("[data-resume]");
      if (resume && this._hass) {
        Promise.resolve(
          this._hass.callService("cover_automatic", "resume", { entity_id: resume.dataset.resume })
        ).catch((err) => console.error("cover-automatic-card:", err));
      }
    }

    _onChange(e) {
      const el = e.target;
      if (el.dataset && el.dataset.scenario && this._hass) {
        Promise.resolve(this._hass.callService("select", "select_option",
          { entity_id: el.dataset.scenario, option: el.value }))
          .catch((err) => { console.error("cover-automatic-card:", err); this._ctrlSig = null; this._render(); });
        return;
      }
      if (el.dataset && el.dataset.master && this._hass) {
        const wanted = el.checked;
        Promise.resolve(this._hass.callService("switch", wanted ? "turn_on" : "turn_off", { entity_id: el.dataset.master }))
          .catch((err) => { console.error("cover-automatic-card:", err); el.checked = !wanted; });
        return;
      }
      if (el.dataset && el.dataset.auto && this._hass) {
        const wanted = el.checked;
        Promise.resolve(
          this._hass.callService("switch", wanted ? "turn_on" : "turn_off", { entity_id: el.dataset.auto })
        ).catch((err) => {
          // Service refused (e.g. no permission): show the real state again
          console.error("cover-automatic-card:", err);
          el.checked = !wanted;
        });
      }
    }
  }

  const STYLE = `
    :host { display: block; container-type: inline-size; }
    .rows { padding: 0 16px 12px; }
    .globals { padding: 0 16px 10px; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.12)); margin-bottom: 4px; }
    .globals.no-title { padding-top: 12px; }
    .g-line { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; }
    .g-line + .g-line { margin-top: 8px; }
    .g-line[hidden] { display: none; }
    .g-line[hidden] + .g-line { margin-top: 0; }
    .missing { margin: 8px 16px; padding: 6px 10px; border-radius: 8px; font-size: 13px; color: var(--primary-text-color); border-left: 3px solid var(--warning-color, #ff9800); background: color-mix(in srgb, var(--warning-color, #ff9800) 12%, transparent); overflow-wrap: anywhere; }
    .missing[hidden] { display: none; }
    .g-field { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--primary-text-color); }
    .g-field > span:first-child { color: var(--secondary-text-color); font-size: 13px; }
    .g-field select { font: inherit; font-size: 14px; padding: 4px 6px; border-radius: 6px; border: 1px solid var(--divider-color, #ccc); background: var(--card-background-color, #fff); color: var(--primary-text-color); max-width: 180px; }
    .g-status { gap: 6px; }
    .chip { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; padding: 3px 8px; border-radius: 12px; background: color-mix(in srgb, var(--primary-text-color) 7%, transparent); color: var(--primary-text-color); white-space: nowrap; }
    .chip ha-icon { --mdc-icon-size: 14px; }
    .chip.zero { color: var(--secondary-text-color); }
    .chip.on { background: color-mix(in srgb, var(--warning-color, #ff9800) 16%, transparent); }
    .chip.warn { background: color-mix(in srgb, var(--error-color, #db4437) 16%, transparent); color: var(--error-color, #db4437); }
    .g-btn { margin-left: auto; display: inline-flex; align-items: center; gap: 4px; font: inherit; font-size: 13px; padding: 4px 10px; border-radius: 14px; border: 1px solid var(--primary-color); background: transparent; color: var(--primary-color); cursor: pointer; }
    .g-btn ha-icon { --mdc-icon-size: 16px; }
    .g-btn:disabled { opacity: .4; cursor: default; }
    .row.no-auto { grid-template-columns: minmax(0, 1.5fr) minmax(110px, 1.4fr) 100px; }
    .rows.no-title { padding-top: 12px; }
    .globals[hidden] { display: none; }
    .row { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(110px, 1.4fr) 100px 64px; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.12)); }
    .rows > div:last-child > .row { border-bottom: 0; }
    .row.unavailable { opacity: .5; }
    .main { min-width: 0; }
    .name { all: unset; cursor: pointer; font-weight: 500; color: var(--primary-text-color); display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
    .name:focus-visible { outline: 2px solid var(--primary-color); border-radius: 4px; }
    .rule { font-size: 12px; color: var(--primary-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: flex; align-items: center; gap: 3px; }
    .rule.none { color: var(--secondary-text-color); }
    .rule ha-icon { --mdc-icon-size: 14px; color: var(--error-color, #db4437); }
    .pos { display: flex; align-items: center; gap: 4px; min-width: 0; }
    .bar { display: flex; align-items: center; gap: 6px; min-width: 0; width: 100%; }
    .track { position: relative; flex: 1 1 auto; min-width: 30px; height: 6px; border-radius: 3px; background: var(--divider-color, rgba(0,0,0,.12)); }
    .fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 3px; background: var(--primary-color); }
    .marker { position: absolute; top: -3px; width: 2px; height: 12px; margin-left: -1px; background: var(--primary-text-color); border-radius: 1px; }
    .label { font-size: 12px; white-space: nowrap; min-width: 66px; text-align: right; color: var(--primary-text-color); font-variant-numeric: tabular-nums; }
    .arrow { color: var(--primary-color); }
    .inv { font-size: 11px; color: var(--secondary-text-color); cursor: help; }
    .dash { color: var(--secondary-text-color); }
    .status { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
    .pill { font-size: 12px; padding: 2px 8px; border-radius: 10px; white-space: nowrap; color: var(--pill); background: color-mix(in srgb, var(--pill) 14%, transparent); }
    .pause { font-size: 11px; color: var(--secondary-text-color); white-space: nowrap; }
    .controls { display: flex; align-items: center; gap: 6px; justify-content: flex-end; }
    .resume { all: unset; cursor: pointer; color: var(--primary-color); display: flex; }
    .resume:focus-visible { outline: 2px solid var(--primary-color); border-radius: 50%; }
    .switch { position: relative; display: inline-block; width: 34px; height: 18px; flex: none; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider { position: absolute; inset: 0; cursor: pointer; border-radius: 9px; background: var(--disabled-color, #bdbdbd); transition: background .2s; }
    .slider::before { content: ""; position: absolute; width: 14px; height: 14px; left: 2px; top: 2px; border-radius: 50%; background: #fff; transition: transform .2s; }
    .switch input:checked + .slider { background: var(--primary-color); }
    .switch input:checked + .slider::before { transform: translateX(16px); }
    .switch input:focus-visible + .slider { outline: 2px solid var(--primary-color); outline-offset: 2px; }
    .empty { padding: 8px 0; color: var(--secondary-text-color); }
    /* Narrow card (phone, sections column): two lines per cover */
    @container (max-width: 480px) {
      .row, .row.no-auto { grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "main status" "pos controls"; row-gap: 6px; }
      .row.no-auto { grid-template-areas: "main status" "pos pos"; }
      .main { grid-area: main; } .status { grid-area: status; } .pos { grid-area: pos; } .controls { grid-area: controls; }
    }
  `;

  class CoverAutomaticCardEditor extends HTMLElement {
    setConfig(config) {
      this._config = { ...config };
      this._render();
    }

    set hass(hass) {
      const first = !this._hass;
      this._hass = hass;
      if (this._form) this._form.hass = hass;
      if (first) this._render();
    }

    _render() {
      if (!this._hass || !this._config) return;
      const covers = Object.keys(findStatusSensors(this._hass));
      const schema = [
        { name: "title", selector: { text: {} } },
        { name: "covers", selector: { entity: { multiple: true, include_entities: covers } } },
        { name: "show_header", selector: { boolean: {} } },
        { name: "show_rule", selector: { boolean: {} } },
        { name: "show_auto", selector: { boolean: {} } },
      ];
      if (!this._form) {
        this._form = document.createElement("ha-form");
        this._form.addEventListener("value-changed", (e) => {
          const value = { ...e.detail.value };
          if (Array.isArray(value.covers) && !value.covers.length) delete value.covers;
          if (!value.title) delete value.title;
          this._config = value;
          const ev = new Event("config-changed", { bubbles: true, composed: true });
          ev.detail = { config: value };
          this.dispatchEvent(ev);
        });
        this.appendChild(this._form);
      }
      const labels = { title: "ed_title", covers: "ed_covers", show_header: "ed_show_header", show_rule: "ed_show_rule", show_auto: "ed_show_auto" };
      this._form.hass = this._hass;
      this._form.schema = schema;
      this._form.data = { show_header: true, show_rule: true, show_auto: true, ...this._config };
      this._form.computeLabel = (s) => t(this._hass, labels[s.name] || s.name);
    }
  }

  customElements.define(CARD_TAG, CoverAutomaticCard);
  customElements.define(EDITOR_TAG, CoverAutomaticCardEditor);

  window.customCards = window.customCards || [];
  if (!window.customCards.some((c) => c.type === CARD_TAG)) {
    window.customCards.push({
      type: CARD_TAG,
      name: "CoverAutomatic",
      description: I18N[(navigator.language || "en").slice(0, 2)]?.desc || I18N.en.desc,
      preview: true,
      documentationURL: "https://github.com/crandler/CoverAutomatic",
    });
  }
})();
