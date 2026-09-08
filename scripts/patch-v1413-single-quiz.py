from pathlib import Path
import re, sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'pkg')

# 1) WhatsApp scheduler: send one single-question post-cult evaluation.
p=root/'api/automation_v130.php'
s=p.read_text()
start=s.find('function v130_send_quiz(')
end=s.find('function v130_due_quizzes()', start)
if start<0 or end<0:
    raise SystemExit('v130_send_quiz anchors not found')
new_func=r'''function v130_send_quiz(string $esc,string $vol):bool{
    $q=db()->prepare("SELECT p.nome,p.whatsapp,p.igreja_id,e.data,c.nome culto_nome,c.horario,d.nome dept,ei.id item_id,ei.funcao,ei.status_confirmacao,ei.checkin_at FROM profiles p JOIN escalas e ON e.id=? JOIN escala_itens ei ON ei.escala_id=e.id AND ei.voluntario_id=p.id LEFT JOIN cultos c ON c.id=e.culto_id LEFT JOIN departamentos d ON d.id=e.departamento_id WHERE p.id=? LIMIT 1");
    $q->execute([$esc,$vol]);$r=$q->fetch();
    if(!$r||!$r['whatsapp']||$r['status_confirmacao']==='recusado')return false;
    $s=db()->prepare('SELECT * FROM quiz_pos_culto WHERE escala_id=? AND voluntario_id=? LIMIT 1');$s->execute([$esc,$vol]);$z=$s->fetch();
    if($z&&(!empty($z['quiz_enviado'])||!empty($z['respondido'])||!empty($z['respondido_em_app'])))return false;
    if($z&&(int)$z['etapa']===0&&strtotime((string)$z['updated_at'])>time()-300)return false;
    $id=$z['id']??uuid4();
    if(!$z){try{db()->prepare('INSERT INTO quiz_pos_culto(id,escala_id,voluntario_id,etapa,quiz_enviado,respondido,respondido_em_app,created_at,updated_at) VALUES(?,?,?,0,0,0,0,NOW(),NOW())')->execute([$id,$esc,$vol]);}catch(Throwable$e){return false;}}
    $date=date('d/m/Y',strtotime($r['data']));$hora=$r['horario']?substr($r['horario'],0,5):'';
    $m="🙏 *Olá, {$r['nome']}!*\n\nQueremos ouvir você sobre este culto.\n\n📋 *".($r['culto_nome']?:'Culto')."*\n📅 {$date}".($hora?" às {$hora}":'')."\n⛪ ".($r['dept']?:'Ministério')." — {$r['funcao']}\n\n⭐ *Como você avalia sua experiência neste culto/serviço?*\n\n*1* - 😞 Péssimo\n*2* - 😕 Ruim\n*3* - 😐 Normal\n*4* - 😊 Bom\n*5* - 🤩 Ótimo\n\n💬 *Se quiser, na mesma resposta deixe um comentário ou sugestão para o culto.*\n\nExemplos:\n*5*\nou\n*5 - Foi muito bom. Sugiro começar o ensaio mais cedo.*\n\n_Responda começando com uma nota de 1 a 5._";
    $res=send_logged_whatsapp('whatsapp_post_quiz',$r['whatsapp'],$m,$r['igreja_id'],['quiz_id'=>$id,'escala_id'=>$esc,'escala_item_id'=>$r['item_id'],'voluntario_id'=>$vol,'checkin_at'=>$r['checkin_at'],'quiz_mode'=>'single_v1413']);
    if(!empty($res['ok'])){db()->prepare('UPDATE quiz_pos_culto SET quiz_enviado=1,etapa=5,updated_at=NOW() WHERE id=? AND respondido=0')->execute([$id]);return true;}
    db()->prepare('UPDATE quiz_pos_culto SET quiz_enviado=0,etapa=0,updated_at=NOW() WHERE id=?')->execute([$id]);return false;
}
'''
s=s[:start]+new_func+s[end:]
p.write_text(s)

