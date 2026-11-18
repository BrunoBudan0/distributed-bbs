# Distributed BBS

Sistema de troca de mensagens instantâneas inspirado no BBS e no IRC. Bots fazem login, criam canais públicos, se inscrevem neles e publicam mensagens. Todas as interações ficam gravadas em disco e replicadas em todos os servidores, todos os processos marcam as mensagens com um relógio lógico, os servidores elegem entre si um coordenador que sincroniza os relógios físicos pelo algoritmo de Berkeley, e podem entrar e sair sem parar o serviço nem perder dados.

Projeto individual da disciplina de Sistemas Distribuídos (Ciência da Computação, FEI), de Bruno Budano Mello.

## Arquitetura

São seis caminhos de mensagem:

1. Pedidos dos bots seguem por `REQ`/`REP` através do broker.
2. Publicações nos canais seguem por `PUB`/`SUB` através do proxy.
3. Os servidores conversam com o serviço de referência por `REQ`/`REP` para receber o rank, avisar que estão vivos e saber quem está disponível.
4. Os servidores conversam entre si, direto, por `REQ`/`REP` na porta 5560, para pedir eleição, pedir a hora ao coordenador e trocar com ele os registros que faltam.
5. O coordenador eleito se anuncia publicando no tópico `servers`, pelo mesmo proxy das publicações.
6. Toda escrita aceita por um servidor é difundida aos outros no tópico `replication`, pelo mesmo proxy.

```
Pedidos (REQ/REP)

bot-1 (REQ) --+                             +-- (REP) server-1 --> volume server-1-data
              +-- ROUTER [ broker ] DEALER -+
bot-2 (REQ) --+    5555             5556    +-- (REP) server-2 --> volume server-2-data

Publicações (PUB/SUB)

server-1 (PUB) --+                         +-- (SUB) bot-1
                 +-- XSUB [ proxy ] XPUB --+
server-2 (PUB) --+   5557          5558    +-- (SUB) bot-2

Rank, heartbeat e lista de servidores (REQ/REP)

server-1 (REQ) --+
                 +-- REP [ reference ] 5559
server-2 (REQ) --+

Eleição, hora e antientropia entre servidores (REQ/REP direto)

server-1 (REQ) -----> (REP 5560) server-2
server-1 (REP 5560) <----- (REQ) server-2

Anúncio do coordenador e difusão das escritas (PUB/SUB, tópicos servers e replication)

servidor (PUB) --> XSUB [ proxy ] XPUB --> (SUB servers, replication) server-1, server-2
```

| Serviço | Responsabilidade | Linguagem | Dados |
|---|---|---|---|
| `broker` | Repassa os pedidos dos bots para os servidores, em rodízio | Python | Nenhum |
| `proxy` | Repassa as publicações dos servidores para os bots inscritos no canal | Python | Nenhum |
| `reference` | Dá o rank de cada servidor e mantém a lista dos disponíveis por heartbeat | Python | Em memória |
| `server-1`, `server-2` | Validam os pedidos, aplicam as regras, gravam em disco, publicam nos canais, replicam todos os dados entre si, elegem o coordenador e sincronizam o relógio com ele | Python | Um volume por servidor, cada um com todos os dados |
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

O relógio lógico salta de 28 para 32 porque o servidor já estava em 31: logo antes, ele trocou mensagens com outro processo e ficou com o maior valor.

Na publicação recebida, `timestamp` é o envio pelo servidor e `received_at` é a chegada ao bot.

Ao subir, cada servidor pede o rank e faz uma eleição. O de rank maior vence e se anuncia no tópico `servers`:

```
server-1-1   | ELECTION | started by this server | asking higher ranked servers=[]
server-1-1   | ELECTION | no higher ranked server answered | this server is now the coordinator
server-2-1   | ELECTION | started by this server | asking higher ranked servers=[]
server-2-1   | ELECTION | no higher ranked server answered | this server is now the coordinator
server-2-1   | SENT     | topic='servers' | operation='coordinator' | sender='server-2' | timestamp=2026-11-11T19:41:03.023Z | logical_clock=8 | payload={'coordinator': 'server-2'}
server-1-1   | RECEIVED | topic='servers' | operation='coordinator' | sender='server-2' | timestamp=2026-11-11T19:41:03.023Z | logical_clock=8 | payload={'coordinator': 'server-2'}
server-1-1   | ELECTION | announcement received | coordinator='server-2'
```

