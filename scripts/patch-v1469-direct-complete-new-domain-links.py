from pathlib import Path
import re

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

old='if(y&&pe){const leaderOwnDepartmentV1459=((Fe=pe.departamentos)==null?void 0:Fe.lider_id)===(e==null?void 0:e.id),ae=!ze&&(we||t==="lider"&&leaderOwnDepartmentV1459),canRemovePeopleV1459=!ze&&(we||leaderOwnDepartmentV1459);return r.jsx(fG,{escala:pe,voluntarios:g,onBack:()=>{b(null),Le()},canManage:ae,canRemovePeople:canRemovePeopleV1459,userId:e==null?void 0:e.id})}'
new='if(y&&pe){window.location.replace("/escala/"+encodeURIComponent(pe.id));return null}'
if s.count(old)!=1:
    raise SystemExit('intermediate branch anchor count='+str(s.count(old)))
s=s.replace(old,new,1)
asset.write_text(s,encoding='utf-8')

runtime_files=[
    root/'api'/'whatsapp_scale_message_v1421.php',
    root/'api'/'volunteer_menu_v1434.php',
    root/'api'/'volunteer_menu_v1435.php',
]
for p in runtime_files:
    txt=p.read_text(encoding='utf-8')
    if 'https://escala.isaacanthony.com.br' not in txt:
        raise SystemExit('old domain anchor not found in '+p.name)
    txt=txt.replace('https://escala.isaacanthony.com.br','https://escaladeproposito.com.br')
    p.write_text(txt,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\1?v=1.4.69\2',h,count=1)
if n!=1:
    raise SystemExit('main asset script tag not found')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw='/* escala-version:1.4.69 */\n'+sw
p.write_text(sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.69\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.69.md').write_text('''# Escala de Propósito v1.4.69 — Escala Completa direta e domínio oficial nos links

- Remove definitivamente o uso da tela intermediária de departamento dentro de /escalas.
- Se qualquer fluxo antigo ainda selecionar um departamento internamente, o sistema redireciona imediatamente para /escala/{id}.
- O clique no departamento, chips e lápis continuam levando para a Escala Completa.
- Atualiza os links enviados pelo WhatsApp/notificações para o domínio oficial https://escaladeproposito.com.br.
- Corrige o link de confirmação da escala gerado por whatsapp_scale_message_v1421.php.
- Corrige os links de PDF da escala enviados pelo menu do voluntário v1434 e v1435.
- Mantém apenas a lista de domínios antigos no Master Comercial para detectar configurações legadas e sugerir a migração; ela não é usada para enviar links aos clientes.
- Adiciona cache-bust v1.4.69 e marca o service worker para evitar bundle antigo em cache.
''',encoding='utf-8')
