<?php
declare(strict_types=1);

require __DIR__.'/bootstrap.php';
require_once __DIR__.'/whatsapp_transport_v1424.php';

$caller=require_auth();
$ctx=user_context();
if((string)($ctx['role']??'')!=='master'){
    out(['data'=>null,'error'=>['message'=>'Somente o MASTER pode consultar os grupos do WhatsApp oficial.']],403);
}

function mwg1475_http_get(string $url,array $headers): array {
    $ch=curl_init($url);
    curl_setopt_array($ch,[
        CURLOPT_RETURNTRANSFER=>true,
        CURLOPT_TIMEOUT=>30,
        CURLOPT_CONNECTTIMEOUT=>10,
        CURLOPT_HTTPHEADER=>$headers,
        CURLOPT_FOLLOWLOCATION=>true,
    ]);
    $body=curl_exec($ch);
    $err=curl_error($ch);
    $status=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);
    curl_close($ch);
    $json=json_decode((string)$body,true);
    return [
        'ok'=>$status>=200&&$status<300,
        'status'=>$status,
        'body'=>$json??$body,
        'raw'=>(string)$body,
        'error'=>$err?:null,
    ];
}

function mwg1475_collect($node,array &$out): void {
    if(!is_array($node))return;
    $jid='';
    foreach(['id','jid','remoteJid','groupJid'] as $k){
        if(isset($node[$k])&&is_scalar($node[$k])&&str_contains((string)$node[$k],'@g.us')){
            $jid=trim((string)$node[$k]);
            break;
        }
    }
    if($jid!==''){
        $name='';
        foreach(['subject','name','pushName','title'] as $k){
            if(isset($node[$k])&&is_scalar($node[$k])&&trim((string)$node[$k])!==''){
                $name=trim((string)$node[$k]);
                break;
            }
        }
        $participants=null;
        foreach(['participants','participantsCount','size'] as $k){
            if(isset($node[$k])){
                $v=$node[$k];
                $participants=is_array($v)?count($v):(is_numeric($v)?(int)$v:null);
                if($participants!==null)break;
            }
        }
        $out[$jid]=[
            'jid'=>$jid,
            'name'=>$name!==''?$name:$jid,
            'participants'=>$participants,
        ];
    }
    foreach($node as $v)if(is_array($v))mwg1475_collect($v,$out);
}

function mwg1475_list_groups(): array {
    $base=rtrim(v1424_cfg('evolution_url',null),'/');
    $key=v1424_cfg('evolution_api_key',null);
    $instance=v1424_cfg('evolution_instance',null);
    if($base===''||$key===''||$instance===''){
        return ['ok'=>false,'groups'=>[],'error'=>'O WhatsApp oficial/Evolution API ainda não está configurado no Config. Global do MASTER.'];
    }

    $headers=['apikey: '.$key,'Accept: application/json'];
    $urls=[
        $base.'/group/fetchAllGroups/'.rawurlencode($instance).'?getParticipants=false',
        $base.'/group/fetchAllGroups/'.rawurlencode($instance),
    ];
    $last=null;
    foreach($urls as $url){
        $res=mwg1475_http_get($url,$headers);
        $last=$res;
        if(!empty($res['ok'])){
            $groups=[];
            mwg1475_collect($res['body']??null,$groups);
            $list=array_values($groups);
            usort($list,fn($a,$b)=>strnatcasecmp((string)$a['name'],(string)$b['name']));
            return [
                'ok'=>true,
                'groups'=>$list,
                'instance'=>$instance,
                'count'=>count($list),
                'status'=>$res['status']??200,
            ];
        }
    }
    return [
        'ok'=>false,
        'groups'=>[],
        'instance'=>$instance,
        'status'=>(int)($last['status']??0),
        'error'=>'Não foi possível consultar os grupos do WhatsApp oficial na Evolution API.',
        'details'=>$last['error']??null,
    ];
}

try{
    $data=mwg1475_list_groups();
    if(empty($data['ok'])){
        out(['data'=>null,'error'=>['message'=>$data['error']??'Falha ao carregar os grupos.','details'=>$data['details']??null]],502);
    }
    try{
        audit((string)($caller['id']??''),'master_whatsapp_groups_refresh','evolution_api',[
            'instance'=>$data['instance']??null,
            'groups_count'=>$data['count']??0,
        ],'info');
    }catch(Throwable $e){}
    out(['data'=>[
        'groups'=>$data['groups']??[],
        'instance'=>$data['instance']??'',
        'count'=>$data['count']??0,
        'refreshed_at'=>date('Y-m-d H:i:s'),
    ],'error'=>null]);
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
