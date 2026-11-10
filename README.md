# Distributed BBS

Sistema de troca de mensagens instantâneas inspirado no BBS e no IRC. Bots fazem login, descobrem e criam canais públicos, todas as interações ficam gravadas em disco e os servidores podem entrar e sair sem parar o serviço.

Projeto individual da disciplina de Sistemas Distribuídos (Ciência da Computação, FEI), de Bruno Budano Mello.

## Arquitetura

Cada bot abre um socket `REQ` no broker. O broker repassa os pedidos, em rodízio, para os servidores conectados, que respondem por um socket `REP`.

```
bot-1 (REQ) --+                             +-- (REP) server-1 --> volume server-1-data
              +-- ROUTER [ broker ] DEALER -+
bot-2 (REQ) --+    5555             5556    +-- (REP) server-2 --> volume server-2-data
```

| Serviço | Responsabilidade | Linguagem | Dados |
|---|---|---|---|
| `broker` | Único endereço conhecido por bots e servidores; repassa as mensagens | Python | Nenhum |
| `server-1`, `server-2` | Validam os pedidos, aplicam as regras e gravam em disco | Python | Um volume por servidor |
| `bot-1`, `bot-2` | Usuários automáticos: fazem login, listam e criam canais | TypeScript | Nenhum |

Toda a comunicação usa a rede criada pelo Docker Compose. Nenhuma porta é publicada na máquina.

## Subindo

Precisa só de **Docker** (com o Docker Compose v2). Na raiz do repositório:

```bash
docker compose up
```

Nenhuma interação é necessária. Clientes e servidores mostram no terminal cada mensagem enviada (`SENT`) ou recebida (`RECEIVED`), com o conteúdo completo:

```
bot-1-1     | SENT     | operation='create_channel' | sender='bot-1' | timestamp=2026-11-09T19:06:53.251Z | payload={ channel: 'general' }
server-1-1  | RECEIVED | operation='create_channel' | sender='bot-1' | timestamp=2026-11-09T19:06:53.251Z | payload={'channel': 'general'}
server-1-1  | SENT     | operation='create_channel' | sender='server-1' | timestamp=2026-11-09T19:06:53.258Z | status='success' | payload={}
bot-1-1     | RECEIVED | operation='create_channel' | sender='server-1' | timestamp=2026-11-09T19:06:53.258Z | status='success' | payload={}
```

Para desligar mantendo os dados, `docker compose down`. Para desligar **e apagar os dados dos servidores**, `docker compose down -v`.

## Protocolo

Todas as mensagens são mapas MessagePack enviados em um único frame.

| Campo | Tipo | Pedido | Resposta |
|---|---|---|---|
| `operation` | texto | Operação pedida | Operação atendida, ou `unidentified` se não foi possível identificar |
| `sender` | texto | Nome do usuário | Nome do servidor que respondeu |
| `timestamp` | inteiro | Envio do pedido, em milissegundos desde 1970 (UTC) | Envio da resposta, na mesma unidade |
| `payload` | mapa | Dados da operação | Dados da resposta ou do erro |
| `status` | texto | Não existe | `success` ou `error` |

| Operação | `payload` do pedido | `payload` da resposta com sucesso |
|---|---|---|
| `login` | `{}` | `{}` |
| `create_channel` | `{channel: "nome"}` | `{}` |
| `list_channels` | `{}` | `{channels: ["nome", ...]}` |

Uma resposta com erro traz `{error_code, error_description}` no `payload`.

| `error_code` | Quando acontece |
|---|---|
| `MALFORMED_MESSAGE` | Os bytes não são MessagePack, ou falta campo, ou um campo tem tipo ou faixa inválidos |
| `UNKNOWN_OPERATION` | A operação não existe |
| `INVALID_USERNAME` | O nome do usuário está fora do formato permitido |
| `INVALID_CHANNEL_NAME` | O nome do canal está fora do formato permitido |
| `CHANNEL_ALREADY_EXISTS` | Já existe canal com esse nome no servidor que atendeu |

## Regras

| Regra | Lógica | Por quê |
|---|---|---|
| Nome de usuário | 1 a 32 letras, dígitos, `_` ou `-` | Tamanho limitado e seguro para exibir no log |
| Nome de canal | 1 a 32 letras minúsculas, dígitos ou `-` | Só minúsculas impede `Geral` e `geral` como canais distintos |
| Login repetido do mesmo usuário | Aceito, e cada login é gravado | O enunciado pede o histórico de todos os logins e não há sessão |
| Canal duplicado | Recusado com `CHANNEL_ALREADY_EXISTS` | O canal original continua o mesmo |
| Erro ou timeout no login | O bot repete o login a cada 2 s até ser aceito | Exigência do enunciado |
| Quando o bot cria canal | Ao listar, cria o primeiro canal de um catálogo fixo que não esteja na lista | Critério simples e previsível; o bot para de criar quando vê o catálogo inteiro |
| Timeout de resposta | 5 s; o bot descarta o socket `REQ` e abre outro | Um `REQ` sem resposta fica preso e não aceita novo envio |

