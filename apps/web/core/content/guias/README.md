# Guias

Páginas estáticas do menu de ajuda (o botão "?" no canto superior direito).

Elas usam exatamente a mesma tipografia e o mesmo layout das Páginas do Atlas, mas o conteúdo
vem destes arquivos HTML, e não do banco de dados.

## Editar o texto de uma página

Abra o `.html` correspondente e edite. É HTML simples:

```html
<h2>Título de seção</h2>
<p>Um parágrafo com <strong>negrito</strong>, <em>itálico</em> e <a href="https://exemplo.com">link</a>.</p>
<ul>
  <li>Item de lista</li>
</ul>
<ol>
  <li>Item numerado</li>
</ol>
<blockquote><p>Citação</p></blockquote>
<pre><code>bloco de código</code></pre>
<img src="https://exemplo.com/imagem.png" alt="descrição" />
```

O título grande no topo da página **não** vem do arquivo: ele é o `label` definido em
`apps/web/core/components/guias/registry.ts`.

A mudança aparece na hora com `pnpm dev`; em produção é preciso rebuildar o `apps/web`.

## Adicionar uma página nova

1. Crie o arquivo de conteúdo aqui, por exemplo `minha-pagina.html`.
2. Em `apps/web/core/components/guias/registry.ts`, importe o arquivo e acrescente uma entrada
   em `GUIAS` com `slug`, `label` e `content`.

A ordem das entradas em `GUIAS` é a ordem em que elas aparecem no menu de ajuda, e a rota
`/:workspaceSlug/guias/:slug` passa a funcionar automaticamente.

## Remover uma página

Apague a entrada correspondente em `GUIAS` (e, se quiser, o arquivo `.html`).
