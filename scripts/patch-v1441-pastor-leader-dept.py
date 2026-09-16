from pathlib import Path
import re

root=Path('pkg')

# -----------------------------------------------------------------------------
# WhatsApp: confirmation/refusal goes to BOTH pastor/admin and department leader.
# -----------------------------------------------------------------------------
helper=root/'api'/'scale_response_notify_v1417.php'
s=helper.read_text(encoding='utf-8')

pat_rec=re.compile(r"function v1417_recipient\(array \$item\):\?array\{.*?\n\}", re.S)
rep_rec=r'''function v1441_recipients(array $item):array{
    $vol=(string)($item['voluntario_id']??'');
    $out=[];$seen=[];
    $add=function(string $id,string $kind)use(&$out,&$seen,$vol){
        if($id===''||$id===$vol)return;
        $p=v1417_profile($id);if(!$p||!v1417_valid_phone((string)($p['whatsapp']??'')))return;
        $dest=v1417_digits((string)$p['whatsapp']);if($dest===''||isset($seen[$dest]))return;
        $seen[$dest]=true;$p['_recipient_kind']=$kind;$out[]=$p;
    };
    /* O pastor/admin principal da igreja recebe sempre. */
    $add(v1417_admin_id((string)($item['igreja_id']??'')),'pastor');
    /* Se a escala tem departamento, o líder EXATAMENTE daquele departamento também recebe. */
    if((string)($item['departamento_id']??'')!==''){
        $leaderId=(string)($item['departamento_lider_id']??'');
        if($leaderId!=='')$add($leaderId,'lider_departamento');
        else v1417_trace('department_without_leader',['item'=>$item['item_id']??null,'departamento_id'=>$item['departamento_id']??null]);
    }
    return $out;
}
/* Compatibilidade com chamadas antigas: devolve o primeiro destinatário. */
function v1417_recipient(array $item):?array{$r=v1441_recipients($item);return$r[0]??null;}'''
s,n=pat_rec.subn(rep_rec,s,count=1)
if n!=1: raise SystemExit('recipient function not found')

