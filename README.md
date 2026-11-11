# Distributed BBS

Sistema de troca de mensagens instantâneas inspirado no BBS e no IRC. Bots fazem login, criam canais públicos, se inscrevem neles e publicam mensagens. Todas as interações ficam gravadas em disco e os servidores podem entrar e sair sem parar o serviço.

Projeto individual da disciplina de Sistemas Distribuídos (Ciência da Computação, FEI), de Bruno Budano Mello.

## Arquitetura

São dois caminhos de mensagem. Pedidos dos bots seguem por `REQ`/`REP` através do broker. Publicações nos canais seguem por `PUB`/`SUB` através do proxy.

```
Pedidos (REQ/REP)

bot-1 (REQ) --+                             +-- (REP) server-1 --> volume server-1-data
              +-- ROUTER [ broker ] DEALER -+
bot-2 (REQ) --+    5555             5556    +-- (REP) server-2 --> volume server-2-data

Publicações (PUB/SUB)

server-1 (PUB) --+                         +-- (SUB) bot-1
                 +-- XSUB [ proxy ] XPUB --+
server-2 (PUB) --+   5557          5558    +-- (SUB) bot-2
```

| Serviço | Responsabilidade | Linguagem | Dados |
|---|---|---|---|
| `broker` | Repassa os pedidos dos bots para os servidores, em rodízio | Python | Nenhum |
| `proxy` | Repassa as publicações dos servidores para os bots inscritos no canal | Python | Nenhum |
| `server-1`, `server-2` | Validam os pedidos, aplicam as regras, gravam em disco e publicam nos canais | Python | Um volume por servidor |
| `bot-1`, `bot-2` | Usuários automáticos: fazem login, criam canais, se inscrevem e publicam | TypeScript | Nenhum |

Toda a comunicação usa a rede criada pelo Docker Compose. Nenhuma porta é publicada na máquina.

## Subindo

Precisa só de **Docker** (com o Docker Compose v2). Na raiz do repositório:

```bash
docker compose up
```

Nenhuma interação é necessária. Clientes e servidores mostram no terminal cada mensagem enviada (`SENT`) ou recebida (`RECEIVED`), com o conteúdo completo. Uma publicação aparece assim, do pedido do bot até a entrega aos inscritos:

```
bot-2-1     | SENT       | operation='publish' | sender='bot-2' | timestamp=2026-11-10T21:47:28.858Z | payload={ channel: 'movies', message: 'Bom dia, pessoal!' }
server-1-1  | RECEIVED | operation='publish' | sender='bot-2' | timestamp=2026-11-10T21:47:28.858Z | payload={'channel': 'movies', 'message': 'Bom dia, pessoal!'}
server-1-1  | SENT     | topic='movies' | operation='publication' | sender='server-1' | timestamp=2026-11-10T21:47:28.861Z | payload={'channel': 'movies', 'author': 'bot-2', 'message': 'Bom dia, pessoal!'}
server-1-1  | SENT     | operation='publish' | sender='server-1' | timestamp=2026-11-10T21:47:28.870Z | status='success' | payload={}
bot-2-1     | RECEIVED   | topic='movies' | operation='publication' | sender='server-1' | timestamp=2026-11-10T21:47:28.861Z | payload={ channel: 'movies', author: 'bot-2', message: 'Bom dia, pessoal!' } | received_at=2026-11-10T21:47:28.871Z
bot-2-1     | RECEIVED   | operation='publish' | sender='server-1' | timestamp=2026-11-10T21:47:28.870Z | status='success' | payload={}
```

Na publicação recebida, `timestamp` é o envio pelo servidor e `received_at` é a chegada ao bot.

Para desligar mantendo os dados, `docker compose down`. Para desligar **e apagar os dados dos servidores**, `docker compose down -v`.

## Protocolo

Pedidos e respostas são mapas MessagePack enviados em um único frame. Publicações têm dois frames: o nome do canal, como tópico, e o mapa MessagePack.

