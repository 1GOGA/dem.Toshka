import React, { useEffect, useRef, useState, useCallback } from 'react'

export interface VideoPlayerModalProps {
  isOpen: boolean
  onClose: () => void
  videoUrl: string
  title: string
  subtitle?: string
  clipMetadata?: {
    duration?: number
    resolution?: string
    fps?: number
    roundNum?: number
    playerName?: string
    weapon?: string
  }
}

export const VideoPlayerModal: React.FC<VideoPlayerModalProps> = ({
  isOpen,
  onClose,
  videoUrl,
  title,
  subtitle,
  clipMetadata,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const timelineRef = useRef<HTMLDivElement | null>(null)

  // Player states
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [bufferedEnd, setBufferedEnd] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1)
  const [isLooping, setIsLooping] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isBuffering, setIsBuffering] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const [showShortcuts, setShowShortcuts] = useState(false)

  // 4:3 Cyber-sport aspect ratio and stretch toggle
  const [videoAspectRatio, setVideoAspectRatio] = useState<string>('16 / 9')
  const [is43Stretched, setIs43Stretched] = useState(false)
  const [isNative43, setIsNative43] = useState(false)

  // Timeline hover & scrubbing
  const [isDraggingSeek, setIsDraggingSeek] = useState(false)
  const [hoverTime, setHoverTime] = useState<number | null>(null)
  const [hoverPositionX, setHoverPositionX] = useState(0)

  // Center ripple animation for actions
  const [ripple, setRipple] = useState<{
    text: string
    icon: 'play' | 'pause' | 'rewind' | 'forward' | 'frame-prev' | 'frame-next'
    key: number
  } | null>(null)

  const controlsTimeoutRef = useRef<number | null>(null)

  const triggerRipple = (text: string, icon: 'play' | 'pause' | 'rewind' | 'forward' | 'frame-prev' | 'frame-next') => {
    setRipple({ text, icon, key: Date.now() })
  }

  // Handle Autohide controls
  const resetControlsTimeout = useCallback(() => {
    setShowControls(true)
    if (controlsTimeoutRef.current) {
      window.clearTimeout(controlsTimeoutRef.current)
    }
    if (isPlaying) {
      controlsTimeoutRef.current = window.setTimeout(() => {
        setShowControls(false)
      }, 2500)
    }
  }, [isPlaying])

  // Play / Pause toggle
  const togglePlay = useCallback(() => {
    const v = videoRef.current
    if (!v) return
    if (v.paused) {
      v.play()
        .then(() => {
          setIsPlaying(true)
          triggerRipple('Воспроизведение', 'play')
        })
        .catch((e) => console.warn('Play interrupted:', e))
    } else {
      v.pause()
      setIsPlaying(false)
      triggerRipple('Пауза', 'pause')
    }
  }, [])

  // Seeking helpers
  const seekRelative = useCallback((seconds: number) => {
    const v = videoRef.current
    if (!v) return
    const target = Math.max(0, Math.min(v.duration || 0, v.currentTime + seconds))
    v.currentTime = target
    setCurrentTime(target)
    if (seconds < 0) {
      triggerRipple(`${seconds}s`, 'rewind')
    } else {
      triggerRipple(`+${seconds}s`, 'forward')
    }
  }, [])

  const stepFrame = useCallback((direction: 'next' | 'prev') => {
    const v = videoRef.current
    if (!v) return
    v.pause()
    setIsPlaying(false)
    const frameDuration = 1 / 60 // 60 FPS CS2 highlight standard
    const target =
      direction === 'next'
        ? Math.min(v.duration || 0, v.currentTime + frameDuration)
        : Math.max(0, v.currentTime - frameDuration)
    v.currentTime = target
    setCurrentTime(target)
    triggerRipple(direction === 'next' ? '+1 кадр' : '-1 кадр', direction === 'next' ? 'frame-next' : 'frame-prev')
  }, [])

  // Volume toggle & slider
  const handleVolumeChange = (newVol: number) => {
    const v = videoRef.current
    if (!v) return
    const clamped = Math.max(0, Math.min(1, newVol))
    v.volume = clamped
    setVolume(clamped)
    if (clamped > 0 && isMuted) {
      v.muted = false
      setIsMuted(false)
    }
  }

  const toggleMute = () => {
    const v = videoRef.current
    if (!v) return
    const target = !isMuted
    v.muted = target
    setIsMuted(target)
  }

  // Playback rate
  const changeSpeed = (rate: number) => {
    const v = videoRef.current
    if (!v) return
    v.playbackRate = rate
    setPlaybackRate(rate)
  }

  // Fullscreen toggle
  const toggleFullscreen = () => {
    const container = containerRef.current
    if (!container) return
    if (!document.fullscreenElement) {
      container.requestFullscreen().then(() => setIsFullscreen(true)).catch(console.warn)
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(console.warn)
    }
  }

  // PiP mode
  const togglePiP = async () => {
    const v = videoRef.current
    if (!v) return
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture()
      } else if (document.pictureInPictureEnabled) {
        await v.requestPictureInPicture()
      }
    } catch (e) {
      console.warn('PiP error:', e)
    }
  }

  // Loop toggle
  const toggleLoop = () => {
    const v = videoRef.current
    if (!v) return
    const target = !isLooping
    v.loop = target
    setIsLooping(target)
  }

  // Time format: MM:SS.s
  const formatTime = (seconds: number) => {
    if (isNaN(seconds) || seconds < 0) return '00:00.0'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    const tenths = Math.floor((seconds % 1) * 10)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${tenths}`
  }

  const hoverRafRef = useRef<number | null>(null)
  const lastContainerMouseMoveRef = useRef<number>(0)
  const lastTimeUpdateRef = useRef<number>(0)
  const wasPlayingOnDragRef = useRef(false)
  const pendingTargetTimeRef = useRef<number | null>(null)

  const handleContainerMouseMove = () => {
    const now = performance.now()
    if (now - lastContainerMouseMoveRef.current > 150) {
      lastContainerMouseMoveRef.current = now
      resetControlsTimeout()
    }
  }

  const debounceSeekTimeoutRef = useRef<number | null>(null)

  // Timeline events: calculate time from pointer position
  const getTimelineTime = (e: React.MouseEvent<HTMLDivElement> | MouseEvent) => {
    if (!timelineRef.current || !videoRef.current) return null
    const rect = timelineRef.current.getBoundingClientRect()
    const clickX = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
    const ratio = rect.width > 0 ? clickX / rect.width : 0
    const target = ratio * (videoRef.current.duration || 0)
    return { target, clickX, ratio }
  }

  const safeSeekVideo = (v: HTMLVideoElement, target: number) => {
    try {
      const vAny = v as unknown as { fastSeek?: (t: number) => void; currentTime: number }
      if (typeof vAny.fastSeek === 'function') {
        vAny.fastSeek(target)
      } else {
        v.currentTime = target
      }
    } catch {
      v.currentTime = target
    }
  }

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDraggingSeek) return
    const res = getTimelineTime(e)
    if (!res || !videoRef.current) return
    safeSeekVideo(videoRef.current, res.target)
    setCurrentTime(res.target)
  }

  const handleTimelineMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDraggingSeek(true)
    const v = videoRef.current
    if (v && !v.paused) {
      wasPlayingOnDragRef.current = true
      v.pause()
    } else {
      wasPlayingOnDragRef.current = false
    }
    const res = getTimelineTime(e)
    if (res) {
      pendingTargetTimeRef.current = res.target
      setCurrentTime(res.target)
      setHoverPositionX(res.clickX)
      setHoverTime(res.target)
    }
  }

  const handleTimelineMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDraggingSeek) return // Handled by global listener for seamless drag outside bar
    const clientX = e.clientX
    if (hoverRafRef.current) return
    hoverRafRef.current = requestAnimationFrame(() => {
      hoverRafRef.current = null
      if (!timelineRef.current || !videoRef.current) return
      const rect = timelineRef.current.getBoundingClientRect()
      const clickX = Math.max(0, Math.min(clientX - rect.left, rect.width))
      const ratio = rect.width > 0 ? clickX / rect.width : 0
      const target = ratio * (videoRef.current.duration || 0)
      setHoverTime(target)
      setHoverPositionX(clickX)
    })
  }

  const handleTimelineMouseLeave = () => {
    if (hoverRafRef.current) {
      cancelAnimationFrame(hoverRafRef.current)
      hoverRafRef.current = null
    }
    if (!isDraggingSeek) {
      setHoverTime(null)
    }
  }

  // Global mouse up & mouse move for seek dragging
  useEffect(() => {
    if (!isDraggingSeek) return

    const handleGlobalMouseUp = () => {
      setIsDraggingSeek(false)
      setHoverTime(null)
      if (debounceSeekTimeoutRef.current) {
        window.clearTimeout(debounceSeekTimeoutRef.current)
        debounceSeekTimeoutRef.current = null
      }
      const v = videoRef.current
      if (v && pendingTargetTimeRef.current !== null) {
        safeSeekVideo(v, pendingTargetTimeRef.current)
        setCurrentTime(pendingTargetTimeRef.current)
        if (wasPlayingOnDragRef.current) {
          v.play().catch(() => {})
        }
        pendingTargetTimeRef.current = null
      }
    }

    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (!timelineRef.current || !videoRef.current) return
      const rect = timelineRef.current.getBoundingClientRect()
      const clickX = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
      const ratio = rect.width > 0 ? clickX / rect.width : 0
      const target = ratio * (videoRef.current.duration || 0)
      pendingTargetTimeRef.current = target
      setCurrentTime(target)
      setHoverPositionX(clickX)
      setHoverTime(target)

      // Only seek video preview if cursor pauses in place for >220ms
      if (debounceSeekTimeoutRef.current) {
        window.clearTimeout(debounceSeekTimeoutRef.current)
      }
      debounceSeekTimeoutRef.current = window.setTimeout(() => {
        if (videoRef.current && !videoRef.current.seeking) {
          safeSeekVideo(videoRef.current, target)
        }
      }, 220)
    }

    window.addEventListener('mouseup', handleGlobalMouseUp)
    window.addEventListener('mousemove', handleGlobalMouseMove)
    return () => {
      window.removeEventListener('mouseup', handleGlobalMouseUp)
      window.removeEventListener('mousemove', handleGlobalMouseMove)
      if (debounceSeekTimeoutRef.current) {
        window.clearTimeout(debounceSeekTimeoutRef.current)
      }
    }
  }, [isDraggingSeek])

  // Fullscreen change listener
  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFsChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFsChange)
    }
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept when focusing inputs or textareas
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return

      switch (e.code) {
        case 'Space':
        case 'KeyK':
          e.preventDefault()
          togglePlay()
          break
        case 'ArrowLeft':
        case 'KeyJ':
          e.preventDefault()
          seekRelative(e.shiftKey ? -5 : -2)
          break
        case 'ArrowRight':
        case 'KeyL':
          e.preventDefault()
          seekRelative(e.shiftKey ? 5 : 2)
          break
        case 'Comma':
          e.preventDefault()
          stepFrame('prev')
          break
        case 'Period':
          e.preventDefault()
          stepFrame('next')
          break
        case 'ArrowUp':
          e.preventDefault()
          handleVolumeChange(volume + 0.1)
          break
        case 'ArrowDown':
          e.preventDefault()
          handleVolumeChange(volume - 0.1)
          break
        case 'KeyM':
          e.preventDefault()
          toggleMute()
          break
        case 'KeyF':
          e.preventDefault()
          toggleFullscreen()
          break
        case 'KeyR':
          e.preventDefault()
          toggleLoop()
          break
        case 'KeyS':
          if (isNative43) {
            e.preventDefault()
            setIs43Stretched((prev) => {
              const next = !prev
              triggerRipple(next ? '↔️ 4:3 Stretched (16:9)' : '🎯 4:3 Native (Black bars)', 'play')
              return next
            })
          }
          break
        case 'Escape':
          e.preventDefault()
          if (showShortcuts) {
            setShowShortcuts(false)
          } else if (document.fullscreenElement) {
            document.exitFullscreen().catch(console.warn)
          } else {
            onClose()
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [
    isOpen,
    togglePlay,
    seekRelative,
    stepFrame,
    volume,
    isMuted,
    showShortcuts,
    isNative43,
    onClose,
  ])

  // Video element events
  const onTimeUpdate = () => {
    const v = videoRef.current
    if (!v) return
    const now = performance.now()
    if (now - lastTimeUpdateRef.current > 200 || v.paused) {
      lastTimeUpdateRef.current = now
      setCurrentTime(v.currentTime)
      if (v.buffered.length > 0) {
        setBufferedEnd(v.buffered.end(v.buffered.length - 1))
      }
    }
  }

  const onLoadedMetadata = () => {
    const v = videoRef.current
    if (!v) return
    setDuration(v.duration || 0)
    setIsPlaying(!v.paused)
    v.volume = volume

    if (v.videoWidth && v.videoHeight) {
      const ratio = v.videoWidth / v.videoHeight
      if (
        Math.abs(ratio - 4 / 3) < 0.08 ||
        (v.videoWidth === 1280 && v.videoHeight === 960) ||
        (v.videoWidth === 1024 && v.videoHeight === 768) ||
        (v.videoWidth === 1440 && v.videoHeight === 1080)
      ) {
        setVideoAspectRatio('4 / 3')
        setIsNative43(true)
      } else {
        setVideoAspectRatio('16 / 9')
        setIsNative43(false)
      }
    }
  }

  if (!isOpen) return null

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0
  const bufferedPercent = duration > 0 ? (bufferedEnd / duration) * 100 : 0

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 7, 12, 0.88)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        ref={containerRef}
        style={{
          backgroundColor: '#0d1017',
          border: '1px solid #28334a',
          borderRadius: isFullscreen ? 0 : '14px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.9), 0 0 40px rgba(56, 189, 248, 0.1)',
          width: isFullscreen ? '100vw' : '92%',
          maxWidth: isFullscreen ? 'none' : (!is43Stretched && videoAspectRatio === '4 / 3' ? '840px' : '1040px'),
          height: isFullscreen ? '100vh' : 'auto',
          maxHeight: isFullscreen ? 'none' : '94vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
        onMouseMove={handleContainerMouseMove}
      >
        {/* Top Header Bar */}
        <div
          style={{
            padding: '12px 20px',
            backgroundColor: '#121622',
            borderBottom: '1px solid #202738',
            display: isFullscreen && !showControls ? 'none' : 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            zIndex: 10,
            transition: 'opacity 0.25s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', overflow: 'hidden' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #38bdf8, #6366f1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 900,
                fontSize: '14px',
                color: '#fff',
                flexShrink: 0,
              }}
            >
              ▶
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div
                style={{
                  fontSize: '15px',
                  fontWeight: 700,
                  color: '#f1f5f9',
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                }}
              >
                {title}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: '#94a3b8' }}>
                {subtitle && <span>{subtitle}</span>}
                <span style={{ backgroundColor: '#1e2433', color: '#38bdf8', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                  {clipMetadata?.resolution || (isNative43 ? '1280x960 (4:3)' : '1080p (16:9)')} • 60 FPS
                </span>
                <span style={{ backgroundColor: '#1e2433', color: '#34d399', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                  AAC Stereo
                </span>
                {clipMetadata?.weapon && (
                  <span style={{ color: '#fbbf24', fontWeight: 600 }}>
                    {clipMetadata.weapon.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons in header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowShortcuts(!showShortcuts)}
              title="Горячие клавиши плеера"
              style={{ padding: '5px 10px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="4" width="20" height="16" rx="2" />
                <path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01M6 12h.01M10 12h.01M14 12h.01M18 12h.01M8 16h8" />
              </svg>
              Клавиши
            </button>

            <a
              href={videoUrl}
              download={title.endsWith('.mp4') ? title : `${title}.mp4`}
              className="btn btn-secondary"
              style={{ padding: '5px 12px', fontSize: '11px', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px' }}
              title="Скачать исходный MP4 файл"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
              </svg>
              Скачать
            </a>

            <button
              type="button"
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                fontSize: '20px',
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '6px',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#f1f5f9')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              title="Закрыть плеер (Esc)"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Video Canvas Container */}
        <div
          style={{
            position: 'relative',
            backgroundColor: '#000',
            aspectRatio: isFullscreen ? 'auto' : (is43Stretched ? '16 / 9' : videoAspectRatio),
            maxHeight: isFullscreen ? 'none' : 'calc(88vh - 160px)',
            width: '100%',
            flex: isFullscreen ? 1 : 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            cursor: isFullscreen && !showControls ? 'none' : 'default',
          }}
          onClick={togglePlay}
          onDoubleClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect()
            const clickXRatio = (e.clientX - rect.left) / rect.width
            if (clickXRatio < 0.3) {
              seekRelative(-5)
            } else if (clickXRatio > 0.7) {
              seekRelative(5)
            } else {
              toggleFullscreen()
            }
          }}
        >
          <video
            ref={videoRef}
            src={videoUrl}
            autoPlay
            playsInline
            preload="auto"
            onTimeUpdate={onTimeUpdate}
            onLoadedMetadata={onLoadedMetadata}
            onWaiting={() => setIsBuffering(true)}
            onPlaying={() => {
              setIsBuffering(false)
              setIsPlaying(true)
            }}
            onPause={() => setIsPlaying(false)}
            onEnded={() => {
              setIsPlaying(false)
              if (isLooping) {
                videoRef.current?.play()
              }
            }}
            style={{
              width: '100%',
              height: '100%',
              maxHeight: isFullscreen ? 'none' : 'calc(88vh - 160px)',
              objectFit: is43Stretched ? 'fill' : 'contain',
              backgroundColor: '#000',
              transform: 'translateZ(0)',
              willChange: 'transform',
            }}
          />

          {/* Buffering Indicator */}
          {isBuffering && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'rgba(0, 0, 0, 0.4)',
                zIndex: 4,
                pointerEvents: 'none',
              }}
            >
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  border: '4px solid rgba(56, 189, 248, 0.2)',
                  borderTopColor: '#38bdf8',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                }}
              />
            </div>
          )}

          {/* Action Ripple in Center */}
          {ripple && (
            <div
              key={ripple.key}
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                backgroundColor: 'rgba(15, 23, 42, 0.85)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                backdropFilter: 'blur(8px)',
                borderRadius: '50px',
                padding: '12px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                color: '#f1f5f9',
                fontSize: '15px',
                fontWeight: 700,
                pointerEvents: 'none',
                zIndex: 6,
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.6)',
                animation: 'fadeRipple 0.65s cubic-bezier(0.16, 1, 0.3, 1) forwards',
              }}
            >
              <span>{ripple.text}</span>
            </div>
          )}

          {/* Keyboard Shortcuts Cheat Sheet Modal Overlay */}
          {showShortcuts && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                backgroundColor: 'rgba(9, 12, 19, 0.92)',
                backdropFilter: 'blur(10px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 20,
              }}
              onClick={(e) => {
                e.stopPropagation()
                setShowShortcuts(false)
              }}
            >
              <div
                style={{
                  backgroundColor: '#161b28',
                  border: '1px solid #2d3852',
                  borderRadius: '12px',
                  padding: '24px',
                  maxWidth: '460px',
                  width: '90%',
                  boxShadow: '0 20px 40px rgba(0,0,0,0.8)',
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '16px', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                    ⌨️ Горячие клавиши плеера
                  </h4>
                  <button
                    type="button"
                    onClick={() => setShowShortcuts(false)}
                    style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '18px', cursor: 'pointer' }}
                  >
                    ✕
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '10px', fontSize: '12px' }}>
                  <span style={{ color: '#cbd5e1' }}>Воспроизведение / Пауза</span>
                  <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                    Пробел / K
                  </kbd>

                  <span style={{ color: '#cbd5e1' }}>Перемотка назад / вперед (2 сек)</span>
                  <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                    ← / → (J / L)
                  </kbd>

                  <span style={{ color: '#cbd5e1' }}>Быстрая перемотка (5 сек)</span>
                  <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                    Shift + ← / →
                  </kbd>

                  <span style={{ color: '#cbd5e1' }}>Покадровый шаг (-1 / +1 кадр 60fps)</span>
                  <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                    , (Б) / . (Ю)
                  </kbd>

                  <span style={{ color: '#cbd5e1' }}>Громкость громче / тише</span>
                  <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                    ↑ / ↓
                  </kbd>

                  <span style={{ color: '#cbd5e1' }}>Включить / отключить звук</span>
                  <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                    M
                  </kbd>

                  <span style={{ color: '#cbd5e1' }}>Полноэкранный режим</span>
                  <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                    F
                  </kbd>

                  <span style={{ color: '#cbd5e1' }}>Зациклить повтор (Loop)</span>
                  <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                    R
                  </kbd>

                  {isNative43 && (
                    <>
                      <span style={{ color: '#cbd5e1' }}>4:3 Stretched / Native</span>
                      <kbd style={{ backgroundColor: '#232b3e', padding: '2px 8px', borderRadius: '4px', border: '1px solid #3b4662', color: '#38bdf8' }}>
                        S
                      </kbd>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Bottom Controls Bar: in windowed mode sits below video in dedicated dock; in fullscreen overlaid */}
        <div
          style={
            isFullscreen
              ? {
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  padding: '24px 20px 14px 20px',
                  background:
                    'linear-gradient(to top, rgba(10, 13, 20, 0.96) 0%, rgba(10, 13, 20, 0.8) 70%, transparent 100%)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  opacity: showControls ? 1 : 0,
                  transition: 'opacity 0.25s ease-in-out',
                  pointerEvents: showControls ? 'auto' : 'none',
                  zIndex: 10,
                }
              : {
                  position: 'relative',
                  width: '100%',
                  padding: '12px 18px 14px 18px',
                  backgroundColor: '#10141f',
                  borderTop: '1px solid #202738',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  opacity: 1,
                  pointerEvents: 'auto',
                  zIndex: 10,
                }
          }
          onClick={(e) => e.stopPropagation()}
        >
            {/* Timeline Progress Bar */}
            <div
              ref={timelineRef}
              style={{
                position: 'relative',
                height: '8px',
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'height 0.15s ease',
              }}
              onClick={handleTimelineClick}
              onMouseDown={handleTimelineMouseDown}
              onMouseMove={handleTimelineMouseMove}
              onMouseLeave={handleTimelineMouseLeave}
            >
              {/* Buffered Bar */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  bottom: 0,
                  width: `${bufferedPercent}%`,
                  backgroundColor: 'rgba(255, 255, 255, 0.25)',
                  borderRadius: '4px',
                }}
              />

              {/* Played Bar */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  bottom: 0,
                  width: `${progressPercent}%`,
                  background: 'linear-gradient(90deg, #38bdf8, #818cf8)',
                  borderRadius: '4px',
                  boxShadow: '0 0 10px rgba(56, 189, 248, 0.6)',
                  transition: isDraggingSeek ? 'none' : 'width 0.2s linear',
                }}
              />

              {/* Scrubber Knob */}
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: `${progressPercent}%`,
                  transform: 'translate(-50%, -50%)',
                  width: '14px',
                  height: '14px',
                  backgroundColor: '#ffffff',
                  border: '2px solid #38bdf8',
                  borderRadius: '50%',
                  boxShadow: '0 2px 6px rgba(0, 0, 0, 0.6)',
                  pointerEvents: 'none',
                  transition: isDraggingSeek ? 'none' : 'left 0.2s linear',
                }}
              />

              {/* Time Hover Preview Badge */}
              {hoverTime !== null && (
                <div
                  style={{
                    position: 'absolute',
                    bottom: '16px',
                    left: `${hoverPositionX}px`,
                    transform: 'translateX(-50%)',
                    backgroundColor: '#1e2433',
                    border: '1px solid #38bdf8',
                    color: '#f1f5f9',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    pointerEvents: 'none',
                    whiteSpace: 'nowrap',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.6)',
                  }}
                >
                  {formatTime(hoverTime)}
                </div>
              )}
            </div>

            {/* Controls Button Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              {/* Left group: Play/Pause, Rewind/Forward, Frame Step, Timestamp */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {/* Play / Pause button */}
                <button
                  type="button"
                  onClick={togglePlay}
                  title={isPlaying ? 'Пауза (Пробел)' : 'Воспроизведение (Пробел)'}
                  style={{
                    width: '38px',
                    height: '38px',
                    borderRadius: '50%',
                    backgroundColor: '#38bdf8',
                    color: '#090d16',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    boxShadow: '0 2px 10px rgba(56, 189, 248, 0.4)',
                    transition: 'transform 0.15s ease, background-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.08)')}
                  onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
                >
                  {isPlaying ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <rect x="6" y="4" width="4" height="16" rx="1" />
                      <rect x="14" y="4" width="4" height="16" rx="1" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style={{ marginLeft: '2px' }}>
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                  )}
                </button>

                {/* Rewind -5s button */}
                <button
                  type="button"
                  onClick={() => seekRelative(-5)}
                  title="Назад на 5 секунд (←)"
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#cbd5e1',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '2px',
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '4px 6px',
                    borderRadius: '4px',
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 17l-5-5 5-5M18 17l-5-5 5-5" />
                  </svg>
                  -5s
                </button>

                {/* Forward +5s button */}
                <button
                  type="button"
                  onClick={() => seekRelative(5)}
                  title="Вперед на 5 секунд (→)"
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#cbd5e1',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '2px',
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '4px 6px',
                    borderRadius: '4px',
                  }}
                >
                  +5s
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M13 17l5-5-5-5M6 17l5-5-5-5" />
                  </svg>
                </button>

                {/* Frame Step Backward */}
                <button
                  type="button"
                  onClick={() => stepFrame('prev')}
                  title="Предыдущий кадр (Запятая ',')"
                  style={{
                    background: 'rgba(255, 255, 255, 0.08)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    color: '#cbd5e1',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '3px 8px',
                    borderRadius: '4px',
                  }}
                >
                  ◀ кадр
                </button>

                {/* Frame Step Forward */}
                <button
                  type="button"
                  onClick={() => stepFrame('next')}
                  title="Следующий кадр (Точка '.')"
                  style={{
                    background: 'rgba(255, 255, 255, 0.08)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    color: '#cbd5e1',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '3px 8px',
                    borderRadius: '4px',
                  }}
                >
                  кадр ▶
                </button>

                {/* Timestamp */}
                <div style={{ fontFamily: 'monospace', fontSize: '13px', color: '#f1f5f9', marginLeft: '6px' }}>
                  <span style={{ color: '#38bdf8', fontWeight: 700 }}>{formatTime(currentTime)}</span>
                  <span style={{ color: '#64748b', margin: '0 4px' }}>/</span>
                  <span style={{ color: '#94a3b8' }}>{formatTime(duration)}</span>
                </div>
              </div>

              {/* Right group: 4:3 Stretched toggle, Speed selector, Loop, Volume slider, PiP, Fullscreen */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* 4:3 Stretched / Native toggle button */}
                {isNative43 && (
                  <button
                    type="button"
                    onClick={() => {
                      const next = !is43Stretched
                      setIs43Stretched(next)
                      triggerRipple(next ? '↔️ 4:3 Stretched (16:9)' : '🎯 4:3 Native (Black bars)', 'play')
                    }}
                    title={
                      is43Stretched
                        ? 'Сейчас: 16:9 Stretched (растянуто без черных полос). Нажмите для 4:3 Native'
                        : 'Сейчас: 4:3 Native (с черными полосами по бокам). Нажмите для 16:9 Stretched'
                    }
                    style={{
                      backgroundColor: is43Stretched ? 'rgba(56, 189, 248, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid',
                      borderColor: is43Stretched ? '#38bdf8' : 'rgba(255, 255, 255, 0.2)',
                      color: is43Stretched ? '#38bdf8' : '#e2e8f0',
                      cursor: 'pointer',
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '3px 8px',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    {is43Stretched ? '↔️ Stretched' : '🎯 4:3 Native'}
                  </button>
                )}

                {/* Speed selector */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {[0.25, 0.5, 1, 1.5].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => changeSpeed(s)}
                      style={{
                        padding: '2px 6px',
                        fontSize: '11px',
                        fontWeight: 700,
                        borderRadius: '4px',
                        border: '1px solid',
                        borderColor: playbackRate === s ? '#38bdf8' : 'rgba(255, 255, 255, 0.15)',
                        backgroundColor: playbackRate === s ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                        color: playbackRate === s ? '#38bdf8' : '#94a3b8',
                        cursor: 'pointer',
                      }}
                      title={`Скорость воспроизведения ${s}x`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>

                {/* Loop toggle */}
                <button
                  type="button"
                  onClick={toggleLoop}
                  title={isLooping ? 'Повтор включен (R)' : 'Повтор выключен (R)'}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: isLooping ? '#38bdf8' : '#64748b',
                    cursor: 'pointer',
                    padding: '4px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 1l4 4-4 4M3 11V9a4 4 0 0 1 4-4h14M7 23l-4-4 4-4M21 13v2a4 4 0 0 1-4 4H3" />
                  </svg>
                </button>

                {/* Volume & Mute */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    type="button"
                    onClick={toggleMute}
                    title={isMuted ? 'Включить звук (M)' : 'Выключить звук (M)'}
                    style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', padding: '4px' }}
                  >
                    {isMuted || volume === 0 ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                        <line x1="23" y1="9" x2="17" y2="15" />
                        <line x1="17" y1="9" x2="23" y2="15" />
                      </svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                      </svg>
                    )}
                  </button>

                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={isMuted ? 0 : volume}
                    onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                    style={{
                      width: '64px',
                      accentColor: '#38bdf8',
                      cursor: 'pointer',
                      height: '4px',
                    }}
                    title={`Громкость: ${Math.round((isMuted ? 0 : volume) * 100)}%`}
                  />
                </div>

                {/* PiP button */}
                <button
                  type="button"
                  onClick={togglePiP}
                  title="Картинка в картинке"
                  style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', padding: '4px' }}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="2" y="3" width="20" height="14" rx="2" />
                    <rect x="12" y="9" width="8" height="6" rx="1" fill="rgba(255,255,255,0.2)" />
                  </svg>
                </button>

                {/* Fullscreen button */}
                <button
                  type="button"
                  onClick={toggleFullscreen}
                  title={isFullscreen ? 'Выйти из полноэкранного режима (F)' : 'На весь экран (F)'}
                  style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', padding: '4px' }}
                >
                  {isFullscreen ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </div>

        {/* CSS Keyframes for spin and ripple */}
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
          @keyframes fadeRipple {
            0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            30% { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
            70% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
            100% { opacity: 0; transform: translate(-50%, -50%) scale(1.1); }
          }
        `}</style>
      </div>
    </div>
  )
}

