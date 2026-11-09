# Distributed BBS

Sistema de troca de mensagens instantâneas inspirado no BBS e no IRC. Bots publicam em canais públicos, todas as interações ficam gravadas em disco e os servidores podem entrar e sair sem parar o serviço.

Projeto individual da disciplina de Sistemas Distribuídos (Ciência da Computação, FEI), de Bruno Budano Mello.

## Stack

| Parte | Tecnologia |
|---|---|
| Servidor | Python |
| Bots | TypeScript |
| Troca de mensagens | ZeroMQ |
| Execução | Docker Compose |

## Subindo

Precisa só de **Docker** (com o Docker Compose v2). Na raiz do repositório:

```bash
docker compose up --build
```

Nenhuma interação é necessária: os bots começam a trabalhar sozinhos, e clientes e servidores mostram no terminal cada mensagem enviada ou recebida.

## Entregas

Cada parte é desenvolvida em uma branch própria.

| Parte | Branch | Status |
|---|---|---|
| 1 | `parte-1` | Em desenvolvimento |
