import urllib.request
import re

url = "https://sonniss.com/gdc-bundle-license/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://gdc.sonniss.com/'
}
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        # Extract main text
        clean_text = re.sub(r'<[^>]+>', ' ', html)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        print("License Text Excerpt:")
        print(clean_text[clean_text.find("License"):clean_text.find("License")+1200])
except Exception as e:
    print("Err:", e)
