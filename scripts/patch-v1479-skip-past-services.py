from pathlib import Path
import re

root=Path('pkg')
p=root/'api'/'whatsapp_group_reminder_v1473.php'
s=p.read_text(encoding='utf-8')

anchor="""function v1473_group_reminders(): array {"""
helper="""function v1479_scale_already_started(array $scale,DateTimeImmutable $now,DateTimeZone $z): bool {
    $date=trim((string)($scale['data']??''));
    $time=trim((string)($scale['horario']??''));
    if($date===''||$date!==$now->format('Y-m-d'))return false;
    if(!preg_match('/^(?:[01]\\d|2[0-3]):[0-5]\\d(?::[0-5]\\d)?$/',$time))return false;
    $hm=substr($time,0,5);
    try{$start=new DateTimeImmutable($date.' '.$hm.':00',$z);}catch(Throwable $e){return false;}
    return $start<=$now;
}
function v1473_group_reminders(): array {"""
if s.count(anchor)!=1:
    raise SystemExit('group reminders anchor count='+str(s.count(anchor)))
s=s.replace(anchor,helper,1)

old="""$out=['checked'=>0,'due'=>0,'sent'=>0,'failed'=>0,'skipped'=>0];try{foreach(v1473_enabled_churches()as$ig)"""
new="""$out=['checked'=>0,'due'=>0,'sent'=>0,'failed'=>0,'skipped'=>0,'past_skipped'=>0];try{foreach(v1473_enabled_churches()as$ig)"""
if s.count(old)!=1:
    raise SystemExit('summary anchor count='+str(s.count(old)))
s=s.replace(old,new,1)

old_loop="""$target=$now->modify('+'.$days.' days')->format('Y-m-d');foreach(v1473_scale_groups_for_date($ig,$target)as$scale){$out['due']++;$res=v1473_send_scale_group_reminder($ig,$scale,$schedule,false);if(!empty($res['sent']))$out['sent']++;elseif(!empty($res['already_sent']))$out['skipped']++;else$out['failed']++;}}"""
new_loop="""$target=$now->modify('+'.$days.' days')->format('Y-m-d');foreach(v1473_scale_groups_for_date($ig,$target)as$scale){
            // v1.4.79: se o lembrete do mesmo dia ficou atrasado (ex.: CRON voltou à tarde),
            // nunca manda uma escala cujo culto já começou ou terminou. Continua apenas
            // com os cultos que ainda vão acontecer naquele dia.
            if(v1479_scale_already_started($scale,$now,$z)){$out['past_skipped']++;$out['skipped']++;continue;}
            $out['due']++;$res=v1473_send_scale_group_reminder($ig,$scale,$schedule,false);if(!empty($res['sent']))$out['sent']++;elseif(!empty($res['already_sent']))$out['skipped']++;else$out['failed']++;
        }}"""
if s.count(old_loop)!=1:
    raise SystemExit('group loop anchor count='+str(s.count(old_loop)))
s=s.replace(old_loop,new_loop,1)
p.write_text(s,encoding='utf-8')

# Atualiza o painel de diagnóstico do CRON para mostrar cultos passados ignorados.
p=root/'cron-fix-v1478.js'
js=p.read_text(encoding='utf-8')
old_js="""  const failed=Number(s.group_reminders_failed||0);
  const jobs=Number(s.jobs_sent||0);
  return 'Grupo: '+due+' devido(s), '+sent+' enviado(s), '+failed+' falha(s) · WhatsApp individual: '+jobs+' enviado(s)';"""
new_js="""  const failed=Number(s.group_reminders_failed||0);
  const past=Number(s.group_reminders_past_skipped||0);
  const jobs=Number(s.jobs_sent||0);
  return 'Grupo: '+due+' devido(s), '+sent+' enviado(s), '+failed+' falha(s), '+past+' culto(s) passado(s) ignorado(s) · WhatsApp individual: '+jobs+' enviado(s)';"""
if js.count(old_js)!=1:
    raise SystemExit('cron summary JS anchor count='+str(js.count(old_js)))
js=js.replace(old_js,new_js,1)
p.write_text(js,encoding='utf-8')

# Expõe o novo contador no resumo global do motor.
p=root/'api'/'automation_v130.php'
a=p.read_text(encoding='utf-8')
old_a="""$s['group_reminders_due']=$gx['due']??0;$s['group_reminders_sent']=$gx['sent']??0;$s['group_reminders_failed']=$gx['failed']??0;"""
new_a="""$s['group_reminders_due']=$gx['due']??0;$s['group_reminders_sent']=$gx['sent']??0;$s['group_reminders_failed']=$gx['failed']??0;$s['group_reminders_past_skipped']=$gx['past_skipped']??0;"""
if a.count(old_a)!=1:
    raise SystemExit('automation group summary anchor count='+str(a.count(old_a)))
a=a.replace(old_a,new_a,1)
p.write_text(a,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
for old,new in [
    ('/app-notifications-v1465.js?v=1.4.78','/app-notifications-v1465.js?v=1.4.79'),
    ('/whatsapp-group-settings-v1473.js?v=1.4.78','/whatsapp-group-settings-v1473.js?v=1.4.79'),
    ('/master-whatsapp-groups-entry-v1475.js?v=1.4.78','/master-whatsapp-groups-entry-v1475.js?v=1.4.79'),
    ('/cron-fix-v1478.js?v=1.4.78','/cron-fix-v1478.js?v=1.4.79'),
]:
    h=h.replace(old,new)
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\1?v=1.4.79\2',h,count=1)
if n!=1:
    raise SystemExit('main bundle tag missing')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.79 */\n'+sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.79\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.79.md').write_text("""# Escala de Propósito v1.4.79 — Não enviar cultos que já passaram

- Corrige o lembrete automático no próprio dia.
- Se o CRON rodar tarde ou voltar a funcionar depois do horário programado, o sistema não envia mais escalas de cultos que já começaram ou terminaram.
- Exemplo: domingo às 15:46, uma escala de oração da manhã às 08:00 é ignorada; a escala do culto da noite às 19:00 continua elegível e é enviada normalmente.
- A comparação usa o horário do culto e o fuso configurado para a igreja.
- Cultos sem horário cadastrado continuam elegíveis, porque o sistema não tem como afirmar que já passaram.
- O diagnóstico do CRON passa a mostrar quantos cultos passados foram ignorados.
- Mantém todos os recursos e correções da v1.4.78.
""",encoding='utf-8')
