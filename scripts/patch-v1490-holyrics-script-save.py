from pathlib import Path
import re
root=Path('pkg')
p=root/'Escala-de-Proposito-Holyrics.js'
s=p.read_text(encoding='utf-8')
assert 'v1.0.8' in s, 'Expected v1.0.8 Holyrics module'
pattern=r'\n/\* Ação \(Receptor\):[^\n]*\n(?:[^\n]*\n)*?function scriptAction\(obj\) \{\n    return foo\(\);\n\}\s*$'
s2,n=re.subn(pattern,'\n',s,count=1)
if n!=1:
  # simpler anchored based on end of file rather than depending on comment wrapping
  pattern2=r'\n/\* Ação \(Receptor\):[\s\S]+?function scriptAction\(obj\) \{\s*return foo\(\);\s*\}\s*$'
  s2,n=re.subn(pattern2,'\n',s,count=1)
if n!=1:raise RuntimeError('Legacy receiver wrapper missing; review source before publishing')
s=s2
s=s.replace('v1.0.8','v1.0.9').replace('V1.0.8','V1.0.9')
s=s.replace('Compatível com testes do tipo Script e do tipo Ação (Receptor).',
  'Use o menu Scripts/Favoritos do Holyrics. A tela de teste Ação (Receptor) não é necessária.')
s=s.replace('No editor JavaScript clique Testar → Salvar.','No editor JavaScript clique Salvar.')
p.write_text(s,encoding='utf-8')

p=root/'holyrics-connect.html'
h=p.read_text(encoding='utf-8')
old='holyrics-copy-script-v1489.js?v=1.4.89'
assert h.count(old)==1
h=h.replace(old,'holyrics-copy-script-v1490.js?v=1.4.90')
old='holyrics-pair-ui-v1489.js?v=1.4.89'
assert h.count(old)==1
h=h.replace(old,'holyrics-pair-ui-v1490.js?v=1.4.90')
old='/Escala-de-Proposito-Holyrics.js?v=1.4.89'
assert h.count(old)==1
h=h.replace(old,'/Escala-de-Proposito-Holyrics.js?v=1.4.90')
p.write_text(h,encoding='utf-8')

p=root/'holyrics-copy-script-v1489.js'
copy=p.read_text(encoding='utf-8')
old='holyrics-copy-script-v1489.js' # module includes this in comment only possibly
copy=copy.replace("var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.89';",
                  "var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.90';")
copy=copy.replace('v1489','v1490').replace('v1.4.89','v1.4.90')
anchor="    download.insertAdjacentElement('afterend', block);"
assert copy.count(anchor)==1
copy=copy.replace(anchor,anchor+"""
    var saveHelp=document.createElement('p');
    saveHelp.style.cssText='background:#fff4d9;border:1px solid #f0d28c;border-radius:8px;padding:10px;font-size:12px;line-height:1.6';
    saveHelp.textContent='IMPORTANTE: No Holyrics, abra Ferramentas > Diversos > Script e crie/edite um item Script. Cole o código no painel da ESQUERDA e clique em Salvar (sem usar o botão Testar – Ação/Receptor). Essa versão não inclui a função scriptAction, que provocava o erro “Valor inválido — Não encontrado”. O painel direito Funções adicionais pode permanecer como está.';
    block.insertAdjacentElement('afterbegin',saveHelp);
""",1)
(root/'holyrics-copy-script-v1490.js').write_text(copy,encoding='utf-8')
p.unlink()

p=root/'holyrics-pair-ui-v1489.js'
s=p.read_text(encoding='utf-8').replace('v1489','v1490')
(root/'holyrics-pair-ui-v1490.js').write_text(s,encoding='utf-8')
p.unlink()

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
     lambda m: m.group(1)+'?v=1.4.90'+m.group(2),h,count=1)
assert n==1
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js','whatsapp-group-settings-v1473.js',
             'master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
  h=h.replace(name+'?v=1.4.89',name+'?v=1.4.90')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.90 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.90\n',encoding='utf-8')

(root/'ATUALIZACAO-v1.4.90.md').write_text("""# Escala de Propósito v1.4.90 — Corrigir salvamento do script no Holyrics

- Retirado do script destinado ao menu Scripts o método extra scriptAction(obj) usado anteriormente como adaptador do teste Ação (Receptor). 
- A função principal foo() permanece e executa a importação do repertório; o fluxo de conexão por código curto continua ativo.
- A página Integração Holyrics agora orienta abrir/criar um item em Ferramentas → Diversos → Script, colar o código no painel esquerdo e clicar diretamente em Salvar, sem usar o teste de Receptor.
- Os botões do portal baixam e copiam o novo script v1.0.9, com controle de cache ?v=1.4.90.
- Nenhuma alteração nos voluntários, escalas, WhatsApp ou agendamento de lembretes.
- Requer substituir uma vez o código no computador após atualizar o portal.
- Importante: os testes automatizados não confirmam a aceitação do salvamento na interface gráfica real do Holyrics.
""",encoding='utf-8')
