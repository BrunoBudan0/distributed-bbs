# Distributed BBS

Sistema de troca de mensagens instantâneas inspirado no BBS e no IRC. Bots fazem login, criam canais públicos, se inscrevem neles e publicam mensagens. Todas as interações ficam gravadas em disco, todos os processos marcam as mensagens com um relógio lógico, os servidores sincronizam o relógio físico com um serviço de referência e podem entrar e sair sem parar o serviço.

Projeto individual da disciplina de Sistemas Distribuídos (Ciência da Computação, FEI), de Bruno Budano Mello.

## Arquitetura

São três caminhos de mensagem. Pedidos dos bots seguem por `REQ`/`REP` através do broker. Publicações nos canais seguem por `PUB`/`SUB` através do proxy. Os servidores conversam com o serviço de referência por `REQ`/`REP` para receber o rank, avisar que estão vivos e acertar o relógio.

```
Pedidos (REQ/REP)

bot-1 (REQ) --+                             +-- (REP) server-1 --> volume server-1-data
              +-- ROUTER [ broker ] DEALER -+
bot-2 (REQ) --+    5555             5556    +-- (REP) server-2 --> volume server-2-data

Publicações (PUB/SUB)

server-1 (PUB) --+                         +-- (SUB) bot-1
                 +-- XSUB [ proxy ] XPUB --+
server-2 (PUB) --+   5557          5558    +-- (SUB) bot-2

Rank, heartbeat e hora (REQ/REP)

server-1 (REQ) --+
                 +-- REP [ reference ] 5559
server-2 (REQ) --+
```

| Serviço | Responsabilidade | Linguagem | Dados |
|---|---|---|---|
| `broker` | Repassa os pedidos dos bots para os servidores, em rodízio | Python | Nenhum |
| `proxy` | Repassa as publicações dos servidores para os bots inscritos no canal | Python | Nenhum |
| `reference` | Dá o rank de cada servidor, mantém a lista dos disponíveis por heartbeat e informa a hora correta | Python | Em memória |
| `server-1`, `server-2` | Validam os pedidos, aplicam as regras, gravam em disco, publicam nos canais e sincronizam o relógio | Python | Um volume por servidor |
| `bot-1`, `bot-2` | Usuários automáticos: fazem login, criam canais, se inscrevem e publicam | TypeScript | Nenhum |

Toda a comunicação usa a rede criada pelo Docker Compose. Nenhuma porta é publicada na máquina.

## Subindo

Precisa só de **Docker** (com o Docker Compose v2). Na raiz do repositório:

```bash
docker compose up
```

Nenhuma interação é necessária. Clientes e servidores mostram no terminal cada mensagem enviada (`SENT`) ou recebida (`RECEIVED`), com o conteúdo completo, incluindo o `timestamp` e o `logical_clock`. Uma publicação aparece assim, do pedido do bot até a entrega aos inscritos:

```
bot-2-1      | SENT       | operation='publish' | sender='bot-2' | timestamp=2026-11-11T14:42:07.925Z | logical_clock=28 | payload={ channel: 'music', message: 'Boa noite a todos.' }
server-2-1   | RECEIVED | operation='publish' | sender='bot-2' | timestamp=2026-11-11T14:42:07.925Z | logical_clock=28 | payload={'channel': 'music', 'message': 'Boa noite a todos.'}
server-2-1   | SENT     | topic='music' | operation='publication' | sender='server-2' | timestamp=2026-11-11T14:42:07.927Z | logical_clock=32 | payload={'channel': 'music', 'author': 'bot-2', 'message': 'Boa noite a todos.'}
server-2-1   | SENT     | operation='publish' | sender='server-2' | timestamp=2026-11-11T14:42:07.931Z | logical_clock=33 | status='success' | payload={}
bot-2-1      | RECEIVED   | topic='music' | operation='publication' | sender='server-2' | timestamp=2026-11-11T14:42:07.927Z | logical_clock=32 | payload={ channel: 'music', author: 'bot-2', message: 'Boa noite a todos.' } | received_at=2026-11-11T14:42:07.932Z
bot-2-1      | RECEIVED   | operation='publish' | sender='server-2' | timestamp=2026-11-11T14:42:07.931Z | logical_clock=33 | status='success' | payload={}
```