pat_notify=re.compile(r"function v1417_notify_scale_response\(string \$itemId,string \$status,string \$source='whatsapp'\):array\{.*?\n\}\nfunction v1417_notify_refusal_reason", re.S)
rep_notify=r'''function v1417_notify_scale_response(string $itemId,string $status,string $source='whatsapp'):array{
    $item=v1417_item($itemId);if(!$item)return['ok'=>false,'reason'=>'item_not_found'];
    $dbStatus=(string)($item['status_confirmacao']??'');if(in_array($dbStatus,['confirmado','tarde','recusado'],true))$status=$dbStatus;
    if(!in_array($status,['confirmado','tarde','recusado'],true))return['ok'=>false,'reason'=>'invalid_status'];
    $tos=v1441_recipients($item);if(!$tos){v1417_trace('no_recipient',['item'=>$itemId,'status'=>$status]);return['ok'=>false,'reason'=>'pastor_and_leader_without_whatsapp'];}
    $confirmed=in_array($status,['confirmado','tarde'],true);
    $title=$confirmed?'✅ *Confirmação de escala*':'❌ *Indisponibilidade na escala*';
    $action=$confirmed?'confirmou presença na escala.':'informou que não poderá participar da escala.';
    $reason=trim((string)($item['justificativa_recusa']??''));
    $msg=$title."\n\n👤 *".($item['voluntario_nome']?:'Voluntário')."* ".$action.
        "\n📋 ".($item['culto_nome']?:'Culto').
        "\n📅 ".v1417_format_date((string)$item['data']).
        "\n🕒 ".substr((string)($item['horario']?:'--:--'),0,5).
        "\n⛪ ".($item['departamento_nome']?:'Sem departamento')." — ".$item['funcao'];
    if(!$confirmed&&$reason!=='')$msg.="\n💬 *Motivo:* ".$reason;
    if($status==='tarde')$msg.="\n⚠️ Confirmação registrada após o horário de início.";
    $msg.=$confirmed?"\n\nA resposta já foi registrada no *Escala de Propósito*.":"\n\n👉 *Ação:* abra a escala e escolha manualmente quem será escalado no lugar.\nA indisponibilidade já foi registrada no *Escala de Propósito*.";
    try{
        $results=[];$any=false;
        foreach($tos as $to){
            $dest=v1417_digits((string)$to['whatsapp']);$type='whatsapp_scale_response_leader';$kind=(string)($to['_recipient_kind']??'responsavel');
            if(v1417_recently_sent($itemId,$status,$dest,$type)){$results[]=['ok'=>true,'deduped'=>true,'recipient_id'=>$to['id']??null,'kind'=>$kind];$any=true;continue;}
            $res=v1424_send_logged_whatsapp($type,$dest,$msg,$item['igreja_id']?:null,[
                'escala_id'=>$item['escala_id'],'escala_item_id'=>$itemId,'voluntario_id'=>$item['voluntario_id'],
                'recipient_id'=>$to['id']??null,'recipient_name'=>$to['nome']??null,'recipient_kind'=>$kind,'status'=>$status,'source'=>$source,'v'=>'1.4.41'
            ]);
            $ok=is_array($res)?!empty($res['ok']):($res!==false);$any=$any||$ok;
            $results[]=['ok'=>$ok,'recipient_id'=>$to['id']??null,'recipient_name'=>$to['nome']??null,'kind'=>$kind];
            v1417_trace($ok?'sent':'failed',['item'=>$itemId,'status'=>$status,'recipient'=>$to['id']??null,'kind'=>$kind,'source'=>$source]);
        }
        return['ok'=>$any,'recipients'=>$results,'status'=>$status];
    }catch(Throwable $e){v1417_trace('exception',['item'=>$itemId,'message'=>substr($e->getMessage(),0,240)]);return['ok'=>false,'reason'=>'exception'];}
}
function v1417_notify_refusal_reason'''
s,n=pat_notify.subn(rep_notify,s,count=1)
if n!=1: raise SystemExit('notify function block not found')

pat_reason=re.compile(r"function v1417_notify_refusal_reason\(string \$itemId,string \$source='whatsapp'\):array\{.*?\n\}", re.S)
rep_reason=r'''function v1417_notify_refusal_reason(string $itemId,string $source='whatsapp'):array{
    $item=v1417_item($itemId);if(!$item)return['ok'=>false,'reason'=>'item_not_found'];
    $reason=trim((string)($item['justificativa_recusa']??''));if($reason==='')return['ok'=>false,'reason'=>'no_reason'];
    $tos=v1441_recipients($item);if(!$tos)return['ok'=>false,'reason'=>'pastor_and_leader_without_whatsapp'];
    $type='whatsapp_scale_refusal_reason_leader';$status='recusado_reason';
    $msg="📝 *Motivo da indisponibilidade*\n\n👤 *".($item['voluntario_nome']?:'Voluntário')."*\n📋 ".($item['culto_nome']?:'Culto')."\n📅 ".v1417_format_date((string)$item['data'])."\n⛪ ".($item['departamento_nome']?:'Sem departamento')." — ".$item['funcao']."\n💬 *Motivo:* ".$reason."\n\n👉 *Ação:* escolha manualmente na escala quem ficará no lugar deste voluntário.";
    try{
        $results=[];$any=false;
        foreach($tos as $to){
            $dest=v1417_digits((string)$to['whatsapp']);$kind=(string)($to['_recipient_kind']??'responsavel');
            if(v1417_recently_sent($itemId,$status,$dest,$type)){$results[]=['ok'=>true,'deduped'=>true,'recipient_id'=>$to['id']??null,'kind'=>$kind];$any=true;continue;}
            $res=v1424_send_logged_whatsapp($type,$dest,$msg,$item['igreja_id']?:null,[
                'escala_id'=>$item['escala_id'],'escala_item_id'=>$itemId,'voluntario_id'=>$item['voluntario_id'],
                'recipient_id'=>$to['id']??null,'recipient_kind'=>$kind,'status'=>$status,'source'=>$source,'v'=>'1.4.41'
            ]);
            $ok=is_array($res)?!empty($res['ok']):($res!==false);$any=$any||$ok;
            $results[]=['ok'=>$ok,'recipient_id'=>$to['id']??null,'kind'=>$kind];
        }
        return['ok'=>$any,'recipients'=>$results];
    }catch(Throwable $e){return['ok'=>false,'reason'=>'exception'];}
}'''
s,n=pat_reason.subn(rep_reason,s,count=1)
if n!=1: raise SystemExit('reason function not found')
helper.write_text(s,encoding='utf-8')

