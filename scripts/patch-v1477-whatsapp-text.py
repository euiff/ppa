from pathlib import Path
import re

root=Path('pkg')
p=root/'api'/'whatsapp_group_reminder_v1473.php'
s=p.read_text(encoding='utf-8')

old_default="Por gentileza, entrem no WhatsApp da igreja e façam a confirmação das pendências."
new_default="Por gentileza, entrem no WhatsApp do sistema Escala de Propósito e façam a confirmação das pendências."

count=s.count(old_default)
if count<1:
    raise SystemExit('old reminder sentence not found')
s=s.replace(old_default,new_default)

old_render="""function v1473_render_message(string $template,array $ctx): string {
    $template=trim($template)!==''?$template:v1473_default_message();
    $repl=["""
new_render="""function v1473_render_message(string $template,array $ctx): string {
    $template=trim($template)!==''?$template:v1473_default_message();
    // v1.4.77: atualiza automaticamente a frase antiga já salva por igrejas
    // para o texto oficial do sistema, sem exigir que cada igreja edite manualmente.
    $template=str_replace(
        'Por gentileza, entrem no WhatsApp da igreja e façam a confirmação das pendências.',
        'Por gentileza, entrem no WhatsApp do sistema Escala de Propósito e façam a confirmação das pendências.',
        $template
    );
    $repl=["""
if s.count(old_render)!=1:
    raise SystemExit('render anchor count='+str(s.count(old_render)))
s=s.replace(old_render,new_render,1)
p.write_text(s,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
for old,new in [
    ('/whatsapp-group-settings-v1473.js?v=1.4.76','/whatsapp-group-settings-v1473.js?v=1.4.77'),
    ('/app-notifications-v1465.js?v=1.4.76','/app-notifications-v1465.js?v=1.4.77'),
    ('/master-whatsapp-groups-entry-v1475.js?v=1.4.76','/master-whatsapp-groups-entry-v1475.js?v=1.4.77'),
]:
    h=h.replace(old,new)
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\1?v=1.4.77\2',h,count=1)
if n!=1:
    raise SystemExit('main bundle tag missing')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.77 */\n'+sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.77\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.77.md').write_text("""# Escala de Propósito v1.4.77 — Texto do WhatsApp ajustado

- Altera a frase do lembrete para:
  **Por gentileza, entrem no WhatsApp do sistema Escala de Propósito e façam a confirmação das pendências.**
- A troca também é aplicada automaticamente às mensagens antigas que ainda tenham a frase “WhatsApp da igreja”, sem precisar editar igreja por igreja.
- Mantém todas as correções e recursos da v1.4.76.
""",encoding='utf-8')
