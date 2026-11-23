"""
backend/services/strategy_exporter.py — Standalone Single-File Offline HTML Playbook Exporter.

Generates self-contained, offline HTML documents with embedded SVG radars,
complete CSS styling, print-to-PDF formatting, and interactive vanilla JS.
Zero external CDN dependencies.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from backend.storage.models import StrategyBookModel, TacticalSetupModel, UtilityLineupModel


def _render_setup_radar_svg(setup: TacticalSetupModel, map_name: str) -> str:
    """Render an inline SVG tactical map with tokens and drawings."""
    tokens = []
    drawings = []
    try:
        tokens = json.loads(setup.tokens_json or "[]")
    except Exception:
        pass
    try:
        drawings = json.loads(setup.drawings_json or "[]")
    except Exception:
        pass

    svg_parts = [
        '<svg viewBox="0 0 1000 1000" class="tactical-radar-svg">',
        '  <defs>',
        '    <linearGradient id="ctGrad" x1="0" y1="0" x2="1" y2="1">',
        '      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.6"/>',
        '      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0"/>',
        '    </linearGradient>',
        '    <linearGradient id="tGrad" x1="0" y1="0" x2="1" y2="1">',
        '      <stop offset="0%" stop-color="#fb923c" stop-opacity="0.6"/>',
        '      <stop offset="100%" stop-color="#fb923c" stop-opacity="0.0"/>',
        '    </linearGradient>',
        '    <filter id="radarGlow" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="3" result="blur" />',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over" />',
        '    </filter>',
        '  </defs>',
        '  <!-- Radar Base Blueprint Grid -->',
        '  <rect width="1000" height="1000" fill="#090d16" />',
        '  <path d="M 0 200 H 1000 M 0 400 H 1000 M 0 600 H 1000 M 0 800 H 1000 M 200 0 V 1000 M 400 0 V 1000 M 600 0 V 1000 M 800 0 V 1000" stroke="#161f30" stroke-width="1" />',
        '  <circle cx="500" cy="500" r="450" fill="none" stroke="#1a253a" stroke-width="2" />',
        '  <circle cx="500" cy="500" r="250" fill="none" stroke="#161f30" stroke-width="1" stroke-dasharray="4,4" />',
        f'  <text x="50" y="70" fill="#334155" font-size="28" font-weight="900" font-family="monospace">{map_name.upper()}</text>',
    ]

    # Draw Bombsites A & B outlines
    svg_parts.extend([
        '  <!-- Bombsite A outline -->',
        '  <rect x="680" y="220" width="160" height="140" fill="rgba(239, 68, 68, 0.08)" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="5,5" rx="8"/>',
        '  <text x="760" y="300" fill="#ef4444" font-size="32" font-weight="900" text-anchor="middle">A</text>',
        '  <!-- Bombsite B outline -->',
        '  <rect x="180" y="240" width="160" height="140" fill="rgba(239, 68, 68, 0.08)" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="5,5" rx="8"/>',
        '  <text x="260" y="320" fill="#ef4444" font-size="32" font-weight="900" text-anchor="middle">B</text>',
    ])

    # Render Drawings (smokes, arrows, zones, text)
    for d in drawings:
        dtype = d.get("layer_type", "")
        col = d.get("color", "#00f2fe")
        geom = {}
        try:
            geom = json.loads(d.get("geometry_json", "{}"))
        except Exception:
            pass

        if dtype == "arrow":
            x1, y1 = geom.get("x1", 0), geom.get("y1", 0)
            x2, y2 = geom.get("x2", 0), geom.get("y2", 0)
            svg_parts.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="4" stroke-linecap="round"/>')
            svg_parts.append(f'  <circle cx="{x2}" cy="{y2}" r="5" fill="{col}"/>')
        elif dtype == "circle":
            cx, cy = geom.get("cx", 0), geom.get("cy", 0)
            r = geom.get("r", 40)
            svg_parts.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" fill-opacity="0.25" stroke="{col}" stroke-width="2"/>')
        elif dtype == "box":
            x, y = geom.get("x", 0), geom.get("y", 0)
            w, h = geom.get("width", 50), geom.get("height", 50)
            svg_parts.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}" fill-opacity="0.2" stroke="{col}" stroke-width="2" rx="4"/>')
        elif dtype == "text" or d.get("text_label"):
            tx, ty = geom.get("x", 500), geom.get("y", 500)
            label = d.get("text_label") or "NOTE"
            svg_parts.append(f'  <text x="{tx}" y="{ty}" fill="{col}" font-size="14" font-weight="800" filter="url(#radarGlow)">{label}</text>')

    # Render Tokens (Players with team colors, role badge, vision cone)
    for tok in tokens:
        tx = tok.get("x", 500)
        ty = tok.get("y", 500)
        side = tok.get("side", setup.side).lower()
        role = tok.get("role", "Rifler")
        callout = tok.get("callout", "")
        col = "#38bdf8" if side == "ct" else "#fb923c"
        grad = "ctGrad" if side == "ct" else "tGrad"
        yaw = tok.get("yaw", 0)

        # Vision cone
        svg_parts.append(
            f'  <g transform="translate({tx}, {ty}) rotate({-yaw})">'
            f'    <path d="M 0 0 L 45 -45 A 64 64 0 0 1 45 45 Z" fill="url(#{grad})" stroke="{col}" stroke-width="0.8" opacity="0.85"/>'
            f'  </g>'
        )

        # Player token ring
        svg_parts.append(
            f'  <circle cx="{tx}" cy="{ty}" r="14" fill="#0f172a" stroke="{col}" stroke-width="3" filter="url(#radarGlow)"/>'
            f'  <circle cx="{tx}" cy="{ty}" r="10" fill="{col}"/>'
            f'  <text x="{tx}" y="{ty + 4}" fill="#000000" font-size="10" font-weight="900" text-anchor="middle">{side.upper()}</text>'
        )

        # Callout / Role label
        lbl = f"{role} • {callout}" if callout else role
        svg_parts.append(
            f'  <rect x="{tx - 50}" y="{ty + 18}" width="100" height="18" fill="rgba(11, 15, 23, 0.9)" stroke="{col}" stroke-width="1" rx="4"/>'
            f'  <text x="{tx}" y="{ty + 31}" fill="#f1f5f9" font-size="10" font-weight="800" text-anchor="middle">{lbl}</text>'
        )

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def export_strategy_book_to_html(book: StrategyBookModel) -> str:
    """Generate self-contained, standalone single-file HTML playbook."""
    setups = book.setups or []
    lineups = book.lineups or []

    # Filter CT and T setups
    ct_setups = [s for s in setups if s.side.lower() == "ct"]
    t_setups = [s for s in setups if s.side.lower() == "t"]

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{book.title} — Tactical Strategy Playbook</title>
  <style>
    /* ========================================================================== */
    /* STANDALONE EMBEDDED CSS (100% OFFLINE / DARK CYBERPUNK TOURNAMENT THEME)   */
    /* ========================================================================== */
    :root {{
      --bg-base: #06090e;
      --bg-surface: #0b1019;
      --bg-card: #0f1624;
      --border-color: #1a2538;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --cyan-accent: #00f2fe;
      --ct-blue: #38bdf8;
      --t-orange: #fb923c;
      --gold-accent: #facc15;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background-color: var(--bg-base);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.5;
      padding: 24px;
      -webkit-font-smoothing: antialiased;
    }}
    .playbook-container {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}
    header.playbook-header {{
      background: linear-gradient(135deg, #0b1019 0%, #111a2e 100%);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
    }}
    .header-badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
    }}
    .badge-map {{
      background-color: rgba(0, 242, 254, 0.15);
      border: 1px solid var(--cyan-accent);
      color: var(--cyan-accent);
    }}
    h1.playbook-title {{
      font-size: 26px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: -0.5px;
    }}
    p.playbook-desc {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .header-actions button {{
      background-color: var(--gold-accent);
      color: #000000;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s ease;
      box-shadow: 0 4px 14px rgba(250, 204, 21, 0.3);
    }}
    .header-actions button:hover {{
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(250, 204, 21, 0.5);
    }}
    .nav-tabs {{
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 8px;
    }}
    .tab-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .tab-btn.active {{
      background-color: var(--bg-card);
      border-color: var(--border-color);
      color: var(--cyan-accent);
    }}
    .tab-content {{
      display: none;
      flex-direction: column;
      gap: 20px;
    }}
    .tab-content.active {{
      display: flex;
    }}
    .setups-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(540px, 1fr));
      gap: 24px;
    }}
    .setup-card {{
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
      break-inside: avoid;
    }}
    .setup-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .side-badge {{
      font-size: 11px;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 4px;
    }}
    .badge-ct {{
      background-color: rgba(56, 189, 248, 0.15);
      color: var(--ct-blue);
      border: 1px solid var(--ct-blue);
    }}
    .badge-t {{
      background-color: rgba(251, 146, 60, 0.15);
      color: var(--t-orange);
      border: 1px solid var(--t-orange);
    }}
    .tactical-radar-svg {{
      width: 100%;
      height: auto;
      max-height: 480px;
      border-radius: 8px;
      border: 1px solid #162030;
      box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8);
    }}
    .lineups-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      background-color: var(--bg-surface);
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border-color);
    }}
    .lineups-table th, .lineups-table td {{
      padding: 10px 14px;
      text-align: left;
    }}
    .lineups-table th {{
      background-color: #111726;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-color);
      font-weight: 700;
    }}
    .lineups-table tr:not(:last-child) td {{
      border-bottom: 1px solid #141b2b;
    }}
    /* Print Stylesheet for PDF Generation */
    @media print {{
      body {{
        background: #ffffff !important;
        color: #000000 !important;
        padding: 0 !important;
      }}
      header.playbook-header {{
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 10px 0 !important;
      }}
      h1.playbook-title {{
        color: #000000 !important;
      }}
      .header-actions, .nav-tabs {{
        display: none !important;
      }}
      .tab-content {{
        display: flex !important;
      }}
      .setup-card {{
        page-break-after: always;
        border: 1px solid #cccccc !important;
        box-shadow: none !important;
        background: #ffffff !important;
      }}
      .tactical-radar-svg {{
        border: 1px solid #333333 !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="playbook-container">
    <!-- Playbook Header -->
    <header class="playbook-header">
      <div>
        <span class="header-badge badge-map">🗺️ {book.map_name.upper()} PLAYBOOK</span>
        <h1 class="playbook-title">{book.title}</h1>
        <p class="playbook-desc">{book.description or 'Official tactical protocols, site execute lineups and default setup playbook.'}</p>
      </div>
      <div class="header-actions">
        <button type="button" onclick="window.print()">
          <span>🖨️</span>
          <span>Печать в PDF / Сохранить</span>
        </button>
      </div>
    </header>

    <!-- Navigation Tabs -->
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="openTab('tab-setups')">📋 Тактические сетапы ({len(setups)})</button>
      <button class="tab-btn" onclick="openTab('tab-lineups')">🎯 Арсенал раскидок ({len(lineups)})</button>
      <button class="tab-btn" onclick="openTab('tab-protocols')">📖 11 Протоколов команды</button>
    </div>

    <!-- Tab 1: Tactical Setups -->
    <div id="tab-setups" class="tab-content active">
      <div class="setups-grid">
"""

    if not setups:
        html += """
        <div style="grid-column: 1 / -1; padding: 40px; text-align: center; color: var(--text-muted); background: var(--bg-surface); border-radius: 8px;">
          Сетапы ещё не добавлены. Создайте схемы расстановки игроков в конструкторе dem.Toshka Strategy Book.
        </div>
        """
    else:
        for s in setups:
            side_cls = "badge-ct" if s.side.lower() == "ct" else "badge-t"
            svg_radar = _render_setup_radar_svg(s, book.map_name)
            html += f"""
        <div class="setup-card">
          <div class="setup-header">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="side-badge {side_cls}">{s.side.upper()}</span>
              <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Фаза: {s.phase}</span>
            </div>
            <h3 style="font-size: 15px; font-weight: 800; color: #ffffff;">{s.title}</h3>
          </div>
          {svg_radar}
          {f'<p style="font-size: 12px; color: var(--text-muted);">{s.description}</p>' if s.description else ''}
        </div>
            """

    html += f"""
      </div>
    </div>

    <!-- Tab 2: Utility Lineups -->
    <div id="tab-lineups" class="tab-content">
      <table class="lineups-table">
        <thead>
          <tr>
            <th>Сторона</th>
            <th>Тип гранаты</th>
            <th>Название раскидки</th>
            <th>Тип броска</th>
            <th>Координаты броска ➔ цели</th>
            <th>Ориентир прицела</th>
          </tr>
        </thead>
        <tbody>
    """

    if not lineups:
        html += """
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">
              Раскидки не занесены. Добавьте смоки, флешки и молотовы в Utility Book.
            </td>
          </tr>
        """
    else:
        for l in lineups:
            side_cls = "badge-ct" if l.side.lower() == "ct" else "badge-t"
            html += f"""
          <tr>
            <td><span class="side-badge {side_cls}">{l.side.upper()}</span></td>
            <td style="font-weight: 700;">{l.utility_type.upper()}</td>
            <td style="font-weight: 800; color: #ffffff;">{l.title}</td>
            <td>{l.throw_type}</td>
            <td style="font-family: monospace; color: var(--text-muted);">({l.pos_x:.0f}, {l.pos_y:.0f}) ➔ ({l.target_x:.0f}, {l.target_y:.0f})</td>
            <td style="color: var(--text-muted);">{l.crosshair_desc or '—'}</td>
          </tr>
            """

    html += """
        </tbody>
      </table>
    </div>

    <!-- Tab 3: 11 Playbook Protocols -->
    <div id="tab-protocols" class="tab-content">
      <div style="display: flex; flex-direction: column; gap: 14px;">
        <div class="setup-card">
          <h3 style="color: var(--cyan-accent); font-size: 15px;">1. Default Map Control (Базовый дефолт)</h3>
          <p style="font-size: 13px; color: var(--text-muted);">
            Контроль ключевых зон карты без спешки. Распределение 3-1-1 или 2-1-2 в зависимости от активных сетапов соперника.
          </p>
        </div>
        <div class="setup-card">
          <h3 style="color: var(--cyan-accent); font-size: 15px;">2. Exec Protocols (Синхронные выходы)</h3>
          <p style="font-size: 13px; color: var(--text-muted);">
            Тайминг одновременного падения гранат (0:52 / 0:38). Первый контакт открывает энтри с поддержкой моментальных флешек.
          </p>
        </div>
        <div class="setup-card">
          <h3 style="color: var(--cyan-accent); font-size: 15px;">3. Post-Plant Formations (Удержание плента)</h3>
          <p style="font-size: 13px; color: var(--text-muted);">
            Отказ от открытых дуэлей в большинстве. Занятие взаимно прикрывающих кроссфайров и игра на затягивание времени дефьюза.
          </p>
        </div>
        <div class="setup-card">
          <h3 style="color: var(--cyan-accent); font-size: 15px;">4. Retake Protocols (Скоординированный ретейк)</h3>
          <p style="font-size: 13px; color: var(--text-muted);">
            Ожидание полного сбора тиммейтов. Заход строго в 2–3 направления одновременно под отбрасываемые ретейк-флешки.
          </p>
        </div>
      </div>
    </div>
  </div>

  <script>
    function openTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      event.target.classList.add('active');
    }
  </script>
</body>
</html>
"""
    return html