# -----------------------------------------------------------------------------
# Frontend: department membership and department leadership are separate concepts.
# -----------------------------------------------------------------------------
asset=list((root/'assets').glob('index-*.js'))[0]
js=asset.read_text(encoding='utf-8')

old='I.from("departamentos").select("id, nome, cor").eq("igreja_id",t).order("nome")'
new='I.from("departamentos").select("id, nome, cor, lider_id").eq("igreja_id",t).order("nome")'
if old not in js: raise SystemExit('departments select anchor not found')
js=js.replace(old,new,1)

old='[pe,q]=h.useState(!1),[oe,xe]=h.useState(null),ke=e==="admin"||e==="master"'
new='[pe,q]=h.useState(!1),[oe,xe]=h.useState(null),[$L1441,SL1441]=h.useState(""),ke=e==="admin"||e==="master"'
if old not in js: raise SystemExit('state anchor not found')
js=js.replace(old,new,1)

pat_role=re.compile(r'const \$e=async\(fe,rt\)=>\{const\{error:mt\}=await I\.from\("user_roles"\)\.update\(\{role:rt\}\)\.eq\("user_id",fe\);if\(mt\)\{V\.error\(mt\.message\);return\}V\.success\("Cargo atualizado!"\),Ue\(\)\},_t=async')
rep_role=r'''const $e=async(fe,rt)=>{const{error:mt}=await I.from("user_roles").update({role:rt}).eq("user_id",fe);if(mt){V.error(mt.message);return}if(rt==="voluntario"){await I.from("departamentos").update({lider_id:null}).eq("lider_id",fe).eq("igreja_id",t)}if(rt==="lider"){const mt2=a.find(en2=>en2.id===fe);tt(mt2||null),ft(he[fe]||[]),SL1441(((re.find(en2=>en2.lider_id===fe)||{}).id)||""),Oe(!0),V.success("Cargo de líder ativado. Agora escolha qual departamento ele lidera.")}else V.success("Cargo atualizado!");Ue()},_t=async'''
js,n=pat_role.subn(rep_role,js,count=1)
if n!=1: raise SystemExit('role handler not found')

old='Me=fe=>{tt(fe),ft(he[fe.id]||[]),Oe(!0)}'
new='Me=fe=>{tt(fe),ft(he[fe.id]||[]),SL1441(((re.find(rt=>rt.lider_id===fe.id)||{}).id)||""),Oe(!0)}'
if old not in js: raise SystemExit('Me modal opener not found')
js=js.replace(old,new,1)

