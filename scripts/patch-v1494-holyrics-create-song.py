from pathlib import Path
import re

root=Path('pkg')
(root/'Escala-de-Proposito-Holyrics-Modulo.js').write_text(
    Path('runtime/v1494/Escala-de-Proposito-Holyrics-Modulo.js').read_text(encoding='utf-8'),
    encoding='utf-8'
)
(root/'api'/'holyrics-core-v1481.php').write_text(
    Path('runtime/v1494/api/holyrics-core-v1481.php').read_text(encoding='utf-8'),
    encoding='utf-8'
)

p=root/'api'/'holyrics-connect-v1481.php'
s=p.read_text(encoding='utf-8')
old="'module_version'=>'v1.3.0'"
if s.count(old)!=1:raise RuntimeError('Holyrics module version missing')
p.write_text(s.replace(old,"'module_version'=>'v1.4.0'",1),encoding='utf-8')

oldUi=root/'holyrics-module-generator-v1492.js'
ui=oldUi.read_text(encoding='utf-8')
ui=ui.replace('v1492','v1494')
needle="'<p style=\"font-size:13px;margin:12px 0 0\"><b>Instalação única no Holyrics:</b>"
if ui.count(needle)!=1:raise RuntimeError('UI instruction anchor missing')
ui=ui.replace(needle,
    """'<p style="font-size:13px;margin:10px 0 0"><b>Novidade:</b> músicas já cadastradas entram na lista; se faltar uma música e houver letra no Escala de Propósito, o Holyrics abre o cadastro preenchido. Sem letra disponível, você poderá colar uma letra autorizada para concluir o cadastro.</p>'+"""
    +"\n      "+needle,1)
(root/'holyrics-module-generator-v1494.js').write_text(ui,encoding='utf-8')
oldUi.unlink()

p=root/'holyrics-connect.html'
h=p.read_text(encoding='utf-8')
needle='/holyrics-module-generator-v1492.js?v=1.4.93'
if h.count(needle)!=1:raise RuntimeError('Module generator script reference missing')
h=h.replace(needle,'/holyrics-module-generator-v1494.js?v=1.4.94',1)
p.write_text(h,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
 lambda m:m.group(1)+'?v=1.4.94'+m.group(2),h,count=1)
if n!=1:raise RuntimeError('Main asset missing')
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js',
 'whatsapp-group-settings-v1473.js','master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
 h=h.replace(name+'?v=1.4.93',name+'?v=1.4.94')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.94 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.94\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.94.md').write_text("""# Escala de Propósito v1.4.94 — Cadastro assistido de músicas no Holyrics gratuito

- Importa para a playlist as músicas que já estão cadastradas no Holyrics.
- Se uma música ainda não existe, usa a API oficial popupCreateSong do Holyrics para abrir o cadastro, preenchendo título, artista, tom e letra, quando disponíveis.
- Após o operador conferir e salvar, o módulo recebe o ID gerado e adiciona a música automaticamente à playlist, antes de continuar para a próxima.
- O fluxo abre apenas uma janela de cadastro por vez, respeitando a limitação do Holyrics.
- Se a própria biblioteca de músicas do Escala de Propósito já possui uma coluna de letra (letra, letras, lyrics ou letra_musica), o endpoint passa esse texto ao módulo na consulta autenticada, sem fontes externas.
- Se não houver letra, o operador pode colar sua letra autorizada no Holyrics; se cancelar, a música fica pendente e as outras seguem.
- Não faz download automático de letras de páginas de terceiros; o título da música, sozinho, não fornece o conteúdo para apresentação.
- Os resultados informam separadamente músicas adicionadas, cadastradas, sem letra, canceladas e falhas.
- O Holyrics 2.24+ pode usar popupCreateSong gratuitamente; não depende do recurso CreateItem, que requer Holyrics Plan.
- Não modifica os módulos de escalas, voluntários, WhatsApp, notificações ou CRON.
- Para instalar no computador, atualize o site e gere novamente o módulo exclusivo de cada igreja; gerar um novo módulo revoga a chave antiga da igreja, afetando outras instalações até que sejam atualizadas.
- A execução do módulo no Holyrics real precisa ser confirmada; os testes de CI apenas verificam fluxos simulados e sintaxe.
""",encoding='utf-8')
