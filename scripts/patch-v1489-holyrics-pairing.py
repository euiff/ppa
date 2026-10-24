from pathlib import Path
import re

root=Path('pkg')
(root/'api'/'holyrics-pairing-v1489.php').write_text(
    Path('runtime/v1489/api/holyrics-pairing-v1489.php').read_text(encoding='utf-8'),
    encoding='utf-8'
)

p=root/'api'/'holyrics-connect-v1481.php'
s=p.read_text(encoding='utf-8')
needle="require_once __DIR__.'/holyrics-core-v1481.php';"
assert s.count(needle)==1
s=s.replace(needle,needle+"\nrequire_once __DIR__.'/holyrics-pairing-v1489.php';")
needle="    if($action==='verify'){"
assert s.count(needle)==1
s=s.replace(needle,"""    if($action==='pair_start'){
        if(($_SERVER['REQUEST_METHOD']??'GET')!=='POST')
            out(['data'=>null,'error'=>['message'=>'Use POST para gerar o código']],405);
        $issued=edp_pair_issue($church);
        out(['data'=>$issued,'error'=>null]);
    }
"""+needle,1)
p.write_text(s,encoding='utf-8')

p=root/'api'/'holyrics-repertoire-v1481.php'
s=p.read_text(encoding='utf-8')
needle="require_once __DIR__.'/holyrics-core-v1481.php';"
assert s.count(needle)==1
s=s.replace(needle,needle+"\nrequire_once __DIR__.'/holyrics-pairing-v1489.php';",1)
needle="    if($action==='health')out(['data'=>['health'=>'ok','version'=>'1.4.84'],'error'=>null]);"
assert s.count(needle)==1
s=s.replace(needle,"""    if($action==='health')out(['data'=>['health'=>'ok','version'=>'1.4.89'],'error'=>null]);
    if($action==='pair'){
        if($method!=='POST')out(['data'=>null,'error'=>['message'=>'Pareamento exige POST HTTPS']],405);
        $paired=edp_pair_redeem((string)($payload['pairing_code']??''));
        if(isset($paired['error']))out(['data'=>null,'error'=>['message'=>$paired['error']]],401);
        out(['data'=>$paired,'error'=>null]);
    }""",1)
p.write_text(s,encoding='utf-8')

p=root/'Escala-de-Proposito-Holyrics.js'
s=p.read_text(encoding='utf-8')
assert 'V1.0.7' in s
s=s.replace('V1.0.7','V1.0.8').replace('v1.0.7','v1.0.8')
begin=s.index('    var token = normalizeKey(h.restore(storageKey));')
end=s.index('\n    // Holyrics permite requisições HTTPS', begin)
s=s[:begin]+"""    // Pareamento seguro: o operador informa APENAS 12 caracteres,
    // em vez de colar uma chave de 64 caracteres que o Holyrics pode cortar.
    function pairNow() {
        var entered = h.input('Digite o código de conexão do Holyrics (12 caracteres, gerado no portal)');
        if (entered == null) return null;
        var code = String(entered).toUpperCase().replace(/[\s-]+/g, '');
        if (!/^[A-HJ-NP-Z2-9]{12}$/.test(code)) {
            throw new Error('Código inválido: use o código de 12 caracteres gerado no portal, não a chave longa.');
        }
        var raw = h.apiRequest(base, {
            type: 'POST',
            headers: {'Content-Type':'application/json','Accept':'application/json'},
            data: JSON.stringify({action:'pair',pairing_code:code}),
            timeout: 20000,
            response_data_type: 'string;utf-8'
        });
        if (raw == null) {
            throw new Error('Não foi possível validar o código no servidor. Verifique o acesso HTTPS e tente novamente.');
        }
        var response;
        try { response = (typeof raw === 'object' && raw.data) ? raw : JSON.parse(String(raw)); }
        catch(e) { throw new Error('Resposta inválida do servidor ao conectar o Holyrics.'); }
        if (!response || response.error) {
            throw new Error((response && response.error && response.error.message) || 'Código expirado ou já utilizado. Gere outro código no portal.');
        }
        var newToken = normalizeKey(response.data && response.data.access_key);
        if (!keyIsValid(newToken)) {
            throw new Error('O servidor não retornou a credencial segura esperada.');
        }
        h.store(storageKey, newToken);
        return newToken;
    }
    var token = normalizeKey(h.restore(storageKey));
    if (!keyIsValid(token)) {
        try { token = pairNow(); }
        catch(e) { h.error('Escala de Propósito: ' + String(e.message || e)); return; }
        if (token == null) return;
    }
""" + s[end:]