## Escolhas e seus custos

| Assunto | Escolha | Alternativa descartada | Custo da escolha |
|---|---|---|---|
| Linguagens | Python no broker e no servidor, TypeScript nos bots | Java nos bots: mais verboso e com etapa de build mais pesada | A biblioteca `zeromq` para Node depende de um binário nativo |
| Serialização | MessagePack | Protobuf: exige arquivo `.proto` e geração de código nas duas linguagens | Sem schema compartilhado; cada lado valida o formato no próprio código |
| Persistência | SQLite, um arquivo por servidor em volume próprio | Arquivo JSON Lines: legível, mas exigiria implementar unicidade e escrita atômica | O arquivo é binário; para inspecionar é preciso um cliente SQLite |
| Timestamp do login | O da mensagem do bot | Relógio do servidor | Confia no relógio do cliente, que aqui é o mesmo da máquina hospedeira |
| Padrão de mensagens | `REQ`/`ROUTER`/`DEALER`/`REP` | `REQ`/`REP` direto: o bot precisaria conhecer cada servidor | O broker é ponto único de falha |

## Limitação conhecida

Cada servidor guarda só o próprio conjunto de dados, como o enunciado pede, e nesta parte os servidores ainda não conversam entre si. Como o broker alterna entre eles, um canal criado no `server-1` não aparece numa listagem atendida pelo `server-2`, até que também seja criado lá. O mesmo vale para o histórico de logins.

## Testes

Os testes são black-box: rodam em um container na rede do Compose e falam com o sistema pelo broker, como um cliente qualquer. A única exceção é a leitura somente leitura do arquivo do `server-1` para conferir os logins gravados, porque o protocolo não tem operação que devolva esse histórico.

```bash
docker compose -p distributed-bbs-test --profile test run --rm --build tests
```

```bash
docker compose -p distributed-bbs-test --profile test down -v
```

Essa execução usa um projeto separado, com só um servidor, para o resultado não depender do rodízio do broker nem dos dados da execução principal.

| Arquivo | O que testa |
|---|---|
| `tests/test_login.py` | Login aceito, formato do nome e gravação em disco |
| `tests/test_channels.py` | Criação, duplicidade, formato do nome e listagem |
| `tests/test_protocol.py` | Formato binário, campos obrigatórios, limites do timestamp e operação desconhecida |

## Se algo falhar

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Bot mostra `TIMEOUT` em sequência | Nenhum servidor conectado ao broker | Conferir com `docker compose ps` e subir um servidor; o bot volta sozinho |
| Bots listam os canais antigos depois de um novo começo | Os volumes foram preservados | `docker compose down -v` |
| Mudança em `server/database/database.sql` não aparece | A tabela já existe no volume | `docker compose down -v` |

## Organização

| Pasta | Conteúdo |
|---|---|
| `broker/` | Proxy `ROUTER`/`DEALER` |
| `server/src/resources/` | Laço de atendimento e rotas das operações |
| `server/src/schemas/` | Validação do formato do pedido |
| `server/src/controllers/` | Regras e decisão de gravar |
| `server/src/repositories/` | Único lugar com SQL |
| `server/src/connectors/` | Único lugar que conhece ZeroMQ e MessagePack |
| `server/database/` | Schema do banco |
| `bot/src/controllers/` | Comportamento do bot |
| `bot/src/connectors/` | Único lugar que conhece ZeroMQ e MessagePack |
| `tests/` | Suíte black-box |

## Glossário

| Termo | Nome no código | Não confundir com |
|---|---|---|
| Bot | `bot` | Servidor; o bot é o usuário do sistema |
| Usuário | `username`, `sender` no pedido | `sender` na resposta, que é o nome do servidor |
| Canal | `channel` | Conexão de rede |
| Login | `login` | Sessão; não existe sessão nesta parte |
| Pedido | `RequestMessage` | Resposta |
| Resposta | `ResponseMessage` | Pedido |
| Recusa | `BbsError` | Timeout, que é falta de resposta |

## Entregas

Cada parte é desenvolvida em uma branch própria.

| Parte | Branch | Conteúdo |
|---|---|---|
| 1 | `parte-1` | Login, criação e listagem de canais, persistência |
