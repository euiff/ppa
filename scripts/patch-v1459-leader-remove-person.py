from pathlib import Path
root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1: raise SystemExit(f'{label}: anchor count={c}')
    s=s.replace(old,new,1)

old='if(y&&pe){const ae=!ze&&(we||t==="lider"&&((Fe=pe.departamentos)==null?void 0:Fe.lider_id)===(e==null?void 0:e.id));return r.jsx(fG,{escala:pe,voluntarios:g,onBack:()=>{b(null),Le()},canManage:ae,userId:e==null?void 0:e.id})}'
new='if(y&&pe){const leaderOwnDepartmentV1459=((Fe=pe.departamentos)==null?void 0:Fe.lider_id)===(e==null?void 0:e.id),ae=!ze&&(we||t==="lider"&&leaderOwnDepartmentV1459),canRemovePeopleV1459=!ze&&(we||leaderOwnDepartmentV1459);return r.jsx(fG,{escala:pe,voluntarios:g,onBack:()=>{b(null),Le()},canManage:ae,canRemovePeople:canRemovePeopleV1459,userId:e==null?void 0:e.id})}'
rep(old,new,'caller permission')

old='fG=({escala:e,voluntarios:t,onBack:n,canManage:s,userId:a})=>{'
new='fG=({escala:e,voluntarios:t,onBack:n,canManage:s,canRemovePeople:canRemovePeopleV1459,userId:a})=>{'
rep(old,new,'detail signature')

old='$t=async ce=>{const{error:me}=await I.from("escala_itens").delete().eq("id",ce);if(me){V.error(me.message);return}V.success("Voluntário removido!"),Le()}'
new='$t=async ce=>{if(!canRemovePeopleV1459){V.error("Você não tem permissão para remover pessoas desta escala");return}const removeItemV1459=i.find(removeRowV1459=>removeRowV1459.id===ce),removeNameV1459=removeItemV1459&&removeItemV1459.profiles&&removeItemV1459.profiles.nome||"este voluntário",removeRoleV1459=removeItemV1459&&removeItemV1459.funcao||"esta função";if(!window.confirm(`Remover ${removeNameV1459} da escala?\\n\\nFunção: ${removeRoleV1459}\\n\\nIsso remove a pessoa somente desta escala.`))return;const{error:me}=await I.from("escala_itens").delete().eq("id",ce);if(me){V.error(me.message);return}V.success(`${removeNameV1459} foi removido(a) desta escala.`),Le()}'
rep(old,new,'remove guard')

old='s&&r.jsx(ie,{size:"icon",variant:"ghost",className:"h-6 w-6",onClick:()=>$t(ce.id),children:r.jsx(Ss,{className:"w-3 h-3 text-destructive"})})'
new='canRemovePeopleV1459&&r.jsx(ie,{size:"icon",variant:"ghost",className:"h-6 w-6 hover:bg-destructive/10",title:"Remover esta pessoa da escala",\"aria-label\":\"Remover pessoa da escala\",onClick:()=>$t(ce.id),children:r.jsx(Ss,{className:"w-3 h-3 text-destructive"})})'
rep(old,new,'trash render')

asset.write_text(s,encoding='utf-8')
(root/'VERSION').write_text('1.4.59\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.59.md').write_text('''# Escala de Propósito v1.4.59 — Líder pode remover pessoas da própria escala

- O líder responsável por um departamento passa a ver a **lixeira** ao lado das pessoas escaladas naquele departamento.
- A permissão é validada pelo `lider_id` do departamento: o líder só remove pessoas das escalas do **departamento que ele lidera**.
- A lixeira não depende apenas do rótulo do cargo; o sistema confere a liderança cadastrada no próprio departamento.
- No modo **Voluntário**, a lixeira continua escondida. Ela aparece no modo de gestão do líder.
- Antes de remover, o sistema pede confirmação mostrando o **nome da pessoa e a função**.
- A remoção tira a pessoa **somente daquela escala**; não remove o voluntário do departamento nem do cadastro da igreja.
- Em departamentos que ele não lidera, a lixeira não aparece para esse líder.
- Pastor/Admin/Master mantêm as permissões já existentes.
- Não altera data, horário, nome do culto, repertório, PDF ou outras partes da escala.
''',encoding='utf-8')
