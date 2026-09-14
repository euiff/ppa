from pathlib import Path
import re, sys
root=Path(sys.argv[1]); api=root/'api'
p=api/'pending_router_v1311.php'; s=p.read_text(encoding='utf-8')
old="function v1311p_active_session(array $msg, array $profiles): ?array { v1311p_ensure_schema(); try{$rows=db()->query(\"SELECT * FROM whatsapp_pending_sessions WHERE expires_at>=NOW() ORDER BY updated_at DESC LIMIT 100\")->fetchAll();}catch(Throwable$e){return null;} $pids=array_flip(v1311p_profile_ids($profiles)); foreach($rows as $r){ if(!empty($r['voluntario_id']) && $pids && !isset($pids[(string)$r['voluntario_id']])) continue; foreach(($msg['identities']??[]) as $id){if(v1311_same_phone((string)$r['sender'],(string)$id)) return $r;} } return null; }"
new="function v1311p_active_session(array $msg, array $profiles): ?array { v1311p_ensure_schema(); try{$rows=db()->query(\"SELECT * FROM whatsapp_pending_sessions WHERE expires_at>=NOW() ORDER BY updated_at DESC LIMIT 100\")->fetchAll();}catch(Throwable$e){return null;} $pids=array_flip(v1311p_profile_ids($profiles)); if($pids){foreach($rows as $r){$vid=(string)($r['voluntario_id']??'');if($vid!==''&&isset($pids[$vid])){v1311p_trace('session_match_profile',['state'=>(string)($r['state']??''),'volunteer_tail'=>substr($vid,-6)]);return $r;}}} foreach($rows as $r){foreach(($msg['identities']??[]) as $id){if(v1311_same_phone((string)$r['sender'],(string)$id)){v1311p_trace('session_match_phone',['state'=>(string)($r['state']??'')]);return $r;}}} return null; }"
if old not in s: raise SystemExit('active session anchor not found')
s=s.replace(old,new,1)
count=s.count('DATE_ADD(NOW(),INTERVAL 60 MINUTE)')
if count<2: raise SystemExit(f'expected >=2 old session expiry anchors, got {count}')
s=s.replace('DATE_ADD(NOW(),INTERVAL 60 MINUTE)','DATE_ADD(NOW(),INTERVAL 7 DAY)')
s=s.replace("'expires_at'=>date('Y-m-d H:i:s',time()+3600)","'expires_at'=>date('Y-m-d H:i:s',time()+604800)",1)
p.write_text(s,encoding='utf-8')

mig=root/'database/migrations/20260914_1428_pending_session_fix.sql'
mig.write_text("""CREATE TABLE IF NOT EXISTS whatsapp_pending_sessions (
 id VARCHAR(36) NOT NULL PRIMARY KEY,
 sender VARCHAR(32) NOT NULL,
 voluntario_id VARCHAR(36) NULL,
 state VARCHAR(24) NOT NULL DEFAULT 'menu',
 selected_type VARCHAR(24) NULL,
 selected_id VARCHAR(64) NULL,
 options_json LONGTEXT NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 expires_at DATETIME NOT NULL,
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 KEY idx_whatsapp_pending_sender (sender,state,expires_at),
 KEY idx_whatsapp_pending_voluntario (voluntario_id,state,expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
UPDATE whatsapp_pending_sessions
SET expires_at=DATE_ADD(updated_at,INTERVAL 7 DAY)
WHERE updated_at>=DATE_SUB(NOW(),INTERVAL 7 DAY)
  AND expires_at<DATE_ADD(updated_at,INTERVAL 7 DAY);
""",encoding='utf-8')

p=root/'sistema.html'; s=p.read_text(encoding='utf-8'); s=re.sub(r'/assets/index-C6Ng0a8i\.js\?v=[^\"<]+','/assets/index-C6Ng0a8i.js?v=1.4.28',s); p.write_text(s,encoding='utf-8')
p=root/'sw.js'; s=p.read_text(encoding='utf-8'); s+='\n/* pending-session-fix-v1.4.28 */\n'; p.write_text(s,encoding='utf-8')
