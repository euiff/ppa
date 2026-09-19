<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
require_once __DIR__.'/system_observer_v1423.php';
system_observer_v1423_register();
$caller=require_auth();$ctx=user_context();
if((string)($ctx['role']??'')!=='master')out(['data'=>null,'error'=>['message'=>'Somente o MASTER pode excluir escalas completas.']],403);

function mse_t(string $t): bool {static $c=[];if(array_key_exists($t,$c))return$c[$t];try{$q=db()->prepare("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=?");$q->execute([$t]);return$c[$t]=(int)$q->fetchColumn()>0;}catch(Throwable$e){return$c[$t]=false;}}
function mse_valid_date(string $d,string $label): string {if($d==='')return'';$x=DateTime::createFromFormat('Y-m-d',$d);if(!$x||$x->format('Y-m-d')!==$d)throw new RuntimeException($label.' inválida.');return$d;}
function mse_group_where(string $ig,string $date,?string $cultoId,array &$args,string $alias='e'): string {$args=[$ig,$date];$w="BINARY {$alias}.igreja_id=BINARY ? AND {$alias}.data=?";if($cultoId===null||$cultoId==='')$w.=" AND {$alias}.culto_id IS NULL";else{$w.=" AND BINARY {$alias}.culto_id=BINARY ?";$args[]=$cultoId;}return$w;}
function mse_one(string $ig,string $date,?string $cultoId): ?array {$a=[];$w=mse_group_where($ig,$date,$cultoId,$a);$sql="SELECT e.igreja_id,i.nome igreja_nome,e.data,e.culto_id,COALESCE(c.nome,'Escala sem culto') culto_nome,c.horario,COUNT(DISTINCT e.id) departamentos,COUNT(ei.id) itens,SUM(CASE WHEN e.status='publicado' THEN 1 ELSE 0 END) publicadas FROM escalas e LEFT JOIN igrejas i ON BINARY i.id=BINARY e.igreja_id LEFT JOIN cultos c ON BINARY c.id=BINARY e.culto_id LEFT JOIN escala_itens ei ON BINARY ei.escala_id=BINARY e.id WHERE {$w} GROUP BY e.igreja_id,i.nome,e.data,e.culto_id,c.nome,c.horario LIMIT 1";$q=db()->prepare($sql);$q->execute($a);$r=$q->fetch(PDO::FETCH_ASSOC);return$r?:null;}
function mse_list(array $b): array {$ig=trim((string)($b['igreja_id']??''));$from=mse_valid_date(trim((string)($b['from']??'')),'Data inicial');$to=mse_valid_date(trim((string)($b['to']??'')),'Data final');$where=['1=1'];$a=[];if($ig!==''){$where[]='BINARY e.igreja_id=BINARY ?';$a[]=$ig;}if($from!==''){$where[]='e.data>=?';$a[]=$from;}if($to!==''){$where[]='e.data<=?';$a[]=$to;}$sql="SELECT e.igreja_id,i.nome igreja_nome,e.data,e.culto_id,COALESCE(c.nome,'Escala sem culto') culto_nome,c.horario,COUNT(DISTINCT e.id) departamentos,COUNT(ei.id) itens,SUM(CASE WHEN e.status='publicado' THEN 1 ELSE 0 END) publicadas FROM escalas e LEFT JOIN igrejas i ON BINARY i.id=BINARY e.igreja_id LEFT JOIN cultos c ON BINARY c.id=BINARY e.culto_id LEFT JOIN escala_itens ei ON BINARY ei.escala_id=BINARY e.id WHERE ".implode(' AND ',$where)." GROUP BY e.igreja_id,i.nome,e.data,e.culto_id,c.nome,c.horario ORDER BY e.data DESC,COALESCE(c.horario,'') ASC,COALESCE(c.nome,'') ASC LIMIT 600";$q=db()->prepare($sql);$q->execute($a);return$q->fetchAll(PDO::FETCH_ASSOC)?:[];}
function mse_delq(string $sql,array $a,array &$o,string $key): void {$q=db()->prepare($sql);$q->execute($a);$o[$key]=($o[$key]??0)+$q->rowCount();}
function mse_delete_group(string $ig,string $date,?string $cultoId): array {$a=[];$w=mse_group_where($ig,$date,$cultoId,$a);$o=[];
 if(mse_t('sos_candidates')&&mse_t('sos_requests'))mse_delq("DELETE sc FROM sos_candidates sc JOIN sos_requests sr ON BINARY sr.id=BINARY sc.request_id JOIN escalas e ON BINARY e.id=BINARY sr.escala_id WHERE {$w}",$a,$o,'sos_candidates');
 if(mse_t('sos_requests'))mse_delq("DELETE sr FROM sos_requests sr JOIN escalas e ON BINARY e.id=BINARY sr.escala_id WHERE {$w}",$a,$o,'sos_requests');
 if(mse_t('whatsapp_confirmation_contexts'))mse_delq("DELETE x FROM whatsapp_confirmation_contexts x JOIN escalas e ON BINARY e.id=BINARY x.escala_id WHERE {$w}",$a,$o,'whatsapp_contexts');
 if(mse_t('whatsapp_scale_pdf_tokens'))mse_delq("DELETE x FROM whatsapp_scale_pdf_tokens x JOIN escalas e ON BINARY e.id=BINARY x.escala_id WHERE {$w}",$a,$o,'pdf_tokens');
 if(mse_t('whatsapp_swap_sessions'))mse_delq("DELETE x FROM whatsapp_swap_sessions x JOIN escala_itens ei ON BINARY ei.id=BINARY x.escala_item_id JOIN escalas e ON BINARY e.id=BINARY ei.escala_id WHERE {$w}",$a,$o,'whatsapp_swaps');
 if(mse_t('whatsapp_send_jobs'))mse_delq("DELETE x FROM whatsapp_send_jobs x JOIN escalas e ON BINARY e.id=BINARY x.escala_id WHERE {$w}",$a,$o,'whatsapp_jobs');
 if(mse_t('trocas'))mse_delq("DELETE x FROM trocas x JOIN escala_itens ei ON BINARY ei.id=BINARY x.escala_item_id JOIN escalas e ON BINARY e.id=BINARY ei.escala_id WHERE {$w}",$a,$o,'trocas');
 if(mse_t('setlist_itens')&&mse_t('setlists'))mse_delq("DELETE si FROM setlist_itens si JOIN setlists s ON BINARY s.id=BINARY si.setlist_id JOIN escalas e ON BINARY e.id=BINARY s.escala_id WHERE {$w}",$a,$o,'setlist_itens');
 foreach(['avaliacoes','quiz_pos_culto','justificativas_ausencia','checkins','setlists'] as $t)if(mse_t($t))mse_delq("DELETE x FROM `$t` x JOIN escalas e ON BINARY e.id=BINARY x.escala_id WHERE {$w}",$a,$o,$t);
 mse_delq("DELETE ei FROM escala_itens ei JOIN escalas e ON BINARY e.id=BINARY ei.escala_id WHERE {$w}",$a,$o,'itens');
 mse_delq("DELETE e FROM escalas e WHERE {$w}",$a,$o,'escalas');return$o;}