| Campo | Tipo | Pedido | Resposta | Publicação |
|---|---|---|---|---|
| `operation` | texto | Operação pedida | Operação atendida, ou `unidentified` | Sempre `publication` |
| `sender` | texto | Nome do usuário | Nome do servidor que respondeu | Nome do servidor que publicou |
| `timestamp` | inteiro | Envio do pedido, em milissegundos desde 1970 (UTC) | Envio da resposta | Envio da publicação |
| `payload` | mapa | Dados da operação | Dados da resposta ou do erro | `{channel, author, message}` |
| `status` | texto | Não existe | `success` ou `error` | Não existe |

| Operação | `payload` do pedido | `payload` da resposta com sucesso |
|---|---|---|
| `login` | `{}` | `{}` |
| `create_channel` | `{channel: "nome"}` | `{}` |
| `list_channels` | `{}` | `{channels: ["nome", ...]}` |
| `publish` | `{channel: "nome", message: "texto"}` | `{}` |

Uma resposta com erro traz `{error_code, error_description}` no `payload`.

| `error_code` | Quando acontece |
|---|---|
| `MALFORMED_MESSAGE` | Os bytes não são MessagePack, ou falta campo, ou um campo tem tipo ou faixa inválidos |
| `UNKNOWN_OPERATION` | A operação não existe |
| `INVALID_USERNAME` | O nome do usuário está fora do formato permitido |
| `INVALID_CHANNEL_NAME` | O nome do canal está fora do formato permitido |
| `CHANNEL_ALREADY_EXISTS` | Já existe canal com esse nome no servidor que atendeu |
| `CHANNEL_NOT_FOUND` | Pedido de publicação num canal que não existe no servidor que atendeu |
| `INVALID_MESSAGE` | A mensagem não é texto ou está fora do tamanho permitido |

## Regras

| Regra | Lógica | Por quê |
|---|---|---|
| Nome de usuário | 1 a 32 letras, dígitos, `_` ou `-` | Tamanho limitado e seguro para exibir no log |
| Nome de canal | 1 a 32 letras minúsculas, dígitos ou `-` | Só minúsculas impede `Geral` e `geral` como canais distintos |
| Mensagem publicada | Texto de 1 a 500 caracteres, qualquer caractere | Limite de tamanho em toda entrada; acentos e quebras de linha chegam intactos |
| Login repetido do mesmo usuário | Aceito, e cada login é gravado | O enunciado pede o histórico de todos os logins e não há sessão |
| Canal duplicado | Recusado com `CHANNEL_ALREADY_EXISTS` | O canal original continua o mesmo |
| Publicação em canal inexistente | Recusada com `CHANNEL_NOT_FOUND`, sem gravar nem publicar | Só se publica em canal criado no servidor |
| Ordem da publicação | Grava em disco, publica no tópico, responde ao bot | Se o servidor cair no meio, a publicação fica guardada em vez de se perder |
| Erro ou timeout no login | O bot repete o login a cada 2 s até ser aceito | Exigência do enunciado |
| Timeout de resposta | 5 s; o bot descarta o socket `REQ` e abre outro | Um `REQ` sem resposta fica preso e não aceita novo envio |

### Comportamento padronizado dos bots

A cada rodada, o bot:

1. Lista os canais.
2. Se a lista tiver menos de 5 canais, cria um canal sorteado entre os do catálogo fixo (`general`, `news`, `sports`, `music`, `movies`) que não estão na lista.
3. Se estiver inscrito em menos de 3 canais, se inscreve em um canal da lista, sorteado entre os que ainda não assina.
4. Sorteia um canal da lista e envia 10 mensagens sorteadas de um catálogo, uma por segundo.

O enunciado descreve os passos 2 e 3 "ao conectar". Eles são repetidos em toda rodada porque, feitos uma vez só, cada bot terminaria com 1 inscrição e o sistema com 2 canais. Repetindo, o bot chega aos 5 canais e às 3 inscrições, e a primeira rodada continua igual à descrição.

O catálogo de canais tem exatamente 5 nomes, para os bots nunca criarem nomes sem fim quando cada servidor enxerga uma lista diferente. O nome é sorteado entre os que faltam porque, pegando sempre o primeiro, os bots travavam: a lista vinha de um servidor, o pedido de criação caía no outro, e o canal escolhido era justamente o que esse outro já tinha.

