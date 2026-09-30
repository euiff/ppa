<?php
declare(strict_types=1);

require_once __DIR__.'/bootstrap.php';

$caller=require_auth();
$ctx=user_context();
$req=input_json();

$name=trim((string)($req['name']??''));
$args=is_array($req['body']??null)?$req['body']:[];

function fn_roles_ok(array $ctx,array $allowed): bool {
    return in_array((string)($ctx['role']??''),$allowed,true);
}
function fn_require_roles(array $ctx,array $allowed,string $message='Sem permissão para esta ação.'): void {
    if(!fn_roles_ok($ctx,$allowed)) out(['data'=>null,'error'=>['message'=>$message]],403);
}
function fn_table(string $name): bool { return table_exists($name); }
function fn_column(string $table,string $column): bool {
    static $cache=[];
    $k=$table.'.'.$column;
    if(array_key_exists($k,$cache)) return $cache[$k];
    try{
        $q=db()->prepare('SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=? AND column_name=?');
        $q->execute([$table,$column]);
        return $cache[$k]=(int)$q->fetchColumn()>0;
    }catch(Throwable $e){ return $cache[$k]=false; }
}
function fn_target_profile(string $uid): ?array {
    if($uid===''||!fn_table('profiles')) return null;
    $q=db()->prepare('SELECT * FROM profiles WHERE BINARY id=BINARY ? LIMIT 1');
    $q->execute([$uid]);
    $r=$q->fetch(PDO::FETCH_ASSOC);
    return $r?:null;
}
function fn_target_user(string $uid): ?array {
    if($uid===''||!fn_table('users')) return null;
    $q=db()->prepare('SELECT * FROM users WHERE BINARY id=BINARY ? LIMIT 1');
    $q->execute([$uid]);
    $r=$q->fetch(PDO::FETCH_ASSOC);
    return $r?:null;
}
function fn_target_roles(string $uid): array {
    if($uid===''||!fn_table('user_roles')) return [];
    $q=db()->prepare('SELECT role FROM user_roles WHERE BINARY user_id=BINARY ? ORDER BY role');
    $q->execute([$uid]);
    return array_values(array_unique(array_map('strval',$q->fetchAll(PDO::FETCH_COLUMN)?:[])));
}
function fn_same_church_or_master(array $ctx,string $uid): void {
    if(($ctx['role']??'')==='master') return;
    $p=fn_target_profile($uid);
    $actorChurch=(string)($ctx['igreja_id']??'');
    $targetChurch=(string)($p['igreja_id']??'');
    if(!$p||$actorChurch===''||$targetChurch===''||$actorChurch!==$targetChurch){
        out(['data'=>null,'error'=>['message'=>'Este usuário não pertence à sua igreja.']],403);
    }
}
function fn_delete_where_if_exists(string $table,string $column,string $uid): int {
    if(!fn_table($table)||!fn_column($table,$column)) return 0;
    $q=db()->prepare("DELETE FROM `$table` WHERE BINARY `$column`=BINARY ?");
    $q->execute([$uid]);
    return $q->rowCount();
}
function fn_ensure_cron_key(): string {
    global $config;
    $key=trim((string)($config['cron_key']??''));
    if($key!=='') return $key;
    $key=bin2hex(random_bytes(32));
    $config['cron_key']=$key;
    $file=__DIR__.'/config.local.php';
    $body="<?php\nreturn ".var_export($config,true).";\n";
    if(file_put_contents($file,$body,LOCK_EX)===false){
        throw new RuntimeException('Não foi possível salvar a chave do CRON.');
    }
    @chmod($file,0640);
    return $key;
}
function fn_base_url(): string {
    $https=(!empty($_SERVER['HTTPS'])&&strtolower((string)$_SERVER['HTTPS'])!=='off')
        || (string)($_SERVER['HTTP_X_FORWARDED_PROTO']??'')==='https';
    $host=trim((string)($_SERVER['HTTP_HOST']??'escaladeproposito.com.br'));
    if($host==='')$host='escaladeproposito.com.br';
    return ($https?'https':'http').'://'.$host;
}
function fn_system_cron_config(array $ctx): never {
    fn_require_roles($ctx,['master']);
    $key=fn_ensure_cron_key();
    $url=fn_base_url().'/api/cron-runner.php?key='.rawurlencode($key);
    $command="curl -fsS ".escapeshellarg($url)." >/dev/null 2>&1";
    out(['data'=>[
        'success'=>true,
        'url'=>$url,
        'command'=>$command,
        'full_line'=>'* * * * * '.$command,
        'schedule'=>'* * * * *'
    ],'error'=>null]);
}
function fn_validate_email(string $email): string {
    $email=strtolower(trim($email));
    if($email===''||!filter_var($email,FILTER_VALIDATE_EMAIL)) throw new RuntimeException('Informe um e-mail válido.');
    return $email;
}
function fn_validate_church(string $churchId): array {
    if($churchId==='') throw new RuntimeException('Igreja não informada.');
    $q=db()->prepare('SELECT * FROM igrejas WHERE BINARY id=BINARY ? LIMIT 1');
    $q->execute([$churchId]);
    $r=$q->fetch(PDO::FETCH_ASSOC);
    if(!$r) throw new RuntimeException('Igreja não encontrada.');
    return $r;
}
function fn_set_single_role(string $uid,string $role,bool $preserveMaster=false): void {
    $allowed=['master','admin','lider','secretaria','voluntario'];
    if(!in_array($role,$allowed,true)) throw new RuntimeException('Cargo inválido.');
    if(!$preserveMaster){
        db()->prepare("DELETE FROM user_roles WHERE BINARY user_id=BINARY ? AND role IN ('master','admin','lider','secretaria','voluntario')")->execute([$uid]);
    }else{
        db()->prepare("DELETE FROM user_roles WHERE BINARY user_id=BINARY ? AND role IN ('admin','lider','secretaria','voluntario')")->execute([$uid]);
    }
    $q=db()->prepare('SELECT COUNT(*) FROM user_roles WHERE BINARY user_id=BINARY ? AND role=?');
    $q->execute([$uid,$role]);
    if((int)$q->fetchColumn()===0){
        db()->prepare('INSERT INTO user_roles(id,user_id,role) VALUES(?,?,?)')->execute([uuid4(),$uid,$role]);
    }
}
function fn_update_metadata(string $uid,array $changes): void {
    $u=fn_target_user($uid);
    if(!$u||!fn_column('users','user_metadata')) return;
    $md=json_decode((string)($u['user_metadata']??''),true);
    if(!is_array($md))$md=[];
    foreach($changes as$k=>$v)$md[$k]=$v;
    db()->prepare('UPDATE users SET user_metadata=?,updated_at=NOW() WHERE BINARY id=BINARY ?')
        ->execute([json_encode($md,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),$uid]);
}
function fn_create_user(array $ctx,array $data): never {
    fn_require_roles($ctx,['master','admin','lider']);

    $email=fn_validate_email((string)($data['email']??''));
    $password=(string)($data['password']??'');
    $nome=trim((string)($data['nome']??''));
    $whatsapp=trim((string)($data['whatsapp']??''));
    $churchId=trim((string)($data['igreja_id']??''));
    $role=trim((string)($data['role']??'voluntario'));
    $deptId=trim((string)($data['departamento_id']??''));

    if($nome==='') throw new RuntimeException('Informe o nome do usuário.');
    if(strlen($password)<6) throw new RuntimeException('A senha deve ter pelo menos 6 caracteres.');
    $church=fn_validate_church($churchId);

    $actorRole=(string)($ctx['role']??'');
    if($actorRole!=='master'){
        if((string)($ctx['igreja_id']??'')!==$churchId) throw new RuntimeException('Você só pode cadastrar usuários na sua própria igreja.');
        if($actorRole==='lider'&&$role!=='voluntario') throw new RuntimeException('Líder só pode cadastrar voluntários.');
        if($actorRole==='admin'&&!in_array($role,['lider','secretaria','voluntario'],true)) throw new RuntimeException('Pastor não pode criar este cargo.');
    }else{
        if(!in_array($role,['admin','lider','secretaria','voluntario'],true)) throw new RuntimeException('Cargo inválido.');
    }

    $chk=db()->prepare('SELECT id FROM users WHERE LOWER(email)=LOWER(?) LIMIT 1');
    $chk->execute([$email]);
    if($chk->fetchColumn()) throw new RuntimeException('Este e-mail já possui cadastro. Use "Usuário existente".');

    $uid=uuid4();
    $pdo=db();
    $pdo->beginTransaction();
    try{
        $md=['nome'=>$nome,'whatsapp'=>$whatsapp?:null,'igreja_id'=>$churchId,'role'=>$role];
        $pdo->prepare('INSERT INTO users(id,email,password_hash,user_metadata,email_confirmed,created_at,updated_at) VALUES(?,?,?,?,1,NOW(),NOW())')
            ->execute([$uid,$email,password_hash($password,PASSWORD_DEFAULT),json_encode($md,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)]);

        $pdo->prepare('INSERT INTO profiles(id,nome,whatsapp,igreja_id,created_at,updated_at) VALUES(?,?,?,?,NOW(),NOW())')
            ->execute([$uid,$nome,$whatsapp!==''?$whatsapp:null,$churchId]);

        $pdo->prepare('INSERT INTO user_roles(id,user_id,role) VALUES(?,?,?)')
            ->execute([uuid4(),$uid,$role]);

        if($deptId!==''&&fn_table('departamento_voluntarios')){
            $q=$pdo->prepare('SELECT id FROM departamentos WHERE BINARY id=BINARY ? AND BINARY igreja_id=BINARY ? LIMIT 1');
            $q->execute([$deptId,$churchId]);
            if($q->fetchColumn()){
                $pdo->prepare('INSERT INTO departamento_voluntarios(departamento_id,voluntario_id) VALUES(?,?)')
                    ->execute([$deptId,$uid]);
            }
        }

        $pdo->commit();
        audit((string)($ctx['id']??''),'admin_create_user','users:'.$uid,['email'=>$email,'igreja_id'=>$churchId,'role'=>$role],'info');

        out(['data'=>[
            'success'=>true,
            'user'=>[
                'id'=>$uid,'email'=>$email,'nome'=>$nome,'whatsapp'=>$whatsapp?:null,
                'igreja_id'=>$churchId,'igreja_nome'=>$church['nome']??null,'role'=>$role
            ]
        ],'error'=>null],201);
    }catch(Throwable $e){
        if($pdo->inTransaction())$pdo->rollBack();
        throw $e;
    }
}
function fn_search_users(array $ctx,array $data): never {
    fn_require_roles($ctx,['master']);
    $term=trim((string)($data['term']??''));
    $like='%'.$term.'%';
    $sql="SELECT p.id,p.nome,p.whatsapp,p.igreja_id,u.email,i.nome igreja_nome,
          (SELECT GROUP_CONCAT(DISTINCT ur.role ORDER BY ur.role SEPARATOR ',') FROM user_roles ur WHERE BINARY ur.user_id=BINARY p.id) roles
          FROM profiles p
          LEFT JOIN users u ON BINARY u.id=BINARY p.id
          LEFT JOIN igrejas i ON BINARY i.id=BINARY p.igreja_id
          WHERE NOT EXISTS(SELECT 1 FROM user_roles rm WHERE BINARY rm.user_id=BINARY p.id AND rm.role='master')
            AND (?='' OR p.nome LIKE ? OR u.email LIKE ? OR p.whatsapp LIKE ?)
          ORDER BY COALESCE(p.nome,''),u.email
          LIMIT 40";
    $q=db()->prepare($sql);
    $q->execute([$term,$like,$like,$like]);
    $rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];
    foreach($rows as&$r){
        $roles=array_values(array_filter(explode(',',(string)($r['roles']??''))));
        $r['roles']=$roles;
        $r['role']=in_array('admin',$roles,true)?'admin':(in_array('lider',$roles,true)?'lider':(in_array('secretaria',$roles,true)?'secretaria':'voluntario'));
    }
    unset($r);
    out(['data'=>['users'=>$rows],'error'=>null]);
}
function fn_promote_pastor(array $ctx,string $uid,array $data): never {
    fn_require_roles($ctx,['master']);
    if($uid==='') throw new RuntimeException('Usuário não informado.');
    $profile=fn_target_profile($uid);
    if(!$profile) throw new RuntimeException('Usuário não encontrado.');
    if(in_array('master',fn_target_roles($uid),true)) throw new RuntimeException('Uma conta Master não pode ser transformada em Pastor.');

    $churchId=trim((string)($data['igreja_id']??''));
    $church=fn_validate_church($churchId);

    $pdo=db();
    $pdo->beginTransaction();
    try{
        if(fn_table('departamentos')&&fn_column('departamentos','lider_id')){
            $pdo->prepare('UPDATE departamentos SET lider_id=NULL WHERE BINARY lider_id=BINARY ?')->execute([$uid]);
        }
        fn_delete_where_if_exists('departamento_voluntarios','voluntario_id',$uid);
        fn_delete_where_if_exists('voluntario_tags','voluntario_id',$uid);
        fn_delete_where_if_exists('volunteer_locations','user_id',$uid);
        fn_delete_where_if_exists('whatsapp_pending_sessions','voluntario_id',$uid);

        if(fn_table('escala_itens')&&fn_table('escalas')){
            $q=$pdo->prepare("DELETE ei FROM escala_itens ei
                              JOIN escalas e ON BINARY e.id=BINARY ei.escala_id
                              WHERE BINARY ei.voluntario_id=BINARY ?
                                AND (e.igreja_id IS NULL OR BINARY e.igreja_id<>BINARY ?)");
            $q->execute([$uid,$churchId]);
        }

        $pdo->prepare('UPDATE profiles SET igreja_id=?,updated_at=NOW() WHERE BINARY id=BINARY ?')->execute([$churchId,$uid]);
        fn_set_single_role($uid,'admin',false);
        fn_update_metadata($uid,['igreja_id'=>$churchId,'role'=>'admin']);

        $pdo->commit();
        audit((string)($ctx['id']??''),'master_promote_pastor','users:'.$uid,['igreja_id'=>$churchId],'warning');

        out(['data'=>[
            'success'=>true,
            'user'=>['id'=>$uid,'nome'=>$profile['nome']??null,'igreja_id'=>$churchId,'igreja_nome'=>$church['nome']??null,'role'=>'admin']
        ],'error'=>null]);
    }catch(Throwable $e){
        if($pdo->inTransaction())$pdo->rollBack();
        throw $e;
    }
}
function fn_cleanup_master(array $ctx): never {
    fn_require_roles($ctx,['master']);
    $uid=(string)($ctx['id']??'');
    if($uid!==''&&fn_table('profiles')){
        db()->prepare('UPDATE profiles SET igreja_id=NULL,updated_at=NOW() WHERE BINARY id=BINARY ?')->execute([$uid]);
        fn_update_metadata($uid,['igreja_id'=>null,'role'=>'master']);
    }
    out(['data'=>['success'=>true],'error'=>null]);
}
function fn_get_user_admin_data(array $ctx,string $uid): never {
    fn_require_roles($ctx,['master','admin','lider']);
    if($uid==='') throw new RuntimeException('Usuário não informado.');
    fn_same_church_or_master($ctx,$uid);
    $u=fn_target_user($uid);
    $p=fn_target_profile($uid);
    if(!$u||!$p) throw new RuntimeException('Usuário não encontrado.');
    $roles=fn_target_roles($uid);
    out(['data'=>['user'=>[
        'id'=>$uid,'email'=>$u['email']??null,'nome'=>$p['nome']??null,'whatsapp'=>$p['whatsapp']??null,
        'igreja_id'=>$p['igreja_id']??null,'roles'=>$roles,
        'role'=>in_array('master',$roles,true)?'master':(in_array('admin',$roles,true)?'admin':(in_array('secretaria',$roles,true)?'secretaria':(in_array('lider',$roles,true)?'lider':'voluntario')))
    ]],'error'=>null]);
}
function fn_update_email(array $ctx,string $uid,array $data): never {
    fn_require_roles($ctx,['master','admin','lider']);
    if($uid==='') throw new RuntimeException('Usuário não informado.');
    fn_same_church_or_master($ctx,$uid);
    $email=fn_validate_email((string)($data['email']??''));
    $q=db()->prepare('SELECT id FROM users WHERE LOWER(email)=LOWER(?) AND BINARY id<>BINARY ? LIMIT 1');
    $q->execute([$email,$uid]);
    if($q->fetchColumn()) throw new RuntimeException('Este e-mail já está sendo usado por outra conta.');
    $q=db()->prepare('UPDATE users SET email=?,updated_at=NOW() WHERE BINARY id=BINARY ?');
    $q->execute([$email,$uid]);
    if($q->rowCount()===0&&!fn_target_user($uid)) throw new RuntimeException('Usuário não encontrado.');
    audit((string)($ctx['id']??''),'admin_update_email','users:'.$uid,['email'=>$email],'info');
    out(['data'=>['success'=>true,'email'=>$email],'error'=>null]);
}
function fn_update_password(array $ctx,string $uid,array $data): never {
    fn_require_roles($ctx,['master','admin','lider']);
    if($uid==='') throw new RuntimeException('Usuário não informado.');
    fn_same_church_or_master($ctx,$uid);
    $password=(string)($data['password']??'');
    if(strlen($password)<6) throw new RuntimeException('A senha deve ter pelo menos 6 caracteres.');
    $q=db()->prepare('UPDATE users SET password_hash=?,updated_at=NOW() WHERE BINARY id=BINARY ?');
    $q->execute([password_hash($password,PASSWORD_DEFAULT),$uid]);
    if($q->rowCount()===0&&!fn_target_user($uid)) throw new RuntimeException('Usuário não encontrado.');
    audit((string)($ctx['id']??''),'admin_update_password','users:'.$uid,[],'warning');
    out(['data'=>['success'=>true],'error'=>null]);
}
function fn_update_profile(array $ctx,string $uid,array $data): never {
    fn_require_roles($ctx,['master','admin','lider']);
    if($uid==='') throw new RuntimeException('Usuário não informado.');
    fn_same_church_or_master($ctx,$uid);
    $nome=trim((string)($data['nome']??''));
    $whatsapp=array_key_exists('whatsapp',$data)?trim((string)$data['whatsapp']):null;
    if($nome==='') throw new RuntimeException('Nome é obrigatório.');
    db()->prepare('UPDATE profiles SET nome=?,whatsapp=?,updated_at=NOW() WHERE BINARY id=BINARY ?')
        ->execute([$nome,$whatsapp!==''?$whatsapp:null,$uid]);
    fn_update_metadata($uid,['nome'=>$nome,'whatsapp'=>$whatsapp!==''?$whatsapp:null]);
    out(['data'=>['success'=>true],'error'=>null]);
}
function fn_update_role(array $ctx,string $uid,array $data): never {
    fn_require_roles($ctx,['master','admin']);
    if($uid==='') throw new RuntimeException('Usuário não informado.');
    fn_same_church_or_master($ctx,$uid);
    $role=trim((string)($data['role']??''));
    if($role==='master') throw new RuntimeException('O cargo Master não pode ser atribuído por esta tela.');
    if(!in_array($role,['admin','lider','secretaria','voluntario'],true)) throw new RuntimeException('Cargo inválido.');
    if(($ctx['role']??'')==='admin'&&$role==='admin'&&$uid!==(string)($ctx['id']??'')){
        throw new RuntimeException('Somente o Master pode transformar outro usuário em Pastor.');
    }
    if(in_array('master',fn_target_roles($uid),true)) throw new RuntimeException('Não é permitido alterar o cargo de uma conta Master.');
    fn_set_single_role($uid,$role,false);
    fn_update_metadata($uid,['role'=>$role]);
    if($role!=='lider'&&fn_table('departamentos')&&fn_column('departamentos','lider_id')){
        db()->prepare('UPDATE departamentos SET lider_id=NULL WHERE BINARY lider_id=BINARY ?')->execute([$uid]);
    }
    out(['data'=>['success'=>true,'role'=>$role],'error'=>null]);
}
function fn_admin_update_user(array $ctx,array $args): never {
    $action=trim((string)($args['action']??''));
    $uid=trim((string)($args['userId']??$args['user_id']??$args['id']??''));
    $data=is_array($args['data']??null)?$args['data']:[];

    switch($action){
        case 'create_user': fn_create_user($ctx,$data);
        case 'search_users': fn_search_users($ctx,$data);
        case 'promote_pastor': fn_promote_pastor($ctx,$uid,$data);
        case 'cleanup_legacy_master_church': fn_cleanup_master($ctx);
        case 'get_user_admin_data': fn_get_user_admin_data($ctx,$uid);
        case 'update_email': fn_update_email($ctx,$uid,$data);
        case 'update_password': fn_update_password($ctx,$uid,$data);
        case 'update_profile': fn_update_profile($ctx,$uid,$data);
        case 'update_role': fn_update_role($ctx,$uid,$data);
        default:
            throw new RuntimeException('Ação de usuário não reconhecida: '.($action?:'(vazia)'));
    }
}

try{
    switch($name){
        case 'system-cron-config':
            fn_system_cron_config($ctx);

        case 'admin-update-user':
            fn_admin_update_user($ctx,$args);

        case 'notify-leader':
            out(['data'=>null,'error'=>['message'=>'Use o módulo específico de notificação do líder.']],400);

        case 'send-whatsapp':
        case 'send-post-quiz':
        case 'test-whatsapp':
        case 'send-whatsapp-otp':
        case 'verify-whatsapp-otp':
        case 'buscar-musica':
            out(['data'=>null,'error'=>['message'=>'Função '.$name.' ainda não está habilitada neste clone.']],400);

        default:
            out(['data'=>null,'error'=>['message'=>'Função interna não reconhecida: '.($name?:'(vazia)')]],400);
    }
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
