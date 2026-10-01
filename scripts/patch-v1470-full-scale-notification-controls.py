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

old='[R,O]=h.useState(!1),[q30,setQ30]=h.useState({}),[sd,setSd]=h.useState({}),Y=h.useCallback'
new='[R,O]=h.useState(!1),[resendItemV1470,setResendItemV1470]=h.useState(null),[resendAllBusyV1470,setResendAllBusyV1470]=h.useState(!1),[q30,setQ30]=h.useState({}),[sd,setSd]=h.useState({}),Y=h.useCallback'
s=one(s,old,new,'full scale resend states')

anchor='}};if(!a&&l){const Fe=new URLSearchParams(window.location.search)'
if s.count(anchor)!=1:
    raise SystemExit('full scale handlers insertion anchor count='+str(s.count(anchor)))

handlers=r'''}};const planFeaturesV1470=async()=>{if(window.EscalaPlanFeatures)return window.EscalaPlanFeatures;try{const pe=localStorage.getItem("escala-facil.auth-token")||"",q=await fetch("/api/plan-features.php",{headers:{Authorization:"Bearer "+pe},cache:"no-store"}),oe=await q.json(),xe=(oe==null?void 0:oe.data)==null?void 0:oe.data.features;if(xe){window.EscalaPlanFeatures=xe;return xe}}catch(pe){}return{whatsapp:!0,app_notifications:!0}},appNotifyV1470=async pe=>{const q=localStorage.getItem("escala-facil.auth-token")||"",oe=await fetch("/api/app-scale-resend-v1470.php",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+q},body:JSON.stringify({escala_id:l.id,escala_item_id:pe||null})}),xe=await oe.json();if(!oe.ok||(xe!=null&&xe.error))throw new Error(((xe==null?void 0:xe.error)==null?void 0:xe.error.message)||"Falha ao reenviar pelo app");return(xe==null?void 0:xe.data)||{}},sendChannelV1470=async pe=>{const q=await planFeaturesV1470();if(q&&q.whatsapp===!1)return{channel:"app",result:await appNotifyV1470(pe)};const{data:oe,error:xe}=await I.functions.invoke("send-whatsapp",{body:{escala_id:l.id,...pe?{escala_item_id:pe}:{},force_resend:!0}});if(xe)throw xe;return{channel:"whatsapp",result:oe||{}}},resendAllV1470=async()=>{setResendAllBusyV1470(!0);try{const pe=await sendChannelV1470(null),q=pe.result||{};pe.channel==="app"?V.success("Notificações pelo app reenviadas: "+(q.queued||0)+"."):(q.queued||0)>0?V.success("Reenvio agendado na fila segura: "+(q.queued||0)+" mensagem(ns)."):(q.sent||0)>0?V.success("Notificações reenviadas: "+(q.sent||0)+" sucesso, "+(q.errors||0)+" erros."):V.warning("Reenvio concluído, mas nenhuma mensagem foi enviada. Erros: "+(q.errors||0)+".")}catch(pe){V.error((pe==null?void 0:pe.message)||"Falha ao reenviar notificações")}finally{setResendAllBusyV1470(!1)}},resendOneV1470=async pe=>{var q;setResendItemV1470(pe.id);try{const oe=await sendChannelV1470(pe.id),xe=oe.result||{},ge=((q=pe.profile)==null?void 0:q.nome)||"voluntário";oe.channel==="app"?V.success("Notificação pelo app reenviada para "+ge+"."):(xe.queued||0)>0?V.success("Reenvio agendado para "+ge+"."):(xe.sent||0)>0?V.success("Notificação reenviada para "+ge+"."):V.warning("Não foi possível reenviar para "+ge+".")}catch(q){V.error((q==null?void 0:q.message)||"Falha ao reenviar notificação individual")}finally{setResendItemV1470(null)}},publishNotifyV1470=async()=>{setResendAllBusyV1470(!0);try{const pe=new Date().toISOString(),{error:q}=await I.from("escalas").update({status:"publicado",published_at:pe}).eq("id",l.id);if(q)throw q;const oe=await sendChannelV1470(null),xe=oe.result||{};oe.channel==="app"?V.success("Escala publicada e "+(xe.queued||0)+" notificação(ões) enviada(s) para o app."):(xe.queued||0)>0?V.success("Escala publicada e "+(xe.queued||0)+" mensagem(ns) colocada(s) na fila."):V.success("Escala publicada. O envio de notificações foi processado."),await Y()}catch(pe){V.error((pe==null?void 0:pe.message)||"Falha ao publicar e notificar")}finally{setResendAllBusyV1470(!1)}};if(!a&&l){const Fe=new URLSearchParams(window.location.search)'''
s=s.replace(anchor,handlers,1)

