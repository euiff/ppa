from pathlib import Path
import re

root = Path('pkg')
scale = root / 'api' / 'whatsapp_scale_message_v1421.php'

s = scale.read_text(encoding='utf-8')
pattern = re.compile(r"function v1421_same_day_repertoire\(array \$r\): array \{.*?\n\}\n\nfunction v1421_build_scale_message", re.S)
replacement = r'''function v1421_same_day_repertoire(array $r): array {
    try {
        $esc=(string)($r['escala_id']??'');
        $ig=(string)($r['igreja_id']??'');
        $data=(string)($r['data']??'');
        $culto=(string)($r['culto_id']??'');
        $rows=[];

        /*
         * A fonte oficial do repertorio e a MESMA escala aberta no painel.
         * O componente do app carrega setlists pelo escala_id; o WhatsApp precisa
         * fazer exatamente a mesma coisa para nunca exibir musicas de outra escala.
         */
        if($esc!=='') {
            $sql="SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom,m.link_youtube
                  FROM setlists s
                  JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id
                  JOIN musicas m ON BINARY m.id=BINARY si.musica_id
                  WHERE BINARY s.escala_id=BINARY ?
                  ORDER BY si.ordem ASC,m.titulo ASC";
            $q=db()->prepare($sql);$q->execute([$esc]);$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];
        }

        /*
         * Fallback somente quando a escala selecionada realmente nao tem repertorio.
         * Nesse caso tentamos outro setlist do mesmo culto/dia. Nunca substituimos
         * um repertorio existente da escala por musicas de outra escala.
         */
        if(!$rows && $ig!=='' && $data!=='' && $culto!=='') {
            $sql="SELECT s.id setlist_id,COUNT(si.musica_id) qtd,MAX(s.created_at) criado
                  FROM setlists s
                  JOIN escalas e2 ON BINARY e2.id=BINARY s.escala_id
                  LEFT JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id
                  WHERE BINARY e2.igreja_id=BINARY ? AND e2.data=? AND BINARY e2.culto_id=BINARY ?
                  GROUP BY s.id
                  HAVING qtd>0
                  ORDER BY qtd DESC,criado DESC,s.id DESC
                  LIMIT 1";
            $q=db()->prepare($sql);$q->execute([$ig,$data,$culto]);
            $setlist=(string)($q->fetchColumn()?:'');
            if($setlist!=='') {
                $sql="SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom,m.link_youtube
                      FROM setlist_itens si
                      JOIN musicas m ON BINARY m.id=BINARY si.musica_id
                      WHERE BINARY si.setlist_id=BINARY ?
                      ORDER BY si.ordem ASC,m.titulo ASC";
                $q=db()->prepare($sql);$q->execute([$setlist]);$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];
            }
        }

        $out=[];$seen=[];
        foreach($rows as $x){
            $id=(string)($x['musica_id']??'');
            $title=trim((string)($x['titulo']??''));
            $key=$id!==''?$id:(function_exists('mb_strtolower')?mb_strtolower($title,'UTF-8'):strtolower($title));
            if($key===''||isset($seen[$key]))continue;
            $seen[$key]=true;$out[]=$x;
            if(count($out)>=30)break;
        }
        return $out;
    } catch(Throwable $e) {
        return [];
    }
}

function v1421_build_scale_message'''

s2, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Funcao v1421_same_day_repertoire nao encontrada')
scale.write_text(s2, encoding='utf-8')

(root / 'VERSION').write_text('1.4.38\n', encoding='utf-8')
(root / 'ATUALIZACAO-v1.4.38.md').write_text('''# Escala de Propósito v1.4.38\n\n- Corrige o repertório do WhatsApp para usar primeiro o repertório oficial da própria escala selecionada.\n- O WhatsApp agora consulta o mesmo `escala_id` que o painel usa em “Repertório do culto”.\n- Se a escala possui repertório, músicas de outras escalas do mesmo dia nunca substituem essa lista.\n- Somente quando a escala não possui repertório existe fallback para outro setlist do mesmo culto/dia.\n- A correção vale para MENU > Repertório, notificação inicial e PDF completo.\n- Mantém nome, artista, tom, links do YouTube e a ordem cadastrada.\n- Não altera confirmação/recusa, webhook ou transporte do WhatsApp.\n''', encoding='utf-8')
