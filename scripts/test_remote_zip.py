import urllib.request
import zipfile
import io

def inspect_remote_zip(url, total_size):
    # Fetch last 128 KB
    tail_size = min(total_size, 256 * 1024)
    start_byte = total_size - tail_size
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://gdc.sonniss.com/',
        'Range': f'bytes={start_byte}-{total_size-1}'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        tail_data = resp.read()
    
    # We can create a Seekable HTTP Range file-like object for zipfile.ZipFile!
    class RemoteZipStream(io.RawIOBase):
        def __init__(self, url, size, tail, tail_start):
            self.url = url
            self.size = size
            self.pos = 0
            self.tail = tail
            self.tail_start = tail_start
            
        def seekable(self):
            return True
            
        def seek(self, offset, whence=0):
            if whence == 0:
                self.pos = offset
            elif whence == 1:
                self.pos += offset
            elif whence == 2:
                self.pos = self.size + offset
            return self.pos
            
        def tell(self):
            return self.pos
            
        def read(self, size=-1):
            if size == -1 or self.pos + size > self.size:
                size = self.size - self.pos
            if size <= 0:
                return b''
            
            # Check if entirely in tail buffer
            if self.pos >= self.tail_start:
                offset_in_tail = self.pos - self.tail_start
                data = self.tail[offset_in_tail:offset_in_tail+size]
                self.pos += len(data)
                return data
                
            # Otherwise fetch range
            end_byte = self.pos + size - 1
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Referer': 'https://gdc.sonniss.com/',
                'Range': f'bytes={self.pos}-{end_byte}'
            }
            req = urllib.request.Request(self.url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            self.pos += len(data)
            return data

    stream = RemoteZipStream(url, total_size, tail_data, start_byte)
    zf = zipfile.ZipFile(stream)
    namelist = zf.namelist()
    print(f"Zip {url.split('/')[-1]} has {len(namelist)} entries.")
    for n in namelist[:15]:
        print("  ", n)
    return zf, namelist

# Test with Part 1 (1301592146 bytes)
zf, names = inspect_remote_zip("https://downloads.sonniss.com/Sonniss.com-GDC2026-GameAudioBundle1of5.zip", 1301592146)