begin=s.index('            // A instância Holyrics pode ter guardado uma chave antiga depois')
end=s.index('\n        }\n        var payload;',begin)
s=s[:begin]+"""            // Uma credencial antiga pode ter sido revogada quando outra foi criada.
            // O novo código curto permite reconectar sem copiar 64 caracteres.
            var fresh = pairNow();
            if (fresh == null) {
                throw new Error('O computador não está autenticado. Gere um código de conexão no portal e execute novamente. ' +
                    (reason ? 'Detalhe: ' + reason : ''));
            }
            token = fresh;
            raw = authorizedRequest(action, serviceId);
            if (raw == null) {
                throw new Error('Computador conectado pelo código, mas a consulta autenticada ainda falhou. ' +
                    (lastErrorSafe() || 'Verifique a API no site.'));
            }"""+s[end:]
p.write_text(s,encoding='utf-8')

p=root/'holyrics-connect.html'
s=p.read_text(encoding='utf-8')
needle='<script src="/holyrics-copy-script-v1488.js?v=1.4.88" defer></script>'
if s.count(needle)!=1:raise RuntimeError('Missing installer script')
s=s.replace(needle,'<script src="/holyrics-copy-script-v1489.js?v=1.4.89" defer></script>' +
 '<script src="/holyrics-pair-ui-v1489.js?v=1.4.89" defer></script>')
needle='/Escala-de-Proposito-Holyrics.js?v=1.4.88'
assert s.count(needle)==1
s=s.replace(needle,'/Escala-de-Proposito-Holyrics.js?v=1.4.89')
s=s.replace('Conectado / chave ativa','Chave criada (não confirma computador conectado)')
p.write_text(s,encoding='utf-8')

oldjs=root/'holyrics-copy-script-v1488.js'
s=oldjs.read_text(encoding='utf-8')
s=s.replace("var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.88';",
            "var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.89';")
s=s.replace('v1488','v1489').replace('v1.4.88','v1.4.89')
s=s.replace('Conexão corrigida para o Holyrics:', 'Conexão por código curto (12 caracteres):')
s=s.replace('A nova versão lê também as chaves que o Holyrics devolve como texto Java. Ele pedirá sua confirmação antes de salvar a chave copiada.',
            'Não é mais necessário digitar ou copiar a chave longa. Gere um código de conexão temporário na etapa 1 e digite esse código no Holyrics. O computador será conectado automaticamente.')
(root/'holyrics-copy-script-v1489.js').write_text(s,encoding='utf-8')
oldjs.unlink()
(root/'holyrics-pair-ui-v1489.js').write_text(
    Path('runtime/v1489/holyrics-pair-ui-v1489.js').read_text(encoding='utf-8'),
    encoding='utf-8'
)

p=root/'sistema.html'
s=p.read_text(encoding='utf-8')
s,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
            lambda m:m.group(1)+'?v=1.4.89'+m.group(2),s,count=1)
if n!=1:raise RuntimeError('Main JS asset missing')
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js',
             'whatsapp-group-settings-v1473.js','master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
    s=s.replace(name+'?v=1.4.88',name+'?v=1.4.89')
p.write_text(s,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.89 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.89\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.89.md').write_text("""# Escala de Propósito v1.4.89 — Pareamento simples com Holyrics

- Novo fluxo: clique em **Gerar código de conexão** na Integração Holyrics do Escala de Propósito.
- Digite somente 12 letras/números no Holyrics. O código vence em 10 minutos e só pode ser usado uma vez.
- O servidor devolve ao Holyrics a chave forte de 64 caracteres por HTTPS, sem exigir entrada manual.
- O código curto é gerado com 60 bits de aleatoriedade e o banco salva somente seu hash.
- A conexão bem-sucedida substitui a chave anterior da igreja, inclusive a exibida em capturas de tela.
- A chave antiga continua ativa até que o computador conclua o pareamento, evitando interrupção prematura.
- A consulta ao repertório e a inclusão de músicas continuam funcionando da mesma maneira.
- Continua possível gerar uma chave manual pelo painel, mas o método recomendado é o código curto.
- A atualização do site não modifica automaticamente o script salvo no Holyrics do computador: substitua o código do script uma vez.
- Mantém escalas, voluntários, WhatsApp, notificações e todas as funções existentes.
""",encoding='utf-8')
