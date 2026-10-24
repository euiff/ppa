<?php
declare(strict_types=1);
require_once __DIR__.'/bootstrap.php';
require_once __DIR__.'/holyrics-core-v1481.php';
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
if(($_SERVER['REQUEST_METHOD']??'GET')!=='GET')out(['data'=>null,'error'=>['message'=>'Método não permitido']],405);
try{
    $action=(string)($_GET['action']??'services');
    // Health público: sem chaves e sem informações de igreja.
    if($action==='health')out(['data'=>['health'=>'ok','version'=>'1.4.84'],'error'=>null]);
    edp_hly_table();
    // PHP em algumas hospedagens não recebe Authorization.
    // O cabeçalho alternativo preserva a chave fora da URL.
    $token=trim((string)($_SERVER['HTTP_X_HOLYRICS_KEY']??''));
    if($token===''){
        $auth=(string)($_SERVER['HTTP_AUTHORIZATION']??$_SERVER['REDIRECT_HTTP_AUTHORIZATION']??'');
        if(preg_match('/^Bearer\\s+([a-f0-9]{48,256})$/i',$auth,$m))$token=$m[1];
    }
    if(!preg_match('/^[a-f0-9]{48,256}$/iD',$token))out(['data'=>null,'error'=>['message'=>'Chave de integração ausente']],401);
    $church=edp_hly_church_by_token(strtolower($token));
    if(!$church)out(['data'=>null,'error'=>['message'=>'Chave inválida ou revogada']],401);
    if($action==='services')out(['data'=>['services'=>edp_hly_services($church)],'error'=>null]);
    if($action==='songs'){
        $id=trim((string)($_GET['service_id']??''));
        if($id==='')out(['data'=>null,'error'=>['message'=>'Selecione o culto']],400);
        $result=edp_hly_songs($church,$id);
        if(isset($result['error']))out(['data'=>null,'error'=>['message'=>$result['error']]],404);
        out(['data'=>$result,'error'=>null]);
    }
    out(['data'=>null,'error'=>['message'=>'Ação inválida']],400);
}catch(Throwable $e){
    error_log('[Holyrics Connect] '.get_class($e).': '.$e->getMessage());
    out(['data'=>null,'error'=>['message'=>'Falha ao consultar repertório']],500);
}
