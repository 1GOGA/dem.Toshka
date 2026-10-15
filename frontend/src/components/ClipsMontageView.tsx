import { useEffect, useState } from 'react'
import { api } from '../api'
import type { CompletedClipDTO, MontageDTO } from '../types'
import { VideoPlayerModal } from './VideoPlayerModal'

interface ClipsMontageViewProps {
  onOpenFolder?: () => void
  currentDemoId?: number | null
  currentMapName?: string | null
}

export function ClipsMontageView({ onOpenFolder, currentDemoId, currentMapName }: ClipsMontageViewProps) {
  const [clips, setClips] = useState<CompletedClipDTO[]>([])
  const [selectedFilenames, setSelectedFilenames] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cleanMessage, setCleanMessage] = useState<string | null>(null)
  const [filterMap, setFilterMap] = useState<string>('all')

  // Montage compile state
  const [isCompiling, setIsCompiling] = useState(false)
  const [compiledMontage, setCompiledMontage] = useState<MontageDTO | null>(null)
  const [activeModalVideo, setActiveModalVideo] = useState<{
    url: string
    title: string
    subtitle?: string
  } | null>(null)

  const loadClips = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await api.listCompletedClips()
      setClips(data)
    } catch (err: any) {
      console.error('Failed to load clips:', err)
      setError(err?.message || 'Не удалось загрузить список готовых роликов')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadClips()
  }, [])

  const handleCleanupLogs = async () => {
    try {
      const res = await api.cleanupRenderLogs()
      setCleanMessage(`Очищено файлов логов: ${res.count}`)
      setTimeout(() => setCleanMessage(null), 3500)
    } catch (err: any) {
      setError(err?.message || 'Ошибка очистки логов')
    }
  }

  const handleCleanupDemoClips = async () => {
    if (!currentDemoId) return
    const confirmed = window.confirm(
      `Удалить все клипы для карты ${currentMapName || 'текущего матча'}?\n\nКлипы других матчей затронуты не будут.`
    )
    if (!confirmed) return
    try {
      const res = await api.cleanupDemoClips(currentDemoId)
      setCleanMessage(`Успешно удалено клипов матча: ${res.count}`)
      setTimeout(() => setCleanMessage(null), 3500)
      loadClips()
    } catch (err: any) {
      setError(err?.message || 'Ошибка удаления клипов матча')
    }
  }

  const handleToggleSelect = (filename: string) => {
    setSelectedFilenames((prev) => {
      if (prev.includes(filename)) {
        return prev.filter((f) => f !== filename)
      } else {
        return [...prev, filename]
      }
    })
  }

  const handleMoveUp = (index: number) => {
    if (index <= 0) return
    const next = [...selectedFilenames]
    const temp = next[index - 1]
    next[index - 1] = next[index]
    next[index] = temp
    setSelectedFilenames(next)
  }

  const handleMoveDown = (index: number) => {
    if (index >= selectedFilenames.length - 1) return
    const next = [...selectedFilenames]
    const temp = next[index + 1]
    next[index + 1] = next[index]
    next[index] = temp
    setSelectedFilenames(next)
  }

  const handleCreateMontageFromSelected = async () => {
    if (selectedFilenames.length === 0) return
    setIsCompiling(true)
    setError(null)

    try {
      const res = await api.createMontage({
        filenames: selectedFilenames,
        output_filename: `custom_montage_${Date.now()}.mp4`,
      })
      setCompiledMontage(res)
      loadClips()
    } catch (err: any) {
      setError(err?.message || 'Ошибка сборки монтажа через FFmpeg')
    } finally {
      setIsCompiling(false)
    }
  }

  const handleDeleteSelected = async () => {
    if (selectedFilenames.length === 0) return
    const confirmed = window.confirm(
      `Вы действительно хотите удалить ${selectedFilenames.length} файл(ов)?\n\n` +
        selectedFilenames.slice(0, 5).join('\n') +
        (selectedFilenames.length > 5 ? '\n...' : '')
    )
    if (!confirmed) return

    try {
      await api.deleteClips(selectedFilenames)
      setSelectedFilenames([])
      loadClips()
      setCleanMessage(`Успешно удалено файлов: ${selectedFilenames.length}`)
      setTimeout(() => setCleanMessage(null), 3000)
    } catch (err: any) {
      setError(err?.message || 'Не удалось удалить файлы')
    }
  }

  const handleCleanupTempFiles = async () => {
    try {
      const res = await api.cleanupTempArtifacts()
      const d = res.cleaned.directories || 0
      const w = res.cleaned.wav_files || 0
      const l = res.cleaned.log_files || 0
      setCleanMessage(`Очищено временных папок: ${d}, промежуточных .wav: ${w}, логов: ${l}. Все MP4 сохранены.`)
      setTimeout(() => setCleanMessage(null), 4000)
    } catch (err: any) {
      setError(err?.message || 'Ошибка очистки временных файлов')
    }
  }

  const handleCleanupAllClips = async () => {
    if (clips.length === 0) return
    const confirmed = window.confirm(
      `ВНИМАНИЕ: Вы действительно хотите удалить ВСЕ (${clips.length}) готовые ролики из папки вывода?\n\nЭто действие необратимо. Исходные .dem файлы затронуты НЕ будут.`
    )
    if (!confirmed) return

    try {
      const res = await api.cleanupAllClips()
      setSelectedFilenames([])
      setCleanMessage(`Успешно удалено ${res.count} роликов. Папка вывода очищена.`)
      setTimeout(() => setCleanMessage(null), 4000)
      loadClips()
    } catch (err: any) {
      setError(err?.message || 'Ошибка очистки всех роликов')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#f1f5f9', letterSpacing: '-0.02em', margin: 0 }}>
            Готовые ролики и монтажная студия
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 0 0' }}>
            Выбирайте отрендеренные клипы, меняйте порядок и объединяйте их в единый качественный MP4 через FFmpeg.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCleanupLogs}
            title="Очистить все файлы логов (.log) HLAE, FFmpeg и запуска"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
          >
            📄 Очистить логи
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCleanupTempFiles}
            title="Очистить промежуточные временные файлы рендера"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
          >
            🧹 Временные файлы
          </button>

          {currentDemoId && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCleanupDemoClips}
              title={`Удалить только клипы карты ${currentMapName || 'текущего матча'}`}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#fb923c' }}
            >
              🗑 Клипы карты {currentMapName ? currentMapName.replace('de_', '').toUpperCase() : ''}
            </button>
          )}

          {clips.length > 0 && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCleanupAllClips}
              title="Очистить все созданные MP4 клипы"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#f87171' }}
            >
              🗑 Очистить все
            </button>
          )}

          <button
            type="button"
            className="btn btn-secondary"
            onClick={onOpenFolder || (() => api.openOutputFolder())}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
            </svg>
            Открыть папку
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadClips}
            disabled={isLoading}
            style={{ fontSize: '12px' }}
          >
            🔄 Обновить
          </button>
        </div>
      </div>

      {cleanMessage && (
        <div style={{ padding: '12px 16px', backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid #22c55e', borderRadius: '8px', color: '#4ade80', fontSize: '13px', marginBottom: '16px' }}>
          ✓ {cleanMessage}
        </div>
      )}

      {error && (
        <div style={{ padding: '14px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', color: '#f87171', fontSize: '13px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Main Grid: Clips on left, Compilation queue on right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px', alignItems: 'start' }}>
        {/* Clips Gallery / List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>
                Готовые клипы ({clips.length})
              </span>

              {/* Map Filter Tabs */}
              <div style={{ display: 'flex', gap: '6px', background: '#0e1118', padding: '3px', borderRadius: '6px', border: '1px solid #232734' }}>
                <button
                  type="button"
                  onClick={() => setFilterMap('all')}
                  style={{
                    border: 'none',
                    padding: '3px 10px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: filterMap === 'all' ? '#38bdf8' : 'transparent',
                    color: filterMap === 'all' ? '#090d16' : '#94a3b8',
                  }}
                >
                  Все ({clips.length})
                </button>
                {Array.from(new Set(clips.map((c) => c.map_name).filter(Boolean))).map((m) => {
                  const count = clips.filter((c) => c.map_name === m).length
                  const isCur = filterMap === m
                  return (
                    <button
                      key={m as string}
                      type="button"
                      onClick={() => setFilterMap(m as string)}
                      style={{
                        border: 'none',
                        padding: '3px 10px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        background: isCur ? '#38bdf8' : 'transparent',
                        color: isCur ? '#090d16' : '#94a3b8',
                      }}
                    >
                      {(m as string).replace('de_', '').toUpperCase()} ({count})
                    </button>
                  )
                })}
              </div>
            </div>

            {clips.length > 0 && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setSelectedFilenames(clips.map((c) => c.filename))}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#38bdf8',
                    fontSize: '12px',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                  }}
                >
                  Выбрать все
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedFilenames([])}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#94a3b8',
                    fontSize: '12px',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                  }}
                >
                  Снять выбор
                </button>
              </div>
            )}
          </div>

          {clips.length === 0 && !isLoading && (
            <div
              style={{
                padding: '60px',
                textAlign: 'center',
                backgroundColor: '#12141a',
                borderRadius: '10px',
                border: '1px solid #232734',
                color: '#64748b',
                fontSize: '13px',
              }}
            >
              В выходной папке пока нет отрендеренных клипов. Отрендерите хайлайты в Студии или Очереди.
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '18px' }}>
            {clips
              .filter((c) => filterMap === 'all' || c.map_name === filterMap)
              .map((c) => {
                const isSelected = selectedFilenames.includes(c.filename)
                return (
                  <div
                    key={c.filename}
                    style={{
                      backgroundColor: '#12141c',
                      border: isSelected ? '1px solid #38bdf8' : '1px solid #232738',
                      borderRadius: '12px',
                      overflow: 'hidden',
                      display: 'flex',
                      flexDirection: 'column',
                      boxShadow: isSelected ? '0 0 16px rgba(56, 189, 248, 0.2)' : '0 4px 14px rgba(0, 0, 0, 0.4)',
                      transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                    }}
                  >
                    {/* 16:9 Video Thumbnail Preview */}
                    <div
                      style={{
                        position: 'relative',
                        width: '100%',
                        aspectRatio: '16 / 9',
                        backgroundColor: '#090b10',
                        overflow: 'hidden',
                        cursor: 'pointer',
                      }}
                      onClick={() =>
                        setActiveModalVideo({
                          url: c.url,
                          title: c.filename,
                          subtitle: `${formatFileSize(c.size_bytes)} • ${new Date(c.modified_at * 1000).toLocaleTimeString()}`,
                        })
                      }
                      title="Нажмите для полноэкранного воспроизведения"
                    >
                      <video
                        preload="metadata"
                        src={`${c.url}#t=0.5`}
                        muted
                        playsInline
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                          opacity: 0.88,
                          transition: 'transform 0.3s ease, opacity 0.3s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'scale(1.04)'
                          e.currentTarget.style.opacity = '1.0'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'scale(1.0)'
                          e.currentTarget.style.opacity = '0.88'
                        }}
                      />

                      {/* Vignette Bottom Gradient */}
                      <div
                        style={{
                          position: 'absolute',
                          inset: 0,
                          background: 'linear-gradient(180deg, rgba(0,0,0,0.3) 0%, transparent 40%, rgba(10,12,18,0.85) 100%)',
                          pointerEvents: 'none',
                        }}
                      />

                      {/* Center Play Button Overlay */}
                      <div
                        style={{
                          position: 'absolute',
                          top: '50%',
                          left: '50%',
                          transform: 'translate(-50%, -50%)',
                          width: '42px',
                          height: '42px',
                          borderRadius: '50%',
                          backgroundColor: 'rgba(15, 23, 42, 0.75)',
                          border: '2px solid rgba(56, 189, 248, 0.6)',
                          boxShadow: '0 0 16px rgba(56, 189, 248, 0.4)',
                          backdropFilter: 'blur(4px)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#38bdf8',
                          fontSize: '16px',
                          pointerEvents: 'none',
                          transition: 'all 0.2s ease',
                        }}
                      >
                        ▶
                      </div>

                      {/* Top Bar Badges */}
                      <div
                        style={{
                          position: 'absolute',
                          top: '10px',
                          left: '10px',
                          right: '10px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          zIndex: 2,
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {/* Checkbox for montage inclusion */}
                        <label
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            backgroundColor: 'rgba(10, 12, 18, 0.75)',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            cursor: 'pointer',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleToggleSelect(c.filename)}
                            style={{ accentColor: '#38bdf8', width: '15px', height: '15px', cursor: 'pointer' }}
                          />
                        </label>

                        {/* Event / Montage Badge */}
                        {c.is_montage ? (
                          <span
                            style={{
                              fontSize: '10px',
                              backgroundColor: '#38bdf8',
                              color: '#090d16',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontWeight: 900,
                              letterSpacing: '0.05em',
                              boxShadow: '0 0 10px rgba(56, 189, 248, 0.5)',
                            }}
                          >
                            🎬 МОНТАЖ
                          </span>
                        ) : c.highlight_type ? (
                          <span
                            style={{
                              fontSize: '10px',
                              backgroundColor: 'rgba(234, 179, 8, 0.85)',
                              color: '#090d16',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontWeight: 800,
                              letterSpacing: '0.05em',
                            }}
                          >
                            ⚡ {c.highlight_type.toUpperCase()}
                          </span>
                        ) : null}
                      </div>

                      {/* Bottom Overlay Info (Map & Size) */}
                      <div
                        style={{
                          position: 'absolute',
                          bottom: '8px',
                          left: '10px',
                          right: '10px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '11px',
                          fontWeight: 700,
                          pointerEvents: 'none',
                        }}
                      >
                        {c.map_name && (
                          <span
                            style={{
                              backgroundColor: 'rgba(15, 23, 42, 0.85)',
                              color: '#38bdf8',
                              padding: '2px 7px',
                              borderRadius: '4px',
                              border: '1px solid rgba(56, 189, 248, 0.3)',
                              fontSize: '10px',
                            }}
                          >
                            🗺️ {c.map_name.replace('de_', '').toUpperCase()}
                          </span>
                        )}
                        <span
                          style={{
                            backgroundColor: 'rgba(15, 23, 42, 0.85)',
                            color: '#94a3b8',
                            padding: '2px 7px',
                            borderRadius: '4px',
                            fontSize: '10px',
                          }}
                        >
                          📦 {formatFileSize(c.size_bytes)}
                        </span>
                      </div>
                    </div>

                    {/* Card Body */}
                    <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div
                        style={{
                          fontSize: '12px',
                          fontWeight: 700,
                          color: '#f1f5f9',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                        title={c.filename}
                      >
                        {c.filename}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: '#64748b' }}>
                        {c.player_name ? (
                          <span style={{ color: '#cbd5e1', fontWeight: 600 }}>
                            👤 {c.player_name} {c.round_num ? `(R${c.round_num})` : ''}
                          </span>
                        ) : (
                          <span>Матч CS2</span>
                        )}
                        <span>🕒 {new Date(c.modified_at * 1000).toLocaleTimeString()}</span>
                      </div>

                      {/* Card Action Buttons */}
                      <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                        <button
                          type="button"
                          className="btn"
                          onClick={() =>
                            setActiveModalVideo({
                              url: c.url,
                              title: c.filename,
                              subtitle: `${formatFileSize(c.size_bytes)} • ${new Date(c.modified_at * 1000).toLocaleTimeString()}`,
                            })
                          }
                          style={{
                            flex: 1,
                            padding: '6px 10px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: 'rgba(56, 189, 248, 0.15)',
                            color: '#38bdf8',
                            border: '1px solid rgba(56, 189, 248, 0.35)',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '4px',
                          }}
                        >
                          <span>▶</span> Смотреть
                        </button>
                        <a
                          href={c.url}
                          download={c.filename}
                          className="btn btn-secondary"
                          style={{
                            padding: '6px 12px',
                            fontSize: '11px',
                            fontWeight: 600,
                            textDecoration: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <span>⬇</span> Скачать
                        </a>
                      </div>
                    </div>
                  </div>
                )
              })}
          </div>
        </div>

        {/* Right Sidebar: Custom Sequence Reorder & Montage Assembly */}
        <div
          style={{
            backgroundColor: '#12141a',
            border: '1px solid #232734',
            borderRadius: '10px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>
              Очередь сборки ({selectedFilenames.length})
            </span>
            {selectedFilenames.length > 0 && (
              <button
                type="button"
                onClick={handleDeleteSelected}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#ef4444',
                  fontSize: '11px',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Удалить выбранные
              </button>
            )}
          </div>

          <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
            Стрелками вверх/вниз настраивайте точный порядок следования клипов в итоговом ролике.
          </p>

          {/* Ordered List with Move Up / Move Down buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '360px', overflowY: 'auto' }}>
            {selectedFilenames.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '12px' }}>
                Выберите клипы слева чекбоксами для объединения.
              </div>
            ) : (
              selectedFilenames.map((fn, idx) => (
                <div
                  key={fn}
                  style={{
                    backgroundColor: '#171a23',
                    border: '1px solid #232734',
                    borderRadius: '6px',
                    padding: '8px 10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '11px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                    <span style={{ color: '#38bdf8', fontWeight: 700 }}>#{idx + 1}</span>
                    <span style={{ color: '#f1f5f9', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {fn}
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button
                      type="button"
                      disabled={idx === 0}
                      onClick={() => handleMoveUp(idx)}
                      style={{
                        padding: '2px 6px',
                        borderRadius: '3px',
                        border: '1px solid #232734',
                        backgroundColor: '#1f2330',
                        color: idx === 0 ? '#475569' : '#f1f5f9',
                        cursor: idx === 0 ? 'not-allowed' : 'pointer',
                      }}
                    >
                      ▲
                    </button>
                    <button
                      type="button"
                      disabled={idx === selectedFilenames.length - 1}
                      onClick={() => handleMoveDown(idx)}
                      style={{
                        padding: '2px 6px',
                        borderRadius: '3px',
                        border: '1px solid #232734',
                        backgroundColor: '#1f2330',
                        color: idx === selectedFilenames.length - 1 ? '#475569' : '#f1f5f9',
                        cursor: idx === selectedFilenames.length - 1 ? 'not-allowed' : 'pointer',
                      }}
                    >
                      ▼
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Montage Assembly Trigger */}
          <button
            type="button"
            className="btn btn-accent"
            onClick={handleCreateMontageFromSelected}
            disabled={isCompiling || selectedFilenames.length === 0}
            style={{ width: '100%', padding: '10px', fontSize: '13px', fontWeight: 700 }}
          >
            {isCompiling ? '⏳ Объединение через FFmpeg...' : '🎬 Собрать монтаж из выбранных'}
          </button>

          {/* Compiled Result Banner */}
          {compiledMontage && (
            <div style={{ marginTop: '12px', padding: '14px', backgroundColor: '#0f1117', borderRadius: '8px', border: '1px solid #22c55e', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#4ade80' }}>
                  ✓ Монтаж готов ({compiledMontage.duration_seconds.toFixed(1)} с, {compiledMontage.total_clips} клипов)
                </span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() =>
                      setActiveModalVideo({
                        url: `/api/montage/${compiledMontage.filename}`,
                        title: compiledMontage.filename,
                        subtitle: `Монтаж (${compiledMontage.duration_seconds.toFixed(1)} с, ${compiledMontage.total_clips} клипов)`,
                      })
                    }
                    style={{ padding: '3px 8px', fontSize: '11px', color: '#38bdf8' }}
                  >
                    ▶ Смотреть в плеере
                  </button>
                  <a
                    href={`/api/montage/${compiledMontage.filename}`}
                    download
                    style={{ color: '#94a3b8', fontSize: '11px', textDecoration: 'none', display: 'flex', alignItems: 'center' }}
                  >
                    ⬇ Скачать
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Advanced Video Player Modal with scrubbing & frame navigation */}
      <VideoPlayerModal
        isOpen={!!activeModalVideo}
        onClose={() => setActiveModalVideo(null)}
        videoUrl={activeModalVideo?.url || ''}
        title={activeModalVideo?.title || 'Воспроизведение клипа'}
        subtitle={activeModalVideo?.subtitle}
      />
    </div>
  )
}

