from pathlib import Path
import sys
root=Path(sys.argv[1])
api=root/'api/master-data-cleanup.php'
s=api.read_text(encoding='utf-8')
old="if($action==='status'){out(['data'=>['churches'=>db()->query('SELECT id,nome FROM igrejas ORDER BY nome')->fetchAll(PDO::FETCH_ASSOC)],'error'=>null]);}"
new="if($action==='status'){$rows=db()->query(\"SELECT i.id,i.nome,COUNT(e.id) total_escalas,MIN(e.data) min_data,MAX(e.data) max_data,SUM(CASE WHEN e.data<CURDATE() THEN 1 ELSE 0 END) past_total,MIN(CASE WHEN e.data<CURDATE() THEN e.data END) past_min,MAX(CASE WHEN e.data<CURDATE() THEN e.data END) past_max FROM igrejas i LEFT JOIN escalas e ON e.igreja_id=i.id GROUP BY i.id,i.nome ORDER BY i.nome\")->fetchAll(PDO::FETCH_ASSOC);out(['data'=>['churches'=>$rows],'error'=>null]);}"
if old not in s: raise SystemExit('status marker not found')
s=s.replace(old,new,1)
api.write_text(s,encoding='utf-8')

p=root/'master-limpeza.html'
h=p.read_text(encoding='utf-8')
old='.muted{color:#69788d}'
new='.muted{color:#69788d}.range{margin-top:8px;padding:10px 12px;background:#f7f9fc;border:1px solid #e2e8f0;border-radius:10px;font-size:12px;line-height:1.45}.range b{color:#172033}'
if old not in h: raise SystemExit('css marker not found')
h=h.replace(old,new,1)
old='<select id="church"><option>Carregando...</option></select><label>Excluir dados até esta data (inclusive)</label>'
new='<select id="church"><option>Carregando...</option></select><div id="range" class="range muted">Selecione uma igreja para ver o período com dados.</div><label>Excluir dados até esta data (inclusive)</label>'
if old not in h: raise SystemExit('select marker not found')
h=h.replace(old,new,1)
old="let last=null;function msg"
new="let last=null,churches=[];function msg"
if old not in h: raise SystemExit('state marker not found')
h=h.replace(old,new,1)
old="async function load(){try{const d=await api({action:'status'});$('church').innerHTML='<option value=\"\">Selecione uma igreja</option>'+d.churches.map(x=>`<option value=\"${x.id}\">${x.nome}</option>`).join('');let z=new Date();z.setMonth(z.getMonth()-6);$('cutoff').value=z.toISOString().slice(0,10)}catch(e){msg(e.message,'err')}}"
new="function fmtDate(d){if(!d)return'—';const[y,m,a]=d.split('-');return`${a}/${m}/${y}`}function showRange(){const x=churches.find(v=>v.id===$('church').value);last=null;$('preview').style.display='none';$('empty').style.display='block';$('confirm').value='';unlock();if(!x){$('range').textContent='Selecione uma igreja para ver o período com dados.';$('cutoff').value='';return}const total=Number(x.total_escalas||0),past=Number(x.past_total||0);if(!total){$('range').innerHTML='<b>Nenhuma escala encontrada</b> para esta igreja.';$('cutoff').value='';return}$('range').innerHTML=`<b>${total} escala(s) encontradas.</b><br>Período total: <b>${fmtDate(x.min_data)}</b> até <b>${fmtDate(x.max_data)}</b>${past?`<br>Histórico já ocorrido: <b>${fmtDate(x.past_min)}</b> até <b>${fmtDate(x.past_max)}</b> (${past} escala(s)).`:''}`;if(x.past_max)$('cutoff').value=x.past_max;else $('cutoff').value=''}async function load(){try{const d=await api({action:'status'});churches=d.churches||[];$('church').innerHTML='<option value=\"\">Selecione uma igreja</option>'+churches.map(x=>`<option value=\"${x.id}\">${x.nome}</option>`).join('');$('cutoff').value=''}catch(e){msg(e.message,'err')}}"
if old not in h: raise SystemExit('load marker not found')
h=h.replace(old,new,1)
old="msg('Confira os números antes de excluir.','ok')}catch(e){last=null;msg(e.message,'err')}finally{$('pv').disabled=false}"
new="if((last.affected||0)<1){const x=churches.find(v=>v.id===$('church').value);if(x&&Number(x.past_total||0)>0)msg(`Nenhum registro existe até ${fmtDate(last.cutoff)}. Esta igreja possui histórico entre ${fmtDate(x.past_min)} e ${fmtDate(x.past_max)}. Ajuste a data limite para esse período.`,'err');else msg('Não há dados antigos para excluir nesta igreja.','info')}else msg(`Encontrados ${last.affected} registro(s) afetado(s). Confira os números antes de excluir.`,'ok');unlock()}catch(e){last=null;msg(e.message,'err')}finally{$('pv').disabled=false}"
if old not in h: raise SystemExit('preview message marker not found')
h=h.replace(old,new,1)
old="document.querySelectorAll('input[name=scope]').forEach(x=>x.onchange=()=>{last=null;$('preview').style.display='none';$('empty').style.display='block'});load();"
new="$('church').addEventListener('change',showRange);$('cutoff').addEventListener('change',()=>{last=null;$('preview').style.display='none';$('empty').style.display='block'});document.querySelectorAll('input[name=scope]').forEach(x=>x.onchange=()=>{last=null;$('preview').style.display='none';$('empty').style.display='block'});load();"
if old not in h: raise SystemExit('event marker not found')
h=h.replace(old,new,1)
p.write_text(h,encoding='utf-8')

p=root/'sistema.html';s=p.read_text(encoding='utf-8');s=s.replace('/assets/index-C6Ng0a8i.js?v=1.4.18','/assets/index-C6Ng0a8i.js?v=1.4.19');p.write_text(s,encoding='utf-8')
p=root/'sw.js';p.write_text(p.read_text(encoding='utf-8')+'\n/* master-cleanup-range-v1.4.19 */\n',encoding='utf-8')