O relógio lógico salta de 28 para 32 porque o servidor já estava em 31: logo antes, a referência respondeu ao heartbeat e à lista de servidores com o relógio dela, e o servidor ficou com o maior valor.

Na publicação recebida, `timestamp` é o envio pelo servidor e `received_at` é a chegada ao bot.

O `server-2` começa com o relógio físico adiantado em 7 s de propósito (`SIMULATED_CLOCK_SKEW_MS` no compose), porque no Docker todos os containers usam o relógio da mesma máquina e não haveria nada para sincronizar. A correção aparece no primeiro heartbeat:

```
bot-2-1      | SENT       | operation='publish' | sender='bot-2' | timestamp=2026-11-11T14:42:06.912Z | logical_clock=25 | payload={ channel: 'music', message: 'Essa música é ótima.' }
bot-2-1      | RECEIVED   | operation='publish' | sender='server-2' | timestamp=2026-11-11T14:42:13.921Z | logical_clock=27 | status='success' | payload={}
server-2-1   | CLOCK    | physical clock synchronized with the reference | offset_before_ms=7000 | offset_after_ms=0 | round_trip_ms=2
bot-2-1      | SENT       | operation='publish' | sender='bot-2' | timestamp=2026-11-11T14:42:07.925Z | logical_clock=28 | payload={ channel: 'music', message: 'Boa noite a todos.' }
bot-2-1      | RECEIVED   | operation='publish' | sender='server-2' | timestamp=2026-11-11T14:42:07.931Z | logical_clock=33 | status='success' | payload={}
```

Antes da sincronização, a resposta do `server-2` aparece 7 s depois do pedido; depois, 6 ms.

Para desligar mantendo os dados, `docker compose down`. Para desligar **e apagar os dados dos servidores**, `docker compose down -v`.

## Protocolo

Pedidos e respostas são mapas MessagePack enviados em um único frame. Publicações têm dois frames: o nome do canal, como tópico, e o mapa MessagePack.

| Campo | Tipo | Pedido | Resposta | Publicação |
|---|---|---|---|---|
| `operation` | texto | Operação pedida | Operação atendida, ou `unidentified` | Sempre `publication` |
| `sender` | texto | Nome de quem pede | Nome de quem respondeu | Nome do servidor que publicou |
| `timestamp` | inteiro | Envio do pedido, em milissegundos desde 1970 (UTC) | Envio da resposta | Envio da publicação |
| `logical_clock` | inteiro | Relógio lógico de quem pede, de 0 a 2^52 | Relógio lógico de quem respondeu | Relógio lógico do servidor que publicou |
| `payload` | mapa | Dados da operação | Dados da resposta ou do erro | `{channel, author, message}` |
| `status` | texto | Não existe | `success` ou `error` | Não existe |

Operações atendidas pelos servidores, pedidas pelos bots:

| Operação | `payload` do pedido | `payload` da resposta com sucesso |
|---|---|---|
| `login` | `{}` | `{}` |
| `create_channel` | `{channel: "nome"}` | `{}` |
| `list_channels` | `{}` | `{channels: ["nome", ...]}` |
| `publish` | `{channel: "nome", message: "texto"}` | `{}` |

Operações atendidas pela referência, pedidas pelos servidores (o `sender` é o nome do servidor):

| Operação | `payload` do pedido | `payload` da resposta com sucesso |
|---|---|---|
| `rank` | `{}` | `{rank: 1}` |
| `list_servers` | `{}` | `{servers: [{name: "server-1", rank: 1}, ...]}`, em ordem de rank |
| `heartbeat` | `{}` | `{time: 1794407196413}`, a hora correta em milissegundos |

