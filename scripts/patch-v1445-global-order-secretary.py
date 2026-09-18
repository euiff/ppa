from pathlib import Path

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
js=asset.read_text(encoding='utf-8')

def rep(text,old,new,label):
    c=text.count(old)
    if c!=1: raise SystemExit(f'{label} anchor count={c}')
    return text.replace(old,new,1)

# Cargo Secretária
js=rep(js,'Jg={master:"Master",admin:"Pastor",lider:"Líder",voluntario:"Voluntário"}','Jg={master:"Master",admin:"Pastor",lider:"Líder",secretaria:"Secretária",voluntario:"Voluntário"}','global role labels')
js=rep(js,'if(rt==="voluntario"){await I.from("departamentos").update({lider_id:null}).eq("lider_id",fe).eq("igreja_id",t)}','if(rt==="voluntario"||rt==="secretaria"){await I.from("departamentos").update({lider_id:null}).eq("lider_id",fe).eq("igreja_id",t)}','clear leadership')
js=rep(js,'if(id&&Ae[id]!=="admin"&&Ae[id]!=="master")Ae[id]="lider"','if(id&&Ae[id]!=="admin"&&Ae[id]!=="master"&&Ae[id]!=="secretaria")Ae[id]="lider"','secretary leader protection')
js=rep(js,'Je=fe=>{switch(fe){case"admin":return"bg-primary/10 text-primary border-primary/20";case"lider":return"bg-status-pending/10 text-status-pending border-status-pending/20";default:return"bg-secondary text-muted-foreground border-border"}},Qt=fe=>fe==="admin"?"Admin":fe==="lider"?"Líder":"Voluntário"','Je=fe=>{switch(fe){case"admin":return"bg-primary/10 text-primary border-primary/20";case"lider":return"bg-status-pending/10 text-status-pending border-status-pending/20";case"secretaria":return"bg-secondary text-foreground border-border";default:return"bg-secondary text-muted-foreground border-border"}},Qt=fe=>fe==="admin"?"Admin":fe==="lider"?"Líder":fe==="secretaria"?"Secretária":"Voluntário"','secretary badge')
js=rep(js,'children:[Ze.length," pessoas cadastradas",s==="voluntario"&&" • Modo visualização"]','children:[Ze.length," pessoas cadastradas",(e==="secretaria"||s==="voluntario")&&" • Modo visualização"]','secretary view mode')
js=rep(js,'children:[r.jsx("option",{value:"voluntario",children:"Voluntário"}),r.jsx("option",{value:"lider",children:"Líder (definir departamento)"}),r.jsx("option",{value:"admin",children:"Admin"})]','children:[r.jsx("option",{value:"voluntario",children:"Voluntário"}),r.jsx("option",{value:"secretaria",children:"Secretária"}),r.jsx("option",{value:"lider",children:"Líder (definir departamento)"}),r.jsx("option",{value:"admin",children:"Admin"})]','role select')
js=rep(js,'A={master:"Master",admin:"Admin",lider:"Líder",voluntario:"Voluntário"}','A={master:"Master",admin:"Admin",lider:"Líder",secretaria:"Secretária",voluntario:"Voluntário"}','master role map')
js=rep(js,'children:[r.jsx(nt,{value:"admin",children:"Admin"}),r.jsx(nt,{value:"lider",children:"Líder"}),r.jsx(nt,{value:"voluntario",children:"Voluntário"})]','children:[r.jsx(nt,{value:"admin",children:"Admin"}),r.jsx(nt,{value:"secretaria",children:"Secretária"}),r.jsx(nt,{value:"lider",children:"Líder"}),r.jsx(nt,{value:"voluntario",children:"Voluntário"})]','master secretary option')

