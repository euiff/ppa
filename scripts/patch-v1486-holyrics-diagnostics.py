from pathlib import Path
import re

root = Path('pkg')
def change(path, old, new, label):
    f = root / path
    s = f.read_text(encoding='utf-8')
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 occurrence, found {count}')
    f.write_text(s.replace(old, new, 1), encoding='utf-8')

script = root / 'Escala-de-Proposito-Holyrics.js'
s = script.read_text(encoding='utf-8')
assert 'V1.0.4' in s and "var token = h.restore(storageKey);" in s
s = s.replace('V1.0.4', 'V1.0.5').replace('v1.0.4', 'v1.0.5')
s = s.replace(
    "h.input('Não consegui autenticar esta igreja. Cole a chave atual da integração Holyrics (se ela foi renovada, use a NOVA chave). Deixe vazio para cancelar.')",
    "h.input('Cole a chave ATUAL de 64 caracteres da igreja. Se não tiver a chave, clique Cancelar.')",
)
change_at = "        h.error('Escala de Propósito: ' + (e.message || e));"
assert s.count(change_at)==1
s = s.replace(change_at,
    """        var safeError = String(e.message || e);
        if (token) safeError = safeError.split(String(token)).join('[chave oculta]');
        try { h.log('[Escala de Propósito Connect] ' + safeError); } catch (ignore) {}
        h.error('Escala de Propósito: ' + safeError);""")
s = s.replace(
    'Compatível com testes do tipo Script e do tipo Ação (Receptor).',
    'Abra pelo menu Scripts/Favoritos; o campo de teste obj.description não é o local para colar funções.'
)
script.write_text(s, encoding='utf-8')

old_ui = root / 'holyrics-copy-script-v1485.js'
js = old_ui.read_text(encoding='utf-8')
assert "var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.84';" in js
js = js.replace('v1485','v1486').replace('v1.4.85','v1.4.86')
js = js.replace(
    "var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.84';",
    "var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.86';"
)
anchor = "    document.getElementById('holyrics-copy-v1486').addEventListener('click', async function () {"
assert js.count(anchor)==1
extra = r"""    var probeBox = document.createElement('div');
    probeBox.style.cssText = 'margin-top:12px;';
    probeBox.innerHTML = '<button class="secondary" type="button" id="holyrics-probe-v1486">🧪 Testar chave + consulta de cultos</button>' +
      '<div id="holyrics-probe-result-v1486" role="status" style="margin-top:7px;font-size:13px"></div>' +
      '<p style="font-size:12px;color:#5d6979">Esse teste usa a MESMA API protegida consultada pelo Holyrics. A chave é enviada apenas no corpo HTTPS e não aparece na URL nem é salva aqui.</p>';
    block.appendChild(probeBox);
    document.getElementById('holyrics-probe-v1486').addEventListener('click', async function() {
      var input = document.getElementById('holyrics-key-v1486');
      var key = String(input.value || '').trim();
      var message = document.getElementById('holyrics-probe-result-v1486');
      if(!key) {
        var secret=document.getElementById('secret');
        var keybox=document.getElementById('keybox');
        if(secret && keybox && !keybox.hidden)key=String(secret.textContent||'').trim();
      }
      if(!/^[a-f0-9]{64}$/i.test(key)){
        message.style.color='#b91c1c';
        message.textContent='Cole uma chave de 64 caracteres no campo Validar chave da igreja.';
        return;
      }
      var btn=this; btn.disabled=true;
      message.style.color='#244f8f';
      message.textContent='Testando consulta protegida à API...';
      try {
        var response=await fetch('/api/holyrics-repertoire-v1481.php',{
          method:'POST',cache:'no-store',credentials:'same-origin',
          headers:{'Content-Type':'application/json','Accept':'application/json'},
          body:JSON.stringify({action:'services',access_key:key})
        });
        var json=null;
        try { json=await response.json(); } catch(e) {}
        if(!response.ok || !json || json.error){
          var err=(json && json.error && json.error.message) || 'Resposta sem JSON';
          message.style.color='#b91c1c';
          message.textContent='Falha HTTP '+response.status+': '+err+'. Se HTTP 401, valide ou renove a chave. Se HTTP 500, existe erro no servidor; consulte os logs PHP.';
        }else if(!json.data || !Array.isArray(json.data.services)){
          message.style.color='#b91c1c';
          message.textContent='A API autenticou, mas devolveu um formato inesperado.';
        }else{
          message.style.color='#166534';
          message.textContent='✓ Consulta autorizada e funcionamento do servidor confirmado. '+json.data.services.length+' culto(s) publicado(s) encontrado(s). Se só falhar no Holyrics, a causa está no envio HTTP ou na configuração local do programa.';
        }
      }catch(err){
        message.style.color='#b91c1c';
        message.textContent='Falha de rede do navegador: '+(err.message||'erro de conexão');
      }finally{
        input.value='';
        btn.disabled=false;
      }
    });

"""
js = js.replace(anchor, extra+anchor,1)
(root / 'holyrics-copy-script-v1486.js').write_text(js,encoding='utf-8')

# Log errors with a reference visible to MASTER without revealing the SQL or secrets.
p=root/'api'/'holyrics-repertoire-v1481.php'
php=p.read_text(encoding='utf-8')
old="""    error_log('[Holyrics Connect] '.get_class($e).': '.$e->getMessage());
    out(['data'=>null,'error'=>['message'=>'Falha ao consultar repertório']],500);"""
new="""    $reference=bin2hex(random_bytes(4));
    error_log('[Holyrics Connect ref='.$reference.'] '.get_class($e).': '.$e->getMessage());
    out(['data'=>null,'error'=>['message'=>'Falha interna ao consultar repertório. Referência: '.$reference]],500);"""
assert php.count(old)==1
p.write_text(php.replace(old,new),encoding='utf-8')

p=root/'holyrics-connect.html'
h=p.read_text(encoding='utf-8')
for before,after in [
    ('holyrics-copy-script-v1485.js?v=1.4.85','holyrics-copy-script-v1486.js?v=1.4.86'),
    ('/Escala-de-Proposito-Holyrics.js?v=1.4.85','/Escala-de-Proposito-Holyrics.js?v=1.4.86'),
]:
    if h.count(before)!=1:raise RuntimeError('HTML anchor: '+before)
    h=h.replace(before,after,1)
p.write_text(h,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
    lambda m:m.group(1)+'?v=1.4.86'+m.group(2),h,count=1)
if n!=1:raise RuntimeError('main bundle tag not found')
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js',
             'whatsapp-group-settings-v1473.js','master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
    h=h.replace(name+'?v=1.4.85',name+'?v=1.4.86')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.86 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.86\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.86.md').write_text("""# Escala de Propósito v1.4.86 — Diagnóstico completo do Holyrics

- Corrige o botão Copiar código completo: a v1.4.85 servia o código v1.4.84 por engano.
- Atualiza o código Holyrics v1.0.5 e usa cache-busting ?v=1.4.86.
- Adiciona Testar chave + consulta de cultos na página de integração, usando a mesma API protegida e o token em um POST HTTPS sem expor a chave na URL.
- Distingue chave inválida (HTTP 401), erro de banco/servidor (HTTP 500 com referência nos logs) e bloqueio local do Holyrics.
- Melhora o texto do pedido de chave e grava erro no log do Holyrics sem mostrar a chave.
- Lembrete: Não escreva nomes de função em obj.description. Execute o item Script salvo no Holyrics.
- Preserva todas as funções existentes, os controles de acesso por igreja e a versão v1.4.85 como base.
- Não confirma conexão real com o computador até o teste local.
""",encoding='utf-8')