Uma resposta com erro traz `{error_code, error_description}` no `payload`.

| `error_code` | Quem devolve | Quando acontece |
|---|---|---|
| `MALFORMED_MESSAGE` | Servidor e referência | Os bytes não são MessagePack, ou falta campo, ou um campo tem tipo ou faixa inválidos |
| `UNKNOWN_OPERATION` | Servidor e referência | A operação não existe |
| `INVALID_USERNAME` | Servidor | O nome do usuário está fora do formato permitido |
| `INVALID_CHANNEL_NAME` | Servidor | O nome do canal está fora do formato permitido |
| `CHANNEL_ALREADY_EXISTS` | Servidor | Já existe canal com esse nome no servidor que atendeu |
| `CHANNEL_NOT_FOUND` | Servidor | Pedido de publicação num canal que não existe no servidor que atendeu |
| `INVALID_MESSAGE` | Servidor | A mensagem não é texto ou está fora do tamanho permitido |
| `INVALID_SERVER_NAME` | Referência | O nome do servidor está fora do formato permitido |
| `UNKNOWN_SERVER` | Referência | Heartbeat de um servidor que nunca pediu rank |

## Regras

| Regra | Lógica | Por quê |
|---|---|---|
| Nome de usuário e de servidor | 1 a 32 letras, dígitos, `_` ou `-` | Tamanho limitado e seguro para exibir no log |
| Nome de canal | 1 a 32 letras minúsculas, dígitos ou `-` | Só minúsculas impede `Geral` e `geral` como canais distintos |
| Mensagem publicada | Texto de 1 a 500 caracteres, qualquer caractere | Limite de tamanho em toda entrada; acentos e quebras de linha chegam intactos |
| Login repetido do mesmo usuário | Aceito, e cada login é gravado | O enunciado pede o histórico de todos os logins e não há sessão |
| Canal duplicado | Recusado com `CHANNEL_ALREADY_EXISTS` | O canal original continua o mesmo |
| Publicação em canal inexistente | Recusada com `CHANNEL_NOT_FOUND`, sem gravar nem publicar | Só se publica em canal criado no servidor |
| Ordem da publicação | Grava em disco, publica no tópico, responde ao bot | Se o servidor cair no meio, a publicação fica guardada em vez de se perder |
| Erro ou timeout no login | O bot repete o login a cada 2 s até ser aceito | Exigência do enunciado |
| Timeout de resposta | 5 s no bot e 2 s no servidor falando com a referência; quem pediu descarta o socket `REQ` e abre outro | Um `REQ` sem resposta fica preso e não aceita novo envio |

### Relógios

