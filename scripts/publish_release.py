import ctypes
from ctypes import wintypes
import urllib.request
import urllib.error
import json
import os
import sys
import time

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME),
        ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_char)),
        ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR),
    ]

def get_github_token() -> str:
    Advapi32 = ctypes.WinDLL('Advapi32.dll')
    CredReadW = Advapi32.CredReadW
    CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    CredReadW.restype = wintypes.BOOL
    CredFree = Advapi32.CredFree
    CredFree.argtypes = [ctypes.c_void_p]

    for target in ['git:https://1GOGA@github.com', 'git:https://github.com']:
        p_cred = ctypes.POINTER(CREDENTIAL)()
        if CredReadW(target, 1, 0, ctypes.byref(p_cred)):
            raw = ctypes.string_at(p_cred.contents.CredentialBlob, p_cred.contents.CredentialBlobSize)
            token = raw.decode('utf-16le', errors='ignore').strip('\x00')
            if not token.startswith('gh'):
                token = raw.decode('utf-8', errors='ignore').strip('\x00')
            CredFree(p_cred)
            if token.startswith('gh'):
                return token
    raise RuntimeError("GitHub token not found in Windows Credential Manager")

REPO = "1GOGA/dem.Toshka"

def github_request(endpoint: str, method: str = 'GET', data=None, content_type: str = 'application/json', is_upload: bool = False):
    token = get_github_token()
    base = "https://uploads.github.com" if is_upload else "https://api.github.com"
    url = f"{base}{endpoint}" if not endpoint.startswith("http") else endpoint
    
    headers = {
        'Authorization': f'token {token}',
        'User-Agent': 'demToshka-Release-Publisher',
        'Accept': 'application/vnd.github+json'
    }
    if content_type:
        headers['Content-Type'] = content_type

    body = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode('utf-8')
        else:
            body = data

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        code = resp.getcode()
        resp_data = resp.read()
        return code, json.loads(resp_data.decode('utf-8')) if resp_data else None