O `server-1` subiu antes de o `server-2` estar cadastrado e se declarou coordenador por um instante; ao receber o anúncio de rank maior, passou a seguir o `server-2`.

O `server-2` começa com o relógio físico adiantado em 7 s de propósito (`SIMULATED_CLOCK_SKEW_MS` no compose), porque no Docker todos os containers usam o relógio da mesma máquina e não haveria nada para sincronizar. Na primeira rodada de Berkeley, o coordenador faz a média entre os dois relógios e os dois se encontram no meio:

```
server-1-1   | SENT     | operation='clock' | sender='server-1' | timestamp=2026-11-11T19:41:02.068Z | logical_clock=38 | payload={}
server-2-1   | RECEIVED | operation='clock' | sender='server-1' | timestamp=2026-11-11T19:41:02.068Z | logical_clock=38 | payload={}
server-2-1   | BERKELEY | clock of 'server-1' was -7003 ms from this coordinator | average adjustment_ms=-3502 | coordinator offset_after_ms=3498
server-2-1   | SENT     | operation='clock' | sender='server-2' | timestamp=2026-11-11T19:41:05.569Z | logical_clock=39 | status='success' | payload={'time': 1794426065569}
server-1-1   | RECEIVED | operation='clock' | sender='server-2' | timestamp=2026-11-11T19:41:05.569Z | logical_clock=39 | status='success' | payload={'time': 1794426065569}
server-1-1   | CLOCK    | physical clock synchronized with the coordinator 'server-2' | offset_before_ms=0 | offset_after_ms=3499 | round_trip_ms=4
```

Os dois servidores passam a concordar em +3,5 s em relação à máquina. Berkeley busca acordo entre os relógios do grupo, não a hora certa.

Se o coordenador cair, o outro servidor percebe no próximo pedido de hora e assume:

```
server-1-1   | TIMEOUT  | the server 'server-2' did not answer
server-1-1   | ELECTION | started by this server | asking higher ranked servers=['server-2']
server-1-1   | TIMEOUT  | the server 'server-2' did not answer
server-1-1   | ELECTION | no higher ranked server answered | this server is now the coordinator
```

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
| `heartbeat` | `{}` | `{}` |

Operações atendidas por um servidor, pedidas por outro servidor (porta 5560; o `sender` é o nome de quem pede e o `timestamp` é o relógio dele):

| Operação | `payload` do pedido | `payload` da resposta com sucesso |
|---|---|---|
| `election` | `{}` | `{}`, o OK da eleição |
| `clock` | `{}` | `{time: 1794426065569}`, a hora combinada pelo coordenador em milissegundos |
| `replication_sync` | `{watermarks: {"server-1": 12, ...}}` | `{records: [registro, ...], watermarks: {...}}`: os registros que quem pediu não tem e as marcas de quem respondeu |
| `replication_push` | `{records: [registro, ...]}`, até 500 | `{}` |

Anúncio do coordenador, publicado no tópico `servers`: `{operation: "coordinator", sender, timestamp, logical_clock, payload: {coordinator: "server-2"}}`.

Difusão de uma escrita, publicada no tópico `replication`: `{operation: "replicated_record", sender, timestamp, logical_clock, payload: registro}`.

Um registro replicado tem o formato `{origin_server, origin_sequence, kind, logical_clock, content}`, em que `kind` é `login`, `channel` ou `publication` e `content` traz os campos da linha gravada (por exemplo, `{username, logged_in_at_ms}` num login).

Uma resposta com erro traz `{error_code, error_description}` no `payload`.