| Regra | Lógica | Por quê |
|---|---|---|
| Relógio lógico | Bots, servidores e referência começam em 0, somam 1 antes de cada envio e mandam o valor em `logical_clock`. Ao receber, ficam com o maior entre o próprio e o recebido | Relógio de Lamport, como apresentado em aula |
| Mensagem recusada | O `logical_clock` recebido é considerado mesmo quando o pedido é recusado, desde que o campo seja válido | Toda mensagem recebida conta, não só as aceitas |
| Limite do relógio lógico | Aceito de 0 a 2^52; ao chegar no limite, o relógio para ali em vez de passar | Sem esse teto, um único cliente mandando o valor máximo empurraria todos os processos para além dele, e daí em diante todos os pedidos seriam recusados. 2^52 cabe com folga no maior inteiro exato do JavaScript |
| Rank | A referência dá ranks 1, 2, 3... na ordem do primeiro pedido; o mesmo nome recebe sempre o mesmo rank | O enunciado pede a lista sem nomes repetidos |
| Heartbeat | O servidor envia um heartbeat depois de cada 10 mensagens de clientes e, em seguida, pede a lista de servidores | Frequência pedida pelo enunciado; o heartbeat sai depois da resposta ao bot, para não atrasá-lo |
| Remoção | A referência tira da lista o servidor sem rank nem heartbeat há mais de 30 s; ele volta com o mesmo rank no próximo heartbeat | Disponibilidade separada do cadastro, para o rank não mudar a cada queda |
| Referência reiniciada | Ela esquece os servidores; o heartbeat recebe `UNKNOWN_SERVER` e o servidor pede rank de novo | O cadastro fica em memória |
| Relógio físico | No heartbeat, o servidor mede a ida e volta e ajusta o relógio para a hora da referência mais metade desse tempo | Algoritmo de Cristian: a resposta leva cerca de metade da ida e volta para chegar |
| Onde o ajuste vale | O servidor guarda um deslocamento (`offset_ms`) e o soma a todo `timestamp` que envia e grava | O container não tem permissão para mudar o relógio do sistema |

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
| Linguagens | Python no broker, no proxy, na referência e no servidor; TypeScript nos bots | Java nos bots: mais verboso e com etapa de build mais pesada | A biblioteca `zeromq` para Node depende de um binário nativo |
| Serialização | MessagePack | Protobuf: exige arquivo `.proto` e geração de código nas duas linguagens | Sem schema compartilhado; cada lado valida o formato no próprio código |
| Persistência | SQLite, um arquivo por servidor em volume próprio | Arquivo JSON Lines: legível, mas exigiria implementar unicidade e escrita atômica | O arquivo é binário; para inspecionar é preciso um cliente SQLite |
| Pedidos | `REQ`/`ROUTER`/`DEALER`/`REP` | `REQ`/`REP` direto: o bot precisaria conhecer cada servidor | O broker é ponto único de falha |
| Publicações | `PUB`/`XSUB`/`XPUB`/`SUB`, com o proxy separado do broker | `PUB` no servidor e `SUB` ligado direto nele: o bot teria de conhecer cada servidor | Mais um ponto único de falha |
| Isolamento dos caminhos | Um contexto ZeroMQ por caminho: pedidos, publicações e referência, no servidor e no bot | Um contexto só por processo | Com um contexto só, a queda do proxy travava também os pedidos: cada tentativa de reconexão consulta o DNS por 3,5 s no mesmo thread de I/O. Separados, a queda do proxy não atrasa nenhuma resposta |
| Tópico | Nome do canal no primeiro frame; o bot confere se o tópico é exatamente um canal assinado | Confiar só no filtro do ZeroMQ, que compara por prefixo e entregaria `news-br` a quem assina `news` | Uma verificação a mais no bot |
| Publicações em disco | Tabela `publication` com canal, autor, mensagem, horário do pedido, horário da publicação e servidor que publicou | Gravar só o texto | Mais colunas, mas qualquer informação pode ser recuperada depois |
| Timestamp do login e do pedido | O da mensagem do bot | Relógio do servidor | Confia no relógio do cliente |
| Sincronização do relógio físico | Cristian, com a referência como fonte da hora | Berkeley, com média entre servidores: o enunciado define a referência como quem informa a hora correta | Se a referência estiver errada, todos os servidores ficam errados juntos |
| Hora no heartbeat | Campo `time` explícito na resposta | Usar só o `timestamp` da resposta, que tem o mesmo valor | Um campo a mais, mas o log mostra que a hora foi pedida |
| Cadastro da referência | Em memória | SQLite também na referência | Se a referência reiniciar, os ranks são distribuídos de novo na ordem dos heartbeats |

## Limitações conhecidas

