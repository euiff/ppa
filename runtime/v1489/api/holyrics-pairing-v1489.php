<?php
declare(strict_types=1);

/**
 * Escala de Propósito Holyrics Connect — pareamento por código temporário v1.4.89.
 * Código aleatório de 12 caracteres base32 (~60 bits), uso único e validade de 10 minutos.
 * A credencial definitiva (256 bits) só é transmitida no corpo de uma resposta HTTPS.
 */

function edp_pair_table(): void {
    db()->exec("CREATE TABLE IF NOT EXISTS holyrics_pairings (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      igreja_id VARCHAR(36) NOT NULL,
      code_hash CHAR(64) NOT NULL,
      expires_at DATETIME NOT NULL,
      used_at DATETIME NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE INDEX idx_holyrics_pair_hash (code_hash),
      INDEX idx_holyrics_pair_igreja (igreja_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
}

function edp_pair_normalize(string $code): string {
    return strtoupper(preg_replace('/[\s-]+/u','',$code)??'');
}

function edp_pair_issue(string $church): array {
    edp_hly_table();
    edp_pair_table();

    $alphabet='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    if(strlen($alphabet)!==32)throw new RuntimeException('Alfabeto de pareamento inválido.');
    $raw=random_bytes(12);
    $code='';
    for($i=0;$i<12;$i++)$code.=$alphabet[ord($raw[$i])&31];
    $hash=hash('sha256',$code);

    $db=db();
    $db->beginTransaction();
    try{
        $q=$db->prepare("UPDATE holyrics_pairings SET used_at=NOW()
            WHERE BINARY igreja_id=BINARY ? AND used_at IS NULL");
        $q->execute([$church]);

        $q=$db->prepare("INSERT INTO holyrics_pairings
           (igreja_id,code_hash,expires_at) VALUES (?, ?, DATE_ADD(NOW(),INTERVAL 10 MINUTE))");
        $q->execute([$church,$hash]);
        $db->commit();
    }catch(Throwable $e){
        if($db->inTransaction())$db->rollBack();
        throw $e;
    }
    // Não invalida o Holyrics já conectado enquanto o novo código não for usado.
    // Parear com sucesso troca a chave ativa desta igreja.
    return [
        'code'=>substr($code,0,4).'-'.substr($code,4,4).'-'.substr($code,8,4),
        'expires_in_seconds'=>600,
        'note'=>'O código vale 10 minutos e só pode ser usado uma vez. Ao conectar, a chave anterior será substituída.'
    ];
}

function edp_pair_redeem(string $entered): array {
    $code=edp_pair_normalize($entered);
    if(!preg_match('/^[A-HJ-NP-Z2-9]{12}$/D',$code)) {
        return ['error'=>'Código inválido. Digite os 12 caracteres exibidos no portal.'];
    }
    edp_hly_table();
    edp_pair_table();
    $db=db();
    $db->beginTransaction();
    try{
        $q=$db->prepare("SELECT id,igreja_id FROM holyrics_pairings
           WHERE code_hash=? AND used_at IS NULL AND expires_at>NOW() LIMIT 1 FOR UPDATE");
        $q->execute([hash('sha256',$code)]);
        $pair=$q->fetch(PDO::FETCH_ASSOC);
        if(!$pair){
            $db->rollBack();
            return ['error'=>'Código expirado ou já utilizado. Gere outro código no portal.'];
        }
        $church=(string)$pair['igreja_id'];
        $token=bin2hex(random_bytes(32));
        $q=$db->prepare("INSERT INTO holyrics_integracoes
             (igreja_id,token_hash,ativo,atualizado_em) VALUES (?,?,1,NOW())
             ON DUPLICATE KEY UPDATE token_hash=VALUES(token_hash),ativo=1,atualizado_em=NOW()");
        $q->execute([$church,hash('sha256',$token)]);

        $q=$db->prepare("UPDATE holyrics_pairings SET used_at=NOW() WHERE id=? AND used_at IS NULL");
        $q->execute([(string)$pair['id']]);
        if($q->rowCount()!==1)throw new RuntimeException('O código já foi consumido.');
        $db->commit();
        return ['access_key'=>$token,'connected'=>true,'message'=>'Computador conectado com sucesso.'];
    }catch(Throwable $e){
        if($db->inTransaction())$db->rollBack();
        throw $e;
    }
}
