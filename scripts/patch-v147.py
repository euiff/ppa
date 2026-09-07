from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "pkg")
p = root / "assets/index-C6Ng0a8i.js"
s = p.read_text()

# v1.4.6 already contains the approved visual model. v1.4.7 only changes
# the print invocation so the user goes straight to Chrome's print dialog.
old_close = 'De.document.close()}catch(ke){V.error((ke==null?void 0:ke.message)||"Não foi possível preparar a impressão")}'
new_close = 'De.document.close(),De.focus(),De.onafterprint=()=>{try{De.close()}catch{}},setTimeout(()=>{try{De.print()}catch(ke){console.warn("[Impressão] Falha ao abrir diálogo",ke)}},300)}catch(ke){V.error((ke==null?void 0:ke.message)||"Não foi possível preparar a impressão")}'
if old_close not in s:
    raise SystemExit("print close anchor not found")
s = s.replace(old_close, new_close, 1)

# Explicitly request A4 portrait in print CSS. This is the strongest setting a
# web page can provide to Chrome/printer drivers without controlling the OS.
s, n = re.subn(r'@page\{size:A4;margin:7mm 7mm 8mm\}', '@page{size:A4 portrait;margin:7mm 7mm 8mm}', s, count=1)
if n != 1:
    raise SystemExit("A4 @page anchor not found")

p.write_text(s)

# Cache bust so installed PWAs also receive the corrected print behavior.
h = root / "sistema.html"
t = h.read_text()
t = re.sub(r'/assets/index-C6Ng0a8i\.js\?v=[^"\']+', '/assets/index-C6Ng0a8i.js?v=1.4.7', t)
t = re.sub(r'/master-migration-entry\.js\?v=[^"\']+', '/master-migration-entry.js?v=1470', t)
h.write_text(t)

sw = root / "sw.js"
t = sw.read_text()
t = re.sub(r'url:"sistema\.html",revision:"[^"]*"', 'url:"sistema.html",revision:"v147-print-dialog-a4"', t)
t = re.sub(r'url:"assets/index-C6Ng0a8i\.js",revision:(?:null|"[^"]*")', 'url:"assets/index-C6Ng0a8i.js",revision:"v147-print-dialog-a4"', t)
if "print-dialog-a4-cache-bust-v1.4.7" not in t:
    t += "\n/* print-dialog-a4-cache-bust-v1.4.7 */\n"
sw.write_text(t)

(root / "registerSW.js").write_text(
    "if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const r=await navigator.serviceWorker.register('/sw.js?v=1.4.7',{scope:'/',updateViaCache:'none'});await r.update()}catch(e){console.warn('[SW v1.4.7]',e)}})}"
)
