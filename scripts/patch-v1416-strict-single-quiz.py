from pathlib import Path
import re, sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'pkg')

# 1) Quiz router: qualquer quiz pendente vira uma unica resposta 1..5 + comentario opcional.
p=root/'api/quiz_router_v131.php'
s=p.read_text()
no_start=s.find('function v131_complete_no(')
handler_start=s.find('function v131_handle_active_quiz(')
router_start=s.find('function v131_quiz_router_handle()', handler_start)
if handler_start<0 or router_start<0:
    raise SystemExit('quiz handler anchors not found')
if no_start>=0 and no_start<handler_start:
    s=s[:no_start]+s[handler_start:]
    handler_start=s.find('function v131_handle_active_quiz(')
    router_start=s.find('function v131_quiz_router_handle()', handler_start)
new_handler=r'''function v1416_parse_single_quiz_answer(string $text): ?array {
    $raw = trim($text);
    if (!preg_match('/^([1-5])(?!\\d)(?:\\s*[-–—:.,]?\\s*(.*))?$/us', $raw, $m)) return null;
    $nota = (int)$m[1];
    $suggestion = trim((string)($m[2] ?? ''));
    $normalized = function_exists('mb_strtolower') ? mb_strtolower($suggestion, 'UTF-8') : strtolower($suggestion);
    if (in_array($normalized, ['pular','sem sugestão','sem sugestao','nada','não','nao'], true)) $suggestion = '';
    if ($suggestion !== '') $suggestion = function_exists('mb_substr') ? mb_substr($suggestion, 0, 1000, 'UTF-8') : substr($suggestion, 0, 1000);
    return [$nota, $suggestion !== '' ? $suggestion : null];
}

function v131_handle_active_quiz(array $quiz, string $text): bool {
    // v1.4.16: TODO quiz pendente usa uma unica resposta.
    // Nao existe pergunta de presenca nem pergunta final separada.
    if (!empty($quiz['respondido']) || (int)($quiz['etapa'] ?? 0) <= 0 || (int)($quiz['etapa'] ?? 0) === 4) return false;

    $parsed = v1416_parse_single_quiz_answer($text);
    if (!$parsed) {
        v131_quiz_reply(
            $quiz,
            "🤔 Responda somente *uma vez*, começando com uma nota de *1 a 5*.\n\nSe quiser, escreva o comentário ou sugestão na mesma mensagem.\n\nEx.: *5*\nou\n*5 - Gostei muito do culto.*",
            'quiz_single_invalid_v1416'
        );
        return true;
    }

    [$nota, $suggestion] = $parsed;
    $labels = [1=>'Péssimo',2=>'Ruim',3=>'Normal',4=>'Bom',5=>'Ótimo'];
    $label = $labels[$nota];

    db()->prepare('UPDATE quiz_pos_culto SET participou=1,avaliacao=?,sugestao=?,feedback=?,etapa=4,respondido=1,updated_at=NOW() WHERE id=?')
        ->execute([$label, $suggestion, $suggestion, $quiz['id']]);
    v131_upsert_avaliacao($quiz, $nota, $suggestion);

    $extra = $suggestion ? "\nSeu comentário/sugestão também foi registrado." : '';
    v131_quiz_reply(
        $quiz,
        "🙏 *Obrigado pela sua avaliação!*\n\nSua resposta foi registrada com sucesso.".$extra."\n\nQue Deus abençoe você por servir. ❤️",
        'quiz_single_completed_v1416'
    );
    return true;
}

'''
s=s[:handler_start]+new_handler+s[router_start:]
p.write_text(s)

# 2) Pending router: mantem todo transporte/sessao da v1.4.15; troca apenas textos e pergunta do quiz.
p=root/'api/pending_router_v1311.php'
s=p.read_text()
old="$step=(int)($r['etapa']??1); $label='📝 Quiz da escala '.$date.($time!==''?' às '.$time:'').' — '.$culto.($step>1?' (etapa '.$step.')':'');"
if old in s:
    s=s.replace(old,"$label='📝 Avaliação do culto '.$date.($time!==''?' às '.$time:'').' — '.$culto;",1)