| Limitação | Efeito | Motivo |
|---|---|---|
| Servidores não sincronizam dados | Um canal criado no `server-1` não aparece numa listagem atendida pelo `server-2` até ser criado lá; publicar nele pelo `server-2` recebe `CHANNEL_NOT_FOUND` | Cada servidor guarda só os próprios dados, como o enunciado pede; a sincronização ainda não faz parte do projeto |
| Um servidor pode ficar com menos de 5 canais | Quando um servidor completa os 5 canais, o bot que lista nele não cria mais nada, e o pedido de criação de quem lista no outro tende a cair de novo no servidor completo, porque o broker alterna pedidos seguidos entre servidores. Numa execução de 90 s, o `server-1` chegou a 5 canais, o `server-2` ficou com 1, e 88 de 183 pedidos de publicação receberam `CHANNEL_NOT_FOUND` | Mesmo motivo; nenhuma escolha do lado do bot resolve, porque o bot não escolhe o servidor que atende |
| Histórico dividido | Logins e publicações ficam só no servidor que atendeu | Mesmo motivo |
| Publicação não espera inscrito | Quem se inscreve depois não recebe as publicações anteriores, que continuam gravadas em disco | `PUB`/`SUB` entrega só para quem já está inscrito no momento do envio |
| Servidor ocioso sai da lista | Um servidor que fica 30 s sem receber 10 mensagens de clientes não manda heartbeat e é removido, mesmo vivo | O enunciado amarra o heartbeat ao número de mensagens, não ao tempo |
| Referência fora do ar | Os bots continuam sendo atendidos, mas cada heartbeat espera 2 s antes de desistir, e o relógio físico deixa de ser corrigido até ela voltar | A referência é um processo único |

## Testes

| Suíte | Como roda | O que testa |
|---|---|---|
| Black-box do sistema (`tests/`, pytest) | Container na rede do Compose, falando com o broker, o proxy e a referência como um cliente qualquer | Login, canais, publicação, entrega aos inscritos, relógio lógico nas respostas e publicações, protocolo da referência e o que fica gravado em disco |
| Unitários do servidor (`server/tests/`, pytest) | Na construção da imagem do servidor; a imagem não é gerada se um teste falhar | Relógio lógico, cálculo de Cristian e quando o servidor manda heartbeat e acerta o relógio |
| Unitários dos bots (`bot/tests/`, `node:test`) | Na construção da imagem do bot; a imagem não é gerada se um teste falhar | Relógio lógico e as decisões de criar, assinar e publicar |

A suíte black-box só lê o arquivo do `server-1`, em modo somente leitura, para conferir logins e publicações gravados, porque o protocolo não tem operação que devolva esse histórico. Os testes da referência usam um segundo serviço de referência, `reference-under-test`, com prazo de heartbeat de 1,5 s, para provar a remoção sem esperar 30 s.

```bash
docker compose -p distributed-bbs-test --profile test run --rm --build tests
```

```bash
docker compose -p distributed-bbs-test --profile test down -v
```

Essa execução usa um projeto separado, com só um servidor e sem bots, para o resultado não depender do rodízio do broker nem dos dados da execução principal.

Para os testes dos bots fora do Docker, dentro de `bot/`:

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
| `tests/test_protocol.py` | Formato binário, campos obrigatórios, limites do timestamp e do relógio lógico, operação desconhecida |
| `tests/test_logical_clock.py` | Relógio lógico do servidor nas respostas, nas recusas e nas publicações |
| `tests/test_reference.py` | Rank, lista, heartbeat com a hora, remoção por silêncio, volta com o mesmo rank e cadastro do `server-1` |
| `server/tests/test_clocks.py` | Relógio lógico, saturação no limite e cálculo de Cristian |
| `server/tests/test_reference_controller.py` | Heartbeat a cada 10 mensagens, pedido de rank quando falta e sincronização do relógio |
| `bot/tests/botDecisions.test.ts` | Números padronizados do enunciado e as decisões de criar, assinar e publicar |
| `bot/tests/logicalClock.test.ts` | Relógio lógico do bot |

