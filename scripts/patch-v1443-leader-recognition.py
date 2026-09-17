from pathlib import Path

root = Path('pkg')
asset = next((root / 'assets').glob('index-*.js'))
js = asset.read_text(encoding='utf-8')

# Na tela de Voluntários, user_roles continua sendo a fonte de permissão,
# mas a liderança REAL de departamento vem de departamentos.lider_id.
# Sobrepomos somente a apresentação local para líderes de departamento que
# não sejam admin/master. Isso preserva permissões administrativas e evita
# confundir participação no departamento com liderança.
old = 'const Ae={};(mt.data||[]).forEach(ts=>{Ae[ts.user_id]=ts.role}),c(Ae),G(en.data||[]);'
new = 'const Ae={};(mt.data||[]).forEach(ts=>{Ae[ts.user_id]=ts.role}),(en.data||[]).forEach(ts=>{const id=ts.lider_id;if(id&&Ae[id]!=="admin"&&Ae[id]!=="master")Ae[id]="lider"}),c(Ae),G(en.data||[]);'
if old not in js:
    raise SystemExit('volunteer role-map anchor not found')
js = js.replace(old, new, 1)

# Defesa adicional no rótulo principal: se o departamento aponta a pessoa
# como líder, jamais exibir "Voluntário" no cartão, mesmo se user_roles estiver
# temporariamente dessincronizado. Admin continua aparecendo como Admin e já
# recebe o chip secundário "Líder de ...".
old_badge = 'className:`shrink-0 text-[10px] px-2 py-0.5 ${Je(l[fe.id]||"voluntario")}`,children:Qt(l[fe.id]||"voluntario")'
new_badge = 'className:`shrink-0 text-[10px] px-2 py-0.5 ${Je(re.some(Ae=>Ae.lider_id===fe.id)&&(l[fe.id]||"voluntario")==="voluntario"?"lider":l[fe.id]||"voluntario")}`,children:Qt(re.some(Ae=>Ae.lider_id===fe.id)&&(l[fe.id]||"voluntario")==="voluntario"?"lider":l[fe.id]||"voluntario")'
if old_badge not in js:
    raise SystemExit('volunteer badge anchor not found')
js = js.replace(old_badge, new_badge, 1)

asset.write_text(js, encoding='utf-8')

(root / 'VERSION').write_text('1.4.43\n', encoding='utf-8')
(root / 'ATUALIZACAO-v1.4.43.md').write_text('''# Escala de Propósito v1.4.43\n\n- Corrige a tela **Voluntários** para reconhecer automaticamente como **Líder** quem estiver definido em `lider_id` de um departamento.\n- A liderança agora é identificada pela fonte correta: o próprio departamento.\n- Mantém separadas as ideias de **participar de um departamento** e **liderar um departamento**.\n- Preserva cargos administrativos: quem for Admin e também líder de departamento continua com permissão de Admin e com a indicação **Líder de ...**.\n- Não altera banco de dados, escalas, WhatsApp, repertório ou migração.\n''', encoding='utf-8')
