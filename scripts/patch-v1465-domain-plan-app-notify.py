from pathlib import Path
import re

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))

def one(text, old, new, label):
    c=text.count(old)
    if c!=1:
        raise SystemExit(f'{label}: anchor count={c}')
    return text.replace(old,new,1)

# 1) Escalas: clicar no cartão do departamento abre direto a Escala Completa.
s=asset.read_text(encoding='utf-8')
old='children:Ne.map((ce,me)=>ke(ce,me))'
new='children:Ne.map((ce,me)=>r.jsx("div",{className:"contents",onClickCapture:it=>{if(it.target.closest("button,a,input,select,textarea,[role=button]"))return;it.preventDefault(),it.stopPropagation(),b(ce.id)},children:ke(ce,me)},ce.id))'
s=one(s,old,new,'direct complete scale click')
asset.write_text(s,encoding='utf-8')

# 2) Gestão Comercial: domínio oficial editável e recursos por plano.
p=root/'master-comercial.html'
h=p.read_text(encoding='utf-8')

old='<div class="field"><label>URL do Webhook</label><input id="webhook" readonly></div>'
new='<div class="field"><label>Domínio oficial do sistema</label><input id="systemUrl" placeholder="https://escaladeproposito.com.br"></div><div class="field"><label>URL do Webhook</label><input id="webhook" placeholder="https://escaladeproposito.com.br/api/mercadopago-webhook.php"></div>'
h=one(h,old,new,'commercial domain field')
h=h.replace('<input id="salesUrl" readonly>','<input id="salesUrl" placeholder="https://escaladeproposito.com.br/">',1)

old="function fill(){trial.value=D.trial_days||10;salesWhatsapp.value=D.sales_whatsapp||'';salesEmail.value=D.sales_email||'';publicKey.value=D.mercadopago_public_key||'';access.value='';secret.value='';"
new="function fill(){trial.value=D.trial_days||10;salesWhatsapp.value=D.sales_whatsapp||'';salesEmail.value=D.sales_email||'';systemUrl.value=D.system_public_url||'https://escaladeproposito.com.br';publicKey.value=D.mercadopago_public_key||'';access.value='';secret.value='';"
h=one(h,old,new,'commercial fill domain')

old="const b={action:'save_settings',trial_days:Number(trial.value),sales_whatsapp:salesWhatsapp.value,sales_email:salesEmail.value,mercadopago_public_key:publicKey.value};"
new="const b={action:'save_settings',trial_days:Number(trial.value),sales_whatsapp:salesWhatsapp.value,sales_email:salesEmail.value,system_public_url:systemUrl.value.trim(),mercadopago_webhook_url:webhook.value.trim(),saas_sales_url:salesUrl.value.trim(),mercadopago_public_key:publicKey.value};"
h=one(h,old,new,'commercial save domain')

old="${Number(p.destaque)?' · Destaque':''}</div><div class=\"row-actions\""
new="${Number(p.destaque)?' · Destaque':''}<br><span class=\"badge ${Number(p.app_notifications_enabled??1)?'active':'expired'}\">App ${Number(p.app_notifications_enabled??1)?'✓':'✕'}</span> <span class=\"badge ${Number(p.whatsapp_enabled??1)?'active':'expired'}\">WhatsApp ${Number(p.whatsapp_enabled??1)?'✓':'✕'}</span></div><div class=\"row-actions\""
if old not in h:
    raise SystemExit('plan card resources anchor missing')
h=h.replace(old,new,1)

old="p=p||{id:'',nome:'',descricao:'',preco:39.9,duracao_dias:30,ativo:1,destaque:0,ordem:10};"
new="p=p||{id:'',nome:'',descricao:'',preco:39.9,duracao_dias:30,ativo:1,destaque:0,ordem:10,whatsapp_enabled:1,app_notifications_enabled:1};"
h=one(h,old,new,'plan modal defaults')

old='<label class="switch"><input id="pDest" type="checkbox" ${Number(p.destaque)?\'checked\':\'\'}> Destaque</label></div>'
new='<label class="switch"><input id="pDest" type="checkbox" ${Number(p.destaque)?\'checked\':\'\'}> Destaque</label><label class="switch"><input id="pApp" type="checkbox" ${Number(p.app_notifications_enabled??1)?\'checked\':\'\'}> Notificações pelo app</label><label class="switch"><input id="pWhats" type="checkbox" ${Number(p.whatsapp_enabled??1)?\'checked\':\'\'}> WhatsApp</label></div>'
h=one(h,old,new,'plan feature toggles')