| `error_code` | Quem devolve | Quando acontece |
|---|---|---|
| `MALFORMED_MESSAGE` | Servidor e referência | Os bytes não são MessagePack, ou falta campo, ou um campo tem tipo ou faixa inválidos |
| `UNKNOWN_OPERATION` | Servidor e referência | A operação não existe |
| `INVALID_USERNAME` | Servidor | O nome do usuário está fora do formato permitido |
| `INVALID_CHANNEL_NAME` | Servidor | O nome do canal está fora do formato permitido ou é `servers` ou `replication`, tópicos reservados aos servidores |
| `CHANNEL_ALREADY_EXISTS` | Servidor | Já existe canal com esse nome no servidor que atendeu |
| `CHANNEL_NOT_FOUND` | Servidor | Pedido de publicação num canal que não existe no servidor que atendeu |
| `INVALID_MESSAGE` | Servidor | A mensagem não é texto ou está fora do tamanho permitido |
| `INVALID_SERVER_NAME` | Referência e servidor | O nome do servidor que pede está fora do formato permitido |
| `UNKNOWN_SERVER` | Referência | Heartbeat de um servidor que nunca pediu rank |
| `NOT_COORDINATOR` | Servidor | Pedido de hora a um servidor que não é o coordenador |
| `INVALID_RECORD` | Servidor | Registro replicado com origem, sequência, tipo ou conteúdo inválidos; nada do lote é gravado |

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
| Timeout de resposta | 5 s no bot, 2 s no servidor falando com a referência e 1 s entre servidores; quem pediu descarta o socket `REQ` e abre outro | Um `REQ` sem resposta fica preso e não aceita novo envio |

### Relógios

| Regra | Lógica | Por quê |
|---|---|---|
| Relógio lógico | Bots, servidores e referência começam em 0, somam 1 antes de cada envio e mandam o valor em `logical_clock`. Ao receber, ficam com o maior entre o próprio e o recebido | Relógio de Lamport, como apresentado em aula |
| Mensagem recusada | O `logical_clock` recebido é considerado mesmo quando o pedido é recusado, desde que o campo seja válido | Toda mensagem recebida conta, não só as aceitas |
| Limite do relógio lógico | Aceito de 0 a 2^52; ao chegar no limite, o relógio para ali em vez de passar | Sem esse teto, um único cliente mandando o valor máximo empurraria todos os processos para além dele, e daí em diante todos os pedidos seriam recusados. 2^52 cabe com folga no maior inteiro exato do JavaScript |
| Rank | A referência dá ranks 1, 2, 3... na ordem do primeiro pedido; o mesmo nome recebe sempre o mesmo rank | O enunciado pede a lista sem nomes repetidos |
| Heartbeat | O servidor envia um heartbeat depois de cada 10 mensagens de clientes e, em seguida, pede a lista de servidores. A resposta do heartbeat não traz mais a hora | Frequência pedida pelo enunciado; o heartbeat sai depois da resposta ao bot, para não atrasá-lo |
| Remoção | A referência tira da lista o servidor sem rank nem heartbeat há mais de 30 s; ele volta com o mesmo rank no próximo heartbeat | Disponibilidade separada do cadastro, para o rank não mudar a cada queda |
| Referência reiniciada | Ela esquece os servidores; o heartbeat recebe `UNKNOWN_SERVER` e o servidor pede rank de novo | O cadastro fica em memória |
| Sincronização do relógio físico | Depois de cada 15 mensagens de clientes, o servidor que não é coordenador pede a hora ao coordenador (`clock`), mandando o próprio relógio no `timestamp` | Frequência pedida pelo enunciado |
| Berkeley no coordenador | O coordenador guarda a diferença de cada servidor que pediu nos últimos 60 s, faz a média com a própria diferença (zero), ajusta o próprio relógio pela média e responde com a hora resultante | É a média de Berkeley: o grupo converge para um valor comum. Leituras com mais de 60 s ficam de fora para um servidor que sumiu não puxar a média |
| Ajuste de quem pediu | O servidor adota a hora recebida mais metade do tempo de ida e volta | Compensa a demora da resposta em chegar |
| Onde o ajuste vale | O servidor guarda um deslocamento (`offset_ms`) e o soma a todo `timestamp` que envia e grava | O container não tem permissão para mudar o relógio do sistema |

### Eleição

