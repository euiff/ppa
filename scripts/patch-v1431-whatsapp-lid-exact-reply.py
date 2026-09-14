from pathlib import Path
import re, sys
root=Path(sys.argv[1]); api=root/'api'

# --- confirmation router: recover LID from historical outbound response, prefer exact active context, reply to exact LID ---
p=api/'confirmation_router_v1311.php'; s=p.read_text(encoding='utf-8')

anchor="""function v1427_reply_phone(array $msg,array $profiles=[]): string {
"""
if anchor not in s: raise SystemExit('reply_phone anchor missing')
insert=r'''function v1431_remember_lid_phone(string $lid,string $phone): void {
    if(!str_contains($lid,'@lid'))return;
    $phone=v1311_digits($phone);if(strlen($phone)<10||strlen($phone)>14)return;
    $k=v1427_lid_key($lid);if($k==='')return;
    v1427_identity_schema();
    try{db()->prepare("INSERT INTO whatsapp_identity_aliases(alias_key,phone,last_seen_at,created_at) VALUES(?,?,NOW(),NOW()) ON DUPLICATE KEY UPDATE phone=VALUES(phone),last_seen_at=NOW()")->execute([$k,$phone]);}catch(Throwable $e){}
}
function v1431_phone_from_historical_lid(string $lid): string {
    if(!str_contains($lid,'@lid'))return '';
    try{
        $q=db()->prepare("SELECT destinatario FROM notification_logs WHERE created_at>=DATE_SUB(NOW(),INTERVAL 30 DAY) AND response_body LIKE ? ORDER BY created_at DESC LIMIT 1");
        $q->execute(['%'.$lid.'%']);$p=v1311_digits((string)($q->fetchColumn()?:''));
        if(strlen($p)>=10&&strlen($p)<=14){v1431_remember_lid_phone($lid,$p);return$p;}
    }catch(Throwable $e){}
    try{
        $q=db()->prepare("SELECT p.whatsapp FROM whatsapp_send_jobs j JOIN escala_itens ei ON BINARY ei.id=BINARY j.escala_item_id JOIN profiles p ON BINARY p.id=BINARY ei.voluntario_id WHERE j.job_type='escala_notification' AND j.updated_at>=DATE_SUB(NOW(),INTERVAL 30 DAY) AND j.result LIKE ? ORDER BY j.updated_at DESC LIMIT 1");
        $q->execute(['%'.$lid.'%']);$p=v1311_digits((string)($q->fetchColumn()?:''));
        if(strlen($p)>=10&&strlen($p)<=14){v1431_remember_lid_phone($lid,$p);return$p;}
    }catch(Throwable $e){}
    return '';
}
function v1431_reply_recipient(array $msg,array $profiles=[]): string {
    $primary=trim((string)($msg['primary_identity']??''));
    if($primary!==''&&str_contains($primary,'@lid'))return $primary;
    foreach(($msg['identities']??[]) as $id){$id=(string)$id;if(str_contains($id,'@lid'))return$id;}
    return v1427_reply_phone($msg,$profiles);
}

'''
s=s.replace(anchor,insert+anchor,1)

old="""        }else{
            foreach(array_unique($lids) as $k){try{$q=db()->prepare("SELECT phone FROM whatsapp_identity_aliases WHERE alias_key=? AND last_seen_at>=DATE_SUB(NOW(),INTERVAL 180 DAY) LIMIT 1");$q->execute([$k]);$p=(string)($q->fetchColumn()?:'');if($p!==''&&strlen($p)>=10&&strlen($p)<=14){$identities[]=$p;break;}}catch(Throwable $e){}}
        }
"""
new="""        }else{
            foreach(array_unique($lids) as $k){try{$q=db()->prepare("SELECT phone FROM whatsapp_identity_aliases WHERE alias_key=? AND last_seen_at>=DATE_SUB(NOW(),INTERVAL 180 DAY) LIMIT 1");$q->execute([$k]);$p=(string)($q->fetchColumn()?:'');if($p!==''&&strlen($p)>=10&&strlen($p)<=14){$identities[]=$p;break;} $rawLid=substr($k,4).'@lid';$p=v1431_phone_from_historical_lid($rawLid);if($p!==''){$identities[]=$p;break;}}catch(Throwable $e){}}
        }
"""
if old not in s: raise SystemExit('alias fallback anchor missing')
s=s.replace(old,new,1)