# 2) Quiz router: preserve raw comment text and add a new single-response stage 5.
p=root/'api/quiz_router_v131.php'
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
if old not in s: raise SystemExit('quiz raw text anchor not found')
s=s.replace(old,new,1)
start=s.find('function v131_handle_active_quiz(')
end=s.find('function v131_quiz_router_handle()',start)
if start<0 or end<0: raise SystemExit('quiz handler anchors not found')
new_handler=r'''function v1413_quiz_normalize(string $text): string {
    $text=trim($text);
    return function_exists('mb_strtolower')?mb_strtolower($text,'UTF-8'):strtolower($text);
}

function v1413_parse_single_quiz_answer(string $text): ?array {
    $raw=trim($text);
    if(!preg_match('/^([1-5])(?!\\d)(?:\\s*[-–—:.,]?\\s*(.*))?$/us',$raw,$m))return null;
    $nota=(int)$m[1];
    $comment=trim((string)($m[2]??''));
    $skip=['pular','sem sugestão','sem sugestao','nada','não','nao'];
    if($comment!==''&&in_array(v1413_quiz_normalize($comment),$skip,true))$comment='';
    if($comment!=='')$comment=function_exists('mb_substr')?mb_substr($comment,0,1000,'UTF-8'):substr($comment,0,1000);
    return [$nota,$comment!==''?$comment:null];
}

function v131_handle_active_quiz(array $quiz, string $text): bool {
    $etapa=(int)($quiz['etapa']??0);
    $raw=trim($text);
    $normalized=v1413_quiz_normalize($raw);

    // v1.4.13: novo quiz de uma única pergunta. A nota e o comentário opcional
    // são enviados na mesma resposta. Etapa 5 diferencia mensagens novas das
    // conversas antigas que ainda estavam nas etapas 1 a 3 durante a atualização.
    if($etapa===5){
        $parsed=v1413_parse_single_quiz_answer($raw);
        if(!$parsed){
            v131_quiz_reply($quiz,"🤔 Para responder, comece com uma nota de *1 a 5*.\n\nSe quiser comentar, escreva na mesma mensagem.\nEx.: *5 - Gostei muito do culto.*",'quiz_single_invalid');
            return true;
        }
        [$nota,$suggestion]=$parsed;
        $labels=[1=>'Péssimo',2=>'Ruim',3=>'Normal',4=>'Bom',5=>'Ótimo'];
        $label=$labels[$nota];
        db()->prepare('UPDATE quiz_pos_culto SET participou=1,avaliacao=?,sugestao=?,feedback=?,etapa=4,respondido=1,updated_at=NOW() WHERE id=?')
            ->execute([$label,$suggestion,$suggestion,$quiz['id']]);
        v131_upsert_avaliacao($quiz,$nota,$suggestion);
        $extra=$suggestion?"\nSeu comentário/sugestão também foi registrado.":'';
        v131_quiz_reply($quiz,"🙏 *Obrigado pela sua avaliação!*\n\nSua resposta foi registrada com sucesso.".$extra."\n\nQue Deus abençoe você por servir. ❤️",'quiz_single_completed');
        return true;
    }

    // Compatibilidade: quem já recebeu o fluxo antigo antes da atualização
    // consegue terminá-lo normalmente.
    $yes=in_array($normalized,['1','sim','s','yes'],true);
    $no=in_array($normalized,['2','não','nao','n','no'],true);

    if($etapa===1){
        if($yes){
            db()->prepare('UPDATE quiz_pos_culto SET participou=1,etapa=2,updated_at=NOW() WHERE id=?')->execute([$quiz['id']]);
            v131_quiz_reply($quiz,"👍 Que bom! Sua presença foi registrada.\n\n*Como foi sua experiência servindo?*\n\n*1* - 😞 Péssimo\n*2* - 😕 Ruim\n*3* - 😐 Normal\n*4* - 😊 Bom\n*5* - 🤩 Ótimo\n\n_Responda somente de 1 a 5_",'quiz_step2');
            return true;
        }
        if($no){v131_complete_no($quiz);return true;}
        v131_quiz_reply($quiz,"🤔 Para concluir este quiz antigo, responda somente:\n*1* - ✅ Sim, estive\n*2* - ❌ Não estive",'quiz_invalid_presence');
        return true;
    }

    if($etapa===2){
        $map=['1'=>['Péssimo',1],'2'=>['Ruim',2],'3'=>['Normal',3],'4'=>['Bom',4],'5'=>['Ótimo',5],'péssimo'=>['Péssimo',1],'pessimo'=>['Péssimo',1],'ruim'=>['Ruim',2],'normal'=>['Normal',3],'bom'=>['Bom',4],'ótimo'=>['Ótimo',5],'otimo'=>['Ótimo',5]];
        if(!isset($map[$normalized])){v131_quiz_reply($quiz,"🤔 Responda somente de *1 a 5* para avaliar sua experiência.",'quiz_invalid_rating');return true;}
        [$label,$nota]=$map[$normalized];
        db()->prepare('UPDATE quiz_pos_culto SET participou=1,avaliacao=?,etapa=3,respondido=0,updated_at=NOW() WHERE id=?')->execute([$label,$quiz['id']]);
        v131_upsert_avaliacao($quiz,$nota,null);
        v131_quiz_reply($quiz,"💬 *Última pergunta deste quiz antigo*\n\nTem alguma sugestão ou comentário?\n\n✍️ Escreva sua resposta.\nSe não quiser comentar, responda *PULAR*.",'quiz_step3');
        return true;
    }

    if($etapa===3){
        $skip=in_array($normalized,['pular','sem sugestão','sem sugestao','nada','não','nao'],true);
        $suggestion=$skip?null:$raw;
        if($suggestion!==null)$suggestion=function_exists('mb_substr')?mb_substr($suggestion,0,1000,'UTF-8'):substr($suggestion,0,1000);
        db()->prepare('UPDATE quiz_pos_culto SET sugestao=?,feedback=?,etapa=4,respondido=1,updated_at=NOW() WHERE id=?')->execute([$suggestion,$suggestion,$quiz['id']]);
        if(!empty($quiz['avaliacao'])){$notaMap=['Péssimo'=>1,'Ruim'=>2,'Normal'=>3,'Bom'=>4,'Ótimo'=>5,'Incrível'=>5];v131_upsert_avaliacao($quiz,$notaMap[$quiz['avaliacao']]??3,$suggestion);}
        v131_quiz_reply($quiz,"🙏 *Obrigado pela sua avaliação!*\n\nSua resposta foi registrada com sucesso. ❤️",'quiz_completed_step3');
        return true;
    }
    return false;
}

'''
s=s[:start]+new_handler+s[end:]
s=s.replace("$handled = v131_handle_active_quiz($quiz, (string)$msg['text']);","$handled = v131_handle_active_quiz($quiz, (string)($msg['text_raw'] ?? $msg['text']));",1)
p.write_text(s)

