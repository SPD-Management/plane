# Camada de extensão SPD (`plane.spd`)

Este fork (`SPD-Management/plane`) é sincronizado com o upstream `makeplane/plane`. Para que o sync
não gere conflitos, **toda customização da Speedio vive em arquivos novos**, agrupados no Django app
`plane.spd`, e é ativada por variáveis de ambiente. Nenhum arquivo do upstream precisa ser editado.

```
apps/api/plane/spd/                 Django app "plane.spd" (label: spd)
  apps.py                           SpdConfig.ready() carrega os plugins listados em SPD_PLUGINS
  conf.py                           leitura das envs SPD_* (com defaults)
  models.py + migrations/           tabelas próprias (prefixo spd_)
  llm.py                            adapter LLM (reaproveita LLM_* do god-mode/env)
  bot.py                            usuário bot que assina as ações automáticas
  plugins/<nome>/                   um plugin = um pacote com register()
  management/commands/              comandos spd_*
  tests/                            pytest (marker unit)
apps/api/plane/settings/spd*.py     settings que ligam o app: prod / local / test
docker-compose.spd.yml              overlay p/ dev local
```

## Ativação

O app só entra em `INSTALLED_APPS` quando o `DJANGO_SETTINGS_MODULE` aponta para um dos settings SPD:

| Ambiente       | `DJANGO_SETTINGS_MODULE`   | Observação                                                                   |
| -------------- | -------------------------- | ---------------------------------------------------------------------------- |
| Produção (k8s) | `plane.settings.spd`       | definir em api, worker, beat-worker e migrator                               |
| Dev local      | `plane.settings.spd_local` | `docker compose -f docker-compose-local.yml -f docker-compose.spd.yml up -d` |
| Testes         | `plane.settings.spd_test`  | `pytest --ds=plane.settings.spd_test plane/spd/tests`                        |

Isso funciona porque `manage.py`, `wsgi.py`, `asgi.py` e `celery.py` usam `os.environ.setdefault`, e o
`Dockerfile.api` copia `plane/` inteiro — a pasta `plane/spd` entra na imagem sem mudanças no build.

Variáveis gerais:

| Var           | Default        | Uso                                   |
| ------------- | -------------- | ------------------------------------- |
| `SPD_PLUGINS` | `ticket_guard` | plugins ativos, separados por vírgula |

## Plugin `ticket_guard`

Revisa com IA os work items dos projetos configurados e sinaliza os que não seguem o formato de ticket.

- **Gatilho**: `post_save` em `Issue` (cobre app web, API v1 e intake). Saves que só tocam
  `updated_at`/estado/prioridade são ignorados; só `name`/`description_*` disparam revisão.
- **Debounce**: cada save grava um token no Redis e agenda a task Celery `review_ticket` com
  `countdown=SPD_TICKET_GUARD_DEBOUNCE_SECONDS`; só a execução com o token mais recente roda.
- **Dedupe**: hash de título+descrição gravado em `spd_ticket_reviews`; conteúdo igual não chama a IA.
- **Resultado**: como o bot "Ticket Guard" (usuário `is_bot`, invisível nas listas de membros):
  - inválido → label `SPD_TICKET_GUARD_LABEL` + **um** comentário (upsert) com problemas e sugestão,
    com notificação in-app para criador/inscritos;
  - válido → remove a label e, se já havia comentário, troca para "✅ formato esperado".
- **Regras**: `plugins/ticket_guard/rules/default.md` (pt-BR, template "misto": bug ou solicitação).
  Para regras específicas de um projeto, crie `rules/<IDENTIFIER>.md` (ex.: `rules/SUPORTE.md`).
- **LLM**: usa `get_llm_config()` do core, ou seja, as mesmas chaves `LLM_PROVIDER`, `LLM_API_KEY`,
  `LLM_MODEL`, `LLM_BASE_URL` do god-mode › AI (Z.AI, OpenAI, qualquer endpoint compatível).
