from pathlib import Path
import sys
root=Path(sys.argv[1])
api=root/'api'

# Transport retries for transient Evolution disconnects.
p=api/'whatsapp_transport_v1424.php'; s=p.read_text(encoding='utf-8')
old="""    if($status===0||$status===408||$status===425||$status===429||$status>=500){
        usleep(350000);
        $retry=v1424_http_json($url,$payload,$headers);$retry['instance']=$instance;$retry['number']=$number;$retry['payload_mode']='text';$retry['first_attempt_status']=$status;
        if(!empty($retry['ok']))return $retry;
        $first=$retry;$status=(int)($retry['status']??0);
    }
"""
new="""    if($status===0||$status===408||$status===425||$status===429||$status>=500){
        $firstStatus=$status;$retryNo=0;
        foreach([350000,1200000,2500000] as $delay){
            usleep($delay);$retryNo++;
            $retry=v1424_http_json($url,$payload,$headers);$retry['instance']=$instance;$retry['number']=$number;$retry['payload_mode']='text';$retry['first_attempt_status']=$firstStatus;$retry['retry_count']=$retryNo;
            if(!empty($retry['ok']))return $retry;
            $first=$retry;$status=(int)($retry['status']??0);
            if(!($status===0||$status===408||$status===425||$status===429||$status>=500))break;
        }
    }
"""
if old not in s: raise SystemExit('transport retry anchor not found')
s=s.replace(old,new,1)
old="""    $body=$first['body']??null;$existsFalse=false;
"""
new="""    $transientRaw=json_encode($first['body']??'',JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES).' '.(string)($first['raw']??'').' '.(string)($first['error']??'');
    $transientLow=function_exists('mb_strtolower')?mb_strtolower($transientRaw,'UTF-8'):strtolower($transientRaw);
    if(str_contains($transientLow,'connection closed')||str_contains($transientLow,'connection lost')||str_contains($transientLow,'socket hang up')||str_contains($transientLow,'econnreset')||str_contains($transientLow,'disconnected')){
        $first['error_code']='evolution_connection_closed';$first['error']='Conexão da Evolution/WhatsApp fechada temporariamente';$first['transient']=true;$first['non_retryable']=false;
    }elseif($status===0||$status===408||$status===425||$status===429||$status>=500){
        $first['error_code']=$first['error_code']??'evolution_transient_failure';$first['transient']=true;$first['non_retryable']=false;
    }
    $body=$first['body']??null;$existsFalse=false;
"""
if old not in s: raise SystemExit('transport transient anchor not found')
s=s.replace(old,new,1)
s=s.replace("$meta['transport_version']='1.4.25';", "$meta['transport_version']='1.4.33';",1)
s=s.replace("if(isset($res['non_retryable']))$meta['non_retryable']=(bool)$res['non_retryable'];", "if(isset($res['non_retryable']))$meta['non_retryable']=(bool)$res['non_retryable'];if(isset($res['transient']))$meta['transient']=(bool)$res['transient'];if(isset($res['retry_count']))$meta['retry_count']=(int)$res['retry_count'];",1)
p.write_text(s,encoding='utf-8')

