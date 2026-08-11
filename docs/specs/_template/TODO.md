# Pendências técnicas — [ID] [Título da tarefa]

O que ficou **conscientemente por fazer** nesta tarefa. Quem pegar esta área no
futuro começa lendo daqui: se um item aqui couber no escopo da nova tarefa, já
resolve junto.

Isto **não** é lista de bug e **não** é backlog de produto. É débito técnico
assumido: algo que a equipe sabia que precisaria, decidiu não fazer agora, e
registrou o motivo para a decisão não se perder.

## Como preencher

- Registre no momento em que a decisão de adiar é tomada — não no fim da sprint.
- Todo item precisa do **porquê ficou de fora**. Sem isso, quem lê no futuro não
  sabe se ainda faz sentido.
- Se o item virar work item no Azure DevOps, anote o número e mantenha o link.
- Item resolvido não é apagado: move para a seção "Resolvidas", com data. O
  histórico é o que impede a equipe de rediscutir a mesma coisa.

## Formato

```markdown
### PT-01 — [título curto]
**O quê:** o que falta fazer, em uma frase.
**Por que ficou de fora:** prazo / dependência / decisão consciente / faltou informação.
**Onde:** `app/modules/<modulo>/<arquivo>.py:<linha>` ou a área afetada.
**Impacto se continuar assim:** o que dói (performance, manutenção, risco, UX).
**Esforço estimado:** baixo / médio / alto.
**Work item:** #____ (ou "não criado")
```

---

## Abertas

### PT-01 — [título]
**O quê:**
**Por que ficou de fora:**
**Onde:**
**Impacto se continuar assim:**
**Esforço estimado:**
**Work item:**

---

## Resolvidas

| ID | Título | Resolvida em | Onde |
|---|---|---|---|
| | | | |
