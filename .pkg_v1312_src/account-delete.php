<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';

$req=input_json();
if(strtoupper((string)($req['confirm']??''))!=='EXCLUIR') out(['error'=>['message'=>'Confirmação inválida']],400);
$u=current_user();
$password=(string)($req['password']??'');
$full=null;
if($u){$st=db()->prepare('SELECT * FROM users WHERE id=? LIMIT 1');$st->execute([$u['id']]);$full=$st->fetch();}
else{
  $email=strtolower(trim((string)($req['email']??'')));
  if(!filter_var($email,FILTER_VALIDATE_EMAIL)) out(['error'=>['message'=>'Informe o e-mail da conta']],400);
  $st=db()->prepare('SELECT * FROM users WHERE email=? LIMIT 1');$st->execute([$email]);$full=$st->fetch();
  if($full)$u=['id'=>$full['id']];
}
if(!$full || !password_verify($password,(string)$full['password_hash'])) out(['error'=>['message'=>'E-mail ou senha incorretos']],400);
$uid=(string)$u['id'];
$pdo=db();
function t_exists(PDO $pdo,string $t):bool{$q=$pdo->prepare('SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=?');$q->execute([$t]);return (int)$q->fetchColumn()>0;}
function c_exists(PDO $pdo,string $t,string $c):bool{$q=$pdo->prepare('SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? AND COLUMN_NAME=?');$q->execute([$t,$c]);return (int)$q->fetchColumn()>0;}
function del_where(PDO $pdo,string $t,string $col,string $uid):void{if(t_exists($pdo,$t)&&c_exists($pdo,$t,$col)){$q=$pdo->prepare("DELETE FROM `$t` WHERE `$col`=?");$q->execute([$uid]);}}
function null_where(PDO $pdo,string $t,string $col,string $uid):void{if(t_exists($pdo,$t)&&c_exists($pdo,$t,$col)){$q=$pdo->prepare("UPDATE `$t` SET `$col`=NULL WHERE `$col`=?");$q->execute([$uid]);}}
try{
  $pdo->beginTransaction();
  $p=$pdo->prepare('SELECT igreja_id,whatsapp FROM profiles WHERE id=? LIMIT 1');$p->execute([$uid]);$profile=$p->fetch()?:[];
  $igreja=$profile['igreja_id']??null;$phone=preg_replace('/\D+/','',(string)($profile['whatsapp']??''));
  // Retira referências operacionais e dados pessoais do usuário.
  foreach(['user_sessions'=>'user_id','password_resets'=>'user_id','user_roles'=>'user_id','departamento_voluntarios'=>'voluntario_id','disponibilidades'=>'voluntario_id','indisponibilidades'=>'voluntario_id','checkins'=>'voluntario_id','avaliacoes'=>'voluntario_id','quiz_pos_culto'=>'voluntario_id','voluntario_tags'=>'voluntario_id','volunteer_locations'=>'user_id','whatsapp_verification_codes'=>'user_id','justificativas_ausencia'=>'voluntario_id'] as $t=>$c) del_where($pdo,$t,$c,$uid);
  // Conteúdo diretamente associado à participação do usuário.
  if(t_exists($pdo,'escala_itens')){ $q=$pdo->prepare('SELECT id FROM escala_itens WHERE voluntario_id=?');$q->execute([$uid]);$ids=$q->fetchAll(PDO::FETCH_COLUMN); if($ids && t_exists($pdo,'whatsapp_send_jobs')){foreach(array_chunk($ids,100) as $chunk){$ph=implode(',',array_fill(0,count($chunk),'?'));$d=$pdo->prepare("DELETE FROM whatsapp_send_jobs WHERE escala_item_id IN ($ph)");$d->execute($chunk);}} $d=$pdo->prepare('DELETE FROM escala_itens WHERE voluntario_id=?');$d->execute([$uid]); }
  if(t_exists($pdo,'trocas')){ $q=$pdo->prepare('DELETE FROM trocas WHERE solicitante_id=? OR substituto_id=?');$q->execute([$uid,$uid]); }
  if(t_exists($pdo,'whatsapp_swap_sessions')){ $q=$pdo->prepare('DELETE FROM whatsapp_swap_sessions WHERE leader_id=? OR voluntario_recusado_id=?');$q->execute([$uid,$uid]); }
  foreach(['whatsapp_confirmation_contexts','whatsapp_pending_sessions','whatsapp_pending_contexts'] as $t) if(t_exists($pdo,$t)){foreach(['voluntario_id','user_id'] as $c)if(c_exists($pdo,$t,$c)){del_where($pdo,$t,$c,$uid);break;}}
  del_where($pdo,'avisos','criado_por',$uid);
  del_where($pdo,'audit_logs','user_id',$uid);
  null_where($pdo,'departamentos','lider_id',$uid);
  null_where($pdo,'escalas','created_by',$uid);
  null_where($pdo,'evento_templates','created_by',$uid);
  null_where($pdo,'musicas','created_by',$uid);
  if(t_exists($pdo,'justificativas_ausencia')&&c_exists($pdo,'justificativas_ausencia','avaliado_por')) null_where($pdo,'justificativas_ausencia','avaliado_por',$uid);
  // Se criou a igreja, transfere a referência para outro admin/master quando possível; senão usa referência anônima sem PII.
  if(t_exists($pdo,'igrejas')&&c_exists($pdo,'igrejas','created_by')){
    $successor=null;
    if($igreja){$q=$pdo->prepare("SELECT p.id FROM profiles p JOIN user_roles r ON r.user_id=p.id WHERE p.igreja_id=? AND p.id<>? AND r.role IN ('master','admin') ORDER BY FIELD(r.role,'master','admin'),p.created_at LIMIT 1");$q->execute([$igreja,$uid]);$successor=$q->fetchColumn()?:null;}
    $q=$pdo->prepare('UPDATE igrejas SET created_by=? WHERE created_by=?');$q->execute([$successor?:'00000000-0000-4000-8000-000000000099',$uid]);
  }
  // Apaga registros de WhatsApp identificáveis pelo telefone da conta.
  if($phone!==''&&t_exists($pdo,'notification_logs')){$tail=substr($phone,-8);$q=$pdo->prepare('DELETE FROM notification_logs WHERE REPLACE(REPLACE(REPLACE(REPLACE(destinatario,"+","")," ",""),"-",""),"(","") LIKE ?');$q->execute(['%'.$tail]);}
  del_where($pdo,'profiles','id',$uid);
  del_where($pdo,'users','id',$uid);
  $pdo->commit();
  out(['ok'=>true,'deleted'=>true]);
}catch(Throwable $e){if($pdo->inTransaction())$pdo->rollBack();out(['error'=>['message'=>'Não foi possível concluir a exclusão da conta.','detail'=>$e->getMessage()]],500);}
