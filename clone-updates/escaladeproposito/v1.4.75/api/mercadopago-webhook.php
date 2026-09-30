<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
require __DIR__.'/billing_lib_v1314.php';
if(is_file(__DIR__.'/system_observer_v1423.php')){
    require_once __DIR__.'/system_observer_v1423.php';
    if(function_exists('system_observer_v1423_register')) system_observer_v1423_register();
}
try{
    billing_v1314_ensure_schema();
    $body=input_json();$dataId='';
    if(isset($_GET['data_id']))$dataId=(string)$_GET['data_id'];
    elseif(isset($_GET['id']))$dataId=(string)$_GET['id'];
    elseif(isset($body['data']['id']))$dataId=(string)$body['data']['id'];
    elseif(isset($body['id'])&&(($body['type']??'')==='payment'))$dataId=(string)$body['id'];

    if($dataId==='')out(['ok'=>true,'ignored'=>'no_payment_id']);
    if(!billing_validate_webhook_signature($dataId))out(['ok'=>false,'error'=>'invalid_signature'],401);

    $payment=billing_mp_request('GET','/v1/payments/'.rawurlencode($dataId));
    $ext=(string)($payment['external_reference']??'');
    $status=(string)($payment['status']??'unknown');
    if($ext==='')out(['ok'=>true,'ignored'=>'no_external_reference']);

    $q=db()->prepare('SELECT * FROM saas_orders WHERE external_reference=? LIMIT 1');
    $q->execute([$ext]);$order=$q->fetch();
    if(!$order)out(['ok'=>true,'ignored'=>'unknown_order']);

    $paid=(float)($payment['transaction_amount']??0);$expected=(float)$order['amount'];
    if(abs($paid-$expected)>0.02){
        db()->prepare("UPDATE saas_orders SET status='amount_mismatch',payment_id=?,raw_status=?,updated_at=NOW() WHERE id=?")
          ->execute([$dataId,$status,$order['id']]);
        out(['ok'=>true,'ignored'=>'amount_mismatch']);
    }
    if($status==='approved'){
        billing_v1314_activate_order($order,$dataId,$status);
    }else{
        $mapped=in_array($status,['pending','in_process','rejected','cancelled','refunded','charged_back'],true)?$status:'pending';
        db()->prepare('UPDATE saas_orders SET status=?,payment_id=?,raw_status=?,updated_at=NOW() WHERE id=?')
          ->execute([$mapped,$dataId,$status,$order['id']]);
        if(in_array($status,['refunded','charged_back'],true)){
            db()->prepare("UPDATE saas_subscriptions SET status='suspended',last_payment_status=?,updated_at=NOW() WHERE igreja_id=? AND last_payment_id=?")
              ->execute([$status,$order['igreja_id'],$dataId]);
        }
    }
    out(['ok'=>true]);
}catch(Throwable $e){
    error_log('[mercadopago-webhook] '.$e->getMessage());
    out(['ok'=>false,'error'=>$e->getMessage()],500);
}
