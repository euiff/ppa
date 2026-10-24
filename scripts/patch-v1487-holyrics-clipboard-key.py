from pathlib import Path
import re

root=Path('pkg')
(root/'Escala-de-Proposito-Holyrics.js').write_text(
    Path('runtime/v1487/Escala-de-Proposito-Holyrics.js').read_text(encoding='utf-8'),
    encoding='utf-8'
)

old=root/'holyrics-copy-script-v1486.js'
content=old.read_text(encoding='utf-8')
old_url="var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.86';"
new_url="var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.87';"
if content.count(old_url)!=1:raise RuntimeError('installer URL anchor missing')
content=content.replace(old_url,new_url)
content=content.replace('v1486','v1487').replace('v1.4.86','v1.4.87')
anchor="    download.insertAdjacentElement('afterend', block);"
if content.count(anchor)!=1:raise RuntimeError('UI guidance anchor missing')
content=content.replace(anchor,anchor+"""
    var guide=document.createElement('div');
    guide.style.cssText='background:#eefbf3;border:1px solid #b8e3c7;border-radius:10px;margin:10px 0;padding:12px;line-height:1.5;font-size:13px';
    guide.innerHTML='<b>Forma mais fácil de conectar no Holyrics:</b> escolha a igreja no portal, clique em <b>Copiar chave</b> e só depois execute o script no Holyrics. O módulo detectará automaticamente a chave copiada (com sua confirmação), sem precisar digitá-la novamente. <b>Não cole a chave no campo obj.description.</b>';
    block.insertAdjacentElement('afterbegin',guide);
""",1)
(root/'holyrics-copy-script-v1487.js').write_text(content,encoding='utf-8')
old.unlink()

p=root/'holyrics-connect.html'
html=p.read_text(encoding='utf-8')
for old,new in [
    ('holyrics-copy-script-v1486.js?v=1.4.86','holyrics-copy-script-v1487.js?v=1.4.87'),
    ('/Escala-de-Proposito-Holyrics.js?v=1.4.86','/Escala-de-Proposito-Holyrics.js?v=1.4.87'),
]:
    if html.count(old)!=1: raise RuntimeError('HTML missing '+old)
    html=html.replace(old,new,1)
p.write_text(html,encoding='utf-8')

p=root/'sistema.html'
html=p.read_text(encoding='utf-8')
html,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
    lambda m:m.group(1)+'?v=1.4.87'+m.group(2),html,count=1)
if n!=1:raise RuntimeError('main JS tag missing')
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js','whatsapp-group-settings-v1473.js',
             'master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
    html=html.replace(name+'?v=1.4.86',name+'?v=1.4.87')
p.write_text(html,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.87 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.87\n',encoding='utf-8')

(root/'ATUALIZACAO-v1.4.87.md').write_text("""# Escala de Propósito v1.4.87 — Chave Holyrics por copiar e colar

- Corrige o erro "Formato de chave inválido" causado por chave antiga ou incompleta no computador.
- O script Holyrics v1.0.6 lê a chave diretamente da área de transferência, após confirmação do operador.
- Se a chave anterior salva falhar, detecta uma chave nova copiada do portal antes de pedir a digitação.
- Valida localmente que a chave contém 64 caracteres hexadecimais e nunca mostra seu conteúdo em alertas/logs.
- Mantém a autenticação por HTTPS e a consulta protegida aos cultos da v1.4.86.
- Na página de integração são exibidas instruções "Copiar chave > Executar script no Holyrics".
- NÃO muda outros recursos de escalas, notificações, WhatsApp nem a forma de publicar.
- ATENÇÃO: após atualizar o site, substitua uma vez o script antigo salvo no computador. A atualização do site não modifica arquivos locais do Holyrics.
""",encoding='utf-8')
