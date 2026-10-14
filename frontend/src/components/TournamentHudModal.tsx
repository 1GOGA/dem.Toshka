import React, { useState } from 'react'

interface TournamentHudModalProps {
  isOpen: boolean
  onClose: () => void
}

export const TournamentHudModal: React.FC<TournamentHudModalProps> = ({ isOpen, onClose }) => {
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  const gsiConfigSample = `"Tournament Broadcast HUD v1.0"
{
  "uri" "http://127.0.0.1:3000"
  "timeout" "1.1"
  "buffer" "0.1"
  "throttle" "0.05"
  "heartbeat" "10.0"
  "data"
  {
    "provider" "1"
    "map" "1"
    "round" "1"
    "player_id" "1"
    "player_state" "1"
    "player_weapons" "1"
    "player_match_stats" "1"
    "allplayers_id" "1"
    "allplayers_state" "1"
    "allplayers_match_stats" "1"
    "allplayers_weapons" "1"
    "allplayers_position" "1"
    "phase_countdowns" "1"
    "allgrenades" "1"
  }
}`

  const handleCopy = () => {
    navigator.clipboard.writeText(gsiConfigSample)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1100 }}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '680px', width: '92%' }}
      >
        <div className="modal-header">
          <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            🏆 Турнирные HUD и Сторонние Оверлеи CS2
          </h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body" style={{ maxHeight: '72vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Explanation Banner */}
          <div
            style={{
              padding: '14px 16px',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '8px',
              fontSize: '13px',
              lineHeight: '1.5',
              color: '#c7d2fe',
            }}
          >
            <strong>Как делают кастомный HUD на турнирах (BLAST, PGL, ESL)?</strong>
            <p style={{ margin: '6px 0 0 0', color: '#94a3b8' }}>
              В Counter-Strike 2 официальный HUD игры отключают через <code>cl_drawhud 0</code>, а поверх видео накладывают веб-интерфейс, получающий данные о матче в реальном времени через <strong>CS2 Game State Integration (GSI)</strong>.
            </p>
          </div>

          {/* Solutions & Tools Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
            {/* Lexogrine HUD Manager */}
            <div
              style={{
                backgroundColor: '#12141c',
                border: '1px solid #282d3d',
                borderRadius: '8px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '10px',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <span style={{ fontSize: '15px' }}>⚡</span>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>
                    Lexogrine HUD Manager (LHM)
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
                  Самый популярный опенсорсный инструмент для турнирных трансляций. Поддерживает десятки кастомных скинов (BLAST, PGL, IEM), аватарки команд, полоски здоровья и статистику.
                </p>
              </div>
              <a
                href="https://lexogrine.com/hud-manager"
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary"
                style={{ fontSize: '12px', textAlign: 'center', textDecoration: 'none', padding: '6px 12px' }}
              >
                ↗ Открыть Lexogrine Website
              </a>
            </div>

            {/* CS-GO-Observer-HUD / OpenHUD */}
            <div
              style={{
                backgroundColor: '#12141c',
                border: '1px solid #282d3d',
                borderRadius: '8px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '10px',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <span style={{ fontSize: '15px' }}>🎨</span>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>
                    OpenHUD & Observer Overlays
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
                  Легковесные HTML5/React оверлеи для OBS и видеоредакторов. Открытый исходный код на GitHub, легко менять цвета и шрифты под свои мувики.
                </p>
              </div>
              <a
                href="https://github.com/moritz-j/cs-go-observer-hud"
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary"
                style={{ fontSize: '12px', textAlign: 'center', textDecoration: 'none', padding: '6px 12px' }}
              >
                ↗ GitHub: Observer HUD
              </a>
            </div>
          </div>

          {/* Workflow in CS2 Highlights Studio */}
          <div
            style={{
              backgroundColor: '#161822',
              border: '1px solid #282d3d',
              borderRadius: '8px',
              padding: '14px 16px',
            }}
          >
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', marginBottom: '8px' }}>
              Как использовать кастомный HUD в нашей студии:
            </div>
            <ol style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <li>
                В настройках съемки выберите <strong>«Без HUD (Cinematic No-HUD)»</strong> или <strong>«Только Killfeed»</strong>.
              </li>
              <li>
                Запустите съемку клипов — CS2 снимет чистый 1080p60 видеоряд без лишних пикселей стандартного интерфейса.
              </li>
              <li>
                Запустите <strong>Lexogrine HUD Manager</strong> на вашем ПК, чтобы просматривать демку с профессиональным турнирным скином в реальном времени.
              </li>
              <li>
                Или наложите оверлей поверх готового MP4 в видеоредакторе (Premiere Pro, CapCut, DaVinci).
              </li>
            </ol>
          </div>

          {/* Quick GSI Config Snippet */}
          <div
            style={{
              backgroundColor: '#0d0f15',
              border: '1px solid #1f2330',
              borderRadius: '8px',
              padding: '12px 14px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#cbd5e1' }}>
                📄 Конфиг GSI: <code>gamestate_integration_hud.cfg</code>
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleCopy}
                style={{ padding: '4px 10px', fontSize: '11px' }}
              >
                {copied ? '✓ Скопировано!' : '📋 Копировать конфиг'}
              </button>
            </div>
            <pre
              style={{
                margin: 0,
                fontSize: '11px',
                color: '#64748b',
                maxHeight: '120px',
                overflowY: 'auto',
                backgroundColor: '#090a0f',
                padding: '8px',
                borderRadius: '4px',
                fontFamily: 'monospace',
              }}
            >
              {gsiConfigSample}
            </pre>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
              Положите этот файл в папку <code>game/csgo/cfg/</code> для автоматической отправки событий матча в сторонний HUD.
            </div>
          </div>
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Понятно, закрыть
          </button>
        </div>
      </div>
    </div>
  )
}