## Escolhas e seus custos

| Assunto | Escolha | Alternativa descartada | Custo da escolha |
|---|---|---|---|
| Linguagens | Python no broker, no proxy e no servidor; TypeScript nos bots | Java nos bots: mais verboso e com etapa de build mais pesada | A biblioteca `zeromq` para Node depende de um binário nativo |
| Serialização | MessagePack | Protobuf: exige arquivo `.proto` e geração de código nas duas linguagens | Sem schema compartilhado; cada lado valida o formato no próprio código |
| Persistência | SQLite, um arquivo por servidor em volume próprio | Arquivo JSON Lines: legível, mas exigiria implementar unicidade e escrita atômica | O arquivo é binário; para inspecionar é preciso um cliente SQLite |
| Pedidos | `REQ`/`ROUTER`/`DEALER`/`REP` | `REQ`/`REP` direto: o bot precisaria conhecer cada servidor | O broker é ponto único de falha |
| Publicações | `PUB`/`XSUB`/`XPUB`/`SUB`, com o proxy separado do broker | `PUB` no servidor e `SUB` ligado direto nele: o bot teria de conhecer cada servidor | Mais um ponto único de falha |
| Isolamento dos caminhos | Um contexto ZeroMQ para os pedidos e outro para as publicações, no servidor e no bot | Um contexto só por processo | Com um contexto só, a queda do proxy travava também os pedidos: cada tentativa de reconexão consulta o DNS por 3,5 s no mesmo thread de I/O. Separados, a queda do proxy não atrasa nenhuma resposta |
| Tópico | Nome do canal no primeiro frame; o bot confere se o tópico é exatamente um canal assinado | Confiar só no filtro do ZeroMQ, que compara por prefixo e entregaria `news-br` a quem assina `news` | Uma verificação a mais no bot |
| Publicações em disco | Tabela `publication` com canal, autor, mensagem, horário do pedido, horário da publicação e servidor que publicou | Gravar só o texto | Mais colunas, mas qualquer informação pode ser recuperada depois |
| Timestamp do login e do pedido | O da mensagem do bot | Relógio do servidor | Confia no relógio do cliente, que aqui é o mesmo da máquina hospedeira |

## Limitações conhecidas

| Limitação | Efeito | Motivo |
|---|---|---|
| Servidores não sincronizam | Um canal criado no `server-1` não aparece numa listagem atendida pelo `server-2` até ser criado lá; publicar nele pelo `server-2` recebe `CHANNEL_NOT_FOUND` | Cada servidor guarda só os próprios dados, como o enunciado pede; a sincronização ainda não faz parte do projeto |
| Um servidor pode ficar com menos de 5 canais | Quando um servidor completa os 5 canais, o bot que lista nele não cria mais nada, e o pedido de criação de quem lista no outro tende a cair de novo no servidor completo, porque o broker alterna pedidos seguidos entre servidores. Numa execução de 90 s, o `server-1` chegou a 5 canais, o `server-2` ficou com 1, e 88 de 183 pedidos de publicação receberam `CHANNEL_NOT_FOUND` | Mesmo motivo; nenhuma escolha do lado do bot resolve, porque o bot não escolhe o servidor que atende |
| Histórico dividido | Logins e publicações ficam só no servidor que atendeu | Mesmo motivo |
| Publicação não espera inscrito | Quem se inscreve depois não recebe as publicações anteriores, que continuam gravadas em disco | `PUB`/`SUB` entrega só para quem já está inscrito no momento do envio |

## Testes

Há duas suítes.

| Suíte | Como roda | O que testa |
|---|---|---|
| Black-box do sistema (`tests/`, pytest) | Container na rede do Compose, falando com o broker e o proxy como um cliente qualquer | Login, canais, publicação, entrega aos inscritos e o que fica gravado em disco |
| Decisões dos bots (`bot/tests/`, `node:test`) | Na construção da imagem do bot; a imagem não é gerada se um teste falhar | Quando criar canal, quando se inscrever e onde publicar |

A suíte black-box só lê o arquivo do `server-1`, em modo somente leitura, para conferir logins e publicações gravados, porque o protocolo não tem operação que devolva esse histórico.