# Ordenação natural global no frontend
js=rep(js,'ce[$].sort((ue,Me)=>(ue.funcao||"").localeCompare(Me.funcao||"","pt-BR",{numeric:!0}))','ce[$].sort((ue,Me)=>(ue.funcao||"").localeCompare(Me.funcao||"","pt-BR",{numeric:!0,sensitivity:"base"})||String(ue.profiles&&ue.profiles.nome||"").localeCompare(String(Me.profiles&&Me.profiles.nome||""),"pt-BR",{sensitivity:"base"}))','scale overview ordering')
js=rep(js,'l((ce||[]).map(ue=>({...ue,profiles:$[ue.voluntario_id]?{nome:$[ue.voluntario_id].nome}:null})).sort((ue,Me)=>(ue.funcao||"").localeCompare(Me.funcao||"","pt-BR",{numeric:!0})))','l((ce||[]).map(ue=>({...ue,profiles:$[ue.voluntario_id]?{nome:$[ue.voluntario_id].nome}:null})).sort((ue,Me)=>(ue.funcao||"").localeCompare(Me.funcao||"","pt-BR",{numeric:!0,sensitivity:"base"})||String(ue.profiles&&ue.profiles.nome||"").localeCompare(String(Me.profiles&&Me.profiles.nome||""),"pt-BR",{sensitivity:"base"})))','single scale ordering')
js=rep(js,'f((ge||[]).map($e=>({...$e,profile:ae[$e.voluntario_id]})).sort(($e,_t)=>($e.funcao||"").localeCompare(_t.funcao||"","pt-BR",{numeric:!0})))','f((ge||[]).map($e=>({...$e,profile:ae[$e.voluntario_id]})).sort(($e,_t)=>($e.funcao||"").localeCompare(_t.funcao||"","pt-BR",{numeric:!0,sensitivity:"base"})||String($e.profile&&$e.profile.nome||"").localeCompare(String(_t.profile&&_t.profile.nome||""),"pt-BR",{sensitivity:"base"})))','full scale main ordering')
js=rep(js,'.map(Me=>({...Me,profile:ce[Me.voluntario_id]})).sort((Me,He)=>(Me.funcao||"").localeCompare(He.funcao||"","pt-BR",{numeric:!0}))','.map(Me=>({...Me,profile:ce[Me.voluntario_id]})).sort((Me,He)=>(Me.funcao||"").localeCompare(He.funcao||"","pt-BR",{numeric:!0,sensitivity:"base"})||String(Me.profile&&Me.profile.nome||"").localeCompare(String(He.profile&&He.profile.nome||""),"pt-BR",{sensitivity:"base"}))','full scale other ordering')
old='te=()=>l?[{dept:l.departamentos,itens:d,status:l.status},...b].filter(pe=>pe==null?void 0:pe.dept).sort((pe,q)=>{var oe,xe;return(((oe=pe.dept)==null?void 0:oe.nome)||"").localeCompare(((xe=q.dept)==null?void 0:xe.nome)||"","pt-BR",{numeric:!0})}):[],B='
new='te=()=>l?[{dept:l.departamentos,itens:d,status:l.status},...b].filter(pe=>pe==null?void 0:pe.dept).map(pe=>({...pe,itens:[...(pe.itens||[])].sort((q,oe)=>String(q.funcao||"").localeCompare(String(oe.funcao||""),"pt-BR",{numeric:!0,sensitivity:"base"})||String(q.profile&&q.profile.nome||"").localeCompare(String(oe.profile&&oe.profile.nome||""),"pt-BR",{sensitivity:"base"}))})).sort((pe,q)=>{var oe,xe;return(((oe=pe.dept)==null?void 0:oe.nome)||"").localeCompare(((xe=q.dept)==null?void 0:xe.nome)||"","pt-BR",{numeric:!0,sensitivity:"base"})}):[],B='
js=rep(js,old,new,'full export ordering')
asset.write_text(js,encoding='utf-8')

# PDF do WhatsApp: departamento A-Z, função natural, nome A-Z
p=root/'api'/'scale-day-pdf-v1434.php'; php=p.read_text(encoding='utf-8')
old="$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];$songs="
new="$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];usort($rows,static function(array $a,array $b):int{foreach(['departamento_nome','funcao','voluntario_nome']as$k){$av=trim((string)($a[$k]??''));$bv=trim((string)($b[$k]??''));$ax=@iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$av);$bx=@iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$bv);$cmp=strnatcasecmp($ax===false?$av:$ax,$bx===false?$bv:$bx);if($cmp!==0)return$cmp;}return 0;});$songs="
php=rep(php,old,new,'pdf v1434 ordering');p.write_text(php,encoding='utf-8')
p=root/'api'/'scale-day-pdf-v1435.php'; php=p.read_text(encoding='utf-8')
old="$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];\n    $songs="
new="$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];\n    usort($rows,static function(array $a,array $b):int{foreach(['departamento_nome','funcao','voluntario_nome']as$k){$av=trim((string)($a[$k]??''));$bv=trim((string)($b[$k]??''));$ax=@iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$av);$bx=@iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$bv);$cmp=strnatcasecmp($ax===false?$av:$ax,$bx===false?$bv:$bx);if($cmp!==0)return$cmp;}return strcmp((string)($a['item_id']??''),(string)($b['item_id']??''));});\n    $songs="
php=rep(php,old,new,'pdf v1435 ordering');p.write_text(php,encoding='utf-8')

