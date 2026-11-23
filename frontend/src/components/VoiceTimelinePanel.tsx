import React, { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api'
import type { RoundVoiceTimelineDTO } from '../types'
import { useTranslation } from '../i18n'

interface VoiceTimelinePanelProps {
  demoId: number
  roundNum: number
  currentTick: number
  startTick: number
  endTick: number
  tickrate?: number
  isPlaying: boolean
  onJumpToTick?: (tick: number) => void
}

export const VoiceTimelinePanel: React.FC<VoiceTimelinePanelProps> = ({
  demoId,
  roundNum,
  currentTick,
  startTick,
  endTick,
  tickrate = 128,
  isPlaying,
  onJumpToTick,
}) => {
  const { lang } = useTranslation()
  const [timelineData, setTimelineData] = useState<RoundVoiceTimelineDTO | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Track playback controls state
  const [mutedSpeakers, setMutedSpeakers] = useState<Set<string>>(new Set())
  const [soloSpeakers, setSoloSpeakers] = useState<Set<string>>(new Set())
  const [trackVolumes, setTrackVolumes] = useState<Record<string, number>>({})

  // Audio elements map for synchronized audio preview
  const audioRefs = useRef<Map<string, HTMLAudioElement>>(new Map())

  // Total round duration in seconds
  const totalRoundTicks = Math.max(1, endTick - startTick)
  const totalRoundSec = Math.max(1, totalRoundTicks / tickrate)
  const playheadPercent = Math.min(100, Math.max(0, ((currentTick - startTick) / totalRoundTicks) * 100))

  useEffect(() => {
    let isSubscribed = true
    setIsLoading(true)
    setError(null)

    api
      .getRoundVoice(demoId, roundNum)
      .then((data) => {
        if (!isSubscribed) return
        setTimelineData(data)
        setIsLoading(false)
      })
      .catch((err) => {
        if (!isSubscribed) return
        console.error('Failed to load round voice data:', err)
        setError(err?.message || 'Voice loading error')
        setIsLoading(false)
      })

    return () => {
      isSubscribed = false
    }
  }, [demoId, roundNum])

  const toggleMute = (steamid: string) => {
    setMutedSpeakers((prev) => {
      const next = new Set(prev)
      if (next.has(steamid)) {
        next.delete(steamid)
      } else {
        next.add(steamid)
      }
      return next
    })
  }

  const toggleSolo = (steamid: string) => {
    setSoloSpeakers((prev) => {
      const next = new Set(prev)
      if (next.has(steamid)) {
        next.delete(steamid)
      } else {
        next.add(steamid)
      }
      return next
    })
  }

  const setVolume = (steamid: string, val: number) => {
    setTrackVolumes((prev) => ({ ...prev, [steamid]: val }))
    const audio = audioRefs.current.get(steamid)
    if (audio) {
      audio.volume = val
    }
  }

  // Determine if a track should currently play sound based on solo and mute states
  const isTrackAudible = (steamid: string): boolean => {
    if (soloSpeakers.size > 0) {
      return soloSpeakers.has(steamid)
    }
    return !mutedSpeakers.has(steamid)
  }

  const tracks = useMemo(() => {
    return timelineData?.tracks || []
  }, [timelineData])

  // Synchronized audio playback with replay scrubber
  useEffect(() => {
    tracks.forEach((track) => {
      let audio = audioRefs.current.get(track.steamid)
      if (!audio) {
        audio = new Audio(track.stream_url)
        audioRefs.current.set(track.steamid, audio)
      }
      const audible = isTrackAudible(track.steamid)
      const vol = trackVolumes[track.steamid] ?? 1.0
      audio.volume = audible ? vol : 0.0

      if (isPlaying && audible) {
        const elapsed = (currentTick - startTick) / tickrate
        if (Math.abs(audio.currentTime - elapsed) > 0.6) {
          audio.currentTime = Math.max(0, elapsed)
        }
        audio.play().catch(() => {})
      } else {
        audio.pause()
      }
    })
  }, [isPlaying, currentTick, startTick, tickrate, tracks, soloSpeakers, mutedSpeakers, trackVolumes])

  useEffect(() => {
    return () => {
      audioRefs.current.forEach((audio) => {
        audio.pause()
      })
      audioRefs.current.clear()
    }
  }, [])

  if (isLoading) {
    return (
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: '#0c1017',
          borderRadius: '8px',
          border: '1px solid #1a2233',
          color: '#94a3b8',
          fontSize: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span style={{ animation: 'spin 1s linear infinite' }}>⏳</span>
        <span>{lang === 'ru' ? 'Сканирование аудио-пакетов коммуникации...' : 'Scanning voice communication packets...'}</span>
      </div>
    )
  }

  if (error || !timelineData?.has_voice || tracks.length === 0) {
    return (
      <div
        style={{
          padding: '10px 14px',
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          borderRadius: '8px',
          border: '1px solid rgba(51, 65, 85, 0.4)',
          color: '#94a3b8',
          fontSize: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <span style={{ fontSize: '15px' }}>🔇</span>
        <div>
          <span style={{ fontWeight: 600, color: '#cbd5e1' }}>
            {lang === 'ru' ? 'Голосовой чат в демке не обнаружен' : 'No in-game voice data in demo'}
          </span>
          <span style={{ display: 'block', fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
            {lang === 'ru'
              ? 'В официальных записях Valve MM/Premier аудиопоток чата вырезается сервером для конфиденциальности. Войс сохраняется на демках FACEIT, Fastcup и серверах с включенным tv_record_voice.'
              : 'Valve MM/Premier servers omit voice chat streams for privacy. In-demo voice is preserved on FACEIT, tournament, and community servers with tv_record_voice enabled.'}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div
      style={{
        backgroundColor: '#0a0d14',
        borderRadius: '8px',
        border: '1px solid #1a2233',
        padding: '12px 14px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      {/* Panel Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '15px' }}>🎙️</span>
          <span style={{ fontSize: '13px', fontWeight: 800, color: '#f8fafc' }}>
            {lang === 'ru' ? 'Voice Timeline — Переговоры игроков' : 'Voice Timeline — Team Comms'}
          </span>
          <span
            style={{
              backgroundColor: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              fontSize: '11px',
              fontWeight: 700,
              padding: '1px 7px',
              borderRadius: '10px',
              border: '1px solid rgba(56, 189, 248, 0.3)',
            }}
          >
            {tracks.length} {lang === 'ru' ? 'спикеров' : 'speakers'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {soloSpeakers.size > 0 && (
            <button
              type="button"
              onClick={() => setSoloSpeakers(new Set())}
              style={{
                background: 'rgba(234, 179, 8, 0.2)',
                border: '1px solid #eab308',
                borderRadius: '4px',
                color: '#eab308',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 6px',
                cursor: 'pointer',
              }}
            >
              {lang === 'ru' ? 'Сброс Solo' : 'Reset Solo'}
            </button>
          )}
          {mutedSpeakers.size > 0 && (
            <button
              type="button"
              onClick={() => setMutedSpeakers(new Set())}
              style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid #ef4444',
                borderRadius: '4px',
                color: '#ef4444',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 6px',
                cursor: 'pointer',
              }}
            >
              {lang === 'ru' ? 'Включить всех' : 'Unmute All'}
            </button>
          )}
        </div>
      </div>

      {/* Multi-Track Stack */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        {tracks.map((track) => {
          const isCT = track.team === 'ct'
          const teamColor = isCT ? '#38bdf8' : '#fb923c'
          const isMuted = mutedSpeakers.has(track.steamid)
          const isSolo = soloSpeakers.has(track.steamid)
          const volume = trackVolumes[track.steamid] ?? 1.0

          // Check if this speaker is actively talking at the current playback tick
          const isSpeakingNow = track.segments.some(
            (seg) => currentTick >= seg.start_tick && currentTick <= seg.end_tick
          )

          return (
            <div
              key={track.steamid}
              style={{
                display: 'grid',
                gridTemplateColumns: '215px 1fr 28px',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: isSpeakingNow ? 'rgba(30, 41, 59, 0.65)' : '#0d131f',
                padding: '4px 8px',
                borderRadius: '6px',
                border: `1px solid ${isSpeakingNow ? teamColor : '#172033'}`,
                transition: 'all 0.12s ease',
              }}
            >
              {/* Speaker Label & Channel Controls */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden' }}>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 800,
                    padding: '1px 4px',
                    borderRadius: '3px',
                    backgroundColor: `${teamColor}25`,
                    color: teamColor,
                    border: `1px solid ${teamColor}50`,
                  }}
                >
                  {isCT ? 'CT' : 'T'}
                </span>

                <span
                  title={`${track.player_name || track.steamid} (~${track.duration_sec}s voice)`}
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: isMuted ? '#64748b' : '#f1f5f9',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    flex: 1,
                  }}
                >
                  {track.player_name || track.steamid.slice(-6)}
                </span>

                {/* Solo Button [S] */}
                <button
                  type="button"
                  onClick={() => toggleSolo(track.steamid)}
                  title={lang === 'ru' ? 'Соло: слушать только этого игрока' : 'Solo: listen to this player only'}
                  style={{
                    width: '18px',
                    height: '18px',
                    padding: 0,
                    borderRadius: '3px',
                    fontSize: '10px',
                    fontWeight: 800,
                    cursor: 'pointer',
                    backgroundColor: isSolo ? '#eab308' : '#1e293b',
                    color: isSolo ? '#000000' : '#94a3b8',
                    border: `1px solid ${isSolo ? '#facc15' : '#334155'}`,
                  }}
                >
                  S
                </button>

                {/* Mute Button [M] */}
                <button
                  type="button"
                  onClick={() => toggleMute(track.steamid)}
                  title={lang === 'ru' ? 'Заглушить этого игрока' : 'Mute this player'}
                  style={{
                    width: '18px',
                    height: '18px',
                    padding: 0,
                    borderRadius: '3px',
                    fontSize: '10px',
                    fontWeight: 800,
                    cursor: 'pointer',
                    backgroundColor: isMuted ? '#ef4444' : '#1e293b',
                    color: isMuted ? '#ffffff' : '#94a3b8',
                    border: `1px solid ${isMuted ? '#f87171' : '#334155'}`,
                  }}
                >
                  M
                </button>

                {/* Volume Slider */}
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={volume}
                  onChange={(e) => setVolume(track.steamid, parseFloat(e.target.value))}
                  title={`${Math.round(volume * 100)}%`}
                  style={{
                    width: '36px',
                    height: '4px',
                    accentColor: teamColor,
                    cursor: 'pointer',
                  }}
                />
              </div>

              {/* Waveform / Speech Activity Track */}
              <div
                style={{
                  position: 'relative',
                  height: '20px',
                  backgroundColor: '#070a10',
                  borderRadius: '4px',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  border: '1px solid #141b2b',
                }}
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect()
                  const clickFrac = (e.clientX - rect.left) / rect.width
                  const targetTick = Math.floor(startTick + clickFrac * totalRoundTicks)
                  onJumpToTick?.(targetTick)
                }}
              >
                {/* Speech Burst Blocks */}
                {track.segments.map((seg, idx) => {
                  const leftPct = Math.min(100, Math.max(0, (seg.start_sec / totalRoundSec) * 100))
                  const widthPct = Math.max(1.2, ((seg.end_sec - seg.start_sec) / totalRoundSec) * 100)
                  const isActiveNow = currentTick >= seg.start_tick && currentTick <= seg.end_tick

                  return (
                    <div
                      key={idx}
                      title={`${track.player_name}: ${seg.start_sec}s - ${seg.end_sec}s`}
                      style={{
                        position: 'absolute',
                        left: `${leftPct}%`,
                        width: `${widthPct}%`,
                        top: '2px',
                        bottom: '2px',
                        backgroundColor: isActiveNow ? '#ffffff' : teamColor,
                        opacity: isMuted ? 0.25 : isActiveNow ? 1.0 : 0.75,
                        borderRadius: '2px',
                        boxShadow: isActiveNow ? `0 0 8px ${teamColor}` : 'none',
                        transition: 'background-color 0.1s ease',
                      }}
                    />
                  )
                })}

                {/* Real-time Playhead Scrubber Cursor */}
                <div
                  style={{
                    position: 'absolute',
                    left: `${playheadPercent}%`,
                    top: 0,
                    bottom: 0,
                    width: '1.5px',
                    backgroundColor: '#ef4444',
                    boxShadow: '0 0 6px #ef4444',
                    pointerEvents: 'none',
                    zIndex: 5,
                  }}
                />
              </div>

              {/* WAV Export Icon */}
              <a
                href={track.download_wav_url}
                download
                title={lang === 'ru' ? 'Скачать изолированный голос игрока в WAV' : 'Download isolated player voice WAV'}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#64748b',
                  fontSize: '12px',
                  textDecoration: 'none',
                  padding: '2px',
                  borderRadius: '3px',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#38bdf8')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#64748b')}
              >
                💾
              </a>
            </div>
          )
        })}
      </div>
    </div>
  )
}
