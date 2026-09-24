from pathlib import Path
root=Path('pkg')

def rep(s,old,new,label):
    c=s.count(old)
    if c!=1: raise SystemExit(f'{label}: {c}')
    return s.replace(old,new,1)

p=root/'api'/'ministerial-hub.php'
s=p.read_text(encoding='utf-8')
anchor="function mh_table(string $t): bool {static $c=[];if(array_key_exists($t,$c))return$c[$t];try{$q=db()->prepare(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=?\");$q->execute([$t]);return$c[$t]=(int)$q->fetchColumn()>0;}catch(Throwable $e){return$c[$t]=false;}}"
helper=anchor+"\nfunction mh_rep_key(string $name): string {$x=$name;if(function_exists('iconv')){$y=@iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$x);if(is_string($y)&&$y!=='')$x=$y;}return strtoupper($x);}"
s=rep(s,anchor,helper,'mh helper')
old="$songs=[];if(mh_table('setlists')&&mh_table('setlist_itens')){$q=db()->prepare(\"SELECT si.ordem,si.musica_id,m.titulo,m.artista,m.tom,m.link_youtube,m.link_spotify,m.link_cifra FROM setlists s JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id JOIN musicas m ON BINARY m.id=BINARY si.musica_id WHERE s.escala_id IN ($ph) ORDER BY si.ordem,m.titulo\");$q->execute($ids);$seen=[];foreach($q->fetchAll(PDO::FETCH_ASSOC)?:[] as$r){$k=$r['musica_id'];if(isset($seen[$k]))continue;$seen[$k]=1;$songs[]=$r;}}"
new="$songs=[];$repertoireSetlistId=null;if(mh_table('setlists')&&mh_table('setlist_itens')){$ra=[$ig,$date];$rw=\"BINARY e2.igreja_id=BINARY ? AND e2.data=?\";if($culto===null||$culto==='')$rw.=\" AND e2.culto_id IS NULL\";else{$rw.=\" AND BINARY e2.culto_id=BINARY ?\";$ra[]=$culto;}$q=db()->prepare(\"SELECT s.id setlist_id,s.escala_id,d.nome departamento_nome,s.created_at,COUNT(si.id) qtd FROM setlists s JOIN escalas e2 ON BINARY e2.id=BINARY s.escala_id LEFT JOIN departamentos d ON BINARY d.id=BINARY e2.departamento_id JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id WHERE $rw GROUP BY s.id,s.escala_id,d.nome,s.created_at HAVING qtd>0\");$q->execute($ra);$cand=$q->fetchAll(PDO::FETCH_ASSOC)?:[];if($cand){$baseEsc=(string)($scales[0]['id']??'');usort($cand,static function($a,$b)use($baseEsc){$ka=mh_rep_key((string)($a['departamento_nome']??''));$kb=mh_rep_key((string)($b['departamento_nome']??''));$pa=(strpos($ka,'LOUVOR')!==false||strpos($ka,'MUSICA')!==false)?0:1;$pb=(strpos($kb,'LOUVOR')!==false||strpos($kb,'MUSICA')!==false)?0:1;if($pa!==$pb)return$pa<=>$pb;$ea=((string)($a['escala_id']??'')===$baseEsc)?0:1;$eb=((string)($b['escala_id']??'')===$baseEsc)?0:1;if($ea!==$eb)return$ea<=>$eb;return strcmp((string)($a['created_at']??''),(string)($b['created_at']??''));});$repertoireSetlistId=(string)($cand[0]['setlist_id']??'');if($repertoireSetlistId!==''){$q=db()->prepare(\"SELECT si.ordem,si.musica_id,m.titulo,m.artista,m.tom,m.link_youtube,m.link_spotify,m.link_cifra FROM setlist_itens si JOIN musicas m ON BINARY m.id=BINARY si.musica_id WHERE BINARY si.setlist_id=BINARY ? ORDER BY si.ordem ASC,m.titulo ASC\");$q->execute([$repertoireSetlistId]);$seen=[];foreach($q->fetchAll(PDO::FETCH_ASSOC)?:[] as$r){$k=(string)($r['musica_id']??'');if($k===''||isset($seen[$k]))continue;$seen[$k]=1;$songs[]=$r;}}}}"
s=rep(s,old,new,'service repertoire query')
s=rep(s,"'summary'=>$summary,'departments'=>$scales,'songs'=>$songs,'swaps'=>$swaps","'summary'=>$summary,'departments'=>$scales,'songs'=>$songs,'repertoire_setlist_id'=>$repertoireSetlistId,'swaps'=>$swaps",'service return setlist')
p.write_text(s,encoding='utf-8')

asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')
old='N=async P=>{const{error:A}=await I.from("setlist_itens").delete().eq("id",P.id);if(A){V.error("Erro ao remover");return}w()},C=async(P,A)=>{'
new='N=async P=>{const A=P.musica_id;let E=null;try{const{data:T}=await I.from("escalas").select("id,data,culto_id,igreja_id").eq("id",u||e).maybeSingle();if(T){let D=I.from("escalas").select("id").eq("igreja_id",T.igreja_id).eq("data",T.data);T.culto_id?D=D.eq("culto_id",T.culto_id):D=D.is("culto_id",null);const{data:F}=await D,Z=(F||[]).map(K=>K.id).filter(Boolean);if(Z.length){const{data:W}=await I.from("setlists").select("id").in("escala_id",Z),K=(W||[]).map(J=>J.id).filter(Boolean);K.length&&A&&(E=(await I.from("setlist_itens").delete().in("setlist_id",K).eq("musica_id",A)).error)}}}else E=(await I.from("setlist_itens").delete().eq("id",P.id)).error}catch(T){E=T}if(E){V.error("Erro ao remover a música do repertório");return}V.success("Música removida do repertório deste culto"),w()},C=async(P,A)=>{'
s=rep(s,old,new,'frontend remove repertoire')
asset.write_text(s,encoding='utf-8')

(root/'VERSION').write_text('1.4.58\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.58.md').write_text('''# Escala de Propósito v1.4.58 — Repertório único e sincronizado

- Corrige a **Página do Culto**, que estava juntando músicas de setlists antigos de vários departamentos da mesma escala e podia mostrar músicas já removidas.
- A Página do Culto passa a selecionar **um único repertório principal**, usando a mesma regra do WhatsApp: prioriza departamento **Louvor/Música** e usa somente os itens daquele setlist.
- **Imprimir** e **Baixar PDF** pela Página do Culto usam esse mesmo repertório atual; não incluem mais músicas antigas de repertórios paralelos.
- Ao remover uma música pela **Escala Completa**, a remoção é propagada para todos os setlists ligados à mesma igreja + data + culto, eliminando a “memória” daquela música em repertórios antigos paralelos.
- Escala Completa, Página do Culto, impressão/PDF e WhatsApp passam a ficar consistentes para o repertório atual.
- Não apaga músicas do cadastro geral da igreja; remove apenas a música do repertório daquele culto/data.
''',encoding='utf-8')