old='r.jsxs(ie,{size:"sm",className:"h-10 text-xs",onClick:he,children:[r.jsx(I2,{className:"w-4 h-4 mr-1.5"})," Baixar PDF"]})]})]})'
new='r.jsxs(ie,{size:"sm",className:"h-10 text-xs",onClick:he,children:[r.jsx(I2,{className:"w-4 h-4 mr-1.5"})," Baixar PDF"]}),we&&r.jsxs(ie,{variant:"outline",size:"sm",className:"h-10 text-xs col-span-2 sm:col-span-1",disabled:resendAllBusyV1470,onClick:l.status==="publicado"?resendAllV1470:publishNotifyV1470,children:[r.jsx(ic,{className:"w-4 h-4 mr-1.5 "+(resendAllBusyV1470?"animate-spin":"")}),resendAllBusyV1470?"Processando...":l.status==="publicado"?"Reenviar Notificações":"Publicar e Notificar"]})]})]})'
s=one(s,old,new,'full scale top notify button')

pat=re.compile(r'r\.jsx\(ht,\{variant:"outline",className:\x60text-\[10px\] shrink-0 \$\{q\.cls\}\x60,children:q\.text\}\)\]\}\),pe\.justificativa_recusa')
replacement='r.jsxs("div",{className:"flex items-center gap-1.5 shrink-0",children:[r.jsx(ht,{variant:"outline",className:"text-[10px] shrink-0 "+q.cls,children:q.text}),we&&l.status==="publicado"&&r.jsxs(ie,{size:"sm",variant:"outline",className:"h-7 text-[10px] px-2",disabled:resendItemV1470===pe.id,onClick:()=>resendOneV1470(pe),title:"Reenviar notificação apenas para este voluntário",children:[r.jsx(ic,{className:"w-3 h-3 mr-1 "+(resendItemV1470===pe.id?"animate-spin":"")}),resendItemV1470===pe.id?"Enviando...":"Reenviar"]})]})]}),pe.justificativa_recusa'
s,n=pat.subn(replacement,s,count=1)
if n!=1:
    raise SystemExit('full scale individual resend anchor='+str(n))

asset.write_text(s,encoding='utf-8')

