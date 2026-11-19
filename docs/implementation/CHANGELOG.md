# Журнал изменений dem.Toshka (Changelog)

Все заметные изменения основного приложения dem.Toshka документируются в этом файле.

---

## [Unreleased / Phase 0 Overhaul] — 2026-11-19

### Добавлено (Added)
- **Комплексная архитектурная документация и аудит (в `docs/`):**
  - `docs/audit/BASELINE_AUDIT.md`: Полный базовый аудит кодовой базы основного приложения с инвентаризацией компонентов, анализом техдолга и производительности.
  - `docs/research/COMPETITIVE_LANDSCAPE.md`: Анализ конкурентов (Scope.gg, Leetify, CS Demo Manager, awpy, demoparser2, demoinfocs-golang) по 10 обязательным критериям.
  - `docs/research/FEATURE_TAKEOVER_MATRIX.md`: Матрица приобретения функций категорий A (Must Have), B (Advantage), C (Differentiators).
  - `docs/research/COMPETITOR_UX_ANALYSIS.md`: Анализ дизайн-системы, визуальной иерархии и эргономики темной темы.
  - `docs/architecture/ARCHITECTURE_REVIEW.md`: Полный системный обзор архитектуры основного приложения.
  - `docs/architecture/DATA_MODEL.md`: Спецификация схемы данных SQLite и ER-диаграмма сущностей.
  - `docs/architecture/DECISIONS.md`: Реестр архитектурных решений (ADR-001 .. ADR-006).
  - `docs/compatibility/CORE_COMPATIBILITY_MATRIX.md`: Матрица совместимости с версиями CS2 и картами.
  - `docs/integration/CINEMATIC_STUDIO_CONTRACT.md`: Контракт манифеста `StudioJobManifest` v1.0 для взаимодействия с Cinematic Studio.
  - `docs/qa/REGRESSION_TEST_PLAN.md`: Протокол тестирования компонентов.
  - `docs/qa/TEST_RESULTS.md`: Фактический отчет о прохождении 351 unit-теста и сборки фронтенда.
  - `docs/implementation/IMPLEMENTATION_REPORT.md`: Сводный отчет о реализации.
- **Интеграционный слой Cinematic Studio Bridge:**
  - `backend/integration/studio_bridge.py`:
    - Модели данных `StudioJobManifest`, `DemoMetadataManifest`, `ClipSpecificationManifest`, `EventItemManifest`, `ProductionRequestManifest`.
    - Сервис `StudioAvailabilityDetector` для безопасного определения наличия установленного расширения студии.
    - Сервис `StudioJobLauncher` для отправки заданий в очередь `manifests/jobs/`.
    - Сервис `StudioJobStatusProvider` для отслеживания хода рендера.
    - Генератор описаний публикаций `SocialPostDraftGenerator` для Telegram, YouTube Shorts и TikTok.
  - `backend/integration/__init__.py`: Публичный интерфейс интеграционного слоя.
- **API Эндпоинты:**
  - `GET /api/studio/status`: Проверка доступности Cinematic Studio и поддерживаемых профилей.
  - `POST /api/studio/jobs`: Формирование и отправка `StudioJobManifest` v1.0 по ID демки и хайлайта.
  - `GET /api/studio/jobs/{job_id}`: Проверка статуса выполнения задания рендера.
  - `POST /api/social-drafts`: Генерация готовых текстов постов для соцсетей.
- **Интерфейс пользователя (Frontend UI):**
  - `frontend/src/components/SocialDraftModal.tsx`: Интерактивное модальное окно генерации описаний для Telegram, YouTube Shorts и TikTok со счётчиком символов и копированием в буфер.
  - `frontend/src/components/HighlightsStudioView.tsx`:
    - Кнопка **«📱 Пост»** для мгновенной генерации анонса хайлайта в соцсети.
    - Кнопка **«🎬 В Studio»** для прямой отправки клип-заявки `StudioJobManifest` v1.0.0 в Cinematic Studio с индикатором статуса и уведомлением.
    - Интерактивный бейдж рейтинга зрелищности (`⭐ <Score>`) с подсказкой факторов скоринга.
  - `frontend/src/components/Header.tsx`: Индикатор доступности Cinematic Studio (`🎬 Studio ON` / `Standalone`).
  - `frontend/src/api.ts`: Клиентские методы `getStudioStatus`, `createStudioJob`, `getStudioJobStatus`, `createSocialDraft`.
- **Тестовый пакет:**
  - `tests/unit/test_studio_bridge.py`: 4 юнит-теста сериализации, очереди и генерации текстов.
  - `tests/unit/test_api_studio.py`: 3 юнит-теста эндпоинтов статуса студии, создания заданий и черновиков постов.

### Изменено (Changed)
- `backend/api/schemas.py`: Добавлены DTO-классы `StudioStatusResponse`, `CreateStudioJobRequest`, `StudioJobResponse`, `SocialDraftRequest`, `SocialDraftResponse`.
- `backend/api/main.py`: Подключены новые эндпоинты управления манифестами заданий и генератора контента.

### Исправлено (Fixed)
- Разделены контексты основного приложения dem.Toshka и отдельного модуля Cinematic Studio: основное приложение не загружает зависимости HLAE и не требует их для анализа матчей.
- Устранена путаница между полями `tags` и `tags_json` при формировании спецификаций клипов.
