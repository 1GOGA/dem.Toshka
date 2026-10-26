import React, { useState, useRef } from 'react'
import type { DemoSummary } from '../types'
import { FolderIcon, LoaderIcon, CheckIcon, FilmIcon } from './Icons'
import { useTranslation } from '../i18n'

interface LibraryViewProps {
  demos: DemoSummary[]
  activeDemoId: number | null
  activeDemo?: DemoSummary | null
  onSelectDemo: (demo: DemoSummary) => void
  onParsePath: (path: string) => Promise<void>
  onUploadDemo?: (file: File) => Promise<void>
  isLoading: boolean
  error: string | null
}

export const LibraryView: React.FC<LibraryViewProps> = ({
  demos,
  activeDemoId,
  activeDemo,
  onSelectDemo,
  onParsePath,
  onUploadDemo,
  isLoading,
  error,
}) => {
  const { t, lang } = useTranslation()
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
            alert(t('library.invalidExtension'))
            return
          }
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
              {t('library.dragDropTitle')}
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
              {t('library.dragDropSubtitle')}
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
              {uploadingName ? <LoaderIcon size={18} color="#ffffff" /> : <FolderIcon size={18} color="#ffffff" />}
              <span>{uploadingName ? `${t('library.uploading')} (${uploadingName})...` : t('library.selectFileBtn')}</span>
            </button>
          </div>
        </div>

        {(uploadingName || isLoading) && (
          <div
            style={{
              marginTop: '20px',
              padding: '20px 24px',
              backgroundColor: 'rgba(10, 16, 28, 0.95)',
              border: '1px solid rgba(56, 189, 248, 0.55)',
              borderRadius: '10px',
              boxShadow: '0 0 35px rgba(56, 189, 248, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Top Row: Rotating Spinner & Status Title */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  border: '3px solid rgba(56, 189, 248, 0.2)',
                  borderTopColor: '#38bdf8',
                  animation: 'spin 0.8s linear infinite',
                }} />
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>{lang === 'ru' ? 'АНАЛИЗ И ОБРАБОТКА ДЕМКИ CS2' : 'ANALYZING & PROCESSING CS2 DEMO'}</span>
                    {uploadingName && (
                      <span style={{ fontSize: '12px', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.15)', padding: '2px 8px', borderRadius: '4px' }}>
                        {uploadingName}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                    {lang === 'ru' ? 'Считывание бинарных тиков CS2, поиск фрагов, клатчей и построение 2D радара...' : 'Parsing binary CS2 ticks, detecting kills, clutches, and building 2D radar...'}
                  </div>
                </div>
              </div>
              <div style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: 700, color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', padding: '4px 10px', borderRadius: '6px' }}>
                SOURCE 2 PARSER ⚡
              </div>
            </div>

            {/* Glowing Shimmer Progress Bar */}
            <div style={{ width: '100%', height: '6px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden', position: 'relative' }}>
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(90deg, #0284c7 0%, #38bdf8 50%, #818cf8 100%)',
                  borderRadius: '3px',
                  animation: 'pulse 1.8s ease-in-out infinite',
                }}
              />
            </div>

            {/* Live Pipeline Steps */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', paddingTop: '4px' }}>
              <div style={{ fontSize: '10.5px', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: '#22c55e', fontWeight: 800 }}>✓</span>
                <span>{lang === 'ru' ? 'Загрузка файла .dem' : 'Uploading .dem file'}</span>
              </div>
              <div style={{ fontSize: '10.5px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700 }}>
                <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#38bdf8', boxShadow: '0 0 8px #38bdf8' }} />
                <span>{lang === 'ru' ? 'Парсинг тиков и убийств' : 'Parsing ticks & kills'}</span>
              </div>
              <div style={{ fontSize: '10.5px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>○</span>
                <span>{lang === 'ru' ? 'Детекция хайлайтов' : 'Detecting highlights'}</span>
              </div>
            </div>
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
            <strong>{lang === 'ru' ? 'Ошибка:' : 'Error:'}</strong> {error}
          </div>
        )}
      </div>

      {/* Matches Grid */}
      <div>
        {activeDemo && (
          <div
            style={{
              marginBottom: '20px',
              padding: '16px 20px',
              backgroundColor: '#0f172a',
              border: '1px solid #38bdf8',
              borderRadius: '12px',
              boxShadow: '0 0 24px rgba(56, 189, 248, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '14px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 16px rgba(56, 189, 248, 0.35)',
                }}
              >
                <FilmIcon size={20} color="#040711" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {lang === 'ru' ? 'АКТИВНЫЙ МАТЧ В РАБОТЕ' : 'ACTIVE MATCH IN STUDIO'}
                  </span>
                  <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#22c55e', boxShadow: '0 0 8px #22c55e' }} />
                </div>
                <div style={{ fontSize: '16px', fontWeight: 800, color: '#ffffff' }}>
                  {(activeDemo.map_name || 'CS2').replace('de_', '').toUpperCase()} — {activeDemo.rounds_count} {lang === 'ru' ? 'раундов' : 'rounds'} ({activeDemo.highlights_count} {lang === 'ru' ? 'хайлайтов' : 'highlights'})
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onSelectDemo(activeDemo)}
              style={{
                padding: '10px 22px',
                background: 'linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)',
                color: '#040711',
                fontWeight: 800,
                fontSize: '13px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 0 20px rgba(56, 189, 248, 0.4)',
                transition: 'transform 0.15s ease',
              }}
            >
              <span>{lang === 'ru' ? '⚡ Продолжить работу в Студии' : '⚡ Continue to Highlights Studio'}</span>
              <span>➔</span>
            </button>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
            {t('library.parsedDemos')} ({demos.length})
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
            {t('library.noDemos')}. {t('library.noDemosSubtitle')}
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
                  className={`card-interactive ${isSelected ? 'glow-ct' : ''}`}
                  onClick={() => onSelectDemo(demo)}
                  style={{
                    backgroundColor: isSelected ? 'var(--bg-card-selected)' : 'var(--bg-surface)',
                    border: `1px solid ${isSelected ? '#38bdf8' : 'var(--border)'}`,
                    borderRadius: '10px',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    boxShadow: isSelected ? '0 0 20px rgba(56, 189, 248, 0.22)' : 'none',
                    transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
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
                        style={{
                          fontSize: '10px',
                          color: '#38bdf8',
                          backgroundColor: 'rgba(56, 189, 248, 0.1)',
                          border: '1px solid rgba(56, 189, 248, 0.25)',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontWeight: 600,
                        }}
                      >
                        Sub-tick CS2
                      </span>
                    </div>

                    <p
                      title={demo.file_path}
                      style={{
                        fontSize: '12px',
                        color: '#cbd5e1',
                        fontWeight: 600,
                        wordBreak: 'break-all',
                        marginBottom: '3px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <FolderIcon size={13} color="#94a3b8" />
                      <span>{demo.file_path.split(/[\\/]/).pop() || demo.file_path}</span>
                    </p>
                    <p
                      title={demo.file_path}
                      style={{
                        fontSize: '10px',
                        color: 'var(--text-muted)',
                        wordBreak: 'break-all',
                        marginBottom: '10px',
                        fontFamily: 'monospace',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
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
                          placeholder={lang === 'ru' ? 'Например: FACEIT финал 16-14 против s1mple' : 'e.g. FACEIT final 16-14 vs s1mple'}
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
                        title={lang === 'ru' ? 'Нажмите чтобы подписать или изменить заметку к этой демке' : 'Click to add or edit custom note for this demo'}
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
                          {demoNotes[demo.id] || (lang === 'ru' ? '+ Подписать демку / заметка' : '+ Add custom note')}
                        </span>
                        <span style={{ fontSize: '11px', color: '#94a3b8' }}>✎</span>
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
                        <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>{t('common.rounds')}</div>
                      </div>
                      <div>
                        <div className="num" style={{ fontSize: '15px', fontWeight: 700 }}>
                          {demo.players_count}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>{t('common.player')}s</div>
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
                        <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>{t('library.colHighlights')}</div>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
                      {t('library.colDuration')}: {formatDuration(demo.duration_seconds)}
                    </span>
                    <button
                      className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        onSelectDemo(demo)
                      }}
                      style={{
                        padding: '8px 16px',
                        fontSize: '12.5px',
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        backgroundColor: isSelected ? '#38bdf8' : undefined,
                        color: isSelected ? '#040711' : undefined,
                        boxShadow: isSelected ? '0 0 16px rgba(56, 189, 248, 0.4)' : undefined,
                      }}
                    >
                      {isSelected ? (
                        <>
                          <CheckIcon size={14} color="#040711" />
                          <span>{lang === 'ru' ? 'В Студию хайлайтов ➔' : 'To Highlights Studio ➔'}</span>
                        </>
                      ) : (
                        <span>{lang === 'ru' ? 'Выбрать и открыть в Студии →' : 'Select & Open in Studio →'}</span>
                      )}
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