helper=r'''<?php
declare(strict_types=1);

function v1470_app_event_schema(): void {
    db()->exec("CREATE TABLE IF NOT EXISTS app_notification_events (
      id VARCHAR(36) NOT NULL PRIMARY KEY,
      igreja_id VARCHAR(36) NOT NULL,
      user_id VARCHAR(36) NOT NULL,
      escala_id VARCHAR(36) NOT NULL,
      escala_item_id VARCHAR(36) NULL,
      title VARCHAR(180) NOT NULL,
      message VARCHAR(600) NULL,
      url VARCHAR(500) NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      expires_at DATETIME NOT NULL,
      KEY idx_app_event_user(user_id,created_at),
      KEY idx_app_event_church(igreja_id,created_at),
      KEY idx_app_event_scale(escala_id),
      KEY idx_app_event_expires(expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
}

function v1470_enqueue_scale_app_events(string $escalaId, ?string $itemId=null): int {
    v1470_app_event_schema();
    try{db()->exec("DELETE FROM app_notification_events WHERE expires_at<NOW()");}catch(Throwable $e){}
    $sql="SELECT ei.id item_id,ei.voluntario_id,ei.funcao,e.id escala_id,e.igreja_id,e.data,d.nome departamento
          FROM escala_itens ei
          JOIN escalas e ON BINARY e.id=BINARY ei.escala_id
          LEFT JOIN departamentos d ON BINARY d.id=BINARY e.departamento_id
          WHERE BINARY e.id=BINARY ?";
    $args=[$escalaId];
    if($itemId!==null&&$itemId!==''){$sql.=" AND BINARY ei.id=BINARY ?";$args[]=$itemId;}
    $sql.=" ORDER BY ei.created_at ASC";
    $q=db()->prepare($sql);$q->execute($args);
    $rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];
    $count=0;
    foreach($rows as $r){
        $uid=trim((string)($r['voluntario_id']??''));
        if($uid==='')continue;
        $parts=array_values(array_filter([
            trim((string)($r['departamento']??'')),
            trim((string)($r['funcao']??'')),
            !empty($r['data'])?date('d/m/Y',strtotime((string)$r['data'])):''
        ],fn($x)=>$x!==''));
        db()->prepare("INSERT INTO app_notification_events
          (id,igreja_id,user_id,escala_id,escala_item_id,title,message,url,created_at,expires_at)
          VALUES(?,?,?,?,?,?,?,?,NOW(),DATE_ADD(NOW(),INTERVAL 7 DAY))")
          ->execute([
            uuid4(),(string)$r['igreja_id'],$uid,$escalaId,(string)$r['item_id'],
            'Lembrete da sua escala',implode(' · ',$parts),
            '/minha-escala/'.rawurlencode($escalaId)
          ]);
        $count++;
    }
    return $count;
}
'''
(root/'api'/'app_notification_events_v1470.php').write_text(helper,encoding='utf-8')

endpoint=r'''<?php
declare(strict_types=1);
require_once __DIR__.'/bootstrap.php';
require_once __DIR__.'/plan_features_v1465.php';
require_once __DIR__.'/app_notification_events_v1470.php';

$u=require_auth();$ctx=user_context();$req=input_json();
$uid=(string)($u['id']??$ctx['id']??'');
$role=(string)($ctx['role']??'');
$igrejaCtx=(string)($ctx['igreja_id']??'');
$escalaId=trim((string)($req['escala_id']??''));
$itemId=trim((string)($req['escala_item_id']??''));
if($escalaId==='')out(['data'=>null,'error'=>['message'=>'Escala não informada.']],400);

try{
    $q=db()->prepare("SELECT id,igreja_id,departamento_id,status FROM escalas WHERE BINARY id=BINARY ? LIMIT 1");
    $q->execute([$escalaId]);$esc=$q->fetch(PDO::FETCH_ASSOC);
    if(!$esc)out(['data'=>null,'error'=>['message'=>'Escala não encontrada.']],404);
    $ig=(string)$esc['igreja_id'];
    if($role!=='master'&&($igrejaCtx===''||$igrejaCtx!==$ig))
        out(['data'=>null,'error'=>['message'=>'Sem permissão para esta igreja.']],403);
    $allowed=in_array($role,['master','admin'],true);
    if(!$allowed&&$role==='lider'){
        $q=db()->prepare("SELECT lider_id FROM departamentos WHERE BINARY id=BINARY ? LIMIT 1");
        $q->execute([(string)$esc['departamento_id']]);
        $allowed=((string)($q->fetchColumn()?:''))===$uid;
    }
    if(!$allowed)out(['data'=>null,'error'=>['message'=>'Sem permissão para reenviar notificações desta escala.']],403);
    if(!v1465_feature_enabled($ig,'app_notifications'))
        out(['data'=>null,'error'=>['message'=>'Notificações pelo app não estão habilitadas neste plano.']],403);
    if($itemId!==''){
        $q=db()->prepare("SELECT COUNT(*) FROM escala_itens WHERE BINARY id=BINARY ? AND BINARY escala_id=BINARY ?");
        $q->execute([$itemId,$escalaId]);
        if((int)$q->fetchColumn()===0)out(['data'=>null,'error'=>['message'=>'Voluntário não pertence a esta escala.']],400);
    }
    $queued=v1470_enqueue_scale_app_events($escalaId,$itemId!==''?$itemId:null);
    try{audit($uid,'app_scale_notification_resend','escala_itens',['escala_id'=>$escalaId,'escala_item_id'=>$itemId?:null,'queued'=>$queued],'info');}catch(Throwable $e){}
    out(['data'=>['success'=>true,'queued'=>$queued,'channel'=>'app'],'error'=>null]);
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
'''
(root/'api'/'app-scale-resend-v1470.php').write_text(endpoint,encoding='utf-8')

