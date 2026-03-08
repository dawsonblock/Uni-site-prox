import { useState, useEffect, useCallback, useRef } from 'react'
import { Server, Search, Play, Square, Save, RefreshCw, Send, Code, ChevronDown, ChevronUp, Clock, Zap, FileCode, Globe, Activity, CheckCircle2, XCircle, Info, Trash2 } from 'lucide-react'

const API_URL = 'http://localhost:8001/api'
const PROXY_URL = 'http://localhost:8000'

// ── Toast System ──
function ToastContainer({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          {t.type === 'success' && <CheckCircle2 size={16} />}
          {t.type === 'error' && <XCircle size={16} />}
          {t.type === 'info' && <Info size={16} />}
          {t.message}
        </div>
      ))}
    </div>
  )
}

function App() {
  const [specs, setSpecs] = useState([])
  const [activeSpec, setActiveSpec] = useState(null)
  const [editorContent, setEditorContent] = useState('')
  const [proxyRunning, setProxyRunning] = useState(false)
  const [toasts, setToasts] = useState([])

  // Discover
  const [discoverUrl, setDiscoverUrl] = useState('')
  const [discoverSite, setDiscoverSite] = useState('')
  const [isDiscovering, setIsDiscovering] = useState(false)

  // Test Console
  const [testEndpoint, setTestEndpoint] = useState('')
  const [testMethod, setTestMethod] = useState('GET')
  const [testResponse, setTestResponse] = useState('')
  const [responseMeta, setResponseMeta] = useState(null)
  const [isTesting, setIsTesting] = useState(false)

  // UI
  const [showInstructions, setShowInstructions] = useState(true)
  const [proxyUptime, setProxyUptime] = useState(null)
  const proxyStartRef = useRef(null)

  const toast = useCallback((message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  const fetchSpecs = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/specs`)
      const data = await res.json()
      setSpecs(data.specs || [])
      if (data.specs.length > 0 && !activeSpec) {
        selectSpec(data.specs[0])
      }
    } catch (_) {
      // silently retry
    }
  }, [activeSpec])

  const fetchProxyStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/proxy/status`)
      const data = await res.json()
      const wasRunning = proxyRunning
      setProxyRunning(data.running)
      if (data.running && !wasRunning) {
        proxyStartRef.current = Date.now()
      } else if (!data.running) {
        proxyStartRef.current = null
        setProxyUptime(null)
      }
    } catch (_) { }
  }, [proxyRunning])

  useEffect(() => {
    fetchSpecs()
    fetchProxyStatus()
    const statusInterval = setInterval(fetchProxyStatus, 2000)
    const uptimeInterval = setInterval(() => {
      if (proxyStartRef.current) {
        setProxyUptime(Math.floor((Date.now() - proxyStartRef.current) / 1000))
      }
    }, 1000)
    return () => {
      clearInterval(statusInterval)
      clearInterval(uptimeInterval)
    }
  }, [fetchSpecs, fetchProxyStatus])

  const selectSpec = (spec) => {
    setActiveSpec(spec)
    setEditorContent(spec.content)
  }

  const handleDiscover = async (e) => {
    e.preventDefault()
    if (!discoverUrl || !discoverSite) return
    setIsDiscovering(true)
    toast('Starting API discovery... This may take a moment.', 'info')
    try {
      const res = await fetch(`${API_URL}/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: discoverUrl, site_name: discoverSite })
      })
      if (res.ok) {
        toast(`Successfully discovered APIs for "${discoverSite}"!`, 'success')
        setDiscoverUrl('')
        setDiscoverSite('')
        await fetchSpecs()
      } else {
        const err = await res.json().catch(() => ({}))
        toast(err.detail || 'Discovery failed. Check the URL and try again.', 'error')
      }
    } catch (_) {
      toast('Network error during discovery.', 'error')
    } finally {
      setIsDiscovering(false)
    }
  }

  const saveSpec = async () => {
    if (!activeSpec) return
    try {
      const res = await fetch(`${API_URL}/specs/${activeSpec.filename}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editorContent })
      })
      if (res.ok) {
        toast('Specification saved successfully!', 'success')
        fetchSpecs()
      } else {
        toast('Failed to save — check your YAML syntax.', 'error')
      }
    } catch (_) {
      toast('Network error while saving.', 'error')
    }
  }

  const deleteSpec = async (filename) => {
    try {
      const res = await fetch(`${API_URL}/specs/${filename}`, { method: 'DELETE' })
      if (res.ok) {
        toast(`Deleted ${filename}`, 'success')
        if (activeSpec?.filename === filename) {
          setActiveSpec(null)
          setEditorContent('')
        }
        fetchSpecs()
      } else {
        toast('Failed to delete spec.', 'error')
      }
    } catch (_) {
      toast('Network error.', 'error')
    }
  }

  const toggleProxy = async () => {
    const endpoint = proxyRunning ? '/proxy/stop' : '/proxy/start'
    try {
      await fetch(`${API_URL}${endpoint}`, { method: 'POST' })
      toast(proxyRunning ? 'Proxy server stopped.' : 'Proxy server starting...', proxyRunning ? 'info' : 'success')
      setTimeout(fetchProxyStatus, 500)
    } catch (_) {
      toast('Error toggling proxy server.', 'error')
    }
  }

  const testProxy = async (e) => {
    e.preventDefault()
    if (!testEndpoint) {
      toast('Enter an endpoint path first.', 'info')
      return
    }
    if (!proxyRunning) {
      toast('Start the proxy server first!', 'error')
      return
    }
    setIsTesting(true)
    setTestResponse('')
    setResponseMeta(null)
    const safeEndpoint = testEndpoint.startsWith('/') ? testEndpoint : '/' + testEndpoint
    const startTime = performance.now()
    try {
      const res = await fetch(`${PROXY_URL}${safeEndpoint}`, { method: testMethod })
      const elapsed = Math.round(performance.now() - startTime)
      const ct = res.headers.get('content-type')
      let body
      if (ct && ct.includes('application/json')) {
        const data = await res.json()
        body = JSON.stringify(data, null, 2)
      } else {
        body = await res.text()
      }
      setResponseMeta({
        status: res.status,
        statusText: res.statusText,
        time: elapsed,
        size: new Blob([body]).size,
      })
      setTestResponse(body)
    } catch (err) {
      setTestResponse(`Error: ${err.message}`)
      setResponseMeta({ status: 0, statusText: 'Network Error', time: 0, size: 0 })
    } finally {
      setIsTesting(false)
    }
  }

  const formatUptime = (s) => {
    if (s == null) return '—'
    const m = Math.floor(s / 60)
    const secs = s % 60
    return m > 0 ? `${m}m ${secs}s` : `${secs}s`
  }

  const formatBytes = (b) => b > 1024 ? `${(b / 1024).toFixed(1)} KB` : `${b} B`

  const getMethodColor = (m) => {
    const map = { GET: 'method-get', POST: 'method-post', PUT: 'method-put', DELETE: 'method-delete', PATCH: 'method-patch' }
    return map[m] || 'method-get'
  }

  const opCount = (spec) => spec.operations ? Object.keys(spec.operations).length : 0

  return (
    <div className="dashboard-layout">
      <ToastContainer toasts={toasts} />

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div>
          <h1 className="gradient-text" style={{ fontSize: '28px', marginBottom: '4px' }}>USP Dashboard</h1>
          <p style={{ color: 'var(--text-tertiary)', fontSize: '13px' }}>Universal Site Proxy Control Center</p>
        </div>

        {/* Proxy Controls */}
        <div className="glass-panel" style={{ padding: '18px' }}>
          <div className="flex-row justify-between" style={{ marginBottom: '12px' }}>
            <h3 className="flex-row gap-2"><Server size={16} /> Proxy Server</h3>
            <div className={`status-dot ${proxyRunning ? 'active' : 'inactive'}`} />
          </div>

          {proxyRunning ? (
            <div className="status-bar online" style={{ marginBottom: '12px' }}>
              <Activity size={14} />
              <span>Running on {PROXY_URL}</span>
              <span style={{ marginLeft: 'auto', opacity: 0.7 }}>{formatUptime(proxyUptime)}</span>
            </div>
          ) : (
            <div className="status-bar offline" style={{ marginBottom: '12px' }}>
              <span>Server offline</span>
            </div>
          )}

          <button className={proxyRunning ? 'btn-danger w-full' : 'btn-primary w-full'} onClick={toggleProxy}>
            {proxyRunning ? <><Square size={15} /> Stop Server</> : <><Play size={15} fill="currentColor" /> Start Server</>}
          </button>
        </div>

        {/* Instructions (Collapsible) */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div className="collapsible-header" onClick={() => setShowInstructions(!showInstructions)}>
            <h3 style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Quick Start Guide</h3>
            {showInstructions ? <ChevronUp size={14} color="var(--text-tertiary)" /> : <ChevronDown size={14} color="var(--text-tertiary)" />}
          </div>
          {showInstructions && (
            <ol style={{ fontSize: '12px', color: 'var(--text-tertiary)', paddingLeft: '16px', marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px', lineHeight: 1.5 }}>
              <li>Enter a target URL and alias in <strong style={{ color: 'var(--text-secondary)' }}>Discovery Engine</strong></li>
              <li>Wait for the headless browser to intercept API calls</li>
              <li>Review your new spec and edit the YAML if needed</li>
              <li>Click <strong style={{ color: 'var(--text-secondary)' }}>Start Server</strong> to launch the proxy</li>
              <li>Click any endpoint pill to auto-fill the <strong style={{ color: 'var(--text-secondary)' }}>Test Console</strong></li>
            </ol>
          )}
        </div>

        {/* Spec List */}
        <div className="glass-panel" style={{ padding: '18px', flex: 1, overflowY: 'auto', minHeight: 0 }}>
          <div className="flex-row justify-between" style={{ marginBottom: '14px' }}>
            <h3 className="flex-row gap-2"><FileCode size={16} /> Specifications</h3>
            <button className="btn-secondary" onClick={fetchSpecs} style={{ padding: '5px 8px' }} title="Refresh">
              <RefreshCw size={13} />
            </button>
          </div>

          <div className="flex-col gap-2">
            {specs.length === 0 ? (
              <div className="empty-state">
                <Globe size={28} strokeWidth={1.5} />
                <span>No specs yet</span>
                <span style={{ fontSize: '11px' }}>Run Discovery to get started</span>
              </div>
            ) : specs.map(spec => (
              <div
                key={spec.filename}
                className={`spec-item ${activeSpec?.filename === spec.filename ? 'active' : ''}`}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              >
                <div onClick={() => selectSpec(spec)} style={{ flex: 1, cursor: 'pointer' }}>
                  <div className="flex-row gap-2">
                    <span className="spec-name">{spec.site}</span>
                    {opCount(spec) > 0 && <span className="badge badge-accent">{opCount(spec)} {opCount(spec) === 1 ? 'endpoint' : 'endpoints'}</span>}
                  </div>
                  <div className="spec-url">{spec.base_url}</div>
                </div>
                <button
                  className="btn-secondary"
                  style={{ padding: '4px', border: 'none', background: 'transparent', opacity: 0.3 }}
                  onClick={(e) => { e.stopPropagation(); deleteSpec(spec.filename) }}
                  title="Delete spec"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="main-content">

        {/* Discovery */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <h2 className="flex-row gap-2" style={{ marginBottom: '16px' }}>
            <Search size={20} style={{ color: 'var(--accent-color)' }} /> Discovery Engine
          </h2>
          <form onSubmit={handleDiscover} className="flex-row gap-3">
            <input
              className="input-glass"
              placeholder="https://example.com/api"
              value={discoverUrl}
              onChange={e => setDiscoverUrl(e.target.value)}
              required
              disabled={isDiscovering}
            />
            <input
              className="input-glass"
              placeholder="site_alias"
              style={{ maxWidth: '180px' }}
              value={discoverSite}
              onChange={e => setDiscoverSite(e.target.value)}
              required
              disabled={isDiscovering}
            />
            <button type="submit" className="btn-primary" disabled={isDiscovering} style={{ minWidth: '140px' }}>
              {isDiscovering ? <><RefreshCw size={15} className="animate-spin" /> Scanning...</> : 'Run Discovery'}
            </button>
          </form>
          {isDiscovering && (
            <div style={{ marginTop: '14px' }}>
              <div className="progress-bar"><div className="progress-bar-fill" style={{ width: '100%' }} /></div>
              <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '8px' }}>
                Launching headless browser, intercepting network traffic...
              </p>
            </div>
          )}
          {!isDiscovering && (
            <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '10px' }}>
              Launches a headless browser to intercept hidden API endpoints and auto-generate a local spec.
            </p>
          )}
        </div>

        {/* Spec Editor + Endpoints */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <div className="flex-row justify-between" style={{ marginBottom: '16px' }}>
            <h2 className="flex-row gap-2">
              <Code size={20} style={{ color: 'var(--accent-secondary)' }} />
              {activeSpec ? activeSpec.site : 'Specification Editor'}
              {activeSpec && <span className="badge badge-accent" style={{ marginLeft: '4px' }}>.yaml</span>}
            </h2>
            {activeSpec && (
              <button className="btn-secondary" onClick={saveSpec}>
                <Save size={14} /> Save
              </button>
            )}
          </div>

          {/* Endpoint Pills */}
          {activeSpec?.operations && Object.keys(activeSpec.operations).length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 500 }}>
                Endpoints — click to test
              </p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {Object.entries(activeSpec.operations).map(([opName, op]) => (
                  <button
                    key={opName}
                    className="endpoint-pill"
                    onClick={() => {
                      setTestMethod(op.method || 'GET')
                      setTestEndpoint(`/${activeSpec.site}${op.path}`)
                      toast(`Loaded ${op.method || 'GET'} ${op.path}`, 'info')
                    }}
                    title={op.description || opName}
                  >
                    <span className={`method-label ${getMethodColor(op.method || 'GET')}`}>
                      {op.method || 'GET'}
                    </span>
                    <span style={{ color: 'var(--text-secondary)' }}>{op.path}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {activeSpec ? (
            <textarea
              className="code-editor"
              value={editorContent}
              onChange={e => setEditorContent(e.target.value)}
              spellCheck={false}
            />
          ) : (
            <div className="empty-state" style={{ height: '300px' }}>
              <FileCode size={36} strokeWidth={1.2} />
              <span>Select a spec from the sidebar</span>
              <span style={{ fontSize: '11px' }}>or run Discovery to create one</span>
            </div>
          )}
        </div>

        {/* Test Console */}
        <div className="glass-panel" style={{ padding: '22px' }}>
          <h2 className="flex-row gap-2" style={{ marginBottom: '16px' }}>
            <Send size={18} style={{ color: 'var(--success-color)' }} /> Test Console
          </h2>

          <form onSubmit={testProxy} className="flex-row gap-2" style={{ marginBottom: '14px' }}>
            <div style={{ display: 'flex', flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid var(--panel-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
              <select
                className="select-glass"
                value={testMethod}
                onChange={e => setTestMethod(e.target.value)}
                style={{ borderRight: '1px solid var(--panel-border)' }}
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="PATCH">PATCH</option>
              </select>
              <input
                className="input-glass"
                style={{ border: 'none', borderRadius: 0, background: 'transparent' }}
                placeholder="/site_alias/endpoint"
                value={testEndpoint}
                onChange={e => setTestEndpoint(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={isTesting} style={{ minWidth: '100px' }}>
              {isTesting ? <RefreshCw size={15} className="animate-spin" /> : <><Zap size={15} /> Send</>}
            </button>
          </form>

          {/* Response Meta */}
          {responseMeta && (
            <div className="response-meta" style={{ marginBottom: '12px' }}>
              <div className="meta-item">
                <span style={{ color: responseMeta.status < 300 ? 'var(--success-color)' : responseMeta.status < 500 ? 'var(--warning-color)' : 'var(--danger-color)' }}>
                  ● {responseMeta.status}
                </span>
                <span className="meta-value">{responseMeta.statusText}</span>
              </div>
              <div className="meta-item">
                <Clock size={12} />
                <span className="meta-value">{responseMeta.time}ms</span>
              </div>
              <div className="meta-item" style={{ marginLeft: 'auto' }}>
                <span className="meta-value">{formatBytes(responseMeta.size)}</span>
              </div>
            </div>
          )}

          <div className="terminal-output" style={{ height: '320px' }}>
            <pre style={{ margin: 0, fontFamily: 'inherit' }}>
              {testResponse || '// Send a request to see the response here'}
            </pre>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
