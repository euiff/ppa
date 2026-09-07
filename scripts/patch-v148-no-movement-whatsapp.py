from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "pkg")
p = root / "assets/index-C6Ng0a8i.js"
s = p.read_text()

calls = [
    'I.functions.invoke("notify-movement",{body:{type:"checkin",escala_id:N,voluntario_id:e.id,igreja_id:t}})',
    'I.functions.invoke("notify-movement",{body:{type:"checkout",escala_id:N,voluntario_id:e.id,igreja_id:t}})',
    'I.functions.invoke("notify-movement",{body:{type:"on_the_way",escala_id:X.id,voluntario_id:e.id,igreja_id:t}})',
]

for call in calls:
    if call not in s:
        raise SystemExit(f"v1.4.8 movement call not found: {call}")
    s = s.replace(call, 'Promise.resolve({data:{disabled:!0},error:null})', 1)

if 'I.functions.invoke("notify-movement"' in s:
    raise SystemExit("unexpected notify-movement call remains")
if 'volunteer_locations' not in s or 'Mapa de Voluntários' not in s:
    raise SystemExit("tracking/map anchor missing after patch")

p.write_text(s)

# Force clients/PWA to receive the no-movement-notification build.
h = root / "sistema.html"
t = h.read_text()
t = re.sub(r'/assets/index-C6Ng0a8i\.js\?v=[^"\']+', '/assets/index-C6Ng0a8i.js?v=1.4.8', t)
t = re.sub(r'/master-migration-entry\.js\?v=[^"\']+', '/master-migration-entry.js?v=1480', t)
h.write_text(t)

sw = root / "sw.js"
t = sw.read_text()
t = re.sub(r'url:"sistema\.html",revision:"[^"]*"', 'url:"sistema.html",revision:"v148-no-movement-whatsapp"', t)
t = re.sub(r'url:"assets/index-C6Ng0a8i\.js",revision:(?:null|"[^"]*")', 'url:"assets/index-C6Ng0a8i.js",revision:"v148-no-movement-whatsapp"', t)
if "no-movement-whatsapp-cache-bust-v1.4.8" not in t:
    t += "\n/* no-movement-whatsapp-cache-bust-v1.4.8 */\n"
sw.write_text(t)

(root / "registerSW.js").write_text(
    "if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const r=await navigator.serviceWorker.register('/sw.js?v=1.4.8',{scope:'/',updateViaCache:'none'});await r.update()}catch(e){console.warn('[SW v1.4.8]',e)}})}"
)
