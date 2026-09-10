from pathlib import Path
import re, sys
root=Path(sys.argv[1]); api=root/'api'

# Recusa no WhatsApp: registra e avisa o responsável, sem abrir SOS automático.
p=api/'confirmation_router_v1311.php'; s=p.read_text(encoding='utf-8')
s=s.replace("if(is_file(__DIR__.'/sos_lib_v140.php')) require_once __DIR__.'/sos_lib_v140.php';\n",'',1)
s=s.replace("ℹ️ Sua recusa para esta escala já foi registrada. Se deseja voltar para a escala, fale com o líder para evitar conflito com uma possível substituição.","ℹ️ Sua recusa para esta escala já foi registrada. Se precisar alterar a resposta, fale com o pastor ou líder responsável.")
s=s.replace("ℹ️ Esta escala já estava confirmada. Para cancelar depois da confirmação, fale com o líder para que a substituição seja feita corretamente.","ℹ️ Esta escala já estava confirmada. Para cancelar depois da confirmação, fale com o pastor ou líder responsável para que ele ajuste a escala.")
s=s.replace("📝 Entendido. Sua indisponibilidade foi registrada.\\n\\nAgora, por favor, *informe o motivo* (ex.: viagem, trabalho, saúde). O líder receberá o aviso.","📝 Entendido. Sua indisponibilidade foi registrada.\\n\\nAgora, por favor, *informe o motivo* (ex.: viagem, trabalho, saúde). O pastor ou líder responsável receberá o aviso e escolherá manualmente quem será escalado no seu lugar.")
old="""    try{
        $auto=function_exists('config_value')?(string)config_value('sos_auto_enabled',(string)($item['igreja_id']??''),'1'):'1';
        if($q->rowCount()>0 && $auto!=='0' && function_exists('sos_v140_create')) sos_v140_create((string)$item['item_id'],null,'Recusa pelo WhatsApp',true);
    }catch(Throwable $sosError){}
"""
if old not in s: raise SystemExit('SOS auto block not found')
s=s.replace(old,'',1); p.write_text(s,encoding='utf-8')

# Motivo da recusa não alimenta mais solicitação SOS.
p=api/'pending_router_v1311.php'; s=p.read_text(encoding='utf-8')
old=" try{if(is_file(__DIR__.'/sos_lib_v140.php'))require_once __DIR__.'/sos_lib_v140.php';if(function_exists('sos_v140_ensure_schema')){sos_v140_ensure_schema();db()->prepare(\"UPDATE sos_requests SET motivo=?,updated_at=NOW() WHERE escala_item_id=? AND status='open'\")->execute([$reason,$item['item_id']]);}}catch(Throwable $ignored){}"
if old not in s: raise SystemExit('SOS reason sync not found')
s=s.replace(old,'',1)
s=s.replace("Sua indisponibilidade e o motivo foram enviados ao líder. Obrigado por avisar.","Sua indisponibilidade e o motivo foram enviados ao pastor ou líder responsável. Ele escolherá quem será escalado no seu lugar. Obrigado por avisar.",1)
p.write_text(s,encoding='utf-8')

# Webhook não interpreta mais SOS 1/SOS 2.
p=api/'webhook-entry-v1311.php'; s=p.read_text(encoding='utf-8')
old="""    $stage='sos_router_load';
    if(is_file(__DIR__.'/sos-router-v140.php')) require_once __DIR__.'/sos-router-v140.php';
    v1311e_trace('phase_ok',['stage'=>$stage,'handler'=>function_exists('sos_v140_router_handle')]);
    $stage='sos_router_handle';
    if(function_exists('sos_v140_router_handle')&&sos_v140_router_handle()){
        v1311e_trace('handled',['stage'=>$stage]);
        v1311e_out(['ok'=>true,'action'=>'sos_router_v140']);
    }

"""
if old not in s: raise SystemExit('SOS webhook block not found')
s=s.replace(old,'',1); p.write_text(s,encoding='utf-8')

# API antiga de SOS não pode mais iniciar busca automática.
p=api/'sos.php'; s=p.read_text(encoding='utf-8')
old="if($action==='create'){$item=(string)($req['escala_item_id']??'');$r=sos_v140_item($item);if(!$r||$r['igreja_id']!==$ig)out(['data'=>null,'error'=>['message'=>'Escala não encontrada']],404);$s=sos_v140_create($item,$uid,trim((string)($req['motivo']??''))?:null,true);out(['data'=>$s,'error'=>null]);}"
new="if($action==='create')out(['data'=>null,'error'=>['message'=>'SOS automático foi desativado. Quando houver uma recusa, o pastor ou líder responsável escolhe manualmente quem será escalado no lugar.']],410);"
if old not in s: raise SystemExit('SOS API create anchor not found')
s=s.replace(old,new,1); p.write_text(s,encoding='utf-8')

