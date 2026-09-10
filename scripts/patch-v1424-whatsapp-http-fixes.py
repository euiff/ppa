from pathlib import Path
import sys, re
root=Path(sys.argv[1])
api=root/'api'

helper=api/'whatsapp_transport_v1424.php'
helper.write_text(r'''<?php
declare(strict_types=1);
/** Escala de Propósito v1.4.24 — transporte compatível e diagnóstico fiel para Evolution API. */
if(!function_exists('v1424_send_logged_whatsapp')){
function v1424_phone(string $phone): string {
    if(function_exists('normalize_phone')) return normalize_phone($phone);
    $d=preg_replace('/\D+/','',$phone)?:'';
    if(strlen($d)>=10 && !str_starts_with($d,'55'))$d='55'.$d;
    return $d;
}
function v1424_http_json(string $url,array $payload,array $headers): array {
    if(function_exists('http_json')) return http_json($url,'POST',$payload,$headers);
    $ch=curl_init($url);curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>25,CURLOPT_CONNECTTIMEOUT=>10,CURLOPT_POST=>true,CURLOPT_HTTPHEADER=>$headers,CURLOPT_POSTFIELDS=>json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)]);
    $body=curl_exec($ch);$err=curl_error($ch);$status=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);curl_close($ch);$json=json_decode((string)$body,true);
    return ['ok'=>$status>=200&&$status<300,'status'=>$status,'body'=>$json??$body,'raw'=>(string)$body,'error'=>$err?:null];
}
function v1424_cfg(string $key,?string $igrejaId=null): string {
    try{if(function_exists('config_value'))return trim((string)config_value($key,$igrejaId,''));}catch(Throwable $e){}
    try{if(function_exists('cfg_map')){$m=cfg_map($igrejaId);return trim((string)($m[$key]??''));}}catch(Throwable $e){}
    return '';
}
function v1424_evolution_send(string $number,string $text,?string $igrejaId=null): array {
    $text=trim($text);
    if($text==='')return ['ok'=>false,'status'=>0,'error'=>'Mensagem vazia: o campo text não pode ser enviado vazio','payload_mode'=>'text'];
    $base=rtrim(v1424_cfg('evolution_url',$igrejaId),'/');$key=v1424_cfg('evolution_api_key',$igrejaId);$instance=v1424_cfg('evolution_instance',$igrejaId);
    if($base===''||$key===''||$instance==='')return ['ok'=>false,'status'=>0,'error'=>'Evolution API não configurada','payload_mode'=>'text'];
    $number=v1424_phone($number);if(strlen($number)<10)return ['ok'=>false,'status'=>0,'error'=>'Número de WhatsApp inválido','payload_mode'=>'text','number'=>$number];
    $url=$base.'/message/sendText/'.rawurlencode($instance);$headers=['Content-Type: application/json','apikey: '.$key];
    $payload=['number'=>$number,'text'=>$text];
    $first=v1424_http_json($url,$payload,$headers);$first['instance']=$instance;$first['number']=$number;$first['payload_mode']='text';
    if(!empty($first['ok']))return $first;
    $status=(int)($first['status']??0);
    if($status===0||$status===408||$status===425||$status===429||$status>=500){
        usleep(350000);
        $retry=v1424_http_json($url,$payload,$headers);$retry['instance']=$instance;$retry['number']=$number;$retry['payload_mode']='text';$retry['first_attempt_status']=$status;
        if(!empty($retry['ok']))return $retry;
        $first=$retry;$status=(int)($retry['status']??0);
    }
    $raw=mb_strtolower(json_encode($first['body']??'',JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES).' '.(string)($first['raw']??'').' '.(string)($first['error']??''));
    $asksNested=(str_contains($raw,'textmessage') && (str_contains($raw,'required')||str_contains($raw,'requires')||str_contains($raw,'missing')) && !str_contains($raw,'cannot read properties of undefined'));
    if(in_array($status,[400,404,422],true)&&$asksNested){
        $nested=v1424_http_json($url,['number'=>$number,'textMessage'=>['text'=>$text]],$headers);$nested['instance']=$instance;$nested['number']=$number;$nested['payload_mode']='textMessage';$nested['first_attempt_status']=$status;
        return $nested;
    }
    return $first;
}
function v1424_send_logged_whatsapp(string $tipo,string $phone,string $message,?string $igrejaId=null,array $meta=[]): array {
    $res=v1424_evolution_send($phone,$message,$igrejaId);
    $meta['transport_version']='1.4.24';$meta['payload_mode']=$res['payload_mode']??'text';
    if(isset($res['first_attempt_status']))$meta['first_attempt_status']=$res['first_attempt_status'];
    try{
        if(!function_exists('log_whatsapp')&&is_file(__DIR__.'/whatsapp_lib.php'))require_once __DIR__.'/whatsapp_lib.php';
        if(function_exists('log_whatsapp'))log_whatsapp($tipo,v1424_phone($phone),$message,$res,$igrejaId,$meta);
    }catch(Throwable $e){}
    return $res;
}
}
''',encoding='utf-8')

