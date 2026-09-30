<?php
declare(strict_types=1);
require_once __DIR__.'/billing_lib_v1313.php';

function billing_v1314_ensure_schema(): void {
    billing_ensure_schema();
    $pdo=db();
    $pdo->exec("CREATE TABLE IF NOT EXISTS saas_promotions (
      id VARCHAR(36) PRIMARY KEY,
      codigo VARCHAR(60) NOT NULL,
      nome VARCHAR(140) NOT NULL,
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
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $cols=[
      'codigo'=>"VARCHAR(60) NOT NULL DEFAULT ''",'nome'=>"VARCHAR(140) NOT NULL DEFAULT ''",'descricao'=>"VARCHAR(255) NULL",
      'tipo'=>"VARCHAR(20) NOT NULL DEFAULT 'percent'",'valor'=>"DECIMAL(10,2) NOT NULL DEFAULT 0",'plan_id'=>"VARCHAR(40) NULL",
      'starts_at'=>"DATETIME NULL",'ends_at'=>"DATETIME NULL",'ativo'=>"TINYINT(1) NOT NULL DEFAULT 1",'publico'=>"TINYINT(1) NOT NULL DEFAULT 0",
      'max_uses'=>"INT NULL",'uses_count'=>"INT NOT NULL DEFAULT 0",'created_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
      'updated_at'=>"DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
    ];
    foreach($cols as$c=>$def)try{billing_add_col('saas_promotions',$c,$def);}catch(Throwable $e){}
}
function billing_v1314_promotion(?string $code,?string $planId=null,bool $publicOnly=false): ?array {
    billing_v1314_ensure_schema();$code=strtoupper(trim((string)$code));if($code==='')return null;
    $sql="SELECT * FROM saas_promotions WHERE UPPER(codigo)=? AND ativo=1 AND (starts_at IS NULL OR starts_at<=NOW()) AND (ends_at IS NULL OR ends_at>=NOW())";
    if($publicOnly)$sql.=" AND publico=1";
    $sql.=" LIMIT 1";
    $q=db()->prepare($sql);$q->execute([$code]);$p=$q->fetch();if(!$p)return null;
    if(!empty($p['plan_id'])&&$planId!==null&&(string)$p['plan_id']!==$planId)return null;
    if($p['max_uses']!==null&&(int)$p['max_uses']>0&&(int)$p['uses_count']>=(int)$p['max_uses'])return null;
    return $p;
}
function billing_v1314_discount(array $plan,?array $promo): array {
    $original=round((float)$plan['preco'],2);$discount=0.0;
    if($promo){$v=max(0,(float)$promo['valor']);$discount=(($promo['tipo']??'percent')==='fixed')?min($original,$v):min($original,$original*min(100,$v)/100);}
    $discount=round($discount,2);$amount=max(1.00,round($original-$discount,2));
    return ['original'=>$original,'discount'=>$discount,'amount'=>$amount];
}
function billing_v1314_public_promotions(): array {
    billing_v1314_ensure_schema();
    return db()->query("SELECT id,codigo,nome,descricao,tipo,valor,plan_id,ends_at FROM saas_promotions
      WHERE ativo=1 AND publico=1 AND (starts_at IS NULL OR starts_at<=NOW()) AND (ends_at IS NULL OR ends_at>=NOW())
        AND (max_uses IS NULL OR max_uses=0 OR uses_count<max_uses)
      ORDER BY created_at DESC LIMIT 10")->fetchAll()?:[];
}
function billing_v1314_activate_order(array $order,string $paymentId,string $paymentStatus): void {
    billing_activate_order($order,$paymentId,$paymentStatus);
    if(!empty($order['promotion_code'])){
        db()->prepare("UPDATE saas_promotions SET uses_count=uses_count+1,updated_at=NOW() WHERE UPPER(codigo)=UPPER(?)")
          ->execute([$order['promotion_code']]);
    }
}
function billing_v1314_subscription_row(string $igrejaId): array {
    billing_v1314_ensure_schema();
    $q=db()->prepare("SELECT s.*,p.nome plan_nome,p.preco plan_preco FROM saas_subscriptions s
      LEFT JOIN saas_plans p ON p.id=s.plan_id WHERE s.igreja_id=? ORDER BY s.updated_at DESC LIMIT 1");
    $q->execute([$igrejaId]);$r=$q->fetch();
    if(!$r){billing_get_or_create_subscription($igrejaId);$q->execute([$igrejaId]);$r=$q->fetch();}
    return $r?:[];
}
