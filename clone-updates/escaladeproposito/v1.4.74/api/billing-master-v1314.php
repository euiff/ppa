<?php
declare(strict_types=1);

require_once __DIR__.'/bootstrap.php';

$auth=require_auth();
$ctx=user_context();
if(($ctx['role']??'')!=='master'){
    out(['data'=>null,'error'=>['message'=>'Somente o Master pode acessar a gestão comercial.']],403);
}

function cm_col(string $table,string $column): bool {
    static $cache=[];
    $k=$table.'.'.$column;
    if(array_key_exists($k,$cache)) return $cache[$k];
    try{
        $q=db()->prepare("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=? AND column_name=?");
        $q->execute([$table,$column]);
        return $cache[$k]=(int)$q->fetchColumn()>0;
    }catch(Throwable $e){ return $cache[$k]=false; }
}
function cm_add_col(string $table,string $column,string $definition): void {
    if(cm_col($table,$column)) return;
    db()->exec("ALTER TABLE `$table` ADD COLUMN `$column` $definition");
}
function cm_schema(): void {
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
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      KEY idx_saas_sub_status(status),
      KEY idx_saas_sub_end(current_period_end)
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
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      UNIQUE KEY uq_saas_orders_ext(external_reference),
      KEY idx_saas_orders_igreja(igreja_id),
      KEY idx_saas_orders_payment(payment_id),
      KEY idx_saas_orders_status(status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");

    $pdo->exec("CREATE TABLE IF NOT EXISTS saas_promotions (
      id VARCHAR(36) PRIMARY KEY,
      codigo VARCHAR(60) NOT NULL,
      nome VARCHAR(120) NOT NULL,
      descricao VARCHAR(255) NULL,
      tipo VARCHAR(20) NOT NULL DEFAULT 'percent',
      valor DECIMAL(10,2) NOT NULL DEFAULT 0,
      plan_id VARCHAR(40) NULL,
      starts_at DATETIME NULL,
      ends_at DATETIME NULL,
      ativo TINYINT(1) NOT NULL DEFAULT 1,
      publico TINYINT(1) NOT NULL DEFAULT 0,
      max_uses INT NULL,
      uses_count INT NOT NULL DEFAULT 0,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      UNIQUE KEY uq_saas_promotions_codigo(codigo)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");

    // Corrige tabelas comerciais de instalações que passaram por versões antigas.
    $cols=[
      'saas_plans'=>[
        'nome'=>"VARCHAR(120) NOT NULL DEFAULT ''",
        'descricao'=>"VARCHAR(255) NULL",
        'preco'=>"DECIMAL(10,2) NOT NULL DEFAULT 0",
        'duracao_dias'=>"INT NOT NULL DEFAULT 30",
        'ativo'=>"TINYINT(1) NOT NULL DEFAULT 1",
        'destaque'=>"TINYINT(1) NOT NULL DEFAULT 0",
        'ordem'=>"INT NOT NULL DEFAULT 0",
        'created_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
        'updated_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
      ],
      'saas_subscriptions'=>[
        'plan_id'=>"VARCHAR(40) NULL",
        'status'=>"VARCHAR(30) NOT NULL DEFAULT 'trial'",
        'manual_note'=>"VARCHAR(255) NULL",
        'last_payment_id'=>"VARCHAR(120) NULL",
        'last_payment_status'=>"VARCHAR(40) NULL",
        'trial_started_at'=>"DATETIME NULL",
        'trial_ends_at'=>"DATETIME NULL",
        'current_period_start'=>"DATETIME NULL",
        'current_period_end'=>"DATETIME NULL",
        'created_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
        'updated_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
      ],
      'saas_orders'=>[
        'igreja_id'=>"VARCHAR(36) NULL",
        'plan_id'=>"VARCHAR(40) NULL",
        'amount'=>"DECIMAL(10,2) NOT NULL DEFAULT 0",
        'original_amount'=>"DECIMAL(10,2) NULL",
        'discount_amount'=>"DECIMAL(10,2) NOT NULL DEFAULT 0",
        'promotion_code'=>"VARCHAR(60) NULL",
        'period_days'=>"INT NOT NULL DEFAULT 30",
        'status'=>"VARCHAR(30) NOT NULL DEFAULT 'pending'",
        'external_reference'=>"VARCHAR(120) NULL",
        'manual_note'=>"VARCHAR(255) NULL",
        'preference_id'=>"VARCHAR(160) NULL",
        'payment_id'=>"VARCHAR(120) NULL",
        'init_point'=>"TEXT NULL",
        'raw_status'=>"VARCHAR(60) NULL",
        'paid_at'=>"DATETIME NULL",
        'created_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
        'updated_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
      ],
      'saas_promotions'=>[
        'codigo'=>"VARCHAR(60) NOT NULL DEFAULT ''",
        'nome'=>"VARCHAR(120) NOT NULL DEFAULT ''",
        'descricao'=>"VARCHAR(255) NULL",
        'tipo'=>"VARCHAR(20) NOT NULL DEFAULT 'percent'",
        'valor'=>"DECIMAL(10,2) NOT NULL DEFAULT 0",
        'plan_id'=>"VARCHAR(40) NULL",
        'starts_at'=>"DATETIME NULL",
        'ends_at'=>"DATETIME NULL",
        'ativo'=>"TINYINT(1) NOT NULL DEFAULT 1",
        'publico'=>"TINYINT(1) NOT NULL DEFAULT 0",
        'max_uses'=>"INT NULL",
        'uses_count'=>"INT NOT NULL DEFAULT 0",
        'created_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
        'updated_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
      ],
    ];
    foreach($cols as$t=>$list){
        foreach($list as$c=>$def){
            try{ cm_add_col($t,$c,$def); }catch(Throwable $e){}
        }
    }

    $defaults=[
      ['basico','Básico','Acesso completo por 30 dias',39.90,30,1,1,10],
      ['semestral','Semestral','6 meses de acesso',199.90,180,1,0,20],
      ['anual','Anual','12 meses de acesso',349.90,365,1,0,30],
    ];
    $st=$pdo->prepare("INSERT IGNORE INTO saas_plans(id,nome,descricao,preco,duracao_dias,ativo,destaque,ordem) VALUES(?,?,?,?,?,?,?,?)");
    foreach($defaults as$d)$st->execute($d);
}
function cm_cfg(string $key,string $default=''): string {
    try{
        $q=db()->prepare("SELECT valor FROM api_config WHERE chave=? AND igreja_id IS NULL ORDER BY updated_at DESC LIMIT 1");
        $q->execute([$key]);
        $v=$q->fetchColumn();
        return $v===false?$default:(string)$v;
    }catch(Throwable $e){ return $default; }
}
function cm_set_cfg(string $key,string $value): void {
    $pdo=db();
    $pdo->prepare("DELETE FROM api_config WHERE chave=? AND igreja_id IS NULL")->execute([$key]);
    $pdo->prepare("INSERT INTO api_config(id,chave,valor,igreja_id,updated_at) VALUES(?,?,?,NULL,NOW())")
        ->execute([uuid4(),$key,$value]);
}
function cm_trial_days(): int {
    return max(1,min(90,(int)cm_cfg('saas_trial_days','10')));
}
function cm_app_url(): string {
    global $config;
    $u=rtrim((string)($config['app_url']??''),'/');
    if($u!=='')return $u;
    $https=(!empty($_SERVER['HTTPS'])&&strtolower((string)$_SERVER['HTTPS'])!=='off')
        || (string)($_SERVER['HTTP_X_FORWARDED_PROTO']??'')==='https';
    $host=(string)($_SERVER['HTTP_HOST']??'escaladeproposito.com.br');
    return ($https?'https':'http').'://'.$host;
}
function cm_mask(string $v): string {
    $v=trim($v);
    if($v==='')return '';
    if(strlen($v)<=10)return str_repeat('•',strlen($v));
    return substr($v,0,6).str_repeat('•',max(8,strlen($v)-10)).substr($v,-4);
}
function cm_dt(mixed $v): ?string {
    $v=trim((string)$v);
    if($v==='')return null;
    $t=strtotime($v);
    return $t?date('Y-m-d H:i:s',$t):null;
}
function cm_plan(string $id,bool $activeOnly=false): ?array {
    if($id==='')return null;
    $sql="SELECT * FROM saas_plans WHERE id=?".($activeOnly?" AND ativo=1":"")." LIMIT 1";
    $q=db()->prepare($sql);$q->execute([$id]);$r=$q->fetch();
    return $r?:null;
}
function cm_ensure_subscription(string $churchId): array {
    $q=db()->prepare("SELECT * FROM saas_subscriptions WHERE igreja_id=? LIMIT 1");
    $q->execute([$churchId]);$r=$q->fetch();
    if($r)return $r;

    $start=date('Y-m-d H:i:s');
    $end=date('Y-m-d H:i:s',time()+cm_trial_days()*86400);
    db()->prepare("INSERT INTO saas_subscriptions(igreja_id,status,trial_started_at,trial_ends_at,created_at,updated_at) VALUES(?,'trial',?,?,NOW(),NOW())")
      ->execute([$churchId,$start,$end]);

    $q->execute([$churchId]);
    return $q->fetch()?:[];
}
function cm_state(array $sub): array {
    $now=time();
    $status=(string)($sub['status']??'trial');
    $until=null;$can=false;$effective=$status?:'expired';

    if($status==='trial'){
        $until=!empty($sub['trial_ends_at'])?strtotime((string)$sub['trial_ends_at']):0;
        $can=$until&&$until>=$now;
        if(!$can)$effective='expired';
    }elseif(in_array($status,['active','canceled'],true)){
        $until=!empty($sub['current_period_end'])?strtotime((string)$sub['current_period_end']):0;
        $can=$until&&$until>=$now;
        $effective=$can?'active':'expired';
    }elseif($status==='suspended'){
        $effective='suspended';
    }elseif($status==='expired'){
        $effective='expired';
    }

    return [
      'can_use'=>$can,
      'status'=>$effective,
      'days_remaining'=>$can&&$until?max(0,(int)ceil(($until-$now)/86400)):0,
      'valid_until'=>$until?date(DATE_ATOM,$until):null
    ];
}
function cm_churches(): array {
    $hasCreated=cm_col('igrejas','created_at');
    $created=$hasCreated?',i.created_at':'';
    $order=$hasCreated?'i.created_at DESC':'i.nome ASC';

    $sql="SELECT i.id,i.nome$created,
             s.plan_id,s.status,s.trial_started_at,s.trial_ends_at,
             s.current_period_start,s.current_period_end,s.last_payment_status,s.manual_note,
             p.nome plan_nome,
             (SELECT COUNT(*) FROM profiles pr WHERE pr.igreja_id=i.id) user_count
          FROM igrejas i
          LEFT JOIN saas_subscriptions s ON s.igreja_id=i.id
          LEFT JOIN saas_plans p ON p.id=s.plan_id
          ORDER BY $order";
    $rows=db()->query($sql)->fetchAll()?:[];

    foreach($rows as&$c){
        if(empty($c['status'])){
            $sub=cm_ensure_subscription((string)$c['id']);
            $c=array_merge($c,$sub);
            if(!empty($c['plan_id'])){
                $pl=cm_plan((string)$c['plan_id']);
                $c['plan_nome']=$pl['nome']??null;
            }
        }
        $st=cm_state($c);
        $c['effective_status']=$st['status'];
        $c['can_use']=$st['can_use'];
        $c['days_remaining']=$st['days_remaining'];
        $c['valid_until']=$st['valid_until'];
    }
    unset($c);
    return $rows;
}
function cm_users(): array {
    $sql="SELECT u.id,u.email,u.created_at,p.nome,p.whatsapp,p.igreja_id,i.nome igreja_nome,
        (SELECT GROUP_CONCAT(ur.role ORDER BY ur.role SEPARATOR ', ') FROM user_roles ur WHERE ur.user_id=u.id) roles
      FROM users u
      LEFT JOIN profiles p ON p.id=u.id
      LEFT JOIN igrejas i ON i.id=p.igreja_id
      ORDER BY u.created_at DESC
      LIMIT 500";
    return db()->query($sql)->fetchAll()?:[];
}
function cm_orders(): array {
    return db()->query("SELECT o.*,p.nome plan_nome,i.nome igreja_nome
      FROM saas_orders o
      LEFT JOIN saas_plans p ON p.id=o.plan_id
      LEFT JOIN igrejas i ON i.id=o.igreja_id
      ORDER BY o.created_at DESC LIMIT 300")->fetchAll()?:[];
}
function cm_response(): never {
    $plans=db()->query("SELECT * FROM saas_plans ORDER BY ordem,nome")->fetchAll()?:[];
    $promos=db()->query("SELECT * FROM saas_promotions ORDER BY created_at DESC")->fetchAll()?:[];
    $churches=cm_churches();
    $orders=cm_orders();
    $users=cm_users();

    $month=(float)(db()->query("SELECT COALESCE(SUM(amount),0) FROM saas_orders WHERE status='approved' AND paid_at>=DATE_FORMAT(NOW(),'%Y-%m-01')")->fetchColumn()?:0);
    $total=(float)(db()->query("SELECT COALESCE(SUM(amount),0) FROM saas_orders WHERE status='approved'")->fetchColumn()?:0);

    $stats=[
      'igrejas'=>count($churches),'usuarios'=>count($users),
      'trial'=>0,'active'=>0,'expired'=>0,'suspended'=>0,
      'revenue_month'=>$month,'revenue_total'=>$total,'pending_orders'=>0
    ];
    foreach($churches as$c){
        $s=(string)($c['effective_status']??'expired');
        if(isset($stats[$s]))$stats[$s]++;
        elseif($s==='canceled')$stats['expired']++;
    }
    foreach($orders as$o){
        if(in_array((string)$o['status'],['pending','in_process'],true))$stats['pending_orders']++;
    }

    $access=cm_cfg('mercadopago_access_token','');
    $secret=cm_cfg('mercadopago_webhook_secret','');

    out(['data'=>[
      'stats'=>$stats,
      'trial_days'=>cm_trial_days(),
      'sales_whatsapp'=>cm_cfg('saas_sales_whatsapp',''),
      'sales_email'=>cm_cfg('saas_sales_email',''),
      'mercadopago_access_token_masked'=>cm_mask($access),
      'mercadopago_access_token_configured'=>$access!=='',
      'mercadopago_public_key'=>cm_cfg('mercadopago_public_key',''),
      'mercadopago_webhook_secret_masked'=>cm_mask($secret),
      'mercadopago_webhook_secret_configured'=>$secret!=='',
      'webhook_url'=>cm_app_url().'/api/mercadopago-webhook.php',
      'sales_url'=>cm_app_url().'/',
      'plans'=>$plans,
      'promotions'=>$promos,
      'churches'=>$churches,
      'orders'=>$orders,
      'users'=>$users
    ],'error'=>null]);
}

try{
    cm_schema();
    $req=input_json();
    $action=(string)($req['action']??'');

    if($_SERVER['REQUEST_METHOD']==='POST'){
        if($action==='save_settings'){
            cm_set_cfg('saas_trial_days',(string)max(1,min(90,(int)($req['trial_days']??10))));
            cm_set_cfg('saas_sales_whatsapp',trim((string)($req['sales_whatsapp']??'')));
            cm_set_cfg('saas_sales_email',trim((string)($req['sales_email']??'')));
            cm_set_cfg('mercadopago_public_key',trim((string)($req['mercadopago_public_key']??'')));
            foreach(['mercadopago_access_token','mercadopago_webhook_secret'] as$k){
                if(array_key_exists($k,$req)&&trim((string)$req[$k])!==''){
                    cm_set_cfg($k,trim((string)$req[$k]));
                }
            }
            audit((string)$ctx['id'],'commercial_settings_updated','saas',[],'info');
        }
        elseif($action==='save_plan'){
            $id=trim((string)($req['id']??''));
            if($id==='')$id='plano-'.substr(preg_replace('/[^a-z0-9]+/i','-',strtolower(trim((string)($req['nome']??'plano')))),0,22).'-'.substr(bin2hex(random_bytes(3)),0,6);
            $nome=trim((string)($req['nome']??''));
            if($nome==='')throw new RuntimeException('Informe o nome do plano.');
            db()->prepare("INSERT INTO saas_plans(id,nome,descricao,preco,duracao_dias,ativo,destaque,ordem,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,NOW(),NOW())
              ON DUPLICATE KEY UPDATE nome=VALUES(nome),descricao=VALUES(descricao),preco=VALUES(preco),
              duracao_dias=VALUES(duracao_dias),ativo=VALUES(ativo),destaque=VALUES(destaque),ordem=VALUES(ordem),updated_at=NOW()")
              ->execute([
                $id,$nome,trim((string)($req['descricao']??'')),
                max(0,(float)($req['preco']??0)),max(1,(int)($req['duracao_dias']??30)),
                !empty($req['ativo'])?1:0,!empty($req['destaque'])?1:0,(int)($req['ordem']??0)
              ]);
        }
        elseif($action==='delete_plan'){
            $id=(string)($req['id']??'');
            if($id==='')throw new RuntimeException('Plano inválido.');
            $q=db()->prepare("SELECT COUNT(*) FROM saas_orders WHERE plan_id=?");$q->execute([$id]);
            if((int)$q->fetchColumn()>0){
                db()->prepare("UPDATE saas_plans SET ativo=0,updated_at=NOW() WHERE id=?")->execute([$id]);
            }else{
                db()->prepare("DELETE FROM saas_plans WHERE id=?")->execute([$id]);
            }
        }
        elseif($action==='save_promotion'){
            $id=trim((string)($req['id']??''))?:uuid4();
            $codigo=strtoupper(trim((string)($req['codigo']??'')));
            $nome=trim((string)($req['nome']??''));
            if($codigo===''||$nome==='')throw new RuntimeException('Informe código e nome da promoção.');
            $tipo=in_array((string)($req['tipo']??''),['percent','fixed'],true)?(string)$req['tipo']:'percent';
            $valor=max(0,(float)($req['valor']??0));if($tipo==='percent')$valor=min(100,$valor);
            $max=(int)($req['max_uses']??0);
            db()->prepare("INSERT INTO saas_promotions(id,codigo,nome,descricao,tipo,valor,plan_id,starts_at,ends_at,ativo,publico,max_uses,uses_count,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,NOW(),NOW())
              ON DUPLICATE KEY UPDATE codigo=VALUES(codigo),nome=VALUES(nome),descricao=VALUES(descricao),tipo=VALUES(tipo),
              valor=VALUES(valor),plan_id=VALUES(plan_id),starts_at=VALUES(starts_at),ends_at=VALUES(ends_at),
              ativo=VALUES(ativo),publico=VALUES(publico),max_uses=VALUES(max_uses),updated_at=NOW()")
              ->execute([
                $id,$codigo,$nome,trim((string)($req['descricao']??'')),$tipo,$valor,
                trim((string)($req['plan_id']??''))?:null,cm_dt($req['starts_at']??null),cm_dt($req['ends_at']??null),
                !empty($req['ativo'])?1:0,!empty($req['publico'])?1:0,$max>0?$max:null
              ]);
        }
        elseif($action==='delete_promotion'){
            db()->prepare("DELETE FROM saas_promotions WHERE id=?")->execute([(string)($req['id']??'')]);
        }
        elseif($action==='subscription_set'){
            $church=(string)($req['igreja_id']??'');
            if($church==='')throw new RuntimeException('Igreja inválida.');
            cm_ensure_subscription($church);
            $status=(string)($req['status']??'active');
            if(!in_array($status,['trial','active','suspended','canceled','expired'],true))$status='active';
            $plan=trim((string)($req['plan_id']??''))?:null;
            $end=cm_dt($req['valid_until']??null);
            $note=trim((string)($req['note']??''));
            if($status==='trial'){
                db()->prepare("UPDATE saas_subscriptions SET plan_id=?,status='trial',trial_ends_at=?,manual_note=?,updated_at=NOW() WHERE igreja_id=?")
                  ->execute([$plan,$end,$note,$church]);
            }else{
                db()->prepare("UPDATE saas_subscriptions SET plan_id=?,status=?,current_period_end=?,manual_note=?,updated_at=NOW() WHERE igreja_id=?")
                  ->execute([$plan,$status,$end,$note,$church]);
            }
        }
        elseif($action==='add_days'){
            $church=(string)($req['igreja_id']??'');
            if($church==='')throw new RuntimeException('Igreja inválida.');
            $days=max(1,min(3650,(int)($req['days']??30)));
            $sub=cm_ensure_subscription($church);
            $base=time();
            foreach(['current_period_end','trial_ends_at']as$f){
                if(!empty($sub[$f])){$t=strtotime((string)$sub[$f]);if($t&&$t>$base)$base=$t;}
            }
            $end=date('Y-m-d H:i:s',$base+$days*86400);
            db()->prepare("UPDATE saas_subscriptions SET status='active',current_period_start=COALESCE(current_period_start,NOW()),
              current_period_end=?,manual_note=?,updated_at=NOW() WHERE igreja_id=?")
              ->execute([$end,trim((string)($req['note']??'Liberação manual pelo Master')),$church]);
        }
        elseif($action==='manual_payment'){
            $church=(string)($req['igreja_id']??'');
            $plan=cm_plan((string)($req['plan_id']??''),false);
            if($church===''||!$plan)throw new RuntimeException('Informe igreja e plano válidos.');
            $id=uuid4();$amount=array_key_exists('amount',$req)?max(0,(float)$req['amount']):(float)$plan['preco'];
            $note=trim((string)($req['note']??'Pagamento manual'));
            $ext='MANUAL-'.$id;
            db()->prepare("INSERT INTO saas_orders(id,igreja_id,plan_id,amount,original_amount,discount_amount,period_days,status,
              external_reference,payment_id,raw_status,manual_note,created_at,paid_at,updated_at)
              VALUES(?,?,?,?,?,0,?,'approved',? ,?,'manual',?,NOW(),NOW(),NOW())")
              ->execute([$id,$church,$plan['id'],$amount,$amount,(int)$plan['duracao_dias'],$ext,'manual-'.$id,$note]);

            $sub=cm_ensure_subscription($church);$base=time();
            foreach(['current_period_end','trial_ends_at']as$f){
                if(!empty($sub[$f])){$t=strtotime((string)$sub[$f]);if($t&&$t>$base)$base=$t;}
            }
            $end=date('Y-m-d H:i:s',$base+max(1,(int)$plan['duracao_dias'])*86400);
            db()->prepare("UPDATE saas_subscriptions SET plan_id=?,status='active',current_period_start=NOW(),current_period_end=?,
              last_payment_id=?,last_payment_status='approved',manual_note=?,updated_at=NOW() WHERE igreja_id=?")
              ->execute([$plan['id'],$end,'manual-'.$id,$note,$church]);
        }
        elseif($action==='force_logout_user'){
            $uid=(string)($req['user_id']??'');
            if($uid==='')throw new RuntimeException('Usuário inválido.');
            db()->prepare("DELETE FROM user_sessions WHERE user_id=?")->execute([$uid]);
        }
        else{
            throw new RuntimeException('Ação comercial inválida.');
        }
    }

    cm_response();
}catch(Throwable $e){
    try{ audit((string)($ctx['id']??''),'commercial_api_error','billing',['message'=>$e->getMessage()],'error'); }catch(Throwable $x){}
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
