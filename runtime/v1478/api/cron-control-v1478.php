<?php
declare(strict_types=1);

require __DIR__.'/bootstrap.php';

$caller=require_auth();
$ctx=user_context();
if((string)($ctx['role']??'')!=='master'){
    out(['data'=>null,'error'=>['message'=>'Somente o MASTER pode administrar o CRON do sistema.']],403);
}

const CR1478_BASE_URL='https://escaladeproposito.com.br';

function cr1478_cron_key(): string {
    global $config;
    $key=trim((string)($config['cron_key']??''));
    if($key!=='')return $key;

    $key=bin2hex(random_bytes(32));
    $config['cron_key']=$key;
    $file=__DIR__.'/config.local.php';
    $php="<?php\nreturn ".var_export($config,true).";\n";
    if(file_put_contents($file,$php,LOCK_EX)===false){
        throw new RuntimeException('Não foi possível salvar a chave do CRON em api/config.local.php.');
    }
    @chmod($file,0640);
    return $key;
}

function cr1478_command_data(): array {
    $key=cr1478_cron_key();
    $url=CR1478_BASE_URL.'/api/cron-runner.php?key='.rawurlencode($key);
    $command='/usr/bin/curl -fsS '.escapeshellarg($url).' >/dev/null 2>&1';
    return [
        'success'=>true,
        'url'=>$url,
        'command'=>$command,
        'full_line'=>'* * * * * '.$command,
        'schedule'=>'* * * * *',
        'base_url'=>CR1478_BASE_URL,
    ];
}

function cr1478_state(string $key): string {
    try{
        $q=db()->prepare("SELECT valor FROM api_config WHERE chave=? AND igreja_id IS NULL ORDER BY updated_at DESC LIMIT 1");
        $q->execute([$key]);
        return trim((string)($q->fetchColumn()?:''));
    }catch(Throwable $e){
        return '';
    }
}

function cr1478_exec_available(): bool {
    if(!function_exists('exec'))return false;
    $disabled=array_map('trim',explode(',',(string)ini_get('disable_functions')));
    return !in_array('exec',$disabled,true);
}

function cr1478_crontab_status(string $fullLine): array {
    if(!cr1478_exec_available()){
        return ['supported'=>false,'installed'=>false,'reason'=>'A hospedagem bloqueou a função exec do PHP.'];
    }

    $out=[];$code=0;
    @exec('command -v crontab 2>/dev/null',$out,$code);
    $bin=trim((string)($out[0]??''));
    if($code!==0||$bin===''){
        foreach(['/usr/bin/crontab','/bin/crontab'] as $candidate){
            if(is_executable($candidate)){$bin=$candidate;break;}
        }
    }
    if($bin===''){
        return ['supported'=>false,'installed'=>false,'reason'=>'Comando crontab não disponível para o usuário do site.'];
    }

    $lines=[];$listCode=0;
    @exec(escapeshellcmd($bin).' -l 2>/dev/null',$lines,$listCode);
    $installed=false;
    $oldDomain=false;
    foreach($lines as $line){
        if(str_contains($line,'/api/cron-runner.php')){
            if(str_contains($line,'escaladeproposito.com.br'))$installed=true;
            if(str_contains($line,'escala.isaacanthony.com.br'))$oldDomain=true;
        }
    }
    return [
        'supported'=>true,
        'installed'=>$installed,
        'old_domain_detected'=>$oldDomain,
        'binary'=>$bin,
        'entries'=>count($lines),
    ];
}

