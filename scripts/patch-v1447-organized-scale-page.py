from pathlib import Path

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label} anchor count={c}')
    s=s.replace(old,new,1)

anchor='},ae.id)};if(y&&pe){'
insert='''},ae.id)},groupScaleCardsV1447=ae=>{const ve=new Map;(ae||[]).forEach(De=>{const Ne=`${De.data||""}|${De.culto_id||"sem-culto"}`;ve.has(Ne)||ve.set(Ne,{key:Ne,data:De.data||"",culto:De.cultos||null,rows:[]}),ve.get(Ne).rows.push(De)});return Array.from(ve.values()).map(De=>({...De,rows:De.rows.slice().sort((Ne,Ue)=>String((Ne.departamentos&&Ne.departamentos.nome)||"").localeCompare(String((Ue.departamentos&&Ue.departamentos.nome)||""),"pt-BR",{numeric:!0,sensitivity:"base"}))})).sort((De,Ne)=>{const Ue=String(De.data||"").localeCompare(String(Ne.data||""));if(Ue!==0)return Ue;const $e=String((De.culto&&De.culto.horario)||"").localeCompare(String((Ne.culto&&Ne.culto.horario)||""));return $e!==0?$e:String((De.culto&&De.culto.nome)||"").localeCompare(String((Ne.culto&&Ne.culto.nome)||""),"pt-BR",{numeric:!0,sensitivity:"base"})})},renderScaleGroupsV1447=ae=>groupScaleCardsV1447(ae).map((ve,De)=>{const Ne=ve.rows||[],Ue=Ne.reduce((ce,me)=>ce+((me.itens||[]).length),0),$e=Ne.reduce((ce,me)=>ce+(me.itens||[]).filter($=>$.status_confirmacao==="confirmado").length,0),_t=Ne.length>0&&Ne.every(ce=>ce.status==="publicado"),Ie=Ne.some(ce=>ce.status==="publicado"),it=((ve.culto&&ve.culto.nome)||"Culto").replace(/\\s\\d{2}:\\d{2}$/,""),ce=ve.culto&&ve.culto.horario?String(ve.culto.horario).slice(0,5):"",me=ve.data?new Date(ve.data+"T00:00:00").toLocaleDateString("pt-BR",{weekday:"short",day:"2-digit",month:"2-digit"}):"";return r.jsx(Nt.div,{initial:{opacity:0,y:4},animate:{opacity:1,y:0},transition:{delay:De*.025},children:r.jsxs("details",{className:"group rounded-2xl border border-border bg-card shadow-sm overflow-hidden open:shadow-md open:border-primary/25 transition-all",children:[r.jsxs("summary",{className:"list-none cursor-pointer select-none p-4 sm:p-5 flex items-start justify-between gap-3 hover:bg-secondary/30 transition-colors [&::-webkit-details-marker]:hidden",children:[r.jsxs("div",{className:"flex items-start gap-3 min-w-0 flex-1",children:[r.jsx("div",{className:"w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0",children:r.jsx(Xs,{className:"w-5 h-5"})}),r.jsxs("div",{className:"min-w-0 flex-1",children:[r.jsxs("div",{className:"flex flex-wrap items-center gap-2",children:[r.jsxs("h3",{className:"font-black text-base sm:text-lg text-foreground leading-tight",children:["Escala de ",it]}),r.jsx(ht,{variant:_t?"default":"secondary",className:`text-[9px] uppercase font-bold ${_t?"bg-status-confirmed/10 text-status-confirmed":""}`,children:_t?"Publicada":Ie?"Parcial":"Rascunho"})]}),r.jsxs("div",{className:"flex flex-wrap gap-x-3 gap-y-1 mt-1.5 text-xs text-muted-foreground",children:[r.jsxs("span",{className:"font-bold text-foreground",children:[r.jsx(fo,{className:"w-3.5 h-3.5 inline mr-1"}),me]}),ce&&r.jsxs("span",{children:[r.jsx(Nn,{className:"w-3.5 h-3.5 inline mr-1"}),ce]}),r.jsxs("span",{children:[Ne.length," departamento",Ne.length===1?"":"s"]}),r.jsxs("span",{children:[Ue," pessoa",Ue===1?"":"s"]}),Ue>0&&r.jsxs("span",{className:"text-status-confirmed font-semibold",children:[$e," confirmado",$e===1?"":"s"]})]}),r.jsx("p",{className:"text-[11px] text-muted-foreground mt-2",children:"Clique para abrir os departamentos e ver as informações desta escala."})]})]}),r.jsx(kd,{className:"w-5 h-5 text-muted-foreground shrink-0 mt-2 transition-transform group-open:rotate-90"})]}),r.jsxs("div",{className:"border-t border-border bg-secondary/10 p-3 sm:p-4 space-y-3",children:[r.jsxs("div",{className:"flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1",children:[r.jsxs("div",{children:[r.jsx("p",{className:"text-sm font-bold text-foreground",children:"Departamentos desta escala"}),r.jsxs("p",{className:"text-[11px] text-muted-foreground",children:["Organizados em ordem alfabética • ",Ne.length," departamento",Ne.length===1?"":"s"]})]}),r.jsx("div",{className:"flex flex-wrap gap-1.5",children:Ne.map(ce=>r.jsx(ht,{variant:"outline",className:"text-[10px] bg-background",children:(ce.departamentos&&ce.departamentos.nome)||"Departamento"},ce.id))})]}),r.jsx("div",{className:"space-y-2",children:Ne.map((ce,me)=>ke(ce,me))})]})]})},ve.key)});if(y&&pe){'''
rep(anchor,insert,'group renderer')
rep('Gerencie as escalas de cultos','Escalas organizadas por culto, data e departamentos','subtitle')
rep('children:Kt.length+tn.length','children:groupScaleCardsV1447(Kt).length+groupScaleCardsV1447(tn).length','filter result count')
rep('Yt.map((ae,ve)=>ke(ae,ve))','renderScaleGroupsV1447(Yt)','calendar grouped render')
rep('children:["(",Kt.length,")"]','children:["(",groupScaleCardsV1447(Kt).length,")"]','future tab count')
rep('children:["(",tn.length,")"]','children:["(",groupScaleCardsV1447(tn).length,")"]','past tab count')
rep('Kt.map((ae,ve)=>ke(ae,ve))','renderScaleGroupsV1447(Kt)','future grouped render')
rep('tn.map((ae,ve)=>ke(ae,ve))','renderScaleGroupsV1447(tn)','past grouped render')

