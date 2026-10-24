from pathlib import Path
import re
root=Path('pkg')
(root/'Escala-de-Proposito-Holyrics-Modulo.js').write_text(
 Path('runtime/v1495/Escala-de-Proposito-Holyrics-Modulo.js').read_text(encoding='utf-8'),
 encoding='utf-8')
p=root/'api'/'holyrics-connect-v1481.php'
s=p.read_text(encoding='utf-8')
old="'module_version'=>'v1.4.0'"
if s.count(old)!=1:raise RuntimeError('Module version anchor missing')
p.write_text(s.replace(old,"'module_version'=>'v1.5.0'",1),encoding='utf-8')
p=root/'holyrics-module-generator-v1494.js'
ui=p.read_text(encoding='utf-8')
ui=ui.replace('v1494','v1495')
before="músicas já cadastradas entram na lista; se faltar uma música e houver letra no Escala de Propósito, o Holyrics abre o cadastro preenchido. Sem letra disponível, você poderá colar uma letra autorizada para concluir o cadastro."
after="um clique sincroniza músicas cadastradas. Se faltar uma e houver letra autorizada no Escala, o módulo tenta criar automaticamente no Holyrics Plan. No Holyrics gratuito, abre o cadastro preenchido para você revisar e salvar. O botão Cadastrar letras ausentes permite fornecer letras autorizadas."
if ui.count(before)!=1:raise RuntimeError('UI description anchor missing')
ui=ui.replace(before,after,1)
(root/'holyrics-module-generator-v1495.js').write_text(ui,encoding='utf-8')
p.unlink()
p=root/'holyrics-connect.html'
h=p.read_text(encoding='utf-8')
old='/holyrics-module-generator-v1494.js?v=1.4.94'
if h.count(old)!=1:raise RuntimeError('Module UI tag missing')
h=h.replace(old,'/holyrics-module-generator-v1495.js?v=1.4.95',1)
p.write_text(h,encoding='utf-8')
p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
  lambda m:m.group(1)+'?v=1.4.95'+m.group(2),h,count=1)
if n!=1:raise RuntimeError('Main JS bundle anchor missing')
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js',
 'whatsapp-group-settings-v1473.js','master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
 h=h.replace(name+'?v=1.4.94',name+'?v=1.4.95')
p.write_text(h,encoding='utf-8')
p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.95 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.95\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.95.md').write_text("""# Escala de Propósito v1.4.95 — Sincronização automática e criação conforme licença

- Ação Sincronizar repertório automaticamente: recebe os títulos do culto e adiciona letras existentes no Holyrics, sem confirmação adicional.
- Música ausente com letra autorizada salva no Escala de Propósito: tenta CreateSong, permitido somente com Holyrics Plan e permissão do módulo. Quando permitido, cria em segundo plano e adiciona à playlist.
- No Holyrics gratuito, a API oficial não permite criar músicas silenciosamente: usa popupCreateSong com letra preenchida para revisão e confirmação do salvamento.
- Não abre várias janelas ao mesmo tempo: somente uma por vez.
- Sem letra disponível, o título fica pendente. A nova ação Cadastrar letras ausentes (assistido) aceita uma letra que o operador tenha autorização para utilizar.
- Versões ambíguas devem ser escolhidas pelo operador.
- Não tenta contornar recursos pagos nem obtém letras de fontes de terceiros sem permissão. Um erro de licença bloqueia novas tentativas naquela execução.
- Mostra contagens de músicas criadas em segundo plano, cadastradas e adicionadas.
- Mantém todas as funções de escalas, voluntários, WhatsApp, lembretes e CRON.
- Após atualizar o site, gere o novo módulo da igreja. Isto revoga a credencial anterior e exige atualizar outros computadores daquela igreja.
- Validado por simulações; ainda requer confirmação na instalação real do Holyrics.
""",encoding='utf-8')
