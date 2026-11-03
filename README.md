<div align="center">

# ⚡ dem.Toshka | CS2 Highlights Studio

### Автономная киберспортивная студия анализа демок Counter-Strike 2, 2D-тактического реплея и автоматического монтажа хайлайтов в 120 FPS

[![Release v0.1.0-beta Installer](https://img.shields.io/badge/Installer-Setup--v0.1.0--beta.exe-38bdf8?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/1GOGA/dem.Toshka/releases)
[![Platform Windows](https://img.shields.io/badge/Platform-Windows_10_%2F_11-0078d4?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/1GOGA/dem.Toshka)
[![Twitch Live](https://img.shields.io/badge/Twitch-pytoshka__-9146ff?style=for-the-badge&logo=twitch&logoColor=white)](https://www.twitch.tv/pytoshka_)
[![DonationAlerts](https://img.shields.io/badge/Donate-DonationAlerts-f97316?style=for-the-badge&logo=heart&logoColor=white)](https://www.donationalerts.com/r/pytoshka_)
[![Steam Trade](https://img.shields.io/badge/Steam-Trade_Offer-0284c7?style=for-the-badge&logo=steam&logoColor=white)](https://steamcommunity.com/tradeoffer/new/?partner=1076140204&token=-A3e3Vab)
[![Telegram](https://img.shields.io/badge/Telegram-@thepytoshka-229ed9?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/thepytoshka)
[![License MIT](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge)](LICENSE)

<br/>

[![Скачать инсталлятор](https://img.shields.io/badge/📥%20Скачать%20Setup--dem.Toshka--v0.1.0--beta.exe-0284c7?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/1GOGA/dem.Toshka/releases)
[![Поддержать автора](https://img.shields.io/badge/💖%20Поддержать%20Автора%20(Донат)-ec4899?style=for-the-badge&logo=heart&logoColor=white)](https://www.donationalerts.com/r/pytoshka_)
[![Смотреть Стрим](https://img.shields.io/badge/🟣%20Twitch%20Стрим-9146ff?style=for-the-badge&logo=twitch&logoColor=white)](https://www.twitch.tv/pytoshka_)
[![Все Релизы](https://img.shields.io/badge/🚀%20Все%20Релизы%20GitHub-10b981?style=for-the-badge&logo=github)](https://github.com/1GOGA/dem.Toshka/releases)
[![Telegram Канал](https://img.shields.io/badge/💬%20Telegram%20Канал%20Разработчика-229ed9?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/thepytoshka)

<br/>

</div>

---

## 🌟 О проекте

**dem.Toshka** — это мощная автономная рабочая станция для игроков, аналитиков, тренеров и авторов контента по **Counter-Strike 2**. Приложение берет на себя всю рутину с консолью: автоматически парсит `.dem` файлы Source 2, вычисляет лучшие моменты матча (ACE, клатчи 1vX, мультикиллы, первые дуэли), строит интерактивный 2D-радар с траекториями и таймерами раскидок, и в один клик записывает готовые MP4-ролики с киберспортивным форматом **4:3**, кастомным прицелом и ультра-плавностью **до 120 FPS**.

---

## 🚀 Ключевые возможности

### 🎬 1. Интеллектуальная Студия Хайлайтов (4 шага)
```
[ 📁 1. Выбор демки ] ──▶ [ 👤 2. Выбор игрока ] ──▶ [ 🎯 3. Моменты & 2D Радар ] ──▶ [ ⚡ 4. Создать нарезку ]
```
* **Шаг 1: Загрузка демки** — перетащите `.dem` файл методом Drag & Drop или выберите файл из библиотеки. Анимированный индикатор наглядно отображает этапы декомпрессии и считывания бинарных тиков Source 2.
* **Шаг 2: Выбор игрока** — выберите себя, тиммейта или режим «Все игроки». Откроется карточка игрока со сводкой фрагов, клатчей и аналитикой.
* **Шаг 3: Моменты и 2D Радар** — фильтруйте эпизоды (ACE, 4K, 3K, Headshots, Clutches) с моментальной синхронизацией на интерактивном 2D-радаре.
* **Шаг 4: Киберспортивный экспорт** — настройте формат, FOV, FPS, прицел и запустите рендер одной акцентной кнопкой **«⚡ СОЗДАТЬ НАРЕЗКУ»**.

---

### ⚡ 2. Single-Session Batching (Без постоянных перезапусков CS2!)
* **Запись всей нарезки за 1 сеанс:** больше не нужно ждать, пока игра перезапустится под каждый фраг. Движок компонует единый сценарий с быстрой перемоткой `demo_gototick` — CS2 открывается **ровно 1 раз**, последовательно фиксирует все выбранные эпизоды и плавно закрывается.
* Экономит до 80% времени при пакетном создании хайлайтов и бережет ресурсы компьютера.

---

### 🎥 3. Режиссер камеры (POV) и Режим «REAL OBS»
* **🎬 Главный Герой:** 100% времени от лица автора фрагов за один запуск игры (идеально для персональных нарезок и фрагмуви).
* **⚡ Килл-кам PRO:** кинематографический турнирный реплей в стиле BLAST Premier (хроника смертей жертв от первого лица ➔ мгновенная отмотка на 4 сек назад ➔ триумф и доигрывание момента победителем).
* **Режим REAL OBS:** убирает спектаторские плашки и X-Ray контуры (`spec_show_xray 0`, `hud_showtargetid 0`), формируя чистую картинку живого матча для Shorts и TikTok.

---

### 📐 4. Формат 4:3 Stretched, 120 FPS и Кастомный Прицел
* **Формат 4:3 (Киберспорт):** растянутые разрешения `1280x960` и `1440x1080` (модели противников шире на 33%, как у s1mple, m0NESY, donk).
* **Поэтапный FPS:** выбор частоты кадров под любую задачу:
  * `30 FPS` — легкий быстрый экспорт.
  * `60 FPS` — стандарт плавного Full HD геймплея.
  * `120 FPS ⚡` — кинематографическая плавность для эффектного Slow-Motion в монтаже.
* **Интерактивный симулятор прицела:** выбор пресетов (*Pro Cyan, Clean Green, Thin White, Hidden*) с моментальным превью на фонах соревновательных карт (*Mirage, Inferno, Nuke, Dust II*).

---

### 🗺️ 5. Интерактивный 2D Тактический Реплей Source 2
* **Сбалансированное масштабирование ников:** при зуме карты ники игроков остаются четкими, контрастными и легко читаемыми (не сжимаются в микро-точки).
* **Живые таймеры гранат:** наглядные круги действия дымовых завес (смок 7s) и зажигательных смесей (молотов 6.2s) с таймерами обратного отсчета.
* **Таймер C4:** статус установки бомбы с указанием конкретного плента (*ПЛЕНТ A / ПЛЕНТ B*) и индикацией времени до взрыва.
* **Умный старт раунда:** 10 секунд бессмысленного стояния на спавне (фризтайм) автоматически пропускаются — радар сразу фокусируется на боевых контактах.

---

### 🔒 6. CS2 Config Shield и VAC Безопасность
* **100% Безопасно для VAC:** игра запускается с изолированными турнирными флагами `-steam -insecure +sv_lan 1 -afxDisableSteamStorage`. Сетевое подключение к серверам Valve полностью заблокировано.
* **Защита пользовательских конфигов:** `ConfigBackupManager` делает защитную резервную копию вашего личного `csgo/cfg/autoexec.cfg` перед запуском съемки и автоматически восстанавливает его после рендера.

---

## 📥 Быстрый старт

### Вариант 1. Установщик Windows (Рекомендуется для всех)
> **Не требует установки Python, Node.js или дополнительных библиотек!**

1. Скачайте файл **[`Setup-dem.Toshka-v0.1.0-beta.exe`](https://github.com/1GOGA/dem.Toshka/releases)**.
2. Запустите инсталлятор и следуйте подсказкам мастера установки.
3. Программа создаст ярлыки на рабочем столе и в меню «Пуск».
4. **Безопасная деинсталляция:** при удалении через «Параметры Windows» программа корректно очищает системные библиотеки и кэш, бережно сохраняя ваши отрендеренные клипы (`renders/`) и загруженные демки (`demos/`).

---

### Вариант 2. Запуск из исходного кода (Для разработчиков)

#### Требования:
* **ОС:** Windows 10 / 11 (64-bit)
* **Python:** 3.10+
* **Node.js:** 18+

```powershell
# 1. Клонируйте репозиторий
git clone https://github.com/1GOGA/dem.Toshka.git
cd dem.Toshka

# 2. Быстрый запуск бэкенда и интерфейса в 1 клик
.\start_app.bat
```
Приложение автоматически откроется в браузере по адресу:  
👉 **`http://localhost:5173`** *(бэкенд API: `http://localhost:8000`)*

> Чтобы корректно остановить все процессы, запустите **`.\stop_app.bat`**.

---

## 🛠️ Разработка и верификация

Проект покрыт автоматическими тестами и строгой валидацией:

```powershell
# Запуск полного набора юнит-тестов (235 тестов)
.\.venv\Scripts\python -m pytest tests/unit/ -v

# Проверка сборки фронтенда (TypeScript + Vite)
cmd.exe /c "npm --prefix frontend run build"
```

---

## 💬 Сообщество и обратная связь

* 📢 **Telegram-канал разработчика:** [@thepytoshka](https://t.me/thepytoshka) — новости, обновления и релизы.
* 🐛 **Баги и предложения:** создавайте [Issue в репозитории GitHub](https://github.com/1GOGA/dem.Toshka/issues).
* 📜 **Лицензия:** [MIT License](LICENSE)

<br/>

<div align="center">
  <sub>Создано с любовью к Counter-Strike 2 сообществу • <strong>pytoshka</strong></sub>
</div>
