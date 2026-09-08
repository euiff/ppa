from pathlib import Path
import re, sys

root=Path(sys.argv[1])

# 1) Restore the proven v1.4.12 quiz state after successful send (etapa=1).
# Keep ONLY the one-question message change. This avoids using etapa=5 as a transport marker.
p=root/'api/automation_v130.php'
s=p.read_text()
old="['quiz_id'=>$id,'escala_id'=>$esc,'escala_item_id'=>$r['item_id'],'voluntario_id'=>$vol,'checkin_at'=>$r['checkin_at'],'quiz_mode'=>'single_v1413']"
new="['quiz_id'=>$id,'escala_id'=>$esc,'escala_item_id'=>$r['item_id'],'voluntario_id'=>$vol,'checkin_at'=>$r['checkin_at'],'quiz_mode'=>'single_v1414']"
if old not in s: raise SystemExit('automation meta anchor not found')
s=s.replace(old,new,1)
old2="UPDATE quiz_pos_culto SET quiz_enviado=1,etapa=5,updated_at=NOW() WHERE id=? AND respondido=0"
new2="UPDATE quiz_pos_culto SET quiz_enviado=1,etapa=1,updated_at=NOW() WHERE id=? AND respondido=0"
if old2 not in s: raise SystemExit('automation etapa=5 anchor not found')
s=s.replace(old2,new2,1)
p.write_text(s)

# 2) The reply router recognizes new one-question quizzes by the successful send log marker.
# This lets us keep etapa=1 exactly like the old working dispatcher and still preserve old
# multi-step quizzes that were already pending before this update.
p=root/'api/quiz_router_v131.php'
s=p.read_text()
anchor="""function v131_handle_active_quiz(array $quiz, string $text): bool {
"""
if anchor not in s: raise SystemExit('quiz handler anchor not found')
helper=r'''function v1414_quiz_is_single(array $quiz): bool {
    if((int)($quiz['etapa']??0)===5)return true; // pending rows created by v1.4.13
    $id=(string)($quiz['id']??'');
    if($id==='')return false;
    try{
        $q=db()->prepare("SELECT id FROM notification_logs WHERE tipo='whatsapp_post_quiz' AND status='enviado' AND meta_data LIKE ? AND (meta_data LIKE '%single_v1413%' OR meta_data LIKE '%single_v1414%') ORDER BY created_at DESC LIMIT 1");
        $q->execute(['%'.$id.'%']);
        return (bool)$q->fetchColumn();
    }catch(Throwable $e){return false;}
}

'''
s=s.replace(anchor,helper+anchor,1)
old_branch="""    // v1.4.13: novo quiz de uma única pergunta. A nota e o comentário opcional
    // são enviados na mesma resposta. Etapa 5 diferencia mensagens novas das
    // conversas antigas que ainda estavam nas etapas 1 a 3 durante a atualização.
    if($etapa===5){
"""
new_branch="""    // v1.4.14: o disparo volta a usar a etapa 1, exatamente como o fluxo que já
    // funcionava. O modo de uma pergunta é identificado pelo log do envio, sem
    // alterar a regra/horário do CRON nem confundir quizzes antigos em andamento.
    if(v1414_quiz_is_single($quiz)){
"""
if old_branch not in s: raise SystemExit('single quiz branch anchor not found')
s=s.replace(old_branch,new_branch,1)
p.write_text(s)

# 3) Pending-menu question must also recognize etapa=1 single quizzes by marker.
p=root/'api/pending_router_v1311.php'
s=p.read_text()
old="if($step===5)return $head."
new="if($step===5||(function_exists('v1414_quiz_is_single')&&v1414_quiz_is_single($quiz)))return $head."
if old not in s: raise SystemExit('pending question stage5 anchor not found')
s=s.replace(old,new,1)
p.write_text(s)

# 4) Cache bust. Frontend stays single-question as in v1.4.13.
p=root/'sistema.html'
s=p.read_text()
s=re.sub(r'/assets/index-C6Ng0a8i\.js\?v=[^\"\']+', '/assets/index-C6Ng0a8i.js?v=1.4.14', s)
p.write_text(s)

p=root/'sw.js'
s=p.read_text()
s=re.sub(r'url:\"sistema\.html\",revision:\"[^\"]*\"', 'url:\"sistema.html\",revision:\"v1414-quiz-dispatch\"', s)
if 'quiz-dispatch-cache-bust-v1.4.14' not in s:
    s += '\n/* quiz-dispatch-cache-bust-v1.4.14 */\n'
p.write_text(s)

(root/'registerSW.js').write_text("if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const r=await navigator.serviceWorker.register('/sw.js?v=1.4.14',{scope:'/',updateViaCache:'none'});await r.update()}catch(e){console.warn('[SW v1.4.14]',e)}})}")
