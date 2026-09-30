<?php
declare(strict_types=1);

$root=$updateRoot??realpath(__DIR__.'/../../../../');
if(!$root||!is_dir($root)) throw new RuntimeException('Raiz do sistema não encontrada para o patch comercial v1.4.71.');

if(!class_exists('ZipArchive')) throw new RuntimeException('A extensão ZipArchive do PHP é necessária para restaurar a Gestão Comercial.');
if(!function_exists('curl_init')) throw new RuntimeException('A extensão cURL do PHP é necessária para restaurar a Gestão Comercial.');

$tmpDir=$root.'/storage/updates/tmp';
if(!is_dir($tmpDir)&&!mkdir($tmpDir,0755,true)&&!is_dir($tmpDir)) {
    throw new RuntimeException('Não foi possível criar a pasta temporária da atualização.');
}

$zipFile=$tmpDir.'/commercial-base-v1464-'.bin2hex(random_bytes(4)).'.zip';
$extract=$tmpDir.'/commercial-base-v1464-'.bin2hex(random_bytes(4));

$url='https://github.com/euiff/ppa/releases/download/v1.4.64/escala-de-proposito-cpanel.zip';
$ch=curl_init($url);
curl_setopt_array($ch,[
    CURLOPT_RETURNTRANSFER=>true,
    CURLOPT_FOLLOWLOCATION=>true,
    CURLOPT_TIMEOUT=>180,
    CURLOPT_CONNECTTIMEOUT=>25,
    CURLOPT_USERAGENT=>'EscalaDeProposito-Updater/1.4.71'
]);
$body=curl_exec($ch);
$status=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);
$err=(string)curl_error($ch);
curl_close($ch);

if($body===false||$status<200||$status>=300) {
    throw new RuntimeException('Falha ao baixar a base comercial. HTTP '.$status.($err!==''?' - '.$err:''));
}
if(file_put_contents($zipFile,$body,LOCK_EX)===false) {
    throw new RuntimeException('Falha ao salvar a base comercial temporária.');
}

$zip=new ZipArchive();
if($zip->open($zipFile)!==true) throw new RuntimeException('Pacote comercial inválido.');
if(!mkdir($extract,0755,true)&&!is_dir($extract)) {
    $zip->close();
    throw new RuntimeException('Falha ao criar pasta temporária de extração.');
}
$zip->extractTo($extract);
$zip->close();

$copy=[
    'master-comercial.html',
    'master-commerce-entry.js',
    'api/billing-master-v1314.php',
    'api/billing_lib_v1314.php',
    'api/billing_lib_v1313.php',
    'api/billing-public.php',
    'api/billing-checkout.php',
    'api/mercadopago-webhook.php',
    'api/subscription-status.php'
];

foreach($copy as$rel){
    $src=$extract.'/'.$rel;
    $dst=$root.'/'.$rel;
    if(!is_file($src)) throw new RuntimeException('Arquivo comercial ausente no pacote: '.$rel);
    if(!is_dir(dirname($dst))&&!mkdir(dirname($dst),0755,true)&&!is_dir(dirname($dst))) {
        throw new RuntimeException('Falha ao criar pasta para '.$rel);
    }
    if(!copy($src,$dst)) throw new RuntimeException('Falha ao restaurar '.$rel);
}

// Ajusta a interface comercial para o clone.
$html=$root.'/master-comercial.html';
$s=(string)file_get_contents($html);

// Remove qualquer entrada antiga de Migração Supabase.
$s=preg_replace('/<a\b[^>]*href=["\'][^"\']*migracao-supabase[^"\']*["\'][^>]*>.*?<\/a>/is','',$s);
$s=preg_replace('/<button\b[^>]*>\s*Migração Supabase\s*<\/button>/is','',$s);

// Resposta robusta da API: mostra erro real em vez de "Unexpected end of JSON input".
$old="async function api(body){const r=await fetch('/api/billing-master-v1314.php',{method:body?'POST':'GET',headers:H,body:body?JSON.stringify(body):undefined});const j=await r.json();if(!r.ok||j.error)throw new Error(j?.error?.message||'Falha no servidor');return j.data}";
$new="async function api(body){const r=await fetch('/api/billing-master-v1314.php',{method:body?'POST':'GET',headers:H,body:body?JSON.stringify(body):undefined,cache:'no-store'});const text=await r.text();let j=null;try{j=text?JSON.parse(text):null}catch(_){throw new Error('A API comercial retornou resposta inválida (HTTP '+r.status+').')}if(!j)throw new Error('A API comercial não retornou dados (HTTP '+r.status+').');if(!r.ok||j.error)throw new Error(j?.error?.message||('Falha no servidor HTTP '+r.status));return j.data}";
if(str_contains($s,$old)) $s=str_replace($old,$new,$s);

$s=str_replace('ESCALA COM PROPÓSITO · INÁCIO LABS','ESCALA DE PROPÓSITO · INÁCIO LABS',$s);
$s=str_replace('Escala com Propósito','Escala de Propósito',$s);

if(file_put_contents($html,$s,LOCK_EX)===false) {
    throw new RuntimeException('Falha ao atualizar a interface da Gestão Comercial.');
}

// O clone não usa o migrador Supabase.
@unlink($root.'/migracao-supabase.html');
@unlink($root.'/api/migration-import.php');

// Validação mínima dos arquivos críticos.
foreach([
    $root.'/api/billing-master-v1314.php',
    $root.'/api/billing_lib_v1314.php',
    $root.'/api/billing_lib_v1313.php'
] as$file){
    if(!is_file($file)||filesize($file)<100) throw new RuntimeException('Módulo comercial incompleto: '.basename($file));
}

// Limpeza temporária.
@unlink($zipFile);
if(is_dir($extract)){
    $it=new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($extract,FilesystemIterator::SKIP_DOTS),
        RecursiveIteratorIterator::CHILD_FIRST
    );
    foreach($it as$f){ $f->isDir()?@rmdir($f->getPathname()):@unlink($f->getPathname()); }
    @rmdir($extract);
}
