import pathlib

torrent_path = pathlib.Path("GameAudioGDCPart9.torrent")
# If it was in memory, let's download it to a file
import urllib.request
url = "https://downloads.sonniss.com/GameAudioGDCPart9.torrent"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://gdc.sonniss.com/'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = resp.read()
    torrent_path.write_bytes(data)

print(f"Downloaded torrent file: {len(data)} bytes")

# Simple bencode decoder for files list
def bdecode_dict(b, idx):
    d = {}
    idx += 1
    while idx < len(b) and b[idx:idx+1] != b'e':
        # key is string
        key, idx = bdecode_str(b, idx)
        val, idx = bdecode_val(b, idx)
        d[key] = val
    return d, idx + 1

def bdecode_list(b, idx):
    l = []
    idx += 1
    while idx < len(b) and b[idx:idx+1] != b'e':
        val, idx = bdecode_val(b, idx)
        l.append(val)
    return l, idx + 1

def bdecode_int(b, idx):
    idx += 1
    end = b.index(b'e', idx)
    return int(b[idx:end]), end + 1

def bdecode_str(b, idx):
    colon = b.index(b':', idx)
    length = int(b[idx:colon])
    start = colon + 1
    end = start + length
    return b[start:end].decode('utf-8', errors='ignore'), end

def bdecode_val(b, idx):
    c = b[idx:idx+1]
    if c == b'd':
        return bdecode_dict(b, idx)
    elif c == b'l':
        return bdecode_list(b, idx)
    elif c == b'i':
        return bdecode_int(b, idx)
    elif c.isdigit():
        return bdecode_str(b, idx)
    raise ValueError(f"Unknown bencode type at {idx}: {c}")

torrent, _ = bdecode_val(data, 0)
info = torrent.get('info', {})
name = info.get('name', '')
print("Torrent Name:", name)
files = info.get('files', [])
print("Total Files in Torrent:", len(files))

# Show categories / vendors in the files list
vendors = set()
for f in files:
    path_parts = f.get('path', [])
    if len(path_parts) > 1:
        vendors.add(path_parts[0])

print(f"\nDiscovered {len(vendors)} vendor packages in GDC 2026 bundle:")
for v in sorted(vendors)[:20]:
    print(" -", v)