def main():
    print(f"=== dem.Toshka GitHub Release Publisher ===")
    token = get_github_token()
    print(f"[*] Retrieved auth token from Credential Manager (length: {len(token)})")

    # 1. Fetch current releases
    print("[*] Fetching existing releases...")
    code, releases = github_request(f"/repos/{REPO}/releases")
    print(f"[*] Found {len(releases)} existing release(s).")
    
    # 2. Delete old releases if any (e.g., v0.1.0 with bug)
    for r in releases:
        tag = r.get('tag_name')
        rel_id = r.get('id')
        print(f"[*] Deleting old release '{tag}' (ID: {rel_id}) as requested...")
        try:
            del_code, _ = github_request(f"/repos/{REPO}/releases/{rel_id}", method='DELETE')
            print(f"[+] Successfully deleted release {rel_id} (HTTP {del_code})")
        except Exception as e:
            print(f"[-] Warning deleting release {rel_id}: {e}")

    # 3. Create new release v0.2.0
    tag_name = "v0.2.0"
    release_name = "dem.Toshka v0.2.0 — Next-Gen Match Intelligence & Clean Killcam Update"
    release_body = """# 🚀 dem.Toshka v0.2.0 — Next-Gen Match Intelligence & Clean Killcam Update

## 📦 Скачать приложение для Windows 10/11 x64
- **[Setup-dem.Toshka-v0.2.0-Windows-x64.exe](https://github.com/1GOGA/dem.Toshka/releases/download/v0.2.0/Setup-dem.Toshka-v0.2.0-Windows-x64.exe)** (244 MB) — **Рекомендуемый установщик** (простая установка в один клик, запуск с рабочего стола).
- **[dem.Toshka_v0.2.0_Windows_x64.zip](https://github.com/1GOGA/dem.Toshka/releases/download/v0.2.0/dem.Toshka_v0.2.0_Windows_x64.zip)** (375 MB) — Портативная версия (без установки: распакуйте архив и запустите `dem.Toshka.exe`).

---

## 🛠️ Что нового и исправления в v0.2.0

### 🎯 1. Исправление Чистого Килл-кама (Clean Killcam Fix)
- **Устранён конфликт с режимом REAL OBS:** Ранее при включении «Только Киллфид (Чистый экран)» в конфиге оставались активными конвары турнирного оверлея и круговой радар. Теперь «Чистый Киллфид» принудительно скрывает радар (`cl_hud_radar_scale 0`) и карточки наблюдателя.
- **Устранён пропуск тиков при поиске (Tick Seeking):** Запас тиков перед стартом (`jump_lead_ticks`) увеличен с 20 до 48 тиков, что гарантирует надёжный триггер захвата HLAE `addAtTick` при Source 2 ключевых кадрах.
- **Расширены тайминги жертвы (Victim Margins):** Добавлен буфер в 2.2с до фрага и 1.2с после, исключая обрезку фрагментов.
- **Быстрые пресеты в интерфейсе:** В модальном окне клипа добавлены кнопки в 1 клик — `✨ Чистый (без худа)` и `🎮 Турнирный HUD`.

### 🧠 2. Demo Vision — Интерактивный 2D Replay & Tactical Map
- Полноценный 2D радар с точной геометрией соревновательных карт CS2.
- Отображение позиций всех 10 игроков, направлений взгляда, HP, брони, оружия и траекторий движения.
- Векторное тактическое рисование (Tactical Drawing): стрелки, линии, зоны, круги, текст с привязкой к раундам и тикам.

### 🎙️ 3. Voice Timeline Engine
- Автоматическое обнаружение голосовых пакетов в демках CS2 (Matchmaking, FACEIT, FastCup).
- Индивидуальные дорожки игроков, таймлайн активности переговоров, экспорт в WAV/FLAC.

### 📊 4. Multi-Match Player Analytics & Performance Patterns
- Сквозная аналитика игрока по нескольким матчам: Aim & Duels, энтри-фраги, торговля (Trading & Isolation), клатч-рейтинг, экономические тренды, CT/T сплит.
- Матрица паттернов эффективности по картам и дням недели.

### 📚 5. Strategy Book & Teamplay Exporter
- Сохранение тактических разборов раундов, закладок и заметок.
- Экспорт тактических отчётов в интерактивный HTML / JSON / PDF для тренеров и команд.
"""

    create_payload = {
        "tag_name": tag_name,
        "target_commitish": "main",
        "name": release_name,
        "body": release_body,
        "draft": False,
        "prerelease": False,
        "make_latest": "true"
    }

    print(f"[*] Creating release '{release_name}' for tag '{tag_name}'...")
    code, new_release = github_request(f"/repos/{REPO}/releases", method='POST', data=create_payload)
    new_release_id = new_release.get('id')
    upload_url_template = new_release.get('upload_url')
    print(f"[+] Release created successfully! ID: {new_release_id}")

    # 4. Upload assets
    assets = [
        ("Setup-dem.Toshka-v0.2.0-Windows-x64.exe", "dist-installer/Setup-dem.Toshka-v0.2.0-Windows-x64.exe"),
        ("dem.Toshka_v0.2.0_Windows_x64.zip", "dist/dem.Toshka_v0.2.0_Windows_x64.zip")
    ]

    for asset_name, asset_path in assets:
        if not os.path.exists(asset_path):
            print(f"[-] Error: File not found: {asset_path}")
            continue
        file_size = os.path.getsize(asset_path)
        print(f"[*] Uploading '{asset_name}' ({file_size / (1024*1024):.1f} MB)... This may take 1-2 minutes...")
        
        with open(asset_path, 'rb') as f:
            file_bytes = f.read()

        upload_url = f"/repos/{REPO}/releases/{new_release_id}/assets?name={asset_name}"
        t0 = time.time()
        try:
            up_code, asset_info = github_request(
                upload_url,
                method='POST',
                data=file_bytes,
                content_type='application/octet-stream',
                is_upload=True
            )
            dt = time.time() - t0
            print(f"[+] Uploaded '{asset_name}' successfully in {dt:.1f}s! Asset ID: {asset_info.get('id')}")
        except Exception as e:
            print(f"[-] Upload failed for '{asset_name}': {e}")
            raise

    print("\n[🎉] ALL DONE! Release is live and published with Windows installer executable!")

if __name__ == '__main__':
    main()