| Regra | Lógica | Por quê |
|---|---|---|
| Quem é o coordenador | O servidor disponível de maior rank. Cada servidor guarda o nome do coordenador em `coordinator_name` | Algoritmo do valentão (Bully): vence o maior identificador |
| Quando há eleição | Ao subir; quando o coordenador não responde ao pedido de hora ou diz que não é coordenador; quando ainda não se sabe quem é o coordenador; ao receber um pedido de eleição; ao receber o anúncio de um servidor de rank menor | Toda forma de descobrir que o coordenador sumiu ou que existe alguém maior |
| Para quem se pede | Só para os servidores de rank maior, da lista da referência | Pedidos só sobem de rank, então ninguém fica esperando quem está esperando por ele |
| Resposta | Quem recebe `election` responde OK na hora e faz a própria eleição em seguida | O OK diz a quem pediu que existe alguém maior vivo |
| Resultado | Se nenhum maior responder em 1 s, o servidor vira coordenador e publica `[servers] {coordinator: nome}`. Se algum responder, ele espera o anúncio | Igual ao Bully; o anúncio vale para todos os servidores de uma vez |
| Anúncio perdido | Quem não sabe o coordenador faz nova eleição na próxima sincronização | O `SUB` pode perder um anúncio enviado antes de a inscrição chegar ao proxy |
| Servidor sem rank | Não faz eleição até ter rank | Sem rank não há como comparar |

### Comportamento padronizado dos bots

A cada rodada, o bot:

1. Lista os canais.
2. Se a lista tiver menos de 5 canais, cria um canal sorteado entre os do catálogo fixo (`general`, `news`, `sports`, `music`, `movies`) que não estão na lista.
3. Se estiver inscrito em menos de 3 canais, se inscreve em um canal da lista, sorteado entre os que ainda não assina.
4. Sorteia um canal da lista e envia 10 mensagens sorteadas de um catálogo, uma por segundo.

O enunciado descreve os passos 2 e 3 "ao conectar". Eles são repetidos em toda rodada porque, feitos uma vez só, cada bot terminaria com 1 inscrição e o sistema com 2 canais. Repetindo, o bot chega aos 5 canais e às 3 inscrições, e a primeira rodada continua igual à descrição.

O catálogo de canais tem exatamente 5 nomes, para os bots nunca criarem nomes sem fim. O nome é sorteado entre os que faltam porque, antes da replicação, pegando sempre o primeiro, os bots travavam: a lista vinha de um servidor, o pedido de criação caía no outro, e o canal escolhido era justamente o que esse outro já tinha.

## Replicação

### O problema

O broker reparte os pedidos dos bots entre os servidores em rodízio. Sem replicação, cada servidor guarda só a parte que passou por ele:
- um canal criado no `server-1` não existe no `server-2`, e publicar nele pelo `server-2` falha;
- o histórico fica dividido;
- se um servidor para, a parte dele some.

O enunciado pede que todos os servidores tenham todos os dados.

### O método escolhido

Replicação por **propagação de atualizações com consistência eventual**: cada servidor aceita a escrita, grava e propaga a atualização aos outros. A propagação tem dois caminhos, ambos vistos em aula:

| Caminho | Como funciona | O que garante |
|---|---|---|
| Difusão (*push*) | Logo depois de gravar, o servidor publica o registro no tópico `replication`; todos os servidores assinam o tópico e aplicam o registro | Os outros servidores recebem a escrita em milissegundos |
| Antientropia (protocolo epidêmico *push-pull*) | A cada 15 mensagens de clientes, ao subir e sempre que conhece um novo coordenador, o servidor manda ao coordenador as suas marcas d'água; o coordenador devolve os registros que faltam e as marcas dele, e o servidor manda de volta o que falta ao coordenador | Recupera o que a difusão perdeu e faz a transferência de estado para quem estava fora do ar ou acabou de chegar |

### Como foi implementado

| Peça | Onde | Papel |
|---|---|---|
| Registro replicado | Tabela `replicated_record`, `models/replicated_record.py` | Toda escrita aceita (login, canal ou publicação) vira um registro identificado por (servidor de origem, sequência da origem). O registro é gravado na mesma transação que a linha de dado |
| Log de registros | `repositories/replication_repository.py` | Guarda todos os registros, inclusive os que perderam um conflito, para que a sequência de cada origem não tenha buracos |
| Marca d'água | `contiguous_watermarks` | Para cada origem, a maior sequência sem nenhum buraco antes dela. Se o servidor tem 1, 2 e 4, a marca é 2, e o 3 e o 4 serão pedidos de novo |
| Aplicação idempotente | `controllers/replication_controller.py` | Um registro só é aplicado na primeira vez em que chega; repetições são ignoradas, então a ordem e a duplicação de entregas não importam |
| Conflito de canal | `models/channel.py` | Se o mesmo canal é criado em dois servidores ao mesmo tempo, vence a criação com o menor (relógio lógico, nome do servidor). É a ordem total de Lamport, então todos os servidores escolhem o mesmo vencedor sem conversar |
| Transferência de estado | `synchronize_on_new_coordinator` | Um servidor que volta ou que acabou de chegar recebe o histórico inteiro, em lotes de até 500 registros por troca |