## Se algo falhar

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Bot mostra `TIMEOUT` em sequência | Nenhum servidor conectado ao broker | Conferir com `docker compose ps` e subir um servidor; o bot volta sozinho |
| Bot publica mas nenhum bot recebe | O proxy caiu ou ninguém assina aquele canal | Conferir o `proxy` com `docker compose ps`; as linhas `SUBSCRIBED` mostram o que cada bot assina |
| `CHANNEL_NOT_FOUND` em parte das publicações | O canal não existe no servidor que atendeu | Esperado enquanto os servidores não sincronizam; ver "Limitações conhecidas" |
| `server-2` responde com horário 7 s à frente no começo | Atraso simulado de propósito | Some no primeiro heartbeat, depois de 10 mensagens de clientes |
| Servidor mostra `TIMEOUT` ao falar com a referência | A referência caiu | Conferir com `docker compose ps`; ao voltar, os servidores se cadastram de novo sozinhos |
| Bots listam os canais antigos depois de um novo começo | Os volumes foram preservados | `docker compose down -v` |
| Mudança em `server/database/database.sql` não aparece | A tabela já existe no volume | `docker compose down -v` |

## Organização

| Pasta | Conteúdo |
|---|---|
| `broker/` | Proxy `ROUTER`/`DEALER` dos pedidos |
| `proxy/` | Proxy `XSUB`/`XPUB` das publicações |
| `reference/` | Serviço de referência: rank, lista de servidores, heartbeat e hora |
| `server/src/resources/` | Laço de atendimento e rotas das operações |
| `server/src/schemas/` | Validação do formato dos pedidos e das respostas da referência |
| `server/src/controllers/` | Regras, decisão de gravar e publicar, conversa com a referência |
| `server/src/models/` | Publicação, relógio lógico e relógio físico |
| `server/src/repositories/` | Único lugar com SQL |
| `server/src/connectors/` | Único lugar que conhece ZeroMQ e MessagePack |
| `server/database/` | Schema do banco |
| `server/tests/` | Testes unitários do servidor |
| `bot/src/controllers/` | Comportamento do bot e suas decisões |
| `bot/src/connectors/` | Único lugar que conhece ZeroMQ e MessagePack |
| `bot/src/models/` | Relógio lógico do bot |
| `bot/tests/` | Testes unitários do bot |
| `tests/` | Suíte black-box |

## Glossário

| Termo | Nome no código | Não confundir com |
|---|---|---|
| Bot | `bot` | Servidor; o bot é o usuário do sistema |
| Usuário | `username`, `sender` no pedido do bot | `sender` na resposta e na publicação, que é o nome do servidor |
| Canal | `channel` | Conexão de rede |
| Tópico | `topic` | Canal: o tópico é o nome do canal usado como filtro do `PUB`/`SUB` |
| Login | `login` | Sessão; não existe sessão no sistema |
| Pedido | `RequestMessage` | Resposta |
| Resposta | `ResponseMessage` | Pedido |
| Publicação | `Publication`, `PublicationMessage` | Pedido de publicação (`publish`), que é o que o bot envia ao servidor |
| Autor | `author`, `author_username` | `sender` da publicação, que é o servidor |
| Inscrição | `subscribe` | Login; a inscrição é só do lado do bot e não passa pelo servidor |
| Relógio lógico | `logical_clock`, `LogicalClock` | `timestamp`, que é o relógio físico |
| Relógio físico | `PhysicalClock`, `offset_ms` | Relógio do sistema operacional, que não é alterado |
| Referência | `reference` | Broker; a referência só conversa com servidores |
| Rank | `rank` | Ordem de chegada dos pedidos; o rank é fixo por nome de servidor |
| Heartbeat | `heartbeat` | Login; o heartbeat é do servidor para a referência |
| Recusa | `BbsError` | Timeout, que é falta de resposta |

## Entregas

Cada parte é desenvolvida em uma branch própria.

| Parte | Branch | Conteúdo |
|---|---|---|
| 1 | `parte-1` | Login, criação e listagem de canais, persistência |
| 2 | `parte-2` | Publicação em canais com `PUB`/`SUB`, proxy, inscrições dos bots e persistência das publicações |
| 3 | `parte-3` | Relógio lógico em todas as mensagens, serviço de referência com rank, lista e heartbeat, sincronização do relógio físico |
