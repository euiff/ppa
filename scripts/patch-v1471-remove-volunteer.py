from pathlib import Path
import re

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

def one(text,old,new,label):
    c=text.count(old)
    if c!=1:
        raise SystemExit(f'{label}: anchor count={c}')
    return text.replace(old,new,1)

old='[R,O]=h.useState(!1),[resendItemV1470,setResendItemV1470]=h.useState(null),[resendAllBusyV1470,setResendAllBusyV1470]=h.useState(!1),[q30,setQ30]=h.useState({}),[sd,setSd]=h.useState({}),Y=h.useCallback'
new='[R,O]=h.useState(!1),[resendItemV1470,setResendItemV1470]=h.useState(null),[resendAllBusyV1470,setResendAllBusyV1470]=h.useState(!1),[removeBusyV1471,setRemoveBusyV1471]=h.useState(null),[q30,setQ30]=h.useState({}),[sd,setSd]=h.useState({}),Y=h.useCallback'
s=one(s,old,new,'remove busy state')

anchor='}};if(!a&&l){const Fe=new URLSearchParams(window.location.search)'
if s.count(anchor)!=1:
    raise SystemExit('remove handler anchor count='+str(s.count(anchor)))
handler=r'''},removeScaleItemV1471=async pe=>{var q;const oe=((q=pe.profile)==null?void 0:q.nome)||"este voluntário",xe=pe.funcao||"esta função";if(!window.confirm("Retirar "+oe+" desta escala?\n\nFunção: "+xe+"\n\nO cadastro do voluntário será mantido."))return;setRemoveBusyV1471(pe.id);try{const ge=localStorage.getItem("escala-facil.auth-token")||"",De=await fetch("/api/scale-item-remove-v1471.php",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+ge},body:JSON.stringify({escala_id:l.id,escala_item_id:pe.id})}),Ne=await De.json();if(!De.ok||(Ne!=null&&Ne.error))throw new Error(((Ne==null?void 0:Ne.error)==null?void 0:Ne.error.message)||"Não foi possível retirar o voluntário");V.success(oe+" foi retirado(a) desta escala."),await Y()}catch(ge){V.error((ge==null?void 0:ge.message)||"Falha ao retirar voluntário da escala")}finally{setRemoveBusyV1471(null)}};if(!a&&l){const Fe=new URLSearchParams(window.location.search)'''
s=s.replace(anchor,handler,1)

old='r.jsxs("div",{className:"flex items-center gap-1.5 shrink-0",children:[r.jsx(ht,{variant:"outline",className:"text-[10px] shrink-0 "+q.cls,children:q.text}),we&&l.status==="publicado"&&r.jsxs(ie,{size:"sm",variant:"outline",className:"h-7 text-[10px] px-2",disabled:resendItemV1470===pe.id,onClick:()=>resendOneV1470(pe),title:"Reenviar notificação apenas para este voluntário",children:[r.jsx(ic,{className:"w-3 h-3 mr-1 "+(resendItemV1470===pe.id?"animate-spin":"")}),resendItemV1470===pe.id?"Enviando...":"Reenviar"]})]})'
new='r.jsxs("div",{className:"flex items-center justify-end gap-1.5 shrink-0 flex-wrap",children:[r.jsx(ht,{variant:"outline",className:"text-[10px] shrink-0 "+q.cls,children:q.text}),we&&l.status==="publicado"&&r.jsxs(ie,{size:"sm",variant:"outline",className:"h-7 text-[10px] px-2",disabled:resendItemV1470===pe.id,onClick:()=>resendOneV1470(pe),title:"Reenviar notificação apenas para este voluntário",children:[r.jsx(ic,{className:"w-3 h-3 mr-1 "+(resendItemV1470===pe.id?"animate-spin":"")}),resendItemV1470===pe.id?"Enviando...":"Reenviar"]}),we&&r.jsx(ie,{size:"sm",variant:"outline",className:"h-7 text-[10px] px-2 border-destructive/40 text-destructive hover:bg-destructive/10",disabled:removeBusyV1471===pe.id,onClick:()=>removeScaleItemV1471(pe),title:"Tirar este voluntário somente desta escala",children:removeBusyV1471===pe.id?"Retirando...":"Retirar"})]})'
s=one(s,old,new,'individual remove button')

asset.write_text(s,encoding='utf-8')

