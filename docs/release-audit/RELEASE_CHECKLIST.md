# Чек-лист перед публичным релизом dem.Toshka (RELEASE_CHECKLIST.md)

**Текущий статус релиза:** 🛑 **BLOCKED (Требуется устранение P0/P1 блокеров)**

---

## 1. Блокирующие исправления до сборки Release Candidate (P0/P1 Gates)

- [ ] **1. Защита пользовательских видеофайлов в деинсталляторе (P0):**
  - [ ] В `packaging/installer.iss` убрать удаление папок `{app}\renders` и `{app}\demos` из секции `[UninstallDelete]`.
  - [ ] Заменить безусловный `DelTree(AppDir, True, True, True)` на выборочное удаление только системных папок (`_internal`, `assets`) и бинарников, либо запрашивать подтверждение через `MsgBox`.
  - [ ] Убрать принудительный `taskkill /IM cs2.exe` при деинсталляции.
- [ ] **2. Защита сетевого контура API от CSRF (P1):**
  - [ ] В `backend/api/main.py` заменить `allow_origins=["*"]` на локальный белый список: `["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000"]`.
- [ ] **3. Санитизация никнеймов игроков от Console Injection (P1):**
  - [ ] В `backend/render/cfg_generator.py` удалять символы `\r` и `\n` из имен игроков при генерации `.cfg` команд CS2.
- [ ] **4. Исправление окон хайлайтов для 64-тиковых CS2 Premier демок (P1):**
  - [ ] В `backend/detector/models.py` и `backend/api/services.py` передавать `tickrate` и вычислять окно как `int(seconds * tickrate)`.
- [ ] **5. Устранение утечки памяти в кэше 2D реплея (P1):**
  - [ ] В `backend/parser/replay.py` ограничить `_DEMO_OBJ_CACHE` размером 1–2 объекта через `OrderedDict` или удалять экземпляр `Demo` после экстракции данных раунда.
- [ ] **6. Изоляция E2E рендер-тестов от автоматического запуска (P1):**
  - [ ] В `tests/integration/test_single_cs2_batch_render.py` и `test_render_e2e.py` требовать флаг `RUN_REAL_CS2_TESTS=1`.
- [ ] **7. Синхронизация версий приложения (P1):**
  - [ ] Зафиксировать версию `0.1.0-beta` в `frontend/package.json`.
  - [ ] Скорректировать публичные бейджи и ссылки в `README.md` с `v1.0` на `Setup-dem.Toshka-v0.1.0-beta.exe`.
- [ ] **8. Устранение интерактивности заблокированных кнопок (P1):**
  - [ ] В `frontend/src/index.css` добавить правило `.card-interactive:hover:not(:disabled)` и `.btn:disabled { pointer-events: none; opacity: 0.45; }`.
- [ ] **9. Закрытие модальных окон по Escape (P1):**
  - [ ] Добавить перехват клавиши `Escape` в `ClipSettingsModal`, `PlayerAnalyticsModal`, `RenderQueueModal`, `TournamentHudModal`.

---

## 2. Действия после устранения блокеров (Release Verification)

- [ ] **1. Запуск полного набора юнит-тестов бэкенда:**
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/unit -v
  ```
  *(Критерий приёмки: 235 passed, 0 failed).*
- [ ] **2. Запуск интеграционных тестов парсера:**
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/integration/test_storage_real_demo.py tests/integration/test_detector_real_demo.py tests/integration/test_real_demo.py
  ```
  *(Критерий приёмки: 40 passed, 0 failed).*
- [ ] **3. Компиляция production-бандла фронтенда:**
  ```powershell
  cmd.exe /c "npm --prefix frontend run build"
  ```
  *(Критерий приёмки: 0 ошибок TypeScript, создан каталог frontend/dist).*
- [ ] **4. Синхронизация фронтенда с PyInstaller-бандлом:**
  ```powershell
  Copy-Item -Path 'frontend/dist/*' -Destination 'dist/dem.Toshka/_internal/frontend/dist' -Recurse -Force
  ```
- [ ] **5. Сборка финального установщика Inno Setup:**
  ```powershell
  & "C:\Users\pyPypy\AppData\Local\Programs\Inno Setup 6\ISCC.exe" packaging\installer.iss
  ```
  *(Критерий приёмки: создан dist-installer/Setup-dem.Toshka-v0.1.0-beta.exe, размер ~224 МБ).*
- [ ] **6. Тест чистой установки и деинсталляции на виртуальной машине / тестовом профиле:**
  - Установка без прав администратора в `%LOCALAPPDATA%\dem.Toshka`.
  - Запуск, импорт демки, рендеринг клипа.
  - Деинсталляция: подтвердить, что созданный MP4 файл в папке пользователя **НЕ удален**.

---

## 3. Критерии перехода в статус SHIP

1. Все P0 и P1 дефекты закрыты и покрыты тестами против регрессий.
2. Инсталлятор не удаляет пользовательские файлы при удалении программы.
3. Промо-материалы трейлера согласованы с **Green List** (никаких ложных упоминаний "HLTV Rating" или "BLAST HUD").
4. Версия везде указана как **`v0.1.0-beta`**.

