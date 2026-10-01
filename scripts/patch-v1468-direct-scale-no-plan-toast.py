from pathlib import Path
import re

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

def one(text,old,new,label):
    c=text.count(old)
    if c!=1:
        raise SystemExit(f'{label}: anchor count={c}')
    return text.replace(old,new,1)

# 1) Corrige o wrapper da v1.4.65: b(id) abria a tela intermediaria.
old='children:Ne.map((ce,me)=>r.jsx("div",{className:"contents",onClickCapture:it=>{if(it.target.closest("button,a,input,select,textarea,[role=button]"))return;it.preventDefault(),it.stopPropagation(),b(ce.id)},children:ke(ce,me)},ce.id))'
new='children:Ne.map((ce,me)=>r.jsx("div",{className:"contents",onClickCapture:it=>{if(it.target.closest("button,a,input,select,textarea,[role=button]"))return;it.preventDefault(),it.stopPropagation(),window.location.href="/escala/"+encodeURIComponent(ce.id)},children:ke(ce,me)},ce.id))'
s=one(s,old,new,'department card direct route')

# 2) Chips dos departamentos vao direto para a Escala Completa.
old='children:Ne.map(ce=>r.jsx(ht,{variant:"outline",className:"text-[10px] bg-background",children:(ce.departamentos&&ce.departamentos.nome)||"Departamento"},ce.id))'
new='children:Ne.map(ce=>r.jsx(ht,{variant:"outline",className:"text-[10px] bg-background cursor-pointer hover:bg-primary/5",onClick:it=>{it.preventDefault(),it.stopPropagation(),window.location.href="/escala/"+encodeURIComponent(ce.id)},children:(ce.departamentos&&ce.departamentos.nome)||"Departamento"},ce.id))'
s=one(s,old,new,'department chips direct route')

# 3) Lapiz do cartao tambem abre a rota real.
old='onClick:it=>{at.light(),it.stopPropagation(),b(ae.id)},"aria-label":"Abrir escala completa para editar pessoas"'
new='onClick:it=>{at.light(),it.stopPropagation(),window.location.href="/escala/"+encodeURIComponent(ae.id)},"aria-label":"Abrir escala completa para editar pessoas"'
s=one(s,old,new,'pencil direct route')

asset.write_text(s,encoding='utf-8')

# 4) Plano sem WhatsApp continua adaptando os textos, mas sem aviso flutuante.
old_guard=root/'plan-feature-guard-v1467.js'
g=old_guard.read_text(encoding='utf-8')
g2,n=re.subn(r'\nfunction addPlanInfo\(\)\{.*?\n\}\n\nfunction applyNoWhatsapp', '\nfunction applyNoWhatsapp', g, count=1, flags=re.S)
if n!=1:
    raise SystemExit('addPlanInfo function not found')
g2=g2.replace('  addPlanInfo();\n','')
(root/'plan-feature-guard-v1468.js').write_text(g2,encoding='utf-8')

# 5) Carrega o guard novo e faz cache-bust do bundle principal.
p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h=h.replace('<script src="/plan-feature-guard-v1467.js?v=1.4.67" defer></script>',
            '<script src="/plan-feature-guard-v1468.js?v=1.4.68" defer></script>')
if 'plan-feature-guard-v1468.js?v=1.4.68' not in h:
    raise SystemExit('guard v1468 not loaded')

h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',r'\1?v=1.4.68\2',h,count=1)
if n!=1:
    raise SystemExit('main asset script tag not found for cache bust')
p.write_text(h,encoding='utf-8')

# 6) Bump simples do service worker.
p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw='/* escala-version:1.4.68 */\n'+sw
p.write_text(sw,encoding='utf-8')

(root/'VERSION').write_text('1.4.68\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.68.md').write_text('''# Escala de Propósito v1.4.68 — Acesso direto à Escala Completa

- Remove totalmente o aviso flutuante "Comunicação pelo aplicativo" para planos sem WhatsApp.
- A diferenciação do plano continua silenciosa: apenas textos e recursos disponíveis se ajustam ao plano contratado.
- Corrige a causa real do clique no departamento: a v1.4.65 chamava a seleção interna que abre a tela intermediária.
- Agora o cartão do departamento navega diretamente para a rota da Escala Completa.
- Os chips com os nomes dos departamentos também são clicáveis e levam direto à Escala Completa.
- O lápis do cartão também passa a navegar diretamente para a Escala Completa.
- Botões internos continuam protegidos contra o clique do cartão.
- Adiciona cache-bust v1.4.68 ao bundle principal e atualiza o service worker para evitar JavaScript antigo em cache.
- Mantém as regras de comunicação por plano: com WhatsApp continua normal; sem WhatsApp usa textos do aplicativo e oculta configurações específicas de WhatsApp.
''',encoding='utf-8')