# 3) Confirmation parser: expose raw text to the pending router so comments keep capitalization.
p=root/'api/confirmation_router_v1311.php'
s=p.read_text()
old="""    return [
        'text' => $normalized,
        'from_me' => $fromMe === true,
"""
new="""    return [
        'text' => $normalized,
        'text_raw' => trim($text),
        'from_me' => $fromMe === true,
"""
if old not in s: raise SystemExit('confirmation raw text anchor not found')
s=s.replace(old,new,1)
p.write_text(s)

# 4) Pending menu: present the new stage-5 quiz as one question and pass raw text to it.
p=root/'api/pending_router_v1311.php'
s=p.read_text()
s=s.replace("$step=(int)($r['etapa']??1); $label='📝 Quiz da escala '.$date.($time!==''?' às '.$time:'').' — '.$culto.($step>1?' (etapa '.$step.')':'');","$step=(int)($r['etapa']??1); $label='📝 Avaliação do culto '.$date.($time!==''?' às '.$time:'').' — '.$culto;",1)
start=s.find('function v1311p_quiz_question(array $quiz): string')
end=s.find('function v1311p_option_still_pending',start)
if start<0 or end<0: raise SystemExit('pending quiz question anchors not found')
new_q=r'''function v1311p_quiz_question(array $quiz): string { $date=!empty($quiz['data'])?date('d/m/Y',strtotime((string)$quiz['data'])):'—'; $time=trim((string)($quiz['horario']??''));$time=$time!==''?substr($time,0,5):''; $head="📝 *Avaliação do culto*\n📋 ".(($quiz['culto_nome']??'')?:'Culto')."\n📅 {$date}".($time!==''?' às '.$time:'')."\n\n"; $step=(int)($quiz['etapa']??1); if($step===5)return $head."⭐ *Como você avalia sua experiência?*\n\n*1* - 😞 Péssimo\n*2* - 😕 Ruim\n*3* - 😐 Normal\n*4* - 😊 Bom\n*5* - 🤩 Ótimo\n\n💬 Se quiser, deixe comentário ou sugestão *na mesma resposta*.\nEx.: *5 - Gostei muito do culto.*\n\n_Digite MENU para voltar._"; if($step===1)return $head."*Você esteve/serviu nesse culto?*\n\n*1* - ✅ Sim, estive\n*2* - ❌ Não estive\n\n_Digite MENU para voltar._"; if($step===2)return $head."*Como foi sua experiência servindo?*\n\n*1* - 😞 Péssimo\n*2* - 😕 Ruim\n*3* - 😐 Normal\n*4* - 😊 Bom\n*5* - 🤩 Ótimo\n\n_Digite MENU para voltar._"; if($step===3)return $head."Envie sua sugestão/comentário. Se não quiser informar, responda *PULAR*.\n\n_Digite MENU para voltar._"; return $head."Este quiz já não possui resposta pendente."; } 
'''
s=s[:start]+new_q+s[end:]
s=s.replace("||(int)($freshQuiz['etapa']??0)>=4)","||(int)($freshQuiz['etapa']??0)===4)",1)
old="$text=trim((string)($msg['text']??''));if($text==='')return false;"
new="$text=trim((string)($msg['text']??''));$textRaw=trim((string)($msg['text_raw']??$text));if($text==='')return false;"
if old not in s: raise SystemExit('pending text anchor not found')
s=s.replace(old,new,1)
s=s.replace("if($state==='quiz')return v1311p_handle_locked_quiz($session,$profiles,$sender,$text);","if($state==='quiz')return v1311p_handle_locked_quiz($session,$profiles,$sender,$textRaw);",1)
s=s.replace("$handled=v131_handle_active_quiz($quiz,$text);if($handled){v1311p_trace('single_answered'","$handled=v131_handle_active_quiz($quiz,$textRaw);if($handled){v1311p_trace('single_answered'",1)
p.write_text(s)

