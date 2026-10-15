import React, { useState } from 'react'
import type { ClipSettings } from '../types'

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
  const [activeTab, setActiveTab] = useState<'screen' | 'radar' | 'hud' | 'camera'>('screen')

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '860px', width: '95%' }}
      >
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px' }}>⚙️</span>
            <div>
              <h3 className="modal-title" style={{ margin: 0 }}>
                Параметры видео и экспорта CS2
              </h3>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                Киберспортивный формат 4:3, стили радара, HUD и режиссер камеры
              </div>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body" style={{ maxHeight: '78vh', overflowY: 'auto', padding: '16px 20px' }}>
          {/* Navigation Tabs */}
          <div
            style={{
              display: 'flex',
              gap: '6px',
              backgroundColor: '#0d1017',
              padding: '4px',
              borderRadius: '8px',
              border: '1px solid #232838',
              marginBottom: '18px',
              overflowX: 'auto',
            }}
          >
            {[
              { id: 'screen', label: '🎮 Экран и 4:3', desc: 'Разрешение, FPS' },
              { id: 'radar', label: '🗺️ Карта и Радар', desc: '130% Огромный, BLAST' },
              { id: 'hud', label: '🏆 HUD и Киллфид', desc: '115% Масштаб, X-Ray' },
              { id: 'camera', label: '🎥 Камера и Прицел', desc: 'POV, FOV, Тайминги' },
            ].map((tab) => {
              const isAct = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id as any)}
                  style={{
                    flex: 1,
                    minWidth: '130px',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: isAct ? '#1e2638' : 'transparent',
                    color: isAct ? '#38bdf8' : '#94a3b8',
                    borderBottom: isAct ? '2px solid #38bdf8' : '2px solid transparent',
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ fontSize: '12px', fontWeight: isAct ? 800 : 600 }}>{tab.label}</div>
                  <div style={{ fontSize: '10px', opacity: 0.7 }}>{tab.desc}</div>
                </button>
              )
            })}
          </div>

          {/* TAB 1: SCREEN & 4:3 */}
          {activeTab === 'screen' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Aspect Ratio */}
              <div style={{ backgroundColor: '#131620', border: '1px solid #232838', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div>
                    <label style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', display: 'block' }}>
                      Формат экрана CS2 (Aspect Ratio)
                    </label>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      4:3 делает модельки шире и повышает видимость врагов; 16:9 — стандартный широкий угол.
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '4px', backgroundColor: '#0d1017', padding: '3px', borderRadius: '8px', border: '1px solid #232734' }}>
                    <button
                      type="button"
                      onClick={() => onUpdateSettings({ ...settings, aspectRatio: '4:3', resolution: '1280x960' })}
                      style={{
                        padding: '6px 14px',
                        fontSize: '12px',
                        fontWeight: 700,
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        backgroundColor: settings.aspectRatio === '4:3' ? '#38bdf8' : 'transparent',
                        color: settings.aspectRatio === '4:3' ? '#090d16' : '#94a3b8',
                      }}
                    >
                      🎮 4:3 (Киберспорт)
                    </button>
                    <button
                      type="button"
                      onClick={() => onUpdateSettings({ ...settings, aspectRatio: '16:9', resolution: '1080p' })}
                      style={{
                        padding: '6px 14px',
                        fontSize: '12px',
                        fontWeight: 700,
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        backgroundColor: settings.aspectRatio !== '4:3' ? '#38bdf8' : 'transparent',
                        color: settings.aspectRatio !== '4:3' ? '#090d16' : '#94a3b8',
                      }}
                    >
                      🖥️ 16:9 (Широкий)
                    </button>
                  </div>
                </div>

                {/* Resolution buttons */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0e111a', padding: '12px 14px', borderRadius: '8px', border: '1px solid #1c2230' }}>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#f1f5f9' }}>
                      {settings.aspectRatio === '4:3' ? 'Разрешение 4:3 в CS2' : 'Разрешение 16:9 в CS2'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      {settings.aspectRatio === '4:3'
                        ? '1280x960 — самый популярный выбор про-игроков (s1mple, m0NESY, b1t)'
                        : '1080p — максимальная детализация Full HD'}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    {settings.aspectRatio === '4:3' ? (
                      <>
                        <button
                          type="button"
                          className={`btn ${settings.resolution === '1280x960' || !settings.resolution || settings.resolution === '1080p' ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => onUpdateSettings({ ...settings, resolution: '1280x960', aspectRatio: '4:3' })}
                          style={{ padding: '6px 12px', fontSize: '11px', fontWeight: 700 }}
                          title="1280x960 — киберспортивный стандарт"
                        >
                          1280x960 ⭐
                        </button>
                        <button
                          type="button"
                          className={`btn ${settings.resolution === '1440x1080' ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => onUpdateSettings({ ...settings, resolution: '1440x1080', aspectRatio: '4:3' })}
                          style={{ padding: '6px 12px', fontSize: '11px', fontWeight: 700 }}
                          title="1440x1080 — высокая четкость Stretched"
                        >
                          1440x1080
                        </button>
                        <button
                          type="button"
                          className={`btn ${settings.resolution === '1024x768' ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => onUpdateSettings({ ...settings, resolution: '1024x768', aspectRatio: '4:3' })}
                          style={{ padding: '6px 12px', fontSize: '11px', fontWeight: 700 }}
                          title="1024x768 — классический 4:3"
                        >
                          1024x768
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          className={`btn ${settings.resolution === '1080p' || settings.resolution === '1920x1080' ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => onUpdateSettings({ ...settings, resolution: '1080p', aspectRatio: '16:9' })}
                          style={{ padding: '6px 12px', fontSize: '11px', fontWeight: 700 }}
                        >
                          1080p Full HD
                        </button>
                        <button
                          type="button"
                          className={`btn ${settings.resolution === '720p' ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => onUpdateSettings({ ...settings, resolution: '720p', aspectRatio: '16:9' })}
                          style={{ padding: '6px 12px', fontSize: '11px', fontWeight: 700 }}
                        >
                          720p HD
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* FPS & Smoothness */}
              <div style={{ backgroundColor: '#131620', border: '1px solid #232838', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <label style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', display: 'block' }}>
                      Частота кадров рендера (FPS)
                    </label>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      60 FPS гарантирует идеальную плавность выстрелов и спрея в CS2.
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {([120, 60, 30] as const).map((fps) => (
                      <button
                        key={fps}
                        className={`btn ${settings.fps === fps ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => onUpdateSettings({ ...settings, fps })}
                        style={{ padding: '6px 14px', fontSize: '12px', fontWeight: 700 }}
                      >
                        {fps === 120 ? '⚡ 120 FPS' : `${fps} FPS`}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: RADAR & MINIMAP */}
          {activeTab === 'radar' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ backgroundColor: '#131620', border: '1px solid #232838', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div>
                    <label style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', display: 'block' }}>
                      🗺️ 2D Радар / Мини-карта в CS2
                    </label>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      Размер и поведение карты на записи: динамика за игроком или турнирный обзор
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                  {[
                    { id: 'player_focus', label: '🧭 Динамический', desc: 'Центрируется и вращается за игроком POV' },
                    { id: 'broadcast', label: '📡 Турнирный BLAST', desc: 'Вся карта, фиксированный север' },
                    { id: 'hidden', label: '🚫 Без радара', desc: 'Скрыть радар (чистый экран)' },
                  ].map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      className={`btn ${(settings.radarMode || 'player_focus') === r.id ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => onUpdateSettings({ ...settings, radarMode: r.id as any })}
                      style={{ textAlign: 'left', padding: '12px 14px' }}
                    >
                      <div style={{ fontWeight: 700, fontSize: '12px' }}>{r.label}</div>
                      <div style={{ fontSize: '10px', opacity: 0.75, marginTop: '4px' }}>{r.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: HUD & KILLFEED */}
          {activeTab === 'hud' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ backgroundColor: '#131620', border: '1px solid #232838', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div>
                    <label style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', display: 'block' }}>
                      🏆 Игровой интерфейс (HUD)
                    </label>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      3 основных режима записи интерфейса в CS2
                    </div>
                  </div>
                </div>

                {/* 3 Main HUD Presets */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '14px' }}>
                  {[
                    { id: 'real', label: '🎥 REAL (OBS Запись)', desc: '1:1 как живая игра: без X-Ray, без плашки спектатора, круглый радар' },
                    { id: 'full', label: '📺 Spectator Pro', desc: 'Турнирный спектатор: HP, патроны, счет' },
                    { id: 'none', label: '🎬 No HUD (Чисто)', desc: 'Полное скрытие для оверлеев и мувиков' },
                  ].map((h) => (
                    <button
                      key={h.id}
                      type="button"
                      className={`btn ${settings.hudMode === h.id ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => {
                        const isReal = h.id === 'real'
                        onUpdateSettings({
                          ...settings,
                          hudMode: h.id as any,
                          hudScale: isReal ? 1.0 : (settings.hudScale || 0.95),
                          ...(isReal ? { xray: false, radarMode: 'player_focus' } : {}),
                        })
                      }}
                      style={{ textAlign: 'left', padding: '12px 14px' }}
                    >
                      <div style={{ fontWeight: 700, fontSize: '12px' }}>{h.label}</div>
                      <div style={{ fontSize: '10px', opacity: 0.75, marginTop: '4px' }}>{h.desc}</div>
                    </button>
                  ))}
                </div>

                {/* Advanced HUD Toggles */}
                <div style={{ backgroundColor: '#0e111a', border: '1px solid #1c2230', borderRadius: '8px', padding: '14px', marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.04em' }}>
                    ⚙️ РАСШИРЕННЫЕ НАСТРОЙКИ HUD (ТУМБЛЕРЫ)
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    {/* Overhead Name Tags */}
                    <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', backgroundColor: '#131622', borderRadius: '6px', cursor: 'pointer', border: '1px solid #23283c' }}>
                      <span style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600 }}>👤 Ники над головами</span>
                      <input
                        type="checkbox"
                        checked={settings.overheadMode !== false}
                        onChange={(e) => onUpdateSettings({ ...settings, overheadMode: e.target.checked })}
                        style={{ accentColor: '#38bdf8', width: '16px', height: '16px', cursor: 'pointer' }}
                      />
                    </label>

                    {/* Killfeed only */}
                    <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', backgroundColor: '#131622', borderRadius: '6px', cursor: 'pointer', border: '1px solid #23283c' }}>
                      <span style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600 }}>⚔️ Только киллфид</span>
                      <input
                        type="checkbox"
                        checked={Boolean(settings.killfeedOnly)}
                        onChange={(e) => onUpdateSettings({ ...settings, killfeedOnly: e.target.checked })}
                        style={{ accentColor: '#38bdf8', width: '16px', height: '16px', cursor: 'pointer' }}
                      />
                    </label>

                    {/* Alive counter mode: numbers vs avatars */}
                    <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', backgroundColor: '#131622', borderRadius: '6px', cursor: 'pointer', border: '1px solid #23283c' }}>
                      <span style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600 }}>🔢 Живые цифрой (5 v 3)</span>
                      <input
                        type="checkbox"
                        checked={Boolean(settings.teamcounterMode)}
                        onChange={(e) => onUpdateSettings({ ...settings, teamcounterMode: e.target.checked })}
                        style={{ accentColor: '#38bdf8', width: '16px', height: '16px', cursor: 'pointer' }}
                      />
                    </label>

                    {/* HUD Scale */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 12px', backgroundColor: '#131622', borderRadius: '6px', border: '1px solid #23283c' }}>
                      <span style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600 }}>📏 Размер HUD</span>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        {[
                          { scale: 0.95, label: '95%' },
                          { scale: 1.0, label: '100%' },
                          { scale: 1.15, label: '115%' },
                        ].map((s) => (
                          <button
                            key={s.scale}
                            type="button"
                            onClick={() => onUpdateSettings({ ...settings, hudScale: s.scale })}
                            style={{
                              padding: '2px 6px',
                              fontSize: '10px',
                              fontWeight: 700,
                              borderRadius: '4px',
                              border: settings.hudScale === s.scale ? '1px solid #38bdf8' : '1px solid #2b3244',
                              backgroundColor: settings.hudScale === s.scale ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                              color: settings.hudScale === s.scale ? '#38bdf8' : '#94a3b8',
                              cursor: 'pointer',
                            }}
                          >
                            {s.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* X-Ray Toggle */}
                <div
                  style={{
                    padding: '12px 14px',
                    backgroundColor: '#0e111a',
                    border: '1px solid #1c2230',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    marginTop: '12px',
                  }}
                  onClick={() => onUpdateSettings({ ...settings, xray: !settings.xray })}
                >
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>
                      Силуэты сквозь стены (X-Ray)
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      {settings.xray !== false
                        ? 'Включено: подсветка контуров игроков через стены (spec_show_xray 1)'
                        : 'Отключено: честный вид без подсветки сквозь стены'}
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.xray !== false}
                    onChange={(e) => onUpdateSettings({ ...settings, xray: e.target.checked })}
                    style={{ width: '18px', height: '18px', accentColor: '#38bdf8', cursor: 'pointer' }}
                  />
                </div>

                {/* Watermark Logo Toggle */}
                <div
                  style={{
                    padding: '12px 14px',
                    backgroundColor: '#0e111a',
                    border: '1px solid #1c2230',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    marginTop: '10px',
                  }}
                  onClick={() => onUpdateSettings({ ...settings, watermark: settings.watermark === false })}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <img
                      src="/logo_video.png"
                      alt="Watermark logo"
                      style={{
                        height: '28px',
                        width: 'auto',
                        maxWidth: '90px',
                        objectFit: 'contain',
                        borderRadius: '4px',
                        filter: 'drop-shadow(0 0 6px rgba(56, 189, 248, 0.4))',
                      }}
                    />
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>
                        Водяной знак dem.Toshka (слева сверху)
                      </div>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                        {settings.watermark !== false
                          ? 'Включено: фирменный вотермарк dem.Toshka в левом верхнем углу видео'
                          : 'Отключено: запись без водяного знака (чистое видео)'}
                      </div>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.watermark !== false}
                    onChange={(e) => onUpdateSettings({ ...settings, watermark: e.target.checked })}
                    onClick={(e) => e.stopPropagation()}
                    style={{ width: '18px', height: '18px', accentColor: '#38bdf8', cursor: 'pointer' }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: CAMERA POV & CROSSHAIR */}
          {activeTab === 'camera' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* POV Camera Director */}
              <div style={{ backgroundColor: '#131620', border: '1px solid #232838', borderRadius: '10px', padding: '16px' }}>
                <label style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', display: 'block', marginBottom: '8px' }}>
                  🎥 Режим камеры (POV съемки)
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginBottom: '10px' }}>
                  <button
                    type="button"
                    className={`btn ${settings.perspective === 'attacker' || !settings.perspective ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => onUpdateSettings({ ...settings, perspective: 'attacker' })}
                    style={{ textAlign: 'left', padding: '10px 12px' }}
                  >
                    <div style={{ fontWeight: 700 }}>👑 Главный герой (ГГ)</div>
                    <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '2px' }}>Камера от лица автора фрагов</div>
                  </button>
                  <button
                    type="button"
                    className={`btn ${settings.perspective === 'dynamic_killcam' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => onUpdateSettings({ ...settings, perspective: 'dynamic_killcam' })}
                    style={{ textAlign: 'left', padding: '10px 12px' }}
                  >
                    <div style={{ fontWeight: 700 }}>🎬 Турнирный Килл-кам</div>
                    <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '2px' }}>Жертва ➔ ГГ за 2с до фрага</div>
                  </button>
                  <button
                    type="button"
                    className={`btn ${settings.perspective === 'victim' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => onUpdateSettings({ ...settings, perspective: 'victim' })}
                    style={{ textAlign: 'left', padding: '10px 12px' }}
                  >
                    <div style={{ fontWeight: 700 }}>💀 Только жертва</div>
                    <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '2px' }}>Глазами убитого противника</div>
                  </button>
                </div>
              </div>

              {/* Crosshair Preset Selector */}
              <div style={{ backgroundColor: '#131620', border: '1px solid #232838', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>
                    🎯 Прицел в CS2
                  </label>
                  <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 700 }}>
                    {settings.crosshairPreset === 'default'
                      ? 'Дефолтный CS2'
                      : settings.crosshairPreset === 'hidden'
                      ? 'Скрыт'
                      : 'Прицел игрока (Pro)'}
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '12px' }}>
                  {[
                    { id: 'default', label: '🎮 Дефолтный CS2', desc: 'Родной прицел игры' },
                    { id: 'pro_cyan', label: '🎯 Прицел игрока (Pro)', desc: 'Кастомный с цветом' },
                    { id: 'hidden', label: '🚫 Без прицела', desc: 'Для мувиков' },
                  ].map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      className={`btn ${(settings.crosshairPreset || 'default') === p.id ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '8px 10px', textAlign: 'left' }}
                      onClick={() =>
                        onUpdateSettings({
                          ...settings,
                          crosshairPreset: p.id as any,
                          customCrosshair: p.id === 'pro_cyan',
                        })
                      }
                    >
                      <div style={{ fontSize: '11px', fontWeight: 700 }}>{p.label}</div>
                      <div style={{ fontSize: '9px', opacity: 0.75, marginTop: '2px' }}>{p.desc}</div>
                    </button>
                  ))}
                </div>

                {/* Pre-roll & Post-roll timings */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', borderTop: '1px solid #1e2433', paddingTop: '12px' }}>
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
          )}
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>
            📁 Сохранение клипов в папку <code>renders/</code>
          </div>
          <button className="btn btn-primary" onClick={onClose} style={{ padding: '6px 18px', fontWeight: 700 }}>
            Применить настройки
          </button>
        </div>
      </div>
    </div>
  )
}