asset.write_text(s,encoding='utf-8')
(root/'VERSION').write_text('1.4.47\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.47.md').write_text('''# Escala de Propósito v1.4.47

- Reorganiza a página **Escalas** para exibir primeiro uma **escala completa por culto e data**, em vez de misturar cada departamento como se fosse uma escala diferente.
- Exemplo: aparece **Escala de Culto da Família — 20/09 — 19:00**. Ao clicar, são exibidos todos os departamentos daquela escala.
- Dentro de cada escala completa, os departamentos ficam em **ordem alfabética** e continuam com acesso aos detalhes, voluntários, funções, edição, publicação, impressão e PDF já existentes.
- O cabeçalho da escala mostra de forma simples: **data, horário, quantidade de departamentos, quantidade de pessoas, confirmações e situação da escala**.
- Mantém separados cultos diferentes no mesmo dia. Exemplo: **Culto** e **Culto da Família** em 20/09 aparecem como duas escalas completas independentes.
- A organização também é aplicada nas abas **Próximas**, **Anteriores** e na visualização por **Calendário**.
- Os contadores e resultados dos filtros passam a contar as **escalas completas por culto/data**, deixando a tela mais fácil de entender.
- Não altera dados existentes nem as regras de permissões, WhatsApp, PDF, impressão ou geração da escala.
''',encoding='utf-8')
