from pathlib import Path
root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text('utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: count={c}')
    s=s.replace(old,new,1)

# 1) Manual add-department inside Scale Complete: detect same dept in same complete scale.
old='H=async()=>{if(!l||!T){V.error("Selecione o departamento");return}const pe=W.filter(ge=>ge.funcao.trim());O(!0);const{data:q,error:oe}=await I.from("escalas").insert({data:l.data,culto_id:l.culto_id,departamento_id:T,igreja_id:l.igreja_id,status:"rascunho",created_by:n==null?void 0:n.id,template_id:l.template_id,antecedencia_minutos:l.antecedencia_minutos}).select().maybeSingle();'
new='H=async()=>{var qDupName;if(!l||!T){V.error("Selecione o departamento");return}const dup=[{id:l.id,dept:l.departamentos},...b].find(ge=>ge&&ge.dept&&ge.dept.id===T);if(dup){const depName=((qDupName=C.find(ge=>ge.id===T))==null?void 0:qDupName.nome)||((dup.dept&&dup.dept.nome)||"este departamento"),choice=window.prompt(`⚠️ DEPARTAMENTO DUPLICADO\\n\\nO departamento "${depName}" já existe nesta escala de ${new Date(l.data+"T00:00:00").toLocaleDateString("pt-BR")}.\\n\\nDigite:\\n1 - Abrir o departamento que já existe\\n2 - Criar outro mesmo assim\\n0 - Cancelar`,"1");if(choice===null||choice.trim()===""||choice.trim()==="0"){V.info("Nenhum departamento duplicado foi criado.");return}if(choice.trim()==="1"){window.location.href=`/escala/${encodeURIComponent(dup.id)}`;return}if(choice.trim()!=="2"){V.warning("Opção inválida. Nenhum departamento foi criado.");return}if(!window.confirm(`Confirmar DUPLICAÇÃO de "${depName}" nesta mesma escala?\\n\\nUse somente se você realmente precisa de dois departamentos iguais.`))return}const pe=W.filter(ge=>ge.funcao.trim());O(!0);const{data:q,error:oe}=await I.from("escalas").insert({data:l.data,culto_id:l.culto_id,departamento_id:T,igreja_id:l.igreja_id,status:"rascunho",created_by:n==null?void 0:n.id,template_id:l.template_id,antecedencia_minutos:l.antecedencia_minutos}).select().maybeSingle();'
rep(old,new,'manual dept duplicate guard')

# 2) Template synchronization: compare against ALL existing depts in same date/cult, not only rows from template.
old='const ae={};ke.forEach(Ne=>{const Ue=`${Ne.data}|${Ne.culto_id||""}`;ae[Ue]||(ae[Ue]={data:Ne.data,culto_id:Ne.culto_id,depts:new Set}),ae[Ue].depts.add(Ne.departamento_id)});const ve=[];if(Object.values(ae).forEach(Ne=>{xe.forEach(Ue=>{Ne.depts.has(Ue.departamento_id)||ve.push({data:Ne.data,culto_id:Ne.culto_id,departamento_id:Ue.departamento_id,created_by:e==null?void 0:e.id,igreja_id:n,template_id:q.id})})}),ve.length===0){oe||V.info("As escalas geradas já estão atualizadas com o template.");return}'
new='const ae={};ke.forEach(Ne=>{const Ue=`${Ne.data}|${Ne.culto_id||""}`;ae[Ue]||(ae[Ue]={data:Ne.data,culto_id:Ne.culto_id})});const dates=[...new Set(ke.map(Ne=>Ne.data))],{data:allExisting}=dates.length?await I.from("escalas").select("id, data, culto_id, departamento_id").eq("igreja_id",n).in("data",dates):{data:[]},existingDeptKeys=new Set((allExisting||[]).map(Ne=>`${Ne.data}|${Ne.culto_id||""}|${Ne.departamento_id||""}`)),ve=[];let duplicateSkipped=0;if(Object.values(ae).forEach(Ne=>{xe.forEach(Ue=>{const key=`${Ne.data}|${Ne.culto_id||""}|${Ue.departamento_id}`;existingDeptKeys.has(key)?duplicateSkipped++:(ve.push({data:Ne.data,culto_id:Ne.culto_id,departamento_id:Ue.departamento_id,created_by:e==null?void 0:e.id,igreja_id:n,template_id:q.id}),existingDeptKeys.add(key))})}),ve.length===0){duplicateSkipped>0?V.warning(`${duplicateSkipped} departamento(s) não foram adicionados porque já existem nessas escalas.`):oe||V.info("As escalas geradas já estão atualizadas com o template.");return}'
rep(old,new,'template sync duplicate guard')

# Add warning after successful sync when duplicates were skipped.
old='V.success(`${ve.length} departamento(s) adicionado(s) às escalas já geradas!`)},tt=q=>'
new='V.success(`${ve.length} departamento(s) adicionado(s) às escalas já geradas!`),duplicateSkipped>0&&V.warning(`${duplicateSkipped} duplicado(s) foram ignorados porque o departamento já existia na escala.`)},tt=q=>'
rep(old,new,'template sync duplicate notice')

