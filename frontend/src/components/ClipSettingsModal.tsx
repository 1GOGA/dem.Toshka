import React from 'react'
import type { ClipSettings } from '../types'
import { useTranslation } from '../i18n'
import {
  CrosshairIcon,
  RadarIcon,
  CameraIcon,
  SlidersIcon,
  SkullIcon,
  FolderIcon,
  EyeIcon,
  ActivityIcon,
} from './Icons'

interface ClipSettingsModalProps {
  isOpen: boolean
  onClose: () => void
  settings: ClipSettings
  onUpdateSettings: (newSettings: ClipSettings) => void
}

export const ClipSettingsModal: React.FC<ClipSettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onUpdateSettings,
}) => {
  const { t, lang } = useTranslation()

  React.useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '820px', width: '95%' }}
      >
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <SlidersIcon size={20} color="#38bdf8" />
            <div>
              <h3 className="modal-title" style={{ margin: 0 }}>
                {t('modal.settings.title')}
              </h3>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                {t('modal.settings.subtitle')}
              </div>
            </div>
          </div>
          <button className="modal-close card-interactive" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body" style={{ maxHeight: '78vh', overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* 1. POV DIRECTOR */}
          <div style={{ backgroundColor: '#131620', border: '1px solid #232838', borderRadius: '10px', padding: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CameraIcon size={14} color="#38bdf8" />
                <span>{lang === 'ru' ? 'РЕЖИССЕР КАМЕРЫ (POV)' : 'CAMERA DIRECTOR (POV)'}</span>
              </div>
              <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>
                {settings.perspective === 'dynamic_killcam'
                  ? (lang === 'ru' ? '⚡ Килл-кам PRO (2 запуска)' : '⚡ Kill-cam PRO (2 runs)')
                  : (lang === 'ru' ? '🎬 Главный герой (ГГ)' : '🎬 Hero POV')}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              <button
                type="button"
                className="btn card-interactive"
                onClick={() => onUpdateSettings({ ...settings, perspective: 'attacker' })}
                style={{
                  padding: '10px',
                  textAlign: 'left',
                  backgroundColor: (!settings.perspective || settings.perspective === 'attacker') ? 'rgba(56, 189, 248, 0.12)' : '#16181f',
                  borderColor: (!settings.perspective || settings.perspective === 'attacker') ? '#38bdf8' : '#282d3c',
                  borderWidth: '1px',
                  borderStyle: 'solid',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <span style={{ fontSize: '11px', fontWeight: 700, color: (!settings.perspective || settings.perspective === 'attacker') ? '#38bdf8' : '#e2e8f0' }}>
                  🎬 {lang === 'ru' ? 'Главный Герой' : 'Hero POV'}
                </span>
                <span style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>
                  {lang === 'ru' ? '100% от автора фрагов (1 запуск CS2)' : '100% from fragger POV (Single CS2 launch)'}
                </span>
              </button>

              <button
                type="button"
                className="btn card-interactive"
                onClick={() => onUpdateSettings({ ...settings, perspective: 'dynamic_killcam' })}
                style={{
                  padding: '10px',
                  textAlign: 'left',
                  backgroundColor: settings.perspective === 'dynamic_killcam' ? 'rgba(139, 92, 246, 0.15)' : '#16181f',
                  borderColor: settings.perspective === 'dynamic_killcam' ? '#8b5cf6' : '#282d3c',
                  borderWidth: '1px',
                  borderStyle: 'solid',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <span style={{ fontSize: '11px', fontWeight: 700, color: settings.perspective === 'dynamic_killcam' ? '#a78bfa' : '#e2e8f0' }}>
                  ⚡ {lang === 'ru' ? 'Килл-кам PRO' : 'Kill-cam PRO'}
                </span>
                <span style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>
                  {lang === 'ru' ? 'Смерти жертв ➔ Откат ➔ Триумф ГГ (2 запуска)' : 'Victim POVs ➔ Rollback ➔ Hero Triumph (2 runs)'}
                </span>
              </button>
            </div>
          </div>

          {/* 2. SCREEN, FORMAT, RESOLUTION, FPS & FOV */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', backgroundColor: '#131620', padding: '14px', borderRadius: '10px', border: '1px solid #232838' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CrosshairIcon size={14} color="#38bdf8" />
              <span>{lang === 'ru' ? 'ФОРМАТ, РАЗРЕШЕНИЕ И УГОЛ ОБЗОРА (FOV)' : 'FORMAT, RESOLUTION & FOV'}</span>
            </div>

            {/* Aspect Ratio */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'block' }}>{lang === 'ru' ? 'Формат экрана CS2' : 'CS2 Aspect Ratio'}</span>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>{lang === 'ru' ? '4:3 делает модели врагов шире на 33%' : '4:3 makes enemy models 33% wider'}</span>
              </div>
              <div style={{ display: 'flex', gap: '4px', backgroundColor: '#0d1017', padding: '2px', borderRadius: '6px', border: '1px solid #232734' }}>
                <button
                  type="button"
                  className="card-interactive"
                  onClick={() => onUpdateSettings({ ...settings, aspectRatio: '4:3', resolution: '1280x960' })}
                  style={{
                    padding: '5px 12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    borderRadius: '4px',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: settings.aspectRatio === '4:3' ? '#38bdf8' : 'transparent',
                    color: settings.aspectRatio === '4:3' ? '#090d16' : '#94a3b8',
                  }}
                >
                  4:3 ({lang === 'ru' ? 'Киберспорт' : 'Esports'})
                </button>
                <button
                  type="button"
                  className="card-interactive"
                  onClick={() => onUpdateSettings({ ...settings, aspectRatio: '16:9', resolution: '1080p' })}
                  style={{
                    padding: '5px 12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    borderRadius: '4px',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: settings.aspectRatio !== '4:3' ? '#38bdf8' : 'transparent',
                    color: settings.aspectRatio !== '4:3' ? '#090d16' : '#94a3b8',
                  }}
                >
                  16:9 ({lang === 'ru' ? 'Широкий' : 'Widescreen'})
                </button>
              </div>
            </div>

            {/* Resolution buttons */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #1c202d', paddingTop: '8px' }}>
              <div>
                <span style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'block' }}>
                  {settings.aspectRatio === '4:3' ? (lang === 'ru' ? 'Разрешение 4:3' : '4:3 Resolution') : (lang === 'ru' ? 'Разрешение 16:9' : '16:9 Resolution')}
                </span>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                  {settings.aspectRatio === '4:3'
                    ? (lang === 'ru' ? '1280x960 — выбор s1mple & m0NESY' : '1280x960 — pro choice (s1mple & m0NESY)')
                    : (lang === 'ru' ? '1920x1080 — стандарт Full HD' : '1920x1080 — Full HD Standard')}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '5px' }}>
                {settings.aspectRatio === '4:3' ? (
                  <>
                    <button
                      type="button"
                      className="btn card-interactive"
                      onClick={() => onUpdateSettings({ ...settings, resolution: '1280x960', aspectRatio: '4:3' })}
                      style={{
                        padding: '4px 8px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: (settings.resolution === '1280x960' || !settings.resolution || settings.resolution === '1080p') ? '#38bdf8' : '#1c2333',
                        color: (settings.resolution === '1280x960' || !settings.resolution || settings.resolution === '1080p') ? '#090d16' : '#cbd5e1',
                        border: '1px solid #2d3748',
                        borderRadius: '4px',
                      }}
                    >
                      1280x960
                    </button>
                    <button
                      type="button"
                      className="btn card-interactive"
                      onClick={() => onUpdateSettings({ ...settings, resolution: '1440x1080', aspectRatio: '4:3' })}
                      style={{
                        padding: '4px 8px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: settings.resolution === '1440x1080' ? '#38bdf8' : '#1c2333',
                        color: settings.resolution === '1440x1080' ? '#090d16' : '#cbd5e1',
                        border: '1px solid #2d3748',
                        borderRadius: '4px',
                      }}
                    >
                      1440x1080
                    </button>
                    <button
                      type="button"
                      className="btn card-interactive"
                      onClick={() => onUpdateSettings({ ...settings, resolution: '1024x768', aspectRatio: '4:3' })}
                      style={{
                        padding: '4px 8px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: settings.resolution === '1024x768' ? '#38bdf8' : '#1c2333',
                        color: settings.resolution === '1024x768' ? '#090d16' : '#cbd5e1',
                        border: '1px solid #2d3748',
                        borderRadius: '4px',
                      }}
                    >
                      1024x768
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      className="btn card-interactive"
                      onClick={() => onUpdateSettings({ ...settings, resolution: '1080p', aspectRatio: '16:9' })}
                      style={{
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: (settings.resolution === '1080p' || settings.resolution === '1920x1080') ? '#38bdf8' : '#1c2333',
                        color: (settings.resolution === '1080p' || settings.resolution === '1920x1080') ? '#090d16' : '#cbd5e1',
                        border: '1px solid #2d3748',
                        borderRadius: '4px',
                      }}
                    >
                      1080p Full HD
                    </button>
                    <button
                      type="button"
                      className="btn card-interactive"
                      onClick={() => onUpdateSettings({ ...settings, resolution: '720p', aspectRatio: '16:9' })}
                      style={{
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: settings.resolution === '720p' ? '#38bdf8' : '#1c2333',
                        color: settings.resolution === '720p' ? '#090d16' : '#cbd5e1',
                        border: '1px solid #2d3748',
                        borderRadius: '4px',
                      }}
                    >
                      720p HD
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* FPS & FOV row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', borderTop: '1px solid #1c202d', paddingTop: '8px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>{lang === 'ru' ? 'Частота кадров (FPS)' : 'Frame Rate (FPS)'}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {([30, 60, 120] as const).map((fpsVal) => (
                    <button
                      key={fpsVal}
                      type="button"
                      className="btn card-interactive"
                      onClick={() => onUpdateSettings({ ...settings, fps: fpsVal })}
                      style={{
                        flex: 1,
                        padding: '4px 6px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: (settings.fps || 60) === fpsVal ? '#38bdf8' : '#1c2333',
                        color: (settings.fps || 60) === fpsVal ? '#090d16' : '#cbd5e1',
                        border: '1px solid #2d3748',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      {fpsVal === 120 ? '120⚡' : `${fpsVal}`}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>{lang === 'ru' ? 'Угол обзора (FOV)' : 'Field of View (FOV)'}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[
                    { val: 68, label: lang === 'ru' ? '68° Дефолт' : '68° Default' },
                    { val: 90, label: '90° Pro' },
                    { val: 100, label: '100° Wide' },
                  ].map((f) => (
                    <button
                      key={f.val}
                      type="button"
                      className="btn card-interactive"
                      onClick={() => onUpdateSettings({ ...settings, fov: f.val })}
                      style={{
                        flex: 1,
                        padding: '4px 4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        backgroundColor: (settings.fov || 90) === f.val ? '#38bdf8' : '#1c2333',
                        color: (settings.fov || 90) === f.val ? '#090d16' : '#cbd5e1',
                        border: '1px solid #2d3748',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 3. RADAR / MINIMAP */}
          <div style={{ backgroundColor: '#131620', padding: '14px', borderRadius: '10px', border: '1px solid #232838' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <RadarIcon size={14} color="#38bdf8" />
                <span>{lang === 'ru' ? 'МИНИ-КАРТА / 2D РАДАР' : 'MINI-MAP / 2D RADAR'}</span>
              </div>
              <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>
                {settings.radarMode === 'broadcast'
                  ? (lang === 'ru' ? 'Турнирный BLAST' : 'Tournament BLAST')
                  : settings.radarMode === 'hidden'
                  ? (lang === 'ru' ? 'Скрыт' : 'Hidden')
                  : (lang === 'ru' ? 'Круглый (Слежение)' : 'Rotating (Focus)')}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              {[
                { id: 'player_focus', label: lang === 'ru' ? 'Круглый (Слежение)' : 'Rotating (Focus)', desc: lang === 'ru' ? 'Центр на игроке, стандарт OBS' : 'Center on player, OBS standard' },
                { id: 'broadcast', label: lang === 'ru' ? 'Турнирный BLAST' : 'Tournament BLAST', desc: lang === 'ru' ? 'Вся карта как на трансляциях' : 'Full map overview as on stream' },
                { id: 'hidden', label: lang === 'ru' ? 'Без радара' : 'No Radar', desc: lang === 'ru' ? 'Скрыт для чистого экрана' : 'Hidden for clean cinematic' },
              ].map((r) => {
                const isSelected = (settings.radarMode || 'player_focus') === r.id
                return (
                  <button
                    key={r.id}
                    type="button"
                    className="btn card-interactive"
                    onClick={() => onUpdateSettings({ ...settings, radarMode: r.id as any })}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      padding: '8px 10px',
                      textAlign: 'left',
                      backgroundColor: isSelected ? 'rgba(16, 185, 129, 0.15)' : '#16181f',
                      borderColor: isSelected ? '#10b981' : '#282d3c',
                      borderWidth: '1px',
                      borderStyle: 'solid',
                      borderRadius: '6px',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: 700, color: isSelected ? '#34d399' : '#e2e8f0' }}>{r.label}</div>
                    <div style={{ fontSize: '9px', color: '#64748b', marginTop: '2px', lineHeight: '1.2' }}>{r.desc}</div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* 4. TACTICAL TOGGLES LIST [ON / OFF] */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', backgroundColor: '#131620', padding: '14px', borderRadius: '10px', border: '1px solid #232838' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
              <SlidersIcon size={14} color="#38bdf8" />
              <span>{lang === 'ru' ? 'ТАКТИЧЕСКИЕ ТУМБЛЕРЫ [ВКЛ / ВЫКЛ]' : 'TACTICAL TOGGLES [ON / OFF]'}</span>
            </div>

            {/* Switch 1: REAL OBS Mode */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CameraIcon size={13} color="#38bdf8" />
                  <span>{lang === 'ru' ? 'Режим REAL OBS (Вид живого матча)' : 'REAL OBS Mode (Live Match View)'}</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  {lang === 'ru' ? '1:1 как при живой игре: скрывает спектаторскую плашку и анимированные аватары' : '1:1 live gameplay: hides spectator bar and animated avatars'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.hudMode === 'real' ? '#38bdf8' : '#64748b' }}>
                  {settings.hudMode === 'real' ? (lang === 'ru' ? 'ВКЛ' : 'ON') : (lang === 'ru' ? 'ВЫКЛ' : 'OFF')}
                </span>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={settings.hudMode === 'real'}
                    onChange={(e) => {
                      const isReal = e.target.checked
                      onUpdateSettings({
                        ...settings,
                        hudMode: isReal ? 'real' : 'full',
                        hudScale: isReal ? 1.0 : (settings.hudScale || 0.95),
                        ...(isReal ? { xray: false, radarMode: 'player_focus' } : {}),
                      })
                    }}
                  />
                  <span className="toggle-slider" />
                </label>
              </div>
            </div>

            {/* Switch 2: X-Ray */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <EyeIcon size={13} color="#38bdf8" />
                  <span>{lang === 'ru' ? 'Силуэты сквозь стены (X-Ray)' : 'Player Silhouettes (X-Ray)'}</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  {lang === 'ru' ? 'Подсветка контуров игроков через стены (spec_show_xray)' : 'Player glowing outlines through obstacles (spec_show_xray)'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.xray !== false ? '#38bdf8' : '#64748b' }}>
                  {settings.xray !== false ? (lang === 'ru' ? 'ВКЛ' : 'ON') : (lang === 'ru' ? 'ВЫКЛ' : 'OFF')}
                </span>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={settings.xray !== false}
                    onChange={(e) => onUpdateSettings({ ...settings, xray: e.target.checked })}
                  />
                  <span className="toggle-slider" />
                </label>
              </div>
            </div>

            {/* Switch 3: Overhead Names */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CrosshairIcon size={13} color="#38bdf8" />
                  <span>{lang === 'ru' ? 'Ники над головами' : 'Overhead Player Tags'}</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  {lang === 'ru' ? 'Имена и шкала здоровья над персонажами (cl_teamid_overhead_mode)' : 'Player names & HP bars above character models (cl_teamid_overhead_mode)'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.overheadMode !== false ? '#38bdf8' : '#64748b' }}>
                  {settings.overheadMode !== false ? (lang === 'ru' ? 'ВКЛ' : 'ON') : (lang === 'ru' ? 'ВЫКЛ' : 'OFF')}
                </span>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={settings.overheadMode !== false}
                    onChange={(e) => onUpdateSettings({ ...settings, overheadMode: e.target.checked })}
                  />
                  <span className="toggle-slider" />
                </label>
              </div>
            </div>

            {/* Switch 4: Killfeed Only */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <SkullIcon size={13} color="#38bdf8" />
                  <span>{lang === 'ru' ? 'Только Киллфид (Чистый экран)' : 'Killfeed Only (Clean Screen)'}</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  {lang === 'ru' ? 'Скрывает полосы патронов и HP, оставляя только уведомления о фрагах' : 'Hides HP and ammo bars, keeping only kill notifications'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.killfeedOnly ? '#38bdf8' : '#64748b' }}>
                  {settings.killfeedOnly ? (lang === 'ru' ? 'ВКЛ' : 'ON') : (lang === 'ru' ? 'ВЫКЛ' : 'OFF')}
                </span>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={Boolean(settings.killfeedOnly)}
                    onChange={(e) => onUpdateSettings({ ...settings, killfeedOnly: e.target.checked })}
                  />
                  <span className="toggle-slider" />
                </label>
              </div>
            </div>

            {/* Switch 5: 5v3 Counter */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ActivityIcon size={13} color="#38bdf8" />
                  <span>{lang === 'ru' ? 'Счётчик живых (5 v 3 цифрами)' : 'Alive Players Counter (5 v 3)'}</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  {lang === 'ru' ? 'Компактные цифры счета живых игроков сверху вместо больших аватаров' : 'Compact living players score counter at top instead of big avatars'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.teamcounterMode ? '#38bdf8' : '#64748b' }}>
                  {settings.teamcounterMode ? (lang === 'ru' ? 'ВКЛ' : 'ON') : (lang === 'ru' ? 'ВЫКЛ' : 'OFF')}
                </span>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={Boolean(settings.teamcounterMode)}
                    onChange={(e) => onUpdateSettings({ ...settings, teamcounterMode: e.target.checked })}
                  />
                  <span className="toggle-slider" />
                </label>
              </div>
            </div>

            {/* Switch 6: Watermark & Corner Selector */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <img
                    src="/logo_video.png"
                    alt="dem.Toshka"
                    style={{ height: '18px', maxWidth: '55px', objectFit: 'contain' }}
                  />
                  <div>
                    <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600 }}>{lang === 'ru' ? 'Водяной знак dem.Toshka' : 'dem.Toshka Watermark'}</div>
                    <div style={{ fontSize: '10px', color: '#94a3b8' }}>{lang === 'ru' ? 'Фирменный логотип студии на видео' : 'Subtle studio logo on video'}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '10px', fontWeight: 700, color: settings.watermark !== false ? '#38bdf8' : '#64748b' }}>
                    {settings.watermark !== false ? (lang === 'ru' ? 'ВКЛ' : 'ON') : (lang === 'ru' ? 'ВЫКЛ' : 'OFF')}
                  </span>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={settings.watermark !== false}
                      onChange={(e) => onUpdateSettings({ ...settings, watermark: e.target.checked })}
                    />
                    <span className="toggle-slider" />
                  </label>
                </div>
              </div>

              {settings.watermark !== false && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '4px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <span style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 600 }}>
                    {lang === 'ru' ? 'Угол водяного знака:' : 'Watermark Corner:'}
                  </span>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {[
                      { id: 'top_left' as const, label: '↖ ' + (lang === 'ru' ? 'Слева верх' : 'Top Left') },
                      { id: 'top_right' as const, label: '↗ ' + (lang === 'ru' ? 'Справа верх' : 'Top Right') },
                      { id: 'bottom_left' as const, label: '↙ ' + (lang === 'ru' ? 'Слева низ' : 'Bottom Left') },
                      { id: 'bottom_right' as const, label: '↘ ' + (lang === 'ru' ? 'Справа низ' : 'Bottom Right') },
                    ].map((pos) => {
                      const isActive = (settings.watermarkPosition || 'top_left') === pos.id
                      return (
                        <button
                          key={pos.id}
                          type="button"
                          className="btn card-interactive"
                          onClick={() => onUpdateSettings({ ...settings, watermarkPosition: pos.id })}
                          style={{
                            fontSize: '10px',
                            fontWeight: 700,
                            padding: '3px 6px',
                            borderRadius: '4px',
                            border: isActive ? '1px solid #38bdf8' : '1px solid #262c3e',
                            backgroundColor: isActive ? 'rgba(56, 189, 248, 0.2)' : '#161a25',
                            color: isActive ? '#38bdf8' : '#94a3b8',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          {pos.label}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 5. HUD SCALE, PRE/POST-ROLL & CROSSHAIR */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', backgroundColor: '#131620', padding: '14px', borderRadius: '10px', border: '1px solid #232838' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CrosshairIcon size={14} color="#38bdf8" />
              <span>{lang === 'ru' ? 'РАЗМЕР HUD, ПРИЦЕЛ И ТАЙМИНГИ' : 'HUD SCALE, CROSSHAIR & TIMINGS'}</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              {/* HUD Scale */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>{lang === 'ru' ? 'Размер HUD' : 'HUD Scale'}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[
                    { scale: 0.95, label: lang === 'ru' ? '95% Компакт' : '95% Compact' },
                    { scale: 1.0, label: '100% 1:1' },
                    { scale: 1.15, label: lang === 'ru' ? '115% Кибер' : '115% Esports' },
                  ].map((s) => (
                    <button
                      key={s.scale}
                      type="button"
                      className="btn card-interactive"
                      onClick={() => onUpdateSettings({ ...settings, hudScale: s.scale })}
                      style={{
                        flex: 1,
                        padding: '4px 4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        borderRadius: '4px',
                        border: '1px solid #2d3748',
                        backgroundColor: settings.hudScale === s.scale ? '#38bdf8' : '#1c2333',
                        color: settings.hudScale === s.scale ? '#090d16' : '#cbd5e1',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Crosshair Preset */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>{lang === 'ru' ? 'Прицел в CS2' : 'CS2 Crosshair'}</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[
                    { p: 'default', label: lang === 'ru' ? 'Дефолт' : 'Default' },
                    { p: 'pro_cyan', label: lang === 'ru' ? 'Pro Цветной' : 'Pro Color' },
                    { p: 'hidden', label: lang === 'ru' ? 'Скрыт' : 'Hidden' },
                  ].map((c) => {
                    const isSelected = (settings.crosshairPreset || 'default') === c.p
                    return (
                      <button
                        key={c.p}
                        type="button"
                        className="btn card-interactive"
                        onClick={() =>
                          onUpdateSettings({
                            ...settings,
                            crosshairPreset: c.p as any,
                            customCrosshair: c.p !== 'default' && c.p !== 'hidden',
                          })
                        }
                        style={{
                          flex: 1,
                          padding: '4px 4px',
                          fontSize: '10px',
                          fontWeight: 700,
                          borderRadius: '4px',
                          border: '1px solid #2d3748',
                          backgroundColor: isSelected ? '#38bdf8' : '#1c2333',
                          color: isSelected ? '#090d16' : '#cbd5e1',
                          cursor: 'pointer',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {c.label}
                      </button>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Timings row: Pre-roll and Post-roll */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', borderTop: '1px solid #1c202d', paddingTop: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
                  {lang === 'ru' ? 'Секунды до фрага (Pre-roll)' : 'Pre-roll lead time (seconds)'}
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  step="0.5"
                  value={settings.preRollSeconds}
                  onChange={(e) => onUpdateSettings({ ...settings, preRollSeconds: parseFloat(e.target.value) || 4.0 })}
                  style={{
                    width: '100%',
                    backgroundColor: '#0e111a',
                    border: '1px solid #28334a',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    color: '#f1f5f9',
                    fontSize: '12px',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
                  {lang === 'ru' ? 'Секунды после фрага (Post-roll)' : 'Post-roll tail time (seconds)'}
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  step="0.5"
                  value={settings.postRollSeconds}
                  onChange={(e) => onUpdateSettings({ ...settings, postRollSeconds: parseFloat(e.target.value) || 2.5 })}
                  style={{
                    width: '100%',
                    backgroundColor: '#0e111a',
                    border: '1px solid #28334a',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    color: '#f1f5f9',
                    fontSize: '12px',
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <FolderIcon size={14} color="#94a3b8" /> {lang === 'ru' ? 'Сохранение клипов в' : 'Saving clips to'} <code>renders/</code>
          </div>
          <button className="btn btn-primary" onClick={onClose} style={{ padding: '6px 18px', fontWeight: 700 }}>
            {lang === 'ru' ? 'Применить настройки' : 'Apply Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