### Mudanças no método

| Mudança | Por quê |
|---|---|
| A escrita não espera as outras réplicas | O pedido do bot é respondido assim que o servidor que atendeu grava. A replicação clássica com escrita em todas as réplicas faria o bot esperar o servidor mais lento ou parado |
| Sem ordem total na entrega | Os registros são idempotentes e comutativos (logins e publicações só se somam; canal tem regra de vencedor), então a ordem de chegada não muda o resultado final |
| Antientropia sempre com o coordenador | Em vez de escolher outro servidor ao acaso, como no protocolo epidêmico, cada servidor conversa com o coordenador da Parte 4. Os pedidos só sobem até o coordenador, então ninguém espera quem está esperando por ele, e todos convergem passando por um ponto em comum |
| Publicação de um canal ainda desconhecido é aceita | A publicação replicada pode chegar antes do registro do canal, que vem de outra origem. Por isso a tabela `publication` deixou de ter chave estrangeira para `channel`; o canal chega logo depois |

Foi descartada a replicação **primário-backup** (escrita remota no coordenador). Com ela, toda escrita passaria pelo coordenador e uma troca de coordenador no meio de uma escrita exigiria numerar as escritas por mandato para não reaproveitar números. Com registros idempotentes e comutativos, uma queda não perde escritas nem cria números repetidos.

### O que se observa rodando

Numa execução com os bots publicando, os bancos dos servidores foram comparados por um resumo de todos os registros, canais, logins e publicações:

| Situação | Resultado |
|---|---|
| 60 s com os dois servidores | Bancos idênticos, com 125 registros. Nenhuma publicação recebeu `CHANNEL_NOT_FOUND` |
| `server-2` parado por 25 s e religado | Ao voltar, recebeu do coordenador os 50 registros que perdeu; bancos idênticos de novo, com 249 registros |
| Um `server-3` novo, sem dados, entra | Vira coordenador por ter o maior rank, os outros mandam a ele todo o histórico, e os três bancos ficam idênticos, com 313 registros |

Nos três casos há um registro a mais do que linhas gravadas: um canal foi criado ao mesmo tempo nos dois servidores, os dois registros ficaram no log, e todos os servidores mantiveram a mesma criação vencedora.

## Escolhas e seus custos

