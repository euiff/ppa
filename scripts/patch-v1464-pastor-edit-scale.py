from pathlib import Path

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

old='r.jsx("div",{className:"flex justify-end",children:r.jsx("a",{href:`/culto?data=${encodeURIComponent(ve.data||"")}&culto_id=${encodeURIComponent((ve.culto&&ve.culto.id)||"")}`,className:"inline-flex items-center justify-center rounded-xl bg-primary text-primary-foreground px-3 py-2 text-xs font-bold hover:opacity-90",onClick:ce=>ce.stopPropagation(),children:"Página do culto"})})'
new='r.jsxs("div",{className:"flex justify-end gap-2 flex-wrap",children:[t==="admin"&&r.jsx("a",{href:`/pastor-editar-escala.html?data=${encodeURIComponent(ve.data||"")}&culto_id=${encodeURIComponent((ve.culto&&ve.culto.id)||"")}`,className:"inline-flex items-center justify-center rounded-xl border border-primary/30 bg-background text-primary px-3 py-2 text-xs font-bold hover:bg-primary/5",onClick:ce=>ce.stopPropagation(),children:"✏️ Editar dados"}),r.jsx("a",{href:`/culto?data=${encodeURIComponent(ve.data||"")}&culto_id=${encodeURIComponent((ve.culto&&ve.culto.id)||"")}`,className:"inline-flex items-center justify-center rounded-xl bg-primary text-primary-foreground px-3 py-2 text-xs font-bold hover:opacity-90",onClick:ce=>ce.stopPropagation(),children:"Página do culto"})]})'
c=s.count(old)
if c!=1:
    raise SystemExit(f'pastor button anchor count={c}')
asset.write_text(s.replace(old,new,1),encoding='utf-8')