# 3) Scale generation: before inserting each complete scale/date, query existing same date+cult.
old='const xe=y.recorrente||(De=N.find(Ne=>Ne.id===oe))!=null&&De.recorrente?y.semanas:1,ge={};F.forEach(Ne=>{ge[Ne.departamento_id]||(ge[Ne.departamento_id]=[])}),q.forEach(Ne=>{ge[Ne.departamento_id].push(Ne)});let ke=0,Fe=0;const ae=F.length-q.length,ve=new Date(y.data+"T12:00:00");for(let Ne=0;Ne<xe;Ne++){const Ue=new Date(ve);Ue.setDate(ve.getDate()+Ne*7);const $e=Ue.toISOString().split("T")[0];for(const[_t,Ie]of Object.entries(ge)){'
new='const xe=y.recorrente||(De=N.find(Ne=>Ne.id===oe))!=null&&De.recorrente?y.semanas:1,ge={};F.forEach(Ne=>{ge[Ne.departamento_id]||(ge[Ne.departamento_id]=[])}),q.forEach(Ne=>{ge[Ne.departamento_id].push(Ne)});let ke=0,Fe=0,dupDates=0;const ae=F.length-q.length,ve=new Date(y.data+"T12:00:00");for(let Ne=0;Ne<xe;Ne++){const Ue=new Date(ve);Ue.setDate(ve.getDate()+Ne*7);const $e=Ue.toISOString().split("T")[0];let exQuery=I.from("escalas").select("id, departamento_id").eq("igreja_id",n).eq("data",$e);oe?exQuery=exQuery.eq("culto_id",oe):exQuery=exQuery.is("culto_id",null);const{data:existingScaleRows,error:existingScaleErr}=await exQuery;if(existingScaleErr){V.error(`Não foi possível conferir duplicidade em ${$e}: ${existingScaleErr.message}`);continue}if(existingScaleRows&&existingScaleRows.length){const cultoLabel=y.novo_culto?y.culto_nome.trim():((N.find(r=>r.id===oe)||{}).nome||"Culto"),depNames=existingScaleRows.map(r=>G(r.departamento_id)).filter(Boolean),answer=window.confirm(`⚠️ ESCALA JÁ EXISTE\\n\\nJá existe "${cultoLabel}" em ${new Date($e+"T00:00:00").toLocaleDateString("pt-BR")} com ${existingScaleRows.length} departamento(s)${depNames.length?`:\\n• ${depNames.join("\\n• ")}`:""}.\\n\\nOK = criar outra escala DUPLICADA mesmo assim\\nCancelar = não duplicar esta data`);if(!answer){dupDates++;continue}}for(const[_t,Ie]of Object.entries(ge)){'
rep(old,new,'complete scale duplicate guard')

# Update final success message to mention skipped duplicate dates.
old='V.success(`${Fe} escala(s) gerada(s) com ${ke} voluntário(s)`+(ae>0?` • ${ae} vaga(s) em aberto para o líder preencher`:"!")),S(!1),'
new='V.success(`${Fe} escala(s) gerada(s) com ${ke} voluntário(s)`+(ae>0?` • ${ae} vaga(s) em aberto para o líder preencher`:"!")+(dupDates>0?` • ${dupDates} data(s) duplicada(s) foram ignoradas`:"")),S(!1),'
rep(old,new,'generation duplicate summary')

asset.write_text(s,encoding='utf-8')
(root/'VERSION').write_text('1.4.57\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.57.md').write_text('''# Escala de Propósito v1.4.57 — Proteção contra escalas e departamentos duplicados

- Ao adicionar um departamento pela **Escala Completa**, o sistema verifica se o mesmo departamento já existe naquela igreja + data + culto.
- Se já existir, aparece um aviso com três caminhos: **1 Abrir o departamento existente**, **2 Criar outro mesmo assim**, **0 Cancelar**.
- A opção de criar duplicado exige uma segunda confirmação explícita para evitar clique acidental.
- Ao **Gerar Escala** por template, o sistema verifica antes se já existe uma escala do mesmo culto na mesma data.
- Se a escala já existir, mostra **ESCALA JÁ EXISTE** com os departamentos encontrados. Só cria outra escala duplicada se o usuário confirmar conscientemente.
- Se cancelar o aviso, aquela data é ignorada e as demais datas recorrentes continuam normalmente.
- A sincronização de templates agora compara com **todos os departamentos já existentes** no mesmo culto/data, inclusive os criados manualmente ou por outro template, evitando duplicação silenciosa.
- Quando a sincronização encontra duplicados, ela os ignora e avisa quantos foram evitados.
- Nenhum duplicado antigo é apagado automaticamente; a versão evita novas duplicações e mantém a opção consciente de duplicar quando realmente necessário.
''',encoding='utf-8')
print(asset)