# WhatsApp da Secretária
p=root/'api'/'volunteer_menu_v1435.php'; menu=p.read_text(encoding='utf-8')
anchor="function v1435_volunteer_id(array $profiles): string {\n    foreach($profiles as $p){$x=trim((string)($p['id']??''));if($x!=='')return $x;}return '';\n}\n"
helpers='''function v1445_is_secretary(array $profiles): bool {
    static $cache=[];$ids=v1435_profile_ids($profiles);if(!$ids)return false;$key=implode('|',$ids);if(array_key_exists($key,$cache))return$cache[$key];
    try{$ph=implode(',',array_fill(0,count($ids),'?'));$q=db()->prepare("SELECT 1 FROM user_roles WHERE user_id IN ($ph) AND role='secretaria' LIMIT 1");$q->execute($ids);return$cache[$key]=(bool)$q->fetchColumn();}catch(Throwable$e){return$cache[$key]=false;}
}
function v1445_church_days(array $profiles): array {
    $ig=v1435_igreja_id($profiles);$vol=v1435_volunteer_id($profiles);if($ig===''||$vol==='')return[];
    try{$q=db()->prepare("SELECT MIN(e.id) escala_id,e.data,e.igreja_id,e.culto_id,c.nome culto_nome,c.horario FROM escalas e LEFT JOIN cultos c ON BINARY c.id=BINARY e.culto_id WHERE BINARY e.igreja_id=BINARY ? AND e.data BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 90 DAY) GROUP BY e.data,e.igreja_id,e.culto_id,c.nome,c.horario ORDER BY e.data ASC,c.horario ASC,c.nome ASC");$q->execute([$ig]);$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];}catch(Throwable$e){if(function_exists('v1311p_trace'))v1311p_trace('v1445_secretary_scales_query_error',['message'=>substr($e->getMessage(),0,240)]);return[];}
    $out=[];foreach($rows as$r){$data=(string)($r['data']??'');if($data==='')continue;$date=date('d/m/Y',strtotime($data));$weekday=['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'][(int)date('w',strtotime($data))]??'';$time=trim((string)($r['horario']??''));$time=$time!==''?substr($time,0,5):'';$culto=trim((string)($r['culto_nome']??''))?:'Culto';$out[]=['type'=>'church_scale','item_id'=>'','escala_id'=>(string)$r['escala_id'],'voluntario_id'=>$vol,'igreja_id'=>(string)$r['igreja_id'],'culto_id'=>(string)($r['culto_id']??''),'data'=>$data,'horario'=>(string)($r['horario']??''),'culto_nome'=>$culto,'roles'=>[],'label'=>"{$weekday}, {$date}".($time!==''?" às {$time}":'')." — {$culto}",'sort_ts'=>strtotime($data.' '.($time?:'00:00'))?:PHP_INT_MAX];}
    usort($out,static fn($a,$b)=>(int)$a['sort_ts']<=>(int)$b['sort_ts']?:strnatcasecmp((string)$a['label'],(string)$b['label']));return$out;
}
function v1445_menu_days(array $profiles): array {return v1445_is_secretary($profiles)?v1445_church_days($profiles):v1435_confirmed_days($profiles);}
function v1445_secretary_scale_row(string $escalaId,array $profiles): ?array {
    if($escalaId===''||!v1445_is_secretary($profiles))return null;$ig=v1435_igreja_id($profiles);$vol=v1435_volunteer_id($profiles);if($ig===''||$vol==='')return null;
    try{$q=db()->prepare("SELECT e.id escala_id,e.data,e.igreja_id,e.culto_id,c.nome culto_nome,c.horario FROM escalas e LEFT JOIN cultos c ON BINARY c.id=BINARY e.culto_id WHERE BINARY e.id=BINARY ? AND BINARY e.igreja_id=BINARY ? LIMIT 1");$q->execute([$escalaId,$ig]);$r=$q->fetch(PDO::FETCH_ASSOC);if(!$r)return null;$r['item_id']='';$r['voluntario_id']=$vol;$r['status_confirmacao']='secretaria';return$r;}catch(Throwable$e){return null;}
}
function v1445_selected_scale(array $option,array $profiles): ?array {
    if(v1445_is_secretary($profiles))return v1445_secretary_scale_row((string)($option['escala_id']??''),$profiles);
    $r=v1435_scale_row((string)($option['item_id']??''));return$r&&($r['status_confirmacao']??'')==='confirmado'?$r:null;
}
'''
menu=rep(menu,anchor,anchor+helpers,'secretary whatsapp helpers')
old='''function v1435_home_text(array $profiles=[]): string {
    $count=0;
    try{if(function_exists('v1311p_collect_options'))$count=count(v1311p_collect_options($profiles));}catch(Throwable $e){}
    $pending=$count>0?"\\n📌 Você tem *{$count} pendência".($count===1?'':'s')."* para responder.\\n":"\\n✅ Você não possui pendências no momento.\\n";
    return "📲 *MENU DO VOLUNTÁRIO*\\n".$pending."\\n*1* - 📌 Pendências\\n*2* - 📅 Dias em que estou escalado\\n*3* - 📄 Selecionar uma escala completa e receber em PDF\\n*4* - 🚫 Adicionar dias em que estou indisponível\\n*5* - 🎵 Repertório de músicas\\n\\n_Responda somente com 1, 2, 3, 4 ou 5._";
}
'''
new='''function v1435_home_text(array $profiles=[]): string {
    $count=0;
    try{if(function_exists('v1311p_collect_options'))$count=count(v1311p_collect_options($profiles));}catch(Throwable $e){}
    $pending=$count>0?"\\n📌 Você tem *{$count} pendência".($count===1?'':'s')."* para responder.\\n":"\\n✅ Você não possui pendências no momento.\\n";
    if(v1445_is_secretary($profiles))return "📲 *MENU DA SECRETÁRIA*\\n".$pending."\\n*1* - 📌 Minhas pendências\\n*2* - 📅 Ver escalas da igreja\\n*3* - 📄 Receber escala completa em PDF\\n*4* - 🚫 Adicionar meus dias indisponíveis\\n*5* - 🎵 Repertório das escalas\\n\\n_Responda somente com 1, 2, 3, 4 ou 5._";
    return "📲 *MENU DO VOLUNTÁRIO*\\n".$pending."\\n*1* - 📌 Pendências\\n*2* - 📅 Dias em que estou escalado\\n*3* - 📄 Selecionar uma escala completa e receber em PDF\\n*4* - 🚫 Adicionar dias em que estou indisponível\\n*5* - 🎵 Repertório de músicas\\n\\n_Responda somente com 1, 2, 3, 4 ou 5._";
}
'''
menu=rep(menu,old,new,'secretary home')
old='''function v1435_show_days(string $sender,array $profiles,?array $session=null): bool {
    $days=v1435_confirmed_days($profiles);$ig=v1435_igreja_id($profiles);
    if(!$days){if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_home',[],null,null,$session);return v1311p_send($sender,$ig,"📅 Você não possui escalas *confirmadas* nos próximos 30 dias.\\n\\n".v1435_home_text($profiles),'volunteer_no_confirmed_days');}
    if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_scales',array_slice($days,0,20),null,null,$session);
    $msg=v1435_days_text($days,'📅 *Dias em que você está escalado e já confirmou:*')."\\n➡️ Digite *0* ou *MENU* para voltar.";
    return v1311p_send($sender,$ig,$msg,'volunteer_confirmed_days',['count'=>count($days)]);
}
'''
new='''function v1435_show_days(string $sender,array $profiles,?array $session=null): bool {
    $secretaria=v1445_is_secretary($profiles);$days=v1445_menu_days($profiles);$ig=v1435_igreja_id($profiles);
    if(!$days){if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_home',[],null,null,$session);$empty=$secretaria?'📅 Não encontrei escalas da igreja nos próximos 90 dias.':'📅 Você não possui escalas *confirmadas* nos próximos 30 dias.';return v1311p_send($sender,$ig,$empty."\\n\\n".v1435_home_text($profiles),'volunteer_no_confirmed_days');}
    if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_scales',array_slice($days,0,20),null,null,$session);
    $title=$secretaria?'📅 *Escalas da igreja:*':'📅 *Dias em que você está escalado e já confirmou:*';$msg=v1435_days_text($days,$title)."\\n➡️ Digite *0* ou *MENU* para voltar.";
    return v1311p_send($sender,$ig,$msg,'volunteer_confirmed_days',['count'=>count($days),'secretaria'=>$secretaria]);
}
'''
menu=rep(menu,old,new,'secretary days')
menu=rep(menu,"$days=v1435_confirmed_days($profiles);$ig=v1435_igreja_id($profiles);\n    if(!$days){if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_home',[],null,null,$session);return v1311p_send($sender,$ig,\"🎵 Não encontrei escala confirmada sua nos próximos 30 dias para consultar repertório.\\n\\n\".v1435_home_text($profiles),'volunteer_no_music_scale');}","$secretaria=v1445_is_secretary($profiles);$days=v1445_menu_days($profiles);$ig=v1435_igreja_id($profiles);\n    if(!$days){if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_home',[],null,null,$session);$empty=$secretaria?\"🎵 Não encontrei escalas da igreja nos próximos 90 dias para consultar repertório.\":\"🎵 Não encontrei escala confirmada sua nos próximos 30 dias para consultar repertório.\";return v1311p_send($sender,$ig,$empty.\"\\n\\n\".v1435_home_text($profiles),'volunteer_no_music_scale');}",'secretary music choices')
menu=rep(menu,"$days=v1435_confirmed_days($profiles);$ig=v1435_igreja_id($profiles);\n    if(!$days){if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_home',[],null,null,$session);return v1311p_send($sender,$ig,\"📄 Não encontrei escala confirmada sua nos próximos 30 dias para gerar PDF.\\n\\n\".v1435_home_text($profiles),'volunteer_no_pdf_scale');}","$secretaria=v1445_is_secretary($profiles);$days=v1445_menu_days($profiles);$ig=v1435_igreja_id($profiles);\n    if(!$days){if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_home',[],null,null,$session);$empty=$secretaria?\"📄 Não encontrei escalas da igreja nos próximos 90 dias para gerar PDF.\":\"📄 Não encontrei escala confirmada sua nos próximos 30 dias para gerar PDF.\";return v1311p_send($sender,$ig,$empty.\"\\n\\n\".v1435_home_text($profiles),'volunteer_no_pdf_scale');}",'secretary pdf choices')
menu=rep(menu,"return v1311p_send($sender,v1435_igreja_id($profiles),v1435_days_text($opts,'📅 *Dias em que você está escalado e já confirmou:*').\"\\n➡️ Digite *0* ou *MENU* para voltar.\",'volunteer_days_readonly');","$title=v1445_is_secretary($profiles)?'📅 *Escalas da igreja:*':'📅 *Dias em que você está escalado e já confirmou:*';return v1311p_send($sender,v1435_igreja_id($profiles),v1435_days_text($opts,$title).\"\\n➡️ Digite *0* ou *MENU* para voltar.\",'volunteer_days_readonly');",'secretary readonly title')
menu=rep(menu,"$r=v1435_scale_row((string)$opts[$idx]['item_id']);if(!$r||($r['status_confirmacao']??'')!=='confirmado')return v1436_show_music_choices($sender,$profiles,$session);","$r=v1445_selected_scale($opts[$idx],$profiles);if(!$r)return v1436_show_music_choices($sender,$profiles,$session);",'secretary music selection')
menu=rep(menu,"$r=v1435_scale_row((string)$opts[$idx]['item_id']);if(!$r||($r['status_confirmacao']??'')!=='confirmado')return v1435_show_pdf_choices($sender,$profiles,$session);","$r=v1445_selected_scale($opts[$idx],$profiles);if(!$r)return v1435_show_pdf_choices($sender,$profiles,$session);",'secretary pdf selection')
p.write_text(menu,encoding='utf-8')

(root/'VERSION').write_text('1.4.45\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.45.md').write_text('''# Escala de Propósito v1.4.45\n\n- Cria o novo cargo **Secretária**.\n- A Secretária pode consultar **todas as escalas da igreja**, mesmo sem estar escalada, além de acessar o **repertório**, imprimir e baixar PDF.\n- O cargo Secretária permanece em **modo de visualização**: não recebe as permissões de edição/gestão de escala do Pastor/Admin.\n- O menu do WhatsApp reconhece Secretária e permite consultar as escalas da igreja, repertório e receber a escala completa em PDF sem depender de estar escalada naquele dia.\n- Padroniza a ordenação de escalas em todo o fluxo principal: **departamento em ordem alfabética**, **função em ordem natural numérica + alfabética** e **nome em ordem alfabética**.\n- Aplica a mesma ordenação à tela de escalas, escala completa, impressão, PDF do painel e PDF enviado/gerado pelo WhatsApp.\n- Mantém a ordem manual do repertório de músicas, pois ela representa a sequência definida para o culto.\n- Não altera confirmações já registradas, pagamentos, migração ou dados existentes.\n''',encoding='utf-8')