old="ordem:Number(pOrdem.value),ativo:pAtivo.checked,destaque:pDest.checked});"
new="ordem:Number(pOrdem.value),ativo:pAtivo.checked,destaque:pDest.checked,app_notifications_enabled:pApp.checked,whatsapp_enabled:pWhats.checked});"
h=one(h,old,new,'plan feature save')

hook="""
systemUrl?.addEventListener('change',()=>{try{let u=systemUrl.value.trim().replace(/\\/$/,'');if(!/^https:\\/\\//i.test(u))return;const oldHosts=['escala.isaacanthony.com.br','topescalas.vercel.app'];if(!webhook.value.trim()||oldHosts.some(x=>webhook.value.includes(x)))webhook.value=u+'/api/mercadopago-webhook.php';if(!salesUrl.value.trim()||oldHosts.some(x=>salesUrl.value.includes(x)))salesUrl.value=u+'/';}catch(e){}});
"""
h=h.replace('</script>',hook+'\n</script>',1)
p.write_text(h,encoding='utf-8')

# 3) API comercial: salva domínio e flags dos planos.
p=root/'api'/'billing-master-v1314.php'
php=p.read_text(encoding='utf-8')

pat_url=re.compile(r"function\\s+cm_app_url\\s*\\(\\s*\\)\\s*(?::\\s*string)?\\s*\\{")
php,n=pat_url.subn(lambda m:m.group(0)+"\\n    $saved=rtrim(trim((string)cm_cfg(\'system_public_url\',\'\')),\'/\');\\n    if($saved!==\'\'&&preg_match(\'#^https://#i\',$saved))return $saved;",php,count=1)
if n!=1: raise SystemExit('cm app url: function not found')

old="    cm_schema();\n    $req=input_json();"
new="    cm_schema();\n    try{cm_add_col('saas_plans','whatsapp_enabled',\"TINYINT(1) NOT NULL DEFAULT 1\");}catch(Throwable $e){}\n    try{cm_add_col('saas_plans','app_notifications_enabled',\"TINYINT(1) NOT NULL DEFAULT 1\");}catch(Throwable $e){}\n    $req=input_json();"
php=one(php,old,new,'feature schema')

old="      'sales_email'=>cm_cfg('saas_sales_email',''),\n      'mercadopago_access_token_masked'=>cm_mask($access),"
new="      'sales_email'=>cm_cfg('saas_sales_email',''),\n      'system_public_url'=>cm_app_url(),\n      'mercadopago_webhook_url'=>cm_cfg('mercadopago_webhook_url',cm_app_url().'/api/mercadopago-webhook.php'),\n      'saas_sales_url'=>cm_cfg('saas_sales_url',cm_app_url().'/'),\n      'mercadopago_access_token_masked'=>cm_mask($access),"
php=one(php,old,new,'commercial response urls')

old="      'webhook_url'=>cm_app_url().'/api/mercadopago-webhook.php',\n      'sales_url'=>cm_app_url().'/',"
new="      'webhook_url'=>cm_cfg('mercadopago_webhook_url',cm_app_url().'/api/mercadopago-webhook.php'),\n      'sales_url'=>cm_cfg('saas_sales_url',cm_app_url().'/'),"
php=one(php,old,new,'commercial displayed urls')

old="            cm_set_cfg('saas_sales_email',trim((string)($req['sales_email']??'')));\n            cm_set_cfg('mercadopago_public_key'"
new="""            cm_set_cfg('saas_sales_email',trim((string)($req['sales_email']??'')));
            $publicUrl=rtrim(trim((string)($req['system_public_url']??'')),'/');
            if($publicUrl===''||!preg_match('#^https://[a-z0-9.-]+(?::[0-9]+)?(?:/.*)?$#i',$publicUrl))throw new RuntimeException('Informe um domínio HTTPS válido.');
            $webhook=trim((string)($req['mercadopago_webhook_url']??''));
            $sales=trim((string)($req['saas_sales_url']??''));
            if($webhook===''||!preg_match('#^https://#i',$webhook))$webhook=$publicUrl.'/api/mercadopago-webhook.php';
            if($sales===''||!preg_match('#^https://#i',$sales))$sales=$publicUrl.'/';
            cm_set_cfg('system_public_url',$publicUrl);
            cm_set_cfg('mercadopago_webhook_url',$webhook);
            cm_set_cfg('saas_sales_url',$sales);
            cm_set_cfg('mercadopago_public_key'"""
