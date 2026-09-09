from pathlib import Path
import sys

root = Path(sys.argv[1])
api = root / 'api' / 'master-data-cleanup.php'
s = api.read_text(encoding='utf-8')

# Os IDs vieram de fontes/tabelas com collations diferentes durante a migração
# (utf8mb4_unicode_ci x utf8mb4_general_ci). Em comparações coluna=coluna o
# MariaDB retorna erro 1267. Como são UUIDs/IDs, comparação binária é segura e
# independe da collation textual.
replacements = {
    'ON e.igreja_id=i.id': 'ON BINARY e.igreja_id=BINARY i.id',
    'ON e.id=ei.escala_id': 'ON BINARY e.id=BINARY ei.escala_id',
    'ON e.id=c.escala_id': 'ON BINARY e.id=BINARY c.escala_id',
    'ON e.id=q.escala_id': 'ON BINARY e.id=BINARY q.escala_id',
    'ON e.id=t.escala_id': 'ON BINARY e.id=BINARY t.escala_id',
    'ON e.id=w.escala_id': 'ON BINARY e.id=BINARY w.escala_id',
    'ON e.id=sr.escala_id': 'ON BINARY e.id=BINARY sr.escala_id',
    'ON e.id=s.escala_id': 'ON BINARY e.id=BINARY s.escala_id',
    'ON e.id=x.escala_id': 'ON BINARY e.id=BINARY x.escala_id',
    'ON sr.id=sc.request_id': 'ON BINARY sr.id=BINARY sc.request_id',
    'ON ei.id=w.escala_item_id': 'ON BINARY ei.id=BINARY w.escala_item_id',
    'ON ei.id=t.escala_item_id': 'ON BINARY ei.id=BINARY t.escala_item_id',
    'ON s.id=si.setlist_id': 'ON BINARY s.id=BINARY si.setlist_id',
}

changed = 0
for old, new in replacements.items():
    n = s.count(old)
    if n:
        s = s.replace(old, new)
        changed += n

if changed < 8:
    raise SystemExit(f'Poucas comparações foram corrigidas ({changed}); revisar estrutura da API.')

# Garantia contra regressão nos joins que causavam o erro 1267.
for bad in [
    'ON e.igreja_id=i.id', 'ON e.id=ei.escala_id', 'ON e.id=c.escala_id',
    'ON e.id=q.escala_id', 'ON e.id=w.escala_id', 'ON e.id=sr.escala_id',
    'ON e.id=s.escala_id', 'ON e.id=x.escala_id', 'ON sr.id=sc.request_id',
    'ON ei.id=w.escala_item_id', 'ON ei.id=t.escala_item_id', 'ON s.id=si.setlist_id'
]:
    if bad in s:
        raise SystemExit('Join ainda sujeito a collation: ' + bad)

api.write_text(s, encoding='utf-8')

# Marca a versão para também renovar o cache do PWA, embora a correção principal seja no PHP.
sw = root / 'sw.js'
sw.write_text(sw.read_text(encoding='utf-8') + '\n/* master-cleanup-collation-v1.4.20 */\n', encoding='utf-8')
