from pathlib import Path
import shutil, sys

cur=Path(sys.argv[1])
stable=Path(sys.argv[2])

for rel in ['api/automation_v130.php','api/quiz_router_v131.php','api/confirmation_router_v1311.php','api/pending_router_v1311.php']:
    shutil.copy2(stable/rel,cur/rel)

p=cur/'api/automation_v130.php'
s=p.read_text()
a=s.index('function v130_send_quiz(')
b=s.index('function v130_due_quizzes()',a)
fn=r'''function v130_send_quiz(string $esc,string $vol):bool{
    $q=db()->prepare("SELECT p.nome,p.whatsapp,p.igreja_id,e.data,c.nome culto_nome,c.horario,d.nome dept,ei.id item_id,ei.funcao,ei.status_confirmacao,ei.checkin_at FROM profiles p JOIN escalas e ON e.id=? JOIN escala_itens ei ON ei.escala_id=e.id AND ei.voluntario_id=p.id LEFT JOIN cultos c ON c.id=e.culto_id LEFT JOIN departamentos d ON d.id=e.departamento_id WHERE p.id=? LIMIT 1");
    $q->execute([$esc,$vol]);$r=$q->fetch();
    if(!$r||!$r['whatsapp']||$r['status_confirmacao']==='recusado')return false;
    $s=db()->prepare('SELECT * FROM quiz_pos_culto WHERE escala_id=? AND voluntario_id=? LIMIT 1');$s->execute([$esc,$vol]);$z=$s->fetch();
    if($z&&(!empty($z['quiz_enviado'])||!empty($z['respondido'])||!empty($z['respondido_em_app'])))return false;
    if($z&&(int)$z['etapa']===0&&strtotime((string)$z['updated_at'])>time()-300)return false;
    $id=$z['id']??uuid4();
    if(!$z){try{db()->prepare('INSERT INTO quiz_pos_culto(id,escala_id,voluntario_id,etapa,quiz_enviado,respondido,respondido_em_app,created_at,updated_at) VALUES(?,?,?,0,0,0,0,NOW(),NOW())')->execute([$id,$esc,$vol]);}catch(Throwable$e){return false;}}
    $date=date('d/m/Y',strtotime($r['data']));$hora=$r['horario']?substr($r['horario'],0,5):'';
    $m="🙏 *Olá, {$r['nome']}!*\n\nQueremos ouvir você sobre este culto.\n\n📋 *".($r['culto_nome']?:'Culto')."*\n📅 {$date}".($hora?" às {$hora}":'')."\n⛪ ".($r['dept']?:'Ministério')." — {$r['funcao']}\n\n⭐ *Como você avalia sua experiência neste culto/serviço?*\n\n*1* - 😞 Péssimo\n*2* - 😕 Ruim\n*3* - 😐 Normal\n*4* - 😊 Bom\n*5* - 🤩 Ótimo\n\n💬 *Se quiser, deixe um comentário ou sugestão na mesma resposta.*\n\nEx.: *5* ou *5 - Gostei muito do culto.*\n\n_Responda começando com uma nota de 1 a 5._";
    $res=send_logged_whatsapp('whatsapp_post_quiz',$r['whatsapp'],$m,$r['igreja_id'],['quiz_id'=>$id,'escala_id'=>$esc,'escala_item_id'=>$r['item_id'],'voluntario_id'=>$vol,'checkin_at'=>$r['checkin_at']]);
    if(!empty($res['ok'])){db()->prepare('UPDATE quiz_pos_culto SET quiz_enviado=1,etapa=2,updated_at=NOW() WHERE id=? AND respondido=0')->execute([$id]);return true;}
    db()->prepare('UPDATE quiz_pos_culto SET quiz_enviado=0,etapa=0,updated_at=NOW() WHERE id=?')->execute([$id]);return false;
}
'''
s=s[:a]+fn+s[b:]
p.write_text(s)

