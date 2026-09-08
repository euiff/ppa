from pathlib import Path
import sys
root=Path(sys.argv[1])
api=root/'api'
helper=api/'scale_response_notify_v1417.php'
endpoint=api/'scale-response-notify.php'

helper.write_text(r'''<?php
declare(strict_types=1);
/** Escala de Propósito v1.4.17 - aviso WhatsApp da resposta da escala ao responsável. */

function v1417_trace(string $event,array $data=[]):void{
    try{$dir=__DIR__.'/../storage';if(!is_dir($dir))@mkdir($dir,0755,true);$f=$dir.'/scale-response-notify-v1417.log';if(is_file($f)&&filesize($f)>1048576)@rename($f,$f.'.1');@file_put_contents($f,json_encode(['at'=>date(DATE_ATOM),'event'=>$event]+$data,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES).PHP_EOL,FILE_APPEND|LOCK_EX);}catch(Throwable $e){}
}
function v1417_digits(string $v):string{return preg_replace('/\\D+/','',$v)?:'';}
function v1417_valid_phone(string $v):bool{$d=v1417_digits($v);return strlen($d)>=10&&strlen($d)<=14;}
function v1417_item(string $itemId):?array{
    try{
        $q=db()->prepare("SELECT ei.id item_id,ei.escala_id,ei.voluntario_id,ei.funcao,ei.status_confirmacao,ei.justificativa_recusa,
            e.data,e.igreja_id,e.created_by,c.horario,c.nome culto_nome,d.nome departamento_nome,d.lider_id departamento_lider_id,
            p.nome voluntario_nome
            FROM escala_itens ei
            JOIN escalas e ON e.id=ei.escala_id
            JOIN profiles p ON p.id=ei.voluntario_id
            LEFT JOIN cultos c ON c.id=e.culto_id
            LEFT JOIN departamentos d ON d.id=e.departamento_id
            WHERE ei.id=? LIMIT 1");$q->execute([$itemId]);$r=$q->fetch();return$r?:null;
    }catch(Throwable $e){v1417_trace('item_error',['item'=>$itemId,'message'=>substr($e->getMessage(),0,240)]);return null;}
}
function v1417_profile(string $id):?array{
    if($id==='')return null;
    try{$q=db()->prepare("SELECT id,nome,whatsapp,igreja_id FROM profiles WHERE id=? LIMIT 1");$q->execute([$id]);$r=$q->fetch();return$r?:null;}catch(Throwable $e){return null;}
}
function v1417_admin_id(string $igrejaId):string{
    if($igrejaId==='')return '';
    try{$q=db()->prepare("SELECT admin_user_id FROM saas_church_access WHERE igreja_id=? LIMIT 1");$q->execute([$igrejaId]);$v=$q->fetchColumn();if($v)return(string)$v;}catch(Throwable $e){}
    try{$q=db()->prepare("SELECT p.id FROM profiles p JOIN user_roles ur ON ur.user_id=p.id WHERE p.igreja_id=? AND ur.role='admin' ORDER BY p.created_at ASC LIMIT 1");$q->execute([$igrejaId]);$v=$q->fetchColumn();if($v)return(string)$v;}catch(Throwable $e){}
    return '';
}
function v1417_recipient(array $item):?array{
    $vol=(string)($item['voluntario_id']??'');
    $ids=[];
    foreach([(string)($item['created_by']??''),(string)($item['departamento_lider_id']??''),v1417_admin_id((string)($item['igreja_id']??''))] as $id){if($id!==''&&$id!==$vol&&!in_array($id,$ids,true))$ids[]=$id;}
    foreach($ids as$id){$p=v1417_profile($id);if($p&&v1417_valid_phone((string)($p['whatsapp']??'')))return$p;}
    return null;
}
function v1417_recently_sent(string $itemId,string $status,string $dest,string $type):bool{
    try{$q=db()->prepare("SELECT id FROM notification_logs WHERE tipo=? AND status='enviado' AND destinatario=? AND meta_data LIKE ? AND meta_data LIKE ? AND created_at>=DATE_SUB(NOW(),INTERVAL 10 MINUTE) ORDER BY created_at DESC LIMIT 1");$q->execute([$type,$dest,'%\"escala_item_id\":\"'.$itemId.'\"%','%\"status\":\"'.$status.'\"%']);return(bool)$q->fetchColumn();}catch(Throwable $e){return false;}
}
function v1417_format_date(string $d):string{$ts=strtotime($d);return$ts?date('d/m/Y',$ts):$d;}
function v1417_notify_scale_response(string $itemId,string $status,string $source='whatsapp'):array{
    $item=v1417_item($itemId);if(!$item)return['ok'=>false,'reason'=>'item_not_found'];
    $dbStatus=(string)($item['status_confirmacao']??'');if(in_array($dbStatus,['confirmado','tarde','recusado'],true))$status=$dbStatus;
    if(!in_array($status,['confirmado','tarde','recusado'],true))return['ok'=>false,'reason'=>'invalid_status'];
    $to=v1417_recipient($item);if(!$to){v1417_trace('no_recipient',['item'=>$itemId,'status'=>$status]);return['ok'=>false,'reason'=>'leader_without_whatsapp'];}
    $dest=v1417_digits((string)$to['whatsapp']);$type='whatsapp_scale_response_leader';
    if(v1417_recently_sent($itemId,$status,$dest,$type))return['ok'=>true,'deduped'=>true,'recipient_id'=>$to['id']??null];
    $confirmed=in_array($status,['confirmado','tarde'],true);
    $title=$confirmed?'✅ *Confirmação de escala*':'❌ *Indisponibilidade na escala*';
    $action=$confirmed?'confirmou presença na escala.':'informou que não poderá participar da escala.';
    $reason=trim((string)($item['justificativa_recusa']??''));
    $msg=$title."\n\n👤 *".($item['voluntario_nome']?:'Voluntário')."* ".$action.
        "\n📋 ".($item['culto_nome']?:'Culto').
        "\n📅 ".v1417_format_date((string)$item['data']).
        "\n🕒 ".substr((string)($item['horario']?:'--:--'),0,5).
        "\n⛪ ".($item['departamento_nome']?:'Ministério')." — ".$item['funcao'];
    if(!$confirmed&&$reason!=='')$msg.="\n💬 *Motivo:* ".$reason;
    if($status==='tarde')$msg.="\n⚠️ Confirmação registrada após o horário de início.";
    $msg.="\n\nA resposta já foi registrada no *Escala de Propósito*.";
    try{
        if(!function_exists('send_logged_whatsapp')&&is_file(__DIR__.'/whatsapp_lib.php'))require_once __DIR__.'/whatsapp_lib.php';
        if(!function_exists('send_logged_whatsapp'))return['ok'=>false,'reason'=>'whatsapp_lib_missing'];
        $res=send_logged_whatsapp($type,$dest,$msg,$item['igreja_id']?:null,[
            'escala_id'=>$item['escala_id'],'escala_item_id'=>$itemId,'voluntario_id'=>$item['voluntario_id'],
            'recipient_id'=>$to['id']??null,'recipient_name'=>$to['nome']??null,'status'=>$status,'source'=>$source,'v'=>'1.4.17'
        ]);
        $ok=is_array($res)?!empty($res['ok']):($res!==false);
        v1417_trace($ok?'sent':'failed',['item'=>$itemId,'status'=>$status,'recipient'=>$to['id']??null,'source'=>$source]);
        return['ok'=>$ok,'recipient_id'=>$to['id']??null,'recipient_name'=>$to['nome']??null,'status'=>$status];
    }catch(Throwable $e){v1417_trace('exception',['item'=>$itemId,'message'=>substr($e->getMessage(),0,240)]);return['ok'=>false,'reason'=>'exception'];}
}
function v1417_notify_refusal_reason(string $itemId,string $source='whatsapp'):array{
    $item=v1417_item($itemId);if(!$item)return['ok'=>false,'reason'=>'item_not_found'];
    $reason=trim((string)($item['justificativa_recusa']??''));if($reason==='')return['ok'=>false,'reason'=>'no_reason'];
    $to=v1417_recipient($item);if(!$to)return['ok'=>false,'reason'=>'leader_without_whatsapp'];
    $dest=v1417_digits((string)$to['whatsapp']);$type='whatsapp_scale_refusal_reason_leader';$status='recusado_reason';
    if(v1417_recently_sent($itemId,$status,$dest,$type))return['ok'=>true,'deduped'=>true];
    $msg="📝 *Motivo da indisponibilidade*\n\n👤 *".($item['voluntario_nome']?:'Voluntário')."*\n📋 ".($item['culto_nome']?:'Culto')."\n📅 ".v1417_format_date((string)$item['data'])."\n⛪ ".($item['departamento_nome']?:'Ministério')." — ".$item['funcao']."\n💬 *Motivo:* ".$reason;
    try{if(!function_exists('send_logged_whatsapp')&&is_file(__DIR__.'/whatsapp_lib.php'))require_once __DIR__.'/whatsapp_lib.php';$res=send_logged_whatsapp($type,$dest,$msg,$item['igreja_id']?:null,['escala_id'=>$item['escala_id'],'escala_item_id'=>$itemId,'voluntario_id'=>$item['voluntario_id'],'recipient_id'=>$to['id']??null,'status'=>$status,'source'=>$source,'v'=>'1.4.17']);$ok=is_array($res)?!empty($res['ok']):($res!==false);return['ok'=>$ok];}catch(Throwable $e){return['ok'=>false,'reason'=>'exception'];}
}
''',encoding='utf-8')