# 5) In-app checkout quiz: one screen with 1-5 rating + optional comment.
p=root/'assets/index-C6Ng0a8i.js'
s=p.read_text()
start=s.find('PY=()=>')
end=s.find(';var MS=1,TY=',start)
if start<0 or end<0: raise SystemExit('in-app quiz component anchors not found')
new_py='''PY=()=>{const{pendingQuiz:e,setPendingQuiz:t}=Lo(),[n,s]=h.useState(null),[a,i]=h.useState(""),[l,c]=h.useState(!1);if(!e)return null;const d=async()=>{var P;if(!n)return;c(!0);try{const x=((P=ux.find(A=>A.value===n))==null?void 0:P.label)||"Bom",v=n===5?"Ótimo":x,j=a.trim()||null,{data:w,error:S}=await I.from("quiz_pos_culto").select("id, quiz_enviado").eq("escala_id",e.escalaId).eq("voluntario_id",e.voluntarioId).maybeSingle();if(S)throw S;const y={participou:!0,avaliacao:v,feedback:j,sugestao:j,etapa:4,respondido:!0,respondido_em_app:!0},{error:b}=w!=null&&w.id?await I.from("quiz_pos_culto").update(y).eq("id",w.id):await I.from("quiz_pos_culto").insert({escala_id:e.escalaId,voluntario_id:e.voluntarioId,...y,quiz_enviado:!1});if(b)throw b;const{data:N}=await I.from("escalas").select("igreja_id").eq("id",e.escalaId).maybeSingle(),{data:C,error:Q}=await I.from("avaliacoes").select("id").eq("escala_id",e.escalaId).eq("voluntario_id",e.voluntarioId).maybeSingle();if(Q)throw Q;const H={nota:n,comentario:j,igreja_id:(N==null?void 0:N.igreja_id)||null},{error:T}=C!=null&&C.id?await I.from("avaliacoes").update(H).eq("id",C.id):await I.from("avaliacoes").insert({escala_id:e.escalaId,voluntario_id:e.voluntarioId,...H});if(T)throw T;V.success("Obrigado pela sua avaliação! 🙏"),at.success(),t(null)}catch(x){console.error("Error submitting quiz:",x),V.error("Erro ao enviar avaliação. Tente novamente.")}finally{c(!1)}},f=()=>{t(null),at.light()};return r.jsx(uc,{children:r.jsx("div",{className:"fixed inset-0 z-[200] flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm",children:r.jsx(Nt.div,{initial:{opacity:0,scale:.9,y:20},animate:{opacity:1,scale:1,y:0},exit:{opacity:0,scale:.9,y:20},className:"w-full max-w-md",children:r.jsxs(Te,{className:"shadow-2xl border-primary/20",children:[r.jsxs(ot,{className:"flex flex-row items-center justify-between space-y-0 pb-2",children:[r.jsxs(lt,{className:"text-xl font-bold flex items-center gap-2",children:[r.jsx(ac,{className:"w-5 h-5 text-primary"}),"Como foi o Culto?"]}),r.jsx(ie,{variant:"ghost",size:"icon",onClick:f,className:"rounded-full",children:r.jsx(ks,{className:"w-5 h-5"})})]}),r.jsxs(Re,{className:"pt-4 space-y-5",children:[r.jsxs("div",{className:"space-y-3",children:[r.jsx("p",{className:"text-center text-sm font-medium",children:"Dê uma nota de 1 a 5 para sua experiência:"}),r.jsx("div",{className:"flex justify-center gap-2",children:ux.map(x=>r.jsxs("button",{onClick:()=>{s(x.value),at.selection()},className:`flex flex-col items-center gap-1 p-2 rounded-xl transition-all ${n===x.value?"bg-primary/10 scale-110 ring-2 ring-primary/30":"hover:bg-secondary"}`,children:[r.jsx("span",{className:"text-3xl",children:x.emoji}),r.jsx("span",{className:"text-[10px] text-muted-foreground",children:x.value})]},x.value))})]}),r.jsxs("div",{className:"space-y-1.5",children:[r.jsx(_e,{className:"text-xs",children:"Comentário / Sugestão (opcional)"}),r.jsx(Oi,{placeholder:"Se quiser, deixe aqui um comentário ou sugestão para o culto...",value:a,onChange:x=>i(x.target.value),className:"min-h-[100px] rounded-xl"})]}),r.jsx(ie,{className:"w-full rounded-xl font-bold",onClick:d,disabled:l||!n,children:l?"Enviando...":"Enviar Avaliação"})]})]})})})})}'''
s=s[:start]+new_py+s[end:]
p.write_text(s)

