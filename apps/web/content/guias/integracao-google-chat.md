A ideia é simples: quando alguma coisa acontece no Atlas — um item de trabalho é criado, muda de status, ganha um comentário — um recado aparece no espaço do Google Chat da equipe. Este guia mostra o caminho inteiro, do webhook do Chat até o Atlas mandando os eventos.

## Antes de começar

- Uma conta **Google Workspace** (Business ou Enterprise). Conta pessoal `@gmail.com` não cria webhook.
- Ser membro de um **espaço** do Google Chat. Webhook não funciona em conversa direta, só em espaço.
- Ser **administrador do workspace** no Atlas, que é quem enxerga a tela de webhooks.

## Passo 1 — Crie o webhook no Google Chat

1. Abra o [Google Chat](https://chat.google.com) no navegador e entre no espaço que vai receber os avisos.
2. Clique no **nome do espaço**, no topo, para abrir o menu.
3. Escolha **Apps e integrações**.
4. Clique em **Adicionar webhooks**.
5. Dê um nome — `Atlas` — e, se quiser um ícone, cole a URL de uma imagem no campo **URL do avatar**.
6. Clique em **Salvar**, depois em **Mais** → **Copiar link**.

A URL copiada tem esta cara:

```
https://chat.googleapis.com/v1/spaces/AAAA1111bbb/messages?key=CHAVE&token=TOKEN
```

**Essa URL é a senha do espaço.** Quem tiver ela posta mensagens no espaço como se fosse o app. Não cole em item de trabalho, em página do Atlas nem em commit. Se vazar, apague o webhook na mesma tela e crie outro.

## Passo 2 — Teste o webhook

Antes de envolver o Atlas, confirme que a URL funciona. No terminal:

```bash
curl -X POST "URL_DO_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"text": "Oi, aqui é o Atlas."}'
```

A mensagem tem que aparecer no espaço na hora. O corpo aceita formatação simples:

- `*negrito*`
- `_itálico_`
- `~riscado~`
- `` `monoespaçado` ``
- `<https://exemplo.com|texto do link>`
- `<users/all>` para notificar todo mundo do espaço

O Chat aceita **1 requisição por segundo** por espaço, somando todos os webhooks dele. Vale lembrar disso antes de mandar avisar cada mudança de campo.

## Passo 3 — Entenda o que o Atlas manda

Em **Configurações do workspace → Webhooks** você cadastra uma URL e escolhe os eventos: **projetos**, **itens de trabalho**, **módulos**, **ciclos** e **comentários**. A cada evento o Atlas faz um `POST` com este corpo:

```json
{
  "event": "issue",
  "action": "create",
  "webhook_id": "...",
  "workspace_id": "...",
  "workspace_slug": "speedio",
  "data": { "id": "...", "name": "...", "state": "..." },
  "activity": { "actor": {}, "field": "state", "old_value": "...", "new_value": "..." }
}
```

E manda junto os cabeçalhos:

- `X-Plane-Event` — o tipo do evento (`issue`, `project`, ...)
- `X-Plane-Delivery` — um identificador único da entrega
- `X-Plane-Signature` — HMAC-SHA256 do corpo, assinado com a chave secreta (`plane_wh_...`) que aparece **uma única vez** quando o webhook é criado

**Aqui está a pegadinha:** não dá para apontar o webhook do Atlas direto para a URL do Google Chat. O Chat só aceita um corpo com `text` ou `cardsV2`; recebendo o JSON do Atlas ele devolve erro 400. Falta alguém no meio para traduzir — é o passo 4.

## Passo 4 — O tradutor no meio

É um serviço minúsculo: recebe o evento do Atlas, confere a assinatura, monta a frase e repassa ao Chat. Pode rodar em Cloud Run, Cloud Functions, n8n, Make — qualquer lugar com uma URL pública em HTTPS (o Atlas recusa `localhost`).

Um exemplo completo, em Python com Flask:

```python
import hashlib
import hmac
import os

import requests
from flask import Flask, request

app = Flask(__name__)

PLANE_SECRET = os.environ["PLANE_WEBHOOK_SECRET"]   # plane_wh_...
CHAT_WEBHOOK = os.environ["GOOGLE_CHAT_WEBHOOK"]    # https://chat.googleapis.com/v1/spaces/...
ATLAS_URL = "https://plane.speedio.com.br"


@app.post("/atlas")
def atlas():
    # 1. confere que o recado veio mesmo do Atlas
    assinatura = request.headers.get("X-Plane-Signature", "")
    esperada = hmac.new(
        PLANE_SECRET.encode(),
        request.get_data(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(assinatura, esperada):
        return "assinatura inválida", 401

    corpo = request.get_json()
    if corpo.get("event") != "issue":
        return "", 204

    dados = corpo.get("data") or {}
    acao = {"create": "criou", "update": "atualizou", "delete": "apagou"}.get(
        corpo.get("action"), corpo.get("action")
    )
    quem = ((corpo.get("activity") or {}).get("actor") or {}).get("display_name", "alguém")
    titulo = dados.get("name", "sem título")
    link = f"{ATLAS_URL}/{corpo['workspace_slug']}/browse/{dados.get('sequence_id', '')}/"

    texto = f"*{quem}* {acao} um item de trabalho: <{link}|{titulo}>"

    # 2. repassa para o Google Chat
    requests.post(CHAT_WEBHOOK, json={"text": texto}, timeout=10)
    return "", 204
```

Publique isso, pegue a URL pública e cadastre em **Configurações do workspace → Webhooks → Adicionar webhook**, marcando só os eventos que interessam. Guarde a chave secreta na variável `PLANE_WEBHOOK_SECRET` — ela é o que garante que o `POST` veio mesmo do Atlas, e não de alguém que descobriu a URL.

## Passo 5 — Deixando mais bonito com um card

Em vez de `text`, o Chat aceita `cardsV2`, que rende um bloco com título e campos:

```json
{
  "cardsV2": [
    {
      "cardId": "atlas-item",
      "card": {
        "header": { "title": "ATLAS-1234", "subtitle": "Item de trabalho atualizado" },
        "sections": [
          {
            "widgets": [
              { "textParagraph": { "text": "<b>Status:</b> Em andamento" } },
              { "textParagraph": { "text": "<b>Responsável:</b> Maria" } }
            ]
          }
        ]
      }
    }
  ]
}
```

Dentro do card o texto aceita HTML simples: `<b>`, `<i>`, `<a>`, `<br>` e `<code>`.

Para agrupar as mensagens de um mesmo item numa conversa só, mande também um `thread` com uma chave estável — o código do item serve bem — e acrescente o parâmetro na URL:

```
POST URL_DO_WEBHOOK&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD

{
  "text": "Status mudou para Concluído",
  "thread": { "threadKey": "ATLAS-1234" }
}
```

## Passo 6 — Sem servidor: um resumo por dia pela API

Se montar o serviço do passo 4 for demais para o caso de vocês, dá para inverter: em vez de o Atlas avisar, um script pergunta ao Atlas e posta um resumo. Roda num cron, não precisa de URL pública e usa a mesma API descrita em _Como integrar a IA_.

```python
import os
import requests

ATLAS = "https://plane.speedio.com.br/api/v1"
HEADERS = {"X-API-Key": os.environ["PLANE_API_KEY"]}
PROJETO = os.environ["PROJECT_ID"]

itens = requests.get(
    f"{ATLAS}/workspaces/speedio/projects/{PROJETO}/issues/",
    headers=HEADERS,
    timeout=30,
).json()["results"]

linhas = [f"• {i['name']}" for i in itens[:10]]
texto = "*Itens de trabalho do projeto hoje*\n" + "\n".join(linhas)

requests.post(os.environ["GOOGLE_CHAT_WEBHOOK"], json={"text": texto}, timeout=10)
```

O token da API sai de **Configurações → Perfil → Tokens de API** e age em seu nome, com as suas permissões. As listagens vêm paginadas: use `next_cursor` quando precisar de mais de uma página.

## Quando não funciona

- **O Chat responde 400.** O corpo não tem `text` nem `cardsV2` — quase sempre é o webhook do Atlas apontado direto para o Chat, sem o tradutor do passo 4.
- **O Chat responde 404.** A URL do webhook foi apagada ou o espaço não existe mais. Gere outra.
- **Chegam mensagens demais.** Filtre por `event` e por `activity.field` no tradutor, e marque menos eventos na tela de webhooks do Atlas. Lembre do limite de 1 mensagem por segundo.
- **O Atlas recusa a URL.** Ele só aceita `http`/`https` e bloqueia `localhost` e `127.0.0.1`. Para testar da sua máquina, exponha com um túnel.
- **A assinatura nunca bate.** Assine os _bytes crus_ do corpo (`request.get_data()`), não o JSON reserializado — qualquer diferença de espaço muda o hash.