endpoint.write_text(r'''<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
require_once __DIR__.'/scale_response_notify_v1417.php';
try{
    $caller=require_auth();$uid=(string)($caller['id']??'');$req=input_json();
    $itemId=trim((string)($req['escala_item_id']??''));$requested=trim((string)($req['resposta']??''));
    if($itemId==='')out(['data'=>null,'error'=>['message'=>'Item da escala não informado']],400);
    $item=v1417_item($itemId);if(!$item)out(['data'=>null,'error'=>['message'=>'Escala não encontrada']],404);
    $allowed=$uid!==''&&$uid===(string)$item['voluntario_id'];
    if(!$allowed){try{$ctx=user_context();$role=(string)($ctx['role']??'');$ig=(string)($ctx['igreja_id']??'');$allowed=in_array($role,['master','admin','lider'],true)&&($role==='master'||$ig===(string)$item['igreja_id']);}catch(Throwable $e){}}
    if(!$allowed)out(['data'=>null,'error'=>['message'=>'Sem permissão']],403);
    $status=(string)($item['status_confirmacao']??'');if($status==='')$status=$requested;
    $r=v1417_notify_scale_response($itemId,$status,'app');
    out(['data'=>$r,'error'=>null]);
}catch(Throwable $e){out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);}
''',encoding='utf-8')

