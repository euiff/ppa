from pathlib import Path
import re

root=Path('pkg')
p=root/'master-migration-entry.js'
s=p.read_text(encoding='utf-8')

# Remove somente o botão flutuante. A opção Migração Supabase do menu lateral continua.
pat=re.compile(r"\n  function addQuickButton\(\)\{.*?\n  \}\n  function inject\(\)\{ addSidebar\(\); addQuickButton\(\); \}",re.S)
rep="""
  function removeQuickButton(){
    const old=document.getElementById('master-supabase-migration-quick');
    if(old) old.remove();
  }
  function inject(){ addSidebar(); removeQuickButton(); }"""
s2,n=pat.subn(rep,s,count=1)
if n!=1:
    raise SystemExit('bloco do botão flutuante não encontrado')
if 'master-supabase-migration-quick' not in s2:
    raise SystemExit('proteção de remoção do botão não aplicada')
if "b.textContent='⇄ Migração Supabase'" in s2:
    raise SystemExit('código antigo do botão flutuante ainda presente')
p.write_text(s2,encoding='utf-8')

# Força o navegador/PWA a buscar a nova versão desse script.
html=root/'sistema.html'
h=html.read_text(encoding='utf-8')
h=re.sub(r'(/master-migration-entry\.js\?v=)[^"<]+',r'\g<1>1442',h)
html.write_text(h,encoding='utf-8')

sw=root/'sw.js'
if sw.exists():
    sw.write_text(sw.read_text(encoding='utf-8')+'\n/* remove-floating-supabase-migration-v1.4.42 */\n',encoding='utf-8')

(root/'VERSION').write_text('1.4.42\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.42.md').write_text('''# Escala de Propósito v1.4.42\n\n- Remove o botão flutuante **Migração Supabase** do painel MASTER.\n- Mantém a opção **Migração Supabase** normalmente no menu lateral do MASTER.\n- Remove automaticamente o botão antigo caso ele ainda esteja no DOM por cache da versão anterior.\n- Atualiza o cache do PWA para carregar a interface nova.\n- Não altera migração, banco de dados, WhatsApp, escalas, repertório ou permissões.\n''',encoding='utf-8')
