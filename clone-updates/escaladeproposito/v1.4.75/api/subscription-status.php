<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
require __DIR__.'/billing_lib_v1313.php';
require_once __DIR__.'/tenant_access_v1323.php';
if(is_file(__DIR__.'/system_observer_v1423.php')){
    require_once __DIR__.'/system_observer_v1423.php';
    if(function_exists('system_observer_v1423_register')) system_observer_v1423_register();
}
try{
    $caller=require_auth();$ctx=user_context();$st=billing_status_for_context($ctx);
    $uid=(string)($caller['id']??$ctx['id']??'');$igreja=(string)($ctx['igreja_id']??'');$role=(string)($ctx['role']??'');
    $billingOwner=$role==='master';
    if(!$billingOwner&&$igreja!=='')$billingOwner=tenant_v1323_is_billing_admin($igreja,$uid);
    $st['billing_owner']=$billingOwner;
    $st['license_scope']='church';
    $st['members_included']=true;
    $st['checkout_url']='/planos.html';
    $st['sales_url']='/vendas.html';
    $st['master_billing_url']='/master-comercial.html';
    out(['data'=>$st,'error'=>null]);
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
