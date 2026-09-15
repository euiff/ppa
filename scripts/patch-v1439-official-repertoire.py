from pathlib import Path
import re

root=Path('pkg')
scale=root/'api'/'whatsapp_scale_message_v1421.php'
asset=list((root/'assets').glob('index-*.js'))[0]
s=scale.read_text(encoding='utf-8')
pat=re.compile(r"function v1421_same_day_repertoire\(array \$r\): array \{.*?\n\}\n\nfunction v1421_build_scale_message",re.S)
rep=r'''function v1439_rep_key(string $name): string {$x=$name;if(function_exists('iconv')){$y=@iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$x);if(is_string($y)&&$y!=='')$x=$y;}return strtoupper($x);} function v1421_same_day_repertoire(array $r): array {try{$esc=(string)($r['escala_id']??'');$ig=(string)($r['igreja_id']??'');$data=(string)($r['data']??'');$culto=(string)($r['culto_id']??'');$setlist='';if($ig!==''&&$data!==''&&$culto!==''){$sql="SELECT s.id setlist_id,s.escala_id,d.nome departamento_nome,s.created_at,COUNT(si.id) qtd FROM setlists s JOIN escalas e2 ON BINARY e2.id=BINARY s.escala_id LEFT JOIN departamentos d ON BINARY d.id=BINARY e2.departamento_id LEFT JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id WHERE BINARY e2.igreja_id=BINARY ? AND e2.data=? AND BINARY e2.culto_id=BINARY ? GROUP BY s.id,s.escala_id,d.nome,s.created_at HAVING qtd>0";$q=db()->prepare($sql);$q->execute([$ig,$data,$culto]);$c=$q->fetchAll(PDO::FETCH_ASSOC)?:[];if($c){usort($c,function($a,$b)use($esc){$ka=v1439_rep_key((string)($a['departamento_nome']??''));$kb=v1439_rep_key((string)($b['departamento_nome']??''));$pa=(strpos($ka,'LOUVOR')!==false||strpos($ka,'MUSICA')!==false)?0:1;$pb=(strpos($kb,'LOUVOR')!==false||strpos($kb,'MUSICA')!==false)?0:1;if($pa!==$pb)return $pa<=>$pb;$ea=((string)($a['escala_id']??'')===$esc)?0:1;$eb=((string)($b['escala_id']??'')===$esc)?0:1;if($ea!==$eb)return $ea<=>$eb;return strcmp((string)($a['created_at']??''),(string)($b['created_at']??''));});$setlist=(string)($c[0]['setlist_id']??'');}}if($setlist===''&&$esc!==''){$q=db()->prepare("SELECT s.id FROM setlists s JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id WHERE BINARY s.escala_id=BINARY ? GROUP BY s.id ORDER BY MIN(si.ordem),s.created_at LIMIT 1");$q->execute([$esc]);$setlist=(string)($q->fetchColumn()?:'');}if($setlist==='')return [];$sql="SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom,m.link_youtube FROM setlist_itens si JOIN musicas m ON BINARY m.id=BINARY si.musica_id WHERE BINARY si.setlist_id=BINARY ? ORDER BY si.ordem ASC,m.titulo ASC";$q=db()->prepare($sql);$q->execute([$setlist]);$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];$out=[];$seen=[];foreach($rows as $x){$id=(string)($x['musica_id']??'');$title=trim((string)($x['titulo']??''));$key=$id!==''?$id:(function_exists('mb_strtolower')?mb_strtolower($title,'UTF-8'):strtolower($title));if($key===''||isset($seen[$key]))continue;$seen[$key]=true;$out[]=$x;if(count($out)>=30)break;}return $out;}catch(Throwable $e){return [];}}

function v1421_build_scale_message'''
s,n=pat.subn(rep,s,count=1)
if n!=1: raise SystemExit('helper PHP não encontrado')
scale.write_text(s,encoding='utf-8')
js=asset.read_text(encoding='utf-8')
a='hG=({escalaId:e,canEdit:t})=>'
helper=r'''gR1439=async e=>{let t=e,n=null;try{const{data:s}=await I.from("escalas").select("id,data,culto_id,igreja_id").eq("id",e).maybeSingle();if(!s)return{escalaId:t,setlistId:n};let a=I.from("escalas").select("id,departamento_id").eq("igreja_id",s.igreja_id).eq("data",s.data);s.culto_id&&(a=a.eq("culto_id",s.culto_id));const{data:i}=await a,l=(i||[]).map(v=>v.id).filter(Boolean),c=[...new Set((i||[]).map(v=>v.departamento_id).filter(Boolean))],{data:d}=c.length?await I.from("departamentos").select("id,nome").in("id",c):{data:[]},f={};(d||[]).forEach(v=>{f[v.id]=v.nome||""});const m=v=>String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toUpperCase(),g=(i||[]).find(v=>{const j=m(f[v.departamento_id]);return j.includes("LOUVOR")||j.includes("MUSICA")});g&&(t=g.id);const{data:x}=await I.from("setlists").select("id,escala_id,created_at").in("escala_id",l);if(x&&x.length){const v=[...x].sort((j,w)=>{const S=(i||[]).find(y=>y.id===j.escala_id),b=(i||[]).find(y=>y.id===w.escala_id),N=m(f[S==null?void 0:S.departamento_id]),C=m(f[b==null?void 0:b.departamento_id]),P=N.includes("LOUVOR")||N.includes("MUSICA")?0:1,A=C.includes("LOUVOR")||C.includes("MUSICA")?0:1;if(P!==A)return P-A;const E=j.escala_id===e?0:1,T=w.escala_id===e?0:1;return E!==T?E-T:String(j.created_at||"").localeCompare(String(w.created_at||""))});t=v[0].escala_id||t,n=v[0].id||null}}catch(s){}return{escalaId:t,setlistId:n}},'''
if js.count(a)!=1: raise SystemExit('anchor hG inválido')
js=js.replace(a,helper+a,1)
old=r'''hG=({escalaId:e,canEdit:t})=>{const{igrejaId:n}=Bt(),[s,a]=h.useState(null),[i,l]=h.useState([]),[c,d]=h.useState([]),[f,m]=h.useState(""),[g,x]=h.useState(!1),[v,j]=h.useState(!0),w=async()=>{var E;j(!0);const{data:P}=await I.from("setlists").select("id").eq("escala_id",e).limit(1),A=((E=P==null?void 0:P[0])==null?void 0:E.id)??null;if(a(A),A){const{data:T}=await I.from("setlist_itens").select("*, musicas(*)").eq("setlist_id",A).order("ordem");l(T||[])}else l([]);j(!1)};h.useEffect(()=>{w()},[e]),'''
new=r'''hG=({escalaId:e,canEdit:t})=>{const{igrejaId:n}=Bt(),[s,a]=h.useState(null),[i,l]=h.useState([]),[c,d]=h.useState([]),[f,m]=h.useState(""),[g,x]=h.useState(!1),[v,j]=h.useState(!0),[u,o]=h.useState(e),w=async()=>{j(!0);const P=await gR1439(e),A=P.setlistId||null;o(P.escalaId||e);if(a(A),A){const{data:T}=await I.from("setlist_itens").select("*, musicas(*)").eq("setlist_id",A).order("ordem");l(T||[])}else l([]);j(!1)};h.useEffect(()=>{w()},[e]),'''
if old not in js: raise SystemExit('loader repertório não encontrado')
js=js.replace(old,new,1)
js=js.replace('I.from("setlists").insert({escala_id:e,nome:"Repertório do culto"})','I.from("setlists").insert({escala_id:u||e,nome:"Repertório do culto"})',1)
st=js.find('printSongs=async()=>{try{');en=js.find('},G=async()=>',st)
if st<0 or en<0: raise SystemExit('printSongs não encontrado')
np=r'''printSongs=async()=>{try{const pe=await gR1439(l.id),q=pe.setlistId;if(!q)return[];const{data:oe,error:xe}=await I.from("setlist_itens").select("id, setlist_id, musica_id, ordem, musicas(id, titulo, artista, tom)").eq("setlist_id",q).order("ordem");if(xe)throw xe;const ge=[],ke=new Set;(oe||[]).forEach((Fe,ae)=>{const ve=Fe.musicas;if(!ve)return;const De=Fe.musica_id||ve.id||`${ve.titulo||""}|${ve.artista||""}|${ve.tom||""}`;ke.has(De)||(ke.add(De),ge.push({titulo:ve.titulo||"Música",artista:ve.artista||"",tom:ve.tom||"",ordem:Number(Fe.ordem)||ae+1}))});return ge.sort((Fe,ae)=>Fe.ordem-ae.ordem)}catch(pe){return[]}}'''
js=js[:st]+np+js[en+1:]
needle='I.from("setlists").select("id").eq("escala_id",e)'
if js.count(needle)!=1: raise SystemExit('lookup voluntário inesperado')
js=js.replace(needle,'(async()=>{const H=await gR1439(e);return{data:H.setlistId?[{id:H.setlistId}]:[]}})()',1)
asset.write_text(js,encoding='utf-8')
(root/'VERSION').write_text('1.4.39\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.39.md').write_text('''# Escala de Propósito v1.4.39

- Corrige a fonte oficial do repertório para ser única por igreja + data + culto.
- Bancos antigos podem conter setlists duplicados em departamentos diferentes; o setlist de Louvor/Música passa a ser a fonte oficial quando existir.
- Painel, página do voluntário, WhatsApp, notificação inicial, impressão e PDF passam a usar a mesma lista oficial.
- Ao abrir outro departamento da mesma escala, o editor aponta para o mesmo repertório oficial e evita novos repertórios divergentes.
- Registros legados duplicados não são apagados automaticamente, evitando perda de dados.
- Não altera confirmação/recusa nem o transporte do WhatsApp.
''',encoding='utf-8')
