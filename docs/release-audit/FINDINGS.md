# Полный реестр находок аудита dem.Toshka (FINDINGS.md)

Каждая находка подтверждена анализом реального исходного кода, воспроизводимым сценарием и независимой проверкой аудиторов.

---

## 1. P0 / BLOCKER (Критические дефекты)

### [P0-INST-01] Деструктивное удаление пользовательских видео и демок деинсталлятором
- **Приоритет:** P0 / BLOCKER
- **Уверенность:** Высокая (100%)
- **Файл:** [`packaging/installer.iss:61-65, 89-91`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/packaging/installer.iss#L61-L65)
- **Предусловия:** Пользователь установил приложение через `Setup-dem.Toshka-v0.1.0-beta.exe`, загрузил демки в `demos/` и отрендерил клипы в `renders/`.
- **Шаги воспроизведения:**
  1. Запустить стандартную деинсталляцию приложения через «Установка и удаление программ» Windows.
  2. Процедура деинсталляции запускает код:
     ```pascal
     [UninstallDelete]
     Type: filesandordirs; Name: "{app}\demos"
     Type: filesandordirs; Name: "{app}\renders"
     ...
     procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
     begin
       if CurUninstallStep = usPostUninstall then
         DelTree(AppDir, True, True, True);
     end;
     ```
- **Ожидалось:** Пользовательские медиафайлы (`renders/`, `demos/`) остаются нетронутыми, либо инсталлятор явно спрашивает: *"Желаете сохранить созданные видеоролики и демки?"*.
- **Фактический результат:** Папки `renders/` и `demos/` принудительно и безвозвратно удаляются с диска. Часы отрендеренных видеороликов стираются без подтверждения.
- **Impact:** Катастрофическая потеря пользовательских данных. Прямое нарушение правила `AGENTS.md` (*"Исходные демки и готовые ролики не удалять автоматически"*).
- **Исправление:** 
  1. Исключить `{app}\demos` и `{app}\renders` из секции `[UninstallDelete]`.
  2. В `DelTree` не передавать корень приложения, если там содержатся пользовательские данные, либо перемещать готовые рендеры в стандартную системную папку пользователя `Videos/dem.Toshka/` или запрашивать диалог `MsgBox(..., mbConfirmation)`.
  3. Убрать `taskkill.exe /F /IM cs2.exe` на строке 75, чтобы не убивать игру пользователя при деинсталляции.

---

## 2. P1 / HIGH (Высокий приоритет)

### [P1-SEC-01] CORS Wildcard (`allow_origins=["*"]`) на локальном демоне (Drive-By Exploit)
- **Приоритет:** P1 / HIGH
- **Уверенность:** Высокая
- **Файл:** [`backend/api/main.py:95-101`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/backend/api/main.py#L95-L101)
- **Доказательство:**
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Шаги воспроизведения:** Пользователь запускает dem.Toshka на `http://127.0.0.1:8000` и параллельно открывает в браузере любой сторонний веб-сайт. Веб-сайт через фоновый `fetch('http://127.0.0.1:8000/api/renders/cleanup-all-clips', {method: 'POST'})` может без ограничений отправлять команды локальному API.
- **Impact:** Удаление пользовательских роликов, несанкционированный запуск внешних процессов (CS2/HLAE), смена директорий хранения через CSRF.
- **Исправление:** Заменить `allow_origins=["*"]` на строгий белый список доверенных локальных адресов:
  ```python
  allow_origins=[
      "http://127.0.0.1:5173",
      "http://localhost:5173",
      "http://127.0.0.1:8000",
      "http://localhost:8000",
  ]
  ```

---

### [P1-SEC-02] Source 2 Console Command Injection через перенос строки в никнейме
- **Приоритет:** P1 / HIGH
- **Уверенность:** Высокая
- **Файл:** [`backend/render/cfg_generator.py:130-134`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/backend/render/cfg_generator.py#L130-L134)
- **Доказательство:**
  ```python
  safe_name = pov_name.replace('"', "").replace(";", "").strip()
  ```
- **Шаги воспроизведения:** В CS2 console `.cfg` файлах символы переноса строки `\r` и `\n` являются разделителями команд. Если игрок в демке имеет никнейм `hacker\nquit\n` или `player\nexec evil.cfg\n`, сгенерированный CFG разрывает строку `mirv_exec spec_player "..."` и выполняет внедренную команду движка.
- **Impact:** Срыв записи, принудительное завершение игры, выполнение посторонних консольных команд CS2.
- **Исправление:** Очищать символы переноса строк:
  ```python
  safe_name = re.sub(r'[\r\n";]+', '', pov_name).strip()
  ```

---

### [P1-QA-01] Искажение окон хайлайтов на 64-тиковых демках CS2 (удвоение времени)
- **Приоритет:** P1 / HIGH
- **Уверенность:** Высокая
- **Файл:** [`backend/detector/models.py:38-48`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/backend/detector/models.py#L38-L48), [`backend/api/services.py:56-57`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/backend/api/services.py#L56-L57)
- **Доказательство:**
  ```python
  multikill_window_ticks: int = 128 * 15   # 1920 тиков
  max_kill_gap_ticks: int = 128 * 4        # 512 тиков
  pre_roll_ticks: int = 128 * 7            # 896 тиков
  ```
- **Шаги воспроизведения:** Загрузить официальную демку CS2 Premier (тикрейт 64). В `services.py` вызывается `detect_highlights(parsed)` без параметров.
- **Ожидалось:** Окно мультикилла 15 секунд (960 тиков при 64 fps), пре-ролл 7 секунд (448 тиков).
- **Фактический результат:** 1920 тиков на 64-тиковой демке длятся **30 секунд**, а пре-ролл — **14 секунд**. Детектор объединяет несвязанные фраги с огромными паузами в мультикиллы, а клипы получаются в 2 раза длиннее нужного.
- **Исправление:** Передавать `tickrate` демки и рассчитывать тики динамически: `int(seconds * tickrate)`.

---

### [P1-QA-02] Утечка оперативной памяти в кэше 2D Реплея (`_DEMO_OBJ_CACHE`)
- **Приоритет:** P1 / HIGH
- **Уверенность:** Высокая
- **Файл:** [`backend/parser/replay.py:124-125, 187-193`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/backend/parser/replay.py#L124-L125)
- **Доказательство:**
  ```python
  _DEMO_OBJ_CACHE[demo_key] = dem  # Неограниченный глобальный dict
  ```
- **Шаги воспроизведения:** Последовательно открыть 2D-реплей для 5–10 разных матчей.
- **Фактический результат:** Каждый объект `awpy.Demo` с Polars-таблицами весит 250MB–1.2GB. Словарь никогда не очищается, память процесса разрастается до 4–6 ГБ, вызывая `MemoryError` или падение ОС на слабых машинах.
- **Исправление:** Ограничить кэш до `OrderedDict` с размером 1–2 элемента либо очищать `_DEMO_OBJ_CACHE` сразу после генерации фреймов раунда в `_REPLAY_DATA_CACHE`.

---

### [P1-QA-03] Запуск реального `cs2.exe` и зависание в тестах интеграции
- **Приоритет:** P1 / HIGH
- **Уверенность:** Высокая
- **Файл:** [`tests/integration/test_single_cs2_batch_render.py:30-39`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/tests/integration/test_single_cs2_batch_render.py#L30-L39), [`tests/integration/test_render_e2e.py:41-50`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/tests/integration/test_render_e2e.py#L41-L50)
- **Шаги воспроизведения:** Запустить `pytest` или `pytest tests/integration/` на машине с установленной CS2. Тест проверяет только `DEFAULT_CS2_EXE.exists()`. Так как игра установлена, он стартует реальный процесс `cs2.exe`, пытается подключиться к Steam и зависает в цикле на 240–300 секунд.
- **Исправление:** Добавить проверку флага `os.getenv("RUN_REAL_CS2_TESTS") == "1"` и проверку запущенного процесса Steam. По умолчанию интеграционные CS2-тесты должны быть исключены из стандартного набора.

---

### [P1-UI-01] Заблокированные кнопки (Disabled) анимируются и светятся как активные
- **Приоритет:** P1 / HIGH
- **Уверенность:** Высокая
- **Файл:** [`frontend/src/index.css:638-644`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/frontend/src/index.css#L638-L644), [`HighlightsStudioView.tsx:3014`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/frontend/src/components/HighlightsStudioView.tsx#L3014)
- **Доказательство:** В CSS селектор `.card-interactive:hover` не содержит фильтра `:not(:disabled)`. Кнопка «Создать нарезку» при 0 выбранных клипов имеет атрибут `disabled`, но при наведении мыши поднимается на `translateY(-2px)`, светится неоновой рамкой и меняет фон.
- **Impact:** Пользователь кликает на кнопку, думая, что она активна, но ничего не происходит.
- **Исправление:** Добавить в `index.css`: `.card-interactive:hover:not(:disabled) { ... }` и `.btn:disabled { opacity: 0.45; cursor: not-allowed !important; pointer-events: none; }`.

---

### [P1-UI-02] Игнорирование клавиши `Escape` в 4 из 5 модальных окон
- **Приоритет:** P1 / HIGH
- **Уверенность:** Высокая
- **Файл:** [`ClipSettingsModal.tsx`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/frontend/src/components/ClipSettingsModal.tsx), [`PlayerAnalyticsModal.tsx`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/frontend/src/components/PlayerAnalyticsModal.tsx), [`RenderQueueModal.tsx`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/frontend/src/components/RenderQueueModal.tsx), [`TournamentHudModal.tsx`](file:///c:/Users/pyPypy/Documents/MySCOPE/demToshka/frontend/src/components/TournamentHudModal.tsx)
- **Доказательство:** Обработчик нажатия клавиши `Escape` (`keydown`) реализован только в `VideoPlayerModal.tsx`. В окнах настроек, очереди рендера и аналитики нажатие Esc не закрывает модалку.
- **Исправление:** Добавить перехват `Escape` и вызов `onClose` во все модальные компоненты.

---

## 3. P2 / MEDIUM (Средний приоритет)

- **[P2-SEC-03] Смена `output_directory` без валидации пути:** `backend/render/storage_manager.py:42-61`. Принимает любой абсолютный путь, создавая риск удаления файлов при очистке.
- **[P2-REL-01] Ошибка 403 Forbidden при кастомной папке рендера:** `backend/api/main.py:649-662`. Эндпоинты стриминга клипов жестко привязаны к `renders_dir = pathlib.Path("renders")` и ломают просмотр клипов, если пользователь сменил папку сохранения.
- **[P2-REL-02] Завершение всех процессов CS2 через `taskkill /IM cs2.exe`:** `backend/render/engine.py:174, 206`. Убивает игру пользователя вместо завершения конкретного дочернего PID.
- **[P2-REL-04] Зависание цикла рендера на 5 минут при ошибке старта CS2:** `backend/render/engine.py:151-165`. Если CS2 не запустился, цикл опрашивает `tasklist` все 300 секунд.
- **[P2-REL-05] Отсутствие `PRAGMA busy_timeout` в SQLite:** `backend/storage/database.py:31-38`. В WAL-режиме при параллельной записи возможна ошибка `database is locked`.
- **[P2-UI-03] Переключатель языка `z-index: 999` просвечивает поверх модальных окон:** `LanguageSwitcher.tsx:15` vs `.modal-overlay { z-index: 200 }`.
- **[P2-UI-04] Дублирующиеся стили кнопок в `index.css`:** Фиолетовый градиент на строках 426-440 переопределяет брендовый Cyan на строке 219.
- **[P2-UI-05] Позиционирование фишек радара через Layout Reflow (`left/top`):** `TacticalReplayRadar.tsx:869`. Заменить на `transform: translate3d(x, y, 0)`.
- **[P2-UI-06] Монолитный бандл фронтенда (618 kB):** Отсутствие `React.lazy()` для тяжелых вкладок Студии и Аналитики.

---

## 4. P3 / LOW (Косметика и полировка)

- **[P3-UI-01] Ошибочный цветовой токен:** `index.css:14` (`--accent-gold: #38bdf8;` вместо янтарного `#f59e0b`).
- **[P3-UI-02] Дробный размер шрифта `font-size: 14.5px`:** `index.css:41`. Субпиксельное размытие на 1080p мониторах со 100% DPI.
- **[P3-UI-03] Пустая таблица без плейсхолдера:** `HighlightsStudioView.tsx:706-735`. При 0 матчей рендерится пустой `<tbody>` без поясняющей плашки.
- **[P3-UI-04] Дефолтный тикрейт 128 во фронтенде:** `frontend/src/App.tsx:277`. Заменить на 64 (стандарт CS2 Subtick).

