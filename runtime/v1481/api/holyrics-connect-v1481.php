<?php
declare(strict_types=1);
require_once __DIR__.'/bootstrap.php';
require_once __DIR__.'/holyrics-core-v1481.php';
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
$u=require_auth();$ctx=user_context();
$role=(string)($ctx['role']??'');$own=(string)($ctx['igreja_id']??'');
if(!in_array($role,['master','admin','pastor'],true))out(['data'=>null,'error'=>['message'=>'Sem permissão para configurar o Holyrics']],403);
$body=($_SERVER['REQUEST_METHOD']??'GET')==='POST'?input_json():$_GET;
$church=trim((string)($body['igreja_id']??$own));
$action=(string)($body['action']??'status');
if($action==='churches'){
    if($role==='master'){
        $q=db()->query('SELECT id,nome FROM igrejas ORDER BY nome');
        out(['data'=>['churches'=>$q->fetchAll(PDO::FETCH_ASSOC)?:[],'master'=>true],'error'=>null]);
    }
    $q=db()->prepare('SELECT id,nome FROM igrejas WHERE BINARY id=BINARY ? LIMIT 1');
    $q->execute([$own]);
    $row=$q->fetch(PDO::FETCH_ASSOC);
    out(['data'=>['churches'=>$row?[$row]:[],'master'=>false],'error'=>null]);
}
if(!edp_hly_allowed_church($role,$own,$church))out(['data'=>null,'error'=>['message'=>'Igreja inválida ou sem permissão']],403);
try{
    edp_hly_table();
    $q=db()->prepare('SELECT id,nome FROM igrejas WHERE BINARY id=BINARY ? LIMIT 1');
    $q->execute([$church]);$name=$q->fetch(PDO::FETCH_ASSOC);
    if(!$name)out(['data'=>null,'error'=>['message'=>'Igreja não encontrada']],404);
    $action=(string)($body['action']??'status');
    if($action==='status'){
        $q=db()->prepare('SELECT ativo,atualizado_em FROM holyrics_integracoes WHERE BINARY igreja_id=BINARY ?');
        $q->execute([$church]);$row=$q->fetch(PDO::FETCH_ASSOC);
        out(['data'=>['igreja'=>$name,'configured'=>(bool)($row&&$row['ativo']),'updated_at'=>$row['atualizado_em']??null],'error'=>null]);
    }
    if(($_SERVER['REQUEST_METHOD']??'GET')!=='POST')out(['data'=>null,'error'=>['message'=>'Use POST para modificar']],405);
    if($action==='rotate'){
        $token=bin2hex(random_bytes(32));$hash=hash('sha256',$token);
        $q=db()->prepare('INSERT INTO holyrics_integracoes (igreja_id,token_hash,ativo,atualizado_em) VALUES (?,?,1,NOW()) ON DUPLICATE KEY UPDATE token_hash=VALUES(token_hash),ativo=1,atualizado_em=NOW()');
        $q->execute([$church,$hash]);
        out(['data'=>['igreja'=>$name,'configured'=>true,'token'=>$token,'warning'=>'Guarde a chave agora. Ela não pode ser recuperada. Uma chave anterior foi revogada.'],'error'=>null]);
    }
    if($action==='revoke'){
        $q=db()->prepare('UPDATE holyrics_integracoes SET ativo=0,atualizado_em=NOW() WHERE BINARY igreja_id=BINARY ?');$q->execute([$church]);
        out(['data'=>['igreja'=>$name,'configured'=>false,'revoked'=>true],'error'=>null]);
    }
    out(['data'=>null,'error'=>['message'=>'Ação inválida']],400);
}catch(Throwable $e){
    error_log('[Holyrics Connect admin] '.get_class($e).': '.$e->getMessage());
    out(['data'=>null,'error'=>['message'=>'Não foi possível salvar a integração']],500);
}
