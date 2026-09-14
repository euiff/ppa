from pathlib import Path
import re, sys
root=Path(sys.argv[1]); api=root/'api'

# 1) Rescue the actual contact number on Evolution payloads that use @lid.
p=api/'confirmation_router_v1311.php'; s=p.read_text(encoding='utf-8')
old="""        // Evolution v2: a identidade real da conversa vem em key.remoteJid/
        // remoteJidAlt e campos PN/participant. O campo sender do topo e o numero
        // da instancia conectada e NAO deve ser usado para localizar o voluntario.
        foreach ([
            ['key','remoteJidAlt'], ['key','remoteJidPn'], ['key','remoteJid'],
            ['key','participantAlt'], ['key','participantPn'], ['key','participant'], ['key','senderPn'],
            ['remoteJidAlt'], ['remoteJidPn'], ['remoteJid'],
            ['participantAlt'], ['participantPn'], ['participant'], ['senderPn']
        ] as $path) {
            $v = v1311_nested($layer,$path);
            if ($v !== null) $addIdentity($v,implode('.',$path));
        }
    }

    // Fallback somente para sender dentro de data, usado por alguns wrappers.
    // Nunca mistura body.sender com o contato: body.sender identifica a instancia.
    if (!$identities && isset($body['data']) && is_array($body['data'])) {
        foreach (['senderPn','sender','participantPn','participant','remoteJidAlt','remoteJid'] as $key) {
            if (isset($body['data'][$key])) $addIdentity($body['data'][$key],'data.'.$key);
        }
    }
"""
new="""        // Evolution/Baileys pode entregar o contato como PN ou como LID.
        // Coletamos todas as identidades de conversa conhecidas e depois usamos
        // body.sender/data.sender apenas como resgate quando so existe LID.
        foreach ([
            ['key','remoteJidAlt'], ['key','remoteJidPn'], ['key','remoteJid'],
            ['key','participantAlt'], ['key','participantPn'], ['key','participant'], ['key','senderPn'],
            ['remoteJidAlt'], ['remoteJidPn'], ['remoteJid'],
            ['participantAlt'], ['participantPn'], ['participant'], ['senderPn']
        ] as $path) {
            $v = v1311_nested($layer,$path);
            if ($v !== null) $addIdentity($v,implode('.',$path));
        }
    }

    // Em algumas versoes da Evolution o remoteJid chega somente como @lid,
    // enquanto o numero real do contato vem em body.sender ou data.sender.
    // So usamos estes campos quando ainda nao existe um PN/telefone direto,
    // evitando misturar o numero da instancia em payloads antigos.
    $hasDirectPhone=false;
    foreach(array_keys($identities) as $id){
        $raw=(string)$id;$digits=v1311_digits($raw);
        if(!str_contains($raw,'@lid')&&!str_contains($raw,'@g.us')&&
           (str_contains($raw,'@s.whatsapp.net')||str_contains($raw,'@c.us')||(strlen($digits)>=10&&strlen($digits)<=14))){$hasDirectPhone=true;break;}
    }
    if($fromMe!==true && !$hasDirectPhone){
        $senderCandidates=[
            'body.sender'=>$body['sender']??null,
            'data.sender'=>(is_array($body['data']??null)?($body['data']['sender']??null):null),
            'data.senderPn'=>(is_array($body['data']??null)?($body['data']['senderPn']??null):null),
        ];
        foreach($senderCandidates as $source=>$candidate){
            if(!is_scalar($candidate))continue;$raw=trim((string)$candidate);$digits=v1311_digits($raw);
            if($raw===''||str_contains($raw,'@lid')||str_contains($raw,'@g.us')||str_contains($raw,'@broadcast'))continue;
            if(str_contains($raw,'@s.whatsapp.net')||str_contains($raw,'@c.us')||(strlen($digits)>=10&&strlen($digits)<=14)){$addIdentity($raw,$source);}
        }
    }

    // Ultimo fallback para wrappers que colocam tudo dentro de data.
    if (!$identities && isset($body['data']) && is_array($body['data'])) {
        foreach (['senderPn','sender','participantPn','participant','remoteJidAlt','remoteJid'] as $key) {
            if (isset($body['data'][$key])) $addIdentity($body['data'][$key],'data.'.$key);
        }
    }
"""
if old not in s: raise SystemExit('parser identity anchor not found')
s=s.replace(old,new,1)

