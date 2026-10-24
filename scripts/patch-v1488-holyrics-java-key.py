from pathlib import Path
import re

root=Path('pkg')
p=root/'Escala-de-Proposito-Holyrics.js'
s=p.read_text(encoding='utf-8')
if "V1.0.6" not in s:
    raise SystemExit("Expected Holyrics 1.0.6 source")
s=s.replace('V1.0.6','V1.0.7').replace('v1.0.6','v1.0.7')

old="""    function normalizeKey(v) {
        if (v == null) return '';
        if (typeof v === 'object') {
            if (v.access_key != null) v = v.access_key;
            else if (v.key != null) v = v.key;
            else if (v.value != null) v = v.value;
            else return '';
        }
        return String(v).replace(/[\\s\\u200B-\\u200D\\uFEFF]/g, '').toLowerCase();
    }"""
new="""    function normalizeKey(v) {
        if (v == null) return '';
        // O JavaScript do Holyrics pode entregar java.lang.String como 'object'.
        // A versão anterior descartava qualquer objeto sem a propriedade 'value';
        // isso descartava uma chave correta, inclusive após Copiar chave no portal.
        try {
            if (typeof v === 'object') {
                if (v.access_key != null) v = v.access_key;
                else if (v.key != null) v = v.key;
                else if (v.value != null) v = v.value;
                else if (v.token != null) v = v.token;
                else if (v.text != null) v = v.text;
                // Não descarte outros objetos: java.lang.String expõe toString().
            }
            var text = String(v).replace(/[\\s\\u200B-\\u200D\\uFEFF]/g, '').toLowerCase();
            // Cole/área de transferência podem incluir aspas externas.
            if ((text.charAt(0) === '"' && text.charAt(text.length - 1) === '"') ||
                (text.charAt(0) === "'" && text.charAt(text.length - 1) === "'")) {
                text = text.substring(1, text.length - 1);
            }
            return text;
        } catch (ignore) {
            return '';
        }
    }"""
if s.count(old)!=1:
    raise SystemExit('normalizeKey anchor mismatch '+str(s.count(old)))
s=s.replace(old,new,1)

# Melhor UX: aceitar chave copiada ou salva, com tamanho diagnóstico sem expor conteúdo.
old="""        if (!keyIsValid(parsed)) {
            throw new Error('A chave informada não possui 64 caracteres hexadecimais. Use COPIAR CHAVE no portal e execute o script novamente. Foram recebidos ' + parsed.length + ' caracteres (a chave não será exibida).');
        }"""
new="""        if (!keyIsValid(parsed)) {
            throw new Error('Chave não reconhecida: foram recebidos ' + parsed.length + ' caracteres; são necessários 64 caracteres hexadecimais. Não gere outra chave: no portal clique COPIAR CHAVE e execute novamente o script. A chave não será exibida.');
        }"""
if s.count(old)!=1:
    raise SystemExit('input error anchor mismatch')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

p=root/'holyrics-copy-script-v1487.js'
js=p.read_text(encoding='utf-8')
old_url="var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.87';"
new_url="var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.88';"
if js.count(old_url)!=1:
    raise SystemExit('copy URL anchor not found')
js=js.replace(old_url,new_url,1).replace('v1487','v1488').replace('v1.4.87','v1.4.88')
js=js.replace('Forma mais fácil de conectar no Holyrics:', 'Conexão corrigida para o Holyrics:')
js=js.replace('O módulo detectará automaticamente a chave copiada (com sua confirmação), sem precisar digitá-la novamente.',
    'A nova versão lê também as chaves que o Holyrics devolve como texto Java. Ele pedirá sua confirmação antes de salvar a chave copiada.')
(root/'holyrics-copy-script-v1488.js').write_text(js,encoding='utf-8')
p.unlink()

p=root/'holyrics-connect.html'
h=p.read_text(encoding='utf-8')
for old,new in [
 ('holyrics-copy-script-v1487.js?v=1.4.87','holyrics-copy-script-v1488.js?v=1.4.88'),
 ('/Escala-de-Proposito-Holyrics.js?v=1.4.87','/Escala-de-Proposito-Holyrics.js?v=1.4.88'),
]:
 if h.count(old)!=1: raise RuntimeError('HTML reference missing '+old)
 h=h.replace(old,new,1)
p.write_text(h,encoding='utf-8')

p=root/'sistema.html'
h=p.read_text(encoding='utf-8')
h,n=re.subn(r'(<script[^>]+src="/assets/index-[^"?]+\.js)(?:\?[^"]*)?(")',
  lambda m:m.group(1)+'?v=1.4.88'+m.group(2),h,count=1)
if n!=1:raise SystemExit('Main frontend asset anchor missing')
for name in ['holyrics-entry-v1481.js','app-notifications-v1465.js',
             'whatsapp-group-settings-v1473.js','master-whatsapp-groups-entry-v1475.js','cron-fix-v1478.js']:
 h=h.replace(name+'?v=1.4.87',name+'?v=1.4.88')
p.write_text(h,encoding='utf-8')

p=root/'sw.js'
sw=p.read_text(encoding='utf-8')
sw=re.sub(r'^/\* escala-version:[^*]+\*/\n?','',sw,count=1)
p.write_text('/* escala-version:1.4.88 */\n'+sw,encoding='utf-8')
(root/'VERSION').write_text('1.4.88\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.88.md').write_text("""# Escala de Propósito v1.4.88 — Holyrics com chave Java

- Corrige o tratamento da chave copiada no Holyrics. O programa pode representar um texto (java.lang.String) como objeto JavaScript.
- A função de leitura não descarta mais objetos que podem ser convertidos em texto com toString().
- Suporta chaves copiadas com espaços, quebras de linha, aspas externas e campos de entrada retornados como objetos.
- Melhora a mensagem de formato inválido informando apenas a quantidade de caracteres (nunca o conteúdo secreto).
- O site disponibiliza o script Holyrics v1.0.7, botão de cópia e download atualizados com ?v=1.4.88 para evitar cache.
- Mantém a chave já gerada; não exige renová-la.
- Mantém escalas, repertórios, notificações e WhatsApp sem alterações.
- Após atualizar o site, substitua uma vez o código anterior no editor de scripts do Holyrics, pois ele fica salvo no computador.
""",encoding='utf-8')