p=root/'api'/'app-pending.php'
ap=p.read_text(encoding='utf-8')
if "app_notification_events_v1470.php" not in ap:
    ap=ap.replace("require_once __DIR__.'/plan_features_v1465.php';","require_once __DIR__.'/plan_features_v1465.php';\nrequire_once __DIR__.'/app_notification_events_v1470.php';",1)
ap=ap.replace("'url'=>'/escala/'.rawurlencode((string)$r['escala_id'])","'url'=>'/minha-escala/'.rawurlencode((string)$r['escala_id'])")
old="""    usort($items,fn($a,$b)=>strcmp((string)($a['created_at']??''),(string)($b['created_at']??'')));
    out(['data'=>['count'=>count($items),'items'=>$items,'disabled'=>false,'checked_at'=>date(DATE_ATOM)],'error'=>null]);"""
new="""    $pendingCount=count($items);
    try{
        v1470_app_event_schema();
        db()->exec("DELETE FROM app_notification_events WHERE expires_at<NOW()");
        $qe=db()->prepare("SELECT id,title,message,url,created_at FROM app_notification_events WHERE BINARY user_id=BINARY ? AND expires_at>NOW() ORDER BY created_at DESC LIMIT 100");
        $qe->execute([$uid]);
        foreach($qe->fetchAll(PDO::FETCH_ASSOC)?:[] as$ev){
            $items[]=['id'=>'event:'.(string)$ev['id'],'type'=>'event','title'=>(string)$ev['title'],'message'=>(string)($ev['message']??''),'url'=>(string)($ev['url']??'/'),'created_at'=>$ev['created_at']??null];
        }
    }catch(Throwable $e){}
    usort($items,fn($a,$b)=>strcmp((string)($a['created_at']??''),(string)($b['created_at']??'')));
    out(['data'=>['count'=>$pendingCount,'items'=>$items,'disabled'=>false,'checked_at'=>date(DATE_ATOM)],'error'=>null]);"""
if old not in ap:
    raise SystemExit('app-pending output anchor missing')
ap=ap.replace(old,new,1)
p.write_text(ap,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\1?v=1.4.70\2',h,count=1)
if n!=1: raise SystemExit('main bundle tag missing')
h=h.replace('/app-notifications-v1465.js?v=1.4.65','/app-notifications-v1465.js?v=1.4.70')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw='/* escala-version:1.4.70 */\n'+sw
p.write_text(sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.70\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.70.md').write_text('''# Escala de Propósito v1.4.70 — Controles de notificação na Escala Completa

- Leva os controles úteis da antiga tela de departamento para a Escala Completa.
- Escala publicada: adiciona o botão Reenviar Notificações no cabeçalho, junto de Imprimir e Baixar PDF.
- Escala em rascunho: o mesmo espaço mostra Publicar e Notificar.
- Cada voluntário da escala publicada ganha o botão Reenviar para envio individual.
- Plano com WhatsApp continua usando a função send-whatsapp e a fila segura já existente.
- Plano sem WhatsApp não tenta chamar a Evolution: cria um novo evento de notificação do aplicativo.
- O reenvio pelo app gera um evento único, permitindo notificar novamente mesmo que a primeira notificação já tenha sido vista.
- O link da notificação do aplicativo passa a abrir /minha-escala/{id}, que é a área correta do voluntário.
- O contador do ícone continua baseado nas pendências reais; eventos de reenvio não inflacionam o badge.
- O push nativo com o aplicativo totalmente encerrado continua dependendo da futura recompilação do APK com a assinatura original.
''',encoding='utf-8')