api=r'''<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
require_once __DIR__.'/system_observer_v1423.php';
system_observer_v1423_register();

$caller=require_auth();
$ctx=user_context();
$role=(string)($ctx['role']??'');
$ig=(string)($ctx['igreja_id']??'');
if($role!=='admin') out(['data'=>null,'error'=>['message'=>'Somente o Pastor pode editar os dados da escala.']],403);
if($ig==='') out(['data'=>null,'error'=>['message'=>'Igreja não identificada.']],400);

function pse_valid_date(string $d,string $label): string {
    $x=DateTime::createFromFormat('Y-m-d',$d);
    if(!$x||$x->format('Y-m-d')!==$d) throw new RuntimeException($label.' inválida.');
    return $d;
}
function pse_valid_time(string $t): ?string {
    $t=trim($t);
    if($t==='') return null;
    if(!preg_match('/^(?:[01]\\d|2[0-3]):[0-5]\\d$/',$t)) throw new RuntimeException('Horário inválido. Use HH:MM.');
    return $t.':00';
}
function pse_group_where(string $ig,string $date,?string $cultoId,array &$args,string $alias='e'): string {
    $args=[$ig,$date];
    $w="BINARY {$alias}.igreja_id=BINARY ? AND {$alias}.data=?";
    if($cultoId===null||$cultoId==='') $w.=" AND {$alias}.culto_id IS NULL";
    else {$w.=" AND BINARY {$alias}.culto_id=BINARY ?";$args[]=$cultoId;}
    return $w;
}
function pse_one(string $ig,string $date,?string $cultoId): ?array {
    $a=[];$w=pse_group_where($ig,$date,$cultoId,$a);
    $sql="SELECT e.igreja_id,e.data,e.culto_id,COALESCE(c.nome,'Escala sem culto') culto_nome,c.horario,
                 COUNT(DISTINCT e.id) departamentos,COUNT(ei.id) itens,
                 SUM(CASE WHEN e.status='publicado' THEN 1 ELSE 0 END) publicadas
          FROM escalas e
          LEFT JOIN cultos c ON BINARY c.id=BINARY e.culto_id
          LEFT JOIN escala_itens ei ON BINARY ei.escala_id=BINARY e.id
          WHERE {$w}
          GROUP BY e.igreja_id,e.data,e.culto_id,c.nome,c.horario
          LIMIT 1";
    $q=db()->prepare($sql);$q->execute($a);$r=$q->fetch(PDO::FETCH_ASSOC);
    return $r?:null;
}
function pse_duplicate_target(string $ig,string $newDate,string $newName,?string $newTime,string $oldDate,?string $oldCulto): bool {
    $hm=$newTime?substr($newTime,0,5):'';
    $sql="SELECT COUNT(DISTINCT e.id)
          FROM escalas e
          LEFT JOIN cultos c ON BINARY c.id=BINARY e.culto_id
          WHERE BINARY e.igreja_id=BINARY ? AND e.data=?
            AND LOWER(TRIM(COALESCE(c.nome,'')))=LOWER(TRIM(?))
            AND COALESCE(TIME_FORMAT(c.horario,'%H:%i'),'')=?";
    $a=[$ig,$newDate,$newName,$hm];
    if($newDate===$oldDate){
        if($oldCulto===null||$oldCulto==='') $sql.=" AND e.culto_id IS NOT NULL";
        else {$sql.=" AND (e.culto_id IS NULL OR BINARY e.culto_id<>BINARY ?)";$a[]=$oldCulto;}
    }
    $q=db()->prepare($sql);$q->execute($a);
    return (int)$q->fetchColumn()>0;
}
function pse_edit(string $ig,string $date,?string $cultoId,string $newDate,string $newName,?string $newTime,array $before): array {
    $newName=trim($newName);
    if($newName==='') throw new RuntimeException('Informe o nome da escala/culto.');
    $oldName=trim((string)($before['culto_nome']??''));
    $oldHm=substr((string)($before['horario']??''),0,5);
    $newHm=$newTime?substr($newTime,0,5):'';
    $clone=$cultoId===null||$cultoId===''||$newName!==$oldName||$newHm!==$oldHm;

    if(($newDate!==$date||$newName!==$oldName||$newHm!==$oldHm) &&
       pse_duplicate_target($ig,$newDate,$newName,$newTime,$date,$cultoId)){
        throw new RuntimeException('Já existe uma escala com esse nome e horário nessa data. Abra a escala existente ou escolha outros dados.');
    }

    $target=$cultoId;
    $pdo=db();$pdo->beginTransaction();
    try{
        if($clone){
            $target=uuid4();
            $q=$pdo->prepare("INSERT INTO cultos(created_at,dia_semana,horario,id,igreja_id,nome,recorrente) VALUES(NOW(),NULL,?,?,?,?,0)");
            $q->execute([$newTime,$target,$ig,$newName]);
        } elseif($newDate!==$date) {
            $a=[];$w=pse_group_where($ig,$newDate,$target,$a);
            $q=$pdo->prepare("SELECT COUNT(*) FROM escalas e WHERE {$w}");
            $q->execute($a);
            if((int)$q->fetchColumn()>0) throw new RuntimeException('Já existe uma escala desse culto na nova data.');
        }

        $a=[];$w=pse_group_where($ig,$date,$cultoId,$a);
        $sql=$clone
            ?"UPDATE escalas e SET e.data=?,e.culto_id=? WHERE {$w}"
            :"UPDATE escalas e SET e.data=? WHERE {$w}";
        $args=$clone?array_merge([$newDate,$target],$a):array_merge([$newDate],$a);
        $q=$pdo->prepare($sql);$q->execute($args);
        $n=$q->rowCount();
        if($n<1) throw new RuntimeException('A escala selecionada não existe mais. Atualize a página.');
        $pdo->commit();
    }catch(Throwable $e){
        if($pdo->inTransaction())$pdo->rollBack();
        throw $e;
    }
    return [
        'before'=>$before,
        'after'=>pse_one($ig,$newDate,$target),
        'updated_departments'=>$n,
        'culto_isolated'=>$clone
    ];
}

$b=$_SERVER['REQUEST_METHOD']==='POST'?input_json():$_GET;
$action=(string)($b['action']??'get');
try{
    $date=pse_valid_date(trim((string)($b['data']??'')),'Data da escala');
    $cultoRaw=$b['culto_id']??null;
    $cultoId=$cultoRaw===null||trim((string)$cultoRaw)===''?null:trim((string)$cultoRaw);
    $row=pse_one($ig,$date,$cultoId);
    if(!$row) throw new RuntimeException('A escala selecionada não existe ou não pertence à sua igreja.');

    if($action==='get') out(['data'=>$row,'error'=>null]);
    if($action!=='edit') throw new RuntimeException('Ação inválida.');

    $newDate=pse_valid_date(trim((string)($b['new_date']??'')),'Nova data');
    $newName=trim((string)($b['new_name']??''));
    $newTime=pse_valid_time(trim((string)($b['new_time']??'')));
    $edited=pse_edit($ig,$date,$cultoId,$newDate,$newName,$newTime,$row);

    try{
        audit(
            (string)($caller['id']??''),
            'pastor_edit_complete_scale',
            'escalas',
            [
                'igreja_id'=>$ig,
                'before'=>[
                    'data'=>$date,
                    'culto_id'=>$cultoId,
                    'nome'=>$row['culto_nome']??null,
                    'horario'=>$row['horario']??null
                ],
                'after'=>[
                    'data'=>$newDate,
                    'culto_id'=>$edited['after']['culto_id']??null,
                    'nome'=>$edited['after']['culto_nome']??$newName,
                    'horario'=>$edited['after']['horario']??$newTime
                ]
            ],
            'warning'
        );
    }catch(Throwable $e){}

    out(['data'=>['success'=>true,'edited'=>$edited],'error'=>null]);
}catch(Throwable $e){
    out(['data'=>null,'error'=>['message'=>$e->getMessage()]],400);
}
'''
(root/'api'/'pastor-scale-edit.php').write_text(api,encoding='utf-8')

