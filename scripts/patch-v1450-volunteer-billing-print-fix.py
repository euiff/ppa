from pathlib import Path

root=Path('pkg')

def rep(s,old,new,label):
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: {c}')
    return s.replace(old,new,1)

# Planos/Pagamentos: somente responsável financeiro.
p=root/'subscription-guard.js'
s=p.read_text(encoding='utf-8')
old="if(s.status==='master'){if(!document.getElementById('saas-master')){const a=document.createElement('a');a.id='saas-master';a.className='saas-pill';a.href='/master-pagamentos.html';a.textContent='💳 Planos & Pagamentos';document.body.appendChild(a)}return}"
new="if(!s.billing_owner){const bm=document.getElementById('saas-master');bm&&bm.remove();const bt=document.getElementById('saas-trial');bt&&bt.remove()}if(s.status==='master'&&s.billing_owner){if(!document.getElementById('saas-master')){const a=document.createElement('a');a.id='saas-master';a.className='saas-pill';a.href='/master-pagamentos.html';a.textContent='💳 Planos & Pagamentos';document.body.appendChild(a)}return}"
s=rep(s,old,new,'billing owner button')
p.write_text(s,encoding='utf-8')

# Página do Culto: devolver ID real da escala para atalhos clássicos.
p=root/'api'/'ministerial-hub.php'
s=p.read_text(encoding='utf-8')
old="return['church'=>mh_church($ig),'base'=>['data'=>$date,'culto_id'=>$culto,'culto_nome'=>$scales[0]['culto_nome'],'horario'=>$scales[0]['horario']],'summary'=>$summary"
new="return['church'=>mh_church($ig),'base'=>['id'=>$scales[0]['id'],'data'=>$date,'culto_id'=>$culto,'culto_nome'=>$scales[0]['culto_nome'],'horario'=>$scales[0]['horario']],'summary'=>$summary"
s=rep(s,old,new,'service base id')
p.write_text(s,encoding='utf-8')

# Bundle principal.
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

# Restaura o nome e o comportamento familiar de Escala completa.
old='href:`/culto?data=${encodeURIComponent(ve.data||"")}&culto_id=${encodeURIComponent((ve.culto&&ve.culto.id)||"")}`,className:"inline-flex items-center justify-center rounded-xl bg-primary text-primary-foreground px-3 py-2 text-xs font-bold hover:opacity-90",onClick:ce=>ce.stopPropagation(),children:"Página do culto"'
new='href:`/escala/${encodeURIComponent((Ne[0]&&Ne[0].id)||"")}`,className:"inline-flex items-center justify-center rounded-xl bg-primary text-primary-foreground px-3 py-2 text-xs font-bold hover:opacity-90",onClick:ce=>ce.stopPropagation(),children:"Escala completa"'
s=rep(s,old,new,'scale complete button')

# Impressão: abre a janela imediatamente no clique para não ser bloqueada pelo Chrome.
old='G=async()=>{var pe,q,oe,xe,ge;try{const ke=te(),Fe=await printSongs(),ae='
new='G=async()=>{var pe,q,oe,xe,ge;const De=window.open("","_blank","width=1100,height=800");if(!De){V.error("Permita pop-ups para imprimir a escala.");return}try{De.document.title="Preparando impressão";De.document.body.innerHTML="<p style=\\\"font-family:Arial;padding:24px\\\">Preparando impressão da escala...</p>";const ke=te(),Fe=await printSongs(),ae='
s=rep(s,old,new,'print early popup')
old=',De=window.open("","_blank","width=1100,height=800");if(!De){V.error("Permita pop-ups para imprimir a escala.");return}const Ne='
s=rep(s,old,';const Ne=','remove late popup')
s=rep(s,'De.document.write(`<!doctype html>','De.document.open(),De.document.write(`<!doctype html>','print document reset')

# PDF clássico: download explícito por Blob, preservando o conteúdo/layout já existente.
old='Ue.save(`escala-${l.data}-${String(((ke=l.cultos)==null?void 0:ke.nome)||"culto").replace(/[^a-z0-9]+/gi,"-").toLowerCase()}.pdf`),V.success(Ne.length?"PDF gerado no modelo de impressão com escala e repertório!":"PDF gerado no modelo de impressão. O culto ainda não possui músicas no repertório.")'
new='(()=>{const He=`escala-${l.data}-${String(((ke=l.cultos)==null?void 0:ke.nome)||"culto").replace(/[^a-z0-9]+/gi,"-").toLowerCase()}.pdf`,We=Ue.output("blob"),nt=URL.createObjectURL(We),Ct=document.createElement("a");Ct.href=nt,Ct.download=He,Ct.style.display="none",document.body.appendChild(Ct),Ct.click(),Ct.remove(),setTimeout(()=>URL.revokeObjectURL(nt),3e3)})(),V.success(Ne.length?"PDF gerado no modelo de impressão com escala e repertório!":"PDF gerado no modelo de impressão. O culto ainda não possui músicas no repertório.")'
s=rep(s,old,new,'pdf blob download')
asset.write_text(s,encoding='utf-8')

(root/'VERSION').write_text('1.4.50\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.50.md').write_text('''# Escala de Propósito v1.4.50

- Remove o botão flutuante **Planos & Pagamentos** da área do voluntário. Ele só aparece para o usuário realmente responsável pelo faturamento da igreja (Master/Pastor/Admin autorizado).
- Na página **Escalas**, o botão volta a se chamar **Escala completa**, como o pessoal já estava acostumado.
- **Escala completa** abre diretamente a escala completa daquele culto/data.
- Corrige a Página do Culto para carregar o **ID real da escala**; antes o atalho de impressão/PDF podia apontar para `/escala/undefined`.
- Corrige **Imprimir** na Escala Completa: a janela é aberta imediatamente no clique antes de carregar o repertório, evitando o bloqueio de pop-up do Chrome.
- Corrige **Baixar PDF** usando download direto por arquivo Blob, mantendo o mesmo PDF clássico.
- O desenho antigo permanece: **A4**, tabela **Departamento | Função | Voluntário | Situação**, departamentos em ordem alfabética e funções em ordem alfabética/numérica natural.
- Não altera dados, escalados, confirmações, repertório, WhatsApp ou permissões existentes.
''',encoding='utf-8')
