<?php
declare(strict_types=1);
require_once __DIR__.'/bootstrap.php';

$u=require_auth();
$uid=(string)($u['id']??'');
if($uid==='') out(['data'=>null,'error'=>['message'=>'Usuário inválido.']],401);

$items=[];

try{
    if(table_exists('escala_itens')&&table_exists('escalas')){
        $sql="SELECT
                ei.id,
                ei.escala_id,
                ei.funcao,
                ei.status_confirmacao,
                ei.created_at,
                e.data,
                e.titulo,
                e.status AS escala_status,
                d.nome AS departamento
              FROM escala_itens ei
              JOIN escalas e ON BINARY e.id=BINARY ei.escala_id
              LEFT JOIN departamentos d ON BINARY d.id=BINARY e.departamento_id
              WHERE BINARY ei.voluntario_id=BINARY ?
                AND COALESCE(ei.status_confirmacao,'pendente')='pendente'
                AND (e.data IS NULL OR e.data>=CURDATE())
                AND COALESCE(e.status,'') NOT IN ('cancelada','cancelado','excluida','excluido')
              ORDER BY e.data ASC, ei.created_at ASC
              LIMIT 100";
        $q=db()->prepare($sql);
        $q->execute([$uid]);
        foreach($q->fetchAll(PDO::FETCH_ASSOC)?:[] as$r){
            $items[]=[
                'id'=>'escala:'.(string)$r['id'],
                'type'=>'escala',
                'item_id'=>(string)$r['id'],
                'escala_id'=>(string)$r['escala_id'],
                'title'=>'Você foi escalado! 🙌',
                'message'=>trim(((string)($r['departamento']??'')) .
                    (((string)($r['departamento']??''))!==''?' · ':'') .
                    ((string)($r['funcao']??'')) .
                    (((string)($r['data']??''))!==''?' · '.date('d/m/Y',strtotime((string)$r['data'])):'')),
                'url'=>'/minha-escala/'.rawurlencode((string)$r['escala_id']),
                'created_at'=>$r['created_at']??null,
            ];
        }
    }

    if(table_exists('trocas')){
        $cols=[];
        try{
            $c=db()->query("SHOW COLUMNS FROM trocas")->fetchAll(PDO::FETCH_COLUMN)?:[];
            $cols=array_map('strval',$c);
        }catch(Throwable$e){}
        if(in_array('substituto_id',$cols,true)){
            $q=db()->prepare("SELECT id,escala_item_id,status,motivo,created_at
                              FROM trocas
                              WHERE BINARY substituto_id=BINARY ?
                                AND COALESCE(status,'pendente')='pendente'
                              ORDER BY created_at ASC LIMIT 50");
            $q->execute([$uid]);
            foreach($q->fetchAll(PDO::FETCH_ASSOC)?:[] as$r){
                $items[]=[
                    'id'=>'troca:'.(string)$r['id'],
                    'type'=>'troca',
                    'title'=>'Solicitação de troca',
                    'message'=>trim((string)($r['motivo']??'Você possui uma troca aguardando resposta.')),
                    'url'=>'/trocas',
                    'created_at'=>$r['created_at']??null,
                ];
            }
        }
    }

    usort($items,fn($a,$b)=>strcmp((string)($a['created_at']??''),(string)($b['created_at']??'')));
    out([
        'data'=>[
            'count'=>count($items),
            'items'=>$items,
            'checked_at'=>date(DATE_ATOM),
        ],
        'error'=>null
    ]);
}catch(Throwable$e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
