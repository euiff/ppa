from pathlib import Path
import re, sys
root=Path(sys.argv[1]); api=root/'api'

# 1) Prefer an inbound identity that actually matches the volunteer profile.
p=api/'confirmation_router_v1311.php'; s=p.read_text(encoding='utf-8')
old="""function v1427_reply_phone(array $msg,array $profiles=[]): string {
    foreach(($msg['identities']??[]) as $id){$p=v1427_plain_phone_from_identity((string)$id);if($p!=='')return$p;}
    foreach($profiles as $p){$d=v1311_digits((string)($p['whatsapp']??''));if(strlen($d)>=10&&strlen($d)<=14)return$d;}
    return '';
}
"""
new="""function v1427_reply_phone(array $msg,array $profiles=[]): string {
    $identities=array_values(array_filter(array_map('strval',$msg['identities']??[])));
    // Primeiro usa a identidade real do webhook que corresponde ao WhatsApp cadastrado.
    foreach($profiles as $profile){
        $saved=v1311_digits((string)($profile['whatsapp']??''));
        if(strlen($saved)<10||strlen($saved)>14)continue;
        foreach($identities as $id){
            $live=v1427_plain_phone_from_identity($id);
            if($live!==''&&v1311_same_phone($saved,$live))return $live;
        }
    }
    // Se o webhook trouxe apenas LID/identidade ambigua, o cadastro e mais seguro.
    foreach($profiles as $profile){$d=v1311_digits((string)($profile['whatsapp']??''));if(strlen($d)>=10&&strlen($d)<=14)return$d;}
    // Ultimo recurso quando ainda nao foi possivel localizar perfil.
    foreach($identities as $id){$p=v1427_plain_phone_from_identity($id);if($p!=='')return$p;}
    return '';
}

function v1429_latest_prompt_intent(array $identities,array $profiles=[]): array {
    $usable=[];
    foreach($profiles as $profile){$saved=v1311_digits((string)($profile['whatsapp']??''));if(strlen($saved)<10)continue;foreach($identities as $id){if(v1311_same_phone($saved,(string)$id))$usable[]=(string)$id;}if(!$usable)$usable[]=$saved;}
    if(!$usable)$usable=$identities;
    if(!$usable)return [];
    try{
        $q=db()->query("SELECT tipo,destinatario,meta_data,created_at FROM notification_logs WHERE status='enviado' AND created_at>=DATE_SUB(NOW(),INTERVAL 14 DAY) AND tipo IN ('whatsapp','whatsapp_post_quiz') ORDER BY created_at DESC LIMIT 500");
        foreach($q->fetchAll() as $r){
            $dest=(string)($r['destinatario']??'');if($dest==='')continue;
            $match=false;foreach($usable as $id){if(v1311_same_phone($dest,(string)$id)){$match=true;break;}}
            if(!$match)continue;
            return ['type'=>(string)$r['tipo']==='whatsapp_post_quiz'?'quiz':'scale','created_at'=>(string)($r['created_at']??''),'meta_data'=>(string)($r['meta_data']??'')];
        }
    }catch(Throwable $e){v1311_trace('latest_prompt_intent_error',['message'=>substr($e->getMessage(),0,240)]);}
    return [];
}
"""
if old not in s: raise SystemExit('reply_phone anchor not found')
s=s.replace(old,new,1)

# Latest outbound prompt wins over an older scale notification. If it was a quiz, let quiz router handle 1/2 too.
old="""    $profiles = v1311_find_profiles($msg['identities']);
    $item = v1311_notification_candidate($msg['identities']);
"""
new="""    $profiles = v1311_find_profiles($msg['identities']);
    $latestIntent=v1429_latest_prompt_intent($msg['identities'],$profiles);
    if(($latestIntent['type']??'')==='quiz'){
        v1311_trace('yield_to_latest_quiz_prompt',['text'=>$text,'created_at'=>$latestIntent['created_at']??null,'profile_count'=>count($profiles)]);
        $GLOBALS['ESCALAS_TOP_V1311_ALLOW_QUIZ']=true;
        return false;
    }
    $item = v1311_notification_candidate($msg['identities']);
"""
if old not in s: raise SystemExit('latest intent insertion anchor not found')
s=s.replace(old,new,1)