| Assunto | Escolha | Alternativa descartada | Custo da escolha |
|---|---|---|---|
| Linguagens | Python no broker, no proxy, na referência e no servidor; TypeScript nos bots | Java nos bots: mais verboso e com etapa de build mais pesada | A biblioteca `zeromq` para Node depende de um binário nativo |
| Serialização | MessagePack | Protobuf: exige arquivo `.proto` e geração de código nas duas linguagens | Sem schema compartilhado; cada lado valida o formato no próprio código |
| Persistência | SQLite, um arquivo por servidor em volume próprio | Arquivo JSON Lines: legível, mas exigiria implementar unicidade e escrita atômica | O arquivo é binário; para inspecionar é preciso um cliente SQLite |
| Pedidos | `REQ`/`ROUTER`/`DEALER`/`REP` | `REQ`/`REP` direto: o bot precisaria conhecer cada servidor | O broker é ponto único de falha |
| Publicações | `PUB`/`XSUB`/`XPUB`/`SUB`, com o proxy separado do broker | `PUB` no servidor e `SUB` ligado direto nele: o bot teria de conhecer cada servidor | Mais um ponto único de falha |
| Isolamento dos caminhos | Um contexto ZeroMQ por caminho: pedidos dos bots, publicações, referência, pedidos entre servidores e anúncios, no servidor e no bot | Um contexto só por processo | Com um contexto só, a queda do proxy travava também os pedidos: cada tentativa de reconexão consulta o DNS por 3,5 s no mesmo thread de I/O. Separados, a queda do proxy não atrasa nenhuma resposta |
| Tópico | Nome do canal no primeiro frame; o bot confere se o tópico é exatamente um canal assinado | Confiar só no filtro do ZeroMQ, que compara por prefixo e entregaria `news-br` a quem assina `news` | Uma verificação a mais no bot |
| Publicações em disco | Tabela `publication` com canal, autor, mensagem, horário do pedido, horário da publicação e servidor que publicou | Gravar só o texto | Mais colunas, mas qualquer informação pode ser recuperada depois |
| Timestamp do login e do pedido | O da mensagem do bot | Relógio do servidor | Confia no relógio do cliente |
| Sincronização do relógio físico | Berkeley com o coordenador eleito, no formato pedido pelo enunciado: cada servidor manda o próprio relógio e recebe a hora combinada | Berkeley clássico, com o coordenador consultando todos os servidores de uma vez: o enunciado define o servidor como quem pergunta | A média só usa as leituras recebidas nos últimos 60 s |
| Hora no pedido de relógio | O próprio `timestamp` do pedido, que já é o relógio de quem pede | Um campo a mais no `payload` | Nenhum; o `timestamp` existe em toda mensagem |
| Hora na resposta | Campo `time` explícito | Usar só o `timestamp` da resposta | Um campo a mais, mas o log mostra que a hora foi pedida |
| Eleição | Bully, por rank | Anel: exige conhecer a ordem dos vizinhos e circular a mensagem por todos | Pedidos em sequência aos ranks maiores, 1 s de espera por servidor que não responde |
| Endereço de outro servidor | O nome do servidor, que é o nome do serviço no Compose, na porta 5560 | Guardar endereços na referência | O nome do servidor precisa ser igual ao nome do container |
| Tópicos `servers` e `replication` | Reservados: nenhum canal pode ter esses nomes, e o servidor só aceita em cada tópico o tipo de mensagem esperado | Aceitar qualquer publicação no tópico | Um bot não consegue se passar por coordenador nem injetar registros criando um canal com esses nomes |
| Replicação | Propagação de atualizações com consistência eventual, difusão pelo tópico `replication` e antientropia com o coordenador | Primário-backup com escrita remota no coordenador | Por alguns milissegundos depois de uma escrita, outro servidor ainda pode não ter o dado |
| Conteúdo do registro no banco | JSON na coluna `content` da tabela `replicated_record` | Uma tabela de log por tipo de dado | O conteúdo do registro não é validado pelo banco, só pelo servidor ao receber |
| Versão do banco | `PRAGMA user_version = 5`; um volume de uma parte anterior faz o servidor parar com a instrução `docker compose down -v` | Migrar as tabelas antigas | Os dados de execuções das partes anteriores não são aproveitados |
| Cadastro da referência | Em memória | SQLite também na referência | Se a referência reiniciar, os ranks são distribuídos de novo na ordem dos heartbeats |

## Limitações conhecidas

