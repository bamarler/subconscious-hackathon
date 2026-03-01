import { useEffect, useState, useCallback, type DragEvent, type ChangeEvent } from 'react'
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

interface PipelineEvent {
  step: number
  step_name: string
  status: string
  data: Record<string, unknown> | null
  error: string | null
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const JOB_ID_KEY = 'comify_job_id'
const COMIC_RESULT_KEY = 'comify_last_comic'

const PIPELINE_STEPS = [
  'Parsing slideshow...',
  'Creating comic blueprint...',
  'Drawing panels...',
]

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [comic, setComic] = useState<ComicResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())
  const [panels, setPanels] = useState<ComicPanel[]>([])

  // Shared SSE streaming logic — works for both fresh start and reconnect
  const streamJob = useCallback(async (jobId: string) => {
    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/stream`)
      if (!res.ok) throw new Error('Failed to connect to job stream')

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const event: PipelineEvent = JSON.parse(line.slice(6))

          if (event.status === 'started') {
            setStep(event.step)
          }

          if (event.status === 'completed') {
            setCompletedSteps((prev) => new Set([...prev, event.step]))
          }

          if (event.status === 'error') {
            throw new Error(
              `Step ${event.step} (${event.step_name}) failed: ${event.error}`
            )
          }

          // Progressive panel rendering
          if (
            event.step === 3 &&
            event.status === 'progress' &&
            event.data?.image_url
          ) {
            const partial: ComicPanel = {
              panel_number: event.data.panel_number as number,
              setting: '',
              characters: [],
              dialogue: '',
              action: '',
              image_url: event.data.image_url as string,
              image_prompt: '',
            }
            setPanels((prev) => {
              // Avoid duplicates on reconnect replay
              if (prev.some((p) => p.panel_number === partial.panel_number)) return prev
              return [...prev, partial]
            })
          }

          // Final result
          if (event.step === 3 && event.status === 'completed' && event.data) {
            const result = event.data as unknown as ComicResult
            setComic(result)
            localStorage.setItem(COMIC_RESULT_KEY, JSON.stringify(result))
            localStorage.removeItem(JOB_ID_KEY)
          }
        }
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message : 'Connection lost. Refresh to reconnect.'
      )
    } finally {
      setLoading(false)
    }
  }, [])

  // On mount: check for active job or cached comic
  useEffect(() => {
    const savedJobId = localStorage.getItem(JOB_ID_KEY)
    if (savedJobId) {
      fetch(`${API_URL}/api/jobs/${savedJobId}`)
        .then((res) => {
          if (!res.ok) throw new Error('not found')
          return res.json()
        })
        .then((status) => {
          if (status.status === 'running' || status.status === 'pending' || status.status === 'completed') {
            streamJob(savedJobId)
          } else {
            localStorage.removeItem(JOB_ID_KEY)
          }
        })
        .catch(() => {
          localStorage.removeItem(JOB_ID_KEY)
        })
      return
    }

    // No active job — restore last comic from cache
    const savedComic = localStorage.getItem(COMIC_RESULT_KEY)
    if (savedComic) {
      try {
        setComic(JSON.parse(savedComic))
      } catch { /* ignore parse errors */ }
    }
  }, [streamJob])

  const handleDrag = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0])
  }

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setFile(e.target.files[0])
  }

  const convert = async () => {
    if (!file) return

    setLoading(true)
    setError('')
    setComic(null)
    setPanels([])
    setStep(0)
    setCompletedSteps(new Set())
    localStorage.removeItem(COMIC_RESULT_KEY)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/api/convert`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const { job_id } = await res.json()
      localStorage.setItem(JOB_ID_KEY, job_id)
      await streamJob(job_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Comify</h1>
        <p>Upload your lecture slides. Get a comic book.</p>
      </header>

      <div className="input-section">
        <div
          className={`drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".pdf,.pptx"
            onChange={handleFileInput}
            hidden
          />
          {file ? (
            <div className="file-info">
              <span className="file-name">{file.name}</span>
              <span className="file-size">
                ({(file.size / 1024 / 1024).toFixed(1)} MB)
              </span>
              <button
                className="remove-file"
                onClick={(e) => {
                  e.stopPropagation()
                  setFile(null)
                }}
              >
                x
              </button>
            </div>
          ) : (
            <div className="drop-prompt">
              <p>Drop your slideshow here or click to browse</p>
              <p className="drop-hint">Supports .pptx and .pdf</p>
            </div>
          )}
        </div>

        <button
          className="convert-btn"
          onClick={convert}
          disabled={loading || !file}
        >
          {loading ? 'Converting...' : 'Generate Comic'}
        </button>
      </div>

      {loading && (
        <div className="loading">
          <div className="pipeline-steps">
            {PIPELINE_STEPS.map((msg, i) => {
              const stepNum = i + 1
              const isDone = completedSteps.has(stepNum)
              const isActive = step === stepNum && !isDone
              return (
                <div
                  key={i}
                  className={`pipeline-step ${isDone ? 'done' : isActive ? 'active' : ''}`}
                >
                  <span className="step-dot" />
                  <span className="step-label">{msg}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Progressive panel preview during image generation */}
      {loading && panels.length > 0 && (
        <div className="panels-preview">
          {panels.map((p) => (
            <div key={p.panel_number} className="panel panel-arriving">
              <div className="panel-image">
                {p.image_url && (
                  <img src={p.image_url} alt={`Panel ${p.panel_number}`} />
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {comic && !loading && (
        <div className="comic-container">
          <h2 className="comic-title">{comic.title}</h2>
          <div className="panels-grid">
            {comic.panels.map((panel) => (
              <div key={panel.panel_number} className="panel">
                <div className="panel-image">
                  {panel.image_url ? (
                    <img
                      src={panel.image_url}
                      alt={`Panel ${panel.panel_number}`}
                    />
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

      <p className="powered-by">Powered by Subconscious AI + fal.ai</p>
    </div>
  )
}

export default App
