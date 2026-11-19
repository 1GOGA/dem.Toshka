# Журнал изменений (Changelog) — dem.Toshka Overhaul

Все значимые изменения в проекте документируются в данном файле.

---

## [0.4.0-takeover] — 2026-11-19

### Добавлено (Added)
- **Пакет `backend/hlae/`**:
  - `HLAEVersionDetector`: PE-инспекция бинарников HLAE и AfxHookSource2 с верификацией совместимости CS2.
  - `HLAECommandBuilder`: типизированный генератор скриптов с поддержкой тикового планирования `mirv_cmd addAtTick`, настройкой чистого HUD и привязкой спектатора.
  - `HLAECampathManager`: модуль сплайновой интерполяции Catmull-Rom $C^1$, вычисление углов наведения `calculate_look_at`, генераторы кругового облета (Orbit) и пролета (Flyby), экспорт и импорт XML `mirv_campath`.
  - `HLAEStreamManager`: профили потоков `Clean Cinematic`, `Broadcast Esports`, `VFX Multi-Pass` с экранированием `{{ ... }}` для AfxHookSource2 0.42.0+.
  - `HLAEController`: супервизор процессов HLAE/CS2 с мониторингом таймаутов и безопасным завершением процессов.
- **Унифицированный парсер демок (`backend/parser/`)**:
  - `DemoParserInterface`: абстрактный контракт для сменных движков парсинга.
  - `AwpyDemoParser`: реализация адаптера для библиотеки Awpy 2.0.2.
  - `EventNormalizer`: фильтрация падений `world`, суицидов, тимкиллов, очистка названий оружия.
  - `TickIndex`: быстрый бинарный поиск раундов и киллов по тикам за время $O(\log N)$.
  - `radar_percent_to_world`: обратный пересчет процентов радара в трехмерные мировые координаты CS2.
- **Кинематографический движок камер (`backend/cinematic/camera_engine.py`)**:
  - Поддержка 12 режимов съемки (POV, Victim, Third-Person, Chase, Free, Orbit, Shoulder, Follow Target, Fixed, Flyby, Top-Down, Custom Spline).
- **Объяснимый скоринг хайлайтов (`backend/detector/highlight_scorer.py`)**:
  - `SmartHighlightScorer`: расчет составного рейтинга зрелищности (ACE, 4K, 3K, хедшоты, волбанги, ноускопы, прострелы через дым, престиж оружия, темп, 1vX клатчи) с детализацией факторов и значками.
- **Исследования и архитектурная документация**:
  - `docs/audit/BASELINE_AUDIT.md`: аудит базового состояния проекта.
  - `docs/research/COMPETITIVE_LANDSCAPE.md`: сравнительный анализ 10 решений на рынке.
  - `docs/research/FEATURE_TAKEOVER_MATRIX.md`: матрица захвата 11 ключевых возможностей.
  - `docs/architecture/ARCHITECTURE_REVIEW.md`: целевая архитектура с диаграммой Mermaid.
  - `docs/architecture/DECISIONS.md`: архитектурные решения ADR-011 – ADR-015.
  - `docs/compatibility/CS2_COMPATIBILITY_MATRIX.md`: матрица совместимости билдов CS2 и тулинга.
  - `docs/qa/REGRESSION_TEST_PLAN.md` и `docs/qa/TEST_RESULTS.md`: план регрессионного тестирования и отчет о 348 успешных тестах.

### Изменено (Changed)
- `backend/render/cfg_backup.py`: добавлена автоматическая разблокировка атрибута "Read-Only" для пользовательских файлов конфигурации в папках Steam userdata, исключена блокировка системного файла видео `cs2_video.txt`.
- Расширен перечень перечислений `CameraType` в `backend/cinematic/models.py`.

### Исправлено (Fixed)
- Предотвращен сброс настроек клавиатуры и мыши CS2 при перезапуске игры после записи хайлайтов.
- Исключены ошибки генерации путей `mirv_campath` с нулевыми отступами в узких коридорах.
