<?php
declare(strict_types=1);

function billing_col(string $table,string $column): bool {
    try{
        $q=db()->prepare("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=? AND column_name=?");
        $q->execute([$table,$column]);
        return (int)$q->fetchColumn()>0;
    }catch(Throwable $e){ return false; }
}
function billing_col_info(string $table,string $column): ?array {
    try{
        $q=db()->prepare("SELECT DATA_TYPE,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA
                          FROM information_schema.columns
                          WHERE table_schema=DATABASE() AND table_name=? AND column_name=? LIMIT 1");
        $q->execute([$table,$column]);
        $r=$q->fetch(PDO::FETCH_ASSOC);
        return $r?:null;
    }catch(Throwable $e){ return null; }
}
function billing_add_col(string $table,string $column,string $definition): void {
    if(billing_col($table,$column))return;
    db()->exec("ALTER TABLE `$table` ADD COLUMN `$column` $definition");
}
function billing_new_id(string $table,?string $preferred=null): mixed {
    $info=billing_col_info($table,'id');
    if(!$info)return null;
    $extra=strtolower((string)($info['EXTRA']??''));
    if(str_contains($extra,'auto_increment'))return null;
    $type=strtolower((string)($info['DATA_TYPE']??''));
    if(in_array($type,['tinyint','smallint','mediumint','int','integer','bigint','decimal','numeric'],true)){
        $q=db()->query("SELECT COALESCE(MAX(`id`),0)+1 FROM `$table`");
        return (int)$q->fetchColumn();
    }
    return $preferred!==null&&$preferred!==''?$preferred:uuid4();
}
function billing_insert_subscription(string $igrejaId,string $start,string $end): void {
    $id=billing_new_id('saas_subscriptions');
    if(billing_col('saas_subscriptions','id')&&$id!==null){
        db()->prepare("INSERT INTO saas_subscriptions(id,igreja_id,status,trial_started_at,trial_ends_at,created_at,updated_at)
                       VALUES(?,?,'trial',?,?,NOW(),NOW())")->execute([$id,$igrejaId,$start,$end]);
    }else{
        db()->prepare("INSERT INTO saas_subscriptions(igreja_id,status,trial_started_at,trial_ends_at,created_at,updated_at)
                       VALUES(?,'trial',?,?,NOW(),NOW())")->execute([$igrejaId,$start,$end]);
    }
}
function billing_insert_plan(array $row): mixed {
    $preferred=isset($row['id'])?(string)$row['id']:null;
    $legacy=billing_new_id('saas_plans',$preferred);
    $id=$legacy!==null?$legacy:($row['id']??null);
    if($id===null||$id==='')$id='plan-'.substr(bin2hex(random_bytes(8)),0,16);
    db()->prepare("INSERT INTO saas_plans(id,nome,descricao,preco,duracao_dias,ativo,destaque,ordem,created_at,updated_at)
      VALUES(?,?,?,?,?,?,?,?,NOW(),NOW())
      ON DUPLICATE KEY UPDATE nome=VALUES(nome),descricao=VALUES(descricao),preco=VALUES(preco),
      duracao_dias=VALUES(duracao_dias),ativo=VALUES(ativo),destaque=VALUES(destaque),ordem=VALUES(ordem),updated_at=NOW()")
      ->execute([$id,$row['nome'],$row['descricao']??null,$row['preco']??0,$row['duracao_dias']??30,
                 !empty($row['ativo'])?1:0,!empty($row['destaque'])?1:0,(int)($row['ordem']??0)]);
    return $id;
}
function billing_insert_order(array $row): mixed {
    $preferred=isset($row['id'])?(string)$row['id']:null;
    $legacy=billing_new_id('saas_orders',$preferred);
    $id=$legacy!==null?$legacy:($row['id']??null);
    if($id===null||$id==='')$id=uuid4();
    db()->prepare("INSERT INTO saas_orders(id,igreja_id,plan_id,amount,original_amount,discount_amount,promotion_code,period_days,status,
      external_reference,preference_id,payment_id,init_point,raw_status,manual_note,created_at,paid_at,updated_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NOW())")
      ->execute([$id,$row['igreja_id'],$row['plan_id'],$row['amount']??0,$row['original_amount']??null,
        $row['discount_amount']??0,$row['promotion_code']??null,$row['period_days']??30,$row['status']??'pending',
        $row['external_reference'],$row['preference_id']??null,$row['payment_id']??null,$row['init_point']??null,
        $row['raw_status']??null,$row['manual_note']??null,$row['created_at']??date('Y-m-d H:i:s'),$row['paid_at']??null]);
    return $id;
}

function billing_ensure_schema(): void {
    $pdo=db();

    $pdo->exec("CREATE TABLE IF NOT EXISTS saas_plans (
      id VARCHAR(40) PRIMARY KEY,
      nome VARCHAR(120) NOT NULL,
      descricao VARCHAR(255) NULL,
      preco DECIMAL(10,2) NOT NULL DEFAULT 0,
      duracao_dias INT NOT NULL DEFAULT 30,
      ativo TINYINT(1) NOT NULL DEFAULT 1,
      destaque TINYINT(1) NOT NULL DEFAULT 0,
      ordem INT NOT NULL DEFAULT 0,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");

    $pdo->exec("CREATE TABLE IF NOT EXISTS saas_subscriptions (
      igreja_id VARCHAR(36) PRIMARY KEY,
      plan_id VARCHAR(40) NULL,
      status VARCHAR(30) NOT NULL DEFAULT 'trial',
      trial_started_at DATETIME NULL,
      trial_ends_at DATETIME NULL,
      current_period_start DATETIME NULL,
      current_period_end DATETIME NULL,
      last_payment_id VARCHAR(120) NULL,
      last_payment_status VARCHAR(40) NULL,
      manual_note VARCHAR(255) NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");

    $pdo->exec("CREATE TABLE IF NOT EXISTS saas_orders (
      id VARCHAR(36) PRIMARY KEY,
      igreja_id VARCHAR(36) NOT NULL,
      plan_id VARCHAR(40) NOT NULL,
      amount DECIMAL(10,2) NOT NULL DEFAULT 0,
      original_amount DECIMAL(10,2) NULL,
      discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
      promotion_code VARCHAR(60) NULL,
      period_days INT NOT NULL DEFAULT 30,
      status VARCHAR(30) NOT NULL DEFAULT 'pending',
      external_reference VARCHAR(120) NOT NULL,
      preference_id VARCHAR(160) NULL,
      payment_id VARCHAR(120) NULL,
      init_point TEXT NULL,
      raw_status VARCHAR(60) NULL,
      manual_note VARCHAR(255) NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      paid_at DATETIME NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");

    $all=[
      'saas_plans'=>[
        'nome'=>"VARCHAR(120) NOT NULL DEFAULT ''",'descricao'=>"VARCHAR(255) NULL",'preco'=>"DECIMAL(10,2) NOT NULL DEFAULT 0",
        'duracao_dias'=>"INT NOT NULL DEFAULT 30",'ativo'=>"TINYINT(1) NOT NULL DEFAULT 1",'destaque'=>"TINYINT(1) NOT NULL DEFAULT 0",
        'ordem'=>"INT NOT NULL DEFAULT 0",'created_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
        'updated_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
      ],
      'saas_subscriptions'=>[
        'igreja_id'=>"VARCHAR(36) NULL",'plan_id'=>"VARCHAR(40) NULL",'status'=>"VARCHAR(30) NOT NULL DEFAULT 'trial'",
        'trial_started_at'=>"DATETIME NULL",'trial_ends_at'=>"DATETIME NULL",'current_period_start'=>"DATETIME NULL",
        'current_period_end'=>"DATETIME NULL",'last_payment_id'=>"VARCHAR(120) NULL",'last_payment_status'=>"VARCHAR(40) NULL",
        'manual_note'=>"VARCHAR(255) NULL",'created_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
        'updated_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
      ],
      'saas_orders'=>[
        'igreja_id'=>"VARCHAR(36) NULL",'plan_id'=>"VARCHAR(40) NULL",'amount'=>"DECIMAL(10,2) NOT NULL DEFAULT 0",
        'original_amount'=>"DECIMAL(10,2) NULL",'discount_amount'=>"DECIMAL(10,2) NOT NULL DEFAULT 0",'promotion_code'=>"VARCHAR(60) NULL",
        'period_days'=>"INT NOT NULL DEFAULT 30",'status'=>"VARCHAR(30) NOT NULL DEFAULT 'pending'",
        'external_reference'=>"VARCHAR(120) NULL",'preference_id'=>"VARCHAR(160) NULL",'payment_id'=>"VARCHAR(120) NULL",
        'init_point'=>"TEXT NULL",'raw_status'=>"VARCHAR(60) NULL",'manual_note'=>"VARCHAR(255) NULL",
        'created_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP",'paid_at'=>"DATETIME NULL",
        'updated_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
      ]
    ];
    foreach($all as$t=>$cols)foreach($cols as$c=>$def)try{billing_add_col($t,$c,$def);}catch(Throwable $e){}

    $defaults=[
      ['mensal','Mensal','Acesso completo por 30 dias',39.90,30,1,0,10],
      ['semestral','Semestral','6 meses de acesso com economia',199.90,180,1,1,20],
      ['anual','Anual','12 meses de acesso pelo melhor custo',349.90,365,1,0,30],
    ];
    foreach($defaults as$d){
        $q=$pdo->prepare("SELECT id FROM saas_plans WHERE nome=? LIMIT 1");$q->execute([$d[1]]);
        if(!$q->fetchColumn())billing_insert_plan([
          'id'=>$d[0],'nome'=>$d[1],'descricao'=>$d[2],'preco'=>$d[3],'duracao_dias'=>$d[4],
          'ativo'=>$d[5],'destaque'=>$d[6],'ordem'=>$d[7]
        ]);
    }
}

function billing_cfg(string $key,?string $default=null): ?string {
    try{
        $q=db()->prepare("SELECT valor FROM api_config WHERE chave=? AND igreja_id IS NULL ORDER BY updated_at DESC LIMIT 1");
        $q->execute([$key]);$v=$q->fetchColumn();return $v===false?$default:(string)$v;
    }catch(Throwable $e){return $default;}
}
function billing_set_cfg(string $key,string $value): void {
    $pdo=db();
    $pdo->prepare("DELETE FROM api_config WHERE chave=? AND igreja_id IS NULL")->execute([$key]);
    $pdo->prepare("INSERT INTO api_config(id,chave,igreja_id,updated_at,valor) VALUES(?,?,NULL,NOW(),?)")
        ->execute([uuid4(),$key,$value]);
}
function billing_trial_days(): int { return max(1,min(90,(int)(billing_cfg('saas_trial_days','10')??'10'))); }
function billing_app_url(): string {
    global $config;
    $u=rtrim((string)($config['app_url']??''),'/');
    if($u!=='')return $u;
    $https=(!empty($_SERVER['HTTPS'])&&strtolower((string)$_SERVER['HTTPS'])!=='off')?'https':'http';
    return $https.'://'.($_SERVER['HTTP_HOST']??'localhost');
}
function billing_plans(bool $onlyActive=true): array {
    billing_ensure_schema();
    return db()->query("SELECT * FROM saas_plans".($onlyActive?" WHERE ativo=1":"")." ORDER BY ordem,nome")->fetchAll()?:[];
}
function billing_plan(string $id): ?array {
    billing_ensure_schema();
    $q=db()->prepare("SELECT * FROM saas_plans WHERE id=? AND ativo=1 LIMIT 1");$q->execute([$id]);$r=$q->fetch();
    return $r?:null;
}
function billing_get_or_create_subscription(string $igrejaId): array {
    billing_ensure_schema();
    $q=db()->prepare("SELECT * FROM saas_subscriptions WHERE igreja_id=? ORDER BY updated_at DESC LIMIT 1");
    $q->execute([$igrejaId]);$r=$q->fetch();if($r)return $r;
    $start=date('Y-m-d H:i:s');$end=date('Y-m-d H:i:s',time()+billing_trial_days()*86400);
    billing_insert_subscription($igrejaId,$start,$end);
    $q->execute([$igrejaId]);return $q->fetch()?:[];
}
function billing_state(array $sub): array {
    $now=time();$status=(string)($sub['status']??'trial');$can=false;$until=null;$effective=$status?:'expired';
    if($status==='trial'){
        $until=!empty($sub['trial_ends_at'])?strtotime((string)$sub['trial_ends_at']):0;
        $can=$until&&$until>=$now;if(!$can)$effective='expired';
    }elseif(in_array($status,['active','canceled'],true)){
        $until=!empty($sub['current_period_end'])?strtotime((string)$sub['current_period_end']):0;
        $can=$until&&$until>=$now;$effective=$can?'active':'expired';
    }elseif($status==='suspended')$effective='suspended';
    else $effective='expired';
    return ['can_use'=>$can,'status'=>$effective,'days_remaining'=>$can&&$until?max(0,(int)ceil(($until-$now)/86400)):0,'valid_until'=>$until?date(DATE_ATOM,$until):null];
}
function billing_status_for_context(array $ctx): array {
    if(($ctx['role']??null)==='master')return ['can_use'=>true,'status'=>'master','days_remaining'=>null,'valid_until'=>null,'role'=>'master','igreja_id'=>null,'bypass'=>true];
    $igreja=(string)($ctx['igreja_id']??'');
    if($igreja==='')return ['can_use'=>false,'status'=>'no_church','days_remaining'=>0,'valid_until'=>null,'role'=>$ctx['role']??null,'igreja_id'=>null,'bypass'=>false];
    $sub=billing_get_or_create_subscription($igreja);$state=billing_state($sub);$plan=null;
    if(!empty($sub['plan_id'])){$p=billing_plan((string)$sub['plan_id']);if($p)$plan=['id'=>$p['id'],'nome'=>$p['nome']];}
    return $state+['role'=>$ctx['role']??null,'igreja_id'=>$igreja,'bypass'=>false,'plan'=>$plan,'trial_days'=>billing_trial_days()];
}
function billing_mp_request(string $method,string $path,?array $payload=null): array {
    $token=trim((string)billing_cfg('mercadopago_access_token',''));
    if($token==='')throw new RuntimeException('Mercado Pago ainda não configurado pelo Master.');
    $url='https://api.mercadopago.com'.$path;
    $headers=['Authorization: Bearer '.$token,'Content-Type: application/json','Accept: application/json'];
    if(function_exists('curl_init')){
        $ch=curl_init($url);$opts=[CURLOPT_RETURNTRANSFER=>true,CURLOPT_CUSTOMREQUEST=>$method,CURLOPT_HTTPHEADER=>$headers,CURLOPT_TIMEOUT=>25,CURLOPT_CONNECTTIMEOUT=>10];
        if($payload!==null)$opts[CURLOPT_POSTFIELDS]=json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
        curl_setopt_array($ch,$opts);$body=curl_exec($ch);$http=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);$err=curl_error($ch);curl_close($ch);
        if($body===false)throw new RuntimeException('Falha ao conectar ao Mercado Pago: '.$err);
    }else{
        $ctx=stream_context_create(['http'=>['method'=>$method,'header'=>implode("\r\n",$headers),'content'=>$payload!==null?json_encode($payload,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES):'','ignore_errors'=>true,'timeout'=>25]]);
        $body=file_get_contents($url,false,$ctx);$http=0;if(isset($http_response_header[0])&&preg_match('/\s(\d{3})\s/',$http_response_header[0],$m))$http=(int)$m[1];
        if($body===false)throw new RuntimeException('Falha ao conectar ao Mercado Pago.');
    }
    $json=json_decode((string)$body,true);if(!is_array($json))$json=['raw'=>(string)$body];
    if($http<200||$http>=300)throw new RuntimeException('Mercado Pago: '.(string)($json['message']??$json['error']??('HTTP '.$http)));
    return $json;
}
function billing_validate_webhook_signature(string $dataId): bool {
    $secret=trim((string)billing_cfg('mercadopago_webhook_secret',''));
    if($secret==='')return true;
    $sig=(string)($_SERVER['HTTP_X_SIGNATURE']??'');$req=(string)($_SERVER['HTTP_X_REQUEST_ID']??'');
    if($sig==='')return false;$parts=[];
    foreach(explode(',',$sig)as$piece){$kv=explode('=',trim($piece),2);if(count($kv)===2)$parts[$kv[0]]=$kv[1];}
    $ts=(string)($parts['ts']??'');$v1=(string)($parts['v1']??'');if($ts===''||$v1==='')return false;
    $manifest=($dataId!==''?'id:'.$dataId.';':'').($req!==''?'request-id:'.$req.';':'').'ts:'.$ts.';';
    return hash_equals(hash_hmac('sha256',$manifest,$secret),$v1);
}
function billing_activate_order(array $order,string $paymentId,string $paymentStatus): void {
    if(($order['status']??'')==='approved'&&(string)($order['payment_id']??'')===$paymentId)return;
    $pdo=db();$pdo->beginTransaction();
    try{
        $sub=billing_get_or_create_subscription((string)$order['igreja_id']);
        $base=time();
        foreach(['current_period_end','trial_ends_at']as$f)if(!empty($sub[$f])){$t=strtotime((string)$sub[$f]);if($t&&$t>$base)$base=$t;}
        $end=$base+max(1,(int)$order['period_days'])*86400;
        $pdo->prepare("UPDATE saas_subscriptions SET plan_id=?,status='active',current_period_start=?,current_period_end=?,last_payment_id=?,last_payment_status=?,updated_at=NOW() WHERE igreja_id=?")
            ->execute([$order['plan_id'],date('Y-m-d H:i:s',$base),date('Y-m-d H:i:s',$end),$paymentId,$paymentStatus,$order['igreja_id']]);
        $pdo->prepare("UPDATE saas_orders SET status='approved',payment_id=?,raw_status=?,paid_at=COALESCE(paid_at,NOW()),updated_at=NOW() WHERE id=?")
            ->execute([$paymentId,$paymentStatus,$order['id']]);
        $pdo->commit();
    }catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();throw $e;}
}
