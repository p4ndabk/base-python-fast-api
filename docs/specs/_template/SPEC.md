# [ID] — [Título da tarefa]

> Template de spec de tarefa. Copie a pasta `_template/` para
> `docs/specs/<ID>-<slug>/` e preencha. Como preencher cada campo:
> [`.claude/task_spec.md`](../../../.claude/task_spec.md).
>
> Remova este bloco de citação ao preencher.

## 1. Identificação

| Campo | Valor |
|---|---|
| **Work item (Azure DevOps)** | #____ — [link] |
| **Tipo** | Feature / User Story / Bug / Débito técnico |
| **Épico / Feature pai** | |
| **Módulo afetado** | `app/modules/____` |
| **P.O.** | |
| **Tech Lead** | |
| **Data do refinamento** | AAAA-MM-DD |
| **Depende de** | #____ (ou "nada") |

## 2. Contexto e objetivo

**Problema:** _o que está ruim hoje, na visão de quem usa._

**Objetivo:** _o que passa a ser possível quando esta tarefa estiver pronta._

**Quem usa:** _perfil/persona que consome esta funcionalidade._

## 3. Escopo — o que entra

- [ ] _item objetivo e verificável_
- [ ] _..._

## 4. Fora de escopo

_O que esta tarefa deliberadamente NÃO faz. Se não estiver aqui e nem no
escopo, é dúvida em aberto (seção 9), não é "pode fazer"._

- _..._
- _..._

## 5. Regras de negócio

Cada linha vira uma regra em `.rules/<modulo>/RULES.md` com ID definitivo
durante a implementação.

| # | Regra | Quando é avaliada | Se violada |
|---|---|---|---|
| 1 | _afirmativa, no presente_ | _criação / atualização / login..._ | _erro + status HTTP_ |
| 2 | | | |

**Regras globais que já se aplicam** (não repita, só confirme):
`_global/RULES.md` — timestamps UTC, e-mail normalizado, paginação máx. 100,
formato único de erro, segredo nunca sai na resposta.

## 6. Contrato da API

Uma sub-seção por rota. Repita o bloco quantas vezes for necessário.

### 6.1 `MÉTODO /caminho`

| Campo | Valor |
|---|---|
| **Autenticação** | pública / requer access token |
| **Status de sucesso** | 200 / 201 / 204 |

**Request**

```json
{
  "campo": "valor"
}
```

| Campo | Tipo | Obrigatório | Regra de formato |
|---|---|---|---|
| `campo` | string | sim | 2–255 caracteres |

**Response (sucesso)**

```json
{
  "id": "uuid",
  "campo": "valor",
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Erros**

| Status | Quando | `code` |
|---|---|---|
| 401 | sem token / token inválido | `UNAUTHORIZED` |
| 404 | recurso não existe | `NOT_FOUND` |
| 409 | duplicidade | `______` |
| 422 | payload fora do formato | `UNPROCESSABLE_ENTITY` |

## 7. Estrutura de banco

**Tabela:** `____`  · **Migration necessária:** sim / não

| Coluna | Tipo | Null | Índice | Observação |
|---|---|---|---|---|
| `id` | UUID (PK) | não | PK | vem do `TimestampMixin` |
| `created_at` | timestamptz | não | — | vem do `TimestampMixin` |
| `updated_at` | timestamptz | não | — | vem do `TimestampMixin` |
| | | | | |

**Relacionamentos:** _FK, cardinalidade, comportamento no delete._

**Dados existentes:** _a tabela já tem dados em produção? Coluna NOT NULL nova
precisa de default ou backfill? Como fica o `downgrade`?_

## 8. Critérios de aceite

Cada cenário vira ao menos um teste. Cobrir o caminho feliz **e** cada erro da
seção 6.

```gherkin
Cenário: [nome do caminho feliz]
  Dado que [estado inicial]
  Quando [ação]
  Então [resultado observável]
  E [efeito colateral verificável]

Cenário: [nome do erro]
  Dado que [estado que provoca o erro]
  Quando [ação]
  Então recebo status [código] com code "[CODE]"
```

## 9. Dúvidas em aberto e decisões

**Dúvidas** — a tarefa não entra em sprint com dúvida bloqueante em aberto.

| # | Dúvida | Responsável | Prazo | Status |
|---|---|---|---|---|
| 1 | | | | aberta / respondida |

**Decisões tomadas no refinamento** — registre o porquê, não só o quê.

| Decisão | Por quê | Quem decidiu |
|---|---|---|
| | | |

## 10. Definition of Ready

A tarefa só entra em sprint com todos marcados:

- [ ] Seções 1 a 8 preenchidas
- [ ] Nenhuma dúvida bloqueante em aberto (seção 9)
- [ ] Contrato da API validado com quem vai consumir (front/mobile/integração)
- [ ] Regras de negócio aprovadas pelo P.O.
- [ ] Impacto em dados existentes avaliado (seção 7)
- [ ] `TODO.md` da pasta revisado — há pendência técnica que deve entrar nesta tarefa?
