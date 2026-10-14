import React, { useEffect, useState, useRef } from 'react'
import { api } from '../api'
import type { ClipSettings, HighlightItem, MontageDTO, RenderJobDTO } from '../types'
import { VideoPlayerModal } from './VideoPlayerModal'

interface RenderQueueModalProps {
  isOpen: boolean
  onClose: () => void
  selectedHighlights: HighlightItem[]
  onRemoveHighlight: (id: string) => void
  onClearAll: () => void
  settings: ClipSettings
  demoId: number | null
  onSubmitRender: (highlightIds: string[]) => Promise<RenderJobDTO[]>
  tickrate: number
}

export const RenderQueueModal: React.FC<RenderQueueModalProps> = ({
  isOpen,
  onClose,
  selectedHighlights,
  onRemoveHighlight,
  onClearAll,
  settings,
  demoId,
  onSubmitRender,
  tickrate,
}) => {
  const [activeTab, setActiveTab] = useState<'queue' | 'history'>('queue')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRetrying, setIsRetrying] = useState(false)
  const [submissionError, setSubmissionError] = useState<string | null>(null)
  const [activeJobs, setActiveJobs] = useState<RenderJobDTO[]>([])
  const [historyJobs, setHistoryJobs] = useState<RenderJobDTO[]>([])
  const [activeModalVideo, setActiveModalVideo] = useState<{
    url: string
    title: string
    subtitle?: string
  } | null>(null)
  const [montageState, setMontageState] = useState<{
    isCreating: boolean
    montage: MontageDTO | null
    error: string | null
  }>({
    isCreating: false,
    montage: null,
    error: null,
  })
  const pollTimerRef = useRef<number | null>(null)

  // Fetch history whenever modal opens
  useEffect(() => {
    if (!isOpen || !demoId) return
    let isMounted = true

    api.listRenderJobs(demoId).then((jobs) => {
      if (isMounted) {
        setHistoryJobs(jobs)
      }
    }).catch((err) => {
      console.warn('Failed to load past render jobs:', err)
    })

    return () => {
      isMounted = false
    }
  }, [isOpen, demoId])

  // Polling for active jobs in queue or history
  useEffect(() => {
    if (!isOpen) {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current)
      return
    }

    const hasUnfinishedJobs =
      activeJobs.some((j) => j.status === 'pending' || j.status === 'running') ||
      historyJobs.some((j) => j.status === 'pending' || j.status === 'running')

    if (hasUnfinishedJobs) {
      pollTimerRef.current = window.setInterval(async () => {
        try {
          if (demoId) {
            const hist = await api.listRenderJobs(demoId)
            setHistoryJobs(hist)
          }
        } catch (e) {
          console.error('Polling error:', e)
        }
      }, 2000)
    } else {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current)
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current)
    }
  }, [isOpen, activeJobs, historyJobs, demoId])

  const handleRetrySingle = async (jobId: string) => {
    try {
      setIsRetrying(true)
      const retried = await api.retryRenderJob(jobId)
      setHistoryJobs((prev) => prev.map((j) => (j.id === jobId ? retried : j)))
    } catch (e: any) {
      console.error('Failed to retry job:', e)
      setSubmissionError(e?.message || 'Failed to retry job')
    } finally {
      setIsRetrying(false)
    }
  }

  const handleRetryFailedBatch = async () => {
    if (!demoId) return
    try {
      setIsRetrying(true)
      const retried = await api.retryFailedJobs(demoId)
      if (retried.length > 0) {
        const hist = await api.listRenderJobs(demoId)
        setHistoryJobs(hist)
      }
    } catch (e: any) {
      console.error('Failed to retry failed jobs:', e)
      setSubmissionError(e?.message || 'Failed to retry failed jobs')
    } finally {
      setIsRetrying(false)
    }
  }

  const [selectedMontageJobIds, setSelectedMontageJobIds] = useState<Set<string>>(new Set())

  // Sync selected completed jobs for montage
  useEffect(() => {
    const completedIds = historyJobs.filter((j) => j.status === 'completed').map((j) => j.id)
    setSelectedMontageJobIds(new Set(completedIds))
  }, [historyJobs])

  const handleToggleMontageJob = (jobId: string) => {
    setSelectedMontageJobIds((prev) => {
      const next = new Set(prev)
      if (next.has(jobId)) {
        next.delete(jobId)
      } else {
        next.add(jobId)
      }
      return next
    })
  }

  const handleSelectAllMontageJobs = () => {
    const completedIds = historyJobs.filter((j) => j.status === 'completed').map((j) => j.id)
    setSelectedMontageJobIds(new Set(completedIds))
  }

  const handleClearMontageSelection = () => {
    setSelectedMontageJobIds(new Set())
  }

  const handleDeleteJob = async (jobId: string) => {
    try {
      await api.deleteRenderJob(jobId)
      setHistoryJobs((prev) => prev.filter((j) => j.id !== jobId))
      setSelectedMontageJobIds((prev) => {
        const next = new Set(prev)
        next.delete(jobId)
        return next
      })
    } catch (e: any) {
      console.error('Failed to delete job:', e)
      setSubmissionError(e?.message || 'Failed to delete job')
    }
  }

  const handleClearCompleted = async () => {
    if (!demoId) return
    try {
      await api.clearCompletedRenderJobs(demoId)
      const hist = await api.listRenderJobs(demoId)
      setHistoryJobs(hist)
    } catch (e: any) {
      console.error('Failed to clear completed jobs:', e)
      setSubmissionError(e?.message || 'Failed to clear completed jobs')
    }
  }

  const handleCreateMontage = async () => {
    if (!demoId) return
    setMontageState({ isCreating: true, montage: null, error: null })
    try {
      const jobIds = selectedMontageJobIds.size > 0
        ? Array.from(selectedMontageJobIds)
        : historyJobs.filter((j) => j.status === 'completed').map((j) => j.id)

      if (jobIds.length === 0) {
        throw new Error('Выберите хотя бы один готовый клип для сборки нарезки')
      }

      const result = await api.createMontage({ demo_id: demoId, job_ids: jobIds })
      setMontageState({ isCreating: false, montage: result, error: null })
      setActiveModalVideo({
        url: `/api/montage/${result.filename}`,
        title: result.filename,
        subtitle: `Full Montage (${result.duration_seconds.toFixed(1)}s, ${result.total_clips} clips)`,
      })
    } catch (e: any) {
      console.error('Failed to create montage:', e)
      setMontageState({ isCreating: false, montage: null, error: e?.message || 'Failed to create montage' })
    }
  }

  if (!isOpen) return null

  const totalDurationSeconds = selectedHighlights.reduce((acc, h) => {
    return acc + (h.clip_end_tick - h.clip_start_tick) / (tickrate || 128)
  }, 0)

  const handleSubmit = async () => {
    if (!demoId || selectedHighlights.length === 0 || isSubmitting) return
    setIsSubmitting(true)
    setSubmissionError(null)

    try {
      const ids = selectedHighlights.map((h) => h.id)
      const jobs = await onSubmitRender(ids)
      setActiveJobs(jobs)
      setActiveTab('history')
      onClearAll()
    } catch (err: any) {
      setSubmissionError(err?.message || 'Failed to submit render jobs')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return (
          <span style={{ color: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
            ⏳ Queued
          </span>
        )
      case 'running':
        return (
          <span style={{ color: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.1)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
            🎥 Recording CS2...
          </span>
        )
      case 'completed':
        return (
          <span style={{ color: '#34d399', backgroundColor: 'rgba(52, 211, 153, 0.1)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
            ✓ Complete
          </span>
        )
      case 'failed':
        return (
          <span style={{ color: '#f87171', backgroundColor: 'rgba(248, 113, 113, 0.1)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
            ✕ Failed
          </span>
        )
      default:
        return <span>{status}</span>
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '750px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <h3 className="modal-title" style={{ margin: 0 }}>
              🎬 Video Render Queue
            </h3>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                className={`nav-tab ${activeTab === 'queue' ? 'active' : ''}`}
                onClick={() => setActiveTab('queue')}
                style={{ fontSize: '12px', padding: '4px 12px' }}
              >
                Selected Clips ({selectedHighlights.length})
              </button>
              <button
                className={`nav-tab ${activeTab === 'history' ? 'active' : ''}`}
                onClick={() => setActiveTab('history')}
                style={{ fontSize: '12px', padding: '4px 12px' }}
              >
                Job Monitor ({historyJobs.length})
              </button>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={async () => {
                try {
                  const res = await api.cleanupRenderLogs()
                  alert(`Очищено файлов логов: ${res.count}`)
                } catch (e: any) {
                  alert(`Ошибка: ${e.message}`)
                }
              }}
              style={{ fontSize: '11px', padding: '3px 8px' }}
              title="Очистить все файлы логов (.log) HLAE и FFmpeg"
            >
              📄 Очистить логи
            </button>
            {demoId && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={async () => {
                  if (!confirm('Удалить клипы этой карты?')) return
                  try {
                    const res = await api.cleanupDemoClips(demoId)
                    alert(`Удалено клипов: ${res.count}`)
                    const hist = await api.listRenderJobs(demoId)
                    setHistoryJobs(hist)
                  } catch (e: any) {
                    alert(`Ошибка: ${e.message}`)
                  }
                }}
                style={{ fontSize: '11px', padding: '3px 8px', color: '#fb923c' }}
                title="Удалить клипы этой демки"
              >
                🗑 Клипы карты
              </button>
            )}
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {submissionError && (
            <div
              style={{
                padding: '10px 14px',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '6px',
                color: '#f87171',
                fontSize: '12px',
                marginBottom: '16px',
              }}
            >
              {submissionError}
            </div>
          )}

          {activeTab === 'queue' && (
            <>
              {/* Export Summary Banner */}
              <div
                style={{
                  backgroundColor: 'var(--bg-app)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  marginBottom: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  fontSize: '12px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Capture Engine: </span>
                    <span style={{ fontWeight: 700, color: 'var(--accent-gold)' }}>
                      HLAE Direct3D 11 ({settings.resolution} @ {settings.fps} FPS)
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Estimated Duration: </span>
                    <span className="num" style={{ fontWeight: 700 }}>
                      {totalDurationSeconds.toFixed(1)}s total
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '12px', color: 'var(--text-muted)', fontSize: '11px', borderTop: '1px solid var(--border)', paddingTop: '6px' }}>
                  <span>POV: <strong style={{ color: 'var(--text-main)' }}>{settings.perspective.toUpperCase()}</strong></span>
                  <span>•</span>
                  <span>X-Ray: <strong style={{ color: settings.xray ? '#34d399' : '#f87171' }}>{settings.xray ? 'ENABLED' : 'DISABLED'}</strong></span>
                  <span>•</span>
                  <span>HUD Mode: <strong style={{ color: 'var(--text-main)' }}>{settings.hudMode.replace('_', ' ').toUpperCase()}</strong></span>
                </div>
              </div>

              {/* Selected List */}
              {selectedHighlights.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '13px' }}>
                  No clips selected. Check highlights in Highlights Studio to add them to this queue.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '350px', overflowY: 'auto' }}>
                  {selectedHighlights.map((hl) => {
                    const dur = ((hl.clip_end_tick - hl.clip_start_tick) / (tickrate || 128)).toFixed(1)
                    return (
                      <div
                        key={hl.id}
                        style={{
                          backgroundColor: 'var(--bg-card)',
                          border: '1px solid var(--border)',
                          borderRadius: '6px',
                          padding: '10px 14px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <span className={`type-badge type-${hl.highlight_type}`} style={{ fontSize: '10px' }}>
                              {hl.highlight_type.toUpperCase()}
                            </span>
                            <span style={{ fontWeight: 700, fontSize: '13px' }}>{hl.pov_name || 'Spectator'}</span>
                            <span style={{ fontSize: '11px', color: 'var(--text-faint)' }}>• Round {hl.round_num}</span>
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            Ticks {hl.clip_start_tick} - {hl.clip_end_tick} ({dur}s)
                          </div>
                        </div>

                        <button
                          className="btn btn-secondary"
                          onClick={() => onRemoveHighlight(hl.id)}
                          style={{ padding: '4px 8px', fontSize: '11px', color: 'var(--accent-red)' }}
                          title="Remove from queue"
                        >
                          ✕
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {activeTab === 'history' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '440px', overflowY: 'auto' }}>
              {/* Batch Monitor Dashboard */}
              {historyJobs.length > 0 && (() => {
                const total = historyJobs.length
                const pending = historyJobs.filter((j) => j.status === 'pending').length
                const running = historyJobs.filter((j) => j.status === 'running').length
                const completed = historyJobs.filter((j) => j.status === 'completed').length
                const failed = historyJobs.filter((j) => j.status === 'failed').length
                const isBatchActive = pending > 0 || running > 0
                const progressPct = total > 0 ? Math.round(((completed + failed) / total) * 100) : 0

                return (
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      padding: '12px 16px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ fontWeight: 700, fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>📊 Batch Monitor</span>
                        <span style={{ fontSize: '11px', color: 'var(--text-faint)' }}>({total} total jobs)</span>
                      </div>

                      {failed > 0 && (
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={handleRetryFailedBatch}
                          disabled={isRetrying || isBatchActive}
                          style={{ padding: '3px 10px', fontSize: '11px', color: '#f87171', border: '1px solid rgba(248, 113, 113, 0.3)' }}
                        >
                          {isRetrying ? 'Retrying...' : `🔄 Retry Failed (${failed})`}
                        </button>
                      )}
                    </div>

                    {/* Metric Pills */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px', textAlign: 'center' }}>
                      <div style={{ backgroundColor: 'var(--bg-card)', padding: '4px 6px', borderRadius: '4px', border: '1px solid var(--border)' }}>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>PENDING</div>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#f59e0b' }}>{pending}</div>
                      </div>
                      <div style={{ backgroundColor: 'var(--bg-card)', padding: '4px 6px', borderRadius: '4px', border: '1px solid var(--border)' }}>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>RUNNING</div>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8' }}>{running}</div>
                      </div>
                      <div style={{ backgroundColor: 'var(--bg-card)', padding: '4px 6px', borderRadius: '4px', border: '1px solid var(--border)' }}>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>COMPLETED</div>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#34d399' }}>{completed}</div>
                      </div>
                      <div style={{ backgroundColor: 'var(--bg-card)', padding: '4px 6px', borderRadius: '4px', border: '1px solid var(--border)' }}>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>FAILED</div>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#f87171' }}>{failed}</div>
                      </div>
                    </div>

                    {/* Overall Progress Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                        <span>
                          {isBatchActive
                            ? `Processing: ${completed + failed} of ${total} finished`
                            : failed === 0
                            ? `✓ All ${completed} clips successfully rendered`
                            : `Finished with ${failed} failure(s)`}
                        </span>
                        <span className="num" style={{ fontWeight: 700 }}>{progressPct}%</span>
                      </div>
                      <div style={{ height: '5px', backgroundColor: 'var(--bg-surface)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${progressPct}%`,
                            height: '100%',
                            backgroundColor: failed > 0 && !isBatchActive ? '#f59e0b' : completed === total ? '#34d399' : '#38bdf8',
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })()}

              {/* Highlight Montage Section */}
              {historyJobs.some((j) => j.status === 'completed') && (
                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    border: '1px solid rgba(234, 179, 8, 0.4)',
                    borderRadius: '8px',
                    padding: '14px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>🎬 Montage Compiler (Объединение клипов в 1 видео)</span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Объединяет отрендеренные MP4 со звуком в единый плавный ролик без пережатия (FFmpeg concat).
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
                        <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                          Выбрано клипов: <strong style={{ color: '#38bdf8' }}>{selectedMontageJobIds.size}</strong> из {historyJobs.filter((j) => j.status === 'completed').length}
                        </span>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={handleSelectAllMontageJobs}
                          style={{ padding: '2px 8px', fontSize: '10px' }}
                        >
                          Выбрать все
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={handleClearMontageSelection}
                          style={{ padding: '2px 8px', fontSize: '10px' }}
                        >
                          Снять выбор
                        </button>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleCreateMontage}
                      disabled={montageState.isCreating || selectedMontageJobIds.size === 0}
                      style={{ padding: '6px 14px', fontSize: '12px', fontWeight: 600, whiteSpace: 'nowrap' }}
                    >
                      {montageState.isCreating ? '⏳ Сборка монтажа...' : `🎬 Собрать монтаж (${selectedMontageJobIds.size} клипов)`}
                    </button>
                  </div>

                  {montageState.error && (
                    <div style={{ padding: '8px 10px', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: '6px', fontSize: '12px', color: '#f87171' }}>
                      ⚠️ {montageState.error}
                    </div>
                  )}

                  {montageState.montage && (
                    <div style={{ marginTop: '4px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: '#34d399' }}>
                          ✓ Единый ролик готов: {montageState.montage.filename} ({montageState.montage.duration_seconds.toFixed(1)} сек, {montageState.montage.total_clips} клипов)
                        </span>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() =>
                              setActiveModalVideo({
                                url: `/api/montage/${montageState.montage!.filename}`,
                                title: montageState.montage!.filename,
                                subtitle: `Full Montage (${montageState.montage!.duration_seconds.toFixed(1)}s, ${montageState.montage!.total_clips} clips)`,
                              })
                            }
                            style={{ padding: '3px 10px', fontSize: '11px', color: '#38bdf8' }}
                          >
                            ▶ Смотреть в плеере
                          </button>
                          <a
                            href={`/api/montage/${montageState.montage.filename}`}
                            download
                            className="btn btn-secondary"
                            style={{ padding: '3px 10px', fontSize: '11px', color: 'var(--text-main)', textDecoration: 'none' }}
                          >
                            ⬇ Скачать монтаж
                          </a>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Action bar for History */}
              {historyJobs.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleClearCompleted}
                    disabled={!historyJobs.some((j) => j.status === 'completed' || j.status === 'failed' || j.status === 'cancelled')}
                    style={{ padding: '4px 10px', fontSize: '11px', color: '#94a3b8' }}
                  >
                    🗑 Очистить завершенные
                  </button>
                </div>
              )}

              {historyJobs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '13px' }}>
                  No render jobs have been submitted for this demo yet.
                </div>
              ) : (
                historyJobs.map((job) => (
                  <div
                    key={job.id}
                    style={{
                      backgroundColor: 'var(--bg-card)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      padding: '14px',
                    }}
                  >
                    {(() => {
                      let parsedSettings: any = null
                      if (job.settings_json) {
                        try {
                          parsedSettings = JSON.parse(job.settings_json)
                        } catch {
                          // Ignore json parse error
                        }
                      }
                      return (
                        <>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              {job.status === 'completed' && (
                                <input
                                  type="checkbox"
                                  checked={selectedMontageJobIds.has(job.id)}
                                  onChange={() => handleToggleMontageJob(job.id)}
                                  title="Включить в единый монтаж"
                                  style={{ cursor: 'pointer', accentColor: '#38bdf8', width: '15px', height: '15px' }}
                                />
                              )}
                              <span style={{ fontWeight: 600, fontSize: '13px' }}>Job #{job.id.slice(0, 8)}</span>
                              {getStatusBadge(job.status)}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontSize: '11px', color: 'var(--text-faint)' }}>
                                {new Date(job.created_at).toLocaleTimeString()}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleDeleteJob(job.id)}
                                title="Удалить задачу"
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  color: 'var(--text-muted)',
                                  fontSize: '13px',
                                  cursor: 'pointer',
                                  padding: '2px 6px',
                                  borderRadius: '4px',
                                  lineHeight: 1,
                                }}
                                onMouseEnter={(e) => (e.currentTarget.style.color = '#f87171')}
                                onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                              >
                                ✕
                              </button>
                            </div>
                          </div>

                          {parsedSettings && (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                              <span style={{ backgroundColor: 'var(--bg-app)', padding: '2px 6px', borderRadius: '4px' }}>
                                POV: <strong style={{ color: 'var(--text-main)' }}>{parsedSettings.perspective || 'attacker'}</strong>
                              </span>
                              <span style={{ backgroundColor: 'var(--bg-app)', padding: '2px 6px', borderRadius: '4px' }}>
                                X-Ray: <strong style={{ color: parsedSettings.xray !== false ? '#34d399' : '#f87171' }}>{parsedSettings.xray !== false ? 'ON' : 'OFF'}</strong>
                              </span>
                              <span style={{ backgroundColor: 'var(--bg-app)', padding: '2px 6px', borderRadius: '4px' }}>
                                HUD: <strong style={{ color: 'var(--text-main)' }}>{(parsedSettings.hud_mode || 'full').replace('_', ' ')}</strong>
                              </span>
                            </div>
                          )}
                        </>
                      )
                    })()}

                    {job.status === 'running' && (
                      <div style={{ marginBottom: '8px' }}>
                        <div style={{ height: '4px', backgroundColor: 'var(--bg-app)', borderRadius: '2px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: '60%',
                              height: '100%',
                              backgroundColor: '#38bdf8',
                              transition: 'width 0.3s ease',
                            }}
                          />
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                          Launching CS2 with HLAE hook and capturing hardware video buffer...
                        </div>
                      </div>
                    )}

                    {job.status === 'completed' && job.output_path && (
                      <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <span style={{ fontSize: '12px', fontWeight: 600, color: '#34d399' }}>
                            ✓ Clip Ready (H.264 + AAC Audio)
                          </span>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() => {
                                const filename = job.output_path ? job.output_path.split(/[\\/]/).pop() || `Job #${job.id.slice(0, 8)}` : `Job #${job.id.slice(0, 8)}`
                                setActiveModalVideo({
                                  url: `/api/videos/${job.id}`,
                                  title: filename,
                                  subtitle: `Clip ID: ${job.id.slice(0, 8)} • 1080p60 H.264 + AAC`,
                                })
                              }}
                              style={{ padding: '3px 10px', fontSize: '11px', color: '#38bdf8' }}
                            >
                              ▶ Смотреть в плеере
                            </button>
                            <a
                              href={`/api/videos/${job.id}`}
                              download
                              className="btn btn-secondary"
                              style={{ padding: '3px 10px', fontSize: '11px', color: 'var(--text-main)', textDecoration: 'none' }}
                            >
                              ⬇ Download
                            </a>
                          </div>
                        </div>

                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          File: <code style={{ color: 'var(--accent-gold)', backgroundColor: 'var(--bg-app)', padding: '2px 6px', borderRadius: '4px' }}>{job.output_path}</code>
                        </div>
                      </div>
                    )}

                    {job.status === 'failed' && (
                      <div style={{ marginTop: '8px', padding: '8px 10px', backgroundColor: 'rgba(239, 68, 68, 0.08)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                        <div style={{ fontSize: '12px', color: '#f87171', marginBottom: '6px' }}>
                          ⚠️ {job.error_summary || 'Unknown rendering failure'}
                        </div>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={() => handleRetrySingle(job.id)}
                          disabled={isRetrying}
                          style={{ padding: '3px 8px', fontSize: '11px', color: 'var(--text-main)' }}
                        >
                          {isRetrying ? 'Retrying...' : '🔄 Retry this task'}
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          {activeTab === 'queue' && selectedHighlights.length > 0 && (
            <button
              className="btn btn-secondary"
              onClick={onClearAll}
              disabled={isSubmitting}
              style={{ marginRight: 'auto' }}
            >
              Clear All
            </button>
          )}

          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>

          {activeTab === 'queue' && selectedHighlights.length > 0 && (
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Queueing Jobs...' : `Render ${selectedHighlights.length} ${selectedHighlights.length === 1 ? 'Highlight' : 'Highlights'}`}
            </button>
          )}
        </div>
      </div>

      {/* Advanced Video Player Modal */}
      <VideoPlayerModal
        isOpen={!!activeModalVideo}
        onClose={() => setActiveModalVideo(null)}
        videoUrl={activeModalVideo?.url || ''}
        title={activeModalVideo?.title || 'Clip Preview'}
        subtitle={activeModalVideo?.subtitle}
      />
    </div>
  )
}
