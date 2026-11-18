<?php
declare(strict_types=1);
/**
 * Escala de Propósito v1.4.96 — edição segura de músicas do repertório.
 * Apenas master, pastor/admin da igreja ou líder de departamento vinculado à igreja.
 * Sempre restringe a alteração por id DA MÚSICA + igreja_id.
 */
require_once __DIR__.'/bootstrap.php';
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');

if (($_SERVER['REQUEST_METHOD']??'')!=='POST') {
    out(['data'=>null,'error'=>['message'=>'Use POST']],405);
}
$actor=require_auth();
$ctx=user_context();
$role=strtolower(trim((string)($ctx['role']??'')));
$actorId=(string)($actor['id']??$ctx['id']??'');
$ownChurch=(string)($ctx['igreja_id']??'');
$body=input_json();
$musicId=trim((string)($body['id']??''));
$requestedChurch=trim((string)($body['igreja_id']??''));

if($musicId==='' || strlen($musicId)>90 || $requestedChurch==='' || strlen($requestedChurch)>90) {
    out(['data'=>null,'error'=>['message'=>'Música ou igreja inválida']],400);
}
if(!in_array($role,['master','admin','pastor','lider'],true)) {
    out(['data'=>null,'error'=>['message'=>'Somente pastor, administrador ou líder autorizado pode editar música']],403);
}
if($role!=='master' && ($ownChurch==='' || !hash_equals($ownChurch,$requestedChurch))) {
    out(['data'=>null,'error'=>['message'=>'Você só pode editar o repertório da sua igreja']],403);
}
try{
    if($role==='lider'){
        if($actorId==='')out(['data'=>null,'error'=>['message'=>'Identidade do líder indisponível']],403);
        $perm=db()->prepare('SELECT 1 FROM departamentos WHERE BINARY igreja_id=BINARY ? AND BINARY lider_id=BINARY ? LIMIT 1');
        $perm->execute([$requestedChurch,$actorId]);
        if(!$perm->fetchColumn()){
            out(['data'=>null,'error'=>['message'=>'É preciso estar vinculado como líder de um departamento desta igreja']],403);
        }
    }
    $q=db()->prepare('SELECT id,igreja_id FROM musicas WHERE BINARY id=BINARY ? AND BINARY igreja_id=BINARY ? LIMIT 1');
    $q->execute([$musicId,$requestedChurch]);
    if(!$q->fetch(PDO::FETCH_ASSOC)){
        out(['data'=>null,'error'=>['message'=>'Música não encontrada nesta igreja']],404);
    }
    $required=['titulo'];
    $editable=['titulo','artista','tom','link_spotify','link_youtube','link_cifra','letra','cifra'];
    $limits=['titulo'=>220,'artista'=>220,'tom'=>12,'link_spotify'=>1500,'link_youtube'=>1500,'link_cifra'=>1500,'letra'=>60000,'cifra'=>60000];
    $updates=[];
    foreach($editable as $field){
        if(!array_key_exists($field,$body))continue;
        if(!is_string($body[$field]) && $body[$field]!==null) {
            out(['data'=>null,'error'=>['message'=>'Campo inválido: '.$field]],400);
        }
        $value=trim((string)($body[$field]??''));
        if(strlen($value)>$limits[$field]){
            out(['data'=>null,'error'=>['message'=>'Campo muito longo: '.$field]],400);
        }
        if($field==='titulo' && $value===''){
            out(['data'=>null,'error'=>['message'=>'Informe o título da música']],400);
        }
        if(str_starts_with($field,'link_') && $value!=='' && (!filter_var($value,FILTER_VALIDATE_URL) || !in_array(strtolower((string)parse_url($value,PHP_URL_SCHEME)),['http','https'],true))) {
            out(['data'=>null,'error'=>['message'=>'O link precisa iniciar com https:// ou http://']],400);
        }
        if($field==='tom' && $value!=='' && !preg_match('/^[A-G](?:#|b)?m?$/D',$value)){
            out(['data'=>null,'error'=>['message'=>'Tom musical inválido']],400);
        }
        $updates[$field]=$value==='' && $field!=='titulo'?null:$value;
    }
    if(!array_key_exists('titulo',$updates)){
        out(['data'=>null,'error'=>['message'=>'Título obrigatório']],400);
    }
    if(!$updates){
        out(['data'=>null,'error'=>['message'=>'Nenhuma alteração enviada']],400);
    }
    // Identificadores SQL são constantes de whitelist; valores sempre preparados.
    $set=implode(', ',array_map(static fn($key)=>"`$key`=?",array_keys($updates)));
    $sql='UPDATE musicas SET '.$set.' WHERE BINARY id=BINARY ? AND BINARY igreja_id=BINARY ?';
    $q=db()->prepare($sql);
    $q->execute([...array_values($updates),$musicId,$requestedChurch]);
    $q=db()->prepare('SELECT id,igreja_id,titulo,artista,tom,link_spotify,link_youtube,link_cifra,letra,cifra FROM musicas WHERE BINARY id=BINARY ? AND BINARY igreja_id=BINARY ? LIMIT 1');
    $q->execute([$musicId,$requestedChurch]);
    $changed=$q->fetch(PDO::FETCH_ASSOC);
    try{audit($actorId,'music_edit','musicas',['music_id'=>$musicId,'igreja_id'=>$requestedChurch,'role'=>$role],'info');}catch(Throwable $ignored){}
    out(['data'=>['music'=>$changed,'updated'=>true],'error'=>null]);
}catch(Throwable $e){
    error_log('[Music Edit v1496] '.get_class($e).': '.$e->getMessage());
    out(['data'=>null,'error'=>['message'=>'Não foi possível salvar a edição; verifique as permissões e tente novamente']],500);
}
