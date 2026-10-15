import React, { useState } from 'react'
import './CinematicShowcaseView.css'

interface CinematicShowcaseViewProps {
  onOpenStudio?: () => void
  onOpenLibrary?: () => void
}

type PovType = 'hero' | 'enemy' | 'director'
type HudType = 'real' | 'minimal' | 'clean'

export const CinematicShowcaseView: React.FC<CinematicShowcaseViewProps> = ({
  onOpenStudio,
  onOpenLibrary,
}) => {
  // Interactive Simulator States
  const [povMode, setPovMode] = useState<PovType>('hero')
  const [hudMode, setHudMode] = useState<HudType>('real')
  const [showWatermark, setShowWatermark] = useState<boolean>(true)
  const [showRadar, setShowRadar] = useState<boolean>(true)

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="cinematic-showcase">
      {/* ====================================================================
          1. CINEMATIC HERO SECTION
          ==================================================================== */}
      <section className="hero-section">
        <div className="hero-backdrop-glow" />
        <div className="showcase-container">
          <div className="hero-grid">
            {/* Left Column: Hero Text & CTAs */}
            <div className="hero-content">
              <div className="hero-eyebrow">
                <span className="eyebrow-dot" />
                <span className="eyebrow-text">INDEPENDENT CS2 PROJECT</span>
                <span className="eyebrow-status">В РАЗРАБОТКЕ</span>
              </div>

              <div className="hero-brand-line">
                <div className="hero-brand-name">
                  <span className="highlight">dem.Toshka</span> | pytoshka
                </div>
                <h1 className="hero-headline">
                  Твои демки. <br />
                  <span className="text-gradient">Твои лучшие моменты.</span>
                </h1>
              </div>

              <p className="hero-description">
                Превращай демки CS2 в хайлайты. Выбирай POV, настраивай HUD и сохраняй моменты,
                которые хочется пересматривать. Локальный движок рендера на базе Source 2 и HLAE.
              </p>

              <div className="hero-cta-group">
                <a
                  href="https://t.me/thepytoshka"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-hero-primary"
                  title="Официальный Telegram канал разработчика"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
                  </svg>
                  СЛЕДИТЬ ЗА РАЗРАБОТКОЙ
                </a>

                <button
                  type="button"
                  onClick={() => scrollToSection('features')}
                  className="btn-hero-secondary"
                >
                  ВОЗМОЖНОСТИ ПРОЕКТА
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M7 13l5 5 5-5M7 6l5 5 5-5" />
                  </svg>
                </button>

                {onOpenStudio && (
                  <button
                    type="button"
                    onClick={onOpenStudio}
                    className="btn-hero-studio"
                    title="Перейти в рабочий интерфейс студии хайлайтов"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                    ОТКРЫТЬ СТУДИЮ
                  </button>
                )}
              </div>

              {/* Technical Spec Row */}
              <div className="hero-specs-row">
                <div className="hero-spec-item">
                  <span className="hero-spec-label">ARCHITECTURE</span>
                  <span className="hero-spec-value">LOCAL-FIRST / DESKTOP</span>
                </div>
                <div className="hero-spec-item">
                  <span className="hero-spec-label">DEMO ENGINE</span>
                  <span className="hero-spec-value">CS2 SOURCE 2 (AWPY)</span>
                </div>
                <div className="hero-spec-item">
                  <span className="hero-spec-label">RECORDING</span>
                  <span className="hero-spec-value">HLAE + FFMPEG 120 FPS</span>
                </div>
              </div>
            </div>

            {/* Right Column: Misaki Mei Cinematic Artwork & Layered HUD */}
            <div className="hero-visual-stage">
              <div className="hero-artwork-wrap">
                <img
                  src="/misaki_mei_hero.png"
                  alt="Misaki Mei — dem.Toshka Art Motif"
                  className="hero-artwork-img"
                  onError={(e) => {
                    // Fallback to jpg if png is not found
                    (e.target as HTMLImageElement).src = '/misaki_mei_hero.jpg'
                  }}
                />
                <div className="hero-artwork-vignette" />

                {/* Layered Floating HUD Badges */}
                <div className="hero-floating-hud-top">
                  <span className="floating-hud-badge">LIVE DEMO</span>
                  <span className="floating-hud-title">de_mirage // TICK 64-128</span>
                </div>

                <div className="hero-floating-killfeed">
                  <div className="killfeed-row">
                    <span className="killfeed-attacker">pytoshka</span>
                    <span className="killfeed-weapon">
                      ⚡ AK-47 <span style={{ color: '#ef4444' }}>HS</span>
                    </span>
                    <span className="killfeed-victim">s1mple</span>
                  </div>
                  <div className="killfeed-meta">
                    <span>ROUND 24 // CLUTCH 1v3</span>
                    <span style={{ color: '#38bdf8' }}>+3 KILLS IN 2.4s</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          2. FEATURE SHOWCASE (EDITORIAL CARDS)
          ==================================================================== */}
      <section id="features" className="section-padding">
        <div className="showcase-container">
          <div className="section-header">
            <span className="section-tag">// 02 ARCHITECTURE & FEATURES</span>
            <h2 className="section-title">Ключевые возможности студии</h2>
            <p className="section-subtitle">
              От глубокого разбора событий в демках CS2 до пакетного захвата кинокадров без
              мучительного ручного монтажа.
            </p>
          </div>

          <div className="features-grid">
            {/* Card 1: Automatic Highlights */}
            <div className="feature-card">
              <div className="feature-card-header">
                <span className="feature-index">SYS.01</span>
                <span className="status-badge ready">ГОТОВО В СТУДИИ</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
              </div>
              <h3 className="feature-title">Автоматический поиск хайлайтов</h3>
              <p className="feature-text">
                Парсер Source 2 сканирует всю демку и мгновенно находит мультикиллы (3K, 4K, ACE),
                выигранные клатчи 1vX, ниндзя-дефьюзы и спрей-трансферы с таймкодами.
              </p>
              <div className="feature-footer-tags">
                <span className="tech-tag">ACE DETECTOR</span>
                <span className="tech-tag">CLUTCH 1vX</span>
                <span className="tech-tag">SPRAY TRANSFER</span>
              </div>
            </div>

            {/* Card 2: Any POV */}
            <div className="feature-card">
              <div className="feature-card-header">
                <span className="feature-index">SYS.02</span>
                <span className="status-badge ready">ГОТОВО В СТУДИИ</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
              </div>
              <h3 className="feature-title">Любой ракурс POV</h3>
              <p className="feature-text">
                Смотри эпизод от своего первого лица (Hero POV), от лица соперника или включи
                турнирный динамический килл-кам, который показывает удержание угла жертвой и
                переключается на стрелка за 2 секунды до выстрела.
              </p>
              <div className="feature-footer-tags">
                <span className="tech-tag">HERO POV</span>
                <span className="tech-tag">VICTIM POV</span>
                <span className="tech-tag">DYNAMIC KILL-CAM</span>
              </div>
            </div>

            {/* Card 3: Your HUD Your Style */}
            <div className="feature-card">
              <div className="feature-card-header">
                <span className="feature-index">SYS.03</span>
                <span className="status-badge ready">ГОТОВО В СТУДИИ</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                  <line x1="8" y1="21" x2="16" y2="21" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
              </div>
              <h3 className="feature-title">Твой HUD — твой стиль</h3>
              <p className="feature-text">
                Полный контроль над визуалом кадра: классический CS2 интерфейс, спектаторский режим,
                минималистичный только-киллфид или абсолютно чистый No-HUD для кинематографичных монтажей.
              </p>
              <div className="feature-footer-tags">
                <span className="tech-tag">KILLFEED-ONLY</span>
                <span className="tech-tag">CLEAN NO-HUD</span>
                <span className="tech-tag">CUSTOM SCALE</span>
              </div>
            </div>

            {/* Card 4: OBS-Style Recording (REAL) */}
            <div className="feature-card">
              <div className="feature-card-header">
                <span className="feature-index">SYS.04</span>
                <span className="status-badge ready">ГОТОВО В СТУДИИ</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polygon points="10 8 16 12 10 16 10 8" />
                </svg>
              </div>
              <h3 className="feature-title">Запись в стиле OBS (Режим REAL)</h3>
              <p className="feature-text">
                Отключение X-Ray и спектаторских панелей со счетом внизу. Видео выглядит в точности
                как чистый захват экрана от лица игрока во время живого матча: с его здоровьем, патронами и круглым радаром.
              </p>
              <div className="feature-footer-tags">
                <span className="tech-tag">ZERO X-RAY</span>
                <span className="tech-tag">ROUND RADAR</span>
                <span className="tech-tag">NATURAL POV</span>
              </div>
            </div>

            {/* Card 5: Match History & Analytics */}
            <div className="feature-card">
              <div className="feature-card-header">
                <span className="feature-index">SYS.05</span>
                <span className="status-badge planned">В РАЗРАБОТКЕ</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
              </div>
              <h3 className="feature-title">История матчей и аналитика</h3>
              <p className="feature-text">
                Внутренняя библиотека ранее сыгранных матчей, тепловые карты позиций на 2D радаре,
                разбор выигранных дуэлей, ADR и объективный анализ полезности игрока по раундам.
              </p>
              <div className="feature-footer-tags">
                <span className="tech-tag">MATCH ARCHIVE</span>
                <span className="tech-tag">HEATMAPS</span>
                <span className="tech-tag">DUEL STATS</span>
              </div>
            </div>

            {/* Card 6: Continuous Batching Montage */}
            <div className="feature-card">
              <div className="feature-card-header">
                <span className="feature-index">SYS.06</span>
                <span className="status-badge ready">ГОТОВО В СТУДИИ</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
                  <line x1="7" y1="2" x2="7" y2="22" />
                  <line x1="17" y1="2" x2="17" y2="22" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                </svg>
              </div>
              <h3 className="feature-title">Пакетный рендер и монтаж</h3>
              <p className="feature-text">
                Single-Launch Continuous Batching: CS2 запускается один раз и по очереди записывает
                все выбранные моменты без перезапуска игры. FFmpeg объединяет клипы в готовый хайлайт-ролик.
              </p>
              <div className="feature-footer-tags">
                <span className="tech-tag">CONTINUOUS BATCHING</span>
                <span className="tech-tag">AUTO FFMPEG MUX</span>
                <span className="tech-tag">120 FPS SMOOTH</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          3. INTERACTIVE POV & HUD SHOWCASE
          ==================================================================== */}
      <section id="interactive" className="section-padding">
        <div className="showcase-container">
          <div className="section-header">
            <span className="section-tag crimson">// 03 INTERACTIVE REEL STUDIO</span>
            <h2 className="section-title">Интерактивный симулятор кадра</h2>
            <p className="section-subtitle">
              Попробуйте переключить ракурсы и стили интерфейса прямо сейчас, чтобы увидеть,
              как настраивается итоговое видео.
            </p>
          </div>

          <div className="interactive-showcase-box">
            {/* Control Switcher Bar */}
            <div className="interactive-controls-bar">
              {/* POV Mode */}
              <div className="control-group">
                <span className="control-group-label">РАКУРС POV:</span>
                <div className="control-segmented-btn">
                  <button
                    type="button"
                    className={`segment-btn ${povMode === 'hero' ? 'active' : ''}`}
                    onClick={() => setPovMode('hero')}
                  >
                    👤 Свой POV (Hero)
                  </button>
                  <button
                    type="button"
                    className={`segment-btn ${povMode === 'enemy' ? 'active crimson-style' : ''}`}
                    onClick={() => setPovMode('enemy')}
                  >
                    🎯 POV Соперника
                  </button>
                  <button
                    type="button"
                    className={`segment-btn ${povMode === 'director' ? 'active' : ''}`}
                    onClick={() => setPovMode('director')}
                  >
                    🎥 Килл-кам
                  </button>
                </div>
              </div>

              {/* HUD Mode */}
              <div className="control-group">
                <span className="control-group-label">СТИЛЬ HUD:</span>
                <div className="control-segmented-btn">
                  <button
                    type="button"
                    className={`segment-btn ${hudMode === 'real' ? 'active' : ''}`}
                    onClick={() => setHudMode('real')}
                  >
                    📺 REAL (OBS)
                  </button>
                  <button
                    type="button"
                    className={`segment-btn ${hudMode === 'minimal' ? 'active' : ''}`}
                    onClick={() => setHudMode('minimal')}
                  >
                    ⚔️ Киллфид
                  </button>
                  <button
                    type="button"
                    className={`segment-btn ${hudMode === 'clean' ? 'active' : ''}`}
                    onClick={() => setHudMode('clean')}
                  >
                    🎬 Clean No-HUD
                  </button>
                </div>
              </div>

              {/* Toggles */}
              <div className="control-group">
                <button
                  type="button"
                  className={`interactive-toggle-btn ${showWatermark ? 'active' : ''}`}
                  onClick={() => setShowWatermark(!showWatermark)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 8v8" />
                    <path d="M8 12h8" />
                  </svg>
                  Водяной знак
                </button>

                <button
                  type="button"
                  className={`interactive-toggle-btn ${showRadar ? 'active' : ''}`}
                  onClick={() => setShowRadar(!showRadar)}
                  disabled={hudMode === 'clean'}
                  style={{ opacity: hudMode === 'clean' ? 0.4 : 1 }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="2" x2="12" y2="12" />
                  </svg>
                  Круглый радар
                </button>
              </div>
            </div>

            {/* Viewport Screen */}
            <div className="interactive-viewport">
              {/* Simulated CS2 Map Canvas Background */}
              <div
                className="interactive-scene-bg"
                style={{
                  backgroundImage: `linear-gradient(to bottom, rgba(6,9,14,0.4), rgba(6,9,14,0.85)), url('/maps/de_mirage.png')`,
                  backgroundSize: '160%',
                  backgroundPosition: povMode === 'enemy' ? '40% 65%' : '60% 45%',
                }}
              />
              <div className="interactive-viewport-vignette" />

              {/* Watermark in Top-Left */}
              {showWatermark && (
                <div className="viewport-watermark">
                  <img src="/logo_video.png" alt="dem.Toshka Watermark" />
                </div>
              )}

              {/* Circular CS2 Radar (Mirage) */}
              {hudMode === 'real' && showRadar && (
                <div className="viewport-radar">
                  <img src="/maps/de_mirage.png" alt="Radar Map" className="radar-map-img" />
                  <div className={`radar-player-dot ${povMode === 'enemy' ? 'enemy-style' : ''}`} />
                  <div className="radar-player-vision" />
                </div>
              )}

              {/* Top Scoreboard Bar (REAL HUD only) */}
              {hudMode === 'real' && (
                <div className="viewport-topbar">
                  <div className="topbar-team ct">
                    <span>CT</span>
                    <span className="topbar-score">12</span>
                  </div>
                  <div className="topbar-timer">0:42</div>
                  <div className="topbar-team t">
                    <span className="topbar-score">11</span>
                    <span>T</span>
                  </div>
                </div>
              )}

              {/* Center Dynamic Crosshair */}
              {hudMode !== 'clean' && (
                <div className="viewport-crosshair">
                  <div className="crosshair-cs2">
                    <div className="crosshair-gap" />
                  </div>
                </div>
              )}

              {/* Killfeed (Shown in REAL and MINIMAL modes) */}
              {hudMode !== 'clean' && (
                <div className="viewport-killfeed">
                  <div className="simulated-kill-pill">
                    <span className={`sim-attacker ${povMode === 'enemy' ? 'enemy-pov' : ''}`}>
                      {povMode === 'enemy' ? 's1mple' : 'pytoshka'}
                    </span>
                    <span className="sim-weapon">{povMode === 'enemy' ? 'M4A1-S' : 'AK-47'}</span>
                    <span className="sim-hs-icon">⚡ HS</span>
                    <span className="sim-victim">
                      {povMode === 'enemy' ? 'pytoshka' : 's1mple'}
                    </span>
                  </div>
                </div>
              )}

              {/* Bottom Vitals & Ammo HUD (REAL mode only) */}
              {hudMode === 'real' && (
                <div className="viewport-bottom-hud">
                  <div className="hud-vital-box">
                    <div className="hud-stat">
                      <span className="hud-stat-num">{povMode === 'enemy' ? '45' : '100'}</span>
                      <span className="hud-stat-label">+ HP</span>
                    </div>
                    <div className="hud-stat">
                      <span className="hud-stat-num">100</span>
                      <span className="hud-stat-label">🛡️ ARMOR</span>
                    </div>
                  </div>

                  <div className="hud-ammo-box">
                    <div className="hud-ammo-num">
                      {povMode === 'enemy' ? '20' : '27'}
                      <span className="hud-ammo-reserve"> / 90</span>
                    </div>
                    <div className="hud-weapon-name">
                      {povMode === 'enemy' ? 'M4A1-S | Printstream' : 'AK-47 | Head Shot'}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Tactical Info Footer Bar */}
            <div className="interactive-info-bar">
              <div className="info-bar-left">
                <span className="info-bar-indicator" />
                <span>
                  АКТИВНЫЙ РЕЖИМ:{' '}
                  <strong style={{ color: '#fff' }}>
                    {povMode === 'hero' ? 'СВОЙ POV (ATTACKER)' : povMode === 'enemy' ? 'POV ЖЕРТВЫ (ENEMY)' : 'ТУРНИРНЫЙ КИЛЛ-КАМ'}
                  </strong>
                  {' — '}
                  {hudMode === 'real' ? 'REAL (ПОЛНЫЙ ИНТЕРФЕЙС)' : hudMode === 'minimal' ? 'ТОЛЬКО КИЛЛФИД' : 'ЧИСТЫЙ NO-HUD'}
                </span>
              </div>
              <div>
                <span>CS2 RENDER PIPELINE: 1920x1080 @ 60/120 FPS</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          4. HOW IT WORKS (3 CONNECTED STEPS)
          ==================================================================== */}
      <section id="workflow" className="section-padding">
        <div className="showcase-container">
          <div className="section-header">
            <span className="section-tag">// 04 WORKFLOW PIPELINE</span>
            <h2 className="section-title">Пайплайн создания хайлайта</h2>
            <p className="section-subtitle">
              От сырой демки матча до готового видеоклипа без лишних манипуляций со сторонними программами.
            </p>
          </div>

          <div className="workflow-grid">
            {/* Step 1 */}
            <div className="workflow-card">
              <div className="workflow-step-num">01</div>
              <h3 className="workflow-title">Загрузка демки CS2</h3>
              <p className="workflow-text">
                Перетащите файл матча <code>.dem</code> прямо в окно программы или укажите путь.
                Локальный анализатор Awpy мгновенно извлечет тики, структуру раундов и полную телеметрию игроков.
              </p>
              <div className="workflow-command-hint">
                AWPY SOURCE 2 PARSE → TICK METADATA
              </div>
            </div>

            {/* Step 2 */}
            <div className="workflow-card">
              <div className="workflow-step-num">02</div>
              <h3 className="workflow-title">Выбор моментов</h3>
              <p className="workflow-text">
                Студия автоматически сгруппирует эйсы, клатчи, быстрые серии фрагов и дуэли.
                Выбирайте нужные клипы галочками или сформируйте подборку по конкретному игроку.
              </p>
              <div className="workflow-command-hint">
                HIGHLIGHT DETECTOR → BATCH SELECTION
              </div>
            </div>

            {/* Step 3 */}
            <div className="workflow-card">
              <div className="workflow-step-num">03</div>
              <h3 className="workflow-title">Настройка POV и рендер</h3>
              <p className="workflow-text">
                Выберите ракурс, стиль HUD, прицел и FPS (60 или 120). Запустите пакетную сессию:
                CS2 запишет все эпизоды за один прогон, а встроенный FFmpeg соберет видео.
              </p>
              <div className="workflow-command-hint">
                CONTINUOUS BATCHING → FINAL MP4
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          5. FREE ACCESS PHILOSOPHY
          ==================================================================== */}
      <section className="section-padding" style={{ borderBottom: 'none' }}>
        <div className="showcase-container">
          <div className="philosophy-banner">
            <span className="section-tag">// 05 PHILOSOPHY</span>
            <h2 className="philosophy-title">Твои хайлайты. Без лишних барьеров.</h2>
            <p className="section-subtitle" style={{ maxWidth: '780px' }}>
              Мы верим, что создание крутых игровых видеороликов должно быть доступным,
              чистым и свободным от подписок, очередей на облачных серверах и навязчивой рекламы.
            </p>

            <div className="philosophy-pillars">
              <div className="pillar-item">
                <span className="pillar-icon">🛡️</span>
                <h3 className="pillar-heading">100% Local-First & Приватность</h3>
                <p className="pillar-text">
                  Все демки, лог-файлы и записанные видеоролики остаются исключительно на вашем
                  компьютере. Никакой передачи конфиденциальных файлов в облако.
                </p>
              </div>

              <div className="pillar-item">
                <span className="pillar-icon">⚡</span>
                <h3 className="pillar-heading">Честное исходное качество</h3>
                <p className="pillar-text">
                  Запись через движок CS2 гарантирует честные 60 или 120 кадров в секунду,
                  высокий битрейт и отсутствие артефактов стороннего сжатия.
                </p>
              </div>

              <div className="pillar-item">
                <span className="pillar-icon">🖤</span>
                <h3 className="pillar-heading">Сделано для сообщества</h3>
                <p className="pillar-text">
                  Разработка ведется независимым автором с любовью к киберспорту CS2,
                  мувимейкингу и стильной эстетике темного аниме.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          6. CREATOR SECTION (TELEGRAM & YOUTUBE)
          ==================================================================== */}
      <section id="creator" className="section-padding">
        <div className="showcase-container">
          <div className="section-header">
            <span className="section-tag crimson">// 06 CREATOR & COMMUNITY</span>
            <h2 className="section-title">Сделано для тех, кто живёт CS2.</h2>
            <p className="section-subtitle">
              Следите за разработкой проекта <strong>dem.Toshka | pytoshka</strong>, участвуйте в обсуждении
              новых функций и смотрите свежие видеодемонстрации в официальных каналах.
            </p>
          </div>

          <div className="creator-cards-grid">
            {/* Telegram Card */}
            <div className="creator-card telegram">
              <div className="creator-card-top">
                <div className="creator-channel-icon tg">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
                  </svg>
                </div>
                <div className="creator-card-info">
                  <h3 className="creator-channel-name">Telegram-канал</h3>
                  <div className="creator-channel-handle">@thepytoshka</div>
                  <p className="creator-channel-desc">
                    Дневники разработки, анонсы новых версий, опросы по функционалу и закрытые бета-тесты.
                  </p>
                </div>
              </div>

              <a
                href="https://t.me/thepytoshka"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-channel-action tg"
              >
                ПЕРЕЙТИ В TELEGRAM
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
              </a>
            </div>

            {/* YouTube Card */}
            <div className="creator-card youtube">
              <div className="creator-card-top">
                <div className="creator-channel-icon yt">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                  </svg>
                </div>
                <div className="creator-card-info">
                  <h3 className="creator-channel-name">YouTube-канал</h3>
                  <div className="creator-channel-handle crimson">@thePytoshka</div>
                  <p className="creator-channel-desc">
                    Видеодемонстрации работы студии, туториалы по рендеру через HLAE и готовые кинематографичные хайлайты.
                  </p>
                </div>
              </div>

              <a
                href="https://www.youtube.com/@thePytoshka"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-channel-action yt"
              >
                СМОТРЕТЬ НА YOUTUBE
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          7. FOOTER
          ==================================================================== */}
      <footer className="cinematic-footer">
        <div className="showcase-container">
          <div className="footer-top">
            <div className="footer-brand">
              <div className="footer-logo">
                dem.Toshka <span className="accent">|</span> pytoshka
              </div>
              <div className="footer-tagline">
                Твои демки — твои лучшие моменты.
              </div>
            </div>

            <div className="footer-links-group">
              <div className="footer-nav-col">
                <span className="footer-col-title">НАВИГАЦИЯ</span>
                <button type="button" className="footer-link" onClick={() => scrollToSection('features')}>
                  Возможности
                </button>
                <button type="button" className="footer-link" onClick={() => scrollToSection('interactive')}>
                  Интерактив
                </button>
                <button type="button" className="footer-link" onClick={() => scrollToSection('workflow')}>
                  Как это работает
                </button>
              </div>

              <div className="footer-nav-col">
                <span className="footer-col-title">СООБЩЕСТВО</span>
                <a
                  href="https://t.me/thepytoshka"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="footer-link"
                >
                  Telegram: @thepytoshka
                </a>
                <a
                  href="https://www.youtube.com/@thePytoshka"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="footer-link"
                >
                  YouTube: @thePytoshka
                </a>
              </div>

              {onOpenStudio && (
                <div className="footer-nav-col">
                  <span className="footer-col-title">ПРИЛОЖЕНИЕ</span>
                  <button type="button" className="footer-link" onClick={onOpenStudio}>
                    Студия хайлайтов
                  </button>
                  {onOpenLibrary && (
                    <button type="button" className="footer-link" onClick={onOpenLibrary}>
                      Библиотека демок
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="footer-bottom">
            <div className="footer-disclaimer">
              Counter-Strike, CS2, Valve and their respective logos are trademarks and/or registered
              trademarks of Valve Corporation. dem.Toshka is an independent fan project not affiliated
              with or endorsed by Valve Corporation.
            </div>
            <div>
              © 2026 <strong>pytoshka</strong>. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default CinematicShowcaseView