pat_save=re.compile(r'pt=async\(\)=>\{if\(!Le\)return;Et\(!0\);const fe=he\[Le\.id\]\|\|\[\],rt=Ye\.filter\(Wt=>!fe\.includes\(Wt\)&&De\.some\(Ae=>Ae\.id===Wt\)\),mt=fe\.filter\(Wt=>!Ye\.includes\(Wt\)&&De\.some\(Ae=>Ae\.id===Wt\)\);let en=!1;if\(rt\.length>0\)\{const\{error:Wt\}=await I\.from\("departamento_voluntarios"\)\.insert\(rt\.map\(Ae=>\(\{departamento_id:Ae,voluntario_id:Le\.id\}\)\)\);Wt&&\(en=!0\)\}if\(mt\.length>0\)\{const\{error:Wt\}=await I\.from\("departamento_voluntarios"\)\.delete\(\)\.in\("departamento_id",mt\)\.eq\("voluntario_id",Le\.id\);Wt&&\(en=!0\)\}if\(Et\(!1\),en\)\{V\.error\("Erro ao salvar departamentos"\);return\}V\.success\("Departamentos atualizados!"\),Oe\(!1\),Ue\(\)\}')
rep_save=r'''pt=async()=>{if(!Le)return;if((l[Le.id]||"voluntario")==="lider"&&!$L1441){V.error("Selecione qual departamento este líder lidera.");return}Et(!0);const fe=he[Le.id]||[],rt=Ye.filter(Wt=>!fe.includes(Wt)&&De.some(Ae=>Ae.id===Wt)),mt=fe.filter(Wt=>!Ye.includes(Wt)&&De.some(Ae=>Ae.id===Wt));let en=!1;if($L1441&&!Ye.includes($L1441)&&!fe.includes($L1441)){rt.push($L1441),ft(Wt=>Wt.includes($L1441)?Wt:[...Wt,$L1441])}if(rt.length>0){const{error:Wt}=await I.from("departamento_voluntarios").insert([...new Set(rt)].map(Ae=>({departamento_id:Ae,voluntario_id:Le.id})));Wt&&(en=!0)}if(mt.length>0){const{error:Wt}=await I.from("departamento_voluntarios").delete().in("departamento_id",mt).eq("voluntario_id",Le.id);Wt&&(en=!0)}const{error:cl}=await I.from("departamentos").update({lider_id:null}).eq("lider_id",Le.id).eq("igreja_id",t);cl&&(en=!0);if($L1441){const{error:ld}=await I.from("departamentos").update({lider_id:Le.id}).eq("id",$L1441).eq("igreja_id",t);ld&&(en=!0);if((l[Le.id]||"voluntario")!=="admin"){const{error:rl}=await I.from("user_roles").update({role:"lider"}).eq("user_id",Le.id);rl||(c(Wt=>({...Wt,[Le.id]:"lider"})))}}if(Et(!1),en){V.error("Erro ao salvar departamentos/liderança");return}V.success("Departamentos e liderança atualizados!"),Oe(!1),Ue()}'''
js,n=pat_save.subn(rep_save,js,count=1)
if n!=1: raise SystemExit('department save handler not found')

old='ue=async()=>{if(!te)return;const{error:fe}=await I.from("profiles").delete().eq("id",te.id);'
new='ue=async()=>{if(!te)return;await I.from("departamentos").update({lider_id:null}).eq("lider_id",te.id).eq("igreja_id",t);const{error:fe}=await I.from("profiles").delete().eq("id",te.id);'
if old not in js: raise SystemExit('delete volunteer anchor not found')
js=js.replace(old,new,1)

old='mt.length>0&&r.jsx("div",{className:"flex flex-wrap gap-1 mt-1.5",children:mt.map(Ae=>r.jsx("span",{className:"text-[10px] px-2 py-1 rounded-full border bg-secondary/30 text-muted-foreground max-w-[150px] truncate",style:{borderColor:Ae.cor||void 0},children:Ae.nome},Ae.id))}),r.jsx("div",{className:"mt-1",children:r.jsx(Gw,{voluntarioId:fe.id,compact:!0,onRatingCalculated:Ae=>Ee(fe.id,Ae)})})'
new='mt.length>0&&r.jsx("div",{className:"flex flex-wrap gap-1 mt-1.5",children:mt.map(Ae=>r.jsx("span",{className:"text-[10px] px-2 py-1 rounded-full border bg-secondary/30 text-muted-foreground max-w-[150px] truncate",style:{borderColor:Ae.cor||void 0},children:Ae.nome},Ae.id))}),re.some(Ae=>Ae.lider_id===fe.id)&&r.jsx("div",{className:"flex flex-wrap gap-1 mt-1.5",children:re.filter(Ae=>Ae.lider_id===fe.id).map(Ae=>r.jsxs("span",{className:"text-[10px] px-2 py-1 rounded-full border border-primary/30 bg-primary/10 text-primary font-semibold",children:["Líder de ",Ae.nome]},"lead-"+Ae.id))}),r.jsx("div",{className:"mt-1",children:r.jsx(Gw,{voluntarioId:fe.id,compact:!0,onRatingCalculated:Ae=>Ee(fe.id,Ae)})})'
if old not in js: raise SystemExit('card memberships anchor not found')
js=js.replace(old,new,1)