old="""function v1311_unresolved_reply(array $msg, array $profiles): bool {
    $dest='';
    foreach(($msg['identities']??[]) as $identity){
        if(str_contains((string)$identity,'@g.us')||str_contains((string)$identity,'@lid'))continue;
        $d=v1311_digits((string)$identity);
        if(strlen($d)>=10&&strlen($d)<=14){$dest=$d;break;}
    }
    if($dest==='')return false;
"""
new="""function v1311_unresolved_reply(array $msg, array $profiles): bool {
    $dest=function_exists('v1427_reply_phone')?v1427_reply_phone($msg,$profiles):'';
    if($dest===''){
        foreach(($msg['identities']??[]) as $identity){
            if(str_contains((string)$identity,'@g.us')||str_contains((string)$identity,'@lid'))continue;
            $d=v1311_digits((string)$identity);
            if(strlen($d)>=10&&strlen($d)<=14){$dest=$d;break;}
        }
    }
    if($dest==='')return false;
"""
if old not in s: raise SystemExit('unresolved reply anchor not found')
s=s.replace(old,new,1)

old="""    $profiles = v1311_find_profiles($msg['identities']);
    $latestIntent=v1429_latest_prompt_intent($msg['identities'],$profiles);
"""
new="""    $profiles = v1311_find_profiles($msg['identities']);
    if($profiles){
        try{
            $phone=v1311_digits((string)($profiles[0]['whatsapp']??''));
            if(strlen($phone)>=10){v1427_identity_schema();foreach(($msg['identities']??[]) as $identity){$k=v1427_lid_key((string)$identity);if($k!=='')db()->prepare("INSERT INTO whatsapp_identity_aliases(alias_key,phone,last_seen_at,created_at) VALUES(?,?,NOW(),NOW()) ON DUPLICATE KEY UPDATE phone=VALUES(phone),last_seen_at=NOW()")->execute([$k,$phone]);}}
        }catch(Throwable $e){}
    }
    $latestIntent=v1429_latest_prompt_intent($msg['identities'],$profiles);
"""
if old not in s: raise SystemExit('profile learn anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

# 2) Persistent reply outbox: interactive responses are never silently lost.
p=api/'whatsapp_transport_v1424.php'; s=p.read_text(encoding='utf-8')
anchor="""function v1424_send_logged_whatsapp(string $tipo,string $phone,string $message,?string $igrejaId=null,array $meta=[]): array {
"""
insert=r'''function v1430_is_interactive_reply_type(string $tipo): bool {
    return in_array($tipo,['whatsapp_confirmation_reply','whatsapp_confirmation_unresolved','whatsapp_quiz_reply','whatsapp_pending_menu'],true);
}
function v1430_reply_outbox_schema(): void {
    if(!function_exists('db'))return;
    try{db()->exec("CREATE TABLE IF NOT EXISTS whatsapp_reply_outbox (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        dedupe_key VARCHAR(64) NOT NULL,
        tipo VARCHAR(80) NOT NULL,
        phone VARCHAR(32) NOT NULL,
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");}catch(Throwable $e){}
}
function v1430_reply_outbox_enqueue(string $tipo,string $phone,string $message,?string $igrejaId,array $meta): string {
    if(!v1430_is_interactive_reply_type($tipo)||!function_exists('db'))return '';
    v1430_reply_outbox_schema();
    $stable=[(string)($meta['escala_item_id']??''),(string)($meta['quiz_id']??''),(string)($meta['reply_reason']??''),v1424_phone($phone),$message];
    $key=hash('sha256',implode('|',$stable));$id=function_exists('uuid4')?uuid4():bin2hex(random_bytes(16));
    try{db()->prepare("INSERT INTO whatsapp_reply_outbox(id,dedupe_key,tipo,phone,igreja_id,message,meta_json,status,attempts,next_attempt_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,'pending',0,NOW(),NOW(),NOW()) ON DUPLICATE KEY UPDATE phone=VALUES(phone),igreja_id=VALUES(igreja_id),message=VALUES(message),meta_json=VALUES(meta_json),updated_at=NOW()")
        ->execute([$id,$key,$tipo,v1424_phone($phone),$igrejaId?:null,$message,json_encode($meta,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)]);
        $q=db()->prepare("SELECT id FROM whatsapp_reply_outbox WHERE dedupe_key=? LIMIT 1");$q->execute([$key]);return (string)($q->fetchColumn()?:$id);
    }catch(Throwable $e){return '';}
}
function v1430_reply_outbox_finish(string $id,array $res): void {
    if($id===''||!function_exists('db'))return;
    try{
        if(!empty($res['ok'])){db()->prepare("UPDATE whatsapp_reply_outbox SET status='sent',attempts=attempts+1,last_error=NULL,sent_at=NOW(),updated_at=NOW() WHERE id=?")->execute([$id]);}
        else{$err=(string)($res['error']??$res['message']??('HTTP '.($res['status']??0)));db()->prepare("UPDATE whatsapp_reply_outbox SET status='pending',attempts=attempts+1,last_error=?,next_attempt_at=DATE_ADD(NOW(),INTERVAL 1 MINUTE),updated_at=NOW() WHERE id=?")->execute([substr($err,0,1000),$id]);}
    }catch(Throwable $e){}
}
function v1424_send_logged_whatsapp(string $tipo,string $phone,string $message,?string $igrejaId=null,array $meta=[]): array {
'''
if anchor not in s: raise SystemExit('transport outbox anchor not found')
s=s.replace(anchor,insert,1)
old="""    $res=v1424_evolution_send($phone,$message,$igrejaId);
    $meta['transport_version']='1.4.29';$meta['payload_mode']=$res['payload_mode']??'text';
"""
new="""    $outboxId='';if(empty($meta['_outbox_retry']))$outboxId=v1430_reply_outbox_enqueue($tipo,$phone,$message,$igrejaId,$meta);
    $res=v1424_evolution_send($phone,$message,$igrejaId);
    if($outboxId!=='')v1430_reply_outbox_finish($outboxId,$res);
    $meta['transport_version']='1.4.30';$meta['payload_mode']=$res['payload_mode']??'text';
    if($outboxId!=='')$meta['reply_outbox_id']=$outboxId;
"""
if old not in s: raise SystemExit('transport send anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

# 3) Cron retries replies that could not be delivered immediately.
p=api/'automation_v130.php'; s=p.read_text(encoding='utf-8')
anchor="function v130_retry_failed_jobs():int{"
worker=r'''function v1430_process_reply_outbox(int $limit=10): array {
    if(!function_exists('v1430_reply_outbox_schema')||!function_exists('db'))return ['processed'=>0,'sent'=>0,'failed'=>0];
    v1430_reply_outbox_schema();$processed=0;$sent=0;$failed=0;
    try{$q=db()->prepare("SELECT * FROM whatsapp_reply_outbox WHERE status='pending' AND attempts<8 AND next_attempt_at<=NOW() ORDER BY created_at ASC LIMIT ".$limit);$q->execute();$rows=$q->fetchAll();}catch(Throwable $e){return ['processed'=>0,'sent'=>0,'failed'=>0];}
    foreach($rows as $r){
        try{$lock=db()->prepare("UPDATE whatsapp_reply_outbox SET status='running',updated_at=NOW() WHERE id=? AND status='pending'");$lock->execute([$r['id']]);if(!$lock->rowCount())continue;$processed++;
            $meta=json_decode((string)($r['meta_json']??''),true);if(!is_array($meta))$meta=[];$meta['_outbox_retry']=true;$meta['reply_outbox_retry']=true;
            $res=v1424_send_logged_whatsapp((string)$r['tipo'],(string)$r['phone'],(string)$r['message'],($r['igreja_id']??'')?:null,$meta);
            if(!empty($res['ok'])){db()->prepare("UPDATE whatsapp_reply_outbox SET status='sent',attempts=attempts+1,last_error=NULL,sent_at=NOW(),updated_at=NOW() WHERE id=?")->execute([$r['id']]);$sent++;}
            else{$a=(int)$r['attempts']+1;$mins=$a<=2?1:($a<=4?2:5);$err=(string)($res['error']??$res['message']??('HTTP '.($res['status']??0)));$status=$a>=8?'failed':'pending';db()->prepare("UPDATE whatsapp_reply_outbox SET status=?,attempts=?,last_error=?,next_attempt_at=DATE_ADD(NOW(),INTERVAL ".$mins." MINUTE),updated_at=NOW() WHERE id=?")->execute([$status,$a,substr($err,0,1000),$r['id']]);$failed++;}
        }catch(Throwable $e){$failed++;try{db()->prepare("UPDATE whatsapp_reply_outbox SET status='pending',attempts=attempts+1,last_error=?,next_attempt_at=DATE_ADD(NOW(),INTERVAL 1 MINUTE),updated_at=NOW() WHERE id=?")->execute([substr($e->getMessage(),0,1000),$r['id']]);}catch(Throwable $z){}}
    }
    return ['processed'=>$processed,'sent'=>$sent,'failed'=>$failed];
}
function v130_retry_failed_jobs():int{'''
if anchor not in s: raise SystemExit('automation worker anchor not found')
s=s.replace(anchor,worker,1)
s=s.replace("'delivery_retried'=>0,'native_notifications_queued'", "'delivery_retried'=>0,'reply_outbox_processed'=>0,'reply_outbox_sent'=>0,'reply_outbox_failed'=>0,'native_notifications_queued'",1)
needle="$s['failed_jobs_requeued']=v130_retry_failed_jobs();$x=v130_enqueue_missing();"
repl="$s['failed_jobs_requeued']=v130_retry_failed_jobs();$ro=v1430_process_reply_outbox(10);$s['reply_outbox_processed']=$ro['processed'];$s['reply_outbox_sent']=$ro['sent'];$s['reply_outbox_failed']=$ro['failed'];$x=v130_enqueue_missing();"
if needle not in s: raise SystemExit('automation run insertion anchor not found')
s=s.replace(needle,repl,1)
p.write_text(s,encoding='utf-8')

# 4) Migration and cache bust.
mig=root/'database/migrations/20260914_1430_whatsapp_inbound_reply_guarantee.sql'
mig.write_text("""CREATE TABLE IF NOT EXISTS whatsapp_reply_outbox (
 id VARCHAR(36) NOT NULL PRIMARY KEY,
 dedupe_key VARCHAR(64) NOT NULL,
 tipo VARCHAR(80) NOT NULL,
 phone VARCHAR(32) NOT NULL,
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
UPDATE api_config SET valor='' WHERE chave='whatsapp_webhook_sync_signature' AND igreja_id IS NULL;
UPDATE api_config SET valor='1970-01-01 00:00:00' WHERE chave='whatsapp_webhook_sync_last_at' AND igreja_id IS NULL;
""",encoding='utf-8')
p=root/'sistema.html'; s=p.read_text(encoding='utf-8'); s=re.sub(r'/assets/index-C6Ng0a8i\.js\?v[^\"<]*','/assets/index-C6Ng0a8i.js?v=1.4.30',s); p.write_text(s,encoding='utf-8')
p=root/'sw.js'; s=p.read_text(encoding='utf-8'); s+='\n/* whatsapp-inbound-reply-guarantee-v1.4.30 */\n'; p.write_text(s,encoding='utf-8')
