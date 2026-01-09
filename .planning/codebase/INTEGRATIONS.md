# External Integrations

**Analysis Date:** 2026-01-09

## APIs & External Services

**Payment Processing:**
- Not applicable

**Email/SMS:**
- Not applicable

**External APIs:**
- Not detected (no HTTP/REST calls)

## Data Storage

**Databases:**
- Not applicable (file-based data)

**File Storage:**
- Local filesystem only
- PFF World Cup 2022 data in `Fifa world cup 2022 data/` directory
- Activity logs in `logs/activity_log.md`

**Caching:**
- Streamlit `@st.cache_resource` for in-memory data caching

## Authentication & Identity

**Auth Provider:**
- Not applicable (no authentication)

**OAuth Integrations:**
- Not applicable

## Monitoring & Observability

**Error Tracking:**
- None (console logging only)

**Analytics:**
- Not applicable

**Logs:**
- Custom `ActivityLogger` class in `src/activity_logger.py`
- File-based logging to `logs/activity_log.md`

## CI/CD & Deployment

**Hosting:**
- Railway - Cloud hosting platform
- `Procfile` - Deployment configuration
- Documentation: `docs/railway_deployment.md`

**CI Pipeline:**
- Not detected (no GitHub Actions or similar)

## Environment Configuration

**Development:**
- Required env vars: None
- Secrets location: Not applicable
- Data: Bundled in `Fifa world cup 2022 data/` directory

**Staging:**
- Not applicable

**Production:**
- Railway auto-assigns `$PORT` environment variable
- No secrets required

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Sources

**PFF FIFA World Cup 2022 Dataset:**
- Type: Sports tracking and event data
- Loading: `kloppy.pff` module
- Location: `Fifa world cup 2022 data/`
- Files:
  - Metadata: `Metadata/{game_id}.json`
  - Rosters: `Rosters/{game_id}.json`
  - Tracking: `Tracking Data/{game_id}.jsonl.bz2`
  - Events: `Event Data/{game_id}.json`
- Default: Game 3821 (Germany vs Japan)
- Format: 29.97 fps tracking data, normalized 0-1 coordinates

**Metrica Sports Open Data:**
- Type: Alternative football tracking dataset
- Loading: `kloppy.metrica` in `main.py`
- Used by: Tkinter desktop UI (`src/ui.py`)

---

*Integration audit: 2026-01-09*
*Update when adding/removing external services*
