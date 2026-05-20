# Comelit Man — Quality Audit

**Last full sweep:** Sweep 5 (final triage) — 2026-05-06; Phase 1 fixes applied 2026-05-20; Phase 2 bundle applied 2026-05-20; Bundle A+B applied 2026-05-20
**Version at audit:** 0.1.4.3
**Tier claim (CLAUDE.md):** Bronze (initial)
**Tier verdict (audited):** Bronze PASS; Silver NOT YET (1 FAIL remaining — test-coverage BL-023); Gold NOT YET (5 FAIL remaining — diagnostics, repairs, exception-translations, docs×4, discovery); Platinum NOT YET (1 FAIL remaining — strict-typing BL-010); Beyond A-D 13/13 PASS; Beyond E 4 PASS / 2 PARTIAL / 16 N/A of 22 ADRs; Beyond F 4 PASS / 1 accepted-FAIL of 5; Beyond G 3 PASS / 1 PARTIAL / 1 N/A of 5; Beyond H 1 PASS / 1 PARTIAL of 2 (read-only)
**Stale rows:** 0 (sum of Stale columns across all dashboards). When this becomes ≥1, schedule re-verification of the affected rows.
**Next review due:** when all sweeps land OR +90 days from last full sweep, whichever first
**Freshness rule:** any row is `STALE` if `Verified` date > 90 days old OR older than the current `manifest.json` minor version (`0.1.x`).

---

## Sources (drive every row below)

| Source | URL | Used by |
|---|---|---|
| HA Integration Quality Scale | https://developers.home-assistant.io/docs/core/integration-quality-scale/ | All tiers |
| HA Quality Scale checklist | https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist | Per-rule rows |
| HA Architecture Decision Records | https://github.com/home-assistant/architecture/tree/master/adr | Beyond-scale E |
| HA developer docs (file structure) | https://developers.home-assistant.io/docs/creating_integration_file_structure/ | Bronze structure |
| HA Brands repo | https://github.com/home-assistant/brands | Bronze brands, BL-014 |
| HACS publish (integration) | https://www.hacs.xyz/docs/publish/integration/ | Beyond-scale F |
| HACS validation action | https://github.com/hacs/action | Beyond-scale G |
| hassfest | https://developers.home-assistant.io/docs/creating_integration_manifest/ | Beyond-scale G |
| pytest-homeassistant-custom-component | https://github.com/MatthewFlamm/pytest-homeassistant-custom-component | BL-013 |
| HA Diagnostics platform | https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics | Silver/Gold |
| HA Repairs platform | https://developers.home-assistant.io/docs/core/platform/repairs/ | Gold, BL-008 |

---

## Tier Summary (dashboard)

Status legend: `PASS | FAIL | PARTIAL | N/A | STALE | UNVERIFIED`
Verdict is `MET` only when every rule in the tier is `PASS` or `N/A`.

