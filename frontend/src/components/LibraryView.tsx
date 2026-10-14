import React, { useState } from 'react'
import type { DemoSummary } from '../types'

interface LibraryViewProps {
  demos: DemoSummary[]
  activeDemoId: number | null
  onSelectDemo: (demo: DemoSummary) => void
  onParsePath: (path: string) => Promise<void>
  isLoading: boolean
  error: string | null
}

export const LibraryView: React.FC<LibraryViewProps> = ({
  demos,
  activeDemoId,
  onSelectDemo,
  onParsePath,
  isLoading,
  error,
}) => {
  const [inputPath, setInputPath] = useState('tests/integration/fixtures/test.dem')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputPath.trim()) {
      onParsePath(inputPath.trim())
    }
  }

  const formatDuration = (secs: number | null) => {
    if (!secs) return '-'
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  return (
    <div className="container">
      {/* File Ingestion Card */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '32px',
        }}
      >
        <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '8px' }}>
          Analyze CS2 Demo File (.dem)
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Provide the local path to a CS2 demo. Ingestion validates the header and checks the SQLite cache. If already analyzed with the current parser schema, cached results load instantly.
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            type="text"
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            placeholder="C:\path\to\match.dem or relative path"
            disabled={isLoading}
            style={{
              flex: 1,
              backgroundColor: 'var(--bg-app)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '10px 14px',
              color: 'var(--text-main)',
              fontSize: '13px',
              fontFamily: 'inherit',
            }}
          />
          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            {isLoading ? 'Analyzing...' : 'Parse & Open Demo'}
          </button>
        </form>

        {error && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              color: '#f87171',
              fontSize: '13px',
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}
      </div>

      {/* Matches Grid */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
            Saved Matches ({demos.length})
          </h3>
        </div>

        {demos.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '48px 24px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px dashed var(--border)',
              borderRadius: '12px',
              color: 'var(--text-muted)',
            }}
          >
            No matches analyzed yet. Enter a demo path above to parse your first CS2 demo.
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: '16px',
            }}
          >
            {demos.map((demo) => {
              const isSelected = demo.id === activeDemoId
              return (
                <div
                  key={demo.id}
                  style={{
                    backgroundColor: isSelected ? 'var(--bg-card-selected)' : 'var(--bg-surface)',
                    border: `1px solid ${isSelected ? 'var(--accent-gold)' : 'var(--border)'}`,
                    borderRadius: '10px',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span
                        style={{
                          fontSize: '16px',
                          fontWeight: 700,
                          color: 'var(--accent-gold)',
                        }}
                      >
                        {demo.map_name || 'Unknown Map'}
                      </span>
                      <span
                        className="num"
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-faint)',
                          backgroundColor: 'var(--bg-app)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                        }}
                      >
                        {demo.tickrate} tick
                      </span>
                    </div>

                    <p
                      style={{
                        fontSize: '11px',
                        color: 'var(--text-muted)',
                        wordBreak: 'break-all',
                        marginBottom: '16px',
                        fontFamily: 'monospace',
                      }}
                    >
                      {demo.file_path}
                    </p>

                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '8px',
                        textAlign: 'center',
                        backgroundColor: 'var(--bg-app)',
                        padding: '10px',
                        borderRadius: '6px',
                        marginBottom: '16px',
                      }}
                    >
                      <div>
                        <div className="num" style={{ fontSize: '15px', fontWeight: 700 }}>
                          {demo.rounds_count}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>Rounds</div>
                      </div>
                      <div>
                        <div className="num" style={{ fontSize: '15px', fontWeight: 700 }}>
                          {demo.players_count}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>Players</div>
                      </div>
                      <div>
                        <div
                          className="num"
                          style={{
                            fontSize: '15px',
                            fontWeight: 700,
                            color: demo.highlights_count > 0 ? 'var(--accent-cyan)' : 'inherit',
                          }}
                        >
                          {demo.highlights_count}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>Highlights</div>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
                      Duration: {formatDuration(demo.duration_seconds)}
                    </span>
                    <button
                      className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => onSelectDemo(demo)}
                      style={{ padding: '6px 14px', fontSize: '12px' }}
                    >
                      {isSelected ? 'Active Match ✓' : 'Open Match →'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

