# Контракт интеграции с Cinematic Studio (Cinematic Studio Integration Contract)

**Версия спецификации:** 1.0.0  
**Дата:** 19 ноября 2026 г.  
**Ветка:** `feature/product-takeover-overhaul`  
**Статус:** Утверждённый межпрограммный интерфейс (IPC / File-Based Manifest Protocol)

---

## 1. Назначение и принципы интеграции

**dem.Toshka** является центральным аналитическим приложением для обнаружения матчевой информации, расчета статистики и выявления ярких моментов.

**dem.Toshka Cinematic Studio** — отдельное опциональное расширение, отвечающее за работу с HLAE, 3D сплайн-камерами (`mirv_campath`), кинематографическими проходами и видеомонтажом.

### Ключевые требования:
1. **Опциональность:** Основное приложение dem.Toshka обязано полноценно функционировать даже в случае полного отсутствия Cinematic Studio.
2. **Версионированный контракт:** Взаимодействие осуществляется через строго валидируемые JSON-манифесты `StudioJobManifest` v1.0.
3. **Двусторонняя связь:**
   - dem.Toshka формирует задание на рендер клипа и сохраняет манифест в каталоге заданий.
   - Cinematic Studio считывает задание, выполняет захват и рендеринг, после чего возвращает отчет о готовности.
   - dem.Toshka автоматически импортирует готовый MP4-актив в локальную библиотеку пользователя.

---

## 2. Архитектура интеграционного моста

```
+-------------------------------------------------------------------------+
|                      MAIN APP: dem.Toshka                               |
|                                                                         |
|  [Highlight Studio] --> [StudioJobManifest Generator]                   |
|                               |                                         |
|  [RenderedAssetImporter] <-- [StudioJobStatusProvider]                  |
+-------------------------------+-----------------------------------------+
                                | File / CLI / IPC Contract
                                v
                +-------------------------------+
                |   manifests/jobs/<job_id>.json |
                |   manifests/status/<id>.json  |
                +-------------------------------+
                                ^
                                |
+-------------------------------+-----------------------------------------+
|                  EXTENSION: Cinematic Studio                            |
|                                                                         |
|  [StudioJobLauncher] --> [HLAE Controller] --> [FFmpeg Compositor]     |
|                               |                                         |
|  [Render Engine] ------> [renders/<clip_name>.mp4]                      |
+-------------------------------------------------------------------------+
```

### Компоненты на стороне основного приложения:
- `StudioAvailabilityDetector`: Проверяет доступность установленной Cinematic Studio (проверка бинарного файла, переменной окружения или рабочей папки).
- `StudioCapabilityProvider`: Опрашивает доступные профили рендера (например, Clean Cinematic, Broadcast Esports, TikTok 9:16, VFX Multi-pass).
- `StudioJobManifest`: Класс данных, формирующий исчерпывающее описание задачи рендера.
- `StudioJobLauncher`: Инициирует выполнение задания через запуск CLI процесса или размещение манифеста в очереди.
- `StudioJobStatusProvider`: Отслеживает статус выполнения (`pending`, `rendering`, `completed`, `failed`, прогресс 0–100%).
- `RenderedAssetImporter`: Регистрирует сгенерированный MP4 файл в локальной базе данных `demtoshka.db`.

---

## 3. Спецификация схемы `StudioJobManifest` v1.0

Формат файла: `JSON` (кодировка UTF-8).

```json
{
  "$schema": "https://demtoshka.app/schemas/studio-job-manifest-v1.json",
  "version": "1.0.0",
  "job_id": "job_20261119_140522_ace_r19_pytoshka",
  "created_at": "2026-11-19T14:05:22.105Z",
  
  "demo": {
    "identifier": "demo_de_anubis_20261005_128t",
    "file_path": "C:\\CS2\\Demos\\match_anubis_faceit.dem",
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "map": "de_anubis",
    "tickrate": 128,
    "match_date": "2026-10-05T18:30:00Z"
  },

  "clip": {
    "round_num": 19,
    "start_tick": 142100,
    "end_tick": 143800,
    "highlight_type": "ace",
    "highlight_score": 96.5,
    "score_explanation": "ACE с M4A1 за 6.8 сек, 3 хедшота, решающий раунд матча",
    "tags": ["ace", "headshot_sequence", "clutch_factor", "site_b"]
  },

  "actors": {
    "primary_player": {
      "steam_id": "76561198000000001",
      "name": "pytoshka_",
      "team": "ct",
      "pov_preference": "first_person"
    },
    "related_players": [
      {
        "steam_id": "76561198000000002",
        "name": "Tiger07",
        "team": "t",
        "role": "victim_1"
      },
      {
        "steam_id": "76561198000000003",
        "name": "ShadowSniper",
        "team": "t",
        "role": "victim_2"
      }
    ]
  },

  "events": [
    {
      "tick": 142450,
      "event_type": "kill",
      "attacker_steam_id": "76561198000000001",
      "victim_steam_id": "76561198000000002",
      "weapon": "m4a1_silencer",
      "headshot": true,
      "wallbang": false,
      "kill_number_in_sequence": 1
    },
    {
      "tick": 142820,
      "event_type": "kill",
      "attacker_steam_id": "76561198000000001",
      "victim_steam_id": "76561198000000003",
      "weapon": "m4a1_silencer",
      "headshot": false,
      "wallbang": false,
      "kill_number_in_sequence": 2
    }
  ],

  "production_request": {
    "profile": "clean_cinematic",
    "resolution": "1920x1080",
    "fps": 60,
    "hud_mode": "killfeed_only",
    "custom_camera_allowed": true,
    "user_notes": "Сделать замедление на 3-м хедшоте",
    "output_directory": "C:\\demToshka\\renders\\ACE_Anubis_pytoshka"
  }
}
```

---

## 4. Спецификация схемы отчета о выполнении `StudioJobStatus`

Файл статуса сохраняется в `manifests/status/<job_id>.json`:

```json
{
  "job_id": "job_20261119_140522_ace_r19_pytoshka",
  "status": "completed",
  "progress_pct": 100.0,
  "stage": "encoding_complete",
  "error": null,
  "started_at": "2026-11-19T14:05:25.000Z",
  "completed_at": "2026-11-19T14:06:40.000Z",
  "output_assets": [
    {
      "file_path": "C:\\demToshka\\renders\\ACE_Anubis_pytoshka\\ACE_FINAL_MASTER.mp4",
      "format": "mp4",
      "duration_seconds": 13.28,
      "file_size_bytes": 26288120,
      "resolution": "1920x1080",
      "fps": 60
    }
  ]
}
```

---

## 5. Поведение при отсутствии или сбое Cinematic Studio

1. **Cinematic Studio не установлена:**
   - Кнопка «Отправить в Cinematic Studio» в основном интерфейсе корректно отображает статус: *«Студия не обнаружена. Доступен базовый локальный захват или экспорт манифеста»*.
   - Пользователь может скачать сформированный `.json` манифест для последующего запуска на другой рабочей машине.
2. **Ошибка во время рендера в студии:**
   - Cinematic Studio записывает в статус `status: "failed"` и подробное описание ошибки в поле `error`.
   - dem.Toshka отображает понятное пользователю уведомление с рекомендациями по устранению (например, *«Недостаточно места на диске»* или *«CS2 не смогла загрузить карту»*), не блокируя работу интерфейса.