| Limitação | Efeito | Motivo |
|---|---|---|
| Consistência eventual | Por alguns milissegundos depois de uma escrita, outro servidor ainda não tem o dado; se a difusão se perder, a diferença dura até a próxima antientropia (15 mensagens de clientes) | A escrita não espera as outras réplicas |
| Dois bots criam o mesmo canal ao mesmo tempo | Os dois recebem sucesso, e os servidores ficam com uma só criação, a de menor relógio lógico | Cada servidor decide a criação sozinho; o conflito é resolvido depois |
| Antientropia depende de tráfego | Sem mensagens de clientes e sem troca de coordenador, um registro perdido pela difusão espera até o próximo pedido | O enunciado amarra os gatilhos periódicos ao número de mensagens |
| O log cresce sempre | A tabela `replicated_record` guarda cada escrita para sempre | Sem compactação; para o tamanho do projeto não pesa |
| Publicação não espera inscrito | Quem se inscreve depois não recebe as publicações anteriores, que continuam gravadas em disco | `PUB`/`SUB` entrega só para quem já está inscrito no momento do envio |
| Servidor ocioso sai da lista | Um servidor que fica 30 s sem receber 10 mensagens de clientes não manda heartbeat e é removido, mesmo vivo | O enunciado amarra o heartbeat ao número de mensagens, não ao tempo |
| Referência fora do ar | Os bots continuam sendo atendidos, mas cada heartbeat espera 2 s antes de desistir, e a lista de servidores usada na eleição fica parada na última versão | A referência é um processo único |
| Berkeley não busca a hora certa | Com o atraso simulado de 7 s, o grupo concorda em cerca de +3,5 s em relação à máquina; se o servidor adiantado reinicia, o acordo se desloca de novo (numa execução, para +5,2 s) | Berkeley faz a média do grupo e não tem fonte de hora externa |
| Espera durante a eleição | Enquanto pede eleição ou hora a outro servidor, o servidor não atende bots; cada servidor que não responde custa 1 s | O laço de atendimento é de uma linha só |
| Dois coordenadores por um instante | Ao subir, um servidor que ainda não vê o maior na lista se declara coordenador até o anúncio do maior chegar | A lista da referência só mostra quem já se cadastrou |
| Anúncio sem autenticação | Qualquer processo na rede do Compose pode publicar no tópico `servers` | Protótipo; os testes usam isso para simular um coordenador que caiu |

## Testes

| Suíte | Como roda | O que testa |
|---|---|---|
| Black-box do sistema (`tests/`, pytest) | Container na rede do Compose, falando com o broker, o proxy, a referência e a porta 5560 do `server-1` como um cliente qualquer | Login, canais, publicação, entrega aos inscritos, relógio lógico, protocolo da referência, eleição, anúncio, Berkeley, replicação e o que fica gravado em disco |
| Unitários do servidor (`server/tests/`, pytest) | Na construção da imagem do servidor; a imagem não é gerada se um teste falhar | Relógio lógico, média de Berkeley, regras da eleição, sincronização a cada 15 mensagens, heartbeat a cada 10, log de registros e antientropia |
| Unitários dos bots (`bot/tests/`, `node:test`) | Na construção da imagem do bot; a imagem não é gerada se um teste falhar | Relógio lógico e as decisões de criar, assinar e publicar |

A suíte black-box só lê o arquivo do `server-1`, em modo somente leitura, para conferir logins e publicações gravados, porque o protocolo não tem operação que devolva esse histórico. Os testes da referência usam um segundo serviço de referência, `reference-under-test`, com prazo de heartbeat de 1,5 s, para provar a remoção sem esperar 30 s. Para provar a troca de coordenador, um teste publica no tópico `servers` o anúncio de um coordenador que não existe e confere que o `server-1` percebe a falta dele e assume. Os testes que mudam um relógio usado pelos demais levam a marcação `changes_shared_clock` e rodam por último.

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
| `tests/test_reference.py` | Rank, lista, heartbeat sem hora, remoção por silêncio, volta com o mesmo rank e cadastro do `server-1` |
| `tests/test_coordination.py` | OK da eleição, anúncio no tópico `servers`, hora do coordenador, média de Berkeley e troca de coordenador quando ele some |
| `tests/test_replication.py` | Toda escrita vira registro e é difundida, registros recebidos aparecem para os bots, repetição ignorada, marca d'água com buraco, conflito de canal e recusa de registro inválido |
| `server/tests/test_clocks.py` | Relógio lógico, saturação no limite e compensação da ida e volta |
| `server/tests/test_berkeley.py` | Média de Berkeley, leituras vencidas e reposicionamento das leituras |
| `server/tests/test_coordination_controller.py` | Para quem se pede eleição, quando assumir, Bully, sincronização a cada 15 mensagens e recusa de quem não é coordenador |
| `server/tests/test_reference_controller.py` | Heartbeat a cada 10 mensagens, pedido de rank quando falta e lista de servidores |
| `server/tests/test_replication_repository.py` | Sequência por origem, gravação única, marca d'água e limite por troca, num SQLite em memória |
| `server/tests/test_replication_controller.py` | Aplicação idempotente, conflito de canal, antientropia nos dois sentidos e coordenador fora do ar |
| `server/tests/test_channel.py` | Regra do vencedor no conflito de canal |
| `bot/tests/botDecisions.test.ts` | Números padronizados do enunciado e as decisões de criar, assinar e publicar |
| `bot/tests/logicalClock.test.ts` | Relógio lógico do bot |