active=['automation_v130.php','quiz_router_v131.php','confirmation_router_v1311.php','pending_router_v1311.php','sos_lib_v140.php','sos-router-v140.php','scale_response_notify_v1417.php','whatsapp_scale_message_v1421.php']
for name in active:
    p=api/name
    if not p.exists(): continue
    s=p.read_text(encoding='utf-8')
    if 'whatsapp_transport_v1424.php' not in s:
        marker='declare(strict_types=1);'
        if marker in s:s=s.replace(marker,marker+"\nrequire_once __DIR__.'/whatsapp_transport_v1424.php';",1)
        else:s=s.replace('<?php','<?php\nrequire_once __DIR__.\'/whatsapp_transport_v1424.php\';',1)
    s=s.replace('send_logged_whatsapp(', 'v1424_send_logged_whatsapp(').replace('v1424_v1424_send_logged_whatsapp(', 'v1424_send_logged_whatsapp(')
    p.write_text(s,encoding='utf-8')

p=api/'church-code.php';s=p.read_text(encoding='utf-8')
old="""    if($role==='master'){
        $req=input_json();
        $igreja=(string)($req['igreja_id']??$_GET['igreja_id']??$igreja);
    }
    if($igreja==='')out(['data'=>null,'error'=>['message'=>'Igreja não identificada.']],400);
"""
new="""    if($role==='master'){
        $req=$_SERVER['REQUEST_METHOD']==='POST'?input_json():[];
        $igreja=(string)($req['igreja_id']??$_GET['igreja_id']??$igreja);
        if($igreja==='')out(['data'=>null,'error'=>null,'meta'=>['reason'=>'master_without_church']],200);
    }
    if($igreja==='')out(['data'=>null,'error'=>['message'=>'Igreja não identificada.']],400);
"""
if old not in s: raise SystemExit('church-code master anchor not found')
s=s.replace(old,new,1);p.write_text(s,encoding='utf-8')

p=root/'codigo-igreja.html';s=p.read_text(encoding='utf-8')
old="data=j.data;church.textContent=data.igreja_nome;code.textContent=data.codigo;link.textContent=data.invite_link"
new="data=j.data;if(!data){church.textContent='O MASTER não pertence a uma igreja específica.';code.textContent='-----';link.textContent='Selecione uma igreja pelo painel MASTER quando precisar consultar dados dela.';return}church.textContent=data.igreja_nome;code.textContent=data.codigo;link.textContent=data.invite_link"
if old not in s: raise SystemExit('codigo-igreja null anchor not found')
s=s.replace(old,new,1);p.write_text(s,encoding='utf-8')

mig=root/'database/migrations/20260909_1424_whatsapp_transport_recovery.sql'
mig.write_text(r'''UPDATE whatsapp_send_jobs j
SET j.status='pending',j.attempts=0,j.scheduled_at=NOW(),j.started_at=NULL,j.finished_at=NULL,j.error=NULL,j.updated_at=NOW()
WHERE j.job_type='escala_notification'
  AND j.status='failed'
  AND j.updated_at>=DATE_SUB(NOW(),INTERVAL 24 HOUR)
  AND NOT EXISTS (
    SELECT 1 FROM notification_logs n
    WHERE n.tipo='whatsapp' AND n.status='enviado'
      AND n.meta_data LIKE CONCAT('%\"escala_item_id\":\"',j.escala_item_id,'\"%')
  );
''',encoding='utf-8')

p=root/'sistema.html';s=p.read_text(encoding='utf-8');s=re.sub(r'/assets/index-C6Ng0a8i\.js\?v=[^"<]+','/assets/index-C6Ng0a8i.js?v=1.4.24',s);p.write_text(s,encoding='utf-8')
p=root/'sw.js';s=p.read_text(encoding='utf-8');s+='\n/* whatsapp-transport-http-fixes-v1.4.24 */\n';p.write_text(s,encoding='utf-8')
