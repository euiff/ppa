from pathlib import Path
import re

root=Path('pkg')
p=root/'api'/'whatsapp_group_reminder_v1473.php'
s=p.read_text(encoding='utf-8')

old="""function v1473_app_url(): string {
    global $config;$u=rtrim(trim((string)($config['app_url']??'')),'/');return $u!==''?$u:'https://escaladeproposito.com.br';
}"""
new="""function v1473_app_url(): string {
    // v1.4.74: domínio oficial atual, sem reaproveitar app_url antigo.
    return 'https://escaladeproposito.com.br';
}"""
if s.count(old)!=1:
    raise SystemExit('app_url anchor count='+str(s.count(old)))
s=s.replace(old,new,1)

oldq="SUM(CASE WHEN COALESCE(NULLIF(ei.status_confirmacao,''),'pendente')='pendente' THEN 1 ELSE 0 END) pending_count"
newq="SUM(CASE WHEN LOWER(TRIM(COALESCE(ei.status_confirmacao,''))) IN ('','pendente') THEN 1 ELSE 0 END) pending_count"
if s.count(oldq)!=1:
    raise SystemExit('pending aggregate anchor count='+str(s.count(oldq)))
s=s.replace(oldq,newq,1)

anchor="function v1473_send_scale_group_reminder(string $igrejaId,array $scale,array $schedule,bool $force=false): array {"
helper="""function v1474_fresh_pending_count(string $igrejaId,string $date,$cultoId): int {
    $sql="SELECT COUNT(ei.id)
          FROM escalas e
          JOIN escala_itens ei ON BINARY ei.escala_id=BINARY e.id
          WHERE BINARY e.igreja_id=BINARY ? AND e.data=? AND e.status='publicado'
            AND LOWER(TRIM(COALESCE(ei.status_confirmacao,''))) IN ('','pendente')";
    $params=[$igrejaId,$date];
    if($cultoId!==null && trim((string)$cultoId)!==''){
        $sql.=" AND BINARY e.culto_id=BINARY ?";
        $params[]=(string)$cultoId;
    }else{
        $sql.=" AND (e.culto_id IS NULL OR e.culto_id='')";
    }
    $q=db()->prepare($sql);$q->execute($params);
    return (int)$q->fetchColumn();
}
function v1473_send_scale_group_reminder(string $igrejaId,array $scale,array $schedule,bool $force=false): array {"""
if s.count(anchor)!=1:
    raise SystemExit('send function anchor count='+str(s.count(anchor)))
s=s.replace(anchor,helper,1)

oldpending="$pdf=v1473_pdf_link($igrejaId,(string)$scale['escala_id']);if(!$pdf)return ['ok'=>false,'sent'=>false,'error'=>'Não foi possível gerar o link do PDF.'];$pending=(int)($scale['pending_count']??0);$hour=trim((string)($scale['horario']??''));"
newpending="""$pdf=v1473_pdf_link($igrejaId,(string)$scale['escala_id']);if(!$pdf)return ['ok'=>false,'sent'=>false,'error'=>'Não foi possível gerar o link do PDF.'];
    $pending=v1474_fresh_pending_count($igrejaId,(string)$scale['data'],$scale['culto_id']??null);
    $scale['pending_count']=$pending;
    $hour=trim((string)($scale['horario']??''));"""
if s.count(oldpending)!=1:
    raise SystemExit('fresh pending anchor count='+str(s.count(oldpending)))
s=s.replace(oldpending,newpending,1)
p.write_text(s,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h=h.replace('/whatsapp-group-settings-v1473.js?v=1.4.73','/whatsapp-group-settings-v1473.js?v=1.4.74')
h=h.replace('/app-notifications-v1465.js?v=1.4.73','/app-notifications-v1465.js?v=1.4.74')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\1?v=1.4.74\2',h,count=1)
if n!=1:
    raise SystemExit('main bundle tag missing')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.74 */\n'+sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.74\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.74.md').write_text("""# Escala de Propósito v1.4.74 — Pendentes e link corretos no grupo

- Corrige a contagem exibida no lembrete do grupo: vazio ou pendente contam como pendência, ignorando maiúsculas/minúsculas e espaços.
- Antes de cada envio, a quantidade é recalculada diretamente do banco para o mesmo dia e culto do PDF.
- Se o PDF mostra 2 pessoas pendentes, a mensagem informa 2 pessoas ainda não confirmaram.
- O link enviado no grupo deixa de usar configurações antigas como escala.isaacanthony.com.br/r/.
- O endereço oficial dos lembretes e links de PDF passa a ser https://escaladeproposito.com.br.
- Mantém o grupo individual por igreja, os vários horários de lembrete e todos os recursos da v1.4.73.
""",encoding='utf-8')
