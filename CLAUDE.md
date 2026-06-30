# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FasihSM Fetcher** is an internal web application for BPS (Badan Pusat Statistik / Indonesian Statistics Agency) that fetches and manages survey data from the Fasih-SM platform (fasih-sm.bps.go.id). The tool eliminates manual data entry by syncing browser sessions and automating bulk operations on survey samples.

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask application
python src/app.py
```

The app runs on `http://localhost:5000/fasihsm-fetcher` by default. Port can be configured via `PORT` environment variable in `.env` file.

The browser will open automatically on startup.

## Browser Extension Setup

The application requires a Chrome/Brave extension for session synchronization:

1. Navigate to `brave://extensions/` or `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `extension/` folder
4. The **Fasih Session Sync** extension will be active

## Architecture

### Core Application Structure

- **`src/app.py`**: Main Flask application with all routes and SSE endpoints. Handles session management, survey listing, sample fetching, bulk approve/reject operations, and the review form engine.

- **`src/auth_service.py`**: Authentication layer managing SSO login via Keycloak with OTP support. Handles session cookies, CSRF tokens, and session persistence to `cache/session/`.

- **`src/bps_client.py`**: API client for Fasih-SM backend. Implements parallel fetching with ThreadPoolExecutor, progress streaming, and sample data parsing.

- **`src/config_loader.py`**: Configuration management system that loads API endpoints, field mappings, and filter configurations from JSON files in `config/`.

- **`src/utils.py`**: Utility functions for caching (with TTL), state management, date formatting (WITA/WIB/WIT timezones), and stop flag coordination for long-running operations.

### Configuration System

The application uses a JSON-based configuration system in `config/`:

- **`endpoints.json`**: API endpoint definitions (URLs, methods, default payloads)
- **`mappings.json`**: Field mapping definitions for handling API response variations
- **`filters.json`**: Filter configuration (region levels, status values, petugas keys, dynamic data fields)

This design allows the app to adapt to Fasih-SM API changes by modifying JSON files without touching Python code.

### Session and Authentication Flow

1. User logs in via SSO (username/password from `.env`)
2. If OTP is required, app stores pending session and waits for OTP input
3. On successful auth, cookies and CSRF token are saved to `cache/session/session_cache.json`
4. Alternative: Browser extension can inject session cookies directly from an active Fasih-SM tab

### Caching Strategy

Multi-level caching system:

- **Session cache** (`cache/session/`): Login cookies and CSRF tokens
- **Metadata cache** (`cache/metadata/`): Survey settings, templates, validation rules (indefinite TTL)
- **Petugas cache** (`cache/petugas/`): Officer/surveyor lists per survey period (30-day TTL by default)
- **Preview cache** (`cache/preview/`): User-saved CSV snapshots for quick table reloads

Cache keys are generated from survey ID, period ID, and category using `cache_key()` function.

### Real-Time Progress Streaming

Long-running operations (sample fetching, bulk approve/reject) use Server-Sent Events (SSE):

- Flask endpoints return `Response()` with `mimetype='text/event-stream'`
- Generator functions yield JSON progress updates: `data: {"progress": N, "total": M}\n\n`
- Frontend JavaScript uses `EventSource` to consume the stream and update progress bars
- Stop flag mechanism (`set_stop_flag`, `get_stop_flag`) allows user to cancel mid-operation

### Parallel Request Pattern

`bps_client.py` uses `ThreadPoolExecutor` for concurrent API calls:

```python
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_detail, id): id for id in ids}
    for future in futures:
        result = future.result()
        # process result
```

This pattern is used for:
- Fetching sample details in bulk
- Counting assignments by region/officer
- Parallel approval/rejection operations

### Stop Flag Coordination

For cancellable operations:
- `set_stop_flag(period_id, True)` sets a flag in `cache/session/stop_flags.json`
- Long-running loops check `get_stop_flag(period_id)` between iterations
- If flag is set, operation yields a "stopped" message and clears the flag

## Key API Endpoints

### Authentication
- `GET /` - Home page with login status
- `POST /import-sso` - Import SSO credentials from `.env`
- `POST /import-session-cookies` - Import session from browser extension
- `GET /login` - Initiate SSO login flow
- `POST /login-otp` - Submit OTP code
- `GET /logout` - Clear session and logout from SSO

### Survey Management
- `GET /listsurvei/<category>/<survey_id>` - List surveys and select a survey period
- `GET /api/sampel-status?period_id=X` - Get assignment status aggregation
- `POST /api/sampel-fetch` - Fetch samples with filters (SSE stream)
- `POST /api/sampel-stop` - Stop ongoing fetch operation

### Bulk Operations
- `POST /api/auto-approve` - Bulk approve assignments (SSE stream)
- `POST /api/bulk-reject` - Bulk reject assignments (SSE stream)
- `POST /api/approve-stop` - Stop ongoing bulk operation

### CSV Export
- `POST /api/sampel-detail-csv` - Generate detailed CSV (SSE stream with progress)
- `GET /api/sampel-detail-download/<token>` - Download generated CSV

### Review Form
- `GET /review/<assignment_id>` - Load review form engine
- `GET /api/survey-templates/<survey_id>` - Get form templates (cached)
- `GET /api/template-file/<template_id>` - Get template file definition (cached)
- `GET /api/template-validation/<template_id>` - Get validation rules (cached)
- `GET /api/assignment-detail/<assignment_id>` - Get assignment data

### Proxy Endpoints (for filtering)
- `GET /api/proxy/region/metadata?groupId=X` - Get region metadata
- `GET /api/proxy/region/level/<N>` - Get regions at level N
- `POST /api/proxy/counts` - Get assignment counts by filter items
- `GET /api/proxy/users` - Get surveyor list with region filtering

## Environment Variables

Create a `.env` file in the project root:

```env
FASIH_USER=your_sso_username
FASIH_PASS=your_sso_password
PORT=5000
```

These are optional if using the browser extension method for session import.

## Code Sealing

The `suntik.bat` file runs `pt seal config/ src/app.py`, which is a code protection/obfuscation step. The sealed code loads configuration files from an embedded payload at runtime rather than from disk. This is visible in the `PT_SEAL_START` / `PT_SEAL_END` block at the top of `src/app.py`.

When modifying `config/` files or `src/app.py`, re-run `suntik.bat` to regenerate the sealed version.

## Development Notes

- The app uses `DispatcherMiddleware` to mount Flask at `/fasihsm-fetcher` path instead of root
- Signal handlers (`SIGINT`, `SIGBREAK`) are configured for instant shutdown on Ctrl+C
- Flask runs in debug mode with `use_debugger=True` but `use_reloader=False` to prevent double-startup
- The extension sends session data to `POST /import-session-cookies` as JSON with `session_text` field
- Theme preference (dark/light) is stored in `config.json` and persists across sessions
- VPN detection checks for connectivity to `fasih-sm.bps.go.id` domain

## Testing Changes

After modifying code:
1. Restart the Flask app (`python src/app.py`)
2. Test login flow (either SSO or extension-based)
3. Select a survey and period from the list
4. Test sample fetching with various filters
5. Verify progress streaming displays correctly
6. Test bulk operations on a small sample set first
7. Check browser console for JavaScript errors (logged to `POST /api/log` endpoint)

## Communication Style Preference

According to `.github/copilot-instructions.md`, the project uses "Manusia Purba Mode" (direct, minimal, verb-first communication style). Keep explanations brief and code-focused.
