<?php
declare(strict_types=1);

function tenant_v1323_ensure_schema(): void {
    static $done=false; if($done)return; $done=true;
    $pdo=db();
    $pdo->exec("CREATE TABLE IF NOT EXISTS saas_church_access (
      igreja_id CHAR(36) NOT NULL PRIMARY KEY,
      join_code CHAR(5) NOT NULL,
      admin_user_id CHAR(36) NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      UNIQUE KEY uq_saas_church_join_code(join_code),
      KEY idx_saas_church_admin_user(admin_user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $pdo->exec("CREATE TABLE IF NOT EXISTS saas_join_rate (
      ip_hash CHAR(64) NOT NULL PRIMARY KEY,
      attempts INT NOT NULL DEFAULT 0,
      window_started_at DATETIME NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
}

function tenant_v1323_generate_code(): string {
    tenant_v1323_ensure_schema();
    for($i=0;$i<120;$i++){
        $code=(string)random_int(10000,99999);
        $st=db()->prepare('SELECT 1 FROM saas_church_access WHERE join_code=? LIMIT 1');
        $st->execute([$code]);
        if(!$st->fetchColumn())return $code;
    }
    throw new RuntimeException('Não foi possível gerar um código de igreja único.');
}

function tenant_v1323_discover_admin(string $igrejaId): ?string {
    try{
        $sql="SELECT p.id FROM profiles p JOIN user_roles ur ON ur.user_id=p.id WHERE p.igreja_id=? AND ur.role='admin' ORDER BY COALESCE(p.created_at,'1970-01-01'),p.id LIMIT 1";
        $st=db()->prepare($sql);$st->execute([$igrejaId]);$id=$st->fetchColumn();
        return $id!==false && $id!==null && $id!=='' ? (string)$id : null;
    }catch(Throwable $e){return null;}
}

function tenant_v1323_access(string $igrejaId,?string $preferredAdmin=null): array {
    tenant_v1323_ensure_schema();
    $st=db()->prepare('SELECT * FROM saas_church_access WHERE igreja_id=? LIMIT 1');
    $st->execute([$igrejaId]);$row=$st->fetch();
    if($row){
        if(empty($row['admin_user_id'])){
            $admin=tenant_v1323_discover_admin($igrejaId) ?: $preferredAdmin;
            if($admin){
                try{db()->prepare('UPDATE saas_church_access SET admin_user_id=?,updated_at=NOW() WHERE igreja_id=? AND admin_user_id IS NULL')->execute([$admin,$igrejaId]);}catch(Throwable $e){}
                $st->execute([$igrejaId]);$row=$st->fetch()?:$row;
            }
        }
        return $row;
    }
    $admin=tenant_v1323_discover_admin($igrejaId) ?: $preferredAdmin;
    for($i=0;$i<40;$i++){
        $code=tenant_v1323_generate_code();
        try{
            db()->prepare('INSERT INTO saas_church_access(igreja_id,join_code,admin_user_id,created_at,updated_at) VALUES(?,?,?,NOW(),NOW())')->execute([$igrejaId,$code,$admin]);
            $st->execute([$igrejaId]);return $st->fetch()?:['igreja_id'=>$igrejaId,'join_code'=>$code,'admin_user_id'=>$admin];
        }catch(Throwable $e){
            $st->execute([$igrejaId]);$existing=$st->fetch();if($existing)return $existing;
        }
    }
    throw new RuntimeException('Não foi possível preparar o acesso da igreja.');
}

function tenant_v1323_by_code(string $code): ?array {
    tenant_v1323_ensure_schema();
    $code=preg_replace('/\D+/','',$code)??'';
    if(strlen($code)!==5)return null;
    $st=db()->prepare('SELECT a.igreja_id,a.join_code,a.admin_user_id,i.nome igreja_nome FROM saas_church_access a JOIN igrejas i ON i.id=a.igreja_id WHERE a.join_code=? LIMIT 1');
    $st->execute([$code]);$row=$st->fetch();return $row?:null;
}

function tenant_v1323_is_billing_admin(string $igrejaId,string $userId): bool {
    if($igrejaId===''||$userId==='')return false;
    $a=tenant_v1323_access($igrejaId,null);
    return !empty($a['admin_user_id']) && hash_equals((string)$a['admin_user_id'],$userId);
}

function tenant_v1323_regenerate_code(string $igrejaId): string {
    tenant_v1323_ensure_schema();
    for($i=0;$i<60;$i++){
        $code=tenant_v1323_generate_code();
        try{
            $st=db()->prepare('UPDATE saas_church_access SET join_code=?,updated_at=NOW() WHERE igreja_id=?');
            $st->execute([$code,$igrejaId]);
            if($st->rowCount()>=0)return $code;
        }catch(Throwable $e){}
    }
    throw new RuntimeException('Não foi possível gerar um novo código agora.');
}

function tenant_v1323_rate_limit(): void {
    tenant_v1323_ensure_schema();
    $ip=(string)($_SERVER['HTTP_CF_CONNECTING_IP']??$_SERVER['REMOTE_ADDR']??'unknown');
    $hash=hash('sha256',$ip);
    $pdo=db();
    $st=$pdo->prepare('SELECT attempts,window_started_at FROM saas_join_rate WHERE ip_hash=? LIMIT 1');$st->execute([$hash]);$row=$st->fetch();
    $now=time();
    if(!$row || strtotime((string)$row['window_started_at']) < $now-600){
        $pdo->prepare('DELETE FROM saas_join_rate WHERE ip_hash=?')->execute([$hash]);
        $pdo->prepare('INSERT INTO saas_join_rate(ip_hash,attempts,window_started_at,updated_at) VALUES(?,1,NOW(),NOW())')->execute([$hash]);
        return;
    }
    $attempts=(int)$row['attempts']+1;
    $pdo->prepare('UPDATE saas_join_rate SET attempts=?,updated_at=NOW() WHERE ip_hash=?')->execute([$attempts,$hash]);
    if($attempts>20){usleep(350000);out(['data'=>null,'error'=>['message'=>'Muitas tentativas. Aguarde alguns minutos e tente novamente.']],429);}
}