old="""    $instanceSender = is_scalar($body['sender'] ?? null) ? trim((string)$body['sender']) : '';
    $normalized = function_exists('mb_strtolower') ? mb_strtolower(trim($text), 'UTF-8') : strtolower(trim($text));
"""
new="""    $instanceSender = is_scalar($body['sender'] ?? null) ? trim((string)$body['sender']) : '';
    $dataTop=is_array($body['data']??null)?$body['data']:[];$keyTop=is_array($dataTop['key']??null)?$dataTop['key']:[];
    $primaryIdentity=is_scalar($keyTop['remoteJid']??null)?trim((string)$keyTop['remoteJid']):'';
    $primaryAlt=is_scalar($keyTop['remoteJidAlt']??null)?trim((string)$keyTop['remoteJidAlt']):'';
    $normalized = function_exists('mb_strtolower') ? mb_strtolower(trim($text), 'UTF-8') : strtolower(trim($text));
"""
if old not in s: raise SystemExit('primary identity anchor missing')
s=s.replace(old,new,1)
old="""        'instance_sender' => $instanceSender,
        'instance_sender_label' => $instanceSender!=='' ? v1311_identity_mask($instanceSender) : '',
"""
new="""        'instance_sender' => $instanceSender,
        'instance_sender_label' => $instanceSender!=='' ? v1311_identity_mask($instanceSender) : '',
        'primary_identity' => $primaryIdentity,
        'primary_alt' => $primaryAlt,
"""
if old not in s: raise SystemExit('return primary anchor missing')
s=s.replace(old,new,1)

old="""        foreach ($rows as $ctx) {
            if (!isset($ids[(string)$ctx['voluntario_id']])) continue;
            $phoneMatch = false;
            foreach ($identities as $identity) if (v1311_same_phone((string)$ctx['sender'], (string)$identity)) { $phoneMatch=true; break; }
            if (!$phoneMatch) continue;
            $item = v1311_item_row((string)$ctx['escala_item_id']);
            if ($item) { $item['_context_id']=$ctx['id']; $item['_anchor']='context'; return $item; }
        }
"""
new="""        foreach ($rows as $ctx) {
            if (!isset($ids[(string)$ctx['voluntario_id']])) continue;
            $phoneMatch = false;
            foreach ($identities as $identity) if (v1311_same_phone((string)$ctx['sender'], (string)$identity)) { $phoneMatch=true; break; }
            if (!$phoneMatch && count($profiles)!==1) continue;
            $item = v1311_item_row((string)$ctx['escala_item_id']);
            if ($item) { $item['_context_id']=$ctx['id']; $item['_anchor']=$phoneMatch?'context':'profile_context_v1431'; return $item; }
        }
"""
if old not in s: raise SystemExit('context candidate anchor missing')
s=s.replace(old,new,1)

old="""    $item = v1311_notification_candidate($msg['identities']);
    v1311_trace('candidate_scan',[
"""
new="""    $item = $profiles?v1311_context_candidate($msg['identities'],$profiles):null;
    if(!$item)$item = v1311_notification_candidate($msg['identities']);
    v1311_trace('candidate_scan',[
"""
if old not in s: raise SystemExit('candidate order anchor missing')
s=s.replace(old,new,1)

s=s.replace("$replyTo=v1427_reply_phone($msg,$profiles);if($replyTo!=='')$item['_reply_to']=$replyTo;","$replyTo=v1431_reply_recipient($msg,$profiles);if($replyTo!=='')$item['_reply_to']=$replyTo;",1)

old="""    $dest=function_exists('v1427_reply_phone')?v1427_reply_phone($msg,$profiles):'';
"""
new="""    $dest=function_exists('v1431_reply_recipient')?v1431_reply_recipient($msg,$profiles):(function_exists('v1427_reply_phone')?v1427_reply_phone($msg,$profiles):'');
"""
if old not in s: raise SystemExit('unresolved recipient anchor missing')
s=s.replace(old,new,1)

old="""        if(!$ok&&$saved!==''&&$replyTo!==$saved&&v1311_same_phone($replyTo,$saved)){
"""
new="""        if(!$ok&&$saved!==''&&$replyTo!==$saved){
"""
if old not in s: raise SystemExit('reply fallback condition anchor missing')
s=s.replace(old,new,1)
s=s.replace("'router'=>'v1.4.29'","'router'=>'v1.4.31'",1)
p.write_text(s,encoding='utf-8')