# CRON: keep transient scale jobs alive and recover direct reply messages after Evolution reconnects.
p=api/'automation_v130.php'; s=p.read_text(encoding='utf-8')
old="""function v130_retry_failed_jobs():int{$max=v130_cfg('whatsapp_job_max_attempts',null,3,1,10);$before=date('Y-m-d H:i:s',time()-v130_cfg('whatsapp_job_retry_seconds',null,300,60,86400));$q=db()->prepare("SELECT id FROM whatsapp_send_jobs WHERE status='failed' AND attempts<? AND updated_at<=? AND (result IS NULL OR result NOT LIKE '%\\\"non_retryable\\\":true%') ORDER BY updated_at LIMIT 20");$q->execute([$max,$before]);$r=$q->fetchAll();foreach($r as$x)db()->prepare("UPDATE whatsapp_send_jobs SET status='pending',scheduled_at=NOW(),started_at=NULL,finished_at=NULL,error=NULL,updated_at=NOW() WHERE id=?")->execute([$x['id']]);return count($r);}
"""
new="""function v1433_transient_whatsapp_row(array $r):bool{$raw=strtolower((string)($r['error']??'').' '.(string)($r['result']??''));if(str_contains($raw,'recipient_not_on_whatsapp')||str_contains($raw,'\\\"non_retryable\\\":true'))return false;if(str_contains($raw,'connection closed')||str_contains($raw,'connection lost')||str_contains($raw,'socket hang up')||str_contains($raw,'econnreset')||str_contains($raw,'disconnected')||str_contains($raw,'evolution_connection_closed')||str_contains($raw,'evolution_transient_failure'))return true;$j=json_decode((string)($r['result']??''),true);$st=is_array($j)?(int)($j['status']??0):0;return $st===0||$st===408||$st===425||$st===429||$st>=500;}
function v130_retry_failed_jobs():int{$normalMax=v130_cfg('whatsapp_job_max_attempts',null,3,1,10);$transientMax=v130_cfg('whatsapp_transient_max_attempts',null,30,5,100);$retryBase=v130_cfg('whatsapp_job_retry_seconds',null,300,60,86400);$q=db()->query("SELECT id,attempts,error,result,updated_at FROM whatsapp_send_jobs WHERE status='failed' AND (result IS NULL OR result NOT LIKE '%\\\"non_retryable\\\":true%') ORDER BY updated_at LIMIT 60");$rows=$q->fetchAll();$n=0;$now=time();foreach($rows as$r){$transient=v1433_transient_whatsapp_row($r);$attempts=(int)($r['attempts']??0);$limit=$transient?$transientMax:$normalMax;if($attempts>=$limit)continue;$delay=$transient?min(300,max(60,30*max(1,$attempts))):$retryBase;$updated=strtotime((string)($r['updated_at']??''))?:0;if($updated>0&&$now-$updated<$delay)continue;$u=db()->prepare("UPDATE whatsapp_send_jobs SET status='pending',scheduled_at=NOW(),started_at=NULL,finished_at=NULL,error=NULL,updated_at=NOW() WHERE id=? AND status='failed'");$u->execute([$r['id']]);$n+=$u->rowCount();}return$n;}
function v1433_retry_failed_interactive_notifications():int{$types=['whatsapp_confirmation_reply','whatsapp_quiz_reply','whatsapp_pending_menu','whatsapp_confirmation_unresolved','whatsapp_scale_response_leader','whatsapp_scale_refusal_reason_leader'];$ph=implode(',',array_fill(0,count($types),'?'));$sql="SELECT id,tipo,destinatario,mensagem,igreja_id,meta_data,response_body,response_status,erro,created_at FROM notification_logs WHERE status IN ('erro','failed') AND created_at>=DATE_SUB(NOW(),INTERVAL 24 HOUR) AND tipo IN ($ph) ORDER BY created_at ASC LIMIT 40";$q=db()->prepare($sql);$q->execute($types);$recovered=0;foreach($q->fetchAll() as$r){$status=(int)($r['response_status']??0);$raw=strtolower((string)($r['response_body']??'').' '.(string)($r['erro']??''));$transient=$status===0||$status===408||$status===425||$status===429||$status>=500||str_contains($raw,'connection closed')||str_contains($raw,'connection lost')||str_contains($raw,'socket hang up')||str_contains($raw,'econnreset')||str_contains($raw,'disconnected');if(!$transient)continue;$meta=json_decode((string)($r['meta_data']??''),true);if(!is_array($meta))$meta=[];$tries=(int)($meta['recovery_attempts_v1433']??0);if($tries>=20)continue;$last=(int)($meta['recovery_last_ts_v1433']??0);$delay=min(300,max(60,30*max(1,$tries)));if($last>0&&time()-$last<$delay)continue;$res=v1424_evolution_send((string)$r['destinatario'],(string)$r['mensagem'],($r['igreja_id']??null)?:null);$meta['recovery_attempts_v1433']=$tries+1;$meta['recovery_last_ts_v1433']=time();$meta['recovery_last_status_v1433']=(int)($res['status']??0);if(!empty($res['ok'])){$meta['recovered_v1433']=true;$u=db()->prepare("UPDATE notification_logs SET status='recuperado',erro=NULL,response_status=?,response_body=?,meta_data=? WHERE id=?");$u->execute([(int)($res['status']??200),json_encode($res['body']??$res,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),json_encode($meta,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),$r['id']]);$recovered++;}else{$u=db()->prepare("UPDATE notification_logs SET response_status=?,response_body=?,erro=?,meta_data=? WHERE id=?");$u->execute([(int)($res['status']??0),json_encode($res['body']??$res,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),(string)($res['error']??'Falha temporária no WhatsApp'),json_encode($meta,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),$r['id']]);}}return$recovered;}
"""
if old not in s: raise SystemExit('retry jobs anchor not found')
s=s.replace(old,new,1)
old="""if($job&&$job['status']==='failed'){$jr=json_decode((string)($job['result']??''),true);if(is_array($jr)&&!empty($jr['non_retryable'])&&($jr['error_code']??'')==='recipient_not_on_whatsapp'){$oldNum=preg_replace('/\D+/','',(string)($jr['number']??''))?:'';$newNum=function_exists('v1424_phone')?v1424_phone((string)($r['whatsapp']??'')):(preg_replace('/\D+/','',(string)($r['whatsapp']??''))?:'');if($oldNum!==''&&$newNum===$oldNum)continue;}elseif((int)$job['attempts']<v130_cfg('whatsapp_job_max_attempts',$r['igreja_id'],3,1,10))continue;}"""
new="""if($job&&$job['status']==='failed'){$jr=json_decode((string)($job['result']??''),true);if(is_array($jr)&&!empty($jr['non_retryable'])&&($jr['error_code']??'')==='recipient_not_on_whatsapp'){$oldNum=preg_replace('/\D+/','',(string)($jr['number']??''))?:'';$newNum=function_exists('v1424_phone')?v1424_phone((string)($r['whatsapp']??'')):(preg_replace('/\D+/','',(string)($r['whatsapp']??''))?:'');if($oldNum!==''&&$newNum===$oldNum)continue;}elseif(v1433_transient_whatsapp_row($job)&&(int)$job['attempts']<v130_cfg('whatsapp_transient_max_attempts',$r['igreja_id'],30,5,100))continue;elseif((int)$job['attempts']<v130_cfg('whatsapp_job_max_attempts',$r['igreja_id'],3,1,10))continue;}"""
if old not in s: raise SystemExit('enqueue failed-job anchor not found')
s=s.replace(old,new,1)
old="$s['failed_jobs_requeued']=v130_retry_failed_jobs();$x=v130_enqueue_missing();"
new="$s['failed_jobs_requeued']=v130_retry_failed_jobs();$s['interactive_replies_recovered']=v1433_retry_failed_interactive_notifications();$x=v130_enqueue_missing();"
if old not in s: raise SystemExit('run_all retry anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
