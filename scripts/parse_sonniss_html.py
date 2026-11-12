import urllib.request
import re

req = urllib.request.Request(
    'https://gdc.sonniss.com/',
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
)
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# find occurrences of downloads.sonniss.com and context
matches = re.finditer(r'.{0,150}downloads\.sonniss\.com.{0,200}', html, re.DOTALL)
for m in matches:
    print("--- Context ---")
    print(m.group(0))