p=cur/'api/quiz_router_v131.php'
s=p.read_text()
old="""    $normalizedText = function_exists('mb_strtolower') ? mb_strtolower(trim($text), 'UTF-8') : strtolower(trim($text));
    return [
        'text' => $normalizedText,
"""
new="""    $rawText = trim($text);
    $normalizedText = function_exists('mb_strtolower') ? mb_strtolower($rawText, 'UTF-8') : strtolower($rawText);
    return [
        'text' => $normalizedText,
        'text_raw' => $rawText,
"""
if old not in s: raise SystemExit('quiz parse anchor not found')
s=s.replace(old,new,1)
start=s.index('    if ($etapa === 2) {')
end=s.index('    // Terceira pergunta',start)
block=r'''    if ($etapa === 2 || $etapa === 5) {
        $raw = trim($text);
        if (!preg_match('/^([1-5])(?!\\d)(?:\\s*[-–—:.,]?\\s*(.*))?$/us', $raw, $m)) {
            v131_quiz_reply($quiz, "🤔 Responda começando com uma nota de *1 a 5*.\n\nSe quiser, escreva o comentário na mesma mensagem.\nEx.: *5 - Gostei muito do culto.*", 'quiz_invalid_rating');
            return true;
        }
        $nota=(int)$m[1];
        $suggestion=trim((string)($m[2]??''));
        $normalizedSuggestion=function_exists('mb_strtolower')?mb_strtolower($suggestion,'UTF-8'):strtolower($suggestion);
        if(in_array($normalizedSuggestion,['pular','sem sugestão','sem sugestao','nada','não','nao'],true))$suggestion='';
        if($suggestion!=='')$suggestion=function_exists('mb_substr')?mb_substr($suggestion,0,1000,'UTF-8'):substr($suggestion,0,1000); else $suggestion=null;
        $labels=[1=>'Péssimo',2=>'Ruim',3=>'Normal',4=>'Bom',5=>'Ótimo'];
        $label=$labels[$nota];
        db()->prepare('UPDATE quiz_pos_culto SET participou=1,avaliacao=?,sugestao=?,feedback=?,etapa=4,respondido=1,updated_at=NOW() WHERE id=?')->execute([$label,$suggestion,$suggestion,$quiz['id']]);
        v131_upsert_avaliacao($quiz,$nota,$suggestion);
        $extra=$suggestion?"\nSeu comentário/sugestão também foi registrado.":'';
        v131_quiz_reply($quiz,"🙏 *Obrigado pela sua avaliação!*\n\nSua resposta foi registrada com sucesso.".$extra."\n\nQue Deus abençoe você por servir. ❤️",'quiz_single_completed');
        return true;
    }

'''
s=s[:start]+block+s[end:]
s=s.replace("$handled = v131_handle_active_quiz($quiz, (string)$msg['text']);","$handled = v131_handle_active_quiz($quiz, (string)($msg['text_raw'] ?? $msg['text']));",1)
p.write_text(s)

mig=cur/'database/migrations/20260908_1415_whatsapp_recovery.sql'
mig.write_text("""UPDATE api_config SET valor='',updated_at=NOW() WHERE igreja_id IS NULL AND chave IN ('whatsapp_webhook_sync_signature','whatsapp_webhook_sync_last_result','whatsapp_webhook_sync_last_at','whatsapp_webhook_sync_last_error');
UPDATE whatsapp_send_jobs j SET j.status='pending',j.attempts=0,j.scheduled_at=NOW(),j.started_at=NULL,j.finished_at=NULL,j.error=NULL,j.updated_at=NOW() WHERE j.job_type='escala_notification' AND j.status IN ('failed','running') AND j.updated_at>=DATE_SUB(NOW(),INTERVAL 6 HOUR) AND NOT EXISTS (SELECT 1 FROM notification_logs n WHERE n.tipo='whatsapp' AND n.status='enviado' AND n.meta_data LIKE CONCAT('%\\\"escala_item_id\\\":\\\"',j.escala_item_id,'\\\"%'));
UPDATE quiz_pos_culto SET etapa=2,updated_at=NOW() WHERE respondido=0 AND etapa=5;
UPDATE quiz_pos_culto q SET q.etapa=2,q.updated_at=NOW() WHERE q.respondido=0 AND q.etapa=1 AND EXISTS (SELECT 1 FROM notification_logs n WHERE n.tipo='whatsapp_post_quiz' AND n.status='enviado' AND n.meta_data LIKE CONCAT('%',q.id,'%') AND (n.meta_data LIKE '%single_v1413%' OR n.meta_data LIKE '%single_v1414%'));
""")
