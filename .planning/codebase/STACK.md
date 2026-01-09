# Technology Stack

**Analysis Date:** 2026-01-09

## Languages

**Primary:**
- Python 3.12.1 - All application code (`app.py`, `src/*.py`)

**Secondary:**
- None (pure Python codebase)

## Runtime

**Environment:**
- Python 3.10+ required
- Virtual environment: `venv/`
- macOS SSL fix via `certifi`

**Package Manager:**
- pip
- Lockfile: None (uses `requirements.txt` only)

## Frameworks

**Core:**
- Streamlit >=1.28.0 - Web UI framework (`app.py`)

**Testing:**
- None (manual tests in `if __name__ == "__main__":` blocks)

**Build/Dev:**
- None (pure Python, no build step)

## Key Dependencies

**Critical:**
- `kloppy>=3.18.0` - Football tracking data loading (PFF/Metrica formats)
- `streamlit>=1.28.0` - Web UI framework
- `matplotlib>=3.7.0` - Pitch/player visualization

**Infrastructure:**
- `numpy>=1.24.0` - Array operations, calculations
- `scipy>=1.10.0` - ConvexHull for shape analysis
- `certifi` - SSL certificate management (macOS fix)

## Configuration

**Environment:**
- No environment variables required
- SSL_CERT_FILE set dynamically via `certifi.where()`
- `.env` in .gitignore but not used

**Build:**
- `.streamlit/config.toml` - Server settings, dark theme
- `Procfile` - Railway deployment command

## Platform Requirements

**Development:**
- macOS/Linux/Windows (any platform with Python)
- No Docker required
- No external dependencies (data bundled in repo)

**Production:**
- Railway deployment target
- Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
- Memory: 512 MB free tier

---

*Stack analysis: 2026-01-09*
*Update after major dependency changes*
