from pathlib import Path
import re

root=Path('pkg')
p=root/'api'/'whatsapp_group_reminder_v1473.php'
s=p.read_text(encoding='utf-8')

old="""function v1474_fresh_pending_count(string $igrejaId,string $date,$cultoId): int {
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
}"""

new="""function v1474_fresh_pending_count(string $igrejaId,string $date,$cultoId): int {
    // v1.4.76: esta consulta espelha o mesmo conjunto usado pelo PDF.
    // O PDF da escala completa busca todas as escalas da mesma igreja/data/culto,
    // independentemente do status individual de cada departamento.
    $sql="SELECT COUNT(ei.id)
          FROM escalas e
          JOIN escala_itens ei ON BINARY ei.escala_id=BINARY e.id
          WHERE BINARY e.igreja_id=BINARY ? AND e.data=?
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
}"""

if s.count(old)!=1:
    raise SystemExit('pending function anchor count='+str(s.count(old)))
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h=h.replace('/whatsapp-group-settings-v1473.js?v=1.4.75','/whatsapp-group-settings-v1473.js?v=1.4.76')
h=h.replace('/app-notifications-v1465.js?v=1.4.75','/app-notifications-v1465.js?v=1.4.76')
h=h.replace('/master-whatsapp-groups-entry-v1475.js?v=1.4.75','/master-whatsapp-groups-entry-v1475.js?v=1.4.76')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\1?v=1.4.76\2',h,count=1)
if n!=1:
    raise SystemExit('main bundle tag missing')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.76 */\n'+sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.76\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.76.md').write_text("""# Escala de Propósito v1.4.76 — Contagem igual ao PDF

- Corrige definitivamente a divergência entre o PDF e a mensagem enviada ao grupo.
- O PDF da escala completa reúne todos os departamentos da mesma igreja, data e culto.
- A contagem anterior verificava somente registros individuais com status publicado, podendo ignorar departamentos que já apareciam no PDF.
- Agora o contador usa exatamente o mesmo conjunto da escala completa: mesma igreja + mesma data + mesmo culto, sem excluir departamentos pelo status interno da escala.
- São considerados sem resposta os itens cujo status_confirmacao está vazio ou pendente.
- Assim, se o PDF mostra 2 voluntários como Pendente, a mensagem informa 2 pessoas ainda não confirmaram sua participação.
- Mantém o domínio atual https://escaladeproposito.com.br, os vários lembretes e o portal MASTER de grupos do WhatsApp da v1.4.75.
""",encoding='utf-8')