function cr1478_install_crontab(string $fullLine): array {
    $status=cr1478_crontab_status($fullLine);
    if(empty($status['supported']))return $status+['success'=>false];

    $bin=(string)$status['binary'];
    $lines=[];$listCode=0;
    @exec(escapeshellcmd($bin).' -l 2>/dev/null',$lines,$listCode);

    $new=[];
    foreach($lines as $line){
        $trim=trim($line);
        if($trim==='')continue;
        if(str_contains($line,'/api/cron-runner.php'))continue;
        if(str_contains($line,'Escala de Proposito CRON'))continue;
        $new[]=$line;
    }
    $new[]=$fullLine.' # Escala de Proposito CRON';

    $tmp=tempnam(sys_get_temp_dir(),'escala_cron_');
    if($tmp===false)throw new RuntimeException('Não foi possível criar arquivo temporário para o CRON.');
    file_put_contents($tmp,implode(PHP_EOL,$new).PHP_EOL,LOCK_EX);

    $installOut=[];$installCode=0;
    @exec(escapeshellcmd($bin).' '.escapeshellarg($tmp).' 2>&1',$installOut,$installCode);
    @unlink($tmp);

    $after=cr1478_crontab_status($fullLine);
    $ok=$installCode===0&&!empty($after['installed']);

    return [
        'success'=>$ok,
        'supported'=>true,
        'installed'=>!empty($after['installed']),
        'old_domain_removed'=>!empty($status['old_domain_detected']),
        'install_code'=>$installCode,
        'output'=>implode("\n",$installOut),
        'message'=>$ok
            ?'CRON instalado/atualizado para escaladeproposito.com.br e execução a cada minuto.'
            :'A hospedagem não permitiu atualizar o crontab automaticamente. Use o comando exibido no painel.',
    ];
}

function cr1478_test_run(): array {
    require_once __DIR__.'/system_observer_v1423.php';
    require_once __DIR__.'/timezone_v133.php';
    require_once __DIR__.'/whatsapp_lib.php';
    require_once __DIR__.'/automation_lib.php';
    require_once __DIR__.'/automation_v130.php';
    require_once __DIR__.'/updater_lib.php';

    if(function_exists('system_observer_v1423_register'))system_observer_v1423_register();
    if(function_exists('v133_apply_timezone'))v133_apply_timezone(null);

    $automation=v130_run_all();
    $update=['checked'=>false,'installed'=>false,'reason'=>'automation_failed'];
    if(!empty($automation['ok'])){
        try{
            $update=updater_maybe_auto_install();
        }catch(Throwable $e){
            $update=['checked'=>true,'installed'=>false,'error'=>$e->getMessage()];
        }
    }

    return [
        'success'=>!empty($automation['ok']),
        'automation'=>$automation,
        'update'=>$update,
        'ran_at'=>date('Y-m-d H:i:s'),
    ];
}

try{
    $action=trim((string)($_GET['action']??$_POST['action']??'config'));
    $cmd=cr1478_command_data();

    if($action==='config'){
        $summaryRaw=cr1478_state('automation_last_summary');
        $summary=json_decode($summaryRaw,true);
        if(!is_array($summary))$summary=[];
        $cmd['last_run']=cr1478_state('automation_last_run');
        $cmd['last_error']=cr1478_state('automation_last_error');
        $cmd['last_summary']=$summary;
        $cmd['crontab']=cr1478_crontab_status((string)$cmd['full_line']);
        out(['data'=>$cmd,'error'=>null]);
    }

    if($action==='test'){
        $test=cr1478_test_run();
        $http=!empty($test['success'])?200:500;
        out(['data'=>$test,'error'=>!empty($test['success'])?null:['message'=>$test['automation']['error']??'Falha ao executar o CRON.']],$http);
    }

    if($action==='install'){
        $result=cr1478_install_crontab((string)$cmd['full_line']);
        $cmd['install']=$result;
        $cmd['last_run']=cr1478_state('automation_last_run');
        $cmd['last_error']=cr1478_state('automation_last_error');
        out(['data'=>$cmd,'error'=>empty($result['success'])?['message'=>$result['message']??'Não foi possível instalar o CRON automaticamente.']:null],empty($result['success'])?409:200);
    }

    out(['data'=>null,'error'=>['message'=>'Ação inválida.']],400);
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);
}