if old not in php:
    raise SystemExit('save settings url anchor missing')
php=php.replace(old,new,1)

pat=re.compile(r"(\$id=cm_insert_plan\(\[.*?\n\s*\]\);)",re.S)
m=pat.search(php)
if not m:
    raise SystemExit('save_plan insert block not found')
block=m.group(1)
if "whatsapp_enabled" not in block:
    add=block+"\n            db()->prepare(\"UPDATE saas_plans SET whatsapp_enabled=?,app_notifications_enabled=? WHERE id=?\")->execute([!empty($req['whatsapp_enabled'])?1:0,!empty($req['app_notifications_enabled'])?1:0,$id]);"
    php=php[:m.start()]+add+php[m.end():]
p.write_text(php,encoding='utf-8')

# 4) Biblioteca de cobrança: domínio oficial também é usado no checkout.
p=root/'api'/'billing_lib_v1313.php'
lib=p.read_text(encoding='utf-8')
pat_burl=re.compile(r"function\\s+billing_app_url\\s*\\(\\s*\\)\\s*(?::\\s*string)?\\s*\\{")
lib,n=pat_burl.subn(lambda m:m.group(0)+"\\n    $saved=rtrim(trim((string)(billing_cfg(\'system_public_url\',\'\')??\'\')),\'/\');\\n    if($saved!==\'\'&&preg_match(\'#^https://#i\',$saved))return $saved;",lib,count=1)
if n!=1: raise SystemExit('billing app url: function not found')
p.write_text(lib,encoding='utf-8')

p=root/'api'/'billing-checkout.php'
chk=p.read_text(encoding='utf-8')
old="'notification_url'=>$app.'/api/mercadopago-webhook.php',"
new="'notification_url'=>(billing_cfg('mercadopago_webhook_url',$app.'/api/mercadopago-webhook.php')?:$app.'/api/mercadopago-webhook.php'),"
chk=one(chk,old,new,'checkout webhook url')
p.write_text(chk,encoding='utf-8')

# 5) Recursos de plano.
features=r'''<?php
declare(strict_types=1);

function v1465_plan_features(string $igrejaId): array {
    $defaults=['whatsapp'=>true,'app_notifications'=>true];
    if($igrejaId==='')return $defaults;
    try{
        $q=db()->prepare("SELECT p.whatsapp_enabled,p.app_notifications_enabled
          FROM saas_subscriptions s
          LEFT JOIN saas_plans p ON p.id=s.plan_id
          WHERE BINARY s.igreja_id=BINARY ?
          ORDER BY s.updated_at DESC LIMIT 1");
        $q->execute([$igrejaId]);
        $r=$q->fetch(PDO::FETCH_ASSOC);
        if(!$r||$r['whatsapp_enabled']===null)return $defaults;
        return ['whatsapp'=>(bool)(int)$r['whatsapp_enabled'],'app_notifications'=>$r['app_notifications_enabled']===null?true:(bool)(int)$r['app_notifications_enabled']];
    }catch(Throwable $e){return $defaults;}
}
function v1465_feature_enabled(string $igrejaId,string $feature): bool {
    $f=v1465_plan_features($igrejaId);
    return array_key_exists($feature,$f)?(bool)$f[$feature]:true;
}
'''
(root/'api'/'plan_features_v1465.php').write_text(features,encoding='utf-8')

endpoint=r'''<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
require_once __DIR__.'/plan_features_v1465.php';
$caller=require_auth();$ctx=user_context();
$ig=(string)($ctx['igreja_id']??'');
if(($ctx['role']??'')==='master'){
    $b=$_SERVER['REQUEST_METHOD']==='POST'?input_json():$_GET;
    $ig=trim((string)($b['igreja_id']??$ig));
}
out(['data'=>['igreja_id'=>$ig,'features'=>v1465_plan_features($ig)],'error'=>null]);
'''
(root/'api'/'plan-features.php').write_text(endpoint,encoding='utf-8')

