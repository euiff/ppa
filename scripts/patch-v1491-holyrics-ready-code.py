from pathlib import Path
import re

root=Path('pkg')

(root/'Escala-de-Proposito-Holyrics-Pronto.js').write_text(
    Path('runtime/v1491/Escala-de-Proposito-Holyrics-Pronto.js').read_text(encoding='utf-8'),
    encoding='utf-8'
)
(root/'holyrics-ready-v1491.js').write_text(
    Path('runtime/v1491/holyrics-ready-v1491.js').read_text(encoding='utf-8'),
    encoding='utf-8'
)

p=root/'api'/'holyrics-connect-v1481.php'
s=p.read_text(encoding='utf-8')
anchor="    if($action==='rotate'){"
new="""    if($action==='ready_script'){
        // Authorized user role and church scope are checked before this point.
        // Fresh script via authenticated POST only. No credentials in URLs.
        $templatePath=dirname(__DIR__).'/Escala-de-Proposito-Holyrics-Pronto.js';
        $template=@file_get_contents($templatePath);
        $marker='ESCALA_TOKEN_SUBSTITUIR_NO_SERVIDOR';
        if(!is_string($template)||substr_count($template,$marker)!==1||
           !str_contains($template,'function foo()')||
           !str_contains($template,'AddLyricsToPlaylist')){
            out(['data'=>null,'error'=>['message'=>'Modelo de integração Holyrics não instalado ou incompleto.']],500);
        }
        $newToken=bin2hex(random_bytes(32));
        $script=str_replace($marker,$newToken,$template);
        $q=db()->prepare('INSERT INTO holyrics_integracoes (igreja_id,token_hash,ativo,atualizado_em)
            VALUES (?,?,1,NOW())
            ON DUPLICATE KEY UPDATE token_hash=VALUES(token_hash),ativo=1,atualizado_em=NOW()');
        $q->execute([$church,hash('sha256',$newToken)]);
        out(['data'=>[
           'igreja'=>$name,
           'configured'=>true,
           'script'=>$script,
           'script_version'=>'v1.1.0',
           'warning'=>'A chave antiga desta igreja foi revogada. Guarde o script com segurança e atualize instalações anteriores.'
        ],'error'=>null]);
    }
"""
if s.count(anchor)!=1:raise RuntimeError('Cannot add ready_script endpoint')
s=s.replace(anchor,new+anchor,1)
p.write_text(s,encoding='utf-8')

p=root/'holyrics-connect.html'
s=p.read_text(encoding='utf-8')
needle='<script src="/holyrics-pair-ui-v1490.js?v=1.4.90" defer></script>'
assert s.count(needle)==1, 'Existing pairing script tag missing'
s=s.replace(needle,needle+'<script src="/holyrics-ready-v1491.js?v=1.4.91" defer></script>',1)
s=s.replace("'Conectado / chave ativa'","'Chave configurada (conexão não verificada)'")
s=s.replace('Baixar script para Holyrics (.js)', 'Baixar script genérico (avançado)')
p.write_text(s,encoding='utf-8')

p=root/'sistema.html'
s=p.read_text(encoding='utf-8')
s,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
            lambda m:m.group(1)+'?v=1.4.91'+m.group(2),s,count=1)
assert n==1,'Missing frontend asset'
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js',
             'whatsapp-group-settings-v1473.js','master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
    s=s.replace(name+'?v=1.4.90',name+'?v=1.4.91')
p.write_text(s,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.91 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.91\n',encoding='utf-8')

(root/'ATUALIZACAO-v1.4.91.md').write_text("""# Escala de Propósito v1.4.91 — Holyrics: gerar e copiar script completo por igreja

- Novo botão **Gerar e copiar código completo** na integração Holyrics.
- O MASTER ou ADMIN/PASTOR da própria igreja gera o script completo com sua credencial inserida pelo servidor.
- Não precisa digitar chave longa ou código temporário; basta colar todo o código no editor do tipo Script do Holyrics e clicar Salvar.
- O script possui somente a função principal foo(); não usa scriptAction nem a janela de teste Ação (Receptor).
- Compatível com GET autenticado e fallback POST HTTPS quando a hospedagem descarta cabeçalhos.
- A credencial forte (256 bits) fica apenas no script retornado ao administrador, nunca em arquivo público ou URL. O banco guarda somente seu hash.
- Gerar novamente revoga a chave anterior somente daquela igreja. Outros computadores precisam receber o código novo.
- O site oferece download do script privado e cópia manual se o navegador bloquear a área de transferência.
- Mantém as funções anteriores de escalas, grupos, WhatsApp, CRON e repertórios.
- A instalação/execução real no Holyrics precisa ser confirmada; testes de CI não substituem teste gráfico.
""",encoding='utf-8')
