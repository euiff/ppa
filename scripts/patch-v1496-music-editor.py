from pathlib import Path
import re

root=Path("pkg")
api_target=root/"api"/"music-edit-v1496.php"
api_target.write_text(
    Path("runtime/v1496/api/music-edit-v1496.php").read_text(encoding="utf-8"),
    encoding="utf-8"
)
asset=next((root/"assets").glob("index-*.js"))
s=asset.read_text(encoding="utf-8")
def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{label}: expected 1 anchor, got {n}")
    s=s.replace(old,new,1)

# Authorization for showing the pencil: pastor/admin/master and leaders of the church.
# Effective authorization is always revalidated by /api/music-edit-v1496.php.
old='const R=t==="admin"||t==="master"||U,O=async()=>'
new='''const R=t==="admin"||t==="master"||U,
M=R||t==="pastor"||t==="lider",
[$E1496,$SET1496]=h.useState(null),
[$S1496,$SS1496]=h.useState(!1),
ed1496=B=>{
  $SET1496(B);
  x({titulo:B.titulo||"",artista:B.artista||"",tom:B.tom||"",
     link_spotify:B.link_spotify||"",link_youtube:B.link_youtube||"",
     link_cifra:B.link_cifra||"",letra:B.letra||"",cifra:B.cifra||""});
  j("");S([]);d(!0);
},
save1496=async()=>{
  if(!$E1496||$S1496)return;
  if(!String(g.titulo||"").trim()){V.error("Informe o título da música");return}
  const igreja=$E1496.igreja_id||n;
  if(!igreja){V.error("Não foi possível identificar a igreja desta música");return}
  $SS1496(!0);
  try{
    const auth=localStorage.getItem("escala-facil.auth-token")||"";
    const body={id:$E1496.id,igreja_id:igreja,
      titulo:String(g.titulo||"").trim(),
      artista:String(g.artista||""),
      tom:String(g.tom||""),
      link_youtube:String(g.link_youtube||""),
      link_spotify:String(g.link_spotify||""),
      link_cifra:String(g.link_cifra||""),
      letra:String(g.letra||""),
      cifra:String(g.cifra||"")};
    const resp=await fetch("/api/music-edit-v1496.php",{
      method:"POST",credentials:"same-origin",cache:"no-store",
      headers:{"Authorization":"Bearer "+auth,"Content-Type":"application/json","Accept":"application/json"},
      body:JSON.stringify(body)
    });
    let result=null;
    try{result=await resp.json()}catch(err){}
    if(!resp.ok||!result||result.error){
      throw new Error(result&&result.error&&result.error.message||"Falha ao salvar música (HTTP "+resp.status+")");
    }
    V.success("Música atualizada com sucesso!");
    d(!1);$SET1496(null);j("");S([]);O();
    T(old=>old&&old.id===$E1496.id?{...old,...(result.data&&result.data.music||body)}:old);
  }catch(err){
    V.error(err&&err.message||"Erro ao salvar alterações da música");
  }finally{$SS1496(!1)}
},
O=async()=>'''
once(old,new,"hook, permissions and save handler")

# Dialog reuse: leaders/pastors may edit without exposing the Add button
once('R&&r.jsxs(zt,{open:c,onOpenChange:d,children:[r.jsx(sr,{asChild:!0',
     'M&&r.jsxs(zt,{open:c,onOpenChange:d,children:[R&&r.jsx(sr,{asChild:!0',
     "repertoire editor dialog")
once('onClick:()=>at.light(),children:[r.jsx(In,{className:"w-4 h-4 mr-2"})," Adicionar"]',
     'onClick:()=>{at.light(),$SET1496(null),x({titulo:"",artista:"",tom:"",link_spotify:"",link_youtube:"",link_cifra:"",letra:"",cifra:""}),j(""),S([])},children:[r.jsx(In,{className:"w-4 h-4 mr-2"})," Adicionar"]',
     "add reset")
once('r.jsx(Vt,{children:"Nova Música"})',
     'r.jsx(Vt,{children:$E1496?"Editar Música":"Nova Música"})',
     "dialog title")
once('r.jsx(Vt,{children:"Nova Música"})', 'r.jsx(Vt,{children:$E1496?"Editar Música":"Nova Música"})',"second dialog title") if False else None

