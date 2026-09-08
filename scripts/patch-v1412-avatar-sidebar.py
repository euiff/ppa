from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'pkg')
js = root / 'assets/index-C6Ng0a8i.js'
s = js.read_text()

# App provider: carrega avatar do usuário, atualiza imediatamente após upload
# e mantém a logo da igreja como fallback.
old = '''jV=({children:e})=>{const{igrejaId:t,userRole:n,user:s}=Bt(),[a,i]=h.useState("admin"),[l,c]=h.useState("Escala de Propósito"),[d,f]=h.useState(""),[m,g]=h.useState(null),[x,v]=h.useState(null);return h.useEffect(()=>{if(!s){f("");return}I.from("profiles").select("nome").eq("id",s.id).maybeSingle().then(({data:j})=>{j!=null&&j.nome&&f(j.nome)})},[s]),h.useEffect(()=>{if(!t){c(n==="master"?"Painel Master":"Escala de Propósito"),g(null);return}I.from("igrejas").select("nome, logo_url").eq("id",t).maybeSingle().then(({data:j})=>{j!=null&&j.nome&&c(j.nome),g((j==null?void 0:j.logo_url)??null)})},[t,n]),r.jsx(iP.Provider,{value:{viewMode:a,setViewMode:i,institutionName:l,userName:d,churchLogoUrl:m,pendingQuiz:x,setPendingQuiz:v},children:e})}'''
new = '''jV=({children:e})=>{const{igrejaId:t,userRole:n,user:s}=Bt(),[a,i]=h.useState("admin"),[l,c]=h.useState("Escala de Propósito"),[d,f]=h.useState(""),[m,g]=h.useState(null),[u,p]=h.useState(null),[x,v]=h.useState(null);return h.useEffect(()=>{if(!s){f(""),p(null);return}const j=()=>I.from("profiles").select("nome, avatar_url").eq("id",s.id).maybeSingle().then(({data:w})=>{w!=null&&w.nome&&f(w.nome),p((w==null?void 0:w.avatar_url)??null)});return j(),window.addEventListener("escala-profile-updated",j),()=>window.removeEventListener("escala-profile-updated",j)},[s]),h.useEffect(()=>{if(!t){c(n==="master"?"Painel Master":"Escala de Propósito"),g(null);return}I.from("igrejas").select("nome, logo_url").eq("id",t).maybeSingle().then(({data:j})=>{j!=null&&j.nome&&c(j.nome),g((j==null?void 0:j.logo_url)??null)})},[t,n]),r.jsx(iP.Provider,{value:{viewMode:a,setViewMode:i,institutionName:l,userName:d,churchLogoUrl:m,userAvatarUrl:u,pendingQuiz:x,setPendingQuiz:v},children:e})}'''
if old not in s:
    raise SystemExit('provider anchor not found')
s = s.replace(old, new, 1)

# Layout lateral: prioridade foto do usuário > logo da igreja > ícone padrão.
old = '''nQ=({children:e})=>{const{signOut:t,userRole:n}=Bt(),{viewMode:s,setViewMode:a,institutionName:i,userName:l,churchLogoUrl:c}=Lo(),{unreadCount:d}=uP()'''
new = '''nQ=({children:e})=>{const{signOut:t,userRole:n}=Bt(),{viewMode:s,setViewMode:a,institutionName:i,userName:l,churchLogoUrl:c,userAvatarUrl:avatar}=Lo(),{unreadCount:d}=uP()'''
if old not in s:
    raise SystemExit('layout destructure anchor not found')
s = s.replace(old, new, 1)

old_desktop = '''c?r.jsx("img",{src:c,alt:i,className:"w-10 h-10 rounded-xl object-cover shadow-lg"}):r.jsx("div",{className:"brand-mark w-11 h-11 rounded-2xl flex items-center justify-center shadow-lg",children:r.jsx(ys,{className:"w-5 h-5 text-sidebar-accent-foreground"})})'''
new_desktop = '''(avatar||c)?r.jsx("img",{src:avatar||c,alt:l||i,className:"w-11 h-11 rounded-full object-cover shadow-lg ring-2 ring-white/10"}):r.jsx("div",{className:"brand-mark w-11 h-11 rounded-2xl flex items-center justify-center shadow-lg",children:r.jsx(ys,{className:"w-5 h-5 text-sidebar-accent-foreground"})})'''
if old_desktop not in s:
    raise SystemExit('desktop avatar anchor not found')