p=api/'confirmation_router_v1311.php'; s=p.read_text(encoding='utf-8')
if "scale_response_notify_v1417.php" not in s:
    marker="declare(strict_types=1);"
    s=s.replace(marker,marker+"\nrequire_once __DIR__.'/scale_response_notify_v1417.php';",1)
old="""function v1311_notify_leader(array $item, string $status): void {
    try {
        $desc = $status==='confirmado' || $status==='tarde'
            ? ($item['voluntario_nome'].' confirmou a escala de '.$item['data'].'.')
            : ($item['voluntario_nome'].' informou que não poderá participar da escala de '.$item['data'].'.');
        db()->prepare("INSERT INTO admin_notifications(id,igreja_id,tipo,titulo,descricao,meta,lida,created_at,updated_at)
            VALUES(?,?,?,?,?,?,0,NOW(),NOW())")
            ->execute([uuid4(),$item['igreja_id'] ?: null,'resposta_escala',$status==='recusado'?'Voluntário recusou a escala':'Escala confirmada',$desc,
                json_encode(['escala_id'=>$item['escala_id'],'escala_item_id'=>$item['item_id'],'voluntario_id'=>$item['voluntario_id'],'status'=>$status],JSON_UNESCAPED_UNICODE)]);
    } catch (Throwable $e) {}
}"""
new=old[:-1]+"\n    try { v1417_notify_scale_response((string)$item['item_id'],$status,'whatsapp'); } catch (Throwable $e) {}\n}"
if old not in s: raise SystemExit('v1311_notify_leader block not found')
s=s.replace(old,new,1);p.write_text(s,encoding='utf-8')

p=api/'pending_router_v1311.php'; s=p.read_text(encoding='utf-8')
needle="v1311p_send($sender,(string)($item['igreja_id']??''),\"✅ *Motivo registrado.*"
if needle not in s: raise SystemExit('pending reason marker not found')
s=s.replace(needle,"try{if(function_exists('v1417_notify_refusal_reason'))v1417_notify_refusal_reason((string)$item['item_id'],'whatsapp');}catch(Throwable $ignored){} "+needle,1)
p.write_text(s,encoding='utf-8')

p=root/'assets/index-C6Ng0a8i.js'; s=p.read_text(encoding='utf-8')
old='pV={async invoke(e,t){const n=await Br("functions.php",{name:e,body:(t==null?void 0:t.body)||{}});return{data:(n==null?void 0:n.data)??null,error:Vr(n==null?void 0:n.error)}}}'
new='pV={async invoke(e,t){const n=e==="notify-leader"?await Br("scale-response-notify.php",{...((t==null?void 0:t.body)||{}),action:"notify"}):await Br("functions.php",{name:e,body:(t==null?void 0:t.body)||{}});return{data:(n==null?void 0:n.data)??null,error:Vr(n==null?void 0:n.error)}}}'
if old not in s: raise SystemExit('functions invoke marker not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

p=root/'sistema.html'; s=p.read_text(encoding='utf-8')
s=s.replace('/assets/index-C6Ng0a8i.js?v=1.4.16','/assets/index-C6Ng0a8i.js?v=1.4.17')
p.write_text(s,encoding='utf-8')
p=root/'sw.js'; s=p.read_text(encoding='utf-8')
s += "\n/* scale-response-leader-whatsapp-v1.4.17 */\n"
p.write_text(s,encoding='utf-8')