p=api/'pending_router_v1311.php'; s=p.read_text(encoding='utf-8')
old="function v1311p_sender(array $msg, array $profiles): string { if(function_exists('v1427_reply_phone')){$d=v1427_reply_phone($msg,$profiles);if($d!=='')return$d;}"
new="function v1311p_sender(array $msg, array $profiles): string { if(function_exists('v1431_reply_recipient')){$d=v1431_reply_recipient($msg,$profiles);if($d!=='')return$d;} if(function_exists('v1427_reply_phone')){$d=v1427_reply_phone($msg,$profiles);if($d!=='')return$d;}"
if old not in s: raise SystemExit('pending sender anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

p=api/'quiz_router_v131.php'; s=p.read_text(encoding='utf-8')
old="""    $msg = v131_parse_inbound($body);
    $robust=null;$robustProfiles=[];$robustReply='';
    if(function_exists('v1311_parse_inbound')){
        try{$robust=v1311_parse_inbound($body);if(function_exists('v1311_find_profiles'))$robustProfiles=v1311_find_profiles($robust['identities']??[]);if(function_exists('v1427_reply_phone'))$robustReply=v1427_reply_phone($robust,$robustProfiles);}catch(Throwable $e){}
    }
"""
new="""    $msg = v131_parse_inbound($body);
    $robust=null;$robustProfiles=[];$robustReply='';$robustAddress='';
    if(function_exists('v1311_parse_inbound')){
        try{$robust=v1311_parse_inbound($body);if(function_exists('v1311_find_profiles'))$robustProfiles=v1311_find_profiles($robust['identities']??[]);if(function_exists('v1427_reply_phone'))$robustReply=v1427_reply_phone($robust,$robustProfiles);if(function_exists('v1431_reply_recipient'))$robustAddress=v1431_reply_recipient($robust,$robustProfiles);}catch(Throwable $e){}
    }
"""
if old not in s: raise SystemExit('quiz robust anchor missing')
s=s.replace(old,new,1)
old="""    if(!$quiz&&$robustReply!=='')$quiz=v131_find_active_quiz($robustReply);
    if (!$quiz) return false;
    if($robustReply!=='')$quiz['_reply_to']=$robustReply;
"""
new="""    if(!$quiz&&$robustReply!=='')$quiz=v131_find_active_quiz($robustReply);
    if (!$quiz) return false;
    if($robustAddress!=='')$quiz['_reply_to']=$robustAddress;elseif($robustReply!=='')$quiz['_reply_to']=$robustReply;
"""
if old not in s: raise SystemExit('quiz reply address anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

p=api/'whatsapp_transport_v1424.php'; s=p.read_text(encoding='utf-8')
old="""function v1424_phone(string $phone): string {
    if(function_exists('normalize_phone')) return normalize_phone($phone);
    $d=preg_replace('/\\D+/','',$phone)?:'';
    if(strlen($d)>=10 && !str_starts_with($d,'55'))$d='55'.$d;
    return $d;
}
"""
insert=r'''function v1431_recipient(string $recipient): string {
    $r=trim($recipient);
    if(preg_match('/^[0-9]+@(lid|s\\.whatsapp\\.net|c\\.us)$/i',$r))return$r;
    return v1424_phone($r);
}
function v1431_learn_outbound_aliases(string $original,array $res): void {
    if(!function_exists('db')||str_contains($original,'@lid'))return;
    $phone=v1424_phone($original);if(str_contains($phone,'@')||strlen($phone)<10)return;
    $lids=[];$walk=null;$walk=static function($v)use(&$walk,&$lids){if(is_array($v)){foreach($v as$x)$walk($x);return;}if(is_scalar($v)){$x=trim((string)$v);if(preg_match('/^[0-9]+@lid$/',$x))$lids[$x]=true;}};$walk($res);
    if(!$lids)return;
    try{db()->exec("CREATE TABLE IF NOT EXISTS whatsapp_identity_aliases (alias_key VARCHAR(80) NOT NULL PRIMARY KEY,phone VARCHAR(20) NOT NULL,last_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,KEY idx_whatsapp_identity_phone (phone),KEY idx_whatsapp_identity_seen (last_seen_at)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");foreach(array_keys($lids) as$lid){$k='lid:'.preg_replace('/\\D+/','',$lid);db()->prepare("INSERT INTO whatsapp_identity_aliases(alias_key,phone,last_seen_at,created_at) VALUES(?,?,NOW(),NOW()) ON DUPLICATE KEY UPDATE phone=VALUES(phone),last_seen_at=NOW()")->execute([$k,$phone]);}}catch(Throwable $e){}
}
'''
if old not in s: raise SystemExit('v1424_phone full block missing')
s=s.replace(old,old+insert,1)

old="""    $number=v1424_phone($number);if(strlen($number)<10)return ['ok'=>false,'status'=>0,'error'=>'Número de WhatsApp inválido','payload_mode'=>'text','number'=>$number];
    $url=$base.'/message/sendText/'.rawurlencode($instance);$headers=['Content-Type: application/json','apikey: '.$key];
    $payload=['number'=>$number,'text'=>$text];
"""
new="""    $number=v1431_recipient($number);$digits=preg_replace('/\\D+/','',$number)?:'';if(!str_contains($number,'@')&&strlen($digits)<10)return ['ok'=>false,'status'=>0,'error'=>'Número de WhatsApp inválido','payload_mode'=>'text','number'=>$number];
    $url=$base.'/message/sendText/'.rawurlencode($instance);$headers=['Content-Type: application/json','apikey: '.$key];
    $payload=['number'=>$number,'text'=>$text];
"""
if old not in s: raise SystemExit('recipient normalize anchor missing')
s=s.replace(old,new,1)
s=s.replace("foreach(v1429_br_phone_variants($number) as $alt){","foreach(str_contains($number,'@')?[]:v1429_br_phone_variants($number) as $alt){",1)
s=s.replace("v1424_phone($phone),$message];","v1431_recipient($phone),$message];",1)
s=s.replace("[$id,$key,$tipo,v1424_phone($phone),$igrejaId?:null,$message", "[$id,$key,$tipo,v1431_recipient($phone),$igrejaId?:null,$message",1)
old="""    $res=v1424_evolution_send($phone,$message,$igrejaId);
    if($outboxId!=='')v1430_reply_outbox_finish($outboxId,$res);
    $meta['transport_version']='1.4.30';$meta['payload_mode']=$res['payload_mode']??'text';
"""
new="""    $res=v1424_evolution_send($phone,$message,$igrejaId);
    v1431_learn_outbound_aliases($phone,$res);
    if($outboxId!=='')v1430_reply_outbox_finish($outboxId,$res);
    $meta['transport_version']='1.4.31';$meta['payload_mode']=$res['payload_mode']??'text';
"""
if old not in s: raise SystemExit('transport send anchor missing')
s=s.replace(old,new,1)
s=s.replace("log_whatsapp($tipo,v1424_phone($phone),$message,$res,$igrejaId,$meta);","log_whatsapp($tipo,v1431_recipient($phone),$message,$res,$igrejaId,$meta);",1)
p.write_text(s,encoding='utf-8')

p=root/'sistema.html'; s=p.read_text(encoding='utf-8'); s=re.sub(r'/assets/index-C6Ng0a8i\\.js\\?v=[^\"<]+','/assets/index-C6Ng0a8i.js?v=1.4.31',s); p.write_text(s,encoding='utf-8')
p=root/'sw.js'; s=p.read_text(encoding='utf-8'); s+='\n/* whatsapp-lid-exact-reply-v1.4.31 */\n'; p.write_text(s,encoding='utf-8')

mig=root/'database/migrations/20260914_1431_whatsapp_lid_exact_reply.sql'
mig.write_text("""CREATE TABLE IF NOT EXISTS whatsapp_identity_aliases (
 alias_key VARCHAR(80) NOT NULL PRIMARY KEY,
 phone VARCHAR(20) NOT NULL,
 last_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 KEY idx_whatsapp_identity_phone (phone), KEY idx_whatsapp_identity_seen (last_seen_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS whatsapp_reply_outbox (
 id VARCHAR(36) NOT NULL PRIMARY KEY,
 dedupe_key VARCHAR(64) NOT NULL,
 tipo VARCHAR(80) NOT NULL,
 phone VARCHAR(80) NOT NULL,
 igreja_id VARCHAR(36) NULL,
 message LONGTEXT NOT NULL,
 meta_json LONGTEXT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'pending',
 attempts INT NOT NULL DEFAULT 0,
 next_attempt_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 last_error VARCHAR(1000) NULL,
 sent_at DATETIME NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uq_reply_outbox_dedupe (dedupe_key),
 KEY idx_reply_outbox_due (status,next_attempt_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
ALTER TABLE whatsapp_reply_outbox MODIFY phone VARCHAR(80) NOT NULL;
""",encoding='utf-8')