# The same form edits the full details, including lyrics and chords.
old='r.jsx(ie,{onClick:()=>{at.medium(),se()},className:"w-full h-11 text-sm font-bold rounded-xl shadow-lg active:scale-95 transition-all",children:"Adicionar Música"})'
new='''r.jsxs("div",{className:"space-y-1.5",children:[
r.jsx(_e,{className:"text-xs",children:"Cifra (opcional)"}),
r.jsx("textarea",{value:g.cifra||"",onChange:B=>x({...g,cifra:B.target.value}),
placeholder:"Cole ou edite a cifra...",className:"w-full h-32 text-sm border border-input rounded-md px-3 py-2 bg-background focus:ring-1 focus:ring-primary outline-none"})
]}),
r.jsx(ie,{disabled:$S1496,onClick:()=>{at.medium(),$E1496?save1496():se()},className:"w-full h-11 text-sm font-bold rounded-xl shadow-lg active:scale-95 transition-all",children:$E1496?($S1496?"Salvando...":"Salvar alterações"):"Adicionar Música"})'''
once(old,new,"editable textarea and save")

# On every song row a compact pencil next to existing Spotify/YouTube/Cifra/Delete controls.
old='R&&r.jsx("button",{onClick:()=>Q(B.id,B.created_by),className:"p-1.5 rounded hover:bg-secondary",children:r.jsx(Ss,{className:"w-3.5 h-3.5 text-destructive"})})'
new='''M&&r.jsx("button",{type:"button",title:"Editar música","aria-label":"Editar música "+B.titulo,
onClick:()=>{at.light(),ed1496(B)},className:"p-1.5 rounded hover:bg-secondary text-primary text-base leading-none",children:"✏️"}),
R&&r.jsx("button",{onClick:()=>Q(B.id,B.created_by),className:"p-1.5 rounded hover:bg-secondary",children:r.jsx(Ss,{className:"w-3.5 h-3.5 text-destructive"})})'''
once(old,new,"edit pencil on repertoire song row")

# Do not mix songs from different congregations in the editor list.
old='O=async()=>{l(!0);const{data:B}=await I.from("musicas").select("*").order("titulo");a(B||[]),l(!1)}'
new='O=async()=>{l(!0);let query=I.from("musicas").select("*").order("titulo");n&&(query=query.eq("igreja_id",n));const{data:B,error:re}=await query;re&&V.error("Não foi possível carregar o repertório"),a(B||[]),l(!1)}'
once(old,new,"church scoped list query")
asset.write_text(s,encoding="utf-8")

p=root/"sistema.html"
h=p.read_text(encoding="utf-8")
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
             lambda m:m.group(1)+"?v=1.4.96"+m.group(2),h,count=1)
if n!=1:raise RuntimeError("index js cache-bust anchor missing")
for name in ["holyrics-entry-v1481.js","app-notifications-v1465.js",
             "whatsapp-group-settings-v1473.js","master-whatsapp-groups-entry-v1475.js","cron-fix-v1478.js"]:
    h=h.replace(name+"?v=1.4.95",name+"?v=1.4.96")
p.write_text(h,encoding="utf-8")

p=root/"sw.js"
sw=p.read_text(encoding="utf-8")
sw=re.sub(r"^/\* escala-version:[^*]+\*/\n?","",sw,count=1)
p.write_text("/* escala-version:1.4.96 */\n"+sw,encoding="utf-8")
(root/"VERSION").write_text("1.4.96\n",encoding="utf-8")
(root/"ATUALIZACAO-v1.4.96.md").write_text("""# Escala de Propósito v1.4.96 — Editar músicas do repertório

- Na tela **Louvor → Repertório**, cada música possui agora um botão de lápis **Editar música** junto aos ícones já existentes.
- Pastor, administrador e líderes de departamento autorizados podem abrir a música, alterar título, artista, tom, links, letra e cifra e **Salvar alterações**.
- Reaproveita o mesmo formulário de cadastro: o título muda para **Editar Música** e os campos são preenchidos com os valores atuais.
- O modo **Adicionar Música** continua intacto; a janela é limpa ao criar uma música nova e não duplica registros ao editar.
- A edição faz UPDATE do mesmo registro (sem apagar ou recriar), preservando associações com escalas, setlists e repertórios publicados.
- O endpoint autenticado valida o papel de pastor/admin/master e, para líder, confere que ele realmente lidera algum departamento da igreja.
- A atualização no banco exige correspondência simultânea entre música e igreja, proibindo alteração de outras igrejas.
- Campos validados (tamanho, título obrigatório, link HTTP(S), tom musical); falhas apresentam mensagem e não fecham o editor.
- O menu Repertório passa a consultar somente músicas da igreja ativa, se houver igreja selecionada.
- Nenhuma alteração nas escalas, notificações, WhatsApp, grupos e Holyrics.
- Os testes automatizados não substituem o teste do login real e da edição efetiva no celular.
""",encoding="utf-8")