old='r.jsxs("div",{className:"space-y-3",children:[De.length===0?r.jsx("p",{className:"text-sm text-muted-foreground text-center py-4",children:"Nenhum departamento disponível"})'
new='r.jsxs("div",{className:"space-y-3",children:[ve&&Le&&r.jsxs("div",{className:"rounded-xl border border-primary/20 bg-primary/5 p-3 space-y-1.5",children:[r.jsx(_e,{className:"text-xs font-bold",children:"Departamento que lidera"}),r.jsxs(qt,{value:$L1441||"__none",onValueChange:fe=>SL1441(fe==="__none"?"":fe),children:[r.jsx(Ut,{className:"h-9 text-sm",children:r.jsx(Zt,{placeholder:"Selecione o departamento"})}),r.jsxs(Ht,{children:[r.jsx(nt,{value:"__none",children:"Não lidera nenhum departamento"}),re.map(fe=>r.jsx(nt,{value:fe.id,children:fe.nome},fe.id))]})]}),r.jsx("p",{className:"text-[10px] text-muted-foreground",children:"Isto define liderança. Os departamentos marcados abaixo definem apenas onde a pessoa participa. Participar de outro departamento não a torna líder dele."})]}),De.length===0?r.jsx("p",{className:"text-sm text-muted-foreground text-center py-4",children:"Nenhum departamento disponível"})'
if old not in js: raise SystemExit('department modal content anchor not found')
js=js.replace(old,new,1)

js=js.replace('r.jsx("option",{value:"lider",children:"Líder"})','r.jsx("option",{value:"lider",children:"Líder (definir departamento)"})',1)

old='r.jsx(_e,{className:"text-xs",children:"Líder"}),r.jsxs(qt,{value:y.lider_id,onValueChange:G=>b(he=>({...he,lider_id:G}))'
new='r.jsx(_e,{className:"text-xs font-bold",children:"Líder responsável deste departamento"}),r.jsxs(qt,{value:y.lider_id,onValueChange:G=>b(he=>({...he,lider_id:G}))'
if old not in js: raise SystemExit('department leader label anchor not found')
js=js.replace(old,new,1)
old2='r.jsx(Ht,{children:c.map(G=>r.jsx(nt,{value:G.id,children:G.nome},G.id))})]})]}),r.jsxs("div",{className:"space-y-1.5",children:[r.jsx(_e,{className:"text-xs",children:"Antecedência padrão (min)"})'
new2='r.jsx(Ht,{children:c.map(G=>r.jsx(nt,{value:G.id,children:G.nome},G.id))})]}),r.jsx("p",{className:"text-[10px] text-muted-foreground",children:"Esse líder receberá as confirmações e recusas deste departamento. A pessoa pode participar de outros departamentos sem ser líder deles."})]}),r.jsxs("div",{className:"space-y-1.5",children:[r.jsx(_e,{className:"text-xs",children:"Antecedência padrão (min)"})'
if old2 not in js: raise SystemExit('department leader explanation anchor not found')
js=js.replace(old2,new2,1)

old='V.success("Departamento criado!"),x(!1),b({nome:"",descricao:"",cor:"#1e3a5f",lider_id:"",antecedencia_minutos:"0"}),K()'
new='if(y.lider_id){await I.from("user_roles").update({role:"lider"}).eq("user_id",y.lider_id).neq("role","admin");const dnew=he&&he[0]&&he[0].id;if(dnew){const{data:exm}=await I.from("departamento_voluntarios").select("id").eq("departamento_id",dnew).eq("voluntario_id",y.lider_id).limit(1);(!exm||exm.length===0)&&await I.from("departamento_voluntarios").insert({departamento_id:dnew,voluntario_id:y.lider_id})}}V.success("Departamento criado!"),x(!1),b({nome:"",descricao:"",cor:"#1e3a5f",lider_id:"",antecedencia_minutos:"0"}),K()'
if old not in js: raise SystemExit('department create success anchor not found')
js=js.replace(old,new,1)