$b=$_SERVER['REQUEST_METHOD']==='POST'?input_json():$_GET;$action=(string)($b['action']??'list');
try{
 if($action==='list'){$churches=db()->query('SELECT id,nome FROM igrejas ORDER BY nome')->fetchAll(PDO::FETCH_ASSOC)?:[];out(['data'=>['churches'=>$churches,'scales'=>mse_list($b)],'error'=>null]);}
 if($action!=='delete')throw new RuntimeException('Ação inválida.');
 $ig=trim((string)($b['igreja_id']??''));$date=mse_valid_date(trim((string)($b['data']??'')),'Data da escala');$cultoRaw=$b['culto_id']??null;$cultoId=$cultoRaw===null||trim((string)$cultoRaw)===''?null:trim((string)$cultoRaw);
 if($ig===''||$date==='')throw new RuntimeException('Escala inválida.');$row=mse_one($ig,$date,$cultoId);if(!$row)throw new RuntimeException('A escala selecionada não existe mais. Atualize a lista.');
 if(trim((string)($b['confirmation']??''))!=='EXCLUIR')throw new RuntimeException('Digite EXCLUIR para confirmar a exclusão.');
 $pdo=db();$pdo->beginTransaction();try{$deleted=mse_delete_group($ig,$date,$cultoId);$pdo->commit();}catch(Throwable$e){if($pdo->inTransaction())$pdo->rollBack();throw$e;}
 try{audit((string)($caller['id']??''),'master_delete_complete_scale','escalas',['igreja_id'=>$ig,'igreja_nome'=>$row['igreja_nome']??null,'data'=>$date,'culto_id'=>$cultoId,'culto_nome'=>$row['culto_nome']??null,'deleted'=>$deleted],'warning');}catch(Throwable$e){}
 out(['data'=>['success'=>true,'scale'=>$row,'deleted'=>$deleted],'error'=>null]);
}catch(Throwable$e){out(['data'=>null,'error'=>['message'=>$e->getMessage()]],400);}