| Tier | Pass | Fail | Partial | N/A | Stale | Unverified | Total | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Bronze   | 14 | 1 | 1 | 2 | 0 | 0 | 18 | NOT YET — `brands` FAIL is *accepted* (won't fix); 1 PARTIAL remaining (BL-020 common-modules) |
| Silver   | 4 | 3 | 2 | 1 | 0 | 0 | 10 | NOT YET (3 FAIL, 2 PARTIAL) |
| Gold     | 4 | 10 | 4 | 3 | 0 | 0 | 21 | NOT YET (10 FAIL, 4 PARTIAL) |
| Platinum | 1 |  2 | 0 | 0 | 0 | 0 |  3 | NOT YET (2 FAIL) |

Beyond-scale dashboard:

| Dimension | Pass | Fail | Partial | N/A | Stale | Unverified | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — Credentials & secrets | 3 | 0 | 0 | 0 | 0 | 0 | 3 |
| B — Resource lifecycle | 2 | 1 | 1 | 0 | 0 | 0 | 4 |
| C — Resilience | 4 | 0 | 0 | 0 | 0 | 0 | 4 |
| D — Logging hygiene | 1 | 0 | 1 | 0 | 0 | 0 | 2 |
| E — HA ADR compliance | 5 | 0 | 1 | 16 | 0 | 0 | 22 |
| F — HACS submission | 4 | 0 | 0 | 1 | 0 | 0 | 5 |
| G — Automated checks | 4 | 0 | 0 | 1 | 0 | 0 | 5 |
| H — LOCKED-file boundary | 1 | 0 | 1 | 0 | 0 | 0 | 2 |

---

## Bronze Rules

Rule URL pattern: `https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/<slug>`

| Rule | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| action-setup | N/A | No service actions registered. `__init__.py:77` only registers static paths and Lovelace resources; no `hass.services.async_register` anywhere in `custom_components/comelit_man/` (grep confirmed). Integration exposes only entities. | 2026-05-06 | — |
| appropriate-polling | PASS | `iot_class: local_push` in `manifest.json:9`. `coordinator.py:32` `UPDATE_INTERVAL = timedelta(seconds=30)` drives `_async_update_data` (`coordinator.py:585`) which only health-checks the connection — actual events arrive via `VipEventListener` on CTPP. 30 s for a connectivity check is reasonable for a local push integration. | 2026-05-06 | — |
| brands | FAIL — accepted | Rule requires brand assets registered in `home-assistant/brands` repo. Verified absent (HTTP 404 on icon.png at master). **User decision 2026-05-06: upstream PR is out of scope; local `custom_components/comelit_man/brand/icon.png` is acceptable for this integration.** Bronze `brands` will remain FAIL — accept it; do not re-open. | 2026-05-06 | BL-014 (won't fix — upstream) |
| common-modules | PARTIAL | `coordinator.py` exists ✓. No shared `entity.py` base class — each entity file (`button.py:45,107,147`, `camera.py:47,83`, `event.py:31`) re-implements `device_info`/`_attr_has_entity_name` boilerplate. Rule wants common patterns extracted. | 2026-05-06 | BL-020 |
| config-flow | PASS | `manifest.json:5` `"config_flow": true`. `config_flow.py:37` `ComelitLocalConfigFlow` with `async_step_user` (line 49). Translations present in `strings.json:22-54` and `translations/en.json`. Options flow in `config_flow.py:107`. | 2026-05-06 | — |
| config-flow-test-coverage | PASS | `tests/test_ha_component.py` fully repaired 2026-05-20: stale imports fixed, constructor signature updated, patch paths corrected, `hass.data`→`entry.runtime_data` assertions updated, voluptuous stub added to conftest. File added to CI test list (`validate.yml`). 24/24 tests pass. | 2026-05-20 | — |
| dependency-transparency | PASS | `manifest.json:10` declares `"requirements": ["aiohttp>=3.9", "av>=12.0.0"]`. Both are pinned with lower bounds (no upper bounds — Platinum concern, not Bronze). | 2026-05-06 | — |
| docs-actions | N/A | No service actions exist (cross-link to `action-setup`). | 2026-05-06 | — |
| docs-high-level-description | PASS | `README.md:1-11` opens with brand/product overview ("Home Assistant custom component for the Comelit 6701W WiFi video intercom...") and feature bullets. | 2026-05-06 | — |
| docs-installation-instructions | PASS | `README.md:19-48` "Installation" (HACS + manual) and "Configuration" sections with step-by-step setup including prerequisites at `README.md:13-17`. | 2026-05-06 | — |
| docs-removal-instructions | PASS | `README.md` "Removing the integration" section added 2026-05-20: steps for Settings → Delete + note about push-channel lapse. | 2026-05-20 | — |
| entity-event-setup | PASS | `event.py:59-61` registers push callback in `async_added_to_hass` via `async_on_remove`. `camera.py:172-193` registers/unregisters callbacks in `async_added_to_hass`/`async_will_remove_from_hass`. `button.py` uses `CoordinatorEntity` which the framework manages. | 2026-05-06 | — |
| entity-unique-id | PASS | All entities set `_attr_unique_id`: `button.py:61` (`{entry_id}_door_{door.index}`), `button.py:122` (`_video_start`), `button.py:162` (`_video_stop`), `camera.py:64` (`_camera_{id}`), `camera.py:113` (`_intercom_camera`), `event.py:47` (`_doorbell`). | 2026-05-06 | — |
| has-entity-name | PASS | `_attr_has_entity_name = True` on every entity class: `button.py:48,110,150`, `camera.py:50,99`, `event.py:34`. | 2026-05-06 | — |
| runtime-data | PASS | `__init__.py:117` `entry.runtime_data = coordinator`. Type alias `coordinator.py:601` `ComelitLocalConfigEntry: TypeAlias = ConfigEntry[ComelitLocalCoordinator]`. Used consistently in `__init__.py:91,134`, `button.py:25`, `camera.py:25`, `event.py:23`. | 2026-05-06 | — |
| test-before-configure | PASS | `config_flow.py:73-84`: instantiates `IconaBridgeClient`, calls `connect()` and `authenticate()` with timeouts before `async_create_entry` (line 90). Maps failures to `invalid_auth`/`cannot_connect` errors (lines 77-82). | 2026-05-06 | — |
| test-before-setup | PASS | `__init__.py:102-115` wraps `coordinator.async_setup()` and raises `ConfigEntryAuthFailed` on `AuthenticationError` (line 105) and `ConfigEntryNotReady` on `TimeoutError`/`ComelitConnectionError`/`OSError` (line 109) and any other `Exception` (line 113). | 2026-05-06 | — |
| unique-config-entry | PASS | `config_flow.py:87-88`: `await self.async_set_unique_id(host)` followed by `self._abort_if_unique_id_configured()`. Aborts with `already_configured` (string in `strings.json:51`). | 2026-05-06 | — |

## Silver Rules

| Rule | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| action-exceptions | N/A | No service actions registered (cross-link to bronze:action-setup). | 2026-05-06 | — |
| config-entry-unloading | PASS | `__init__.py:133-140` `async_unload_entry` — calls `async_unload_platforms`, then `entry.runtime_data.async_shutdown()` on success. `coordinator.py:242-257` `async_shutdown` cancels keepalive, stops video session, stops VIP listener, stops RTSP server, disconnects client. Options-flow reload wired at `__init__.py:121,126-130`. | 2026-05-06 | — |
| docs-configuration-parameters | PASS | `README.md:40-48` documents the `Enable Notifications` option (the only configurable option after setup). Strings/translations cover the description: `strings.json:9-21`. | 2026-05-06 | — |
| docs-installation-parameters | PASS | `README.md:32-39` documents host + token + password setup steps. Per-field labels and descriptions in `strings.json:22-44` (host, port, http_port, token, password). | 2026-05-06 | — |
| entity-unavailable | PARTIAL | `button.py:45,107,147` inherit `CoordinatorEntity[ComelitLocalCoordinator]` → buttons auto-mark unavailable when `coordinator.last_update_success` is False ✓. `camera.py:47,83` `class ...(Camera)` and `event.py:31` `class ...(EventEntity)` do **not** inherit `CoordinatorEntity` and never set `_attr_available`, so they remain "available" even when coordinator/connection is dead. Grep: only button.py uses `CoordinatorEntity`. | 2026-05-06 | BL-021 |
| integration-owner | PASS | `manifest.json:4` `"codeowners": ["@mnestrud"]`. | 2026-05-06 | — |
| log-when-unavailable | PARTIAL | Connection-level transitions logged: `coordinator.py:592` `_LOGGER.warning("Comelit device disconnected, attempting reconnect")`, `coordinator.py:240` `_LOGGER.info("Comelit reconnected successfully")`. However, this fires on every reconnect cycle (no edge-detection) and is not entity-level — rule wants once-only entity-level transitions. | 2026-05-06 | BL-022 |
| parallel-updates | FAIL | No `PARALLEL_UPDATES` constant declared anywhere in `custom_components/comelit_man/` (grep returned no matches across all platforms). Rule requires the constant per platform. | 2026-05-06 | BL-005 |
| reauthentication-flow | FAIL | `config_flow.py` has only `async_step_user` (line 49) and the options flow (line 113). No `async_step_reauth` (grep confirmed empty). When the device token is rotated, the user must delete + re-add the integration. | 2026-05-06 | BL-004 |
| test-coverage | FAIL | Rule requires >95% coverage across modules. (1) No coverage measurement infrastructure: no `.coveragerc`, no `pytest-cov` in `validate.yml:46-47` deps, no coverage threshold gate. (2) Multiple modules untested: `camera_utils.py` (BL-011), `models.py`, `exceptions.py`, `auth.py` standalone (test_auth.py exists but excluded from CI list at `validate.yml:50-66`), `config_reader.py`. (3) `test_ha_component.py` (the only `__init__.py`/config-flow test) is broken + excluded (cross-link to bronze:config-flow-test-coverage / BL-018). | 2026-05-06 | BL-023 |

## Gold Rules

| Rule | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| devices | PASS | All entities provide `DeviceInfo`. Buttons + intercom camera + doorbell event share `(DOMAIN, entry_id)` (`button.py:67-72,127-132,167-172`, `camera.py:131-138`, `event.py:50-57`). Additional cameras get their own device with `via_device` (`camera.py:67-75`). `manufacturer`/`model` set from `const.py:4-5`. | 2026-05-06 | — |
| diagnostics | FAIL | No `diagnostics.py` file (Glob confirmed absent). | 2026-05-06 | BL-003 |
| discovery | FAIL | `manifest.json` has no `dhcp` / `zeroconf` / `ssdp` / `bluetooth` / `usb` keys (grep confirmed). Device is discoverable via UDP `INFO` to port 24199 per CLAUDE.md device-quirks section but no discovery flow is registered. | 2026-05-06 | BL-030 |
| discovery-update-info | N/A | Depends on `discovery` being implemented first; deferred until BL-030. | 2026-05-06 | (gated on BL-030) |
| docs-data-update | PARTIAL | `README.md:152-167` "Protocol" section explains the channels and event flow conceptually. Rule wants an explicit "Data update" / how-data-refreshes section — current docs require the reader to infer it. | 2026-05-06 | BL-029 |
| docs-examples | PASS | `README.md:91-150` shows three automation examples (notify on ring, notify with camera link, notify and start video). | 2026-05-06 | — |
| docs-known-limitations | FAIL | No "Known limitations" section in `README.md` (211 lines reviewed end-to-end). | 2026-05-06 | BL-029 |
| docs-supported-devices | PARTIAL | `README.md:15` mentions "Comelit 6701W (or compatible ICONA Bridge device)" — single-line mention, no explicit supported/unsupported model + firmware list. | 2026-05-06 | BL-029 |
| docs-supported-functions | PASS | `README.md:50-59` "Entities" table lists every entity and what it does. `README.md:62-85` documents the Lovelace cards. | 2026-05-06 | — |
| docs-troubleshooting | FAIL | No troubleshooting section in `README.md`. CLAUDE.md has a debug-logging hint that hasn't been ported to user docs. | 2026-05-06 | BL-029 |
| docs-use-cases | PASS | `README.md:87-150` covers three doorbell use-cases (notify only, notify + open camera, notify + auto-start video). | 2026-05-06 | — |
| dynamic-devices | N/A | The 6701W has fixed physical topology — doors and cameras are wired into the building and cannot be added at runtime. UCFG fetched at setup + reconnect (`coordinator.py:143,217`); no need for runtime addition. | 2026-05-06 | — |
| entity-category | PARTIAL | No `_attr_entity_category` set on any entity (grep confirmed). Door-open buttons + intercom camera + doorbell event are correctly primary (no category needed) ✓. Start Video Feed / Stop Video Feed buttons (`button.py:107,147`) are arguably `EntityCategory.DIAGNOSTIC` — they don't represent device functions, just session control. | 2026-05-06 | BL-031 |
| entity-device-class | FAIL | No `_attr_device_class` anywhere (grep confirmed). Doorbell event entity should set `EventDeviceClass.DOORBELL`. Door buttons could use a button device class but options are limited. | 2026-05-06 | BL-028 |
| entity-disabled-by-default | PARTIAL | No `_attr_entity_registry_enabled_default` set (grep confirmed). All entities enabled. Start Video Feed / Stop Video Feed buttons could reasonably default-disabled (most users will use them via the Lovelace card, not as bare entities). | 2026-05-06 | BL-031 |
| entity-translations | FAIL | Only `event.py:35` sets `_attr_translation_key = "doorbell"`. Buttons + cameras use hardcoded English names: `button.py:62` (door name from device), `button.py:112` `_attr_name = "Start Video Feed"`, `button.py:152` `_attr_name = "Stop Video Feed"`, `camera.py:65` (camera name from device), `camera.py:100` `_attr_name = "Live Feed"`. | 2026-05-06 | BL-025 |
| exception-translations | FAIL | No `translations/exceptions.json` (Glob confirmed absent). Config-flow errors translated via `strings.json:46-50` ✓ but runtime exceptions raised in coordinator/entities (`RuntimeError` in `coordinator.py:321,349,356,360,369,380`, `DoorOpenError`, `VideoCallError`) are not. | 2026-05-06 | BL-026 |
| icon-translations | FAIL | No `icons.json` file (Glob confirmed absent). Icons hardcoded: `_attr_icon = "mdi:door-open"` (`button.py:49`), `mdi:video` (`button.py:111`), `mdi:video-off` (`button.py:151`), `mdi:doorbell-video` (`camera.py:101`), `mdi:doorbell` (`event.py:37`). | 2026-05-06 | BL-027 |
| reconfiguration-flow | FAIL | `config_flow.py` has only `async_step_user` and the options flow; no `async_step_reconfigure` (grep confirmed). Changing host/token requires delete+re-add. | 2026-05-06 | BL-009 |
| repair-issues | FAIL | No `repairs.py` file (Glob confirmed absent). | 2026-05-06 | BL-008 |
| stale-devices | N/A | Fixed topology (cross-link to `dynamic-devices`); devices never go stale at runtime. | 2026-05-06 | — |

## Platinum Rules

| Rule | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| async-dependency | PASS | `aiohttp` is async-native ✓. `av` (PyAV) is synchronous but correctly offloaded: `rtp_receiver.py:470,533` uses `loop.run_in_executor(None, ...)` for both codec init and frame decode, so the event loop is never blocked by FFmpeg calls. All internal modules are async (`client.py`, `auth.py`, `coordinator.py`, `vip_listener.py`, etc.). | 2026-05-06 | — |
| inject-websession | FAIL | `token.py:37` creates its own session: `async with aiohttp.ClientSession(timeout=timeout) as session:`. Should use HA's `homeassistant.helpers.aiohttp_client.async_get_clientsession(hass)` instead. `extract_token` is called from `config_flow.py:67` where `self.hass` is available, so plumbing is straightforward. | 2026-05-06 | BL-024 |
| strict-typing | FAIL | No `pyproject.toml`, `mypy.ini`, `setup.cfg`, or `py.typed` marker file (Bash find confirmed all absent). No mypy step in `validate.yml`. Source has type hints throughout (e.g., `coordinator.py:38-46`) but no strict-mode enforcement. | 2026-05-06 | BL-006, BL-010 |

---

## Beyond-Scale Audit

Same row shape as the tier tables. Run in Sweeps 4a–4d. LOCKED-file findings (`door.py`, `video_call.py`) are tagged `Locked: YES` and `REQUIRES OWNER APPROVAL` — never auto-fixed.

### A — Credentials & secrets (Sweep 4a)

| Check | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| Token storage location (config entry data vs. options vs. plaintext) | PASS | Stored in `ConfigEntry.data[CONF_TOKEN]` (`config_flow.py:95`) — HA's standard config registry, encrypted at rest. Read at `__init__.py:99`. Held in `coordinator.py:56` as instance variable for runtime use. No file writes, no plaintext persistence. | 2026-05-06 | — |
| `grep -ni "token\|password\|cookie"` across logging paths shows no secret leakage | PASS | (a) Auth token: only `token.py:135` logs it, masked to first/last 4 chars (`%s...%s` with `token[:4]`/`token[-4:]`) — flagged with `# nosemgrep`. (b) UDPM session token at `video_call.py:295,492-493`: ephemeral 16-bit stream identifier, not a secret. (c) FCM `DEVICE_TOKEN = "comelit-local-ha-integration"` at `push.py:17`: hardcoded constant we mint, not a secret. (d) `config_flow.py:69` `_LOGGER.exception("Token extraction failed: %s", err)` — `err` from `extract_token` only contains `TokenExtractionError` messages (HTTP status, file size); no token contents — verified by reading `token.py:51,54,71,80,86,101,138,144,146`. | 2026-05-06 | — |
| Auth error paths (UAUT failures) do not echo token in exception or log | PASS | `auth.py:30-33` builds error from `response.get("response-code")` + `response.get("response-string")` only — never echoes `token`. Caller `coordinator.py:142,216` propagates the `AuthenticationError` unchanged; `__init__.py:104-107` re-raises as `ConfigEntryAuthFailed(f"Authentication failed for Comelit device: {err}")`, again not including the token. | 2026-05-06 | — |

### B — Resource lifecycle (Sweep 4a)

| Check | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| Every `asyncio.create_task` has a matching cancel on unload | PARTIAL | **Tracked tasks (cancel-on-stop verified):** `client.py:88` receive task → `client.py:100` `task.cancel()` in `disconnect()`; `coordinator.py:464` keepalive → `coordinator.py:466-470` `_cancel_keepalive`; `vip_listener.py:148` listen loop → `vip_listener.py:158` `self._task.cancel()`; `rtsp_server.py:209-210` 2 loops → `rtsp_server.py:223` `task.cancel()`; `rtp_receiver.py:186,200` keepalive + decode → `rtp_receiver.py:602` `task.cancel()`; `video_call.py:447,450,498` (LOCKED — read-only check) tracked in instance vars. **Untracked fire-and-forget:** `button.py:92` (10s delayed video-stop), `coordinator.py:435` (auto-restart video on CALL_END), `coordinator.py:583` (refresh on disconnect), `video_call.py:483` (LOCKED). All four use `hass.async_create_task` (HA-supervised) so they're not strict leaks, but they continue to run after entry unload and call into a partially-shut-down coordinator. | 2026-05-06 | BL-032 |
| RTSP server stopped on `async_unload_entry` | PASS | Chain: `__init__.py:139` → `coordinator.async_shutdown()` (`coordinator.py:242`) → `coordinator.py:250-253` calls `self._rtsp_server.stop()` and clears the reference. `rtsp_server.py:216-223` `stop()` cancels tasks and closes server socket. | 2026-05-06 | — |
| All UDP/TCP sockets closed on unload (RTP receiver, ICONA client) | PASS | TCP: `client.py:91-106` `disconnect()` cancels receive task and calls `self._writer.close()` + `await self._writer.wait_closed()`. UDP (RTP receiver): `rtp_receiver.py:589-602` `stop()` cancels keepalive + decode tasks and closes the `DatagramTransport`. Both invoked from `coordinator.async_shutdown()` via `async_stop_video()` → session.stop() (LOCKED) and `client.disconnect()` (`coordinator.py:256`). | 2026-05-06 | — |
| `async_remove_entry` defined and clears persisted state if any | FAIL | `grep` for `async_remove_entry` returned no matches across `custom_components/`. Currently no per-entry persisted state outside the `ConfigEntry` itself, but the FCM push registration with the device should be unregistered on remove (cross-link to `push.py:53` "Push notifications registered" — never explicitly de-registered). | 2026-05-06 | BL-002 |

### C — Resilience (Sweep 4a)

| Check | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| Reconnect/backoff after the device's wifi-sleep disconnect | PASS | Two-layer detection: (1) Receive-loop 120s timeout in `client.py` → calls disconnect callback → `coordinator.py:573-583` `_on_client_disconnect` schedules immediate refresh. (2) `coordinator.py:585-596` `_async_update_data` runs every 30 s, checks `self._client.connected`, calls `_reconnect()` when False. Backoff inherited from HA's `DataUpdateCoordinator` framework (sufficient for this use case — no need for explicit exponential backoff on a local-network device). | 2026-05-06 | — |
| Keepalive timer reset behavior on reconnect | PASS | `coordinator.py:461-464` `_start_keepalive` cancels any previous task before creating a new one. Called at setup (`coordinator.py:168`) and after every successful reconnect (`coordinator.py:239`). The 90-second keepalive (`coordinator.py:472-503`) sends `push-info` to keep the device's TCP idle-timer reset. | 2026-05-06 | — |
| VIP listener auto-restarts on TCP drop | PASS | `coordinator.py:200-203` stops old VIP in `_reconnect`. `coordinator.py:228-237` starts new VIP after reconnect (when notifications enabled). Additional restart point: `coordinator.py:505-525` `_ensure_vip_listener` is called from `async_stop_video` (line 565) so VIP picks up the CTPP slot after a video session ends. Init timestamp preserved across restart via `self._ctpp_init_ts` (line 75) so the device's CTPP counter stays consistent. | 2026-05-06 | — |
| RTSP server idle behavior — no leak between calls, gating works | PASS | RTSP server is a singleton started once at setup (`coordinator.py:171-175`) and only stopped at shutdown (`coordinator.py:250-253`). Per-session gating: `mark_ready()` set when video starts (`coordinator.py:425-426`), `mark_not_ready()` + `disconnect_clients()` on stop (`coordinator.py:558-560`) and reconnect (`coordinator.py:196-198`). `stream_source()` waits up to 5 s on `_video_ready_event` (`camera.py:140-161`). RTCP Sender Reports every 5 s (CLAUDE.md video section). | 2026-05-06 | — |

### D — Logging hygiene (Sweep 4a)

| Check | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| All `_LOGGER.info` sites inventoried with keep/downgrade decision | PARTIAL | **39 sites inventoried** (grep). Categorized: (a) **Setup/lifecycle, fires once-per-session — keep info:** `__init__.py:86`, `coordinator.py:131,166,175,178`, `vip_listener.py:149`, `rtsp_server.py:213`, `auth.py:35`, `push.py:53`, `config_reader.py:95`. (b) **User-action logs — keep info:** `button.py:76,84,103,139,142,176`, `door.py:57` (LOCKED), `event.py:69`, `coordinator.py:376,395,416,434`. (c) **First-of-kind diagnostic loggers (fire once per session) — keep:** `rtp_receiver.py:244,264` (transport detection), `video_call.py:825` (audio-start landmark, LOCKED), `client.py:181`. (d) **Reconnect-cycle loggers — should be edge-detected (BL-022):** `coordinator.py:240` "reconnected successfully", `coordinator.py:523` "VIP event listener restarted". (e) **LOCKED — read-only audit:** `video_call.py:473,500,514,825,845,854`, `door.py:57`, `vip_listener.py:234,336,408`, `rtsp_server.py:447,669` (one-shot landmarks, fine). Per-call review still owed for borderline cases (e.g., `coordinator.py:395+416` are redundant with `button.py:139+142`). | 2026-05-06 | BL-007 |
| No PII or token at any log level (cross-link to A) | PASS | Cross-references Dimension A. Apt-address strings (e.g. `SB000006`) are logged in `event.py:69` and `vip_listener.py:408` — these are building/door identifiers, not user PII. Host IP is logged at info on connect/reconnect — operational state. No user names, no GPS, no MAC addresses persisted in logs at info level. | 2026-05-06 | — |

### E — HA ADR compliance (Sweep 4b)

ADR index pulled from `https://github.com/home-assistant/architecture/tree/master/adr`. URL pattern for any specific ADR: `https://github.com/home-assistant/architecture/blob/master/adr/<filename>`.

| ADR | Title | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|---|
| 0001 | Record Architecture Decisions | N/A | Process for HA core itself; not applicable to custom integrations. | 2026-05-06 | — |
| 0002 | Minimum Supported Python Version | N/A | Superseded by ADR-0020. | 2026-05-06 | — |
| 0003 | Monitor Condition and Data Selectors | N/A | Integration registers no triggers/conditions; only entity-platform schemas. `config_flow.py:25-34` uses `voluptuous` types directly which HA renders with default selectors. | 2026-05-06 | — |
| 0004 | Webscraping | N/A | No external webscraping. `token.py` does HTTP login to the **local LAN device** to extract a backup tarball — local-device interaction, not third-party scraping. | 2026-05-06 | — |
| 0005 | Code Formatting | PASS | `validate.yml:24-33` runs `ruff check custom_components/` on every push and PR. | 2026-05-06 | — |
| 0006 | Docker Images | N/A | HA core distribution decision; custom integrations are not affected. | 2026-05-06 | — |
| 0007 | Integration Config YAML Structure | N/A | Integration is config-flow only; no YAML schema. | 2026-05-06 | — |
| 0008 | Code Owners | PASS | `manifest.json:4` `"codeowners": ["@mnestrud"]`. | 2026-05-06 | — |
| 0009 | Translations 2.0 | PARTIAL | `strings.json` + `translations/en.json` exist for config-flow, options-flow, and one event entity (`event.py:35` `_attr_translation_key = "doorbell"`). **Missing:** entity-name translations (BL-025), exception translations (BL-026), icon translations (BL-027) — all already filed under Gold rules. | 2026-05-06 | BL-025, BL-026, BL-027 |
| 0010 | Integration Configuration | PASS | `manifest.json:5` `"config_flow": true`. Sole configuration mechanism is the UI flow at `config_flow.py:37`; no YAML configuration exists. | 2026-05-06 | — |
| 0011 | Discovery Requires Unique ID | N/A (deferred) | Integration has no discovery flow today (`bronze:` not affected; `gold:discovery` FAIL → BL-030). When BL-030 lands, the discovery flow MUST set `unique_id` per this ADR. The user-flow already does so at `config_flow.py:87`, so the pattern is established. | 2026-05-06 | (gated on BL-030) |
| 0012 | Define Supported Installation Methods | N/A | Core distribution decision. | 2026-05-06 | — |
| 0013 | Home Assistant Container | N/A | Core distribution decision. | 2026-05-06 | — |
| 0014 | Home Assistant Supervised | N/A | Core distribution decision. | 2026-05-06 | — |
| 0015 | Home Assistant OS | N/A | Core distribution decision. | 2026-05-06 | — |
| 0016 | Home Assistant Core | N/A | Core distribution decision. | 2026-05-06 | — |
| 0017 | Hardware Screening OS | N/A | Core hardware decision. | 2026-05-06 | — |
| 0018 | Supported Databases | N/A | Core database decision; integration uses no recorder-direct or DB code. | 2026-05-06 | — |
| 0019 | GPIO | N/A | Integration does not use GPIO. | 2026-05-06 | — |
| 0020 | Minimum Supported Python Version | PARTIAL | `README.md:17` declares "Home Assistant 2026.1+" (which mandates Python 3.13). However, (a) `manifest.json` has no `homeassistant` minimum-version field — hassfest may not enforce the README's claim. (b) `validate.yml:39-40` matrix runs Python 3.11 + 3.12 + 3.13 — testing 3.11/3.12 is wasted work given HA 2026.1's 3.13 floor and risks false-positive CI green when 3.13-only syntax is used in source. | 2026-05-06 | BL-033 |
| 0021 | YAML Integration Configuration Deprecation Policy | N/A | Integration is config-flow only; no YAML schema to deprecate. | 2026-05-06 | — |
| 0022 | Integration Quality Scale | PASS | This audit document IS the response to ADR-0022. The integration follows the quality-scale framework even though it does not yet meet any tier formally. CLAUDE.md declares the tier (Bronze, initial) and references this audit file. | 2026-05-06 | — |

### F — HACS submission compliance (Sweep 4c)

| Check | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| `hacs.json` present and valid | PASS | `hacs.json` exists at repo root: `{"name": "Comelit Man", "render_readme": true}`. Minimal but valid for a single-integration custom repo. The hacs/action job in `validate.yml:8-15` runs on every push and would flag schema errors. | 2026-05-06 | — |
| Repo topics include the HACS-required topics | FAIL | `gh repo view mnestrud/comelit-man --json repositoryTopics` returned `repositoryTopics: null`. HACS recommends `home-assistant`, `homeassistant`, `hacs`, `integration` plus device-specific tags. | 2026-05-06 | BL-035 |
| GitHub releases used (semver, not zip uploads) | FAIL | `gh release list -R mnestrud/comelit-man` returned no rows; `gh api repos/mnestrud/comelit-man/releases` returned `[]`. `latestRelease` = null. The `manifest.json:11` version is at `0.1.4.3` and `CHANGELOG.md` exists, but no GitHub releases tag any of these. HACS users currently install from `main` HEAD instead of stable releases. | 2026-05-06 | BL-034 |
| Brand registration in `home-assistant/brands` | FAIL — accepted | Verified absent (HTTP 404 on `home-assistant/brands/master/custom_integrations/comelit_man/icon.png`). **User decision 2026-05-06 (Sweep 1):** upstream PR is out of scope; local `brand/icon.png` accepted. Cross-link to `bronze:brands` row. | 2026-05-06 | (won't fix — see Sweep 1 amendment) |
| No bundled zip in repo root | PASS | Glob `*.zip` against repo root returned no matches. | 2026-05-06 | — |

### G — Automated checks coverage (Sweep 4c)

| Check | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| hassfest job present in CI | PASS | `validate.yml:17-22` `hassfest` job runs `home-assistant/actions/hassfest@master` on every push and PR. | 2026-05-06 | — |
| `hacs/action` validation job present in CI | PASS | `validate.yml:8-15` `HACS Validation` job runs `hacs/action@main` with `category: integration`. | 2026-05-06 | — |
| ruff job present in CI | PASS | `validate.yml:24-33` `Ruff` job runs `ruff check custom_components/`. (Cross-link to ADR-0005.) | 2026-05-06 | — |
| pytest matrix covers supported Python versions | PARTIAL | `validate.yml:38-40` matrix: `["3.11", "3.12", "3.13"]`. HA 2026.1+ requires Python 3.13 (per `README.md:17`); the 3.11/3.12 jobs are wasted CI minutes and risk false-positive green when 3.13-only syntax is present. Cross-link to ADR-0020. **Also:** test list at `validate.yml:50-66` excludes several test files (cross-link to bronze:config-flow-test-coverage / BL-018). | 2026-05-06 | BL-033 (Python matrix), BL-018 (test list) |
| Brands lint job (or manual check documented) | N/A | Brand registration is accepted-FAIL (out of scope per user decision 2026-05-06); a brands-lint CI step would only enforce the upstream PR which won't be filed. | 2026-05-06 | — |

### H — LOCKED-file boundary (Sweep 4d, read-only)

**Audit policy applied:** Both files were read end-to-end. Findings recorded as observations with `Locked: YES, REQUIRES OWNER APPROVAL`. **No source code modified.** The integration's most-protected protocol logic lives here; behaviour is "stable, verified" per CLAUDE.md after extensive PCAP-driven debugging.

| Check | Status | Evidence (path:line / SHA) | Verified | Action (BL-NNN) |
|---|---|---|---|---|
| `door.py` audited read-only — findings filed as `Locked: YES` | PARTIAL | **151 lines.** **Findings:** (1) **Latent `NameError` in `finally`** — `door.py:60-63` references `opened_channel`, which is assigned at line 47 inside the `try` block. If `client.get_channel("CTPP")` at line 46 raises (uncommon — dict lookup returning None — but possible on a torn-down client), `opened_channel` is unbound and the finally block throws `NameError`, masking the original exception. Defensive: initialize `opened_channel = False` before `try:`. (2) **Parameter shadowing** — `door.py:49` rebinds the `client` parameter when opening a transient channel; reviewer-cognitive load. Style only; correctness unaffected. (3) **`AuthenticationError` mapping** — Path 3 (`door.py:51`) re-authenticates the transient client; if the token has been rotated, the resulting `AuthenticationError` is wrapped in `DoorOpenError` at `door.py:59` rather than surfaced to trigger the reauth flow (when BL-004 lands). (4) **CLAUDE.md drift** — CLAUDE.md "Door Control" section refers to `open_door_fast` and `open_door_standalone`; the file actually has a single `open_door` entry point that branches internally. Functional behaviour matches the documented logic but the function names are wrong. (5) **Logging:** `door.py:57` info-level "Door 'X' opened successfully (regular path)/(fast path)" — once per door press, appropriate level. No token leakage. | 2026-05-06 | BL-036 (defensive NameError fix — Locked), BL-037 (CLAUDE.md update — not Locked), BL-038 (auth-error reauth mapping — coordinator wrapper, may avoid Locked-file edit) |
| `video_call.py` audited read-only — findings filed as `Locked: YES` | PASS — with notes | **859 lines.** Reflects a mature, protocol-faithful implementation: 11-step `start()`, separate `_ctpp_monitor_loop` with `0x1840`/`0x1860`/`0x1800` state machine, 9-step `_inline_reestablish` for CALL_END recovery without TCP reconnect, audio answer sequence, three independent counters (init_ts, call_ts, call_counter) with PCAP-verified increments (`_CTR_INCR_BYTE4`/`BYTE5`/`BOTH`). **Strengths:** every magic number has a `# PCAP-verified:` justification comment; `_ctpp_lock` correctly serialises counter mutation between CTPP monitor / door-during-video / answer sequence; `_cleanup` (line 517) cancels all tracked tasks with a 2 s timeout each (avoids the 30-40 s freeze on dead TCP observed on 3.14/aarch64); `VIDEO_CHANNEL_NAMES` enumeration prevents leaking channel registrations on cleanup. **Findings:** (1) **One untracked fire-and-forget task** — `video_call.py:483` `asyncio.create_task(self._run_answer_sequence(...))` is not assigned to any instance attribute, so `_cleanup()` cannot cancel it. The wrapping `_run_answer_sequence` already swallows exceptions, so failure mode is silent rather than crashing. Cross-link to BL-032 (filed in Sweep 4a). (2) **`_LOGGER.debug` UDPM token** at line 295 — ephemeral 16-bit stream identifier, not a secret (re-confirmed from Sweep 4a). (3) **Info-level logs** (lines 473, 500, 514, 825, 845, 854) all fire once per session in normal flow — appropriate level. (4) **Type hints** complete throughout; `"Channel"` forward-refs used at lines 124, 172, 583, 678. (5) **Tests** in CI: `tests/test_video_call.py` and `tests/test_video_signaling.py` per `validate.yml:55-57`. The 9-step `_inline_reestablish` path is the highest-risk untested branch — out-of-scope for this read-only sweep, but flagged for BL-023 test-coverage planning. | 2026-05-06 | BL-032 (already filed — covers video_call.py:483); audit observation only — no LOCKED edits proposed |

---

## Recommended Fix Sequence (Sweep 5 output)

Ordering optimised for (a) tier-by-tier achievement, (b) shared-PR efficiency, (c) external-latency parallelism (BL-034/BL-035 first because GitHub state is independent of code work).

### Phase 1 — Bronze MET + quick hygiene wins (~1 day)

| # | ID | What | Why first | Effort |
|---|---|---|---|---|
| 1 | BL-035 | `gh repo edit --add-topic ...` | External, ~2 min | S |
| 2 | BL-034 | `gh release create v0.1.4.3` from CHANGELOG.md | External, ~10 min | S |
| 3 | BL-001 | Add `integration_type: "device"` to manifest | Hassfest will start to enforce | S |
| 4 | BL-033 | Add `"homeassistant": "2026.1.0"` to manifest; trim CI matrix to 3.13 | Aligns version claims with hassfest | S |
| 5 | BL-037 | Update CLAUDE.md "Door Control" function names | 5-min docs fix | S |
| 6 | BL-017 | Add "Removing the integration" section to README | Bronze blocker | S |
| 7 | BL-018 | Fix `test_ha_component.py` imports + add to CI test list | Bronze blocker | S |
| 8 | **BL-020 + BL-021 (one PR)** | Extract `entity.py` base inheriting `CoordinatorEntity` | Bundle: BL-021 falls out of BL-020 if base inherits CoordinatorEntity. Bronze PARTIAL → PASS, Silver PARTIAL → PASS in one move. | M |

**End state:** Bronze MET (effective; `brands` accepted-FAIL); Silver `entity-unavailable` cleared.

### Phase 2 — Silver MET (~2-3 days)

| # | ID | What | Notes | Effort |
|---|---|---|---|---|
| 9 | BL-005 | `PARALLEL_UPDATES = 0` per platform | One-line per file | S |
| 10 | BL-022 | Edge-detect connection state → one-shot warn/info | After BL-007 review confirms which sites collapse | S |
| 11 | BL-004 | `async_step_reauth` in config flow | High-sev Silver blocker | M |
| 12 | BL-013 | Migrate to `pytest-homeassistant-custom-component` | **Prereq for BL-023.** Don't chase 95 % coverage on hand-rolled mocks. | L |
| 13 | BL-011 | Add `tests/test_camera_utils.py` | Folds into Phase 12; do during BL-013 retest | S |
| 14 | BL-023 | `pytest-cov` + `.coveragerc` + threshold gate; close coverage gaps | Largest Silver work item | L |

**End state:** Silver MET.

### Phase 3 — Gold + Platinum MET (~1 week)

| # | ID | What | Notes | Effort |
|---|---|---|---|---|
| 15 | BL-031 | `EntityCategory.DIAGNOSTIC` + `enabled_by_default=False` on Start/Stop Video buttons | Trivial | S |
| 16 | BL-028 | `EventDeviceClass.DOORBELL` on doorbell event | One line | S |
| 17 | BL-027 | Move `mdi:*` icons to `icons.json` | Pure refactor | S |
| 18 | BL-009 | `async_step_reconfigure` | Stacks on BL-004 | M |
| 19 | BL-029 | README expansion: 4 Gold doc rules in one PR | Single PR | M |
| 20 | BL-025 | Entity-name translations | | M |
| 21 | BL-006 | `pyproject.toml` + ruff config + dep upper bounds | **Prereq for BL-010** | S |
| 22 | BL-024 | Replace standalone `aiohttp.ClientSession` in `token.py` with `async_get_clientsession(hass)` | Plumbing only | S |
| 23 | BL-010 | `py.typed` + mypy strict + CI mypy step | Largest Platinum work item | M |
| 24 | BL-026 | Translatable exceptions ⚠ **REQUIRES OWNER APPROVAL** for any LOCKED-file edit | Try coordinator-only first; touch LOCKED files only with explicit approval | M |
| 25 | BL-008 | `repairs.py` for known recoverable failure modes | | M |
| 26 | BL-003 | `diagnostics.py` (redact token) | | M |
| 27 | BL-030 | UDP discovery (port 24199) — set `unique_id` from device MAC per ADR-0011 | Unblocks `gold:discovery-update-info` | M |

**End state:** Gold + Platinum MET (except `bronze:brands` accepted-FAIL forever).

### Phase 4 — final hygiene / optional

| ID | What | Sev |
|---|---|---|
| BL-002 | `async_remove_entry` (FCM unregister) | Medium |
| BL-038 | Door auth-error → reauth mapping (after BL-004) | Low |
| BL-007 | Info-log review (most sites already correct) | Low |
| BL-032 | Track fire-and-forget tasks on entry unload | Low |
| BL-036 | door.py NameError defensive fix — **LOCKED, REQUIRES OWNER APPROVAL** | Low |
| BL-016 | Recover audio-protocol findings doc (or remove CLAUDE.md reference) | Low |
| BL-012 | Coordinator split — DEFERRED, no quality-scale gate | Low |

### Closed during the audit

| ID | Closure reason |
|---|---|
| BL-014 | Decomposed in Sweep 4c — covered by BL-034 + BL-035 + accepted-FAIL brands |
| BL-015 | Decomposed in Sweep 5 — `hacs/action` already in CI; mypy in BL-010; brands lint N/A |
| BL-019 | Merged into BL-014 in Sweep 1 |

---

## Backlog Snapshot

Live source: `memory/comelit_man_backlog.md`. This snapshot is rebuilt at the end of each sweep.

**As of 2026-05-06 (Sweep 5):** 38 items total. 31 Confirmed (active work); 4 Closed (BL-014, BL-015, BL-019 decomposed/merged; BL-012 Deferred); BL-026 + BL-036 are LOCKED-touching items requiring owner approval. See "Recommended Fix Sequence" above for ordering.

---

## Audit Change Log

| Date | Sweep | Change |
|---|---|---|
| 2026-05-06 | 0 | Skeleton created. Rule list pulled from HA quality-scale checklist; all rows `UNVERIFIED`; dashboard zeros; backlog seeded with BL-001..BL-016 in `Triage pending`. No source files modified. |
| 2026-05-06 | 1 | Bronze tier audited end-to-end. 12 PASS / 3 FAIL / 1 PARTIAL / 2 N/A → tier `NOT YET`. New backlog items BL-017 (README removal section), BL-018 (test_ha_component.py broken imports + missing CI inclusion), BL-019 *merged into BL-014* (brands registration is part of HACS hygiene), BL-020 (entity.py shared base). BL-002 re-scoped — Bronze docs-removal split out as BL-017; BL-002 stays as `beyond:B` lifecycle. BL-014 promoted from `gate:none` to `gate:bronze` because brand registration is required by Bronze. No source files modified. |
| 2026-05-06 | 1 (amended) | User decision: upstream brands PR is out of scope. `bronze:brands` row marked **FAIL — accepted**, BL-014 brands portion re-classified Won't fix; BL-014 demoted back to `gate:none` (HACS hygiene only). Bronze effective blockers: 2 FAIL + 1 PARTIAL (BL-017, BL-018, BL-020). |
| 2026-05-06 | 2 | Silver tier audited end-to-end. 4 PASS / 3 FAIL / 2 PARTIAL / 1 N/A → tier `NOT YET`. New backlog items BL-021 (entity-unavailable for camera/event), BL-022 (log-when-unavailable edge-detect once-only), BL-023 (test-coverage infrastructure + raise to 95%). BL-004 + BL-005 confirmed (existed in skeleton). No source files modified. |
| 2026-05-06 | 3 | Gold + Platinum tiers audited end-to-end. Gold: 4 PASS / 10 FAIL / 4 PARTIAL / 3 N/A → `NOT YET`. Platinum: 1 PASS / 2 FAIL → `NOT YET`. New backlog items BL-024 (inject-websession), BL-025 (entity-translations), BL-026 (exception-translations), BL-027 (icon-translations), BL-028 (entity-device-class), BL-029 (Gold docs expansion — limitations / troubleshooting / data-update / supported-devices), BL-030 (UDP discovery), BL-031 (entity-category + disabled-by-default for video buttons). Existing BL-003 / BL-006 / BL-008 / BL-009 / BL-010 confirmed. No source files modified. |
| 2026-05-06 | 4a | Beyond-Scale dimensions A–D audited end-to-end. A (Credentials): 3/3 PASS. B (Lifecycle): 2 PASS / 1 FAIL / 1 PARTIAL. C (Resilience): 4/4 PASS. D (Logging hygiene): 1 PASS / 1 PARTIAL. New backlog item BL-032 (track and cancel HA-supervised fire-and-forget tasks on entry unload). Existing BL-002 (lifecycle), BL-007 (info-level review), BL-022 (edge-detect reconnect logs) confirmed. **Notable:** the integration shows good defensive hygiene — token masking with nosemgrep tags, RTSP gating, keepalive cancel-on-restart, VIP listener auto-restart on reconnect. The main lifecycle gap is the absent `async_remove_entry` (BL-002), already known. No source files modified. |
| 2026-05-06 | 4b | Beyond-Scale dimension E (ADR walk) audited end-to-end. 22 ADRs reviewed. 4 PASS / 0 FAIL / 2 PARTIAL / 16 N/A. **PASS:** 0005 (code formatting), 0008 (code owners), 0010 (config-flow only), 0022 (quality scale). **PARTIAL:** 0009 (translation gaps already tracked in BL-025/026/027), 0020 (Python version mismatch — README says HA 2026.1+ but manifest has no min HA version, CI matrix tests 3.11/3.12 unnecessarily). 16 ADRs are core-distribution / GPIO / YAML — N/A for a config-flow custom integration. New backlog item BL-033. No source files modified. |
| 2026-05-06 | 4c | Beyond-Scale F (HACS submission) + G (Automated checks) audited. F: 2 PASS / 2 eff. FAIL / 1 accepted-FAIL. G: 3 PASS / 1 PARTIAL / 1 N/A. **F findings:** `hacs.json` valid (PASS), repo topics absent (FAIL → BL-035), no GitHub releases (FAIL → BL-034 — `gh api releases` returned `[]` despite manifest.json at 0.1.4.3 + CHANGELOG.md present), brands accepted-FAIL, no bundled zip (PASS). **G findings:** all required CI jobs (hassfest, hacs/action, ruff) present and run on every push/PR; pytest matrix is too wide (BL-033 already filed); brands lint N/A given the won't-fix decision. **Cosmetic note:** GitHub labels the LICENSE as "Other" despite README saying Apache 2.0 and the file content matching — likely missing the canonical first-line marker. Not filed as a backlog item but noted here. ADR-0011 note added to BL-030 body. New backlog items BL-034, BL-035. BL-014 *decomposed* — its remaining scope is fully covered by BL-034/BL-035 plus the accepted-FAIL brand portion. No source files modified. |
| 2026-05-06 | 4d | Beyond-Scale H (LOCKED-file read-only audit) audited end-to-end. **`door.py` PARTIAL** — 5 findings: latent NameError in finally (BL-036, Locked), parameter shadowing (style), auth-error reauth mapping (BL-038), CLAUDE.md drift on function names (BL-037, not Locked), logging clean. **`video_call.py` PASS with notes** — 859 lines, mature PCAP-faithful implementation: per-magic-number `# PCAP-verified:` comments, `_ctpp_lock` serializes counter mutation, `_cleanup` cancels tracked tasks with 2 s timeout, channel enumeration prevents leaks. One untracked fire-and-forget at `video_call.py:483` already covered by BL-032. **No LOCKED files modified.** New backlog items BL-036 (Locked), BL-037, BL-038. |
| 2026-05-06 | 5 | Final triage. Five items moved out of `Triage pending`: BL-001 (Low/none — hygiene), BL-011 (Low/silver — folds into BL-023), BL-013 (Medium/none — prereq for BL-023), BL-016 (re-tagged developer hygiene). BL-012 delinked from `bronze:common-modules` and stays Deferred. **BL-015 decomposed** — work fully covered by BL-010 (mypy job) + already-in-CI hacs/action + accepted-FAIL brands. Added "Recommended Fix Sequence" with 4 phases mapping every Confirmed item to a tier checkpoint. Surfaced **Stale rows** total in the audit summary block (0 today) so CLAUDE.md startup banner can read it. CLAUDE.md startup checklist + banner format updated to include `STALE: <count>` (plan deliverable 3). Deliverables 1-3 from the plan are now complete. |