- **Falhas**: LLM indisponível → log, nada é escrito no ticket, e a próxima edição tenta de novo
  (a task tem 2 retries com backoff).

| Var                                 | Default               | Uso                                                         |
| ----------------------------------- | --------------------- | ----------------------------------------------------------- |
| `SPD_TICKET_GUARD_PROJECTS`         | vazio (**desligado**) | identificadores dos projetos, ex. `SUPORTE` ou `SUPORTE,CS` |
| `SPD_TICKET_GUARD_LABEL`            | `formato-invalido`    | nome da label                                               |
| `SPD_TICKET_GUARD_DEBOUNCE_SECONDS` | `20`                  | espera após a última edição                                 |
| `SPD_TICKET_GUARD_MIN_SCORE`        | `70`                  | pontuação mínima para considerar válido                     |

Reavaliar manualmente (dentro do container `api`/`worker`):

```bash
python manage.py spd_ticket_guard_review SUPORTE-12 --force
python manage.py spd_ticket_guard_review <uuid> --ignore-project-filter
```

## Como criar um novo plugin

1. Crie `apps/api/plane/spd/plugins/<nome>/__init__.py` com uma função `register()`.
   É nela que você conecta signals, registra hooks etc. Ela roda uma vez, em `AppConfig.ready()`.
2. Tasks Celery: qualquer `@shared_task` importada em `plane/spd/tasks.py` é descoberta
   automaticamente (`autodiscover_tasks`). Re-exporte a task do plugin lá.
3. Models: declare em `plane/spd/models.py` (ou num módulo importado por ele) com `db_table = "spd_..."`
   e gere a migration **só do app spd**:

   ```bash
   docker compose -f docker-compose-test.yml run --rm api-tests \
     python manage.py makemigrations spd --settings=plane.settings.spd_test
   ```

   Se a migration depender de tabelas do core, aponte a dependência para a última migration do
   upstream (`plane/db/migrations/`), nunca para uma migration criada no fork.

4. Rotas HTTP: crie `plane/spd/urls.py` com `urlpatterns = [path("api/spd/...", ...)] + plane.urls.urlpatterns`
   e defina `ROOT_URLCONF = "plane.spd.urls"` nos settings `spd*.py`.
5. Config editável no god-mode: use `plane/utils/instance_config_variables/extended.py`
   (lista vazia criada pelo upstream justamente para isso).
6. Frontend: os pontos de extensão do upstream são os arquivos `extended.*`
   (`apps/web/app/routes/extended.ts`, `apps/web/core/components/**/extended.tsx`,
   `apps/admin/providers/extended.tsx`, ...). Prefira colocar código novo em pastas próprias e
   importá-lo a partir desses stubs.
7. Ative o plugin em `SPD_PLUGINS` e documente as envs aqui.

Testes: `plane/spd/tests/`, marker `unit`:

```bash
docker compose -f docker-compose-test.yml run --rm api-tests \
  pytest --ds=plane.settings.spd_test plane/spd/tests -m unit -vv
```

## Regra de ouro

- Não edite arquivos existentes do upstream. Se for inevitável, mantenha a mudança em uma linha
  (ex.: um `import` no fim de um settings) e registre aqui o motivo.
- Migrations só no app `spd`. Migrations no app `db` conflitam com o upstream a cada release.

### Pontos de conflito já existentes no fork (para o próximo sync)

- `ce574ae83` (defaults pt-BR/America/Sao*Paulo) criou `plane/db/migrations/0123*\*` e alterou models
  do core. Ao sincronizar, renumere/refaça essa migration depois das novas do upstream.
- `37833ac3c` (Z.AI / OpenAI-compatible) adicionou `LLM_BASE_URL` em
  `plane/utils/instance_config_variables/core.py` em vez de `extended.py`, e alterou
  `plane/app/views/external/base.py`. Se o upstream mexer nesses arquivos, reaplicar a diff.