```bash
docker compose -p distributed-bbs-test --profile test run --rm --build tests
```

```bash
docker compose -p distributed-bbs-test --profile test down -v
```

Essa execução usa um projeto separado, com só um servidor e sem bots, para o resultado não depender do rodízio do broker nem dos dados da execução principal.

Para as decisões dos bots fora do Docker, dentro de `bot/`:

```bash
npm ci
```

```bash
npm test
```

| Arquivo | O que testa |
|---|---|
| `tests/test_login.py` | Login aceito, formato do nome e gravação em disco |
| `tests/test_channels.py` | Criação, duplicidade, formato do nome e listagem |
| `tests/test_publications.py` | Publicação, entrega no tópico certo, timestamp, gravação em disco e recusas que não gravam nem publicam |
| `tests/test_protocol.py` | Formato binário, campos obrigatórios, limites do timestamp e operação desconhecida |
| `bot/tests/botDecisions.test.ts` | Números padronizados do enunciado e as decisões de criar, assinar e publicar |

## Se algo falhar

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Bot mostra `TIMEOUT` em sequência | Nenhum servidor conectado ao broker | Conferir com `docker compose ps` e subir um servidor; o bot volta sozinho |
| Bot publica mas nenhum bot recebe | O proxy caiu ou ninguém assina aquele canal | Conferir o `proxy` com `docker compose ps`; as linhas `SUBSCRIBED` mostram o que cada bot assina |
| `CHANNEL_NOT_FOUND` em parte das publicações | O canal não existe no servidor que atendeu | Esperado enquanto os servidores não sincronizam; ver "Limitações conhecidas" |
| Bots listam os canais antigos depois de um novo começo | Os volumes foram preservados | `docker compose down -v` |
| Mudança em `server/database/database.sql` não aparece | A tabela já existe no volume | `docker compose down -v` |

## Organização

| Pasta | Conteúdo |
|---|---|
| `broker/` | Proxy `ROUTER`/`DEALER` dos pedidos |
| `proxy/` | Proxy `XSUB`/`XPUB` das publicações |
| `server/src/resources/` | Laço de atendimento e rotas das operações |
| `server/src/schemas/` | Validação do formato do pedido |
| `server/src/controllers/` | Regras e decisão de gravar e publicar |
| `server/src/repositories/` | Único lugar com SQL |
| `server/src/connectors/` | Único lugar que conhece ZeroMQ e MessagePack |
| `server/database/` | Schema do banco |
| `bot/src/controllers/` | Comportamento do bot e suas decisões |
| `bot/src/connectors/` | Único lugar que conhece ZeroMQ e MessagePack |
| `bot/tests/` | Testes das decisões do bot |
| `tests/` | Suíte black-box |

## Glossário

| Termo | Nome no código | Não confundir com |
|---|---|---|
| Bot | `bot` | Servidor; o bot é o usuário do sistema |
| Usuário | `username`, `sender` no pedido | `sender` na resposta e na publicação, que é o nome do servidor |
| Canal | `channel` | Conexão de rede |
| Tópico | `topic` | Canal: o tópico é o nome do canal usado como filtro do `PUB`/`SUB` |
| Login | `login` | Sessão; não existe sessão no sistema |
| Pedido | `RequestMessage` | Resposta |
| Resposta | `ResponseMessage` | Pedido |
| Publicação | `Publication`, `PublicationMessage` | Pedido de publicação (`publish`), que é o que o bot envia ao servidor |
| Autor | `author`, `author_username` | `sender` da publicação, que é o servidor |
| Inscrição | `subscribe` | Login; a inscrição é só do lado do bot e não passa pelo servidor |
| Recusa | `BbsError` | Timeout, que é falta de resposta |

## Entregas

Cada parte é desenvolvida em uma branch própria.

| Parte | Branch | Conteúdo |
|---|---|---|
| 1 | `parte-1` | Login, criação e listagem de canais, persistência |
| 2 | `parte-2` | Publicação em canais com `PUB`/`SUB`, proxy, inscrições dos bots e persistência das publicações |
