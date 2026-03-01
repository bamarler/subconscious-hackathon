# Dependencies

All tools needed to develop and run the Lecture-to-Comic converter.

## Python (3.13+)

The backend runtime.

**macOS:**
```bash
brew install python@3.13
```

**Windows:**
```powershell
choco install python --version=3.13
```

**Linux (Ubuntu/Debian):**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update && sudo apt install python3.13
```

## uv

Fast Python package manager. Manages the backend's virtualenv and dependencies.

**macOS:**
```bash
brew install uv
```

**Windows:**
```powershell
choco install uv
```

**Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify: `uv --version`

## Bun

JavaScript runtime and package manager. Runs the frontend dev server and builds.

**macOS:**
```bash
brew install oven-sh/bun/bun
```

**Windows:**
```powershell
choco install bun
```

**Linux:**
```bash
curl -fsSL https://bun.sh/install | bash
```

Verify: `bun --version`

## Make

Runs the project Makefile commands (`make up`, `make init`, etc.).

**macOS:**
```bash
brew install make
```

**Windows:**
```powershell
choco install make
```

**Linux:**
```bash
sudo apt install make
```

## API Keys

You need two API keys set in `backend/.env`:

| Key | Where to get it |
|-----|----------------|
| `SUBCONSCIOUS_API_KEY` | Sign up at [subconscious.dev](https://subconscious.dev), generate a key from the dashboard |
| `IDEOGRAM_API_KEY` | Sign up at [ideogram.ai](https://ideogram.ai), get a key from developer settings |

Run `make init-env` to create the `.env` file from the template, then fill in your keys.

## Quick Start

```bash
make init    # install all deps + create .env
make up      # start backend (port 8000) + frontend (port 5173)
```
