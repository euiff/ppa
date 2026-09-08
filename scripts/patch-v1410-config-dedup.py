from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'pkg')
smart = root / 'smart-features.js'
s = smart.read_text()

old = "const holder=document.createElement('div');holder.id='smart-sos-link';holder.append(card('sf-notif','🔔','Notificações','Escalas próximas, SOS e avisos importantes','/notificacoes.html'));holder.append(card('sf-sos','🚨','SOS Escala','Acompanhe substituições inteligentes e candidatos','/sos.html'));\n  try{const r=await fetch('/api/church-admin.php',{headers:{Authorization:'Bearer '+token},cache:'no-store'});if(r.ok)holder.append(card('sf-admin','👑','Administração da igreja','Titularidade, licença e transferência de administrador','/administracao-igreja.html'))}catch{}\n  holder.append(card('sf-privacy','🛡️','Privacidade e conta','Política de privacidade e exclusão da conta','/excluir-conta.html'));holder.append(card('sf-about','ℹ️','Sobre o app','Escala de Propósito e dados do desenvolvedor','/sobre-app.html'));box.appendChild(holder)"
new = "const holder=document.createElement('div');holder.id='smart-sos-link';holder.append(card('sf-notif','🔔','Notificações','Escalas próximas, SOS e avisos importantes','/notificacoes.html'));holder.append(card('sf-sos','🚨','SOS Escala','Acompanhe substituições inteligentes e candidatos','/sos.html'));box.appendChild(holder);\n  try{const r=await fetch('/api/church-admin.php',{headers:{Authorization:'Bearer '+token},cache:'no-store'});if(r.ok&&!document.getElementById('sf-admin'))holder.append(card('sf-admin','👑','Administração da igreja','Titularidade, licença e transferência de administrador','/administracao-igreja.html'))}catch{}\n  if(!document.getElementById('sf-privacy'))holder.append(card('sf-privacy','🛡️','Privacidade e conta','Política de privacidade e exclusão da conta','/excluir-conta.html'));if(!document.getElementById('sf-about'))holder.append(card('sf-about','ℹ️','Sobre o app','Escala de Propósito e dados do desenvolvedor','/sobre-app.html'))"
if old not in s:
    raise SystemExit('smart-features configCards anchor not found')
s = s.replace(old, new, 1)
smart.write_text(s)

# Cache bust so installed PWAs receive the correction.
h = root / 'sistema.html'
t = h.read_text()
t = re.sub(r'/smart-features\.js\?v=[^\"\']+', '/smart-features.js?v=1410', t)
t = re.sub(r'/assets/index-C6Ng0a8i\.js\?v=[^\"\']+', '/assets/index-C6Ng0a8i.js?v=1.4.10', t)
h.write_text(t)

sw = root / 'sw.js'
t = sw.read_text()
t = re.sub(r'url:\"sistema\.html\",revision:\"[^\"]*\"', 'url:\"sistema.html\",revision:\"v1410-config-dedup\"', t)
if 'config-dedup-cache-bust-v1.4.10' not in t:
    t += '\n/* config-dedup-cache-bust-v1.4.10 */\n'
sw.write_text(t)

(root / 'registerSW.js').write_text("if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const r=await navigator.serviceWorker.register('/sw.js?v=1.4.10',{scope:'/',updateViaCache:'none'});await r.update()}catch(e){console.warn('[SW v1.4.10]',e)}})}")
