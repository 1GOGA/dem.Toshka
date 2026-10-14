import React, { useState } from 'react'

export interface CrosshairConfig {
  preset: string
  color: string
  fov?: number
  viewmodelFov?: number
  hudMode?: string
  customCrosshair?: boolean
  size?: number
  gap?: number
  thickness?: number
  outline?: boolean
  dot?: boolean
}

interface InteractiveCrosshairPreviewProps {
  config: CrosshairConfig
  onChangeConfig?: (newConfig: Partial<CrosshairConfig>) => void
  interactiveControls?: boolean
}

// Color palette mapping
const COLOR_MAP: Record<string, string> = {
  cyan: '#00ffb4',
  green: '#00ff22',
  yellow: '#ffd700',
  white: '#ffffff',
  pink: '#ff4da6',
  blue: '#38bdf8',
  red: '#ff3344',
  orange: '#ff8800',
}

// Background scene definitions
type SceneId = 'dust2' | 'mirage' | 'inferno' | 'nuke' | 'skybox' | 'smoke'

interface SceneInfo {
  id: SceneId
  name: string
  map: string
  desc: string
  bgGradient: string
  accentColor: string
}

const SCENES: SceneInfo[] = [
  {
    id: 'dust2',
    name: 'Dust II — Long A',
    map: 'de_dust2',
    desc: 'Песчаные текстуры и яркое освещение угла Long',
    bgGradient: 'radial-gradient(ellipse at 50% 45%, #7a6345 0%, #3e3223 50%, #1f1912 100%)',
    accentColor: '#d4a373',
  },
  {
    id: 'mirage',
    name: 'Mirage — A-Site / Palace',
    map: 'de_mirage',
    desc: 'Контрастные тени дворца и кирпичные ящики плента',
    bgGradient: 'radial-gradient(ellipse at 50% 50%, #524738 0%, #29241c 55%, #13110d 100%)',
    accentColor: '#c99a5b',
  },
  {
    id: 'inferno',
    name: 'Inferno — Banana',
    map: 'de_inferno',
    desc: 'Каменная кладка, тени и желтоватая плитка банана',
    bgGradient: 'radial-gradient(ellipse at 50% 50%, #544c41 0%, #2d2822 60%, #14120f 100%)',
    accentColor: '#ddb892',
  },
  {
    id: 'nuke',
    name: 'Nuke — Ramp Site',
    map: 'de_nuke',
    desc: 'Тёмный индустриальный металл и холодный бетон',
    bgGradient: 'radial-gradient(ellipse at 50% 50%, #323d4c 0%, #18202b 60%, #0a0e14 100%)',
    accentColor: '#64748b',
  },
  {
    id: 'skybox',
    name: 'Bright Sky / Sun',
    map: 'skybox',
    desc: 'Экстремально яркий скайбокс — тест читаемости прицела на солнце',
    bgGradient: 'radial-gradient(ellipse at 50% 40%, #e0f2fe 0%, #7dd3fc 45%, #0284c7 90%)',
    accentColor: '#38bdf8',
  },
  {
    id: 'smoke',
    name: 'CS2 Volumetric Smoke',
    map: 'smoke',
    desc: 'Густая серая дымовая завеса',
    bgGradient: 'radial-gradient(ellipse at 50% 50%, #475569 0%, #1e293b 60%, #0f172a 100%)',
    accentColor: '#94a3b8',
  },
]