# 6) Cache bust.
p=root/'sistema.html'
s=p.read_text()
s=re.sub(r'/assets/index-C6Ng0a8i\\.js\\?v=[^\\"\\']+','/assets/index-C6Ng0a8i.js?v=1.4.13',s)
s=re.sub(r'/smart-features\\.js\\?v=[^\\"\\']+','/smart-features.js?v=1413',s)
p.write_text(s)

p=root/'sw.js'
s=p.read_text()
s=re.sub(r'url:\\"sistema\\.html\\",revision:\\"[^\\"]*\\"','url:\\"sistema.html\\",revision:\\"v1413-single-quiz\\"',s)
s=re.sub(r'url:\\"assets/index-C6Ng0a8i\\.js\\",revision:(?:null|\\"[^\\"]*\\")','url:\\"assets/index-C6Ng0a8i.js\\",revision:\\"v1413-single-quiz\\"',s)
if 'single-quiz-cache-bust-v1.4.13' not in s:s+='\n/* single-quiz-cache-bust-v1.4.13 */\n'
p.write_text(s)
(root/'registerSW.js').write_text("if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const r=await navigator.serviceWorker.register('/sw.js?v=1.4.13',{scope:'/',updateViaCache:'none'});await r.update()}catch(e){console.warn('[SW v1.4.13]',e)}})}")