page=r'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Editar escala — Pastor</title>
<style>
*{box-sizing:border-box}body{margin:0;font:14px Inter,Arial,sans-serif;background:#f5f7fb;color:#172033}.w{max-width:720px;margin:auto;padding:18px}.card{background:#fff;border:1px solid #e0e7f0;border-radius:18px;padding:18px;box-shadow:0 8px 30px #13223a0d}.top{display:flex;align-items:center;gap:12px;margin-bottom:16px}.back{border:0;background:#eef3f9;color:#32465f;border-radius:10px;padding:10px 12px;font-weight:800;cursor:pointer}.title{min-width:0}.title h1{margin:0;font-size:22px}.muted{color:#6c7b90;margin-top:4px}.note{background:#eff6ff;border:1px solid #cfe0fb;color:#315986;border-radius:12px;padding:11px;margin-bottom:16px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.field{display:grid;gap:6px}.full{grid-column:1/-1}label{font-weight:800}input{height:44px;border:1px solid #cbd6e5;border-radius:11px;padding:0 12px;font:inherit}.stats{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.pill{padding:6px 9px;border-radius:999px;background:#f0f4f8;color:#526176;font-size:12px;font-weight:800}.actions{display:flex;gap:9px;justify-content:flex-end;margin-top:18px}.btn{min-height:44px;border:0;border-radius:11px;padding:0 15px;font-weight:850;cursor:pointer}.primary{background:#1764e8;color:#fff}.secondary{background:#eef3f9;color:#31465f}.btn:disabled{opacity:.55;cursor:not-allowed}.msg{display:none;margin:0 0 14px;padding:11px;border-radius:10px}.msg.ok{display:block;background:#eaf8ef;color:#17643a}.msg.err{display:block;background:#fff0f0;color:#9a2525}.msg.info{display:block;background:#edf4ff;color:#234d89}@media(max-width:600px){.w{padding:12px}.grid{grid-template-columns:1fr}.full{grid-column:auto}.actions{flex-direction:column-reverse}.btn{width:100%}}
</style>
</head>
<body>
<main class="w">
  <div class="top">
    <button class="back" id="back">← Voltar</button>
    <div class="title"><h1>✏️ Editar dados da escala</h1><div class="muted">Exclusivo do Pastor</div></div>
  </div>
  <div id="msg" class="msg"></div>
  <section class="card">
    <div class="note"><b>Você pode corrigir nome, data e horário.</b> Departamentos, pessoas escaladas, funções, confirmações e repertório permanecem na escala.</div>
    <div class="stats" id="stats"></div>
    <div class="grid">
      <div class="field full"><label for="name">Nome da escala / culto</label><input id="name" maxlength="255" autocomplete="off"></div>
      <div class="field"><label for="date">Data</label><input id="date" type="date"></div>
      <div class="field"><label for="time">Horário</label><input id="time" type="time"></div>
    </div>
    <div class="actions">
      <button class="btn secondary" id="cancel">Cancelar</button>
      <button class="btn primary" id="save">Salvar alterações</button>
    </div>
  </section>
</main>
<script>
const token=localStorage.getItem('escala-facil.auth-token')||'';
const H={'Content-Type':'application/json',Accept:'application/json',...(token?{Authorization:'Bearer '+token}:{})};
const $=id=>document.getElementById(id);
const qs=new URLSearchParams(location.search);
let current={data:qs.get('data')||'',culto_id:qs.get('culto_id')||''},row=null,busy=false;
function message(t,c='info'){$('msg').className='msg '+c;$('msg').textContent=t}
function fmt(d){if(!d)return'';const [y,m,dd]=d.split('-');return dd+'/'+m+'/'+y}
async function api(body){
  const r=await fetch('/api/pastor-scale-edit.php',{method:'POST',credentials:'include',headers:H,body:JSON.stringify(body)});
  let j={};try{j=await r.json()}catch{}
  if(!r.ok||j.error)throw new Error(j?.error?.message||'Falha na operação');
  return j.data
}
function fill(r){
  row=r;
  $('name').value=r.culto_nome&&r.culto_nome!=='Escala sem culto'?r.culto_nome:'';
  $('date').value=r.data||'';
  $('time').value=r.horario?String(r.horario).slice(0,5):'';
  $('stats').innerHTML='<span class="pill">'+Number(r.departamentos||0)+' departamento(s)</span><span class="pill">'+Number(r.itens||0)+' pessoa(s)/item(ns)</span><span class="pill">'+(Number(r.publicadas||0)>0?'Publicada':'Rascunho')+'</span>'
}
async function load(){
  message('Carregando escala...','info');
  try{fill(await api({action:'get',data:current.data,culto_id:current.culto_id}));$('msg').className='msg'}
  catch(e){message(e.message,'err');$('save').disabled=true}
}
async function save(){
  if(!row||busy)return;
  const name=$('name').value.trim(),date=$('date').value,time=$('time').value;
  if(!name||!date){message('Informe nome e data.','err');return}
  const changed=name!==(row.culto_nome||'')||date!==row.data||time!==String(row.horario||'').slice(0,5);
  if(!changed){message('Nenhuma alteração foi feita.','info');return}
  if(!confirm('Salvar alteração desta escala?\n\n'+(row.culto_nome||'Escala')+' '+fmt(row.data)+' → '+name+' '+fmt(date)+(time?' às '+time:'')))return;
  busy=true;$('save').disabled=true;$('cancel').disabled=true;message('Salvando...','info');
  try{
    const d=await api({action:'edit',data:row.data,culto_id:row.culto_id,new_name:name,new_date:date,new_time:time});
    fill(d.edited.after);
    current={data:d.edited.after.data,culto_id:d.edited.after.culto_id||''};
    const u=new URL(location.href);u.searchParams.set('data',current.data);u.searchParams.set('culto_id',current.culto_id);history.replaceState(null,'',u);
    message('Escala atualizada. Pessoas, funções, confirmações e repertório foram preservados.','ok')
  }catch(e){message(e.message,'err')}
  finally{busy=false;$('save').disabled=false;$('cancel').disabled=false}
}
$('save').addEventListener('click',save);
$('back').addEventListener('click',()=>history.length>1?history.back():location.assign('/escalas'));
$('cancel').addEventListener('click',()=>history.length>1?history.back():location.assign('/escalas'));
load();
</script>
</body>
</html>
'''
(root/'pastor-editar-escala.html').write_text(page,encoding='utf-8')

(root/'VERSION').write_text('1.4.64\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.64.md').write_text('''# Escala de Propósito v1.4.64 — Pastor pode editar dados da escala

- Na lista agrupada de escalas, o perfil **Pastor (`admin`)** passa a ver **✏️ Editar dados** ao lado de **Página do culto**.
- A edição do Pastor é limitada a **nome da escala/culto, data e horário**.
- **Líder, Secretária e Voluntário não recebem essa opção.**
- O Master continua com a edição administrativa que já existia em **Master → Gerenciar escalas**.
- Ao mudar data, todos os departamentos daquela escala são movidos juntos.
- Ao mudar nome ou horário, o sistema cria um culto isolado para aquela escala, evitando alterar outras datas que usam o mesmo cadastro de culto.
- Pessoas escaladas, funções, confirmações, repertório e demais vínculos da escala são preservados.
- Há proteção contra criar outra escala com o mesmo nome e horário na data de destino.
- A alteração fica registrada na auditoria como `pastor_edit_complete_scale`.
''',encoding='utf-8')
