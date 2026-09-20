from pathlib import Path
root=Path('pkg')
php=root/'api'/'ministerial-hub.php'
html=root/'gestao-ministerial.html'

p=php.read_text(encoding='utf-8')
old="foreach($rows as&$r){$r['departamentos']=$deps[$r['id']]??'';$n=(int)$r['cultos'];if($n===0)$r['faixa']='Sem escala';elseif($avg>0&&$n>=3&&$n>$avg*1.5)$r['faixa']='Carga alta';elseif($avg>=2&&$n<$avg*.5)$r['faixa']='Carga baixa';else$r['faixa']='Equilibrado';}$r=null;"
new="foreach($rows as&$r){$r['departamentos']=$deps[$r['id']]??'';$n=(int)$r['cultos'];if($n===0)$r['faixa']='Sem escala';elseif($avg>0&&$n>=3&&$n>$avg*1.5)$r['faixa']='Carga alta';elseif($avg>=2&&$n<$avg*.5)$r['faixa']='Carga baixa';else$r['faixa']='Equilibrado';}unset($r);$rows=array_values(array_filter($rows,static fn($x)=>is_array($x)&&isset($x['id'])));"
if p.count(old)!=1: raise SystemExit(f'php anchor={p.count(old)}')
p=p.replace(old,new,1)
php.write_text(p,encoding='utf-8')

s=html.read_text(encoding='utf-8')
old="let balanceData=null;function renderBalance(){const d=balanceData,q=(document.getElementById('bsearch')?.value||'').toLocaleLowerCase('pt-BR'),dep=(document.getElementById('bdep')?.value||'all');const deps=[...new Set(d.people.flatMap(p=>(p.departamentos||'').split(' • ').filter(Boolean)))].sort((a,b)=>a.localeCompare(b,'pt-BR'));"
new="let balanceData=null;function balancePeople(d){return(Array.isArray(d&&d.people)?d.people:[]).filter(p=>p&&typeof p==='object')}function renderBalance(){const d=balanceData||{},people=balancePeople(d),q=(document.getElementById('bsearch')?.value||'').toLocaleLowerCase('pt-BR'),dep=(document.getElementById('bdep')?.value||'all');const deps=[...new Set(people.flatMap(p=>(p.departamentos||'').split(' • ').filter(Boolean)))].sort((a,b)=>a.localeCompare(b,'pt-BR',{numeric:true,sensitivity:'base'}));"
if s.count(old)!=1: raise SystemExit(f'js start anchor={s.count(old)}')
s=s.replace(old,new,1)
s=s.replace("const rows=d.people.filter(p=>", "const rows=people.filter(p=>",1)
s=s.replace("const max=Math.max(1,...d.people.map(p=>Number(p.cultos||0)));", "const max=Math.max(1,...people.map(p=>Number(p.cultos||0)));",1)

old="async function balance(){const from=Q.get('from')||'',to=Q.get('to')||'';balanceData=await api('balance',{from,to});const d=balanceData;app.className='';app.innerHTML=hero('Equilíbrio da equipe','Veja quantas vezes cada pessoa serviu no período e identifique facilmente sobrecarga ou pouca participação.')+nav('balance')+`<div class=\"grid stats\">${stat(d.people.length,'Pessoas')}"
new="async function balance(){const from=Q.get('from')||'',to=Q.get('to')||'';balanceData=await api('balance',{from,to});const d=balanceData,people=balancePeople(d);app.className='';app.innerHTML=hero('Equilíbrio da equipe','Veja quantas vezes cada pessoa serviu no período e identifique facilmente sobrecarga ou pouca participação.')+nav('balance')+`<div class=\"grid stats\">${stat(people.length,'Pessoas')}"
if s.count(old)!=1: raise SystemExit(f'balance anchor={s.count(old)}')
s=s.replace(old,new,1)

old="<button class=\"btn primary\" onclick=\"showTab('impressao');setTimeout(()=>window.print(),100)\">Imprimir / Salvar PDF</button>"
new="<button class=\"btn primary\" onclick=\"top.location.href='/escala/'+encodeURIComponent(b.id)\">Imprimir / PDF — modelo clássico</button>"
if s.count(old)!=1: raise SystemExit(f'print button anchor={s.count(old)}')
s=s.replace(old,new,1)

old="<section id=\"tab-impressao\" class=\"tabpage\"><div class=\"printbox\"><div style=\"text-align:center;margin-bottom:20px\"><h1 style=\"margin:0\">${esc(d.church.nome)}</h1><h2 style=\"margin:6px 0\">${esc(b.culto_nome)}</h2><div>${date(b.data)} ${time(b.horario)}</div></div><h2>ESCALA COMPLETA</h2>${scaleHtml(d,true)}<h2 style=\"margin-top:24px\">REPERTÓRIO</h2>${d.songs.length?d.songs.map((x,i)=>`<div>${i+1}. <b>${esc(x.titulo)}</b>${x.artista?' — '+esc(x.artista):''}${x.tom?' (Tom: '+esc(x.tom)+')':''}</div>`).join(''):'<div>Nenhuma música cadastrada.</div>'}</div></section>"
new="<section id=\"tab-impressao\" class=\"tabpage\"><div class=\"card\"><h2 style=\"margin-top:0\">Impressão / PDF</h2><p>Para manter exatamente o modelo antigo da Escala Completa, com A4, tabela e a ordenação já existente, use o botão abaixo. Você será levado ao mesmo gerador clássico de impressão e PDF.</p><button class=\"btn primary\" onclick=\"top.location.href='/escala/'+encodeURIComponent(b.id)\">Abrir Escala Completa — impressão/PDF</button></div></section>"
if s.count(old)!=1: raise SystemExit(f'print tab anchor={s.count(old)}')
s=s.replace(old,new,1)
html.write_text(s,encoding='utf-8')

(root/'VERSION').write_text('1.4.49\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.49.md').write_text('''# Escala de Propósito v1.4.49\n\n- Corrige o erro **can\'t access property "departamentos", p is null** em **Equilíbrio da equipe**.\n- Corrige a causa no PHP: a última pessoa do relatório não é mais transformada em `null`.\n- Adiciona proteção no frontend para registros incompletos não derrubarem a tela.\n- A nova **Página do Culto** não usa mais um segundo modelo de impressão.\n- **Imprimir / PDF** leva para a própria **Escala Completa**, preservando exatamente o gerador antigo já existente.\n- O modelo antigo continua em **A4 retrato**, tabela **Departamento | Função | Voluntário | Situação**, com departamentos em ordem alfabética e funções em ordem alfabética/numérica natural.\n- O sistema tenta manter o conteúdo em uma folha A4 quando couber; se houver conteúdo demais, continua sem cortar as linhas da tabela.\n- Os botões antigos **Imprimir** e **Baixar PDF** da Escala Completa permanecem intactos.\n''',encoding='utf-8')
