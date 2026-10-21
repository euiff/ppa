from pathlib import Path
import re

root=Path('pkg')

def patch_file(path, old, new, label):
    p=root/path
    s=p.read_text(encoding='utf-8')
    if s.count(old)!=1: raise RuntimeError(f'{label}: occurrences={s.count(old)}')
    p.write_text(s.replace(old,new,1),encoding='utf-8')

patch_file('api/app-pending.php',
    "AND (e.data IS NULL OR e.data>=CURDATE()) AND COALESCE(e.status,'') NOT IN ('cancelada','cancelado','excluida','excluido')",
    "AND (e.data IS NULL OR e.data>=CURDATE()) AND e.status='publicado'",
    'native draft exclusion')

patch_file('api/app-pending.php',
    "SELECT id,title,message,url,created_at FROM app_notification_events WHERE BINARY user_id=BINARY ? AND expires_at>NOW() ORDER BY created_at DESC LIMIT 100",
    "SELECT ev.id,ev.title,ev.message,ev.url,ev.created_at FROM app_notification_events ev JOIN escalas e ON BINARY e.id=BINARY ev.escala_id WHERE BINARY ev.user_id=BINARY ? AND ev.expires_at>NOW() AND e.status='publicado' ORDER BY ev.created_at DESC LIMIT 100",
    'event draft exclusion')

patch_file('api/app_notification_events_v1470.php',
    'WHERE BINARY e.id=BINARY ?',
    "WHERE BINARY e.id=BINARY ? AND e.status='publicado'",
    'event generation guard')

patch_file('api/app-scale-resend-v1470.php',
    "if(!$esc)out(['data'=>null,'error'=>['message'=>'Escala não encontrada.']],404);",
    "if(!$esc)out(['data'=>null,'error'=>['message'=>'Escala não encontrada.']],404);\n    if((string)$esc['status']!=='publicado')out(['data'=>null,'error'=>['message'=>'Primeiro publique a escala para enviar notificações.']],409);",
    'publish gate endpoint')

asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')
def r(old,new,label):
    global s
    if s.count(old)!=1: raise RuntimeError(f'{label}: occurrences={s.count(old)}')
    s=s.replace(old,new,1)

r('.eq("voluntario_id",t.id).gte("escalas.data",f).order("created_at",{ascending:!1}).limit(10)',
  '.eq("voluntario_id",t.id).eq("escalas.status","publicado").gte("escalas.data",f).order("created_at",{ascending:!1}).limit(10)',
  'browser draft exclusion')
r('const j=v.escalas,w=v.status_confirmacao==="pendente",S=(j==null?void 0:j.status)!=="publicado";x.push(',
  'const j=v.escalas,w=v.status_confirmacao==="pendente",S=(j==null?void 0:j.status)!=="publicado";if(S)return;x.push(',
  'browser extra status guard')

r('V.success("Escala publicada!");const{data:me,error:$}=await I.functions.invoke("send-whatsapp",{body:{escala_id:e.id,force_resend:!1}});',
  'V.success("Escala publicada!");try{const tokV1480=localStorage.getItem("escala-facil.auth-token")||"",respV1480=await fetch("/api/app-scale-resend-v1470.php",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+tokV1480},body:JSON.stringify({escala_id:e.id})}),dataV1480=await respV1480.json();if(respV1480.ok&&!(dataV1480!=null&&dataV1480.error))V.success("Aplicativo: "+((dataV1480==null?void 0:dataV1480.data)==null?0:dataV1480.data.queued||0)+" avisos.");else if(respV1480.status!==403)V.warning("Escala publicada, mas os avisos no aplicativo não foram concluídos.")}catch(appErrorV1480){V.warning("Escala publicada, mas o aviso no aplicativo falhou.")}const{data:me,error:$}=await I.functions.invoke("send-whatsapp",{body:{escala_id:e.id,force_resend:!1}});',
  'detail button app and whatsapp')

r('sendChannelV1470=async pe=>{const q=await planFeaturesV1470();if(q&&q.whatsapp===!1)return{channel:"app",result:await appNotifyV1470(pe)};const{data:oe,error:xe}=await I.functions.invoke("send-whatsapp",{body:{escala_id:l.id,...pe?{escala_item_id:pe}:{},force_resend:!0}});if(xe)throw xe;return{channel:"whatsapp",result:oe||{}}}',
  'sendChannelV1470=async pe=>{const q=await planFeaturesV1470(),resultsV1480={queued:0,sent:0,errors:0,app_queued:0},failuresV1480=[];let sentAnyV1480=!1;if(!q||q.app_notifications!==!1)try{const apV1480=await appNotifyV1470(pe);resultsV1480.app_queued=apV1480.queued||0;sentAnyV1480=!0}catch(errV1480){if(!String(errV1480==null?void 0:errV1480.message).includes("não estão habilitadas neste plano"))failuresV1480.push("aplicativo: "+(errV1480.message||"erro"))}if(!q||q.whatsapp!==!1)try{const{data:oe,error:xe}=await I.functions.invoke("send-whatsapp",{body:{escala_id:l.id,...pe?{escala_item_id:pe}:{},force_resend:!0}});if(xe)throw xe;Object.assign(resultsV1480,oe||{});sentAnyV1480=!0}catch(errV1480){failuresV1480.push("WhatsApp: "+(errV1480.message||"erro"))}if(!sentAnyV1480)throw new Error(failuresV1480.join(" | ")||"Nenhum canal de notificação habilitado");if(failuresV1480.length)V.warning("Avisos parciais: "+failuresV1480.join(" | "));return{channel:"both",result:resultsV1480}}',
  'complete scale app and whatsapp')

