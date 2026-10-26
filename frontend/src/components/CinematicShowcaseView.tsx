import React from 'react'
import './CinematicShowcaseView.css'
import { useTranslation } from '../i18n'

interface CinematicShowcaseViewProps {
  onOpenStudio?: () => void
  onOpenLibrary?: () => void
}

export const CinematicShowcaseView: React.FC<CinematicShowcaseViewProps> = ({
  onOpenStudio,
  onOpenLibrary,
}) => {
  const { t, lang } = useTranslation()

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
                <span className="eyebrow-status">{t('showcase.heroStatus')}</span>
              </div>

              <div className="hero-brand-line">
                <div className="hero-brand-name">
                  <span className="highlight">dem.Toshka</span> | pytoshka
                </div>
                <h1 className="hero-headline">
                  {t('showcase.heroTitle1')} <br />
                  <span className="text-gradient">{t('showcase.heroTitle2')}</span>
                </h1>
              </div>

              <p className="hero-description">
                {t('showcase.heroDesc')}
              </p>

              <div className="hero-cta-group">
                {/* 1. PRIMARY STUDIO LAUNCHER BUTTON */}
                {onOpenStudio && (
                  <button
                    type="button"
                    onClick={onOpenStudio}
                    className="btn-hero-studio-primary"
                    title={lang === "ru" ? "Перейти в рабочий интерфейс студии хайлайтов" : "Open Highlights Studio"}
                  >
                    <span className="btn-hero-studio-icon">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                        <polygon points="5 3 19 12 5 21 5 3" />
                      </svg>
                    </span>
                    <span>{t('showcase.openStudioBtn')}</span>
                    <span className="btn-hero-studio-arrow">➔</span>
                  </button>
                )}

                {/* 2. TELEGRAM CHANNEL */}
                <a
                  href="https://t.me/thepytoshka"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-hero-telegram"
                  title={lang === "ru" ? "Официальный Telegram канал разработчика @thepytoshka" : "Official developer Telegram channel @thepytoshka"}
                >
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
                  </svg>
                  <span>{t('showcase.followDev')}</span>
                </a>

                {/* 3. EXPLORE FEATURES */}
                <button
                  type="button"
                  onClick={() => scrollToSection('features')}
                  className="btn-hero-secondary"
                >
                  <span>{t('showcase.featuresBtn')}</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M7 13l5 5 5-5M7 6l5 5 5-5" />
                  </svg>
                </button>
              </div>

              {/* Technical Spec Row */}
              <div className="hero-specs-row">
                <div className="hero-spec-item">
                  <span className="hero-spec-label">{t('showcase.archTitle')}</span>
                  <span className="hero-spec-value">{t('showcase.archValue')}</span>
                </div>
                <div className="hero-spec-item">
                  <span className="hero-spec-label">{t('showcase.engineTitle')}</span>
                  <span className="hero-spec-value">{t('showcase.engineValue')}</span>
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

                {/* Layered Floating Header Bar (No Button Overlap) */}
                <div className="hero-artwork-top-bar">
                  <div className="hero-floating-hud-top">
                    <span className="floating-hud-badge">LIVE DEMO</span>
                    <span className="floating-hud-title">de_mirage // SUBTICK</span>
                  </div>

                  {onOpenStudio && (
                    <button
                      type="button"
                      className="hero-floating-studio-cta"
                      onClick={onOpenStudio}
                      title={lang === "ru" ? "Перейти в Студию хайлайтов" : "Go to Highlights Studio"}
                    >
                      <span className="live-pulse-dot" />
                      <span>{t('showcase.openInStudio')}</span>
                      <span>➔</span>
                    </button>
                  )}
                </div>

                {/* Layered Bottom Card: Clear Highlight Detection Showcase */}
                <div className="hero-floating-killfeed">
                  <div className="killfeed-badge-header">
                    <span className="killfeed-pill-accent">🎯 {lang === "ru" ? "ПРИМЕР ХАЙЛАЙТА" : "HIGHLIGHT EXAMPLE"}</span>
                    <span className="killfeed-pill-badge">CLUTCH 1v3</span>
                  </div>
                  <div className="killfeed-row">
                    <span className="killfeed-attacker">pytoshka <small>({lang === "ru" ? "Игрок" : "Player"})</small></span>
                    <span className="killfeed-weapon">
                      ⚡ AK-47 <span style={{ color: '#ef4444' }}>HEADSHOT</span>
                    </span>
                    <span className="killfeed-victim">s1mple <small>({lang === "ru" ? "Жертва" : "Victim"})</small></span>
                  </div>
                  <div className="killfeed-meta">
                    <span>{lang === "ru" ? "РАУНД 24 // ТАКТИЧЕСКИЙ РАЗМЕН" : "ROUND 24 // TACTICAL TRADE"}</span>
                    <span style={{ color: '#38bdf8', fontWeight: 700 }}>{lang === "ru" ? "+3 КИЛЛА ЗА 2.4 СЕК" : "+3 KILLS IN 2.4S"}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          1.5. STUDIO FAST-TRACK ACTION STRIP
          ==================================================================== */}
      <div className="showcase-studio-strip">
        <div className="showcase-container">
          <div className="studio-strip-card">
            <div className="studio-strip-left">
              <span className="studio-strip-tag">{t('showcase.stripTag')}</span>
              <h3 className="studio-strip-title">{t('showcase.stripTitle')}</h3>
              <p className="studio-strip-desc">{t('showcase.stripDesc')}</p>
            </div>
            <div className="studio-strip-right">
              {onOpenStudio && (
                <button
                  type="button"
                  onClick={onOpenStudio}
                  className="btn-strip-studio"
                  title={lang === "ru" ? "Открыть рабочую студию хайлайтов" : "Launch Highlights Studio"}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  <span>{t('showcase.stripStudioBtn')}</span>
                  <span>➔</span>
                </button>
              )}
              {onOpenLibrary && (
                <button
                  type="button"
                  onClick={onOpenLibrary}
                  className="btn-strip-library"
                  title={lang === "ru" ? "Перейти в Библиотеку сохраненных матчей" : "Go to Match Library"}
                >
                  <span>{t('showcase.stripLibraryBtn')}</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ====================================================================
          2. FEATURE SHOWCASE (EDITORIAL CARDS)
          ==================================================================== */}
      <section id="features" className="section-padding">
        <div className="showcase-container">
          <div className="section-header">
            <span className="section-tag">// 02 ARCHITECTURE & FEATURES</span>
            <h2 className="section-title">{t('showcase.featuresHeadline')}</h2>
            <p className="section-subtitle">
              {t('showcase.featuresSubheadline')}
            </p>
          </div>

          <div className="features-grid">
            {/* Card 1: Automatic Highlights */}
            <div className="feature-card">
              <div className="feature-card-header">
                <span className="feature-index">SYS.01</span>
                <span className="status-badge ready">{lang === "ru" ? "ГОТОВО В СТУДИИ" : "STUDIO READY"}</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
              </div>
              <h3 className="feature-title">{lang === "ru" ? "Автоматический поиск хайлайтов" : "Automated Highlight Discovery"}</h3>
              <p className="feature-text">
                {lang === "ru"
                  ? "Парсер Source 2 сканирует всю демку и мгновенно находит мультикиллы (3K, 4K, ACE), выигранные клатчи 1vX, ниндзя-дефьюзы и спрей-трансферы с таймкодами."
                  : "Source 2 parser scans the entire demo and instantly detects multikills (3K, 4K, ACE), won 1vX clutches, ninja defuses, and spray transfers with precise tick timestamps."}
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
                <span className="status-badge ready">{lang === "ru" ? "ГОТОВО В СТУДИИ" : "STUDIO READY"}</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
              </div>
              <h3 className="feature-title">{lang === "ru" ? "Любой ракурс POV" : "Any Camera Angle & POV"}</h3>
              <p className="feature-text">
                {lang === "ru"
                  ? "Смотри эпизод от своего первого лица (Hero POV), от лица соперника или включи турнирный динамический килл-кам, который показывает удержание угла жертвой и переключается на стрелка за 2 секунды до выстрела."
                  : "Watch clips from first-person Hero POV, opponent perspective, or tournament dynamic killcam showing victim crosshair hold and switching to fragger 2s before firing."}
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
                <span className="status-badge ready">{lang === "ru" ? "ГОТОВО В СТУДИИ" : "STUDIO READY"}</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                  <line x1="8" y1="21" x2="16" y2="21" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
              </div>
              <h3 className="feature-title">{lang === "ru" ? "Твой HUD — твой стиль" : "Your HUD — Your Signature Style"}</h3>
              <p className="feature-text">
                {lang === "ru"
                  ? "Полный контроль над визуалом кадра: классический CS2 интерфейс, спектаторский режим, минималистичный только-киллфид или абсолютно чистый No-HUD для кинематографичных монтажей."
                  : "Complete aesthetic control: classic CS2 interface, spectator mode, minimalist killfeed-only, or clean cinematic No-HUD for movie edits."}
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
                <span className="status-badge ready">{lang === "ru" ? "ГОТОВО В СТУДИИ" : "STUDIO READY"}</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polygon points="10 8 16 12 10 16 10 8" />
                </svg>
              </div>
              <h3 className="feature-title">{lang === "ru" ? "Запись в стиле OBS (Режим REAL)" : "OBS-Style Recording (REAL Mode)"}</h3>
              <p className="feature-text">
                {lang === "ru"
                  ? "Отключение X-Ray и спектаторских панелей со счетом внизу. Видео выглядит в точности как чистый захват экрана от лица игрока во время живого матча: с его здоровьем, патронами и круглым радаром."
                  : "Disables X-Ray and spectator score bars. Captured video looks identical to a genuine live game stream from player POV with health, ammo and rotating mini-map."}
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
                <span className="status-badge ready">{lang === "ru" ? "ГОТОВО В СТУДИИ" : "STUDIO READY"}</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
              </div>
              <h3 className="feature-title">{lang === "ru" ? "История матчей и аналитика" : "Match History & Tactical Analytics"}</h3>
              <p className="feature-text">
                {lang === "ru"
                  ? "Внутренняя библиотека ранее сыгранных матчей, интерактивная 2D карта, разбор выигранных дуэлей, ADR и объективный анализ полезности игрока по раундам."
                  : "Integrated demo library, interactive 2D replay radar, opening duel efficiency, ADR, and round-by-round player impact breakdown."}
              </p>
              <div className="feature-footer-tags">
                <span className="tech-tag">MATCH ARCHIVE</span>
                <span className="tech-tag">2D REPLAY</span>
                <span className="tech-tag">DUEL STATS</span>
              </div>
            </div>

            {/* Card 6: Continuous Batching Montage */}
            <div className="feature-card">
              <div className="feature-card-header">
                <span className="feature-index">SYS.06</span>
                <span className="status-badge ready">{lang === "ru" ? "ГОТОВО В СТУДИИ" : "STUDIO READY"}</span>
              </div>
              <div className="feature-icon-wrap">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
                  <line x1="7" y1="2" x2="7" y2="22" />
                  <line x1="17" y1="2" x2="17" y2="22" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                </svg>
              </div>
              <h3 className="feature-title">{lang === "ru" ? "Пакетный рендер и монтаж" : "Continuous Batch Render & Montage"}</h3>
              <p className="feature-text">
                {lang === "ru"
                  ? "Single-Launch Continuous Batching: CS2 запускается один раз и по очереди записывает все выбранные моменты без перезапуска игры. FFmpeg объединяет клипы в готовый хайлайт-ролик."
                  : "Single-Launch Continuous Batching: CS2 opens once and records all selected clips in sequence without restarting. FFmpeg stitches clips into a ready-to-share montage."}
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
          3. HOW IT WORKS (3 CONNECTED STEPS)
          ==================================================================== */}
      <section id="workflow" className="section-padding">
        <div className="showcase-container">
          <div className="section-header">
            <span className="section-tag">// 03 WORKFLOW PIPELINE</span>
            <h2 className="section-title">{t('showcase.howItWorks')}</h2>
            <p className="section-subtitle">
              {t('showcase.pipelineSubtitle')}
            </p>
          </div>

          <div className="workflow-grid">
            {/* Step 1 */}
            <div className="workflow-card">
              <div className="workflow-step-num">01</div>
              <h3 className="workflow-title">{t('showcase.step1Title')}</h3>
              <p className="workflow-text">
                {t('showcase.step1Desc')}
              </p>
              <div className="workflow-command-hint">
                AWPY SOURCE 2 PARSE → TICK METADATA
              </div>
            </div>

            {/* Step 2 */}
            <div className="workflow-card">
              <div className="workflow-step-num">02</div>
              <h3 className="workflow-title">{t('showcase.step2Title')}</h3>
              <p className="workflow-text">
                {t('showcase.step2Desc')}
              </p>
              <div className="workflow-command-hint">
                HIGHLIGHT DETECTOR → BATCH SELECTION
              </div>
            </div>

            {/* Step 3 */}
            <div className="workflow-card">
              <div className="workflow-step-num">03</div>
              <h3 className="workflow-title">{t('showcase.step3Title')}</h3>
              <p className="workflow-text">
                {t('showcase.step3Desc')}
              </p>
              <div className="workflow-command-hint">
                CONTINUOUS BATCHING → FINAL MP4
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          4. FREE ACCESS PHILOSOPHY
          ==================================================================== */}
      <section className="section-padding" style={{ borderBottom: 'none' }}>
        <div className="showcase-container">
          <div className="philosophy-banner">
            <span className="section-tag">// 04 PHILOSOPHY</span>
            <h2 className="philosophy-title">{t('showcase.philosophyTitle')}</h2>
            <p className="section-subtitle" style={{ maxWidth: '780px' }}>
              {t('showcase.philosophyDesc')}
            </p>

            <div className="philosophy-pillars">
              <div className="pillar-item">
                <span className="pillar-icon">🛡️</span>
                <h3 className="pillar-heading">{lang === "ru" ? "100% Local-First & Приватность" : "100% Local-First & Privacy"}</h3>
                <p className="pillar-text">
                  {lang === "ru"
                    ? "Все демки, лог-файлы и записанные видеоролики остаются исключительно на вашем компьютере. Никакой передачи конфиденциальных файлов в облако."
                    : "All demos, logs, and rendered video clips stay exclusively on your computer. Zero uploads to external servers or cloud services."}
                </p>
              </div>

              <div className="pillar-item">
                <span className="pillar-icon">⚡</span>
                <h3 className="pillar-heading">{lang === "ru" ? "Честное исходное качество" : "True Pristine Engine Quality"}</h3>
                <p className="pillar-text">
                  {lang === "ru"
                    ? "Запись через движок CS2 гарантирует честные 60 или 120 кадров в секунду, высокий битрейт и отсутствие артефактов стороннего сжатия."
                    : "In-engine CS2 rendering guarantees genuine 60 or 120 FPS, maximum crisp bitrate, and zero compression artifacts."}
                </p>
              </div>

              <div className="pillar-item">
                <span className="pillar-icon">🖤</span>
                <h3 className="pillar-heading">{lang === "ru" ? "Сделано для сообщества" : "Crafted for the Community"}</h3>
                <p className="pillar-text">
                  {lang === "ru"
                    ? "Разработка ведется независимым автором с любовью к киберспорту CS2 и мувимейкингу."
                    : "Developed by an independent creator with a genuine passion for CS2 esports and cinematic moviemaking."}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          5. CREATOR SECTION (TELEGRAM & YOUTUBE)
          ==================================================================== */}
      <section id="creator" className="section-padding">
        <div className="showcase-container">
          <div className="section-header">
            <span className="section-tag crimson">// 05 CREATOR & COMMUNITY</span>
            <h2 className="section-title">{t('showcase.creatorTitle')}</h2>
            <p className="section-subtitle">
              {t('showcase.creatorSub')}
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
                  <h3 className="creator-channel-name">{lang === "ru" ? "Telegram-канал" : "Telegram Channel"}</h3>
                  <div className="creator-channel-handle">@thepytoshka</div>
                  <p className="creator-channel-desc">
                    {lang === "ru" ? "Дневники разработки, анонсы новых версий, опросы по функционалу и закрытые бета-тесты." : "Devlogs, new feature announcements, community polls, and closed beta access."}
                  </p>
                </div>
              </div>

              <a
                href="https://t.me/thepytoshka"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-channel-action tg"
              >
                {lang === "ru" ? "ПЕРЕЙТИ В TELEGRAM" : "OPEN TELEGRAM"}
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
                  <h3 className="creator-channel-name">{lang === "ru" ? "YouTube-канал" : "YouTube Channel"}</h3>
                  <div className="creator-channel-handle crimson">@thePytoshka</div>
                  <p className="creator-channel-desc">
                    {lang === "ru" ? "Видеодемонстрации работы студии, туториалы по рендеру через HLAE и готовые кинематографичные хайлайты." : "Studio video showcases, HLAE rendering guides, and cinematic community highlights."}
                  </p>
                </div>
              </div>

              <a
                href="https://www.youtube.com/@thePytoshka"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-channel-action yt"
              >
                {lang === "ru" ? "СМОТРЕТЬ НА YOUTUBE" : "WATCH ON YOUTUBE"}
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
                {lang === "ru" ? "Твои демки — твои лучшие моменты." : "Your demos — your best moments."}
              </div>
            </div>

            <div className="footer-links-group">
              <div className="footer-nav-col">
                <span className="footer-col-title">{lang === "ru" ? "НАВИГАЦИЯ" : "NAVIGATION"}</span>
                <button type="button" className="footer-link" onClick={() => scrollToSection('features')}>
                  {lang === "ru" ? "Возможности" : "Features"}
                </button>
                <button type="button" className="footer-link" onClick={() => scrollToSection('workflow')}>
                  {lang === "ru" ? "Как это работает" : "How it Works"}
                </button>
              </div>

              <div className="footer-nav-col">
                <span className="footer-col-title">{lang === "ru" ? "СООБЩЕСТВО" : "COMMUNITY"}</span>
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
                  <span className="footer-col-title">{lang === "ru" ? "ПРИЛОЖЕНИЕ" : "APPLICATION"}</span>
                  <button type="button" className="footer-link" onClick={onOpenStudio}>
                    {lang === "ru" ? "Студия хайлайтов" : "Highlights Studio"}
                  </button>
                  {onOpenLibrary && (
                    <button type="button" className="footer-link" onClick={onOpenLibrary}>
                      {lang === "ru" ? "Библиотека демок" : "Match Library"}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="footer-bottom">
            <div className="footer-disclaimer">
              {t('showcase.disclaimer')}
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
