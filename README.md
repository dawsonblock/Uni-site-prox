<div align="center">

# ⚡ Universal Site Proxy

**Turn any website into a local REST API in seconds.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-a78bfa?style=for-the-badge)](LICENSE)

<br />

*Automated API discovery via headless browser interception • YAML-based spec management • Local proxy server • Web dashboard*

---

</div>

## 🧐 What Is This?

Universal Site Proxy (USP) is a tool that discovers hidden API endpoints on any website by launching a headless browser, intercepting all network traffic, and generating a clean YAML specification. It then spins up a local FastAPI proxy server that exposes those same endpoints on `localhost`, letting you interact with any website's backend as if it were your own API.

```
Website → Headless Browser → API Discovery → YAML Spec → Local Proxy → Your Code
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Auto-Discovery** | Headless Playwright browser intercepts all API calls from any website |
| 📝 **YAML Specs** | Clean, editable specification files for each discovered site |
| 🖥️ **Local Proxy** | FastAPI server mirrors discovered endpoints on `localhost:8000` |
| 🎨 **Web Dashboard** | Beautiful glassmorphic control center with real-time management |
| ⚡ **Test Console** | Built-in API tester with response metadata (status, latency, size) |
| 🔔 **Toast Notifications** | Elegant, non-intrusive feedback for all operations |
| 🧩 **Endpoint Pills** | Click-to-test buttons auto-generated from your specs |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for dashboard)

### Installation

```bash
# Clone the repository
git clone https://github.com/dawsonblock/Uni-site-prox.git
cd Uni-site-prox

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### CLI Usage

```bash
# Discover APIs from any website
usp discover https://dummyjson.com/products --site my_api

# Start the local proxy server
usp serve

# Your API is now available at http://localhost:8000/my_api/...
curl http://localhost:8000/my_api/get_products
```

### Dashboard (Recommended)

The dashboard gives you a visual interface for everything:

```bash
# Install dashboard dependencies
cd dashboard/frontend && npm install && npm run build && cd ..
pip install uvicorn psutil pyyaml

# Start the dashboard
cd dashboard && uvicorn backend:app --host 127.0.0.1 --port 8001
```

Then open **<http://127.0.0.1:8001>** in your browser.

## 🎛️ Dashboard Guide

The dashboard provides a complete workflow without touching the command line:

1. **Enter a URL** — Paste any website URL into the Discovery Engine
2. **Run Discovery** — A headless browser intercepts all hidden API calls
3. **Review the Spec** — Browse the auto-generated YAML and edit if needed
4. **Start the Proxy** — One click to launch your local API server
5. **Test Endpoints** — Click any endpoint pill to instantly query it

### Dashboard Features

- **Proxy Server Controls** — Start/stop with live uptime counter
- **Interactive Endpoint Pills** — Color-coded by HTTP method (GET/POST/PUT/DELETE)
- **Response Metadata** — Status code, latency (ms), and response size
- **YAML Editor** — Inline editing with save validation
- **Spec Management** — Endpoint count badges, delete buttons, refresh
- **Toast Notifications** — No more browser alert popups
- **Collapsible Guide** — Quick start instructions built right in

## 📁 Project Structure

```
universal_site_proxy_build/
├── universal_site_proxy/       # Core Python package
│   ├── browser.py              # Playwright-based API discovery
│   ├── cli.py                  # CLI entry point (usp command)
│   ├── server.py               # FastAPI proxy server
│   ├── spec_loader.py          # YAML spec loading & validation
│   ├── models.py               # Pydantic data models
│   └── registry.py             # Runtime execution registry
├── dashboard/
│   ├── backend.py              # FastAPI dashboard controller
│   ├── static/                 # Built frontend assets
│   └── frontend/               # React + Vite source
│       ├── src/App.jsx         # Main React application
│       └── src/index.css       # Premium design system
├── api_maps/                   # Generated YAML specifications
├── tests/                      # Test suite
├── pyproject.toml              # Python package config
└── README.md
```

## 🔧 Configuration

Each discovered site produces a YAML spec in `api_maps/`:

```yaml
site: my_api
base_url: https://example.com
auth: null
operations:
  get_products:
    method: GET
    path: /products
    execution_mode: http
    cache_ttl_sec: 60
    description: Auto-discovered GET /products
    forward_body: false
    allowed_headers: []
    allowed_query_params: null
```

You can manually edit these files to:

- Add authentication headers
- Adjust cache TTL
- Filter allowed query params
- Change execution modes

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Core Engine** | Python, Playwright, FastAPI |
| **Proxy Server** | FastAPI + Uvicorn |
| **Dashboard Backend** | FastAPI (port 8001) |
| **Dashboard Frontend** | React + Vite |
| **Design** | Glassmorphism, JetBrains Mono, Outfit |
| **Icons** | Lucide React |

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
<sub>Built with ⚡ by <a href="https://github.com/dawsonblock">dawsonblock</a></sub>
</div>
