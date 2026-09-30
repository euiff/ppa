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
    $plans=array_map(fn($p)=>[
      'id'=>$p['id'],'nome'=>$p['nome'],'descricao'=>$p['descricao']??null,
      'preco'=>(float)$p['preco'],'duracao_dias'=>(int)$p['duracao_dias'],'destaque'=>(bool)$p['destaque']
    ],billing_plans(true));
    $promos=array_map(fn($p)=>[
      'codigo'=>$p['codigo'],'nome'=>$p['nome'],'descricao'=>$p['descricao']??null,
      'tipo'=>$p['tipo'],'valor'=>(float)$p['valor'],'plan_id'=>$p['plan_id']??null,'ends_at'=>$p['ends_at']??null
    ],billing_v1314_public_promotions());
    out(['data'=>[
      'produto'=>'Escala de Propósito','trial_days'=>billing_trial_days(),'plans'=>$plans,'promotions'=>$promos,
      'sales_whatsapp'=>billing_cfg('saas_sales_whatsapp',''),'sales_email'=>billing_cfg('saas_sales_email','')
    ],'error'=>null]);
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
