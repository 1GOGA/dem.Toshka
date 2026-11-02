import { useEffect, useState } from 'react'
import { api } from '../api'
import type { CompletedClipDTO, MontageDTO } from '../types'
import { useTranslation } from '../i18n'
import { VideoPlayerModal } from './VideoPlayerModal'

interface ClipsMontageViewProps {
  onOpenFolder?: () => void
  currentDemoId?: number | null
  currentMapName?: string | null
}

export function ClipsMontageView({ onOpenFolder, currentDemoId, currentMapName }: ClipsMontageViewProps) {
  const { lang } = useTranslation()
  const [clips, setClips] = useState<CompletedClipDTO[]>([])
  const [selectedFilenames, setSelectedFilenames] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cleanMessage, setCleanMessage] = useState<string | null>(null)
  const [filterMap, setFilterMap] = useState<string>('all')
  const [filterDemo, setFilterDemo] = useState<string>('all')

  // Montage compile state
  const [isCompiling, setIsCompiling] = useState(false)
  const [compiledMontage, setCompiledMontage] = useState<MontageDTO | null>(null)
  const [activeModalVideo, setActiveModalVideo] = useState<{
    url: string
    title: string
    subtitle?: string
  } | null>(null)
  const [hoveredClip, setHoveredClip] = useState<string | null>(null)

  const loadClips = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await api.listCompletedClips()
      setClips(data)
    } catch (err: any) {
      console.error('Failed to load clips:', err)
      setError(err?.message || (lang === 'ru' ? 'Не удалось загрузить список готовых роликов' : 'Failed to load clips list'))
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
      setCleanMessage(lang === 'ru' ? `Очищено файлов логов: ${res.count}` : `Cleaned up ${res.count} log files`)
      setTimeout(() => setCleanMessage(null), 3500)
    } catch (err: any) {
      setError(err?.message || (lang === 'ru' ? 'Ошибка очистки логов' : 'Failed to clear logs'))
    }
  }

  const handleCleanupDemoClips = async () => {
    if (!currentDemoId) return
    const confirmed = window.confirm(
      lang === 'ru'
        ? `Удалить все клипы для карты ${currentMapName || 'текущего матча'}?\n\nКлипы других матчей затронуты не будут.`
        : `Delete all clips for ${currentMapName || 'current match'}?\n\nClips of other matches will not be affected.`
    )
    if (!confirmed) return
    try {
      const res = await api.cleanupDemoClips(currentDemoId)
      setCleanMessage(lang === 'ru' ? `Успешно удалено клипов матча: ${res.count}` : `Successfully removed ${res.count} match clips`)
      setTimeout(() => setCleanMessage(null), 3500)
      loadClips()
    } catch (err: any) {
      setError(err?.message || (lang === 'ru' ? 'Ошибка удаления клипов матча' : 'Error deleting match clips'))
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
      setError(err?.message || (lang === 'ru' ? 'Ошибка сборки монтажа через FFmpeg' : 'FFmpeg montage compilation error'))
    } finally {
      setIsCompiling(false)
    }
  }

  const handleDeleteSelected = async () => {
    if (selectedFilenames.length === 0) return
    const confirmed = window.confirm(
      (lang === 'ru'
        ? `Вы действительно хотите удалить ${selectedFilenames.length} файл(ов)?\n\n`
        : `Are you sure you want to delete ${selectedFilenames.length} file(s)?\n\n`) +
        selectedFilenames.slice(0, 5).join('\n') +
        (selectedFilenames.length > 5 ? '\n...' : '')
    )
    if (!confirmed) return

    try {
      await api.deleteClips(selectedFilenames)
      setSelectedFilenames([])
      loadClips()
      setCleanMessage(lang === 'ru' ? `Успешно удалено файлов: ${selectedFilenames.length}` : `Successfully deleted ${selectedFilenames.length} files`)
      setTimeout(() => setCleanMessage(null), 3000)
    } catch (err: any) {
      setError(err?.message || (lang === 'ru' ? 'Не удалось удалить файлы' : 'Failed to delete files'))
    }
  }

  const handleCleanupTempFiles = async () => {
    try {
      const res = await api.cleanupTempArtifacts()
      const d = res.cleaned.directories || 0
      const w = res.cleaned.wav_files || 0
      const l = res.cleaned.log_files || 0
      setCleanMessage(
        lang === 'ru'
          ? `Очищено временных папок: ${d}, промежуточных .wav: ${w}, логов: ${l}. Все MP4 сохранены.`
          : `Cleaned up ${d} temp dirs, ${w} intermediate .wav files, ${l} logs. All MP4s preserved.`
      )
      setTimeout(() => setCleanMessage(null), 4000)
    } catch (err: any) {
      setError(err?.message || (lang === 'ru' ? 'Ошибка очистки временных файлов' : 'Error cleaning up temp files'))
    }
  }

  const handleCleanupAllClips = async () => {
    if (clips.length === 0) return
    const confirmed = window.confirm(
      lang === 'ru'
        ? `ВНИМАНИЕ: Вы действительно хотите удалить ВСЕ (${clips.length}) готовые ролики из папки вывода?\n\nЭто действие необратимо. Исходные .dem файлы затронуты НЕ будут.`
        : `WARNING: Are you sure you want to delete ALL (${clips.length}) clips from the output folder?\n\nThis cannot be undone. Source .dem files will NOT be affected.`
    )
    if (!confirmed) return

    try {
      const res = await api.cleanupAllClips()
      setSelectedFilenames([])
      setCleanMessage(lang === 'ru' ? `Успешно удалено ${res.count} роликов. Папка вывода очищена.` : `Successfully removed ${res.count} clips. Output folder cleared.`)
      setTimeout(() => setCleanMessage(null), 4000)
      loadClips()
    } catch (err: any) {
      setError(err?.message || (lang === 'ru' ? 'Ошибка очистки всех роликов' : 'Error clearing clips'))
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
            {lang === 'ru' ? 'Готовые ролики и монтажная студия' : 'Rendered Clips & Montage Studio'}
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 0 0' }}>
            {lang === 'ru'
              ? 'Выбирайте отрендеренные клипы, меняйте порядок и объединяйте их в единый качественный MP4 через FFmpeg.'
              : 'Select rendered clips, reorder them and compile into a single high-quality MP4 using FFmpeg.'}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCleanupLogs}
            title={lang === 'ru' ? 'Очистить все файлы логов (.log) HLAE, FFmpeg и запуска' : 'Clear all log files (.log) from HLAE, FFmpeg and launch'}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
          >
            📄 {lang === 'ru' ? 'Очистить логи' : 'Clear Logs'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCleanupTempFiles}
            title={lang === 'ru' ? 'Очистить промежуточные временные файлы рендера' : 'Clean up temporary intermediate render files'}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
          >
            🧹 {lang === 'ru' ? 'Временные файлы' : 'Temp Files'}
          </button>

          {currentDemoId && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCleanupDemoClips}
              title={lang === 'ru' ? `Удалить только клипы карты ${currentMapName || 'текущего матча'}` : `Delete only clips for ${currentMapName || 'current match'}`}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#fb923c' }}
            >
              🗑 {lang === 'ru' ? 'Клипы карты' : 'Clips for'} {currentMapName ? currentMapName.replace('de_', '').toUpperCase() : ''}
            </button>
          )}

          {clips.length > 0 && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCleanupAllClips}
              title={lang === 'ru' ? 'Очистить все созданные MP4 клипы' : 'Delete all created MP4 clips'}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#f87171' }}
            >
              🗑 {lang === 'ru' ? 'Очистить все' : 'Clear All'}
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
            {lang === 'ru' ? 'Открыть папку' : 'Open Folder'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadClips}
            disabled={isLoading}
            style={{ fontSize: '12px' }}
          >
            🔄 {lang === 'ru' ? 'Обновить' : 'Refresh'}
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
                {lang === 'ru' ? 'Готовые клипы' : 'Rendered Clips'} ({clips.length})
              </span>

              {/* Map & Demo Filter Controls */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
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
                    {lang === 'ru' ? 'Все карты' : 'All Maps'} ({clips.length})
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

                {/* Demo/Game Dropdown Filter */}
                {Array.from(new Set(clips.map((c) => c.demo_id).filter((id): id is number => id !== null && id !== undefined))).length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>
                      🎮 {lang === 'ru' ? 'Матч:' : 'Demo:'}
                    </span>
                    <select
                      value={filterDemo}
                      onChange={(e) => setFilterDemo(e.target.value)}
                      style={{
                        backgroundColor: '#0e1118',
                        color: filterDemo === 'all' ? '#94a3b8' : '#38bdf8',
                        border: '1px solid #232734',
                        borderRadius: '6px',
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        outline: 'none',
                      }}
                    >
                      <option value="all">
                        {lang === 'ru' ? 'Все матчи / демки' : 'All Demos / Matches'}
                      </option>
                      {Array.from(
                        new Map(
                          clips
                            .filter((c) => c.demo_id !== null && c.demo_id !== undefined)
                            .map((c) => [
                              c.demo_id as number,
                              {
                                id: c.demo_id as number,
                                label: c.demo_filename
                                  ? c.demo_filename
                                  : `${c.map_name ? c.map_name.replace('de_', '').toUpperCase() : 'Match'} #${c.demo_id}`,
                                count: clips.filter((item) => item.demo_id === c.demo_id).length,
                              },
                            ])
                        ).values()
                      ).map((d) => (
                        <option key={d.id} value={String(d.id)}>
                          {d.label} ({d.count})
                        </option>
                      ))}
                      <option value="montages">
                        🎬 {lang === 'ru' ? 'Только сборные монтажи' : 'Only Montages'} ({clips.filter((c) => c.is_montage).length})
                      </option>
                    </select>
                  </div>
                )}
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
                  {lang === 'ru' ? 'Выбрать все' : 'Select All'}
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
                  {lang === 'ru' ? 'Снять выбор' : 'Deselect All'}
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
              {lang === 'ru'
                ? 'В выходной папке пока нет отрендеренных клипов. Отрендерите хайлайты в Студии или Очереди.'
                : 'No rendered clips in the output folder yet. Render highlights in Studio or Queue.'}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '18px' }}>
            {clips
              .filter((c) => {
                if (filterMap !== 'all' && c.map_name !== filterMap) return false
                if (filterDemo === 'all') return true
                if (filterDemo === 'montages') return c.is_montage
                return String(c.demo_id) === filterDemo
              })
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
                    {/* 16:9 Video Thumbnail Preview (Optimized on-demand loading) */}
                    <div
                      style={{
                        position: 'relative',
                        width: '100%',
                        aspectRatio: '16 / 9',
                        backgroundColor: '#090b10',
                        overflow: 'hidden',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={() => setHoveredClip(c.filename)}
                      onMouseLeave={() => setHoveredClip(null)}
                      onClick={() =>
                        setActiveModalVideo({
                          url: c.url,
                          title: c.filename,
                          subtitle: `${formatFileSize(c.size_bytes)} • ${new Date(c.modified_at * 1000).toLocaleTimeString()}`,
                        })
                      }
                      title={lang === 'ru' ? 'Нажмите для полноэкранного воспроизведения' : 'Click for fullscreen playback'}
                    >
                      {hoveredClip === c.filename ? (
                        <video
                          preload="auto"
                          src={`${c.url}#t=0.5`}
                          poster={c.thumbnail_url || undefined}
                          autoPlay
                          loop
                          muted
                          playsInline
                          style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                            transform: 'scale(1.03)',
                            transition: 'transform 0.3s ease',
                          }}
                        />
                      ) : c.thumbnail_url ? (
                        <img
                          src={c.thumbnail_url}
                          alt={c.filename}
                          loading="lazy"
                          style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                            display: 'block',
                            transition: 'transform 0.3s ease',
                          }}
                        />
                      ) : (
                        <div
                          style={{
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: 'radial-gradient(ellipse at center, rgba(18, 26, 44, 0.9) 0%, rgba(8, 11, 18, 0.98) 100%)',
                            position: 'relative',
                          }}
                        >
                          <div
                            style={{
                              position: 'absolute',
                              inset: 0,
                              backgroundImage: 'linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px)',
                              backgroundSize: '20px 20px',
                            }}
                          />
                        </div>
                      )}

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
                            🎬 {lang === 'ru' ? 'МОНТАЖ' : 'MONTAGE'}
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
                          <span>{lang === 'ru' ? 'Матч CS2' : 'CS2 Match'}</span>
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
                          <span>▶</span> {lang === 'ru' ? 'Смотреть' : 'Watch'}
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
                          <span>⬇</span> {lang === 'ru' ? 'Скачать' : 'Download'}
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
              {lang === 'ru' ? 'Очередь сборки' : 'Assembly Queue'} ({selectedFilenames.length})
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
                {lang === 'ru' ? 'Удалить выбранные' : 'Delete Selected'}
              </button>
            )}
          </div>

          <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
            {lang === 'ru'
              ? 'Стрелками вверх/вниз настраивайте точный порядок следования клипов в итоговом ролике.'
              : 'Use up/down arrows to set the exact sequence of clips in the final video.'}
          </p>

          {/* Ordered List with Move Up / Move Down buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '360px', overflowY: 'auto' }}>
            {selectedFilenames.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '12px' }}>
                {lang === 'ru'
                  ? 'Выберите клипы слева чекбоксами для объединения.'
                  : 'Select clips on the left with checkboxes to merge.'}
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
            {isCompiling
              ? (lang === 'ru' ? '⏳ Объединение через FFmpeg...' : '⏳ Merging via FFmpeg...')
              : (lang === 'ru' ? '🎬 Собрать монтаж из выбранных' : '🎬 Build Montage from Selected')}
          </button>

          {/* Compiled Result Banner */}
          {compiledMontage && (
            <div style={{ marginTop: '12px', padding: '14px', backgroundColor: '#0f1117', borderRadius: '8px', border: '1px solid #22c55e', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#4ade80' }}>
                  {lang === 'ru' ? '✓ Монтаж готов' : '✓ Montage Ready'} ({compiledMontage.duration_seconds.toFixed(1)} {lang === 'ru' ? 'с' : 's'}, {compiledMontage.total_clips} {lang === 'ru' ? 'клипов' : 'clips'})
                </span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() =>
                      setActiveModalVideo({
                        url: `/api/montage/${compiledMontage.filename}`,
                        title: compiledMontage.filename,
                        subtitle: `${lang === 'ru' ? 'Монтаж' : 'Montage'} (${compiledMontage.duration_seconds.toFixed(1)} ${lang === 'ru' ? 'с' : 's'}, ${compiledMontage.total_clips} ${lang === 'ru' ? 'клипов' : 'clips'})`,
                      })
                    }
                    style={{ padding: '3px 8px', fontSize: '11px', color: '#38bdf8' }}
                  >
                    ▶ {lang === 'ru' ? 'Смотреть в плеере' : 'Watch in Player'}
                  </button>
                  <a
                    href={`/api/montage/${compiledMontage.filename}`}
                    download
                    style={{ color: '#94a3b8', fontSize: '11px', textDecoration: 'none', display: 'flex', alignItems: 'center' }}
                  >
                    ⬇ {lang === 'ru' ? 'Скачать' : 'Download'}
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
        title={activeModalVideo?.title || (lang === 'ru' ? 'Воспроизведение клипа' : 'Video Player')}
        subtitle={activeModalVideo?.subtitle}
      />
    </div>
  )
}