# CRON não executa mais rotina SOS.
p=api/'automation_v130.php'; s=p.read_text(encoding='utf-8')
s=s.replace("if(is_file(__DIR__.'/sos_lib_v140.php'))require_once __DIR__.'/sos_lib_v140.php';\n",'',1)
s=s.replace("if(function_exists('sos_v140_cleanup'))$s['sos_expired']=sos_v140_cleanup();","$s['sos_expired']=0;",1)
p.write_text(s,encoding='utf-8')

# Saúde da escala não mostra busca automática de substituto.
p=api/'scale-health.php'; s=p.read_text(encoding='utf-8')
s=s.replace("require_once __DIR__.'/sos_lib_v140.php';\n",'',1)
s=s.replace("  sos_v140_ensure_schema();$q=db()->prepare(\"SELECT COUNT(*) FROM sos_requests WHERE escala_id=? AND status='open'\");$q->execute([$scale]);$sos=(int)$q->fetchColumn();\n","  $sos=0;\n",1)
s=s.replace("if($sos)$tips[]=\"$sos SOS buscando substituto\";",'',1)
p.write_text(s,encoding='utf-8')

# Mensagem ao pastor/líder deixa claro que a substituição é manual.
p=api/'scale_response_notify_v1417.php'; s=p.read_text(encoding='utf-8')
old='$msg.="\\n\\nA resposta já foi registrada no *Escala de Propósito*.";'
new='$msg.=$confirmed?"\\n\\nA resposta já foi registrada no *Escala de Propósito*.":"\\n\\n👉 *Ação:* abra a escala e escolha manualmente quem será escalado no lugar.\\nA indisponibilidade já foi registrada no *Escala de Propósito*.";'
if old not in s: raise SystemExit('leader message anchor not found')
s=s.replace(old,new,1)
old='$msg="📝 *Motivo da indisponibilidade*\\n\\n👤 *".($item[\'voluntario_nome\']?:\'Voluntário\')."*\\n📋 ".($item[\'culto_nome\']?:\'Culto\')."\\n📅 ".v1417_format_date((string)$item[\'data\'])."\\n⛪ ".($item[\'departamento_nome\']?:\'Ministério\')." — ".$item[\'funcao\']."\\n💬 *Motivo:* ".$reason;'
new='$msg="📝 *Motivo da indisponibilidade*\\n\\n👤 *".($item[\'voluntario_nome\']?:\'Voluntário\')."*\\n📋 ".($item[\'culto_nome\']?:\'Culto\')."\\n📅 ".v1417_format_date((string)$item[\'data\'])."\\n⛪ ".($item[\'departamento_nome\']?:\'Ministério\')." — ".$item[\'funcao\']."\\n💬 *Motivo:* ".$reason."\\n\\n👉 *Ação:* escolha manualmente na escala quem ficará no lugar deste voluntário.";'
if old not in s: raise SystemExit('reason leader message anchor not found')
s=s.replace(old,new,1); p.write_text(s,encoding='utf-8')

# Remove o card SOS das configurações e referências de marketing.
p=root/'smart-features.js'; s=p.read_text(encoding='utf-8')
s=s.replace("holder.append(card('sf-notif','🔔','Notificações','Escalas próximas, SOS e avisos importantes','/notificacoes.html'));holder.append(card('sf-sos','🚨','SOS Escala','Acompanhe substituições inteligentes e candidatos','/sos.html'));","holder.append(card('sf-notif','🔔','Notificações','Escalas, confirmações e avisos importantes','/notificacoes.html'));",1)
p.write_text(s,encoding='utf-8')
p=root/'sobre-app.html'; s=p.read_text(encoding='utf-8'); s=s.replace(', SOS Escala e gestão por igreja.',' e gestão por igreja.',1); p.write_text(s,encoding='utf-8')

# Encerra solicitações SOS antigas em aberto, sem apagar histórico.
mig=root/'database/migrations/20260909_1426_manual_replacement.sql'
mig.write_text("UPDATE sos_requests SET status='cancelled',closed_at=COALESCE(closed_at,NOW()),updated_at=NOW() WHERE status='open';\nUPDATE sos_candidates SET status='closed',responded_at=COALESCE(responded_at,NOW()) WHERE status IN ('offered','eligible');\n",encoding='utf-8')

# Cache-bust.
p=root/'sistema.html'; s=p.read_text(encoding='utf-8'); s=re.sub(r'/assets/index-C6Ng0a8i\.js\?v=[^\"<]+','/assets/index-C6Ng0a8i.js?v=1.4.26',s); p.write_text(s,encoding='utf-8')
p=root/'sw.js'; s=p.read_text(encoding='utf-8'); s+='\n/* manual-replacement-no-sos-v1.4.26 */\n'; p.write_text(s,encoding='utf-8')
