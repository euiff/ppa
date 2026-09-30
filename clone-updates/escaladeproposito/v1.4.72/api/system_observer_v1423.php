<?php
declare(strict_types=1);
/** Escala de Propósito v1.4.23 — observabilidade central (sem segredos). */
if(!function_exists('syslog_v1423_ensure_schema')){
function syslog_v1423_ensure_schema(): void {
    static $done=false;if($done)return;$done=true;
    try{db()->exec("CREATE TABLE IF NOT EXISTS system_logs (
      id VARCHAR(36) NOT NULL PRIMARY KEY,
      log_type VARCHAR(24) NOT NULL DEFAULT 'info',
      source VARCHAR(80) NOT NULL DEFAULT 'system',
      action VARCHAR(160) NULL,
      message TEXT NOT NULL,
      details LONGTEXT NULL,
      severity VARCHAR(16) NOT NULL DEFAULT 'info',
      status VARCHAR(20) NOT NULL DEFAULT 'done',
      user_id VARCHAR(36) NULL,
      igreja_id VARCHAR(36) NULL,
      url VARCHAR(1000) NULL,
      http_method VARCHAR(12) NULL,
      http_status INT NULL,
      fingerprint VARCHAR(64) NULL,
      occurrences INT NOT NULL DEFAULT 1,
      first_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      last_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      resolved_at DATETIME NULL,
      resolved_by VARCHAR(36) NULL,
      resolution_note VARCHAR(1000) NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      KEY idx_system_logs_created(created_at),
      KEY idx_system_logs_type(log_type,status,created_at),
      KEY idx_system_logs_church(igreja_id,created_at),
      KEY idx_system_logs_fingerprint(fingerprint,last_seen_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");}catch(Throwable $e){}
}
function syslog_v1423_uuid(): string {if(function_exists('uuid4'))return uuid4();$d=random_bytes(16);$d[6]=chr((ord($d[6])&0x0f)|0x40);$d[8]=chr((ord($d[8])&0x3f)|0x80);return vsprintf('%s%s-%s-%s-%s-%s%s%s',str_split(bin2hex($d),4));}
function syslog_v1423_sensitive(string $k): bool {$k=strtolower($k);foreach(['password','senha','token','secret','segredo','api_key','apikey','authorization','cookie','cpf','card','cartao','access_token','refresh_token','webhook_token'] as $x)if(str_contains($k,$x))return true;return false;}
function syslog_v1423_sanitize($v,$depth=0){if($depth>5)return '[limite]';if(is_array($v)){$o=[];foreach($v as$k=>$x){$ks=(string)$k;$o[$ks]=syslog_v1423_sensitive($ks)?'[PROTEGIDO]':syslog_v1423_sanitize($x,$depth+1);}return$o;}if(is_object($v))return syslog_v1423_sanitize((array)$v,$depth+1);if(is_string($v)){if(strlen($v)>4000)$v=substr($v,0,4000).'…';return$v;}return$v;}
function syslog_v1423_identity(): array {$uid=null;$ig=null;try{if(function_exists('user_context')){$c=user_context();if(is_array($c)){$uid=(string)($c['user_id']??$c['id']??'')?:null;$ig=(string)($c['igreja_id']??'')?:null;}}}catch(Throwable $e){}return[$uid,$ig];}
function syslog_v1423_write(array $x): void {
    static $busy=false;if($busy)return;$busy=true;
    try{syslog_v1423_ensure_schema();[$du,$di]=syslog_v1423_identity();$type=(string)($x['log_type']??'info');$sev=(string)($x['severity']??($type==='error'?'error':'info'));$status=(string)($x['status']??(in_array($type,['error','warning'],true)?'open':'done'));$msg=trim((string)($x['message']??''));if($msg==='')$msg='Evento do sistema';$details=syslog_v1423_sanitize($x['details']??[]);$detailsJson=$details===[]||$details===null?null:json_encode($details,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);$url=(string)($x['url']??($_SERVER['REQUEST_URI']??''));$method=(string)($x['http_method']??($_SERVER['REQUEST_METHOD']??''));$http=isset($x['http_status'])?(int)$x['http_status']:null;$user=(string)($x['user_id']??$du??'')?:null;$ig=(string)($x['igreja_id']??$di??'')?:null;$action=(string)($x['action']??'')?:null;$source=(string)($x['source']??'system');$basis=implode('|',[$type,$source,$action?:'',substr($msg,0,500),$url,$method,(string)$http,(string)$user]);$fp=hash('sha256',$basis);
        $q=db()->prepare("SELECT id FROM system_logs WHERE fingerprint=? AND status=? AND last_seen_at>=DATE_SUB(NOW(),INTERVAL 3 MINUTE) ORDER BY last_seen_at DESC LIMIT 1");$q->execute([$fp,$status]);$id=$q->fetchColumn();
        if($id){db()->prepare("UPDATE system_logs SET occurrences=occurrences+1,last_seen_at=NOW(),updated_at=NOW(),details=COALESCE(?,details),http_status=COALESCE(?,http_status) WHERE id=?")->execute([$detailsJson,$http,$id]);}
        else{db()->prepare("INSERT INTO system_logs(id,log_type,source,action,message,details,severity,status,user_id,igreja_id,url,http_method,http_status,fingerprint,occurrences,first_seen_at,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,NOW(),NOW(),NOW(),NOW())")->execute([syslog_v1423_uuid(),$type,$source,$action,$msg,$detailsJson,$sev,$status,$user,$ig,$url?:null,$method?:null,$http,$fp]);}
    }catch(Throwable $e){}finally{$busy=false;}
}
function system_observer_v1423_register(): void {
    static $registered=false;if($registered)return;$registered=true;syslog_v1423_ensure_schema();
    set_error_handler(function($no,$str,$file,$line){if(!(error_reporting()&$no))return false;$map=[E_WARNING=>'warning',E_USER_WARNING=>'warning',E_RECOVERABLE_ERROR=>'error',E_USER_ERROR=>'error'];if(isset($map[$no]))syslog_v1423_write(['log_type'=>$map[$no]==='error'?'error':'warning','source'=>'php','action'=>'php_error','message'=>(string)$str,'details'=>['errno'=>$no,'file'=>basename((string)$file),'line'=>(int)$line],'severity'=>$map[$no],'status'=>'open']);return false;});
    register_shutdown_function(function(){static $done=false;if($done)return;$done=true;$e=error_get_last();if($e&&in_array((int)$e['type'],[E_ERROR,E_PARSE,E_CORE_ERROR,E_COMPILE_ERROR,E_USER_ERROR],true))syslog_v1423_write(['log_type'=>'error','source'=>'php','action'=>'fatal_error','message'=>(string)$e['message'],'details'=>['file'=>basename((string)$e['file']),'line'=>(int)$e['line']],'severity'=>'critical','status'=>'open']);$code=http_response_code();if($code>=400){syslog_v1423_write(['log_type'=>'error','source'=>'http','action'=>'http_error','message'=>'Requisição retornou HTTP '.$code,'details'=>['uri'=>$_SERVER['REQUEST_URI']??''],'severity'=>$code>=500?'error':'warning','status'=>'open','http_status'=>$code]);}});
}
}
