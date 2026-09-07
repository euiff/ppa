from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "pkg")

# Tela do código da igreja: remove a opção de gerar novo e deixa claro que o código é permanente.
h = root / "codigo-igreja.html"
t = h.read_text()

old_buttons = '<div class="btns"><button id="copy" class="btn primary">COPIAR CÓDIGO</button><button id="regen" class="btn secondary">GERAR NOVO</button></div>'
new_buttons = '<div class="btns" style="grid-template-columns:1fr"><button id="copy" class="btn primary">COPIAR CÓDIGO</button></div>'
if old_buttons not in t:
    raise SystemExit("botão GERAR NOVO não encontrado")
t = t.replace(old_buttons, new_buttons, 1)

old_warn = 'A licença é da <b>igreja</b>. Voluntários e líderes entram usando este código ou o link de convite e não pagam individualmente. Se você gerar um novo código, o anterior deixa de funcionar.'
new_warn = 'Este é o <b>código permanente da igreja</b>. Voluntários e líderes entram usando este mesmo código ou o link de convite. O código não pode ser trocado ou regenerado.'
if old_warn not in t:
    raise SystemExit("aviso antigo do código não encontrado")
t = t.replace(old_warn, new_warn, 1)

old_load = "async function load(action){const r=await fetch('/api/church-code.php',{method:action?'POST':'GET',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:action?JSON.stringify({action}):undefined,cache:'no-store'});"
new_load = "async function load(){const r=await fetch('/api/church-code.php',{method:'GET',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},cache:'no-store'});"
if old_load not in t:
    raise SystemExit("função load antiga não encontrada")
t = t.replace(old_load, new_load, 1)

t = re.sub(r";regen\.onclick=async\(\)=>\{.*?\};</script>", ";</script>", t, count=1)
if 'GERAR NOVO' in t or 'regen.onclick' in t or 'id="regen"' in t:
    raise SystemExit("opção de regenerar ainda presente na tela")
if 'código permanente da igreja' not in t:
    raise SystemExit("texto de código permanente ausente")
h.write_text(t)

# Backend: bloqueia também tentativas diretas de regeneração pela API.
p = root / "api/church-code.php"
s = p.read_text()
s = s.replace('Somente o administrador principal da igreja pode ver ou trocar o código.', 'Somente o administrador principal da igreja pode ver o código.')
old = "    $req=$_SERVER['REQUEST_METHOD']==='POST'?input_json():[];\n    if(($req['action']??'')==='regenerate'){\n        $access['join_code']=tenant_v1323_regenerate_code($igreja);\n    }\n"
new = "    $req=$_SERVER['REQUEST_METHOD']==='POST'?input_json():[];\n    if(($req['action']??'')==='regenerate'){\n        out(['data'=>null,'error'=>['message'=>'O código da igreja é permanente e não pode ser regenerado.']],409);\n    }\n"
if old not in s:
    raise SystemExit("bloco de regeneração da API não encontrado")
s = s.replace(old, new, 1)
if 'tenant_v1323_regenerate_code($igreja)' in s:
    raise SystemExit("chamada de regeneração ainda ativa na API")
p.write_text(s)

# Cache-bust da tela estática e do PWA.
sw = root / "sw.js"
if sw.exists():
    x = sw.read_text()
    if "fixed-church-code-v1.4.9" not in x:
        x += "\n/* fixed-church-code-v1.4.9 */\n"
    sw.write_text(x)

rsw = root / "registerSW.js"
if rsw.exists():
    x = rsw.read_text()
    x = re.sub(r"/sw\.js\?v=[0-9.]+", "/sw.js?v=1.4.9", x)
    rsw.write_text(x)
