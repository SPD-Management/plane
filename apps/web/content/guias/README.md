# Guias

Páginas estáticas do menu de ajuda (o botão "?" no canto superior direito).

Elas usam exatamente a mesma tipografia e o mesmo layout das Páginas do Atlas, mas o conteúdo vem
destes arquivos Markdown, e não do banco de dados.

## Editar o texto de uma página

Abra o `.md` correspondente e edite. É Markdown comum, com as extensões do GitHub (tabelas, listas
de tarefas, `~~riscado~~`):

```markdown
## Título de seção

Um parágrafo com **negrito**, _itálico_, `código` e [link](https://exemplo.com).

- Item de lista
- Outro item

1. Item numerado
2. Outro item

> Citação

| Coluna | Outra |
| ------ | ----- |
| valor  | valor |

![descrição](https://exemplo.com/imagem.png)
```

Blocos de código levam três crases e, se quiser destaque de sintaxe no futuro, o nome da linguagem:

````markdown
```bash
curl https://exemplo.com
```
````

Duas coisas a saber:

- **O título grande no topo não vem do arquivo.** Ele é o `label` definido em
  `apps/web/core/components/guias/registry.ts`. Por isso os arquivos começam em `##`, e não em `#`.
- **HTML dentro do Markdown é ignorado**, de propósito. Escreva em Markdown mesmo.

A mudança aparece na hora com `pnpm dev`; para chegar em produção é preciso commitar e dar push na
`main`, que é o que dispara o build das imagens.

## Adicionar uma página nova

1. Crie o arquivo de conteúdo aqui, por exemplo `minha-pagina.md`.
2. Em `apps/web/core/components/guias/registry.ts`, importe o arquivo e acrescente uma entrada em
   `GUIAS` com `slug`, `label` e `content`.

A ordem das entradas em `GUIAS` é a ordem em que elas aparecem no menu de ajuda, e a rota
`/:workspaceSlug/guias/:slug` passa a funcionar automaticamente.

## Remover uma página

Apague a entrada correspondente em `GUIAS` (e, se quiser, o arquivo `.md`).
