A ideia desta página é usar IA no dia a dia de planejamento e de gestão de tarefas: escrever melhor um item de trabalho, resumir o que aconteceu num ciclo, abrir e atualizar tarefas sem sair da conversa com o seu agente.

## Parte 1 — A IA dentro da plataforma

### Passo 1 — Habilite a IA na instância

Um administrador da instância abre o painel de administração, vai em **IA** e cadastra o provedor e a chave de API que serão usados pela plataforma.

### Passo 2 — Use a IA dentro do produto

Com a IA habilitada, o assistente fica disponível no editor de páginas e na descrição dos itens de trabalho.

- Selecione um trecho de texto para pedir um ajuste.
- Peça um resumo do conteúdo da página.

### Passo 3 — Boas práticas

- Nunca cole credenciais ou dados sensíveis nos comandos.
- Revise sempre o texto gerado antes de publicar.

## Parte 2 — Conecte a sua IA aos seus projetos

A parte 1 é a IA _dentro_ do produto. Esta parte é o contrário: como fazer o seu agente de IA — Claude Code, Cursor, um script próprio — ler e escrever nos seus projetos, para que ele participe do planejamento e da gestão das tarefas. Há dois caminhos, e os dois usam o mesmo token.

- **API REST** — para scripts, automações e integrações.
- **MCP** — para o seu agente consultar e mexer nas tarefas em linguagem natural. É a opção recomendada.

### Passo 1 — Gere o seu token

Abra **Configurações → Perfil → Tokens de API** e crie um token. Ele aparece **uma única vez**, na hora da criação — copie e guarde num gerenciador de senhas.

O link direto:

```
https://plane.speedio.com.br/settings/profile/api-tokens/
```

O token é **pessoal e age como você**: tudo o que ele fizer aparece com o seu nome, e ele enxerga exatamente os projetos que você enxerga. Trate como senha.

### Passo 2 — Anote os seus dados de conexão

- **URL da instância** — `https://plane.speedio.com.br`
- **Slug do workspace** — `speedio`. É o pedaço da URL logo depois do domínio, como em `plane.speedio.com.br/speedio/projects/...`
- **Token** — o que você gerou no passo anterior, no formato `plane_api_...`

### Passo 3 — Opção A: API REST

A autenticação é pelo cabeçalho `X-API-Key` — não é `Authorization: Bearer`. A base de todas as chamadas é `https://plane.speedio.com.br/api/v1/`.

Teste rápido, listando os seus projetos:

```bash
curl -H "X-API-Key: SEU_TOKEN" \
  https://plane.speedio.com.br/api/v1/workspaces/speedio/projects/
```

Os endpoints mais usados:

- `GET /api/v1/workspaces/speedio/projects/` — lista os projetos
- `GET /api/v1/workspaces/speedio/projects/<project_id>/issues/` — itens de trabalho do projeto
- `POST /api/v1/workspaces/speedio/projects/<project_id>/issues/` — cria um item de trabalho
- `GET /api/v1/workspaces/speedio/issues/<IDENTIFICADOR>-<número>/` — busca um item pelo código que aparece na interface, como `VENDAS-1234`

Também existem rotas para ciclos, módulos, estados, etiquetas, membros, intake e anexos, no mesmo padrão.

As respostas de listagem vêm paginadas: o corpo traz `results` com os registros e `next_cursor` para pedir a página seguinte.

### Passo 4 — Opção B: MCP

O MCP é o jeito de dar ao seu agente acesso aos projetos sem você escrever chamada de API nenhuma. Você pede _"abra um item de trabalho no projeto Vendas"_ e ele resolve.

Instale o servidor. Ele é um pacote Python, distribuído pelo `uv`:

```bash
uv tool install plane-mcp-server
```

Depois registre no Claude Code, de dentro da pasta do seu projeto:

```bash
claude mcp add -s local plane \
  --env PLANE_API_KEY=SEU_TOKEN \
  --env PLANE_WORKSPACE_SLUG=speedio \
  --env PLANE_BASE_URL=https://plane.speedio.com.br \
  -- ~/.local/bin/plane-mcp-server stdio
```

Reinicie a sessão do agente e confira com `claude mcp list` — o servidor `plane` deve aparecer como conectado. Em outros clientes, como Cursor ou Claude Desktop, a ideia é a mesma: comando `plane-mcp-server stdio` e essas três variáveis de ambiente.

### Passo 5 — Três armadilhas

- **Não use `uvx plane-mcp-server` direto no comando do MCP.** Na primeira execução ele baixa dezenas de pacotes e estoura o limite de 30 segundos de conexão, e o servidor aparece como _failed to connect_. Instale antes com `uv tool install` e aponte para o binário, como no passo anterior.
- **Sempre defina o `PLANE_BASE_URL`.** Sem ele o servidor tenta falar com `api.plane.so`, que é o serviço na nuvem, e o seu token daqui não vale lá.
- **Não deixe o token dentro do repositório.** O `-s local` do comando acima guarda a configuração fora do projeto, justamente para o token não acabar num commit. Se ele vazar, revogue na mesma tela em que foi criado e gere outro — revogar é imediato.

### Passo 6 — O que dá para pedir

Com o MCP ligado, o agente enxerga projetos, itens de trabalho, ciclos, módulos, páginas, membros, comentários, anexos e apontamentos de hora. Alguns pedidos que ajudam no planejamento e na gestão das tarefas:

- "Liste os itens de trabalho em andamento no projeto CS."
- "Abra um bug no projeto Operações com o resumo desta conversa e me atribua."
- "O que entrou no ciclo atual de Vendas? O que ficou para trás?"
- "Quebre esta demanda em tarefas menores e crie cada uma no projeto Marketing."
- "Comente no VENDAS-1234 explicando o que foi corrigido."

Vale a mesma regra da parte 1: o agente age com as suas permissões e em nome do seu usuário. Confira o que ele propõe antes de deixar escrever.
