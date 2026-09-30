<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
require __DIR__.'/billing_lib_v1314.php';
require_once __DIR__.'/tenant_access_v1323.php';
if(is_file(__DIR__.'/system_observer_v1423.php')){
    require_once __DIR__.'/system_observer_v1423.php';
    if(function_exists('system_observer_v1423_register')) system_observer_v1423_register();
}

try{
    billing_v1314_ensure_schema();
    $caller=require_auth();$ctx=user_context();
    if(($ctx['role']??null)==='master') out(['data'=>null,'error'=>['message'=>'A conta Master não precisa contratar plano.']],400);
    $igreja=(string)($ctx['igreja_id']??'');
    if($igreja==='') out(['data'=>null,'error'=>['message'=>'Conta sem igreja vinculada.']],400);
    $uid=(string)($caller['id']??$ctx['id']??'');
    if(!tenant_v1323_is_billing_admin($igreja,$uid)) out(['data'=>null,'error'=>['message'=>'A licença é da igreja. Somente o administrador principal pode contratar ou renovar o plano.']],403);

    $req=input_json();
    $plan=billing_plan((string)($req['plan_id']??''));
    if(!$plan) out(['data'=>null,'error'=>['message'=>'Plano inválido.']],400);

    $promoCode=strtoupper(trim((string)($req['promo_code']??'')));
    $promo=$promoCode!==''?billing_v1314_promotion($promoCode,(string)$plan['id']):null;
    if($promoCode!==''&&!$promo) out(['data'=>null,'error'=>['message'=>'Cupom inválido, expirado ou não disponível para este plano.']],400);
    $price=billing_v1314_discount($plan,$promo);

    $ua=(string)($_SERVER['HTTP_USER_AGENT']??'');
    if(str_contains($ua,'EscalaPlay/1')){
        out(['data'=>null,'error'=>['code'=>'play_consumption_only','message'=>'Compras não são processadas nesta versão do aplicativo.']],403);
    }

    $seed=uuid4();
    $ext='ECP-'.$seed;
    $amount=$price['amount'];
    $days=(int)$plan['duracao_dias'];
    $app=billing_app_url();
    $orderId=billing_insert_order([
      'id'=>$seed,'igreja_id'=>$igreja,'plan_id'=>$plan['id'],'amount'=>$amount,
      'original_amount'=>$price['original'],'discount_amount'=>$price['discount'],
      'promotion_code'=>$promo?$promo['codigo']:null,'period_days'=>$days,'status'=>'pending',
      'external_reference'=>$ext,'created_at'=>date('Y-m-d H:i:s')
    ]);

    try{
        $desc=(string)($plan['descricao']??'').($promo?' • promoção '.$promo['codigo']:'');
        $pref=billing_mp_request('POST','/checkout/preferences',[
          'items'=>[[
            'id'=>(string)$plan['id'],'title'=>'Escala de Propósito - '.$plan['nome'],'description'=>$desc,
            'quantity'=>1,'currency_id'=>'BRL','unit_price'=>$amount
          ]],
          'external_reference'=>$ext,
          'notification_url'=>$app.'/api/mercadopago-webhook.php',
          'back_urls'=>[
            'success'=>$app.'/planos.html?payment=success',
            'pending'=>$app.'/planos.html?payment=pending',
            'failure'=>$app.'/planos.html?payment=failure'
          ],
          'auto_return'=>'approved',
          'metadata'=>['order_id'=>$orderId,'igreja_id'=>$igreja,'plan_id'=>$plan['id'],'promotion_code'=>$promo?$promo['codigo']:null]
        ]);
        $init=(string)($pref['init_point']??'');
        if($init==='')throw new RuntimeException('Mercado Pago não retornou o link do checkout.');
        db()->prepare('UPDATE saas_orders SET preference_id=?,init_point=?,updated_at=NOW() WHERE id=?')
          ->execute([(string)($pref['id']??''),$init,$orderId]);
        out(['data'=>[
          'order_id'=>$orderId,'checkout_url'=>$init,'original_amount'=>$price['original'],
          'discount_amount'=>$price['discount'],'amount'=>$amount,'promotion_code'=>$promo?$promo['codigo']:null
        ],'error'=>null]);
    }catch(Throwable $e){
        db()->prepare("UPDATE saas_orders SET status='error',raw_status=?,updated_at=NOW() WHERE id=?")
          ->execute([substr($e->getMessage(),0,60),$orderId]);
        throw $e;
    }
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
