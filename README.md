# Lecture-to-Comic (Comify)

Transform lecture slideshows into vibrant comic book panels using AI. Upload a PowerPoint or PDF, and watch as an intelligent pipeline extracts key concepts, creates characters, writes dialogue, generates images, and produces a complete 6-panel comic strip.

## 🎯 Features

- **File Upload**: Drag-and-drop support for .pptx and .pdf files
- **AI-Powered Pipeline**: 6-step intelligent processing pipeline:
  1. Extract key concepts and narrative arc
  2. Create characters with visual descriptions
  3. Write comic script with dialogue and action
  4. Generate optimized image prompts
  5. Produce high-quality comic panel images
- **Real-time Progress**: Stream pipeline steps to frontend as they complete
- **Progressive Rendering**: Panels appear as they're generated
- **Responsive UI**: Built with React + TypeScript for smooth interactions

## 📋 Project Structure

```
subconscious-hackathon/
├── backend/                 # Python FastAPI server
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration management
│   │   ├── main.py         # FastAPI app setup
│   │   ├── models.py       # Pydantic models
│   │   └── routes.py       # API endpoints
│   ├── pyproject.toml      # Python dependencies
│   └── main.py             # Entry point
├── frontend/               # React + TypeScript SPA
│   ├── src/
│   │   ├── App.tsx         # Main component
│   │   ├── App.css         # Styles
│   │   └── main.tsx        # React entry point
│   ├── package.json        # Node dependencies
│   ├── vite.config.ts      # Vite configuration
│   └── tsconfig.json       # TypeScript config
├── api/                    # Vercel serverless function
│   └── index.py
├── Makefile                # Development commands
├── requirements.txt        # Python dependencies
└── vercel.json            # Vercel deployment config
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**
- **Bun** (JavaScript runtime and package manager)
- **uv** (Python package manager)

See [DEPENDENCIES.md](DEPENDENCIES.md) for detailed installation instructions.

### Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd subconscious-hackathon
   ```

2. **Install dependencies** (all at once)
   ```bash
   make init
   ```

   Or manually:
   ```bash
   # Backend
   uv sync --project backend
   
   # Frontend
   bun install --cwd frontend
   ```

3. **Set up environment variables**
   
   Create `.env` or `.env.local` files:
   
   **Backend** (`.env`):
   ```
   SUBCONSCIOUS_API_KEY=your_key_here
   FAL_KEY=your_fal_key_here
   ```
   
   **Frontend** (`.env.local`):
   ```
   VITE_API_URL=http://localhost:8000
   ```

4. **Start development servers**
   ```bash
   make up
   ```

   Or separately:
   ```bash
   # Backend
   uv run --project backend --directory backend uvicorn app.main:app --reload --port 8000

   # Frontend (in another terminal)
   bun run --cwd frontend dev
   ```

   Frontend runs at `http://localhost:5173`
   Backend runs at `http://localhost:8000`

## 📚 Development Commands

```bash
make help           # Show all available commands
make check-deps     # Verify dependencies
make init           # Install all dependencies
make up             # Start both servers
make down           # Stop both servers
make test           # Run tests
make clean          # Clean build artifacts
```

## 🏗️ Architecture

### Backend (Python FastAPI)

- **Endpoints**:
  - `POST /api/convert` — Submit slideshow, stream pipeline events via SSE
  - `GET /health` — Health check

- **Pipeline Steps**:
  1. **Parse Slideshow** — Extract text from .pptx or .pdf
  2. **Concept Extraction** — Identify key ideas and narrative arc (Subconscious AI)
  3. **Character Mapping** — Define characters with visual descriptions (Subconscious AI)
  4. **Panel Script Writing** — Create 6-panel comic script (Subconscious AI)
  5. **Image Prompt Generation** — Optimize prompts for image model (Subconscious AI)
  6. **Image Generation** — Generate panel images (fal.ai Flux)

- **Technologies**:
  - **FastAPI** — Web framework
  - **Pydantic** — Data validation
  - **python-pptx** — PowerPoint parsing
  - **PyMuPDF** — PDF parsing
  - **Subconscious SDK** — LLM orchestration with structured outputs
  - **fal-client** — Image generation

### Frontend (React + TypeScript)

- **Features**:
  - Drag-and-drop file upload
  - Server-Sent Events (SSE) for real-time progress
  - Progressive panel rendering
  - Responsive design

- **Technologies**:
  - **React 19** — UI framework
  - **TypeScript** — Type safety
  - **Vite** — Build tool
  - **CSS** — Custom styling

## 🔌 API Reference

### POST /api/convert

**Request:**
```json
{
  "lecture_notes": "string or file content"
}
```

**Response (SSE Stream):**
```json
{
  "step": 1,
  "step_name": "Parsing slideshow",
  "status": "started|completed|progress|error",
  "data": { /* step-specific data */ },
  "error": null
}
```

**Status Values:**
- `started` — Step initialization
- `completed` — Step finished with result
- `progress` — Incremental progress (image generation)
- `error` — Step failed

## 🎨 UI/UX Highlights

- **Drag-and-drop input** with visual feedback
- **Loading animation** showing pipeline progress
- **Grid layout** for comic panels
- **Fallback placeholders** while images load
- **Error handling** with user-friendly messages

## 📦 Build & Deploy

### Build Frontend
```bash
bun run --cwd frontend build
```
Output: `frontend/dist/`

### Build Backend
Backend runs directly via uvicorn (no building needed)

### Deploy to Vercel
```bash
vercel --prod
```
Uses config from `vercel.json`

## 🔄 Environment Variables

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| `VITE_API_URL` | Backend URL (frontend) | `http://localhost:8000` | `https://api.example.com` |
| `SUBCONSCIOUS_API_KEY` | Subconscious AI key (backend) | (required) | `sk-...` |
| `FAL_KEY` | fal.ai API key (backend) | (required) | `key-...` |
| `PORT` | Backend port (backend) | `8000` | `8080` |

## 🛠️ Troubleshooting

**Port already in use?**
```bash
# Kill processes on ports 5173, 5174, 5175 (frontend dev ports)
Get-NetTCPConnection -LocalPort 5173,5174,5175 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Kill process on port 8000 (backend)
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

**Module not found errors?**
```bash
# Reinstall dependencies
make clean
make init
```

**Frontend not connecting to backend?**
- Check `.env.local` has correct `VITE_API_URL`
- Ensure backend is running on the correct port
- Check CORS is enabled in backend

## 📝 License

See [LICENSE](LICENSE) for details.

## 🙏 Credits

- **Subconscious AI** — LLM orchestration with structured outputs
- **Ideogram/fal.ai** — Image generation
- Built during a hackathon event

## 📚 Additional Resources

- [CLAUDE.md](CLAUDE.md) — AI development guidance
- [DEPENDENCIES.md](DEPENDENCIES.md) — Detailed dependency installation
- [Makefile](Makefile) — Available development commands
