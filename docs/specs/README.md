# `docs/specs/` — specs de tarefa

Cada tarefa refinada com P.O. e Tech Lead vira **uma pasta** aqui, com a spec e
as pendências técnicas daquela entrega.

```
docs/specs/
├── README.md                      # este arquivo
├── _template/                     # copie esta pasta para criar uma spec nova
│   ├── SPEC.md
│   └── TODO.md
└── 1234-cadastro-de-produtos/     # exemplo de referência, preenchido
    ├── SPEC.md
    └── TODO.md
```

| Arquivo | Conteúdo |
|---|---|
| `SPEC.md` | o que construir: contexto, escopo, regras, contrato, banco, critérios de aceite |
| `TODO.md` | o que ficou conscientemente por fazer, para quem pegar a área no futuro |

Nome da pasta: `<ID do work item>-<slug>` — `1234-cadastro-de-produtos`.
O ID na frente faz a pasta ordenar por tarefa e liga direto ao Azure DevOps.

## Fluxo

```
1. refinamento com P.O. + TL
        ↓  preenche SPEC.md a partir de _template/
2. cola o conteúdo na descrição do work item no Azure DevOps
        ↓
3. commita a pasta em docs/specs/<ID>-<slug>/
        ↓  (a spec entra no PR e é revisada como código)
4. "implemente a spec docs/specs/1234-cadastro-de-produtos/SPEC.md"
        ↓
5. durante a implementação: o que for adiado vai para TODO.md
```

O Azure DevOps continua sendo a fonte da verdade para **status e planejamento**.
O repositório guarda o **conteúdo técnico** versionado junto com o código — quem
abrir o projeto daqui a um ano entende por que cada decisão foi tomada sem
precisar de acesso ao board.

Se a spec mudar depois do refinamento, atualize os dois lugares no mesmo PR.

## Criando uma spec nova

```bash
cp -r docs/specs/_template docs/specs/1245-listagem-de-pedidos
```

Depois preencha o `SPEC.md`. Como preencher cada campo, com exemplos de resposta
boa e ruim: [`.claude/task_spec.md`](../../.claude/task_spec.md).

## Para quem for implementar

A spec **não** substitui o processo de implementação. Ela diz *o que* construir;
[`.claude/base_spec.md`](../../.claude/base_spec.md) diz *como*, e a skill
`new-module` é o roteiro. A ordem é:

1. Ler o `SPEC.md` da tarefa
2. Ler o `TODO.md` da mesma pasta e das pastas relacionadas — pode haver
   pendência que se resolve de graça dentro desta tarefa
3. Transcrever a seção 5 (regras de negócio) para `.rules/<modulo>/RULES.md`
   com IDs definitivos (`RN-PRODUCTS-001`)
4. Seguir o `base_spec.md` a partir do formulário de rota
5. Transformar cada cenário da seção 8 em teste
