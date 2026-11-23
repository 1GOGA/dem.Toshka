import React, { useState, useRef, useEffect, useMemo } from 'react'
import type {
  ReplayPlayerState,
  ReplayKillItem,
  ReplayGrenadeItem,
  ReplayBombData,
  TacticalDrawingDTO,
  BookmarkDTO,
} from '../types'
import { SkullIcon, SmokeIcon, FlameIcon, FlashIcon, GrenadeIcon } from './Icons'
import { useTranslation } from '../i18n'

export interface TacticalReplayRadarProps {
  radarImageUrl?: string
  mapName?: string
  currentTick: number
  tickrate: number
  startTick: number
  players: ReplayPlayerState[]
  kills: ReplayKillItem[]
  grenades?: ReplayGrenadeItem[]
  bomb?: ReplayBombData | null
  playerTrails?: Record<string, Array<{ x: number; y: number; is_alive: boolean }>>
  currentLevel?: 'upper' | 'lower'
  hasMultipleLevels?: boolean
  showTrails: boolean
  showShots: boolean
  showGrenades: boolean
  onJumpToTick?: (tick: number) => void
  maxContainerHeight?: string
  roundNum?: number
  savedDrawings?: TacticalDrawingDTO[]
  savedBookmarks?: BookmarkDTO[]
  onSaveDrawing?: (drawing: {
    round_num: number
    layer_type: 'pen' | 'arrow' | 'line' | 'circle' | 'box' | 'text'
    color: string
    stroke_width: number
    geometry_json: string
    tick?: number
    text_label?: string
  }) => void
  onDeleteDrawing?: (drawingId: string) => void
  onSaveBookmark?: (bookmark: {
    round_num: number
    tick: number
    title: string
    category: string
    notes?: string
    player_steamid?: string
  }) => void
  onDeleteBookmark?: (bookmarkId: string) => void
}