r('oe.channel==="app"?V.success("Escala publicada e "+(xe.queued||0)+" notificação(ões) enviada(s) para o app."):(xe.queued||0)>0?V.success("Escala publicada e "+(xe.queued||0)+" mensagem(ns) colocada(s) na fila."):V.success("Escala publicada. O envio de notificações foi processado.")',
  'V.success("Escala publicada. Aplicativo: "+(xe.app_queued||0)+" aviso(s); WhatsApp: "+(xe.queued||xe.sent||0)+" mensagem(ns).")',
  'publish success feedback')
r('pe.channel==="app"?V.success("Notificações pelo app reenviadas: "+(q.queued||0)+"."):(q.queued||0)>0?V.success("Reenvio agendado na fila segura: "+(q.queued||0)+" mensagem(ns)."):(q.sent||0)>0?V.success("Notificações reenviadas: "+(q.sent||0)+" sucesso, "+(q.errors||0)+" erros."):V.warning("Reenvio concluído, mas nenhuma mensagem foi enviada. Erros: "+(q.errors||0)+".")',
  'V.success("Reenvio realizado. Aplicativo: "+(q.app_queued||0)+" aviso(s); WhatsApp: "+(q.queued||q.sent||0)+" mensagem(ns).")',
  'resend all feedback')
r('oe.channel==="app"?V.success("Notificação pelo app reenviada para "+ge+"."):(xe.queued||0)>0?V.success("Reenvio agendado para "+ge+"."):(xe.sent||0)>0?V.success("Notificação reenviada para "+ge+"."):V.warning("Não foi possível reenviar para "+ge+".")',
  'V.success("Reenvio para "+ge+". App: "+(xe.app_queued||0)+", WhatsApp: "+(xe.queued||xe.sent||0)+".")',
  'resend one feedback')

r('e.status==="publicado"&&(ue!=null&&ue.id))try{const Ee=await Ye({escala_id:e.id,escala_item_id:ue.id,force_resend:!1});((Ee==null?void 0:Ee.queued)||0)>0?V.success("WhatsApp agendado na fila segura para o voluntário adicionado."):((Ee==null?void 0:Ee.sent)||0)>0?V.success("Notificação WhatsApp enviada para o voluntário adicionado."):V.warning("Voluntário adicionado, mas o WhatsApp não foi enviado (sem número/token ou erro no provedor).")}catch(Ee){console.error("[EscalaDetail] notify on add error:",Ee),V.warning("Voluntário adicionado, mas falhou ao enviar WhatsApp agora.")}',
  'e.status==="publicado"&&(ue!=null&&ue.id))V.warning("Voluntário salvo. Clique em Reenviar Notificações quando quiser avisar pelo aplicativo e WhatsApp.");',
  'no auto send on saving published volunteer')

r('Como a escala já está publicada, o voluntário adicionado será notificado automaticamente.',
  'Após adicionar, clique em Reenviar Notificações para avisar pelo aplicativo e WhatsApp.',
  'published edit helper text')

asset.write_text(s,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\g<1>?v=1.4.80\g<2>',h,count=1)
if n!=1: raise RuntimeError('main JS missing')
for old,new in [
    ('app-notifications-v1465.js?v=1.4.79','app-notifications-v1465.js?v=1.4.80'),
    ('whatsapp-group-settings-v1473.js?v=1.4.79','whatsapp-group-settings-v1473.js?v=1.4.80'),
    ('master-whatsapp-groups-entry-v1475.js?v=1.4.79','master-whatsapp-groups-entry-v1475.js?v=1.4.80'),
    ('cron-fix-v1478.js?v=1.4.79','cron-fix-v1478.js?v=1.4.80')
]: h=h.replace(old,new)
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.80 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.80\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.80.md').write_text("""# Escala de Propósito v1.4.80 — Avisar somente ao publicar

- Salvar escala, preencher template ou adicionar voluntário não dispara avisos.
- O app não exibe nem anuncia escala em rascunho; consultas web e nativa filtram por status publicado.
- O endpoint de eventos do app recusa notificação de rascunho, mesmo se chamado diretamente.
- Ao clicar Publicar e Notificar, o sistema publica e aciona aplicativo e WhatsApp, conforme os canais habilitados no plano.
- A publicação não deixa de avisar pelo app só porque o WhatsApp está habilitado.
- O botão Reenviar Notificações na escala completa também usa ambos os canais.
- Se houver falha em um canal, a outra tentativa não é cancelada; o sistema mostra aviso parcial.
- Mantém os recursos da versão 1.4.79.
""",encoding='utf-8')