start=s.find('function v1311p_quiz_question(array $quiz): string')
end=s.find('function v1311p_dedupe_file', start)
if start<0 or end<0:
    raise SystemExit('pending quiz question anchors not found')
new_question=r'''function v1311p_quiz_question(array $quiz): string {
    $date=!empty($quiz['data'])?date('d/m/Y',strtotime((string)$quiz['data'])):'—';
    $time=trim((string)($quiz['horario']??''));
    $time=$time!==''?substr($time,0,5):'';
    $head="📝 *Avaliação do culto*\n📋 ".(($quiz['culto_nome']??'')?:'Culto')."\n📅 {$date}".($time!==''?' às '.$time:'')."\n\n";
    return $head."⭐ *Como você avalia sua experiência neste culto/serviço?*\n\n*1* - 😞 Péssimo\n*2* - 😕 Ruim\n*3* - 😐 Normal\n*4* - 😊 Bom\n*5* - 🤩 Ótimo\n\n💬 Se quiser, deixe um comentário ou sugestão *na mesma resposta*.\n\nEx.: *5* ou *5 - Gostei muito do culto.*\n\n_Responda somente uma vez. Digite MENU para voltar._";
}

'''
s=s[:start]+new_question+s[end:]
p.write_text(s)

# 3) Automation: nao muda a regra de disparo; apenas explicita resposta unica e normaliza quizzes legados pendentes.
p=root/'api/automation_v130.php'
s=p.read_text()
s=s.replace('_Responda começando com uma nota de 1 a 5._','_Responda somente uma vez, começando com uma nota de 1 a 5._',1)
anchor='function v131_repair_quiz_noise()'
idx=s.find(anchor)
if idx<0: raise SystemExit('automation helper anchor not found')
helper='function v1416_normalize_pending_quizzes():int{try{$q=db()->prepare("UPDATE quiz_pos_culto SET etapa=2,updated_at=NOW() WHERE respondido=0 AND quiz_enviado=1 AND etapa IN (1,3,5)");$q->execute();return$q->rowCount();}catch(Throwable$e){return 0;}}\n'
if 'function v1416_normalize_pending_quizzes()' not in s:
    s=s[:idx]+helper+s[idx:]
s=s.replace("'quizzes_autofinalized'=>0,'quiz_noise_cleaned'=>0","'quizzes_autofinalized'=>0,'quizzes_normalized_single'=>0,'quiz_noise_cleaned'=>0",1)
s=s.replace("$s['quiz_noise_cleaned']=v131_repair_quiz_noise();$s['quizzes_autofinalized']=v131_finalize_stale_quizzes();$x=v130_due_quizzes();","$s['quiz_noise_cleaned']=v131_repair_quiz_noise();$s['quizzes_normalized_single']=v1416_normalize_pending_quizzes();$s['quizzes_autofinalized']=v131_finalize_stale_quizzes();$x=v130_due_quizzes();",1)
p.write_text(s)

# 4) Cache bust. O modal do app ja possui nota 1..5 + comentario opcional na mesma tela.
p=root/'sistema.html'
s=p.read_text()
s=re.sub(r'/assets/index-C6Ng0a8i\\.js\\?v=[^\"\\\']+', '/assets/index-C6Ng0a8i.js?v=1.4.16', s)
p.write_text(s)
p=root/'sw.js'
s=p.read_text()
if not s.startswith('// single-quiz-strict-v1.4.16'):
    s='// single-quiz-strict-v1.4.16\n'+s
s=s.replace('v1.4.15','v1.4.16')
p.write_text(s)
(root/'registerSW.js').write_text("if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const r=await navigator.serviceWorker.register('/sw.js?v=1.4.16',{scope:'/',updateViaCache:'none'});await r.update()}catch(e){console.warn('[SW v1.4.16]',e)}})}")