export const TacticalReplayRadar: React.FC<TacticalReplayRadarProps> = ({
  radarImageUrl,
  mapName = 'CS2 Map',
  currentTick,
  tickrate = 128,
  startTick: _startTick,
  players,
  kills,
  grenades = [],
  bomb,
  playerTrails = {},
  currentLevel = 'upper',
  hasMultipleLevels = false,
  showTrails,
  showShots,
  showGrenades,
  onJumpToTick,
  maxContainerHeight = '560px',
  roundNum = 1,
  savedDrawings = [],
  savedBookmarks = [],
  onSaveDrawing,
  onDeleteDrawing,
  onSaveBookmark,
  onDeleteBookmark,
}) => {
  const { lang } = useTranslation()
  // Zoom & Pan state
  const [zoom, setZoom] = useState<number>(1)
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [hoveredKill, setHoveredKill] = useState<ReplayKillItem | null>(null)
  const [hoveredGrenade, setHoveredGrenade] = useState<ReplayGrenadeItem | null>(null)
  const [nameDensity, setNameDensity] = useState<'auto' | 'compact' | 'minimal'>('auto')
  const [showFovCones, setShowFovCones] = useState<boolean>(true)
  const [showEquipment, setShowEquipment] = useState<boolean>(true)
  const [focusedSteamId, setFocusedSteamId] = useState<string | null>(null)

  // Tactical Drawing State (Phase 2)
  const [isDrawingMode, setIsDrawingMode] = useState<boolean>(false)
  const [activeDrawTool, setActiveDrawTool] = useState<'pen' | 'arrow' | 'line' | 'circle' | 'box' | 'text'>('arrow')
  const [drawColor, setDrawColor] = useState<string>('#00f2fe')
  const [strokeWidth, setStrokeWidth] = useState<number>(3)
  const [drawings, setDrawings] = useState<TacticalDrawingDTO[]>(savedDrawings)
  const [isDrawingActive, setIsDrawingActive] = useState<boolean>(false)
  const [activeDragStart, setActiveDragStart] = useState<{ x: number; y: number } | null>(null)
  const [activeDragCurrent, setActiveDragCurrent] = useState<{ x: number; y: number } | null>(null)
  const [penPoints, setPenPoints] = useState<Array<[number, number]>>([])
  const [textPromptOpen, setTextPromptOpen] = useState<boolean>(false)
  const [textPromptCoord, setTextPromptCoord] = useState<{ x: number; y: number } | null>(null)
  const [textInputValue, setTextInputValue] = useState<string>('')

  // Bookmarks State (Phase 2)
  const [bookmarks, setBookmarks] = useState<BookmarkDTO[]>(savedBookmarks)
  const [bookmarkModalOpen, setBookmarkModalOpen] = useState<boolean>(false)
  const [bookmarksDrawerOpen, setBookmarksDrawerOpen] = useState<boolean>(false)
  const [bmTitle, setBmTitle] = useState<string>('')
  const [bmCategory, setBmCategory] = useState<string>('TACTICAL_MISTAKE')
  const [bmNotes, setBmNotes] = useState<string>('')

  useEffect(() => {
    setDrawings(savedDrawings)
  }, [savedDrawings])

  useEffect(() => {
    setBookmarks(savedBookmarks)
  }, [savedBookmarks])

  // Dynamic scaling for nicknames so they shrink and remain unobtrusive when zooming in
  const nameScale = useMemo(() => {
    // Base inverse zoom exponential: at zoom 1.0 -> 1.0, at zoom 2.0 -> 0.39, at zoom 3.0 -> 0.22
    const base = Math.max(0.55, 1 / Math.pow(zoom, 0.55))
    if (nameDensity === 'compact') return base * 0.8
    if (nameDensity === 'minimal') return 0
    return Math.max(0.2, base)
  }, [zoom, nameDensity])

  // Keep player dots legible without ballooning into oversized circles at high zoom
  const dotScale = useMemo(() => {
    return Math.max(0.55, 1 / Math.pow(zoom, 0.5))
  }, [zoom])

  const containerRef = useRef<HTMLDivElement>(null)

  // Zoom handlers
  const handleZoomIn = () => {
    setZoom((prev) => Math.min(3.5, Number((prev + 0.35).toFixed(2))))
  }

  const handleZoomOut = () => {
    setZoom((prev) => {
      const next = Math.max(1, Number((prev - 0.35).toFixed(2)))
      if (next === 1) setPan({ x: 0, y: 0 })
      return next
    })
  }

  const handleResetZoom = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  // Native wheel listener on container with preventDefault to prevent window scroll
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const onWheelNative = (e: WheelEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (e.deltaY < 0) {
        setZoom((prev) => Math.min(3.5, Number((prev + 0.25).toFixed(2))))
      } else {
        setZoom((prev) => {
          const next = Math.max(1, Number((prev - 0.25).toFixed(2)))
          if (next === 1) setPan({ x: 0, y: 0 })
          return next
        })
      }
    }

    el.addEventListener('wheel', onWheelNative, { passive: false })
    return () => {
      el.removeEventListener('wheel', onWheelNative)
    }
  }, [])

  // Coordinate inversion: transforms screen click coordinates into 0..1000 SVG coordinates
  const getSvgCoords = (clientX: number, clientY: number) => {
    const el = containerRef.current
    if (!el) return { x: 500, y: 500 }
    const rect = el.getBoundingClientRect()
    const xRel = clientX - rect.left
    const yRel = clientY - rect.top
    const cx = rect.width / 2
    const cy = rect.height / 2
    const xInner = cx + (xRel - cx - pan.x) / zoom
    const yInner = cy + (yRel - cy - pan.y) / zoom
    const svgX = Math.max(0, Math.min(1000, (xInner / rect.width) * 1000))
    const svgY = Math.max(0, Math.min(1000, (yInner / rect.height) * 1000))
    return { x: Number(svgX.toFixed(1)), y: Number(svgY.toFixed(1)) }
  }

  // Mouse handlers: handles either Tactical Drawing OR Zoom/Pan dragging
  const handleMouseDown = (e: React.MouseEvent) => {
    if (isDrawingMode) {
      const coords = getSvgCoords(e.clientX, e.clientY)
      if (activeDrawTool === 'text') {
        setTextPromptCoord(coords)
        setTextPromptOpen(true)
        return
      }
      setIsDrawingActive(true)
      setActiveDragStart(coords)
      setActiveDragCurrent(coords)
      if (activeDrawTool === 'pen') {
        setPenPoints([[coords.x, coords.y]])
      }
      return
    }

    if (zoom > 1) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDrawingMode && isDrawingActive) {
      const coords = getSvgCoords(e.clientX, e.clientY)
      setActiveDragCurrent(coords)
      if (activeDrawTool === 'pen') {
        setPenPoints((prev) => [...prev, [coords.x, coords.y]])
      }
      return
    }

    if (isDragging && zoom > 1) {
      const maxPan = (zoom - 1) * 220
      const nextX = Math.max(-maxPan, Math.min(maxPan, e.clientX - dragStart.x))
      const nextY = Math.max(-maxPan, Math.min(maxPan, e.clientY - dragStart.y))
      setPan({ x: nextX, y: nextY })
    }
  }

  const handleMouseUp = () => {
    if (isDrawingMode && isDrawingActive) {
      setIsDrawingActive(false)
      if (activeDragStart && activeDragCurrent) {
        let geomJson = ''
        if (activeDrawTool === 'pen') {
          if (penPoints.length >= 2) {
            geomJson = JSON.stringify({ points: penPoints })
          }
        } else if (activeDrawTool === 'arrow' || activeDrawTool === 'line') {
          const dist = Math.hypot(activeDragCurrent.x - activeDragStart.x, activeDragCurrent.y - activeDragStart.y)
          if (dist >= 6) {
            geomJson = JSON.stringify({
              x1: activeDragStart.x,
              y1: activeDragStart.y,
              x2: activeDragCurrent.x,
              y2: activeDragCurrent.y,
            })
          }
        } else if (activeDrawTool === 'circle') {
          const rx = Math.abs(activeDragCurrent.x - activeDragStart.x)
          const ry = Math.abs(activeDragCurrent.y - activeDragStart.y)
          if (rx >= 6 || ry >= 6) {
            geomJson = JSON.stringify({
              cx: activeDragStart.x,
              cy: activeDragStart.y,
              rx: Math.max(8, rx),
              ry: Math.max(8, ry),
            })
          }
        } else if (activeDrawTool === 'box') {
          const x = Math.min(activeDragStart.x, activeDragCurrent.x)
          const y = Math.min(activeDragStart.y, activeDragCurrent.y)
          const w = Math.abs(activeDragCurrent.x - activeDragStart.x)
          const h = Math.abs(activeDragCurrent.y - activeDragStart.y)
          if (w >= 6 && h >= 6) {
            geomJson = JSON.stringify({ x, y, w, h })
          }
        }

        if (geomJson) {
          const newDrawing: TacticalDrawingDTO = {
            id: 'draw_' + Date.now(),
            project_id: 'proj',
            round_num: roundNum,
            tick: currentTick,
            layer_type: activeDrawTool,
            color: drawColor,
            stroke_width: strokeWidth,
            geometry_json: geomJson,
            created_at: new Date().toISOString(),
          }
          setDrawings((prev) => [...prev, newDrawing])
          onSaveDrawing?.({
            round_num: roundNum,
            layer_type: activeDrawTool,
            color: drawColor,
            stroke_width: strokeWidth,
            geometry_json: geomJson,
            tick: currentTick,
          })
        }
      }
      setActiveDragStart(null)
      setActiveDragCurrent(null)
      setPenPoints([])
      return
    }

    setIsDragging(false)
  }

  const handleSaveTextLabel = () => {
    if (!textInputValue.trim() || !textPromptCoord) {
      setTextPromptOpen(false)
      setTextInputValue('')
      return
    }
    const geomJson = JSON.stringify({ x: textPromptCoord.x, y: textPromptCoord.y })
    const newDrawing: TacticalDrawingDTO = {
      id: 'draw_' + Date.now(),
      project_id: 'proj',
      round_num: roundNum,
      tick: currentTick,
      layer_type: 'text',
      color: drawColor,
      stroke_width: strokeWidth,
      geometry_json: geomJson,
      text_label: textInputValue.trim(),
      created_at: new Date().toISOString(),
    }
    setDrawings((prev) => [...prev, newDrawing])
    onSaveDrawing?.({
      round_num: roundNum,
      layer_type: 'text',
      color: drawColor,
      stroke_width: strokeWidth,
      geometry_json: geomJson,
      tick: currentTick,
      text_label: textInputValue.trim(),
    })
    setTextPromptOpen(false)
    setTextInputValue('')
  }

  const handleUndoDrawing = () => {
    if (drawings.length === 0) return
    const last = drawings[drawings.length - 1]
    setDrawings((prev) => prev.slice(0, -1))
    if (last.id && !last.id.startsWith('draw_')) {
      onDeleteDrawing?.(last.id)
    }
  }

  const handleClearDrawings = () => {
    drawings.forEach((d) => {
      if (d.id && !d.id.startsWith('draw_')) {
        onDeleteDrawing?.(d.id)
      }
    })
    setDrawings([])
  }

  const handleSaveBookmark = () => {
    if (!bmTitle.trim()) return
    const newBm: BookmarkDTO = {
      id: 'bm_' + Date.now(),
      project_id: 'proj',
      round_num: roundNum,
      tick: currentTick,
      title: bmTitle.trim(),
      category: bmCategory,
      notes: bmNotes.trim() || undefined,
      player_steamid: focusedSteamId || undefined,
      created_at: new Date().toISOString(),
    }
    setBookmarks((prev) => [...prev, newBm])
    onSaveBookmark?.({
      round_num: roundNum,
      tick: currentTick,
      title: bmTitle.trim(),
      category: bmCategory,
      notes: bmNotes.trim() || undefined,
      player_steamid: focusedSteamId || undefined,
    })
    setBookmarkModalOpen(false)
    setBmTitle('')
    setBmNotes('')
  }

  // Kills that occurred up to current tick
  const pastKills = useMemo(() => {
    return kills.filter((k) => k.tick <= currentTick)
  }, [kills, currentTick])

  // Filter living players only (dead players do not render duplicate tokens)
  const livingPlayers = useMemo(() => {
    return players.filter((p) => p.is_alive)
  }, [players])

  // Active grenades at currentTick
  const activeGrenades = useMemo(() => {
    if (!showGrenades || !grenades || grenades.length === 0) return []
    return grenades.filter((g) => {
      // Show if in-flight or detonated and not yet expired
      return g.start_tick <= currentTick && currentTick <= g.end_tick
    })
  }, [grenades, currentTick, showGrenades])

  // Active detonated grenades that require high-contrast countdown timers
  const detonatedGrenades = useMemo(() => {
    return activeGrenades.filter(
      (g) =>
        (g.type === 'smoke' || g.type === 'molotov') &&
        currentTick >= g.detonate_tick &&
        currentTick <= g.end_tick
    )
  }, [activeGrenades, currentTick])

  return (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{
        position: 'relative',
        width: '100%',
        maxWidth: maxContainerHeight,
        aspectRatio: '1 / 1',
        margin: '0 auto',
        backgroundColor: '#0a0d14',
        borderRadius: '10px',
        border: '1px solid #1e2433',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.55)',
        cursor: isDrawingMode ? 'crosshair' : zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
        userSelect: 'none',
        overscrollBehavior: 'contain',
        touchAction: 'none',
      }}
    >
      <style>{`
        @keyframes radarPing {
          0% { transform: scale(0.9); opacity: 0.95; }
          100% { transform: scale(2.5); opacity: 0; }
        }
        @keyframes radarBombPing {
          0% { transform: scale(0.9); opacity: 1; }
          100% { transform: scale(2.2); opacity: 0; }
        }
        @keyframes smokePulse {
          0%, 100% { opacity: 0.55; }
          50% { opacity: 0.28; }
        }
        @keyframes fireGlow {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 4px rgba(249, 115, 22, 0.6)); }
          50% { transform: scale(1.04); filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.8)); }
        }
        @keyframes flashBurst {
          0% { transform: scale(0.5); opacity: 1; }
          100% { transform: scale(2.2); opacity: 0; }
        }
        @keyframes timerUrgentPulse {
          0%, 100% { transform: scale(1); filter: brightness(1); }
          50% { transform: scale(1.06); filter: brightness(1.35); }
        }
        @keyframes blindPulse {
          0%, 100% { transform: scale(1); opacity: 0.95; filter: drop-shadow(0 0 6px #facc15); }
          50% { transform: scale(1.4); opacity: 0.4; filter: drop-shadow(0 0 14px #ffffff); }
        }
        @keyframes focusPulse {
          0%, 100% { transform: scale(1); opacity: 0.9; }
          50% { transform: scale(1.15); opacity: 0.5; }
        }
      `}</style>

      {/* Active Utility & Objective HUD Strip (Always readable timers at glance) */}
      {(detonatedGrenades.length > 0 || (bomb && currentTick >= bomb.plant_tick && currentTick <= bomb.plant_tick + 40 * tickrate)) && (
        <div
          style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            zIndex: 35,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            flexWrap: 'wrap',
            maxWidth: 'calc(100% - 230px)',
            pointerEvents: 'auto',
          }}
        >
          {bomb && currentTick >= bomb.plant_tick && currentTick <= bomb.plant_tick + 40 * tickrate && (
            <div
              onClick={() => onJumpToTick?.(bomb.plant_tick)}
              title={lang === 'ru' ? 'Бомба C4 установлена. Клик для перехода к моменту установки' : 'C4 Bomb planted. Click to jump to plant tick'}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '2px 6px',
                borderRadius: '6px',
                backgroundColor: 'rgba(220, 38, 38, 0.95)',
                border: '1.5px solid #ffffff',
                boxShadow: '0 0 14px rgba(239, 68, 68, 0.9)',
                color: '#ffffff',
                fontSize: '10px',
                fontWeight: 900,
                fontFamily: 'monospace',
                animation: 'radarBombPing 1s ease-out infinite',
                cursor: 'pointer',
              }}
            >
              <span>💣</span>
              <span>{lang === 'ru' ? 'ПЛЕНТ' : 'PLANT'} {bomb.site || 'CS2'}:</span>
              <span style={{ color: '#fef08a' }}>
                {Math.max(0, 40 - (currentTick - bomb.plant_tick) / tickrate).toFixed(1)}s
              </span>
            </div>
          )}

          {detonatedGrenades.map((g) => {
            const remainingSec = Math.max(0, (g.end_tick - currentTick) / tickrate)
            const isMolotov = g.type === 'molotov'
            const isExpiring = isMolotov ? remainingSec <= 2.0 : remainingSec <= 4.0

            return (
              <div
                key={`hud-util-${g.id}`}
                onClick={() => onJumpToTick?.(g.detonate_tick)}
                title={lang === 'ru' ? `Клик для перехода к подрыву: ${isMolotov ? 'Молотов' : 'Смок'} (${g.thrower_name})` : `Click to jump to detonation: ${isMolotov ? 'Molotov' : 'Smoke'} (${g.thrower_name})`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '3px 7px',
                  borderRadius: '6px',
                  backgroundColor: 'rgba(11, 15, 23, 0.94)',
                  backdropFilter: 'blur(8px)',
                  border: `1.5px solid ${isExpiring ? '#ef4444' : isMolotov ? '#f97316' : '#38bdf8'}`,
                  boxShadow: `0 2px 8px ${isExpiring ? 'rgba(239, 68, 68, 0.6)' : isMolotov ? 'rgba(249, 115, 22, 0.4)' : 'rgba(56, 189, 248, 0.3)'}`,
                  color: '#ffffff',
                  fontSize: '11px',
                  fontWeight: 800,
                  fontFamily: 'monospace',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span>{isMolotov ? '🔥' : '💨'}</span>
                <span style={{ color: isExpiring ? '#fca5a5' : isMolotov ? '#fed7aa' : '#94a3b8' }}>
                  {isMolotov ? `${remainingSec.toFixed(1)}s` : `${Math.ceil(remainingSec)}s`}
                </span>
              </div>
            )
          })}
        </div>
      )}

      {/* Floating Controls Bar (Zoom, Pan & Nicknames) */}
      <div
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          zIndex: 35,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        {/* Toggle FOV Vision Cones */}
        <button
          type="button"
          onClick={() => setShowFovCones((prev) => !prev)}
          title={lang === 'ru' ? 'Взгляд / Конусы видимости (FOV 90°)' : 'Player FOV vision cones (90°)'}
          style={{
            backgroundColor: showFovCones ? 'rgba(56, 189, 248, 0.22)' : 'rgba(11, 15, 23, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '3px 8px',
            borderRadius: '6px',
            border: `1px solid ${showFovCones ? '#38bdf8' : 'rgba(56, 189, 248, 0.3)'}`,
            color: showFovCones ? '#38bdf8' : '#64748b',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            boxShadow: '0 4px 14px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span>👁️</span>
          <span>{lang === 'ru' ? 'Взгляд' : 'FOV'}</span>
        </button>

        {/* Toggle Equipment Badges */}
        <button
          type="button"
          onClick={() => setShowEquipment((prev) => !prev)}
          title={lang === 'ru' ? 'Отображение оружия, брони и дефьюзов' : 'Toggle equipment & weapons'}
          style={{
            backgroundColor: showEquipment ? 'rgba(56, 189, 248, 0.22)' : 'rgba(11, 15, 23, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '3px 8px',
            borderRadius: '6px',
            border: `1px solid ${showEquipment ? '#38bdf8' : 'rgba(56, 189, 248, 0.3)'}`,
            color: showEquipment ? '#38bdf8' : '#64748b',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            boxShadow: '0 4px 14px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span>🛡️</span>
          <span>{lang === 'ru' ? 'Экип' : 'Gear'}</span>
        </button>

        {/* Toggle Tactical Drawing Mode */}
        <button
          type="button"
          onClick={() => setIsDrawingMode((prev) => !prev)}
          title={lang === 'ru' ? 'Тактическое рисование (стрелки, зоны, текст)' : 'Tactical Drawing Canvas (arrows, zones, text)'}
          style={{
            backgroundColor: isDrawingMode ? 'rgba(0, 242, 254, 0.25)' : 'rgba(11, 15, 23, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '3px 8px',
            borderRadius: '6px',
            border: `1.5px solid ${isDrawingMode ? '#00f2fe' : 'rgba(56, 189, 248, 0.3)'}`,
            color: isDrawingMode ? '#00f2fe' : '#94a3b8',
            fontSize: '11px',
            fontWeight: 800,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            boxShadow: isDrawingMode ? '0 0 12px rgba(0, 242, 254, 0.4)' : '0 4px 14px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span>🎨</span>
          <span>{lang === 'ru' ? 'Рисовать' : 'Draw'}</span>
        </button>

        {/* Add Bookmark Button */}
        <button
          type="button"
          onClick={() => {
            const sec = Math.floor((currentTick - _startTick) / (tickrate || 128))
            const mins = Math.floor(sec / 60)
            const remSec = sec % 60
            setBmTitle(`R${roundNum} [${mins}:${remSec.toString().padStart(2, '0')}]`)
            setBookmarkModalOpen(true)
          }}
          title={lang === 'ru' ? 'Добавить закладку к текущему тику' : 'Add bookmark at current tick'}
          style={{
            backgroundColor: 'rgba(11, 15, 23, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '3px 8px',
            borderRadius: '6px',
            border: '1px solid rgba(250, 204, 21, 0.4)',
            color: '#facc15',
            fontSize: '11px',
            fontWeight: 800,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
            boxShadow: '0 4px 14px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span>🔖</span>
          <span>+</span>
        </button>

        {/* Toggle Bookmarks Drawer */}
        <button
          type="button"
          onClick={() => setBookmarksDrawerOpen((prev) => !prev)}
          title={lang === 'ru' ? 'Список тактических закладок' : 'View tactical bookmarks list'}
          style={{
            backgroundColor: bookmarksDrawerOpen ? 'rgba(250, 204, 21, 0.25)' : 'rgba(11, 15, 23, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '3px 8px',
            borderRadius: '6px',
            border: `1.5px solid ${bookmarksDrawerOpen ? '#facc15' : 'rgba(250, 204, 21, 0.4)'}`,
            color: '#facc15',
            fontSize: '11px',
            fontWeight: 800,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            boxShadow: '0 4px 14px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span>📑</span>
          <span>{bookmarks.length}</span>
        </button>

        {/* Nickname Density Selector */}
        <button
          type="button"
          onClick={() => {
            setNameDensity((prev) => (prev === 'auto' ? 'compact' : prev === 'compact' ? 'minimal' : 'auto'))
          }}
          title={
            lang === 'ru'
              ? `Масштаб ников: ${nameDensity === 'auto' ? 'Авто (уменьшаются при зуме)' : nameDensity === 'compact' ? 'Мини (сокращённые)' : 'Скрыть (только точки)'}`
              : `Player Names Density: ${nameDensity === 'auto' ? 'Auto (scale with zoom)' : nameDensity === 'compact' ? 'Mini (compact tags)' : 'Hidden (dots only)'}`
          }
          style={{
            backgroundColor: 'rgba(11, 15, 23, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '3px 8px',
            borderRadius: '6px',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            color: nameDensity === 'minimal' ? '#64748b' : '#38bdf8',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            boxShadow: '0 4px 14px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span>👥 {lang === 'ru' ? 'Ники:' : 'Names:'}</span>
          <span style={{ color: nameDensity === 'minimal' ? '#94a3b8' : '#ffffff' }}>
            {nameDensity === 'auto'
              ? (lang === 'ru' ? 'Авто' : 'Auto')
              : nameDensity === 'compact'
              ? (lang === 'ru' ? 'Мини' : 'Mini')
              : (lang === 'ru' ? 'Выкл' : 'Off')}
          </span>
        </button>

        {/* Zoom Controls */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: 'rgba(11, 15, 23, 0.92)',
            backdropFilter: 'blur(8px)',
            padding: '3px 8px',
            borderRadius: '6px',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            boxShadow: '0 4px 14px rgba(0, 0, 0, 0.6)',
          }}
        >
        <button
          type="button"
          onClick={handleZoomOut}
          disabled={zoom <= 1}
          title={lang === 'ru' ? 'Отдалить (-)' : 'Zoom Out (-)'}
          style={{
            background: 'transparent',
            border: 'none',
            color: zoom <= 1 ? '#475569' : '#38bdf8',
            cursor: zoom <= 1 ? 'not-allowed' : 'pointer',
            fontSize: '15px',
            fontWeight: 800,
            padding: '2px 5px',
            lineHeight: 1,
          }}
        >
          −
        </button>
        <button
          type="button"
          onClick={handleResetZoom}
          title={lang === 'ru' ? 'Сбросить масштаб (100%)' : 'Reset Zoom (100%)'}
          style={{
            fontSize: '11px',
            color: '#94a3b8',
            fontFamily: 'monospace',
            fontWeight: 700,
            minWidth: '34px',
            textAlign: 'center',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          {zoom.toFixed(1)}x
        </button>
        <button
          type="button"
          onClick={handleZoomIn}
          disabled={zoom >= 3.5}
          title={lang === 'ru' ? 'Приблизить (+)' : 'Zoom In (+)'}
          style={{
            background: 'transparent',
            border: 'none',
            color: zoom >= 3.5 ? '#475569' : '#38bdf8',
            cursor: zoom >= 3.5 ? 'not-allowed' : 'pointer',
            fontSize: '15px',
            fontWeight: 800,
            padding: '2px 5px',
            lineHeight: 1,
          }}
        >
          +
        </button>
        </div>
      </div>

      {/* Tactical Drawing Floating Toolbar (Phase 2) */}
      {isDrawingMode && (
        <div
          style={{
            position: 'absolute',
            top: '44px',
            right: '10px',
            zIndex: 36,
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            backgroundColor: 'rgba(9, 13, 20, 0.96)',
            backdropFilter: 'blur(10px)',
            padding: '4px 8px',
            borderRadius: '8px',
            border: '1px solid #00f2fe',
            boxShadow: '0 6px 20px rgba(0, 242, 254, 0.3)',
          }}
        >
          {/* Tool selectors */}
          {[
            { id: 'arrow', label: '➔', title: lang === 'ru' ? 'Стрелка захода' : 'Directional Arrow' },
            { id: 'pen', label: '✏️', title: lang === 'ru' ? 'Свободный карандаш' : 'Freehand Pen' },
            { id: 'line', label: '📏', title: lang === 'ru' ? 'Прямая линия' : 'Straight Line' },
            { id: 'circle', label: '⭕', title: lang === 'ru' ? 'Зона контроля' : 'Zone Ellipse' },
            { id: 'box', label: '⬛', title: lang === 'ru' ? 'Прямоугольник укрытия' : 'Tactical Box' },
            { id: 'text', label: '🔤', title: lang === 'ru' ? 'Текстовая подпись' : 'Text Label' },
          ].map((tool) => (
            <button
              key={tool.id}
              type="button"
              onClick={() => setActiveDrawTool(tool.id as any)}
              title={tool.title}
              style={{
                background: activeDrawTool === tool.id ? 'rgba(0, 242, 254, 0.3)' : 'transparent',
                border: activeDrawTool === tool.id ? '1px solid #00f2fe' : '1px solid transparent',
                borderRadius: '4px',
                color: activeDrawTool === tool.id ? '#00f2fe' : '#94a3b8',
                fontSize: '13px',
                padding: '2px 5px',
                cursor: 'pointer',
              }}
            >
              {tool.label}
            </button>
          ))}

          <div style={{ width: '1px', height: '16px', backgroundColor: 'rgba(255,255,255,0.15)', margin: '0 2px' }} />

          {/* Color Palettes */}
          {['#00f2fe', '#facc15', '#f43f5e', '#4ade80', '#c084fc', '#ffffff'].map((c) => (
            <div
              key={c}
              onClick={() => setDrawColor(c)}
              title={c}
              style={{
                width: '14px',
                height: '14px',
                borderRadius: '50%',
                backgroundColor: c,
                border: drawColor === c ? '2px solid #ffffff' : '1px solid rgba(0,0,0,0.5)',
                boxShadow: drawColor === c ? `0 0 8px ${c}` : 'none',
                cursor: 'pointer',
                transform: drawColor === c ? 'scale(1.15)' : 'scale(1)',
                transition: 'transform 0.1s ease',
              }}
            />
          ))}

          <div style={{ width: '1px', height: '16px', backgroundColor: 'rgba(255,255,255,0.15)', margin: '0 2px' }} />

          {/* Stroke Widths */}
          {[2, 4, 8].map((w) => (
            <button
              key={w}
              type="button"
              onClick={() => setStrokeWidth(w)}
              title={`${w}px`}
              style={{
                background: strokeWidth === w ? 'rgba(255,255,255,0.2)' : 'transparent',
                border: strokeWidth === w ? '1px solid #ffffff' : '1px solid transparent',
                borderRadius: '4px',
                color: '#f1f5f9',
                fontSize: '10px',
                fontWeight: 700,
                padding: '1px 4px',
                cursor: 'pointer',
              }}
            >
              {w}p
            </button>
          ))}

          <div style={{ width: '1px', height: '16px', backgroundColor: 'rgba(255,255,255,0.15)', margin: '0 2px' }} />

          {/* Undo and Clear */}
          <button
            type="button"
            onClick={handleUndoDrawing}
            title={lang === 'ru' ? 'Отменить последнюю фигуру' : 'Undo last shape'}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              fontSize: '12px',
              cursor: 'pointer',
              padding: '2px 4px',
            }}
          >
            ↩️
          </button>
          <button
            type="button"
            onClick={handleClearDrawings}
            title={lang === 'ru' ? 'Очистить все рисунки' : 'Clear all drawings'}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#ef4444',
              fontSize: '12px',
              cursor: 'pointer',
              padding: '2px 4px',
            }}
          >
            🧹
          </button>
        </div>
      )}

      {/* Tooltip Overlay for Hovered Kill or Grenade */}
      {(hoveredKill || hoveredGrenade) && (
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            zIndex: 40,
            backgroundColor: 'rgba(9, 13, 20, 0.94)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            padding: '5px 10px',
            borderRadius: '6px',
            fontSize: '11px',
            color: '#f1f5f9',
            boxShadow: '0 4px 16px rgba(0,0,0,0.7)',
            pointerEvents: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          {hoveredKill && (
            <>
              <SkullIcon size={12} color="#ef4444" />
              <span>
                <strong>{hoveredKill.attacker_name}</strong> [{hoveredKill.weapon || 'kill'}] ➔{' '}
                <strong>{hoveredKill.victim_name}</strong>
              </span>
              <span style={{ color: '#64748b', fontSize: '10px' }}>{lang === 'ru' ? '(клик для перехода к тику)' : '(click to jump to tick)'}</span>
            </>
          )}
          {hoveredGrenade && !hoveredKill && (
            <>
              {hoveredGrenade.type === 'smoke' && <SmokeIcon size={13} color="#94a3b8" />}
              {hoveredGrenade.type === 'molotov' && <FlameIcon size={13} color="#f97316" />}
              {hoveredGrenade.type === 'flash' && <FlashIcon size={13} color="#facc15" />}
              {hoveredGrenade.type === 'he' && <GrenadeIcon size={13} color="#ef4444" />}
              <span>
                <strong>
                  {hoveredGrenade.type === 'smoke'
                    ? (lang === 'ru' ? 'Дым' : 'Smoke')
                    : hoveredGrenade.type === 'molotov'
                    ? (lang === 'ru' ? 'Огонь / Молотов' : 'Incendiary / Molotov')
                    : hoveredGrenade.type === 'flash'
                    ? (lang === 'ru' ? 'Световая граната' : 'Flashbang')
                    : (lang === 'ru' ? 'Осколочная граната (HE)' : 'HE Grenade')}
                </strong>
                {hoveredGrenade.thrower_name ? (lang === 'ru' ? ` (бросил: ${hoveredGrenade.thrower_name})` : ` (thrown by: ${hoveredGrenade.thrower_name})`) : ''}
                {hoveredGrenade.type === 'smoke' || hoveredGrenade.type === 'molotov' ? (
                  <span style={{ color: '#38bdf8', marginLeft: '6px' }}>
                    {lang === 'ru' ? 'Осталось:' : 'Remaining:'} {Math.max(0, (hoveredGrenade.end_tick - currentTick) / tickrate).toFixed(1)}s
                  </span>
                ) : null}
              </span>
            </>
          )}
        </div>
      )}

      {/* Scalable Tactical Inner Canvas */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: 'center center',
          transition: isDragging ? 'none' : 'transform 0.12s ease-out',
        }}
      >
        {/* Source 2 Radar Map Backdrop */}
        {radarImageUrl && (
          <img
            src={radarImageUrl}
            alt={mapName}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'fill',
              pointerEvents: 'none',
              opacity: 0.94,
              filter: 'brightness(0.96) contrast(1.08)',
              zIndex: 1,
            }}
          />
        )}

        {/* SVG Tactical Vectors, Rings, Trails, Grenades & Gunfire */}
        <svg
          viewBox="0 0 1000 1000"
          style={{
            width: '100%',
            height: '100%',
            position: 'absolute',
            top: 0,
            left: 0,
            pointerEvents: 'none',
            zIndex: 2,
          }}
        >
          <defs>
            {/* Soft Smoke Cloud Gradient */}
            <radialGradient id="tactical-smoke-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#94a3b8" stopOpacity="0.55" />
              <stop offset="50%" stopColor="#64748b" stopOpacity="0.38" />
              <stop offset="85%" stopColor="#475569" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#334155" stopOpacity="0" />
            </radialGradient>

            {/* Fiery Molotov Flame Gradient */}
            <radialGradient id="tactical-molotov-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.75" />
              <stop offset="40%" stopColor="#f97316" stopOpacity="0.45" />
              <stop offset="75%" stopColor="#f59e0b" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
            </radialGradient>

            {/* Flashbang Detonation Burst Gradient */}
            <radialGradient id="tactical-flash-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.95" />
              <stop offset="45%" stopColor="#fef08a" stopOpacity="0.6" />
              <stop offset="85%" stopColor="#facc15" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#eab308" stopOpacity="0" />
            </radialGradient>

            {/* HE Explosion Shockwave Gradient */}
            <radialGradient id="tactical-he-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f97316" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#ef4444" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#b91c1c" stopOpacity="0" />
            </radialGradient>

            {/* FOV Vision Cone Gradients */}
            <radialGradient id="tactical-fov-ct" cx="0%" cy="0%" r="100%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.45" />
              <stop offset="65%" stopColor="#0284c7" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#0369a1" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="tactical-fov-t" cx="0%" cy="0%" r="100%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.45" />
              <stop offset="65%" stopColor="#d97706" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#b45309" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Subtle Radar Concentric Distance Rings */}
          <circle cx="500" cy="500" r="460" fill="none" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="6 6" opacity="0.12" />
          <circle cx="500" cy="500" r="280" fill="none" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="6 6" opacity="0.1" />

          {/* Player Movement Breadcrumb Trails */}
          {showTrails &&
            Object.entries(playerTrails).map(([steamId, points]) => {
              if (points.length < 2) return null
              // Check side from living players or default to CT
              const pInfo = livingPlayers.find((p) => p.steam_id === steamId)
              const isCT = pInfo?.side === 'ct'
              const stroke = isCT ? '#3b82f6' : '#f97316'
              const polyPoints = points.map((pt) => `${pt.x * 10},${pt.y * 10}`).join(' ')
              return (
                <polyline
                  key={`trail-${steamId}`}
                  points={polyPoints}
                  fill="none"
                  stroke={stroke}
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeOpacity="0.4"
                  strokeDasharray="4 2"
                />
              )
            })}

          {/* ================================================================= */}
          {/* GRENADE LAYER: SMOKES, MOLOTOVS, FLASHBANGS, HE GRENADES         */}
          {/* ================================================================= */}
          {showGrenades &&
            activeGrenades.map((g) => {
              const gx = g.x * 10
              const gy = g.y * 10
              const isInFlight = currentTick < g.detonate_tick
              const isDetonated = currentTick >= g.detonate_tick && currentTick <= g.end_tick

              // In-flight projectile trajectory
              if (isInFlight) {
                // Find current flight position from trajectory
                let flightX = gx
                let flightY = gy
                if (g.trajectory && g.trajectory.length > 0) {
                  // Find closest trajectory frame up to currentTick
                  let closest = g.trajectory[0]
                  for (const pt of g.trajectory) {
                    if (pt.tick <= currentTick) {
                      closest = pt
                    } else {
                      break
                    }
                  }
                  flightX = closest.x * 10
                  flightY = closest.y * 10
                }

                return (
                  <g key={`grenade-flight-${g.id}`}>
                    {/* Dotted path to landing */}
                    <line
                      x1={flightX}
                      y1={flightY}
                      x2={gx}
                      y2={gy}
                      stroke={g.type === 'smoke' ? '#94a3b8' : g.type === 'molotov' ? '#f97316' : '#facc15'}
                      strokeWidth="1.5"
                      strokeDasharray="3 3"
                      strokeOpacity="0.6"
                    />
                    {/* In-flight projectile indicator */}
                    <circle
                      cx={flightX}
                      cy={flightY}
                      r="4.5"
                      fill={g.type === 'smoke' ? '#94a3b8' : g.type === 'molotov' ? '#f97316' : '#facc15'}
                      stroke="#ffffff"
                      strokeWidth="1"
                    />
                  </g>
                )
              }

              // Active Detonated Grenades
              if (isDetonated) {
                // 1. SMOKE GRENADE (20.0s duration in CS2)
                if (g.type === 'smoke') {
                  const remainingSec = Math.max(0, (g.end_tick - currentTick) / tickrate)
                  const totalDur = g.duration_seconds || 20.0
                  const ratio = Math.max(0, Math.min(1, remainingSec / totalDur))
                  const isDissipating = remainingSec <= 4.0
                  const radius = 38
                  const circumference = 2 * Math.PI * radius // ~238.76
                  const strokeDash = circumference * ratio

                  return (
                    <g
                      key={`smoke-${g.id}`}
                      pointerEvents="auto"
                      onMouseEnter={() => setHoveredGrenade(g)}
                      onMouseLeave={() => setHoveredGrenade(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Volumetric Smoke Cloud Base */}
                      <circle
                        cx={gx}
                        cy={gy}
                        r={radius}
                        fill="url(#tactical-smoke-grad)"
                        opacity={isDissipating ? 0.45 : 0.85}
                        style={{
                          animation: isDissipating ? 'smokePulse 1.2s ease-in-out infinite' : undefined,
                        }}
                      />

                      {/* Subtle cloud billow rings */}
                      <circle cx={gx - 8} cy={gy - 6} r={radius * 0.72} fill="url(#tactical-smoke-grad)" opacity="0.5" />
                      <circle cx={gx + 8} cy={gy + 6} r={radius * 0.68} fill="url(#tactical-smoke-grad)" opacity="0.5" />

                      {/* Circular Countdown Progress Ring along circumference */}
                      <circle
                        cx={gx}
                        cy={gy}
                        r={radius}
                        fill="none"
                        stroke={isDissipating ? '#ef4444' : '#94a3b8'}
                        strokeWidth="2.2"
                        strokeDasharray={`${strokeDash} ${circumference}`}
                        strokeLinecap="round"
                        transform={`rotate(-90 ${gx} ${gy})`}
                        opacity={isDissipating ? 0.95 : 0.75}
                      />

                      {/* Center Smoke Badge & Remaining Seconds */}
                      <circle cx={gx} cy={gy} r="11" fill="rgba(15, 23, 42, 0.85)" stroke={isDissipating ? '#ef4444' : '#64748b'} strokeWidth="1" />
                      <text
                        x={gx}
                        y={gy + 3.5}
                        fill={isDissipating ? '#fca5a5' : '#f1f5f9'}
                        fontSize="9"
                        fontWeight="800"
                        fontFamily="monospace"
                        textAnchor="middle"
                      >
                        {Math.ceil(remainingSec)}s
                      </text>
                    </g>
                  )
                }

                // 2. MOLOTOV / INCENDIARY (7.03s duration in CS2)
                if (g.type === 'molotov') {
                  const remainingSec = Math.max(0, (g.end_tick - currentTick) / tickrate)
                  const totalDur = g.duration_seconds || 7.03
                  const ratio = Math.max(0, Math.min(1, remainingSec / totalDur))
                  const isExpiring = remainingSec <= 2.0
                  const radius = 28
                  const circumference = 2 * Math.PI * radius // ~175.93
                  const strokeDash = circumference * ratio

                  return (
                    <g
                      key={`molotov-${g.id}`}
                      pointerEvents="auto"
                      onMouseEnter={() => setHoveredGrenade(g)}
                      onMouseLeave={() => setHoveredGrenade(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Fiery Fire Zone Circle */}
                      <circle
                        cx={gx}
                        cy={gy}
                        r={radius}
                        fill="url(#tactical-molotov-grad)"
                        opacity={isExpiring ? 0.5 : 0.85}
                        style={{
                          animation: 'fireGlow 1.5s ease-in-out infinite',
                        }}
                      />

                      {/* Fire Perimeter Countdown Ring */}
                      <circle
                        cx={gx}
                        cy={gy}
                        r={radius}
                        fill="none"
                        stroke={isExpiring ? '#dc2626' : '#f97316'}
                        strokeWidth="2.5"
                        strokeDasharray={`${strokeDash} ${circumference}`}
                        strokeLinecap="round"
                        transform={`rotate(-90 ${gx} ${gy})`}
                        opacity="0.9"
                      />

                      {/* Center Molotov Badge */}
                      <circle cx={gx} cy={gy} r="10" fill="rgba(24, 10, 10, 0.9)" stroke="#f97316" strokeWidth="1" />
                      <text
                        x={gx}
                        y={gy + 3.5}
                        fill="#fed7aa"
                        fontSize="8.5"
                        fontWeight="800"
                        fontFamily="monospace"
                        textAnchor="middle"
                      >
                        {remainingSec.toFixed(1)}s
                      </text>
                    </g>
                  )
                }

                // 3. FLASHBANG BURST (~1.2s post-detonation)
                if (g.type === 'flash') {
                  const elapsedSec = (currentTick - g.detonate_tick) / tickrate
                  if (elapsedSec >= 0 && elapsedSec <= 1.2) {
                    const radius = 10 + elapsedSec * 35
                    const opacity = Math.max(0, 1 - elapsedSec / 1.2) * 0.9
                    return (
                      <g key={`flash-${g.id}`}>
                        <circle cx={gx} cy={gy} r={radius} fill="url(#tactical-flash-grad)" opacity={opacity} />
                        <circle cx={gx} cy={gy} r={radius * 1.15} fill="none" stroke="#fef08a" strokeWidth="1.5" opacity={opacity * 0.8} />
                      </g>
                    )
                  }
                }

                // 4. HE GRENADE EXPLOSION SHOCKWAVE (~1.0s post-detonation)
                if (g.type === 'he') {
                  const elapsedSec = (currentTick - g.detonate_tick) / tickrate
                  if (elapsedSec >= 0 && elapsedSec <= 1.0) {
                    const radius = 12 + elapsedSec * 30
                    const opacity = Math.max(0, 1 - elapsedSec / 1.0) * 0.85
                    return (
                      <g key={`he-${g.id}`}>
                        <circle cx={gx} cy={gy} r={radius} fill="url(#tactical-he-grad)" opacity={opacity * 0.5} />
                        <circle cx={gx} cy={gy} r={radius} fill="none" stroke="#f97316" strokeWidth="2" strokeDasharray="4 2" opacity={opacity} />
                      </g>
                    )
                  }
                }
              }

              return null
            })}

          {/* Active Gunfire Muzzle Burst & Tracer Beams (Recent Kills Only) */}
          {showShots &&
            pastKills
              .filter((k) => {
                const dt = (currentTick - k.tick) / tickrate
                return dt >= 0 && dt <= 1.8
              })
              .map((k, i) => (
                <g key={`shot-${i}`}>
                  <line
                    x1={k.attacker_x * 10}
                    y1={k.attacker_y * 10}
                    x2={k.victim_x * 10}
                    y2={k.victim_y * 10}
                    stroke="#facc15"
                    strokeWidth="3.5"
                    strokeOpacity="0.9"
                  />
                  <circle
                    cx={k.attacker_x * 10}
                    cy={k.attacker_y * 10}
                    r="12"
                    fill="rgba(250, 204, 21, 0.45)"
                    stroke="#facc15"
                    strokeWidth="2"
                  />
                </g>
              ))}

          {/* Kill Vector Lines: ONLY for recent kills (<= 3.5s) OR when hovering over a kill marker */}
          {pastKills
            .filter((k) => {
              const ageSec = (currentTick - k.tick) / tickrate
              return (ageSec >= 0 && ageSec <= 3.5) || (hoveredKill && hoveredKill.tick === k.tick)
            })
            .map((k, i) => {
              const ageSec = (currentTick - k.tick) / tickrate
              const opacity = hoveredKill?.tick === k.tick ? 0.95 : Math.max(0.2, (3.5 - ageSec) / 3.5)
              return (
                <line
                  key={`kill-line-${i}`}
                  x1={k.attacker_x * 10}
                  y1={k.attacker_y * 10}
                  x2={k.victim_x * 10}
                  y2={k.victim_y * 10}
                  stroke={k.attacker_side === 'ct' ? '#38bdf8' : '#f97316'}
                  strokeWidth={hoveredKill?.tick === k.tick ? '2.5' : '1.5'}
                  strokeDasharray="4 3"
                  opacity={opacity}
                />
              )
            })}

          {/* ================================================================= */}
          {/* PLAYER FOV CONES & VISION DIRECTION (SOURCE 2 YAW TELEMETRY)      */}
          {/* ================================================================= */}
          {showFovCones &&
            livingPlayers.map((p) => {
              const isCurrentLevel = hasMultipleLevels ? p.level === currentLevel : true
              if (!isCurrentLevel) return null
              const isCT = p.side === 'ct'
              const yaw = p.yaw ?? 0
              const isFocused = focusedSteamId === p.steam_id
              const coneRadius = isFocused ? 76 : 52
              const gradId = isCT ? 'tactical-fov-ct' : 'tactical-fov-t'
              const strokeColor = isCT ? '#38bdf8' : '#fbbf24'
              // 90 degree FOV cone (-45 to +45 deg)
              const rCos = coneRadius * 0.7071
              const rSin = coneRadius * 0.7071

              return (
                <g
                  key={`fov-${p.steam_id}`}
                  transform={`translate(${p.x * 10}, ${p.y * 10}) rotate(${-yaw})`}
                  opacity={isFocused ? 1.0 : focusedSteamId ? 0.35 : 0.85}
                  style={{ pointerEvents: 'none', transition: 'transform 0.12s linear' }}
                >
                  {/* FOV Cone Sector */}
                  <path
                    d={`M 0 0 L ${rCos.toFixed(1)} ${(-rSin).toFixed(1)} A ${coneRadius} ${coneRadius} 0 0 1 ${rCos.toFixed(1)} ${rSin.toFixed(1)} Z`}
                    fill={`url(#${gradId})`}
                    stroke={strokeColor}
                    strokeWidth="0.8"
                    strokeOpacity="0.4"
                  />
                  {/* Center Line of Sight Pointer */}
                  <line
                    x1="0"
                    y1="0"
                    x2={coneRadius}
                    y2="0"
                    stroke={strokeColor}
                    strokeWidth={isFocused ? '2' : '1.2'}
                    strokeOpacity="0.85"
                  />
                  <circle cx={coneRadius} cy="0" r="1.5" fill={strokeColor} opacity="0.9" />
                </g>
              )
            })}

          {/* ================================================================= */}
          {/* TACTICAL DRAWING LAYER (PHASE 2 PERSISTENT VECTOR OVERLAY)        */}
          {/* ================================================================= */}
          {drawings.map((d) => {
            try {
              const geom = JSON.parse(d.geometry_json)
              if (d.layer_type === 'pen' && geom.points && geom.points.length > 1) {
                const poly = geom.points.map((pt: [number, number]) => `${pt[0]},${pt[1]}`).join(' ')
                return (
                  <polyline
                    key={d.id}
                    points={poly}
                    fill="none"
                    stroke={d.color}
                    strokeWidth={d.stroke_width}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity={0.92}
                  />
                )
              }
              if (d.layer_type === 'arrow' && geom.x1 !== undefined) {
                const { x1, y1, x2, y2 } = geom
                const angle = Math.atan2(y2 - y1, x2 - x1)
                const arrowLen = 14
                const arrowWidth = 7
                const pLeftX = x2 - arrowLen * Math.cos(angle) + arrowWidth * Math.sin(angle)
                const pLeftY = y2 - arrowLen * Math.sin(angle) - arrowWidth * Math.cos(angle)
                const pRightX = x2 - arrowLen * Math.cos(angle) - arrowWidth * Math.sin(angle)
                const pRightY = y2 - arrowLen * Math.sin(angle) + arrowWidth * Math.cos(angle)
                return (
                  <g key={d.id} opacity={0.92}>
                    <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={d.color} strokeWidth={d.stroke_width} strokeLinecap="round" />
                    <polygon points={`${x2},${y2} ${pLeftX},${pLeftY} ${pRightX},${pRightY}`} fill={d.color} />
                    {d.text_label && (
                      <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 8} fill={d.color} fontSize="12" fontWeight="800" textAnchor="middle">
                        {d.text_label}
                      </text>
                    )}
                  </g>
                )
              }
              if (d.layer_type === 'line' && geom.x1 !== undefined) {
                return (
                  <line
                    key={d.id}
                    x1={geom.x1}
                    y1={geom.y1}
                    x2={geom.x2}
                    y2={geom.y2}
                    stroke={d.color}
                    strokeWidth={d.stroke_width}
                    strokeLinecap="round"
                    opacity={0.9}
                  />
                )
              }
              if (d.layer_type === 'circle' && geom.cx !== undefined) {
                return (
                  <ellipse
                    key={d.id}
                    cx={geom.cx}
                    cy={geom.cy}
                    rx={geom.rx}
                    ry={geom.ry}
                    fill={`${d.color}22`}
                    stroke={d.color}
                    strokeWidth={d.stroke_width}
                    opacity={0.88}
                  />
                )
              }
              if (d.layer_type === 'box' && geom.x !== undefined) {
                return (
                  <rect
                    key={d.id}
                    x={geom.x}
                    y={geom.y}
                    width={geom.w}
                    height={geom.h}
                    fill={`${d.color}22`}
                    stroke={d.color}
                    strokeWidth={d.stroke_width}
                    opacity={0.88}
                  />
                )
              }
              if (d.layer_type === 'text' && geom.x !== undefined) {
                return (
                  <text
                    key={d.id}
                    x={geom.x}
                    y={geom.y}
                    fill={d.color}
                    fontSize="13"
                    fontWeight="800"
                    fontFamily="monospace"
                    filter="drop-shadow(0 2px 4px rgba(0,0,0,0.9))"
                  >
                    {d.text_label || 'Tactical Note'}
                  </text>
                )
              }
            } catch {
              return null
            }
            return null
          })}

          {/* Active Live In-Progress Drawing Shape */}
          {isDrawingMode && isDrawingActive && activeDragStart && activeDragCurrent && (
            <g opacity={0.85}>
              {activeDrawTool === 'pen' && penPoints.length > 1 && (
                <polyline
                  points={penPoints.map((pt) => `${pt[0]},${pt[1]}`).join(' ')}
                  fill="none"
                  stroke={drawColor}
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                />
              )}
              {activeDrawTool === 'arrow' && (
                <>
                  <line
                    x1={activeDragStart.x}
                    y1={activeDragStart.y}
                    x2={activeDragCurrent.x}
                    y2={activeDragCurrent.y}
                    stroke={drawColor}
                    strokeWidth={strokeWidth}
                    strokeDasharray="4 2"
                  />
                  <circle cx={activeDragCurrent.x} cy={activeDragCurrent.y} r="4" fill={drawColor} />
                </>
              )}
              {activeDrawTool === 'line' && (
                <line
                  x1={activeDragStart.x}
                  y1={activeDragStart.y}
                  x2={activeDragCurrent.x}
                  y2={activeDragCurrent.y}
                  stroke={drawColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray="4 2"
                />
              )}
              {activeDrawTool === 'circle' && (
                <ellipse
                  cx={activeDragStart.x}
                  cy={activeDragStart.y}
                  rx={Math.abs(activeDragCurrent.x - activeDragStart.x)}
                  ry={Math.abs(activeDragCurrent.y - activeDragStart.y)}
                  fill={`${drawColor}22`}
                  stroke={drawColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray="4 2"
                />
              )}
              {activeDrawTool === 'box' && (
                <rect
                  x={Math.min(activeDragStart.x, activeDragCurrent.x)}
                  y={Math.min(activeDragStart.y, activeDragCurrent.y)}
                  width={Math.abs(activeDragCurrent.x - activeDragStart.x)}
                  height={Math.abs(activeDragCurrent.y - activeDragStart.y)}
                  fill={`${drawColor}22`}
                  stroke={drawColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray="4 2"
                />
              )}
            </g>
          )}
        </svg>

        {/* ================================================================= */}
        {/* LIVING PLAYERS (HTML OVERLAYS) — TOKENS, BADGES, WEAPONS & FOCUS  */}
        {/* ================================================================= */}
        {livingPlayers.map((p) => {
          const isCurrentLevel = hasMultipleLevels ? p.level === currentLevel : true
          const isCT = p.side === 'ct'
          const teamColor = isCT ? '#38bdf8' : '#f97316'
          const isFocused = focusedSteamId === p.steam_id
          const isDimmed = Boolean(focusedSteamId && !isFocused)
          const opacity = isCurrentLevel ? (isDimmed ? 0.38 : 1) : 0.18

          const hpColor = p.health >= 50 ? '#22c55e' : p.health >= 20 ? '#f59e0b' : '#ef4444'

          return (
            <div
              key={p.steam_id}
              onClick={() => setFocusedSteamId((prev) => (prev === p.steam_id ? null : p.steam_id))}
              title={
                lang === 'ru'
                  ? `${p.name} (${p.side.toUpperCase()}) | HP: ${Math.round(p.health)} | Броня: ${p.armor ?? 0}%${p.has_helmet ? ' + Шлем' : ''}${p.has_defuser ? ' | Кит' : ''}${p.weapon ? ` | ${p.weapon}` : ''}\nКлик для фокуса на игроке`
                  : `${p.name} (${p.side.toUpperCase()}) | HP: ${Math.round(p.health)} | Armor: ${p.armor ?? 0}%${p.has_helmet ? ' + Helmet' : ''}${p.has_defuser ? ' | Defuser' : ''}${p.weapon ? ` | ${p.weapon}` : ''}\nClick to focus player`
              }
              style={{
                position: 'absolute',
                left: `${Math.max(2, Math.min(98, p.x))}%`,
                top: `${Math.max(2, Math.min(98, p.y))}%`,
                transform: 'translate(-50%, -50%)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                pointerEvents: 'auto',
                cursor: 'pointer',
                opacity,
                transition: 'left 0.12s linear, top 0.12s linear, opacity 0.2s ease',
                zIndex: isFocused ? 25 : isCurrentLevel ? 15 : 2,
              }}
            >
              {/* Focused Selection Ring */}
              {isFocused && (
                <div
                  style={{
                    position: 'absolute',
                    top: '-6px',
                    left: '-6px',
                    right: '-6px',
                    bottom: '-6px',
                    borderRadius: '50%',
                    border: '2px solid #00f2fe',
                    animation: 'focusPulse 1.2s ease-in-out infinite',
                    pointerEvents: 'none',
                  }}
                />
              )}

              {/* Flashed Blind Ring */}
              {p.is_flashed && (
                <div
                  style={{
                    position: 'absolute',
                    top: '-7px',
                    left: '-7px',
                    right: '-7px',
                    bottom: '-7px',
                    borderRadius: '50%',
                    border: '2.5px solid #facc15',
                    backgroundColor: 'rgba(250, 204, 21, 0.3)',
                    animation: 'blindPulse 0.8s ease-in-out infinite',
                    pointerEvents: 'none',
                  }}
                />
              )}

              {/* Tactical Player Dot with Team Background & Dual Health Border */}
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  backgroundColor: teamColor,
                  border: `2px solid ${hpColor}`,
                  boxShadow: isFocused
                    ? '0 0 14px #00f2fe'
                    : `0 0 8px ${teamColor}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '9.5px',
                  fontWeight: 900,
                  color: '#ffffff',
                  transform: `scale(${dotScale})`,
                  transformOrigin: 'center center',
                  position: 'relative',
                }}
              >
                {isCT ? 'CT' : 'T'}

                {/* Defuser Badge for CT */}
                {p.has_defuser && isCT && showEquipment && (
                  <span
                    style={{
                      position: 'absolute',
                      top: '-6px',
                      right: '-6px',
                      fontSize: '9px',
                      filter: 'drop-shadow(0 0 3px #0284c7)',
                      lineHeight: 1,
                    }}
                  >
                    ✂️
                  </span>
                )}
              </div>

              {/* Player Name, Health & Weapon Pill */}
              {isCurrentLevel && nameScale > 0 && (
                <div
                  style={{
                    marginTop: '2px',
                    backgroundColor: 'rgba(9, 12, 18, 0.94)',
                    backdropFilter: 'blur(4px)',
                    padding: nameDensity === 'compact' ? '1px 4px' : '2px 5px',
                    borderRadius: '4px',
                    border: isFocused ? '1px solid #00f2fe' : `1px solid ${teamColor}66`,
                    fontSize: '9px',
                    fontWeight: 700,
                    color: '#f1f5f9',
                    whiteSpace: 'nowrap',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '1px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.6)',
                    transform: `scale(${nameScale})`,
                    transformOrigin: 'top center',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                    <span>{nameDensity === 'compact' ? p.name.slice(0, 5) : p.name.slice(0, 11)}</span>
                    <span
                      style={{
                        color: hpColor,
                        fontSize: '9.5px',
                        fontWeight: 800,
                      }}
                    >
                      {Math.round(p.health)}
                    </span>
                  </div>

                  {/* Weapon & Armor Badges Row */}
                  {showEquipment && (p.weapon || (p.armor !== undefined && p.armor > 0)) && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '3px',
                        fontSize: '7.5px',
                        color: '#94a3b8',
                        borderTop: '1px solid rgba(255,255,255,0.08)',
                        paddingTop: '1px',
                        width: '100%',
                        justifyContent: 'center',
                      }}
                    >
                      {p.weapon && p.weapon !== 'knife' && (
                        <span style={{ color: '#cbd5e1', fontWeight: 600 }}>{p.weapon}</span>
                      )}
                      {p.armor !== undefined && p.armor > 0 && (
                        <span style={{ color: p.has_helmet ? '#38bdf8' : '#64748b' }}>
                          🛡️{p.armor}{p.has_helmet ? 'H' : ''}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {/* ================================================================= */}
        {/* ACTIVE UTILITY TIMERS & BADGES (CRISP HIGH-CONTRAST HTML LAYER)   */}
        {/* ================================================================= */}
        {showGrenades &&
          detonatedGrenades.map((g) => {
            const isSmoke = g.type === 'smoke'
            const remainingSec = Math.max(0, (g.end_tick - currentTick) / tickrate)
            const isExpiring = isSmoke ? remainingSec <= 4.0 : remainingSec <= 2.0
            const timerScale = Math.max(0.65, 1 / Math.pow(zoom, 0.6))

            return (
              <div
                key={`html-grenade-timer-${g.id}`}
                onClick={() => onJumpToTick?.(g.detonate_tick)}
                onMouseEnter={() => setHoveredGrenade(g)}
                onMouseLeave={() => setHoveredGrenade(null)}
                title={
                  lang === 'ru'
                    ? `${isSmoke ? '💨 Дым' : '🔥 Огонь'}: осталось ${isSmoke ? Math.ceil(remainingSec) : remainingSec.toFixed(1)}с. Бросил: ${g.thrower_name || 'Игрок'}`
                    : `${isSmoke ? '💨 Smoke' : '🔥 Fire'}: ${isSmoke ? Math.ceil(remainingSec) : remainingSec.toFixed(1)}s remaining. Thrown by: ${g.thrower_name || 'Player'}`
                }
                style={{
                  position: 'absolute',
                  left: `${Math.max(2, Math.min(98, g.x))}%`,
                  top: `${Math.max(2, Math.min(98, g.y))}%`,
                  transform: `translate(-50%, -50%) scale(${timerScale})`,
                  zIndex: 22,
                  pointerEvents: 'auto',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '2px 7px',
                  borderRadius: '6px',
                  backgroundColor: isExpiring ? 'rgba(220, 38, 38, 0.95)' : 'rgba(11, 15, 25, 0.94)',
                  backdropFilter: 'blur(6px)',
                  border: `1.5px solid ${isExpiring ? '#fca5a5' : isSmoke ? '#38bdf8' : '#f97316'}`,
                  boxShadow: `0 0 12px ${isExpiring ? 'rgba(239, 68, 68, 0.9)' : isSmoke ? 'rgba(56, 189, 248, 0.6)' : 'rgba(249, 115, 22, 0.8)'}`,
                  fontSize: '11px',
                  fontWeight: 900,
                  fontFamily: 'monospace',
                  color: '#ffffff',
                  whiteSpace: 'nowrap',
                  animation: isExpiring ? 'timerUrgentPulse 0.6s ease-in-out infinite' : undefined,
                  transition: 'border-color 0.2s, background-color 0.2s',
                }}
              >
                <span>{isSmoke ? '💨' : '🔥'}</span>
                <span style={{ color: isExpiring ? '#ffffff' : isSmoke ? '#e2e8f0' : '#fed7aa' }}>
                  {isSmoke ? `${Math.ceil(remainingSec)}s` : `${remainingSec.toFixed(1)}s`}
                </span>
              </div>
            )
          })}

        {/* ================================================================= */}
        {/* PLANTED C4 BOMB TIMER & BEACON (IF PLANTED & ACTIVE)              */}
        {/* ================================================================= */}
        {bomb && currentTick >= bomb.plant_tick && currentTick <= bomb.plant_tick + 40 * tickrate && (
          <div
            style={{
              position: 'absolute',
              left: `${Math.max(2, Math.min(98, bomb.x))}%`,
              top: `${Math.max(2, Math.min(98, bomb.y))}%`,
              transform: `translate(-50%, -50%) scale(${Math.max(0.65, 1 / Math.pow(zoom, 0.6))})`,
              zIndex: 26,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              pointerEvents: 'auto',
              cursor: 'pointer',
            }}
            onClick={() => onJumpToTick?.(bomb.plant_tick)}
            title={lang === 'ru' ? `💣 Бомба C4 установлена на Плент ${bomb.site || 'CS2'}. Клик для перехода к установке` : `💣 C4 planted at Site ${bomb.site || 'CS2'}. Click to jump to plant`}
          >
            {/* Pulsing Beacon Ring */}
            <div
              style={{
                position: 'absolute',
                top: '-8px',
                left: '-8px',
                width: '38px',
                height: '38px',
                borderRadius: '50%',
                border: '2px solid #ef4444',
                animation: 'radarBombPing 1.2s cubic-bezier(0, 0, 0.2, 1) infinite',
                pointerEvents: 'none',
              }}
            />
            {/* Main C4 Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: 'rgba(220, 38, 38, 0.95)',
                border: '2px solid #ffffff',
                boxShadow: '0 0 16px rgba(239, 68, 68, 1)',
                color: '#ffffff',
                fontSize: '11px',
                fontWeight: 900,
                fontFamily: 'monospace',
                whiteSpace: 'nowrap',
              }}
            >
              <span>💣</span>
              <span>{bomb.site ? (lang === 'ru' ? `ПЛЕНТ ${bomb.site}` : `PLANT ${bomb.site}`) : 'C4'}:</span>
              <span style={{ color: '#fef08a' }}>
                {Math.max(0, 40 - (currentTick - bomb.plant_tick) / tickrate).toFixed(1)}s
              </span>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* KILL MARKERS (TEMPORAL DECAY TO ELIMINATE CLUTTER)               */}
        {/* ================================================================= */}
        {pastKills.map((k, i) => {
          const ageSec = (currentTick - k.tick) / tickrate
          const isRecent = ageSec >= 0 && ageSec <= 3.5

          if (isRecent) {
            // RECENT KILL (<= 3.5 seconds): Active prominent death event with ping animation
            return (
              <div
                key={`kill-recent-${i}`}
                onClick={() => onJumpToTick?.(k.tick)}
                onMouseEnter={() => setHoveredKill(k)}
                onMouseLeave={() => setHoveredKill(null)}
                title={lang === 'ru' ? `💀 Килл: ${k.attacker_name} ➔ ${k.victim_name}. Клик для перехода` : `💀 Kill: ${k.attacker_name} ➔ ${k.victim_name}. Click to jump`}
                style={{
                  position: 'absolute',
                  left: `${Math.max(2, Math.min(98, k.victim_x))}%`,
                  top: `${Math.max(2, Math.min(98, k.victim_y))}%`,
                  transform: 'translate(-50%, -50%)',
                  zIndex: 25,
                  cursor: 'pointer',
                  pointerEvents: 'auto',
                }}
              >
                {/* Expanding Pulsing Ping Ring */}
                <div
                  style={{
                    position: 'absolute',
                    top: '-6px',
                    left: '-6px',
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    border: '2px solid #ef4444',
                    animation: 'radarPing 1.2s cubic-bezier(0, 0, 0.2, 1) infinite',
                    pointerEvents: 'none',
                  }}
                />

                {/* Main Kill Badge */}
                <div
                  style={{
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    backgroundColor: '#ef4444',
                    border: '1.5px solid #ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 0 10px rgba(239, 68, 68, 0.9)',
                  }}
                >
                  <SkullIcon size={10} color="#ffffff" />
                </div>
              </div>
            )
          }

          // HISTORICAL / OLDER KILL (> 3.5 seconds): Faint, unobtrusive tactical death marker
          return (
            <div
              key={`kill-past-${i}`}
              onClick={() => onJumpToTick?.(k.tick)}
              onMouseEnter={() => setHoveredKill(k)}
              onMouseLeave={() => setHoveredKill(null)}
              title={lang === 'ru' ? `💀 ${k.attacker_name} [${k.weapon || 'kill'}] ➔ ${k.victim_name}. Клик для перехода к тику` : `💀 ${k.attacker_name} [${k.weapon || 'kill'}] ➔ ${k.victim_name}. Click to jump to tick`}
              style={{
                position: 'absolute',
                left: `${Math.max(2, Math.min(98, k.victim_x))}%`,
                top: `${Math.max(2, Math.min(98, k.victim_y))}%`,
                transform: hoveredKill === k ? 'translate(-50%, -50%) scale(1.3)' : 'translate(-50%, -50%)',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: hoveredKill === k ? 'rgba(239, 68, 68, 0.9)' : 'rgba(15, 23, 42, 0.75)',
                border: hoveredKill === k ? '1.5px solid #ffffff' : '1px solid rgba(239, 68, 68, 0.45)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: hoveredKill === k ? 1 : 0.35,
                zIndex: hoveredKill === k ? 28 : 5,
                cursor: 'pointer',
                pointerEvents: 'auto',
                transition: 'all 0.15s ease',
              }}
            >
              <SkullIcon size={hoveredKill === k ? 7 : 6} color={hoveredKill === k ? '#ffffff' : '#f87171'} />
            </div>
          )
        })}

        {/* Text Label Input Popover Modal */}
        {textPromptOpen && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              zIndex: 60,
              backgroundColor: 'rgba(0, 0, 0, 0.65)',
              backdropFilter: 'blur(4px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            onClick={(e) => {
              if (e.target === e.currentTarget) setTextPromptOpen(false)
            }}
          >
            <div
              style={{
                backgroundColor: '#0b0f19',
                border: '1px solid #00f2fe',
                borderRadius: '10px',
                padding: '16px',
                width: '320px',
                boxShadow: '0 8px 32px rgba(0, 242, 254, 0.25)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '13px', fontWeight: 800, color: '#00f2fe', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  🔤 {lang === 'ru' ? 'Тактическая надпись' : 'Tactical Text Label'}
                </span>
                <button
                  type="button"
                  onClick={() => setTextPromptOpen(false)}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '14px' }}
                >
                  ✕
                </button>
              </div>
              <input
                type="text"
                autoFocus
                value={textInputValue}
                onChange={(e) => setTextInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveTextLabel()
                  if (e.key === 'Escape') setTextPromptOpen(false)
                }}
                placeholder={lang === 'ru' ? 'Напр: Сплит Б, Окно, Перетяжка...' : 'e.g. B Split, Window, Rotate...'}
                style={{
                  backgroundColor: '#131926',
                  border: '1px solid rgba(0, 242, 254, 0.3)',
                  borderRadius: '6px',
                  padding: '8px 10px',
                  color: '#ffffff',
                  fontSize: '13px',
                  outline: 'none',
                }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setTextPromptOpen(false)}
                  style={{
                    padding: '5px 12px',
                    borderRadius: '6px',
                    backgroundColor: 'transparent',
                    border: '1px solid #334155',
                    color: '#94a3b8',
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  {lang === 'ru' ? 'Отмена' : 'Cancel'}
                </button>
                <button
                  type="button"
                  onClick={handleSaveTextLabel}
                  style={{
                    padding: '5px 14px',
                    borderRadius: '6px',
                    backgroundColor: '#00f2fe',
                    border: 'none',
                    color: '#000000',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  {lang === 'ru' ? 'Добавить' : 'Add'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Quick-Add Bookmark Modal */}
        {bookmarkModalOpen && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              zIndex: 60,
              backgroundColor: 'rgba(0, 0, 0, 0.72)',
              backdropFilter: 'blur(5px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            onClick={(e) => {
              if (e.target === e.currentTarget) setBookmarkModalOpen(false)
            }}
          >
            <div
              style={{
                backgroundColor: '#0b0f19',
                border: '1.5px solid rgba(250, 204, 21, 0.6)',
                borderRadius: '12px',
                padding: '18px',
                width: '360px',
                maxWidth: '92%',
                boxShadow: '0 12px 36px rgba(0, 0, 0, 0.8), 0 0 24px rgba(250, 204, 21, 0.2)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '15px' }}>🔖</span>
                  <span style={{ fontSize: '14px', fontWeight: 800, color: '#facc15' }}>
                    {lang === 'ru' ? 'Новая тактическая закладка' : 'New Tactical Bookmark'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setBookmarkModalOpen(false)}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '16px' }}
                >
                  ✕
                </button>
              </div>

              <div style={{ display: 'flex', gap: '8px', fontSize: '11px', color: '#94a3b8' }}>
                <span style={{ backgroundColor: '#1e293b', padding: '2px 6px', borderRadius: '4px' }}>
                  {lang === 'ru' ? `Раунд ${roundNum}` : `Round ${roundNum}`}
                </span>
                <span style={{ backgroundColor: '#1e293b', padding: '2px 6px', borderRadius: '4px', fontFamily: 'monospace' }}>
                  {lang === 'ru' ? `Тик ${currentTick}` : `Tick ${currentTick}`}
                </span>
                {focusedSteamId && (
                  <span style={{ backgroundColor: '#1e293b', padding: '2px 6px', borderRadius: '4px', color: '#38bdf8' }}>
                    👤 {players.find((p) => p.steam_id === focusedSteamId)?.name || 'Player'}
                  </span>
                )}
              </div>

              <div>
                <label style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  {lang === 'ru' ? 'Название события' : 'Bookmark Title'}
                </label>
                <input
                  type="text"
                  autoFocus
                  value={bmTitle}
                  onChange={(e) => setBmTitle(e.target.value)}
                  placeholder="R1 [1:15] Вход на плент..."
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    backgroundColor: '#131926',
                    border: '1px solid rgba(250, 204, 21, 0.3)',
                    borderRadius: '6px',
                    padding: '7px 10px',
                    color: '#ffffff',
                    fontSize: '12px',
                    outline: 'none',
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  {lang === 'ru' ? 'Категория' : 'Category'}
                </label>
                <select
                  value={bmCategory}
                  onChange={(e) => setBmCategory(e.target.value)}
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    backgroundColor: '#131926',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    padding: '7px 10px',
                    color: '#f8fafc',
                    fontSize: '12px',
                    outline: 'none',
                  }}
                >
                  <option value="TACTICAL_MISTAKE">❌ {lang === 'ru' ? 'Тактическая ошибка' : 'Tactical Mistake'}</option>
                  <option value="CLUTCH">👑 {lang === 'ru' ? 'Клатч' : 'Clutch'}</option>
                  <option value="UTILITY_SETUP">🎯 {lang === 'ru' ? 'Раскидка / Сетап' : 'Utility Setup'}</option>
                  <option value="COMM_ERROR">🔇 {lang === 'ru' ? 'Ошибка коммуникации' : 'Comm Error'}</option>
                  <option value="GREAT_PLAY">⭐ {lang === 'ru' ? 'Отличный мув' : 'Great Play'}</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  {lang === 'ru' ? 'Заметки / Разбор (опционально)' : 'Notes / Breakdown (optional)'}
                </label>
                <textarea
                  value={bmNotes}
                  onChange={(e) => setBmNotes(e.target.value)}
                  rows={3}
                  placeholder={lang === 'ru' ? 'Что пошло не так или что сработало идеально...' : 'What went wrong or what worked well...'}
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    backgroundColor: '#131926',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    color: '#e2e8f0',
                    fontSize: '12px',
                    outline: 'none',
                    resize: 'none',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '4px' }}>
                <button
                  type="button"
                  onClick={() => setBookmarkModalOpen(false)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '6px',
                    backgroundColor: 'transparent',
                    border: '1px solid #334155',
                    color: '#94a3b8',
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  {lang === 'ru' ? 'Отмена' : 'Cancel'}
                </button>
                <button
                  type="button"
                  onClick={handleSaveBookmark}
                  disabled={!bmTitle.trim()}
                  style={{
                    padding: '6px 16px',
                    borderRadius: '6px',
                    backgroundColor: bmTitle.trim() ? '#facc15' : '#475569',
                    border: 'none',
                    color: '#000000',
                    fontSize: '12px',
                    fontWeight: 800,
                    cursor: bmTitle.trim() ? 'pointer' : 'not-allowed',
                  }}
                >
                  {lang === 'ru' ? 'Сохранить' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Bookmarks Drawer */}
        {bookmarksDrawerOpen && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              right: 0,
              bottom: 0,
              width: '310px',
              maxWidth: '85%',
              zIndex: 55,
              backgroundColor: 'rgba(9, 13, 20, 0.96)',
              backdropFilter: 'blur(12px)',
              borderLeft: '1px solid #1e293b',
              boxShadow: '-8px 0 24px rgba(0, 0, 0, 0.7)',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Drawer Header */}
            <div
              style={{
                padding: '12px 14px',
                borderBottom: '1px solid #1e293b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '15px' }}>📑</span>
                <span style={{ fontSize: '13px', fontWeight: 800, color: '#facc15' }}>
                  {lang === 'ru' ? 'Тактические закладки' : 'Bookmarks'}
                </span>
                <span
                  style={{
                    backgroundColor: 'rgba(250, 204, 21, 0.2)',
                    color: '#facc15',
                    padding: '1px 6px',
                    borderRadius: '10px',
                    fontSize: '11px',
                    fontWeight: 800,
                  }}
                >
                  {bookmarks.length}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setBookmarksDrawerOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '16px',
                  padding: '2px 6px',
                }}
              >
                ✕
              </button>
            </div>

            {/* Drawer List */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {bookmarks.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '30px 10px', color: '#64748b', fontSize: '12px' }}>
                  {lang === 'ru'
                    ? 'Закладок пока нет. Нажмите 🔖 + на панели, чтобы сохранить ключевой момент.'
                    : 'No bookmarks yet. Click 🔖 + on the toolbar to bookmark this moment.'}
                </div>
              ) : (
                bookmarks.map((b) => {
                  const categoryColor =
                    b.category === 'TACTICAL_MISTAKE'
                      ? '#ef4444'
                      : b.category === 'CLUTCH'
                      ? '#c084fc'
                      : b.category === 'UTILITY_SETUP'
                      ? '#38bdf8'
                      : b.category === 'COMM_ERROR'
                      ? '#fb923c'
                      : '#4ade80'

                  const categoryLabel =
                    b.category === 'TACTICAL_MISTAKE'
                      ? (lang === 'ru' ? 'Ошибка' : 'Mistake')
                      : b.category === 'CLUTCH'
                      ? (lang === 'ru' ? 'Клатч' : 'Clutch')
                      : b.category === 'UTILITY_SETUP'
                      ? (lang === 'ru' ? 'Сетап' : 'Setup')
                      : b.category === 'COMM_ERROR'
                      ? (lang === 'ru' ? 'Связь' : 'Comm')
                      : (lang === 'ru' ? 'Мув' : 'Play')

                  return (
                    <div
                      key={b.id}
                      style={{
                        backgroundColor: '#111726',
                        border: '1px solid #1e293b',
                        borderRadius: '8px',
                        padding: '8px 10px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                        transition: 'border-color 0.15s ease',
                        cursor: 'pointer',
                      }}
                      onClick={() => onJumpToTick?.(b.tick)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <span
                            style={{
                              fontSize: '9px',
                              fontWeight: 800,
                              padding: '1px 5px',
                              borderRadius: '4px',
                              backgroundColor: `${categoryColor}25`,
                              color: categoryColor,
                              border: `1px solid ${categoryColor}60`,
                            }}
                          >
                            {categoryLabel}
                          </span>
                          <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                            R{b.round_num} • #{b.tick}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            setBookmarks((prev) => prev.filter((item) => item.id !== b.id))
                            if (b.id && !b.id.startsWith('bm_')) {
                              onDeleteBookmark?.(b.id)
                            }
                          }}
                          title={lang === 'ru' ? 'Удалить закладку' : 'Delete bookmark'}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#64748b',
                            cursor: 'pointer',
                            fontSize: '12px',
                            padding: '0 4px',
                          }}
                        >
                          ✕
                        </button>
                      </div>

                      <div style={{ fontSize: '12px', fontWeight: 700, color: '#f1f5f9' }}>
                        {b.title}
                      </div>

                      {b.notes && (
                        <div style={{ fontSize: '11px', color: '#94a3b8', fontStyle: 'italic', lineHeight: 1.3 }}>
                          {b.notes}
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
