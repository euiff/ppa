from pathlib import Path
import re

root = Path("pkg")
(root / "Escala-de-Proposito-Holyrics-Modulo.js").write_text(
    Path("runtime/v1492/Escala-de-Proposito-Holyrics-Modulo.js").read_text(encoding="utf-8"),
    encoding="utf-8",
)
(root / "holyrics-module-generator-v1492.js").write_text(
    Path("runtime/v1492/holyrics-module-generator-v1492.js").read_text(encoding="utf-8"),
    encoding="utf-8",
)

p = root / "api" / "holyrics-connect-v1481.php"
api = p.read_text(encoding="utf-8")
anchor = "    if($action==='ready_script'){"
assert api.count(anchor) == 1, "Holyrics authorized endpoint anchor not found"
module_action = """    if($action==='ready_module'){
        // A seleção de igreja e as permissões MASTER/ADMIN/PASTOR são
        // verificadas neste endpoint antes de chegar a este bloco.
        // Gerar exclusivamente em POST autenticado, sem cache HTTP.
        if(($_SERVER['REQUEST_METHOD']??'GET')!=='POST')
            out(['data'=>null,'error'=>['message'=>'Use POST para gerar o módulo.']],405);
        $templatePath=dirname(__DIR__).'/Escala-de-Proposito-Holyrics-Modulo.js';
        $source=@file_get_contents($templatePath);
        $marker='ESCALA_MODULO_TOKEN_SUBSTITUIR_NO_SERVIDOR';
        if(!is_string($source)||substr_count($source,$marker)!==1||
           !str_contains($source,'function info()')||
           !str_contains($source,'function actions(module)')||
           !str_contains($source,'AddLyricsToPlaylist')){
            out(['data'=>null,'error'=>['message'=>'Modelo de módulo Holyrics não instalado ou incompleto.']],500);
        }
        $newToken=bin2hex(random_bytes(32));
        $personalized=str_replace($marker,$newToken,$source);
        $q=db()->prepare('INSERT INTO holyrics_integracoes (igreja_id,token_hash,ativo,atualizado_em)
            VALUES (?,?,1,NOW()) ON DUPLICATE KEY UPDATE
            token_hash=VALUES(token_hash),ativo=1,atualizado_em=NOW()');
        $q->execute([$church,hash('sha256',$newToken)]);
        header('Cache-Control: private, no-store, no-cache, must-revalidate');
        header('Pragma: no-cache');
        header('X-Content-Type-Options: nosniff');
        out(['data'=>[
            'igreja'=>$name,
            'module'=>$personalized,
            'module_version'=>'v1.2.0',
            'configured'=>true,
            'warning'=>'A credencial antiga desta igreja foi substituída. Atualize os outros computadores.'
        ],'error'=>null]);
    }
"""
api = api.replace(anchor, module_action + anchor, 1)
p.write_text(api,encoding="utf-8")

p = root / "holyrics-connect.html"
html=p.read_text(encoding="utf-8")
tag='<script src="/holyrics-ready-v1491.js?v=1.4.91" defer></script>'
assert html.count(tag)==1, "Old ready script tag not found"
html=html.replace(tag,tag+'<script src="/holyrics-module-generator-v1492.js?v=1.4.92" defer></script>',1)
p.write_text(html,encoding="utf-8")

p=root/"sistema.html"
html=p.read_text(encoding="utf-8")
html,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
    lambda m: m.group(1)+"?v=1.4.92"+m.group(2),html,count=1)
assert n==1,"Main JS bundle script not found"
for name in ["holyrics-entry-v1481.js","app-notifications-v1465.js",
             "whatsapp-group-settings-v1473.js","master-whatsapp-groups-entry-v1475.js",
             "cron-fix-v1478.js"]:
    html=html.replace(name+"?v=1.4.91",name+"?v=1.4.92")
p.write_text(html,encoding="utf-8")

p=root/"sw.js"
sw=p.read_text(encoding="utf-8")
sw=re.sub(r"^/\* escala-version:[^*]+\*/\n?","",sw,count=1)
p.write_text("/* escala-version:1.4.92 */\n"+sw,encoding="utf-8")
(root/"VERSION").write_text("1.4.92\n",encoding="utf-8")

(root/"ATUALIZACAO-v1.4.92.md").write_text("""# Escala de Propósito v1.4.92 — Módulo Holyrics por igreja

- **Novo caminho recomendado:** na Integração Holyrics, escolha a igreja e clique em **Gerar e copiar módulo Holyrics**.
- O servidor retorna um módulo completo, baseado no modelo oficial de Módulos do Holyrics (funções \`info()\` e \`actions(module)\`), com credencial privada daquela igreja já configurada.
- O módulo disponibiliza a ação **Importar repertório da escala**, que lista os cultos publicados, pesquisa as músicas e as adiciona à playlist do Holyrics.
- Não é necessário criar ou editar item de Script ou utilizar **Ação (Receptor)**, ambiente que estava rejeitando o salvamento com \`scriptAction\`.
- Para instalar, abra **Ferramentas → Módulos → Adicionar módulo** no Holyrics 2.23 ou mais recente, cole o código completo e ative o módulo.
- Geração segura: MASTER/ADMIN/PASTOR da igreja autorizada; token novo de 64 caracteres só no corpo de resposta HTTPS privada, nunca na URL ou em arquivo público; banco grava apenas hash.
- Gerar novamente revoga a chave antiga APENAS daquela igreja. Computadores que usam a chave antiga precisarão receber o módulo novo.
- O modo antigo de Script continua disponível dentro de **Opções antigas (avançado)** para compatibilidade.
- Nenhuma alteração no funcionamento de escalas, voluntários, WhatsApp, CRON ou notificações.
- A aceitação do módulo na interface gráfica real do Holyrics ainda precisa ser testada; testes automatizados validam a estrutura, a sintaxe e a importação simulada.
""",encoding="utf-8")