export const InteractiveCrosshairPreview: React.FC<InteractiveCrosshairPreviewProps> = ({
  config,
  onChangeConfig,
  interactiveControls = true,
}) => {
  const [activeScene, setActiveScene] = useState<SceneId>('dust2')
  const [showEnemyDummy, setShowEnemyDummy] = useState<boolean>(true)
  const [showWeaponBarrel, setShowWeaponBarrel] = useState<boolean>(true)

  // Current crosshair parameters based on preset
  const preset = config.preset || 'pro_cyan'
  const isHidden = preset === 'hidden'
  const colorHex = COLOR_MAP[config.color || 'cyan'] || '#00ffb4'
  const fov = config.fov || 90

  // Calculate preset values
  const getPresetValues = () => {
    switch (preset) {
      case 'pro_cyan':
        return { size: 3, gap: 1, thickness: 1.5, dot: false, outline: true }
      case 'green_clean':
        return { size: 2.5, gap: 0, thickness: 1, dot: false, outline: false }
      case 'dot':
        return { size: 0, gap: 0, thickness: 2.5, dot: true, outline: true }
      case 'minimal_white':
        return { size: 2, gap: -1, thickness: 1, dot: false, outline: false }
      case 'custom':
        return {
          size: config.size ?? 3,
          gap: config.gap ?? 1,
          thickness: config.thickness ?? 1.5,
          dot: config.dot ?? false,
          outline: config.outline ?? true,
        }
      case 'default':
      default:
        return { size: 3.5, gap: 2, thickness: 1.5, dot: false, outline: true }
    }
  }

  const pValues = getPresetValues()
  const scene = SCENES.find((s) => s.id === activeScene) || SCENES[0]

  // FOV zoom scaling: lower FOV = zoomed in, higher FOV = zoomed out
  const fovScale = (90 / Math.max(60, Math.min(110, fov)))

  return (
    <div
      style={{
        backgroundColor: '#0f1219',
        border: '1px solid #232838',
        borderRadius: '14px',
        overflow: 'hidden',
        boxShadow: '0 12px 30px rgba(0, 0, 0, 0.45)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Top Controls Header */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: '#141822',
          borderBottom: '1px solid #202636',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px' }}>🎯</span>
          <span style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>
            Интерактивный симулятор прицела & Viewport CS2
          </span>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
            }}
          >
            FOV: {fov}°
          </span>
        </div>

        {/* Scene Toggles */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '11px', color: '#64748b', marginRight: '4px' }}>Фон:</span>
          {SCENES.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveScene(s.id)}
              style={{
                fontSize: '11px',
                fontWeight: 600,
                padding: '4px 8px',
                borderRadius: '5px',
                border: activeScene === s.id ? '1px solid #38bdf8' : '1px solid #262c3e',
                backgroundColor: activeScene === s.id ? 'rgba(56, 189, 248, 0.2)' : '#161a25',
                color: activeScene === s.id ? '#38bdf8' : '#94a3b8',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              title={s.desc}
            >
              {s.name.split('—')[0].trim()}
            </button>
          ))}
        </div>
      </div>

      {/* Main Viewport Simulation Window */}
      <div
        style={{
          position: 'relative',
          height: '240px',
          width: '100%',
          background: scene.bgGradient,
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          userSelect: 'none',
        }}
      >
        {/* Tactical Grid / Wall architecture overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: activeScene === 'skybox' ? 0.05 : 0.15,
            backgroundImage: `linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px)`,
            backgroundSize: `${30 * fovScale}px ${30 * fovScale}px`,
            pointerEvents: 'none',
          }}
        />

        {/* Realistic Distant Corner / Archway */}
        {activeScene !== 'skybox' && activeScene !== 'smoke' && (
          <div
            style={{
              position: 'absolute',
              top: '15%',
              bottom: 0,
              left: '42%',
              right: '42%',
              background: 'linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.2) 100%)',
              borderLeft: '1px solid rgba(255,255,255,0.08)',
              borderRight: '1px solid rgba(255,255,255,0.08)',
              transform: `scale(${fovScale})`,
              transformOrigin: 'center bottom',
              pointerEvents: 'none',
            }}
          />
        )}

        {/* Enemy Dummy Silhouette (at head height in crosshair) */}
        {showEnemyDummy && (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: `translate(-50%, -46%) scale(${fovScale * 0.95})`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              pointerEvents: 'none',
              opacity: 0.85,
            }}
          >
            {/* Enemy Head Silhouette (Headshot Target) */}
            <div
              style={{
                width: '18px',
                height: '22px',
                borderRadius: '8px 8px 6px 6px',
                backgroundColor: '#181e28',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                boxShadow: '0 0 10px rgba(239, 68, 68, 0.2)',
                position: 'relative',
              }}
            >
              {/* Eye Visor Glow */}
              <div
                style={{
                  position: 'absolute',
                  top: '6px',
                  left: '3px',
                  right: '3px',
                  height: '3px',
                  backgroundColor: 'rgba(239, 68, 68, 0.7)',
                  borderRadius: '2px',
                }}
              />
            </div>
            {/* Torso & Armor */}
            <div
              style={{
                width: '38px',
                height: '52px',
                backgroundColor: '#121620',
                borderRadius: '6px 6px 4px 4px',
                marginTop: '2px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            />
          </div>
        )}

        {/* Weapon Barrel / Viewmodel (Bottom Right) */}
        {showWeaponBarrel && (
          <div
            style={{
              position: 'absolute',
              bottom: '-10px',
              right: config.viewmodelFov === 68 ? '40px' : '20px',
              width: '130px',
              height: '90px',
              pointerEvents: 'none',
              transform: config.viewmodelFov === 68 ? 'rotate(-6deg) scale(0.95)' : 'rotate(-2deg) scale(1.05)',
              transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
              opacity: 0.75,
            }}
          >
            <svg viewBox="0 0 200 120" fill="none" style={{ width: '100%', height: '100%' }}>
              <path
                d="M10 100 L90 40 L160 35 L190 42 L200 70 L150 110 Z"
                fill="#161a22"
                stroke="#2a3242"
                strokeWidth="2"
              />
              <line x1="80" y1="42" x2="160" y2="38" stroke="#38bdf8" strokeWidth="2" opacity="0.6" />
              <rect x="140" y="32" width="24" height="6" rx="2" fill="#252c3b" />
            </svg>
          </div>
        )}

        {/* Minimalist In-Game HUD overlay elements */}
        {config.hudMode !== 'none' && (
          <>
            {/* Top Round Timer Mock */}
            <div
              style={{
                position: 'absolute',
                top: '12px',
                left: '50%',
                transform: 'translateX(-50%)',
                backgroundColor: 'rgba(10, 12, 16, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px',
                padding: '3px 12px',
                fontSize: '11px',
                fontWeight: 700,
                color: '#f1f5f9',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ color: '#4f86f7' }}>CT 7</span>
              <span style={{ color: '#94a3b8' }}>1:34</span>
              <span style={{ color: '#de9b35' }}>5 T</span>
            </div>

            {/* Bottom Health/Ammo (if full or real HUD) */}
            {(config.hudMode === 'full' || config.hudMode === 'real' || config.hudMode === 'huge_esports') && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '12px',
                  left: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  backgroundColor: 'rgba(10, 12, 16, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  padding: '4px 10px',
                  fontSize: '12px',
                  fontWeight: 800,
                }}
              >
                <span style={{ color: '#34d399' }}>✚ 100</span>
                <span style={{ color: '#38bdf8' }}>🛡️ 100</span>
              </div>
            )}
          </>
        )}

        {/* THE CROSSHAIR (CENTRAL RETICLE) */}
        {!isHidden ? (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {/* Center Dot (if enabled) */}
            {pValues.dot && (
              <div
                style={{
                  width: `${pValues.thickness * 2}px`,
                  height: `${pValues.thickness * 2}px`,
                  backgroundColor: colorHex,
                  borderRadius: '50%',
                  boxShadow: pValues.outline ? '0 0 0 1px #000000' : 'none',
                }}
              />
            )}

            {/* Crosshair Lines (Left, Right, Top, Bottom) */}
            {pValues.size > 0 && (
              <>
                {/* Left Line */}
                <div
                  style={{
                    position: 'absolute',
                    right: `${pValues.gap + (pValues.dot ? 2 : 1)}px`,
                    width: `${pValues.size * 4}px`,
                    height: `${pValues.thickness}px`,
                    backgroundColor: colorHex,
                    boxShadow: pValues.outline ? '0 0 0 1px #000000' : 'none',
                  }}
                />
                {/* Right Line */}
                <div
                  style={{
                    position: 'absolute',
                    left: `${pValues.gap + (pValues.dot ? 2 : 1)}px`,
                    width: `${pValues.size * 4}px`,
                    height: `${pValues.thickness}px`,
                    backgroundColor: colorHex,
                    boxShadow: pValues.outline ? '0 0 0 1px #000000' : 'none',
                  }}
                />
                {/* Top Line */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: `${pValues.gap + (pValues.dot ? 2 : 1)}px`,
                    width: `${pValues.thickness}px`,
                    height: `${pValues.size * 4}px`,
                    backgroundColor: colorHex,
                    boxShadow: pValues.outline ? '0 0 0 1px #000000' : 'none',
                  }}
                />
                {/* Bottom Line */}
                <div
                  style={{
                    position: 'absolute',
                    top: `${pValues.gap + (pValues.dot ? 2 : 1)}px`,
                    width: `${pValues.thickness}px`,
                    height: `${pValues.size * 4}px`,
                    backgroundColor: colorHex,
                    boxShadow: pValues.outline ? '0 0 0 1px #000000' : 'none',
                  }}
                />
              </>
            )}
          </div>
        ) : (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              color: 'rgba(255, 255, 255, 0.4)',
              fontSize: '11px',
              fontWeight: 600,
              backgroundColor: 'rgba(0, 0, 0, 0.4)',
              padding: '2px 8px',
              borderRadius: '4px',
            }}
          >
            🚫 Прицел скрыт (Cinematic / No-Crosshair)
          </div>
        )}
      </div>

      {/* Bottom Interactive Toolbar */}
      {interactiveControls && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#12151e',
            borderTop: '1px solid #202636',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          {/* Quick Color Picker */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>Цвет:</span>
            {Object.entries(COLOR_MAP).map(([name, hex]) => (
              <button
                key={name}
                type="button"
                onClick={() => onChangeConfig && onChangeConfig({ color: name })}
                title={name}
                style={{
                  width: '18px',
                  height: '18px',
                  borderRadius: '50%',
                  backgroundColor: hex,
                  border: config.color === name ? '2px solid #ffffff' : '1px solid rgba(255,255,255,0.2)',
                  cursor: 'pointer',
                  transform: config.color === name ? 'scale(1.25)' : 'scale(1.0)',
                  transition: 'all 0.15s ease',
                }}
              />
            ))}
          </div>

          {/* Dummy and Weapon Toggles */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={() => setShowEnemyDummy(!showEnemyDummy)}
              style={{
                fontSize: '11px',
                fontWeight: 600,
                padding: '4px 10px',
                borderRadius: '5px',
                border: showEnemyDummy ? '1px solid #38bdf8' : '1px solid #283042',
                backgroundColor: showEnemyDummy ? 'rgba(56, 189, 248, 0.15)' : '#161a24',
                color: showEnemyDummy ? '#38bdf8' : '#94a3b8',
                cursor: 'pointer',
              }}
            >
              {showEnemyDummy ? '🎯 Мишень: Вкл' : '🎯 Мишень: Выкл'}
            </button>

            <button
              type="button"
              onClick={() => setShowWeaponBarrel(!showWeaponBarrel)}
              style={{
                fontSize: '11px',
                fontWeight: 600,
                padding: '4px 10px',
                borderRadius: '5px',
                border: showWeaponBarrel ? '1px solid #38bdf8' : '1px solid #283042',
                backgroundColor: showWeaponBarrel ? 'rgba(56, 189, 248, 0.15)' : '#161a24',
                color: showWeaponBarrel ? '#38bdf8' : '#94a3b8',
                cursor: 'pointer',
              }}
            >
              {showWeaponBarrel ? '🔫 Оружие: Вкл' : '🔫 Оружие: Выкл'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