old='V.success("Departamento atualizado!"),j(!1),S(null),b({nome:"",descricao:"",cor:"#1e3a5f",lider_id:"",antecedencia_minutos:"0"}),K()'
new='if(y.lider_id){await I.from("user_roles").update({role:"lider"}).eq("user_id",y.lider_id).neq("role","admin");const{data:exm}=await I.from("departamento_voluntarios").select("id").eq("departamento_id",w.id).eq("voluntario_id",y.lider_id).limit(1);(!exm||exm.length===0)&&await I.from("departamento_voluntarios").insert({departamento_id:w.id,voluntario_id:y.lider_id})}if(w.lider_id&&w.lider_id!==y.lider_id){const{data:ol}=await I.from("departamentos").select("id").eq("lider_id",w.lider_id).limit(1);(!ol||ol.length===0)&&await I.from("user_roles").update({role:"voluntario"}).eq("user_id",w.lider_id).eq("role","lider")}V.success("Departamento atualizado!"),j(!1),S(null),b({nome:"",descricao:"",cor:"#1e3a5f",lider_id:"",antecedencia_minutos:"0"}),K()'
if old not in js: raise SystemExit('department update success anchor not found')
js=js.replace(old,new,1)

old='z=async G=>{if(!confirm(`Deseja realmente excluir "${G.nome}"?`))return;const{error:he}=await I.from("departamentos").delete().eq("id",G.id);if(he){V.error(`Erro: ${he.message}`);return}V.success("Departamento excluído!"),K()}'
new='z=async G=>{if(!confirm(`Deseja realmente excluir "${G.nome}"?`))return;const lid=G.lider_id||"";const{error:he}=await I.from("departamentos").delete().eq("id",G.id);if(he){V.error(`Erro: ${he.message}`);return}if(lid){const{data:ol}=await I.from("departamentos").select("id").eq("lider_id",lid).limit(1);(!ol||ol.length===0)&&await I.from("user_roles").update({role:"voluntario"}).eq("user_id",lid).eq("role","lider")}V.success("Departamento excluído!"),K()}'
if old not in js: raise SystemExit('department delete anchor not found')
js=js.replace(old,new,1)

asset.write_text(js,encoding='utf-8')

(root/'VERSION').write_text('1.4.41\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.41.md').write_text('''# Escala de Propósito v1.4.41

- Confirmações e recusas de escala passam a ser enviadas para o pastor/admin **e** para o líder do departamento da escala.
- Se pastor e líder forem a mesma pessoa, a mensagem é enviada somente uma vez.
- Se não houver departamento ou líder válido, o pastor/admin continua recebendo normalmente.
- O motivo da indisponibilidade segue a mesma regra de destinatários.
- A liderança passa a ser explicitamente vinculada ao campo `departamentos.lider_id`; participar de vários departamentos não torna a pessoa líder de todos.
- Na tela de voluntários, ao definir o cargo como Líder, abre a seleção do departamento que ele lidera.
- O modal de Departamentos do voluntário separa **Departamento que lidera** de **Departamentos em que participa**.
- O cartão do voluntário mostra um selo “Líder de …” separado dos departamentos em que participa.
- Ao criar/editar um departamento, o campo “Líder responsável deste departamento” fica explícito.
- O líder escolhido entra automaticamente como membro do próprio departamento; participar de outros departamentos não transfere liderança.
- Ao deixar de liderar todos os departamentos, o cargo global de Líder é removido automaticamente, sem alterar usuários Admin.
- Não altera o recebimento 1/2 do WhatsApp, quiz, repertório, PDF ou transporte da Evolution.
''',encoding='utf-8')
print('patched',root)
