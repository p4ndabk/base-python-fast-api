# Pendências técnicas — 1234 Cadastro de produtos

> **Exemplo de referência**, junto com a spec fictícia desta pasta.

O que ficou **conscientemente por fazer** nesta tarefa. Quem pegar esta área no
futuro começa lendo daqui: se um item couber no escopo da nova tarefa, já
resolve junto.

## Abertas

### PT-01 — Busca por nome sem índice de texto
**O quê:** `GET /products` filtra só por `is_active`. Buscar por nome parcial
(`ILIKE '%teclado%'`) não usa o índice B-tree atual e vai degradar quando a
tabela crescer.
**Por que ficou de fora:** busca textual não estava no escopo da #1234; o P.O.
preferiu entregar o CRUD primeiro.
**Onde:** `app/modules/products/repository.py` (método `list`)
**Impacto se continuar assim:** com ~50 mil produtos a listagem filtrada fica
lenta. Hoje são ~800, então não dói ainda.
**Esforço estimado:** médio (índice GIN + `pg_trgm`, ou migrar para busca full-text)
**Work item:** não criado — abrir quando a busca entrar no escopo

### PT-02 — Preço sem histórico de alteração
**O quê:** alterar o preço sobrescreve o valor anterior. Não há como saber por
quanto o produto foi vendido no mês passado.
**Por que ficou de fora:** exigiria uma tabela `product_price_history` e uma
decisão de produto sobre retenção; travaria a entrega.
**Onde:** `app/modules/products/service.py` (método `update`)
**Impacto se continuar assim:** relatório financeiro retroativo fica impossível;
quanto mais tempo passa, mais histórico se perde de forma irrecuperável.
**Esforço estimado:** alto
**Work item:** #1252

### PT-03 — Desativação não tem autoria
**O quê:** `is_active = false` não registra quem desativou nem quando.
`updated_at` diz quando, mas não quem.
**Por que ficou de fora:** auditoria será tratada de forma transversal, não por
módulo (discussão em aberto com o TL).
**Onde:** `app/modules/products/service.py` (método `deactivate`)
**Impacto se continuar assim:** sem rastro para investigar produto desativado
por engano.
**Esforço estimado:** baixo por módulo, médio se for transversal
**Work item:** não criado — depende da decisão sobre auditoria global

## Resolvidas

| ID | Título | Resolvida em | Onde |
|---|---|---|---|
| PT-00 | `price` estava como `Float` no primeiro rascunho | 2026-08-05 (na própria #1234) | `models.py` — trocado por `Numeric(10,2)` |
