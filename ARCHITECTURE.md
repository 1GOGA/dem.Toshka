# Архитектура CS2 Highlights Studio

## Цель
Локальное приложение для ручного импорта `.dem`, анализа матча, обнаружения и сохранения хайлайтов, ручного выбора моментов и последующего рендера POV-видео. Steam/FACEIT login не входит в MVP.

## Пользовательский сценарий
1. Перетащить `.dem` или выбрать файл.
2. Проверить файл и запустить парсер.
3. Выбрать своего игрока по SteamID/имени, если автоматическое определение неоднозначно.
4. Просмотреть сводку, раунды и события.
5. Выбрать автоматические кандидаты: мультикиллы, эйсы, clutch-кандидаты и подтверждённые специальные события.
6. Настроить границы, POV и поддерживаемые визуальные параметры.
7. Отрендерить клипы и объединить через FFmpeg.
8. Сохранить MP4 и повторно открыть матч без нового парсинга, если исходник и версия схемы совпадают.

## Предварительный стек
- Frontend: React + TypeScript + Vite, тёмный desktop-first UI.
- Backend: Python; FastAPI только если выбранной интеграции действительно нужен HTTP API.
- Parser: выбрать после сравнительного теста актуальных Awpy и demoinfocs-golang.
- Storage: SQLite для матчей, событий, хайлайтов, настроек и render jobs.
- Video: FFmpeg для сборки/перекодирования; захват игрового изображения — отдельный адаптер.
- Desktop packaging: отложить до стабильного MVP; затем оценить Tauri/Electron.

## Модули
### Demo ingestion
Проверяет расширение, существование, доступность и размер файла; вычисляет fingerprint; никогда не меняет и не удаляет исходник.

### Parser
Извлекает доступные метаданные, игроков, раунды, счёт, убийства, смерти, ассисты, оружие, headshot/wallbang, урон и гранаты — только если библиотека действительно предоставляет эти данные. Неизвестные поля остаются null/unknown.

### Player identity
Стабильный идентификатор хранится отдельно от отображаемого имени. Если пользователь не выбран, не угадывать молча — показать список игроков.

### Highlight detector
Типы: kill, double/triple/4K/ace, clutch-кандидат, а также headshot/wallbang/no-scope/grenade kill, если данные подтверждены. Границы pre-roll/post-roll настраиваются. Хранить раунд, ticks, время (если корректно доступно), POV-кандидата, ID исходных событий и причину детектирования. Не объединять события через границу раунда.

### Match analytics
Базовые показатели: K/D/A, убийства по раундам, HS count/%, распределение оружия, ADR только при корректных данных урона. Формулы документировать. Не выдавать самодельный показатель за HLTV Rating.

### Local persistence
SQLite хранит fingerprint демки, версии парсера/схемы, игроков, раунды, события, хайлайты, пользовательские настройки, задачи рендера и пути к результатам. Не копировать бинарную демку в БД без необходимости.

### UI
Library, Match Overview, Highlights Studio, Clip Settings, Render Queue, Settings. Реальные данные из backend; mock-данные разрешены только в явном dev-режиме. Фильтры не должны сбрасывать выбор. Неподдерживаемые переключатели disabled с пояснением.

### Render engine
Стадии: validate → prepare → playback/capture → verify source → encode → verify output → complete. Проверять доступность CS2, демки, инструмента захвата и FFmpeg. Записывать логи и exit code. При сбое рендера анализ матча продолжает работать.

## Важные ограничения
- Парсинг событий не означает, что видеорендер готов.
- Не предполагать поддержку headless-рендера или команд CS2 без проверки текущей версии.
- POV соперника, X-Ray, HUD и voice проверять независимо.
- Голос нельзя восстановить, если его нет в исходной демке.
- Сначала доказать один короткий клип, затем делать batch render.

## Модель данных
`Demo`: id, source_path, fingerprint, map_name, duration, parse_status, parser_version.  
`Player`: stable_id, steam_id_nullable, name, team, player_slot_nullable.  
`Round`: round_number, start_tick, end_tick, winner, score_metadata.  
`Event`: id, tick, time_seconds_nullable, round_number, event_type, actor_id_nullable, target_id_nullable, weapon_nullable, payload_json.  
`Highlight`: id, demo_id, type, round_number, start_tick, end_tick, pov_player_id_nullable, event_ids, selected, detection_source.  
`RenderJob`: id, highlight_ids, settings_json, status, progress, output_path, error_summary, log_path, timestamps.

## Этапы
A. Аудит среды и парсеров.  
B. CLI-парсер и JSON.  
C. Тесты на реальных демках.  
D. Highlight detector.  
E. SQLite и статистика.  
F. UI и выбор моментов.  
G. Proof-of-concept одного рендера.  
H. FFmpeg и проверка MP4.  
I. Очередь пакетного рендера.  
J. Упаковка desktop-приложения.
