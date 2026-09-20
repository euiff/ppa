from pathlib import Path
root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))

# backend service null-ref fix
p=root/'api'/'ministerial-hub.php'
s=p.read_text(encoding='utf-8')
old="foreach($scales as&$s){$s['itens']=$by[$s['id']]??[];usort($s['itens'],static fn($a,$b)=>strnatcasecmp((string)$a['funcao'],(string)$b['funcao'])?:strnatcasecmp((string)$a['voluntario_nome'],(string)$b['voluntario_nome']));}$s=null;"
new="foreach($scales as&$s){$s['itens']=$by[$s['id']]??[];usort($s['itens'],static fn($a,$b)=>strnatcasecmp((string)$a['funcao'],(string)$b['funcao'])?:strnatcasecmp((string)$a['voluntario_nome'],(string)$b['voluntario_nome']));}unset($s);$scales=array_values(array_filter($scales,static fn($x)=>is_array($x)&&isset($x['id'])));"
if s.count(old)!=1: raise SystemExit('backend anchor '+str(s.count(old)))
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

# frontend defensive null filtering
p=root/'gestao-ministerial.html'
h=p.read_text(encoding='utf-8')
old="function confirmations(d){const all=d.departments.flatMap(x=>x.itens.map(i=>({...i,departamento_nome:x.departamento_nome})));const groups=['pendente','recusado','confirmado','ausente'];"
new="function confirmations(d){const all=(d.departments||[]).filter(Boolean).flatMap(x=>(x.itens||[]).filter(Boolean).map(i=>({...i,departamento_nome:x.departamento_nome||'Departamento'})));const groups=['pendente','recusado','confirmado','ausente'];"
if h.count(old)!=1: raise SystemExit('confirmations anchor '+str(h.count(old)))
h=h.replace(old,new,1)
old="function scaleHtml(d,print=false){return d.departments.map(dep=>`<section class=\"${print?'':'card '}dept\"><h3 class=\"${print?'print-dept':''}\">${esc(dep.departamento_nome||'Departamento')}</h3>${dep.itens.length?dep.itens.map(i=>`<div class=\"person\"><div><b>${esc(i.funcao)}</b></div><div>${esc(i.voluntario_nome||'Vaga não preenchida')}</div><div class=\"status ${i.status_confirmacao==='confirmado'?'ok':i.status_confirmacao==='recusado'?'bad':'warn'}\">${statusLabel(i.status_confirmacao)}</div></div>`).join(''):'<div class=\"empty\">Nenhum integrante nesta escala.</div>'}</section>`).join('')}"
new="function scaleHtml(d,print=false){return(d.departments||[]).filter(Boolean).map(dep=>{const itens=(dep.itens||[]).filter(Boolean);return `<section class=\"${print?'':'card '}dept\"><h3 class=\"${print?'print-dept':''}\">${esc(dep.departamento_nome||'Departamento')}</h3>${itens.length?itens.map(i=>`<div class=\"person\"><div><b>${esc(i.funcao||'—')}</b></div><div>${esc(i.voluntario_nome||'Vaga não preenchida')}</div><div class=\"status ${i.status_confirmacao==='confirmado'?'ok':i.status_confirmacao==='recusado'?'bad':'warn'}\">${statusLabel(i.status_confirmacao)}</div></div>`).join(''):'<div class=\"empty\">Nenhum integrante nesta escala.</div>'}</section>`}).join('')}"
if h.count(old)!=1: raise SystemExit('scaleHtml anchor '+str(h.count(old)))
h=h.replace(old,new,1)
p.write_text(h,encoding='utf-8')

# pencil becomes open full scale, no schedule metadata editing
p=asset
s=p.read_text(encoding='utf-8')
old='onClick:it=>{at.light(),xe(ae,it)},"aria-label":"Editar escala",children:r.jsx(_c,{className:"w-4 h-4 text-muted-foreground"})'
new='onClick:it=>{at.light(),it.stopPropagation(),b(ae.id)},"aria-label":"Abrir escala completa para editar pessoas",title:"Escala completa — editar pessoas",children:r.jsx(_c,{className:"w-4 h-4 text-muted-foreground"})'
if s.count(old)!=1: raise SystemExit('pencil anchor '+str(s.count(old)))
s=s.replace(old,new,1)
asset.write_text(s,encoding='utf-8')

(root/'VERSION').write_text('1.4.55\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.55.md').write_text('''# Escala de Propósito v1.4.55 — Página do Culto e escala imutável\n\n- Corrige o erro **can\'t access property "departamento_nome", dep is null** que aparecia em algumas Páginas do Culto.\n- Corrige a causa no PHP: o último departamento não é mais transformado em `null` após o `foreach`.\n- Adiciona proteção extra no frontend para ignorar departamentos/itens inválidos sem derrubar a Página do Culto.\n- O **lápis** dos cartões de departamento não abre mais edição de data, horário, culto ou departamento.\n- O lápis agora abre a **Escala Completa daquele departamento** para editar somente as pessoas/funções da escala.\n- Depois que uma escala é criada, **data, horário e nome do culto não são mais editados por esse botão**. Para mudar essas informações, a escala deve ser excluída e criada novamente.\n- O botão de excluir escala continua disponível.\n- Mantém Página do Culto, PDF direto, impressão, WhatsApp e demais funções das versões anteriores.\n''',encoding='utf-8')