endpoint=r'''<?php
declare(strict_types=1);
require_once __DIR__.'/bootstrap.php';

$u=require_auth();
$ctx=user_context();
$req=input_json();

$uid=(string)($u['id']??$ctx['id']??'');
$role=(string)($ctx['role']??'');
$igrejaCtx=(string)($ctx['igreja_id']??'');
$escalaId=trim((string)($req['escala_id']??''));
$itemId=trim((string)($req['escala_item_id']??''));

if($escalaId===''||$itemId===''){
    out(['data'=>null,'error'=>['message'=>'Escala ou voluntário não informado.']],400);
}

try{
    $q=db()->prepare("SELECT ei.id,ei.voluntario_id,ei.funcao,e.id escala_id,e.igreja_id,e.departamento_id
                      FROM escala_itens ei
                      JOIN escalas e ON BINARY e.id=BINARY ei.escala_id
                      WHERE BINARY ei.id=BINARY ? AND BINARY e.id=BINARY ?
                      LIMIT 1");
    $q->execute([$itemId,$escalaId]);
    $item=$q->fetch(PDO::FETCH_ASSOC);
    if(!$item)out(['data'=>null,'error'=>['message'=>'Voluntário não encontrado nesta escala.']],404);

    $ig=(string)$item['igreja_id'];
    if($role!=='master'&&($igrejaCtx===''||$igrejaCtx!==$ig)){
        out(['data'=>null,'error'=>['message'=>'Sem permissão para esta igreja.']],403);
    }

    $allowed=in_array($role,['master','admin'],true);
    if(!$allowed&&$role==='lider'){
        $q=db()->prepare("SELECT lider_id FROM departamentos WHERE BINARY id=BINARY ? LIMIT 1");
        $q->execute([(string)$item['departamento_id']]);
        $allowed=((string)($q->fetchColumn()?:''))===$uid;
    }
    if(!$allowed){
        out(['data'=>null,'error'=>['message'=>'Sem permissão para retirar pessoas desta escala.']],403);
    }

    db()->beginTransaction();
    try{
        try{
            $q=db()->prepare("UPDATE trocas SET status='recusado' WHERE BINARY escala_item_id=BINARY ? AND status='pendente'");
            $q->execute([$itemId]);
        }catch(Throwable $e){}
        try{
            $q=db()->prepare("DELETE FROM app_notification_events WHERE BINARY escala_item_id=BINARY ?");
            $q->execute([$itemId]);
        }catch(Throwable $e){}

        $q=db()->prepare("DELETE FROM escala_itens WHERE BINARY id=BINARY ? AND BINARY escala_id=BINARY ?");
        $q->execute([$itemId,$escalaId]);
        if($q->rowCount()<1)throw new RuntimeException('O voluntário já havia sido retirado ou a escala foi alterada.');

        db()->commit();
    }catch(Throwable $e){
        if(db()->inTransaction())db()->rollBack();
        throw $e;
    }

    try{
        audit($uid,'scale_item_removed','escala_itens',[
            'escala_id'=>$escalaId,
            'escala_item_id'=>$itemId,
            'voluntario_id'=>(string)$item['voluntario_id'],
            'funcao'=>(string)($item['funcao']??'')
        ],'warning');
    }catch(Throwable $e){}

    out(['data'=>['success'=>true,'escala_id'=>$escalaId,'escala_item_id'=>$itemId],'error'=>null]);
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
'''
(root/'api'/'scale-item-remove-v1471.php').write_text(endpoint,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\1?v=1.4.71\2',h,count=1)
if n!=1: raise SystemExit('main bundle tag missing')
h=h.replace('/app-notifications-v1465.js?v=1.4.70','/app-notifications-v1465.js?v=1.4.71')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw='/* escala-version:1.4.71 */\n'+sw
p.write_text(sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.71\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.71.md').write_text('''# Escala de Propósito v1.4.71 — Retirar voluntário da Escala Completa

- Corrige a sequência de versões: esta atualização continua a partir da **v1.4.70**, sem voltar para a linha v1.3.x.
- Na tela **Escala Completa**, cada voluntário passa a ter o botão **Retirar** ao lado do status/Reenviar.
- Antes da retirada, o sistema confirma o nome e a função e informa que o cadastro do voluntário será mantido.
- A ação remove a pessoa **somente daquela escala**; não apaga o voluntário, o departamento ou o histórico de cadastro.
- Pastor/Admin/Master podem retirar pessoas da escala; o backend também aceita o líder responsável pelo próprio departamento.
- Solicitações de troca pendentes ligadas ao item são encerradas e eventos de notificação desse item são limpos quando existirem.
- Depois da retirada, a Escala Completa é atualizada imediatamente.
- Mantém todos os recursos e correções da v1.4.70, inclusive Reenviar Notificações, app, WhatsApp, PDF e impressão.
''',encoding='utf-8')