## Se algo falhar

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Bot mostra `TIMEOUT` em sequência | Nenhum servidor conectado ao broker | Conferir com `docker compose ps` e subir um servidor; o bot volta sozinho |
| Bot publica mas nenhum bot recebe | O proxy caiu ou ninguém assina aquele canal | Conferir o `proxy` com `docker compose ps`; as linhas `SUBSCRIBED` mostram o que cada bot assina |
| `CHANNEL_NOT_FOUND` logo depois de criar um canal | A difusão do canal ainda não chegou ao servidor que atendeu | Raro e passageiro; some em milissegundos |
| Servidor para com "schema version" no log | Volume de dados de uma parte anterior | `docker compose down -v` |
| Servidores respondem com horário alguns segundos à frente da máquina | Atraso simulado de 7 s no `server-2` e média de Berkeley | Esperado; os servidores concordam entre si. Para tirar o atraso, apague `SIMULATED_CLOCK_SKEW_MS` do compose |
| Servidor mostra `TIMEOUT` ao falar com outro servidor | O outro servidor caiu | Esperado; se era o coordenador, há eleição e um novo coordenador se anuncia |
| Servidor mostra `TIMEOUT` ao falar com a referência | A referência caiu | Conferir com `docker compose ps`; ao voltar, os servidores se cadastram de novo sozinhos |
| Bots listam os canais antigos depois de um novo começo | Os volumes foram preservados | `docker compose down -v` |
| Mudança em `server/database/database.sql` não aparece | A tabela já existe no volume | `docker compose down -v` |

## Organização

| Pasta | Conteúdo |
|---|---|
| `broker/` | Proxy `ROUTER`/`DEALER` dos pedidos |
| `proxy/` | Proxy `XSUB`/`XPUB` das publicações |
| `reference/` | Serviço de referência: rank, lista de servidores e heartbeat |
| `server/src/resources/` | Laço que ouve os três sockets de entrada e as rotas das operações |
| `server/src/schemas/` | Validação do formato dos pedidos, dos anúncios e das respostas de outros processos |
| `server/src/controllers/` | Regras, decisão de gravar e publicar, conversa com a referência, eleição, Berkeley e replicação |
| `server/src/models/` | Publicação, relógio lógico, relógio físico e média de Berkeley |
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
| Coordenador | `coordinator_name` | Referência; o coordenador é um dos servidores, eleito entre eles |
| Eleição | `election`, `hold_election` | Rank; o rank vem da referência, a eleição usa o rank para decidir |
| Anúncio | `CoordinatorAnnouncement`, tópico `servers` | Publicação em canal; o anúncio vai só para servidores |
| Rodada de Berkeley | `BerkeleyCoordinator`, operação `clock` | Cristian; aqui o coordenador faz a média, não é dono da hora |
| Registro replicado | `ReplicatedRecord`, tabela `replicated_record` | Mensagem de pedido; o registro é o fato gravado, com origem e sequência |
| Marca d'água | `watermarks`, `contiguous_watermarks` | Maior sequência recebida; a marca para no primeiro buraco |
| Antientropia | `replication_sync`, `replication_push` | Difusão; a antientropia é a conferência periódica que recupera o que a difusão perdeu |
| Recusa | `BbsError` | Timeout, que é falta de resposta |

## Entregas

Cada parte é desenvolvida em uma branch própria.

| Parte | Branch | Conteúdo |
|---|---|---|
| 1 | `parte-1` | Login, criação e listagem de canais, persistência |
| 2 | `parte-2` | Publicação em canais com `PUB`/`SUB`, proxy, inscrições dos bots e persistência das publicações |
| 3 | `parte-3` | Relógio lógico em todas as mensagens, serviço de referência com rank, lista e heartbeat, sincronização do relógio físico |
| 4 | `parte-4` | Eleição do coordenador (Bully), anúncio no tópico `servers` e sincronização dos relógios por Berkeley com o coordenador |
| 5 | `parte-5` | Replicação de todos os dados em todos os servidores: difusão no tópico `replication`, antientropia com o coordenador e conflito resolvido pelo relógio lógico |
