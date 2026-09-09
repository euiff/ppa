from pathlib import Path
import sys
root=Path(sys.argv[1])
api=root/'api'
helper=api/'whatsapp_scale_message_v1421.php'
helper.write_text(r'''<?php
declare(strict_types=1);
/** Escala de Propósito v1.4.21 — restaura link de confirmação e repertório na notificação inicial. */

function v1421_same_day_repertoire(array $r): array {
    try {
        $esc=(string)($r['escala_id']??'');
        $ig=(string)($r['igreja_id']??'');
        $data=(string)($r['data']??'');
        $culto=(string)($r['culto_id']??'');
        if($esc==='') return [];

        $sql="SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom
              FROM setlists s
              JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id
              JOIN musicas m ON BINARY m.id=BINARY si.musica_id
              WHERE BINARY s.escala_id=BINARY ?
              ORDER BY si.ordem ASC,m.titulo ASC";
        $q=db()->prepare($sql);$q->execute([$esc]);$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];

        if(!$rows && $ig!=='' && $data!=='') {
            if($culto!=='') {
                $sql="SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom
                      FROM setlists s
                      JOIN escalas e2 ON BINARY e2.id=BINARY s.escala_id
                      JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id
                      JOIN musicas m ON BINARY m.id=BINARY si.musica_id
                      WHERE BINARY e2.igreja_id=BINARY ? AND e2.data=? AND BINARY e2.culto_id=BINARY ?
                      ORDER BY s.created_at ASC,si.ordem ASC,m.titulo ASC";
                $q=db()->prepare($sql);$q->execute([$ig,$data,$culto]);
            } else {
                $sql="SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom
                      FROM setlists s
                      JOIN escalas e2 ON BINARY e2.id=BINARY s.escala_id
                      JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id
                      JOIN musicas m ON BINARY m.id=BINARY si.musica_id
                      WHERE BINARY e2.igreja_id=BINARY ? AND e2.data=?
                      ORDER BY s.created_at ASC,si.ordem ASC,m.titulo ASC";
                $q=db()->prepare($sql);$q->execute([$ig,$data]);
            }
            $rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];
        }

        $out=[];$seen=[];
        foreach($rows as $x){
            $id=(string)($x['musica_id']??'');
            $key=$id!==''?$id:mb_strtolower(trim((string)($x['titulo']??'')));
            if($key===''||isset($seen[$key]))continue;
            $seen[$key]=true;$out[]=$x;
            if(count($out)>=30)break;
        }
        return $out;
    } catch(Throwable $e) {
        return [];
    }
}

function v1421_build_scale_message(string $itemId): ?array {
    $sql="SELECT ei.*,p.nome voluntario_nome,p.whatsapp,e.data,e.observacoes,e.antecedencia_minutos,e.ensaio_data,e.ensaio_horario,e.igreja_id,e.culto_id,
                 d.nome departamento_nome,d.antecedencia_minutos dept_antecedencia,c.nome culto_nome,c.horario culto_horario
          FROM escala_itens ei
          JOIN escalas e ON BINARY e.id=BINARY ei.escala_id
          LEFT JOIN profiles p ON BINARY p.id=BINARY ei.voluntario_id
          LEFT JOIN departamentos d ON BINARY d.id=BINARY e.departamento_id
          LEFT JOIN cultos c ON BINARY c.id=BINARY e.culto_id
          WHERE BINARY ei.id=BINARY ? LIMIT 1";
    $st=db()->prepare($sql);$st->execute([$itemId]);$r=$st->fetch(PDO::FETCH_ASSOC);
    if(!$r||empty($r['whatsapp']))return null;

    $token=function_exists('ensure_item_token')?ensure_item_token($itemId):null;
    $date=!empty($r['data'])?date('d/m/Y',strtotime((string)$r['data'])):'—';
    $hora=!empty($r['culto_horario'])?substr((string)$r['culto_horario'],0,5):'';
    $ant=(int)($r['antecedencia_minutos']??$r['dept_antecedencia']??0);

    $m="Olá, ".($r['voluntario_nome']?:'voluntário').".\n\n*Você foi escalado(a):*";
    if(!empty($r['culto_nome']))$m.="\n📋 Culto: *{$r['culto_nome']}*";
    $m.="\n📅 {$date}";
    if($hora!=='')$m.="\n🕐 Horário: {$hora}";
    $m.="\n⛪ ".($r['departamento_nome']?:'Ministério')." — ".($r['funcao']?:'Função');
    if($ant>0)$m.="\n⏰ Chegar {$ant} min antes";
    if(!empty($r['ensaio_data']))$m.="\n🎶 Ensaio: ".date('d/m/Y',strtotime((string)$r['ensaio_data'])).(!empty($r['ensaio_horario'])?' às '.substr((string)$r['ensaio_horario'],0,5):'');
    if(!empty($r['observacoes']))$m.="\n\n📝 ".trim((string)$r['observacoes']);

    $songs=v1421_same_day_repertoire($r);
    if($songs){
        $m.="\n\n🎵 *Repertório do dia:*";
        foreach($songs as $i=>$song){
            $titulo=trim((string)($song['titulo']??''));if($titulo==='')continue;
            $art=trim((string)($song['artista']??''));$tom=trim((string)($song['tom']??''));
            $line="\n".($i+1).". *{$titulo}*";
            if($art!=='')$line.=" — {$art}";
            if($tom!=='')$line.=" (Tom: {$tom})";
            $m.=$line;
        }
    }

    $m.="\n\n*Confirme sua presença:*\n*1* - ✅ Confirmar presença\n*2* - ❌ Não posso participar";
    if($token){
        $base='https://escala.isaacanthony.com.br';
        $m.="\n\n🔗 *Também pode confirmar ou informar que não poderá participar pelo link:*\n{$base}/confirmar/{$token}";
    }
    $m.="\n\n🙏 Obrigado por servir!";
    return ['message'=>$m,'phone'=>$r['whatsapp'],'row'=>$r,'repertoire_count'=>count($songs)];
}

function v1421_process_scale_whatsapp_job(array $job): array {
    $itemId=(string)($job['escala_item_id']??'');
    if($itemId==='')return ['ok'=>false,'error'=>'Item da escala ausente','status'=>0];

    $state=db()->prepare('SELECT status_confirmacao FROM escala_itens WHERE BINARY id=BINARY ?');
    $state->execute([$itemId]);$current=$state->fetchColumn();
    if($current && $current!=='pendente'){
        $res=['ok'=>true,'skipped'=>true,'reason'=>'already_answered','status'=>200];
        db()->prepare("UPDATE whatsapp_send_jobs SET status='done',finished_at=NOW(),updated_at=NOW(),result=? WHERE BINARY id=BINARY ?")
            ->execute([json_encode($res,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),(string)$job['id']]);
        return $res;
    }

    $built=v1421_build_scale_message($itemId);
    if(!$built){$res=['ok'=>false,'error'=>'Voluntário sem WhatsApp ou item inexistente','status'=>0];}
    else{
        $res=send_logged_whatsapp('whatsapp',$built['phone'],$built['message'],$built['row']['igreja_id']?:null,[
            'escala_id'=>$job['escala_id']??$built['row']['escala_id'],
            'escala_item_id'=>$itemId,
            'job_id'=>$job['id']??null,
            'confirmation_link'=>true,
            'repertoire_count'=>$built['repertoire_count']??0,
            'message_version'=>'1.4.21'
        ]);
    }

    if(!empty($res['ok'])){
        db()->prepare('UPDATE escala_itens SET notificado=1,updated_at=NOW() WHERE BINARY id=BINARY ?')->execute([$itemId]);
        db()->prepare("UPDATE whatsapp_send_jobs SET status='done',finished_at=NOW(),updated_at=NOW(),result=? WHERE BINARY id=BINARY ?")
            ->execute([json_encode($res,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),(string)$job['id']]);
    } else {
        db()->prepare("UPDATE whatsapp_send_jobs SET status='failed',attempts=attempts+1,finished_at=NOW(),updated_at=NOW(),error=?,result=? WHERE BINARY id=BINARY ?")
            ->execute([$res['error']??'Falha no envio',json_encode($res,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),(string)$job['id']]);
    }
    return $res;
}
''',encoding='utf-8')

p=api/'automation_v130.php'
s=p.read_text(encoding='utf-8')
req="require_once __DIR__.'/webhook_sync_v1311.php';"
if "whatsapp_scale_message_v1421.php" not in s:
    if req not in s: raise SystemExit('webhook require marker not found')
    s=s.replace(req,req+"\nrequire_once __DIR__.'/whatsapp_scale_message_v1421.php';",1)
old="$r=process_whatsapp_job($j);$n++;"
new="$r=(($j['job_type']??'')==='escala_notification'&&function_exists('v1421_process_scale_whatsapp_job'))?v1421_process_scale_whatsapp_job($j):process_whatsapp_job($j);$n++;"
if old not in s: raise SystemExit('process job marker not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

sw=root/'sw.js'
sw.write_text(sw.read_text(encoding='utf-8')+'\n/* whatsapp-scale-link-repertoire-v1.4.21 */\n',encoding='utf-8')