p=root/'api'/'whatsapp_transport_v1424.php'
wt=p.read_text(encoding='utf-8')
if "plan_features_v1465.php" not in wt:
    wt=wt.replace("declare(strict_types=1);","declare(strict_types=1);\nrequire_once __DIR__.'/plan_features_v1465.php';",1)
old="function v1424_cfg(string $key,?string $igrejaId=null): string {\n    try{if(function_exists('config_value'))"
new="function v1424_cfg(string $key,?string $igrejaId=null): string {\n    if($igrejaId&&in_array($key,['evolution_url','evolution_api_key','evolution_instance'],true)&&function_exists('v1465_feature_enabled')&&!v1465_feature_enabled($igrejaId,'whatsapp'))return '';\n    try{if(function_exists('config_value'))"
wt=one(wt,old,new,'whatsapp plan guard')
p.write_text(wt,encoding='utf-8')

# 6) Pendências e notificações no app/PWA.
pending=r'''<?php
declare(strict_types=1);
require_once __DIR__.'/bootstrap.php';
require_once __DIR__.'/plan_features_v1465.php';
$u=require_auth();$ctx=user_context();
$uid=(string)($u['id']??$ctx['id']??'');$ig=(string)($ctx['igreja_id']??'');
if($uid==='')out(['data'=>null,'error'=>['message'=>'Usuário inválido.']],401);
if(!v1465_feature_enabled($ig,'app_notifications'))out(['data'=>['count'=>0,'items'=>[],'disabled'=>true],'error'=>null]);
$items=[];
try{
    if(table_exists('escala_itens')&&table_exists('escalas')){
        $sql="SELECT ei.id,ei.escala_id,ei.funcao,ei.status_confirmacao,ei.created_at,e.data,e.titulo,e.status escala_status,d.nome departamento
          FROM escala_itens ei JOIN escalas e ON BINARY e.id=BINARY ei.escala_id LEFT JOIN departamentos d ON BINARY d.id=BINARY e.departamento_id
          WHERE BINARY ei.voluntario_id=BINARY ? AND COALESCE(ei.status_confirmacao,'pendente')='pendente'
          AND (e.data IS NULL OR e.data>=CURDATE()) AND COALESCE(e.status,'') NOT IN ('cancelada','cancelado','excluida','excluido')
          ORDER BY e.data ASC,ei.created_at ASC LIMIT 100";
        $q=db()->prepare($sql);$q->execute([$uid]);
        foreach($q->fetchAll(PDO::FETCH_ASSOC)?:[] as$r){
            $dep=trim((string)($r['departamento']??''));$fn=trim((string)($r['funcao']??''));$dt=!empty($r['data'])?date('d/m/Y',strtotime((string)$r['data'])):'';
            $msg=implode(' · ',array_values(array_filter([$dep,$fn,$dt],fn($x)=>$x!=='')));
            $items[]=['id'=>'escala:'.(string)$r['id'],'type'=>'escala','item_id'=>(string)$r['id'],'escala_id'=>(string)$r['escala_id'],'title'=>'Você foi escalado! 🙌','message'=>$msg,'url'=>'/escala/'.rawurlencode((string)$r['escala_id']),'created_at'=>$r['created_at']??null];
        }
    }
    usort($items,fn($a,$b)=>strcmp((string)($a['created_at']??''),(string)($b['created_at']??'')));
    out(['data'=>['count'=>count($items),'items'=>$items,'disabled'=>false,'checked_at'=>date(DATE_ATOM)],'error'=>null]);
}catch(Throwable $e){out(['data'=>null,'error'=>['message'=>$e->getMessage()]],500);}
'''
(root/'api'/'app-pending.php').write_text(pending,encoding='utf-8')

