from pathlib import Path

root = Path('pkg')
asset = next((root / 'assets').glob('index-*.js'))
js = asset.read_text(encoding='utf-8')

# Escala completa: vagas do template em ordem natural (numero + texto).
old = 'x.map(pe=>r.jsxs("div",{className:"flex items-center gap-2 p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/5"'
new = '[...x].sort((pe,q)=>String(pe.funcao||"").localeCompare(String(q.funcao||""),"pt-BR",{numeric:!0,sensitivity:"base"})||(pe.index||0)-(q.index||0)).map(pe=>r.jsxs("div",{className:"flex items-center gap-2 p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/5"'
if js.count(old) != 1:
    raise SystemExit(f'open-slot sorting anchor count={js.count(old)}')
js = js.replace(old, new, 1)

# Voluntarios dos seletores em ordem alfabetica.
replacements = [
    ('j.map(q=>r.jsx(nt,{value:q.id', '[...j].sort((q,pe)=>String(q.nome||"").localeCompare(String(pe.nome||""),"pt-BR",{sensitivity:"base"})).map(q=>r.jsx(nt,{value:q.id'),
    ('j.map(pe=>r.jsx(nt,{value:pe.id', '[...j].sort((pe,q)=>String(pe.nome||"").localeCompare(String(q.nome||""),"pt-BR",{sensitivity:"base"})).map(pe=>r.jsx(nt,{value:pe.id'),
    ('F.map(oe=>r.jsx(nt,{value:oe.id', '[...F].sort((oe,xe)=>String(oe.nome||"").localeCompare(String(xe.nome||""),"pt-BR",{sensitivity:"base"})).map(oe=>r.jsx(nt,{value:oe.id'),
]
for old, new in replacements:
    if js.count(old) != 1:
        raise SystemExit(f'volunteer selector anchor count={js.count(old)}: {old}')
    js = js.replace(old, new, 1)

# Lista principal de voluntarios/funcoes em ordem natural da funcao e depois nome.
old = 'd.map(pe=>{var xe;const q=Vf(pe.status_confirmacao)'
new = '[...d].sort((pe,q)=>String(pe.funcao||"").localeCompare(String(q.funcao||""),"pt-BR",{numeric:!0,sensitivity:"base"})||String(pe.profile&&pe.profile.nome||"").localeCompare(String(q.profile&&q.profile.nome||""),"pt-BR",{sensitivity:"base"})).map(pe=>{var xe;const q=Vf(pe.status_confirmacao)'
if js.count(old) != 1:
    raise SystemExit(f'main scheduled-list anchor count={js.count(old)}')
js = js.replace(old, new, 1)

# Outros departamentos: departamento alfabetico; dentro dele, funcao natural + nome.
old = 'b.map(pe=>{var q,oe;return r.jsxs("div"'
new = '[...b].sort((pe,q)=>String(pe.dept&&pe.dept.nome||"").localeCompare(String(q.dept&&q.dept.nome||""),"pt-BR",{sensitivity:"base"})).map(pe=>{var q,oe;return r.jsxs("div"'
if js.count(old) != 1:
    raise SystemExit(f'department-list anchor count={js.count(old)}')
js = js.replace(old, new, 1)

old = 'pe.itens.map(xe=>{var ke;const ge=Vf(xe.status_confirmacao)'
new = '[...pe.itens].sort((xe,ge)=>String(xe.funcao||"").localeCompare(String(ge.funcao||""),"pt-BR",{numeric:!0,sensitivity:"base"})||String(xe.profile&&xe.profile.nome||"").localeCompare(String(ge.profile&&ge.profile.nome||""),"pt-BR",{sensitivity:"base"})).map(xe=>{var ke;const ge=Vf(xe.status_confirmacao)'
if js.count(old) != 1:
    raise SystemExit(f'other-department items anchor count={js.count(old)}')
js = js.replace(old, new, 1)

asset.write_text(js, encoding='utf-8')
(root / 'VERSION').write_text('1.4.44\n', encoding='utf-8')
(root / 'ATUALIZACAO-v1.4.44.md').write_text('''# Escala de Propósito v1.4.44\n\n- Organiza a tela **Escala Completa** para facilitar a leitura e o preenchimento.\n- As funções/vagas do template passam a usar **ordem natural numérica e alfabética** (ex.: 1, 2, 3... e depois o texto da função).\n- Voluntários nos campos **Escalar voluntário** passam a aparecer em **ordem alfabética pelo nome**.\n- A lista de voluntários já escalados é organizada pela função e, em caso de empate, pelo nome.\n- Na seção de outros departamentos, os departamentos ficam em ordem alfabética e as funções em ordem natural.\n- Não altera dados, permissões, WhatsApp, banco de dados nem regras de confirmação da escala.\n''', encoding='utf-8')
