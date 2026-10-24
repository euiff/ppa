from pathlib import Path
import re

root=Path('pkg')
(root/'Escala-de-Proposito-Holyrics-Modulo.js').write_text(
    Path('runtime/v1493/Escala-de-Proposito-Holyrics-Modulo.js').read_text(encoding='utf-8'),
    encoding='utf-8'
)
p=root/'api'/'holyrics-connect-v1481.php'
s=p.read_text(encoding='utf-8')
old="'module_version'=>'v1.2.0'"
if s.count(old)!=1:raise RuntimeError('module version missing')
s=s.replace(old,"'module_version'=>'v1.3.0'",1)
p.write_text(s,encoding='utf-8')

p=root/'holyrics-connect.html'
h=p.read_text(encoding='utf-8')
needle='/holyrics-module-generator-v1492.js?v=1.4.92'
if h.count(needle)!=1:raise RuntimeError('module JS link missing')
h=h.replace(needle,'/holyrics-module-generator-v1492.js?v=1.4.93',1)
p.write_text(h,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
    lambda m:m.group(1)+'?v=1.4.93'+m.group(2),h,count=1)
if n!=1:raise RuntimeError('Frontend bundle anchor missing')
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js',
 'whatsapp-group-settings-v1473.js','master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
    h=h.replace(name+'?v=1.4.92',name+'?v=1.4.93')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.93 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.93\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.93.md').write_text("""# Escala de Propósito v1.4.93 — Holyrics: biblioteca de letras e títulos

- A conexão existente já lista os cultos e os títulos do repertório da igreja.
- O módulo Holyrics v1.3 agora verifica se há letras cadastradas na biblioteca do programa (API oficial GetSongs).
- Se a biblioteca estiver vazia, explica que é preciso adicionar letras no Holyrics. Não diz mais "Importadas 0 de 3" como se a conexão tivesse falhado.
- Faz comparação segura por títulos e variações: remove acentos e pontuação e reconhece títulos com nomes alternativos entre parênteses, como "Oceanos" / "Oceanos (Onde Meus Pés Podem Falhar)".
- Nunca escolhe automaticamente uma versão aproximada ou quando houver mais de um resultado; o operador confirma a versão.
- Adiciona à playlist apenas letras já cadastradas no próprio Holyrics; não inventa ou baixa letras de músicas de terceiros.
- Retorna resultado separado: adicionadas, não encontradas, seleção cancelada ou erro ao adicionar.
- Para obter o novo módulo no computador, vá à Integração Holyrics, gere e copie novamente o módulo da igreja e substitua o antigo. Gerar novamente revoga a credencial anterior da igreja, portanto outros computadores com o módulo antigo precisarão atualizar.
- Mantém todas as funcionalidades de escalas, voluntários, WhatsApp, lembretes, CRON e permissões.
""",encoding='utf-8')