devices=r'''<?php
declare(strict_types=1);
require_once __DIR__.'/bootstrap.php';
require_once __DIR__.'/plan_features_v1465.php';
$u=require_auth();$ctx=user_context();$uid=(string)($u['id']??$ctx['id']??'');$ig=(string)($ctx['igreja_id']??'');
if($uid==='')out(['data'=>null,'error'=>['message'=>'Usuário inválido.']],401);
try{
    db()->exec("CREATE TABLE IF NOT EXISTS app_devices(id VARCHAR(36) NOT NULL PRIMARY KEY,user_id VARCHAR(36) NOT NULL,igreja_id VARCHAR(36) NULL,push_token VARCHAR(512) NULL,platform VARCHAR(30) NOT NULL DEFAULT 'android',device_name VARCHAR(120) NULL,app_version VARCHAR(40) NULL,enabled TINYINT(1) NOT NULL DEFAULT 1,last_seen_at DATETIME NOT NULL,created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,UNIQUE KEY uq_app_device_token(push_token(191)),KEY idx_app_devices_user(user_id),KEY idx_app_devices_church(igreja_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $b=input_json();$action=(string)($b['action']??'touch');$token=trim((string)($b['push_token']??''));
    if($action==='register'){
        if($token==='')throw new RuntimeException('Token de notificação ausente.');
        $q=db()->prepare("SELECT id FROM app_devices WHERE push_token=? LIMIT 1");$q->execute([$token]);$id=(string)($q->fetchColumn()?:uuid4());
        db()->prepare("INSERT INTO app_devices(id,user_id,igreja_id,push_token,platform,device_name,app_version,enabled,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,1,NOW(),NOW(),NOW()) ON DUPLICATE KEY UPDATE user_id=VALUES(user_id),igreja_id=VALUES(igreja_id),platform=VALUES(platform),device_name=VALUES(device_name),app_version=VALUES(app_version),enabled=1,last_seen_at=NOW(),updated_at=NOW()")->execute([$id,$uid,$ig?:null,$token,trim((string)($b['platform']??'android'))?:'android',trim((string)($b['device_name']??''))?:null,trim((string)($b['app_version']??''))?:null]);
    }elseif($action==='unregister'&&$token!==''){db()->prepare("UPDATE app_devices SET enabled=0,updated_at=NOW() WHERE user_id=? AND push_token=?")->execute([$uid,$token]);}
    else{db()->prepare("UPDATE app_devices SET last_seen_at=NOW(),updated_at=NOW() WHERE user_id=? AND enabled=1")->execute([$uid]);}
    $q=db()->prepare("SELECT COUNT(*) FROM app_devices WHERE user_id=? AND enabled=1");$q->execute([$uid]);
    out(['data'=>['registered_devices'=>(int)$q->fetchColumn(),'app_notifications_enabled'=>v1465_feature_enabled($ig,'app_notifications')],'error'=>null]);
}catch(Throwable $e){out(['data'=>null,'error'=>['message'=>$e->getMessage()]],400);}
'''
(root/'api'/'app-device.php').write_text(devices,encoding='utf-8')

js=r'''(()=>{
'use strict';
const KEY='escala-facil.auth-token',SEEN='escala-app-seen-v1465:',POLL=20000;let last=-1,timer=null;
const token=()=>{try{return localStorage.getItem(KEY)||''}catch{return''}};
function badge(n){n=Math.max(0,Number(n)||0);try{if(window.EscalaNative?.setBadge)window.EscalaNative.setBadge(n);else if(n>0&&navigator.setAppBadge)navigator.setAppBadge(n).catch(()=>{});else if(!n&&navigator.clearAppBadge)navigator.clearAppBadge().catch(()=>{})}catch(e){}}
function seenKey(){const t=token();return SEEN+(t?t.slice(-12):'anon')}function getSeen(){try{const a=JSON.parse(localStorage.getItem(seenKey())||'[]');return Array.isArray(a)?a:[]}catch{return[]}}function saveSeen(a){try{localStorage.setItem(seenKey(),JSON.stringify(a.slice(-300)))}catch{}}
async function notify(i,count){try{if(window.EscalaNative?.notify){window.EscalaNative.notify(String(i.title||'Escala de Propósito'),String(i.message||''),String(i.url||'/'),Number(count)||1);return}if(!('Notification'in window)||Notification.permission!=='granted')return;const reg=await navigator.serviceWorker?.getRegistration?.();if(reg?.showNotification)await reg.showNotification(i.title||'Escala de Propósito',{body:i.message||'',icon:'/icon-192.png',badge:'/icon-192.png',tag:'escala-'+String(i.id||''),renotify:true,data:{url:i.url||'/'}})}catch(e){}}
async function refresh(){const t=token();if(!t){badge(0);return}try{const r=await fetch('/api/app-pending.php',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+t},body:'{}',cache:'no-store'}),j=await r.json();if(!r.ok||j.error)throw 0;const d=j.data||{},items=Array.isArray(d.items)?d.items:[],count=Number(d.count)||0;badge(count);if(count!==last){window.dispatchEvent(new CustomEvent('escala-pending-count',{detail:{count,items}}));last=count}const s=getSeen(),set=new Set(s);for(const i of items.filter(x=>x?.id&&!set.has(x.id))){await notify(i,count);s.push(i.id);set.add(i.id)}saveSeen(s)}catch(e){}}
function start(){if(timer)clearInterval(timer);refresh();timer=setInterval(refresh,POLL)}
document.addEventListener('DOMContentLoaded',start);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});window.addEventListener('focus',refresh);window.addEventListener('online',refresh);window.EscalaAppNotifications={refresh,badge};
})();'''
(root/'app-notifications-v1465.js').write_text(js,encoding='utf-8')

