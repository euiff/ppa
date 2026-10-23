# Escala de Propósito Connect — Holyrics v1.0

O módulo adiciona uma integração opcional. Não modifica escalas, publicações nem notificações existentes.

## Para a administração da igreja
1. No Escala de Propósito, após instalar a atualização do sistema, acesse **Integração Holyrics** (ou `https://escaladeproposito.com.br/holyrics-connect.html`).
2. Escolha a igreja e clique **Gerar / renovar chave**. Guarde a chave mostrada (uma única vez).
3. A chave permite apenas leitura de repertório de escalas publicadas da própria igreja. É possível revogá-la a qualquer momento. Não envie a chave em grupos de WhatsApp.

## Para o operador no Holyrics
1. Atualize para o Holyrics 2.23.0+.
2. Libere `https://escaladeproposito.com.br` em Arquivo → Configurações → Avançado → JavaScript → Configurações → Requisições permitidas.
3. Vá em Ferramentas → Diversos → Script. Crie o script **Escala de Propósito**, cole o conteúdo do arquivo `Escala-de-Proposito-Holyrics.js` e salve.
4. Execute o script. Na primeira vez, informe a chave individual da igreja. Nas próximas, escolha apenas o culto e confirme a importação.
5. Use favoritos/atalho do próprio Holyrics para deixar esse script acessível.

Observações: o script adiciona músicas já existentes na biblioteca do Holyrics. Se houver várias versões com o mesmo nome, pede ao operador que escolha. Não apaga a playlist. Caso uma música não esteja cadastrada no Holyrics, será listada como não encontrada. Letras e áudio não são enviados pelo Escala de Propósito.

Este método usa a API de scripts oficial, mas **não** insere automaticamente a opção no menu nativo “Importar Lista Externa”, que depende de integração específica com o fornecedor do Holyrics.

## Segurança
- Conexão HTTPS e chave por igreja; só o hash SHA-256 da chave é armazenado no servidor.
- A chave é transmitida no cabeçalho Authorization, não na URL.
- Apenas Master / Admin / Pastor da igreja podem emitir ou revogar a chave.
- O Holyrics guarda a chave localmente; se outro usuário obtiver acesso à máquina, revogue a chave e gere uma nova.
