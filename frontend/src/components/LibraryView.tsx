import React, { useState, useRef } from 'react'
import type { DemoSummary } from '../types'

interface LibraryViewProps {
  demos: DemoSummary[]
  activeDemoId: number | null
  onSelectDemo: (demo: DemoSummary) => void
  onParsePath: (path: string) => Promise<void>
  onUploadDemo?: (file: File) => Promise<void>
  isLoading: boolean
  error: string | null
}

export const LibraryView: React.FC<LibraryViewProps> = ({
  demos,
  activeDemoId,
  onSelectDemo,
  onParsePath,
  onUploadDemo,
  isLoading,
  error,
}) => {
  const [inputPath, setInputPath] = useState('tests/integration/fixtures/test.dem')
  const [uploadingName, setUploadingName] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Custom demo signatures / user notes persisted in localStorage
  const [demoNotes, setDemoNotes] = useState<Record<number, string>>(() => {
    const notes: Record<number, string> = {}
    demos.forEach((d) => {
      const saved = localStorage.getItem(`dem_note_${d.id}`)
      if (saved) notes[d.id] = saved
    })
    return notes
  })
  const [editingDemoId, setEditingDemoId] = useState<number | null>(null)
  const [noteDraft, setNoteDraft] = useState<string>('')

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''
    setInputPath(file.name)
    if (onUploadDemo) {
      setUploadingName(file.name)
      try {
        await onUploadDemo(file)
      } finally {
        setUploadingName(null)
      }
    } else {
      const filePath = (file as any).path || file.name
      await onParsePath(filePath)
    }
  }

  const saveNote = (demoId: number) => {
    if (noteDraft.trim()) {
      localStorage.setItem(`dem_note_${demoId}`, noteDraft.trim())
      setDemoNotes((prev) => ({ ...prev, [demoId]: noteDraft.trim() }))
    } else {
      localStorage.removeItem(`dem_note_${demoId}`)
      setDemoNotes((prev) => {
        const next = { ...prev }
        delete next[demoId]
        return next
      })
    }
    setEditingDemoId(null)
  }

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
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node)) {
            setIsDragging(false)
          }
        }}
        onDrop={async (e) => {
          e.preventDefault()
          setIsDragging(false)
          const file = e.dataTransfer.files?.[0]
          if (!file) return
          if (!file.name.toLowerCase().endsWith('.dem')) {
            alert('Пожалуйста, выберите файл с расширением .dem')
            return
          }
          setInputPath(file.name)
          if (onUploadDemo) {
            setUploadingName(file.name)
            try {
              await onUploadDemo(file)
            } finally {
              setUploadingName(null)
            }
          } else {
            await onParsePath(file.name)
          }
        }}
        style={{
          backgroundColor: isDragging ? 'rgba(56, 189, 248, 0.08)' : 'var(--bg-surface)',
          border: isDragging ? '2px dashed #38bdf8' : '1px solid var(--border)',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '32px',
          transition: 'all 0.2s ease',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 4px 0' }}>
              Добавить CS2 демку (.dem) в библиотеку
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
              Выберите файл с компьютера или перетащите его прямо сюда (Drag & Drop). Демка парсится движком CS2 Source 2 и сохраняется в локальной базе.
            </p>
          </div>

          {/* Prominent Add Demo File Button */}
          <div>
            <input
              type="file"
              ref={fileInputRef}
              accept=".dem"
              style={{ display: 'none' }}
              onChange={handleFileSelect}
            />
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || !!uploadingName}
              style={{
                padding: '12px 24px',
                fontSize: '14px',
                fontWeight: 800,
                background: uploadingName
                  ? 'linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)'
                  : 'linear-gradient(135deg, #6366f1 0%, #38bdf8 100%)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                cursor: (isLoading || !!uploadingName) ? 'wait' : 'pointer',
                opacity: (isLoading || !!uploadingName) ? 0.85 : 1,
                boxShadow: '0 4px 20px rgba(99, 102, 241, 0.45)',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <span style={{ fontSize: '18px' }}>{uploadingName ? '⏳' : '📁'}</span>
              <span>{uploadingName ? `Загрузка и парсинг (${uploadingName})...` : 'Выбрать .dem с компьютера'}</span>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            type="text"
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            placeholder="Или введите локальный путь: C:\cs2\demos\match.dem"
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
          <button type="submit" className="btn btn-secondary" disabled={isLoading} style={{ padding: '10px 18px', fontWeight: 600 }}>
            {isLoading ? 'Анализ...' : 'Парсинг по пути'}
          </button>
        </form>

        {uploadingName && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              backgroundColor: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              borderRadius: '8px',
              color: '#38bdf8',
              fontSize: '13px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <span style={{ fontSize: '16px' }}>⏳</span>
            <span>Загрузка и полный анализ демки <strong>{uploadingName}</strong> движком CS2 Source 2... Это займет несколько секунд.</span>
          </div>
        )}

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
            <strong>Ошибка:</strong> {error}
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
                        marginBottom: '10px',
                        fontFamily: 'monospace',
                      }}
                    >
                      {demo.file_path}
                    </p>

                    {/* User custom demo signature/note */}
                    {editingDemoId === demo.id ? (
                      <div
                        style={{ display: 'flex', gap: '6px', marginBottom: '14px' }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input
                          type="text"
                          value={noteDraft}
                          onChange={(e) => setNoteDraft(e.target.value)}
                          placeholder="Например: FACEIT финал 16-14 против s1mple"
                          autoFocus
                          style={{
                            flex: 1,
                            backgroundColor: '#0f1219',
                            border: '1px solid #38bdf8',
                            borderRadius: '6px',
                            padding: '5px 8px',
                            fontSize: '11px',
                            color: '#f1f5f9',
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveNote(demo.id)
                            if (e.key === 'Escape') setEditingDemoId(null)
                          }}
                        />
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ padding: '4px 8px', fontSize: '11px' }}
                          onClick={() => saveNote(demo.id)}
                        >
                          ✓
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '11px' }}
                          onClick={() => setEditingDemoId(null)}
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <div
                        style={{
                          marginBottom: '14px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          backgroundColor: demoNotes[demo.id] ? 'rgba(56, 189, 248, 0.08)' : 'rgba(255, 255, 255, 0.03)',
                          border: `1px solid ${demoNotes[demo.id] ? 'rgba(56, 189, 248, 0.25)' : '#1e2433'}`,
                          padding: '5px 10px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                        onClick={(e) => {
                          e.stopPropagation()
                          setEditingDemoId(demo.id)
                          setNoteDraft(demoNotes[demo.id] || '')
                        }}
                        title="Нажмите чтобы подписать или изменить заметку к этой демке"
                      >
                        <span
                          style={{
                            fontSize: '11px',
                            color: demoNotes[demo.id] ? '#38bdf8' : '#64748b',
                            fontStyle: demoNotes[demo.id] ? 'normal' : 'italic',
                            fontWeight: demoNotes[demo.id] ? 600 : 400,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {demoNotes[demo.id] ? `📝 ${demoNotes[demo.id]}` : '+ Подписать демку / заметка'}
                        </span>
                        <span style={{ fontSize: '11px', color: '#94a3b8' }}>✏️</span>
                      </div>
                    )}

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