guard=r'''(()=>{
'use strict';
const token=()=>{try{return localStorage.getItem('escala-facil.auth-token')||''}catch{return''}};
function hideWhatsApp(){document.querySelectorAll('a,button').forEach(el=>{const t=(el.textContent||'').trim(),href=(el.getAttribute('href')||'');if(/whats\s*app/i.test(t)||/whatsapp|evolution/i.test(href)){el.style.display='none';el.setAttribute('aria-hidden','true')}})}
async function run(){const t=token();if(!t)return;try{const r=await fetch('/api/plan-features.php',{headers:{Authorization:'Bearer '+t},cache:'no-store'}),j=await r.json();const f=j?.data?.features||{};window.EscalaPlanFeatures=f;if(f.whatsapp===false){document.documentElement.dataset.whatsappEnabled='0';hideWhatsApp();new MutationObserver(hideWhatsApp).observe(document.body,{subtree:true,childList:true})}}catch(e){}}
document.addEventListener('DOMContentLoaded',run);
})();'''
(root/'plan-feature-guard-v1465.js').write_text(guard,encoding='utf-8')

p=root/'sistema.html'
sh=p.read_text(encoding='utf-8')
inject='  <script src="/plan-feature-guard-v1465.js?v=1.4.65" defer></script>\n  <script src="/app-notifications-v1465.js?v=1.4.65" defer></script>\n'
if 'app-notifications-v1465.js' not in sh:sh=sh.replace('</body>',inject+'</body>',1)
p.write_text(sh,encoding='utf-8')

p=root/'sw.js';sw=p.read_text(encoding='utf-8');marker='/* app-notification-click-v1.4.65 */'
if marker not in sw:
    sw+=r'''
/* app-notification-click-v1.4.65 */
self.addEventListener('notificationclick',event=>{event.notification.close();const url=(event.notification&&event.notification.data&&event.notification.data.url)||'/';event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(list=>{for(const c of list){if('focus'in c){try{c.navigate(url)}catch(e){}return c.focus()}}return clients.openWindow?clients.openWindow(url):null}))});
'''
p.write_text(sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.65\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.65.md').write_text('''# Escala de Propósito v1.4.65 — Domínio, planos e notificações do app

- Clique no cartão de um departamento abre diretamente a Escala Completa.
- O Master pode editar domínio oficial, URL do webhook do Mercado Pago e página pública de vendas.
- O domínio padrão/sugerido é https://escaladeproposito.com.br.
- Cada plano ganha Notificações pelo app e WhatsApp como recursos independentes.
- Plano sem WhatsApp bloqueia o transporte Evolution também no servidor.
- O app/PWA consulta pendências e atualiza badge/notificações enquanto estiver ativo.
- /api/app-device.php prepara registro de dispositivos/tokens para o APK com push nativo.
- /api/app-pending.php centraliza pendências do aplicativo.
- Igrejas legadas continuam com os dois recursos ativos por padrão.
- Push nativo com o APK totalmente fechado depende da recompilação do APK com a assinatura original.
''',encoding='utf-8')