s = s.replace(old_desktop, new_desktop, 1)

old_small = '''c?r.jsx("img",{src:c,alt:i,className:"w-8 h-8 rounded-lg object-cover"}):r.jsx("div",{className:"w-8 h-8 rounded-lg bg-sidebar-accent flex items-center justify-center",children:r.jsx(ys,{className:"w-4 h-4 text-sidebar-accent-foreground"})})'''
new_small = '''(avatar||c)?r.jsx("img",{src:avatar||c,alt:l||i,className:"w-8 h-8 rounded-full object-cover ring-1 ring-white/10"}):r.jsx("div",{className:"w-8 h-8 rounded-lg bg-sidebar-accent flex items-center justify-center",children:r.jsx(ys,{className:"w-4 h-4 text-sidebar-accent-foreground"})})'''
if s.count(old_small) < 2:
    raise SystemExit('collapsed/mobile avatar anchors not found')
s = s.replace(old_small, new_small)

# Lista de voluntários: foto do voluntário; se não houver, mostra a logo da igreja;
# se a igreja também não tiver logo, mantém a inicial do nome.
old = '''wG=()=>{const{userRole:e,igrejaId:t,userDepartments:n}=Bt(),{viewMode:s}=Lo(),'''
new = '''wG=()=>{const{userRole:e,igrejaId:t,userDepartments:n}=Bt(),{viewMode:s,churchLogoUrl:churchFallback}=Lo(),'''
if old not in s:
    raise SystemExit('volunteer page destructure anchor not found')
s = s.replace(old, new, 1)

old_card = '''children:fe.avatar_url?r.jsx("img",{src:fe.avatar_url,alt:`Foto de ${fe.nome||"voluntário"}`,className:"w-14 h-14 rounded-2xl object-cover shadow-sm ring-2 ring-background group-hover:ring-primary/10 transition-all"}):r.jsx("div",{className:"w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 via-indigo-500/10 to-cyan-500/20 flex items-center justify-center text-primary font-black text-lg shadow-inner",children:(Wt=(en=fe.nome)==null?void 0:en.charAt(0))==null?void 0:Wt.toUpperCase()})'''
new_card = '''children:(fe.avatar_url||churchFallback)?r.jsx("img",{src:fe.avatar_url||churchFallback,alt:fe.avatar_url?`Foto de ${fe.nome||"voluntário"}`:"Logo da igreja",className:"w-14 h-14 rounded-2xl object-cover shadow-sm ring-2 ring-background group-hover:ring-primary/10 transition-all"}):r.jsx("div",{className:"w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 via-indigo-500/10 to-cyan-500/20 flex items-center justify-center text-primary font-black text-lg shadow-inner",children:(Wt=(en=fe.nome)==null?void 0:en.charAt(0))==null?void 0:Wt.toUpperCase()})'''
if old_card not in s:
    raise SystemExit('volunteer card avatar anchor not found')
s = s.replace(old_card, new_card, 1)

js.write_text(s)

# Cache bust para PWA e navegador receberem o novo avatar no layout.
h = root / 'sistema.html'
t = h.read_text()
t = re.sub(r'/assets/index-C6Ng0a8i\.js\?v[^\"\']*', '/assets/index-C6Ng0a8i.js?v=1.4.12', t)
h.write_text(t)

sw = root / 'sw.js'
t = sw.read_text()
t = re.sub(r'url:\"assets/index-C6Ng0a8i\.js\",revision:(?:null|\"[^\"]*\")', 'url:\"assets/index-C6Ng0a8i.js\",revision:\"v1412-avatar-sidebar\"', t)
if 'avatar-sidebar-cache-bust-v1.4.12' not in t:
    t += '\n/* avatar-sidebar-cache-bust-v1.4.12 */\n'
sw.write_text(t)

(root / 'registerSW.js').write_text("if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const r=await navigator.serviceWorker.register('/sw.js?v=1.4.12',{scope:'/',updateViaCache:'none'});await r.update()}catch(e){console.warn('[SW v1.4.12]',e)}})}")
