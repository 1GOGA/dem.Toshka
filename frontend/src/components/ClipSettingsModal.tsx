import React from 'react'
import type { ClipSettings } from '../types'
import { useTranslation } from '../i18n'
import {
  CrosshairIcon,
  RadarIcon,
  CameraIcon,
  SlidersIcon,
  VolumeIcon,
  VolumeMuteIcon,
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
  const { t } = useTranslation()

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
                <span>РЕЖИССЕР КАМЕРЫ (POV)</span>
              </div>
              <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>
                {settings.perspective === 'dynamic_killcam'
                  ? '⚡ Килл-кам PRO (2 запуска)'
                  : settings.perspective === 'victim'
                  ? '💀 Лицо жертвы'
                  : '🎬 Главный герой (ГГ)'}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
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
                  🎬 Главный Герой
                </span>
                <span style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>
                  100% от автора фрагов (1 запуск CS2)
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
                  ⚡ Килл-кам PRO
                </span>
                <span style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>
                  Смерти жертв ➔ Откат ➔ Триумф ГГ (2 запуска)
                </span>
              </button>

              <button
                type="button"
                className="btn card-interactive"
                onClick={() => onUpdateSettings({ ...settings, perspective: 'victim' })}
                style={{
                  padding: '10px',
                  textAlign: 'left',
                  backgroundColor: settings.perspective === 'victim' ? 'rgba(239, 68, 68, 0.15)' : '#16181f',
                  borderColor: settings.perspective === 'victim' ? '#ef4444' : '#282d3c',
                  borderWidth: '1px',
                  borderStyle: 'solid',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <span style={{ fontSize: '11px', fontWeight: 700, color: settings.perspective === 'victim' ? '#f87171' : '#e2e8f0' }}>
                  💀 Только Жертва
                </span>
                <span style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>
                  Камера от лица погибших врагов
                </span>
              </button>
            </div>
          </div>

          {/* 2. SCREEN, FORMAT, RESOLUTION, FPS & FOV */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', backgroundColor: '#131620', padding: '14px', borderRadius: '10px', border: '1px solid #232838' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CrosshairIcon size={14} color="#38bdf8" />
              <span>ФОРМАТ, РАЗРЕШЕНИЕ И УГОЛ ОБЗОРА (FOV)</span>
            </div>

            {/* Aspect Ratio */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'block' }}>Формат экрана CS2</span>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>4:3 делает модели врагов шире на 33%</span>
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
                  4:3 (Киберспорт)
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
                  16:9 (Широкий)
                </button>
              </div>
            </div>

            {/* Resolution buttons */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #1c202d', paddingTop: '8px' }}>
              <div>
                <span style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'block' }}>
                  {settings.aspectRatio === '4:3' ? 'Разрешение 4:3' : 'Разрешение 16:9'}
                </span>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                  {settings.aspectRatio === '4:3' ? '1280x960 — выбор s1mple & m0NESY' : '1920x1080 — стандарт Full HD'}
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
                <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>Частота кадров (FPS)</span>
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
                <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>Угол обзора (FOV)</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[
                    { val: 68, label: '68° Дефолт' },
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
                <span>МИНИ-КАРТА / 2D РАДАР</span>
              </div>
              <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>
                {settings.radarMode === 'broadcast'
                  ? 'Турнирный BLAST'
                  : settings.radarMode === 'hidden'
                  ? 'Скрыт'
                  : 'Круглый (Слежение)'}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              {[
                { id: 'player_focus', label: 'Круглый (Слежение)', desc: 'Центр на игроке, стандарт OBS' },
                { id: 'broadcast', label: 'Турнирный BLAST', desc: 'Вся карта как на трансляциях' },
                { id: 'hidden', label: 'Без радара', desc: 'Скрыт для чистого экрана' },
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
              <span>ТАКТИЧЕСКИЕ ТУМБЛЕРЫ [ВКЛ / ВЫКЛ]</span>
            </div>

            {/* Switch 1: REAL OBS Mode */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CameraIcon size={13} color="#38bdf8" />
                  <span>Режим REAL OBS (Вид живого матча)</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  1:1 как при живой игре: скрывает спектаторскую плашку и анимированные аватары
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.hudMode === 'real' ? '#38bdf8' : '#64748b' }}>
                  {settings.hudMode === 'real' ? 'ВКЛ' : 'ВЫКЛ'}
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
                  <span>Силуэты сквозь стены (X-Ray)</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  Подсветка контуров игроков через стены (spec_show_xray)
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.xray !== false ? '#38bdf8' : '#64748b' }}>
                  {settings.xray !== false ? 'ВКЛ' : 'ВЫКЛ'}
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
                  <span>Ники над головами</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  Имена и шкала здоровья над персонажами (cl_teamid_overhead_mode)
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.overheadMode !== false ? '#38bdf8' : '#64748b' }}>
                  {settings.overheadMode !== false ? 'ВКЛ' : 'ВЫКЛ'}
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
                  <span>Только Киллфид (Чистый экран)</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  Скрывает полосы патронов и HP, оставляя только уведомления о фрагах
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.killfeedOnly ? '#38bdf8' : '#64748b' }}>
                  {settings.killfeedOnly ? 'ВКЛ' : 'ВЫКЛ'}
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
                  <span>Счётчик живых (5 v 3 цифрами)</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  Компактные цифры счета живых игроков сверху вместо больших аватаров
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.teamcounterMode ? '#38bdf8' : '#64748b' }}>
                  {settings.teamcounterMode ? 'ВКЛ' : 'ВЫКЛ'}
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

            {/* Switch 6: Watermark */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <img
                  src="/logo_video.png"
                  alt="dem.Toshka"
                  style={{ height: '18px', maxWidth: '55px', objectFit: 'contain' }}
                />
                <div>
                  <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600 }}>Водяной знак dem.Toshka</div>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Фирменный логотип в верхнем углу клипа</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.watermark !== false ? '#38bdf8' : '#64748b' }}>
                  {settings.watermark !== false ? 'ВКЛ' : 'ВЫКЛ'}
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

            {/* Switch 7: Preview Recording Window & Sound */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {settings.previewRecording !== false ? <VolumeIcon size={13} color="#38bdf8" /> : <VolumeMuteIcon size={13} color="#94a3b8" />}
                  <span>Окно CS2 и звук записи</span>
                </div>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                  {settings.previewRecording !== false ? 'Окно игры видно, звук включен' : 'Тихий фоновый режим без звука'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: settings.previewRecording !== false ? '#38bdf8' : '#64748b' }}>
                  {settings.previewRecording !== false ? 'ВКЛ' : 'ТИХИЙ'}
                </span>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={settings.previewRecording !== false}
                    onChange={(e) => onUpdateSettings({ ...settings, previewRecording: e.target.checked })}
                  />
                  <span className="toggle-slider" />
                </label>
              </div>
            </div>
          </div>

          {/* 5. HUD SCALE, PRE/POST-ROLL & CROSSHAIR */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', backgroundColor: '#131620', padding: '14px', borderRadius: '10px', border: '1px solid #232838' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CrosshairIcon size={14} color="#38bdf8" />
              <span>РАЗМЕР HUD, ПРИЦЕЛ И ТАЙМИНГИ</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              {/* HUD Scale */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>Размер HUD</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[
                    { scale: 0.95, label: '95% Компакт' },
                    { scale: 1.0, label: '100% 1:1' },
                    { scale: 1.15, label: '115% Кибер' },
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
                <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>Прицел в CS2</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[
                    { p: 'default', label: 'Дефолт' },
                    { p: 'pro_cyan', label: 'Pro Цветной' },
                    { p: 'hidden', label: 'Скрыт' },
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
                  Секунды до фрага (Pre-roll)
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
                  Секунды после фрага (Post-roll)
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
            <FolderIcon size={14} color="#94a3b8" /> Сохранение клипов в <code>renders/</code>
          </div>
          <button className="btn btn-primary" onClick={onClose} style={{ padding: '6px 18px', fontWeight: 700 }}>
            Применить настройки
          </button>
        </div>
      </div>
    </div>
  )
}
