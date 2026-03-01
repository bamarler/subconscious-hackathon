import { useState } from 'react'
import './App.css'

interface ComicPanel {
  panel_number: number
  setting: string
  characters: string[]
  dialogue: string
  action: string
  image_url: string | null
  image_prompt: string
}

interface ComicResult {
  title: string
  panels: ComicPanel[]
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const LOADING_MESSAGES = [
  'Extracting key concepts...',
  'Casting characters...',
  'Writing the script...',
  'Generating image prompts...',
  'Drawing panels...',
]

function App() {
  const [lectureNotes, setLectureNotes] = useState('')
  const [comic, setComic] = useState<ComicResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [loadingMsg, setLoadingMsg] = useState('')
  const [step, setStep] = useState(0)

  const convert = async () => {
    if (lectureNotes.length < 20) return

    setLoading(true)
    setError('')
    setComic(null)
    setStep(0)

    let msgIdx = 0
    setLoadingMsg(LOADING_MESSAGES[0])
    const interval = setInterval(() => {
      msgIdx = Math.min(msgIdx + 1, LOADING_MESSAGES.length - 1)
      setLoadingMsg(LOADING_MESSAGES[msgIdx])
      setStep(msgIdx)
    }, 8000)

    try {
      const res = await fetch(`${API_URL}/api/convert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lecture_notes: lectureNotes }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      setComic(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      clearInterval(interval)
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Lecture to Comic</h1>
        <p>Paste your lecture notes. Get a comic book.</p>
      </header>

      <div className="input-section">
        <textarea
          className="notes-input"
          placeholder="Paste your lecture notes, slide text, or any educational content here..."
          value={lectureNotes}
          onChange={(e) => setLectureNotes(e.target.value)}
          disabled={loading}
        />
        <button
          className="convert-btn"
          onClick={convert}
          disabled={loading || lectureNotes.length < 20}
        >
          {loading ? 'Converting...' : 'Generate Comic'}
        </button>
      </div>

      {loading && (
        <div className="loading">
          <div className="pipeline-steps">
            {LOADING_MESSAGES.map((msg, i) => (
              <div
                key={i}
                className={`pipeline-step ${i < step ? 'done' : i === step ? 'active' : ''}`}
              >
                <span className="step-dot" />
                <span className="step-label">{msg}</span>
              </div>
            ))}
          </div>
          <p className="loading-text">{loadingMsg}</p>
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {comic && (
        <div className="comic-container">
          <h2 className="comic-title">{comic.title}</h2>
          <div className="panels-grid">
            {comic.panels.map((panel) => (
              <div key={panel.panel_number} className="panel">
                <div className="panel-image">
                  {panel.image_url ? (
                    <img src={panel.image_url} alt={`Panel ${panel.panel_number}`} />
                  ) : (
                    <div className="panel-placeholder">
                      <span className="panel-number">#{panel.panel_number}</span>
                    </div>
                  )}
                </div>
                <div className="panel-caption">
                  <p className="panel-setting">{panel.setting}</p>
                  <p className="panel-dialogue">"{panel.dialogue}"</p>
                  <p className="panel-action">{panel.action}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="powered-by">Powered by Subconscious AI + Ideogram</p>
    </div>
  )
}

export default App
