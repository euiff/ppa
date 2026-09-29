<?php
$root=$updateRoot??realpath(__DIR__.'/../../../../');
if(!$root||!is_dir($root))throw new RuntimeException('Raiz do sistema não encontrada no patch v1.4.65.');
foreach(['sistema.html','index.html']as$name){
  $p=$root.'/'.$name;
  if(!is_file($p))continue;
  $s=(string)file_get_contents($p);
  $s=preg_replace('/<script[^>]+master-migration-entry\.js[^>]*><\/script>\s*/i','',$s);
  $s=preg_replace('/<a\b[^>]*href=["\'][^"\']*migracao-supabase[^"\']*["\'][^>]*>.*?<\/a>/is','',$s);
  if(stripos($s,'clone-app-notifications.js')===false){
    $tag='<script src="/clone-app-notifications.js?v=1.4.65" defer></script>';
    $s=stripos($s,'</body>')!==false?str_ireplace('</body>',$tag."\n</body>",$s):$s."\n".$tag."\n";
  }
  if(file_put_contents($p,$s,LOCK_EX)===false)throw new RuntimeException('Falha ao atualizar '.$name);
}
@file_put_contents($root.'/master-migration-entry.js',"(()=>{})();\n",LOCK_EX);
@unlink($root.'/migracao-supabase.html');
@unlink($root.'/api/migration-import.php');