# Reply fallback: if exact inbound number fails, retry the registered WhatsApp for the same volunteer.
old="""        $res=v1424_send_logged_whatsapp('whatsapp_confirmation_reply', $replyTo, $message, $item['igreja_id'] ?: null, [
            'escala_id'=>$item['escala_id'], 'escala_item_id'=>$item['item_id'], 'voluntario_id'=>$item['voluntario_id'],
            'reply_reason'=>$reason, 'router'=>'v1.3.11'
        ]);
        $ok=is_array($res) ? !empty($res['ok']) : ($res!==false);
"""
new="""        $meta=['escala_id'=>$item['escala_id'], 'escala_item_id'=>$item['item_id'], 'voluntario_id'=>$item['voluntario_id'], 'reply_reason'=>$reason, 'router'=>'v1.4.29'];
        $res=v1424_send_logged_whatsapp('whatsapp_confirmation_reply', $replyTo, $message, $item['igreja_id'] ?: null, $meta);
        $ok=is_array($res) ? !empty($res['ok']) : ($res!==false);
        $saved=(string)($item['whatsapp']??'');
        if(!$ok&&$saved!==''&&$replyTo!==$saved&&v1311_same_phone($replyTo,$saved)){
            $res=v1424_send_logged_whatsapp('whatsapp_confirmation_reply', $saved, $message, $item['igreja_id'] ?: null, $meta+['reply_fallback'=>'profile_whatsapp']);
            $ok=is_array($res)?!empty($res['ok']):($res!==false);
        }
"""
if old not in s: raise SystemExit('reply fallback anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

# 2) Pending router: an old pending-menu session must not hijack a newer scale/quiz notification.
p=api/'pending_router_v1311.php'; s=p.read_text(encoding='utf-8')
old="$session=v1311p_active_session($msg,$profiles); if($session){ if(!v1311p_mark_event($msg))return true; $state=(string)($session['state']??'menu');"
new="$session=v1311p_active_session($msg,$profiles); $latestIntent=function_exists('v1429_latest_prompt_intent')?v1429_latest_prompt_intent($msg['identities']??[],$profiles):[]; if($session&&$latestIntent){$promptTs=strtotime((string)($latestIntent['created_at']??''))?:0;$sessionTs=strtotime((string)($session['updated_at']??''))?:0;if($promptTs>$sessionTs+2){v1311p_trace('session_superseded_by_new_prompt',['old_state'=>(string)($session['state']??''),'intent'=>(string)($latestIntent['type']??''),'prompt_at'=>$latestIntent['created_at']??null]);v1311p_delete_session($session);$session=null;}} if(!$session&&($latestIntent['type']??'')==='scale'&&in_array($text,['1','2'],true)){v1311p_trace('yield_to_direct_scale_reply',['text'=>$text,'prompt_at'=>$latestIntent['created_at']??null]);return false;} if(!$session&&($latestIntent['type']??'')==='quiz'&&preg_match('/^[1-5](?:\\s*(?:-|–|—|:).*)?$/u',$text)){v1311p_trace('yield_to_direct_quiz_reply',['text'=>substr($text,0,80),'prompt_at'=>$latestIntent['created_at']??null]);return false;} if($session){ if(!v1311p_mark_event($msg))return true; $state=(string)($session['state']??'menu');"
if old not in s: raise SystemExit('pending session anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

# 3) Transport: if Evolution says a Brazilian number does not exist, retry the equivalent with/without ninth digit.
p=api/'whatsapp_transport_v1424.php'; s=p.read_text(encoding='utf-8')
anchor="""function v1424_http_json(string $url,array $payload,array $headers): array {
"""
insert="""function v1429_br_phone_variants(string $number): array {
    $d=preg_replace('/\\D+/','',$number)?:'';$out=[];
    if(!str_starts_with($d,'55'))return $out;
    $local=substr($d,2);$alt='';
    if(strlen($local)===11&&isset($local[2])&&$local[2]==='9')$alt=substr($local,0,2).substr($local,3);
    elseif(strlen($local)===10)$alt=substr($local,0,2).'9'.substr($local,2);
    if($alt!=='')$out[]='55'.$alt;
    return array_values(array_unique(array_filter($out,static fn($x)=>$x!==$d)));
}
function v1424_http_json(string $url,array $payload,array $headers): array {
"""
if anchor not in s: raise SystemExit('transport helper anchor not found')
s=s.replace(anchor,insert,1)
old="""    if($existsFalse){
        $first['error_code']='recipient_not_on_whatsapp';
        $first['error']='Número não encontrado/registrado no WhatsApp pela Evolution API: '.$number;
        $first['non_retryable']=true;
    }
    return $first;
"""
new="""    if($existsFalse){
        foreach(v1429_br_phone_variants($number) as $alt){
            $altRes=v1424_http_json($url,['number'=>$alt,'text'=>$text],$headers);$altRes['instance']=$instance;$altRes['number']=$alt;$altRes['payload_mode']='text';$altRes['original_number']=$number;$altRes['number_variant_retry']=true;
            if(!empty($altRes['ok']))return $altRes;
        }
        $first['error_code']='recipient_not_on_whatsapp';
        $first['error']='Número não encontrado/registrado no WhatsApp pela Evolution API: '.$number;
        $first['non_retryable']=true;
    }
    return $first;
"""
if old not in s: raise SystemExit('transport existsFalse anchor not found')
s=s.replace(old,new,1)
s=s.replace("$meta['transport_version']='1.4.25';","$meta['transport_version']='1.4.29';",1)
p.write_text(s,encoding='utf-8')

# Cache bust.
p=root/'sistema.html'; s=p.read_text(encoding='utf-8'); s=re.sub(r'/assets/index-C6Ng0a8i\\.js\\?v=[^\"<]+','/assets/index-C6Ng0a8i.js?v=1.4.29',s); p.write_text(s,encoding='utf-8')
p=root/'sw.js'; s=p.read_text(encoding='utf-8'); s+='\n/* whatsapp-direct-reply-reliability-v1.4.29 */\n'; p.write_text(s,encoding='utf-8')
