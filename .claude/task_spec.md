# task_spec.md — como preencher a spec de uma tarefa

Guia de preenchimento do template em
[`docs/specs/_template/SPEC.md`](../docs/specs/_template/SPEC.md).
Exemplo completo: [`docs/specs/1234-cadastro-de-produtos/`](../docs/specs/1234-cadastro-de-produtos/SPEC.md).

Este documento é o par do [`base_spec.md`](base_spec.md):

| | Responde | Quem preenche | Quando |
|---|---|---|---|
| `task_spec.md` (aqui) | **o que** construir | P.O. + Tech Lead + dev | no refinamento, antes da sprint |
| `base_spec.md` | **como** construir | quem implementa (pessoa ou IA) | ao codar |

Uma spec bem preenchida faz a implementação virar transcrição. Uma spec vaga
transfere a decisão de produto para quem está codando — que é o pior lugar
possível para ela ser tomada, porque é o único onde ninguém percebe que uma
decisão foi tomada.

---

## Regra geral

**Se um campo não puder ser respondido no refinamento, ele vira dúvida na seção
9 — não vira "a gente vê depois".** "Depois" significa que a decisão será tomada
por quem estiver implementando, às 3 da tarde, sozinho, sem o P.O. na sala.

---

## Campo a campo

### 1. Identificação
Mecânico, mas o campo **Depende de** é o que evita a tarefa entrar na sprint e
travar no segundo dia. Preencha mesmo que seja "nada".

### 2. Contexto e objetivo
O bloco que mais economiza tempo depois, porque é o único que explica **por quê**.

- ✅ "O catálogo é mantido numa planilha; dois vendedores já cadastraram o mesmo item com códigos diferentes."
- ❌ "Precisamos de um CRUD de produtos." — isso é a solução, não o problema.

Se o contexto não couber em três frases, provavelmente são duas tarefas.

### 3. Escopo
Itens verificáveis. Cada item deve permitir responder "está pronto?" com sim ou não.

- ✅ "Listar produtos com paginação"
- ❌ "Melhorar a performance da listagem" — melhorar quanto? de quanto para quanto?

### 4. Fora de escopo
**O campo mais subestimado do template.** Ele existe por dois motivos:

1. corta scope creep na revisão do PR ("mas eu achei que também ia ter...");
2. impede que quem implementa — especialmente uma IA — resolva "de brinde" algo
   que o P.O. decidiu não fazer agora.

Liste o que foi **discutido e recusado**, não tudo que existe no universo. Se
possível, diga para onde foi: "Categorias — entra na #1240".

### 5. Regras de negócio
Cada linha vira uma regra em `.rules/<modulo>/RULES.md` durante a implementação.
Escreva no presente, afirmativa, sem "deveria" ou "idealmente".

- ✅ "SKU é único no sistema"
- ❌ "O sistema deveria evitar SKUs repetidos, se possível"

O ID definitivo (`RN-PRODUCTS-001`) é atribuído na implementação — na spec basta
numerar 1, 2, 3.

**Toda regra precisa de uma resposta a "se violada"**, com status HTTP. Se a
resposta não estiver clara, é dúvida para o P.O., não escolha do dev. A tabela
de status codes está na Etapa 3 do `base_spec.md`.

### 6. Contrato da API
Preencha com **JSON de exemplo real**, não com descrição de campo. Um JSON
elimina ambiguidade que um parágrafo não elimina:

- ✅ `"price": "199.90"` — deixa claro que é string decimal, não float
- ❌ "o preço do produto" — string? número? centavos? com moeda?

Liste **todos** os erros possíveis com o `code`. Cada erro listado aqui vira um
teste obrigatório (é item da Definition of Done do `base_spec.md`). Um erro não
listado é um erro que ninguém vai testar.

Este é o bloco a validar com quem consome (front, mobile, integração) **antes**
da sprint. Contrato descoberto na integração custa uma sprint inteira.

### 7. Estrutura de banco
Três perguntas que precisam de resposta explícita:

1. **A tabela já existe em produção com dados?** Se sim, coluna `NOT NULL` nova
   precisa de `server_default` ou backfill em três passos.
2. **O que acontece no delete?** Apaga de verdade, ou desativa? Se há FK, qual o
   `ondelete`?
3. **Como fica o `downgrade`?** Migration sem rollback é migration que trava o deploy.

Não repita `id`, `created_at` e `updated_at` como se fossem decisão: vêm do
`TimestampMixin`.

### 8. Critérios de aceite
Gherkin porque o P.O. valida sem ler código e o dev transforma em teste quase 1:1.

Regra de cobertura: **um cenário para o caminho feliz e um para cada erro da
seção 6.** Se a seção 6 lista 401, 409 e 422, faltam cenários se houver menos
de quatro.

O "Então" precisa ser observável de fora:

- ✅ "Então recebo status 409 com code SKU_ALREADY_EXISTS"
- ❌ "Então o sistema trata o erro adequadamente"

Inclua o efeito colateral quando ele importa: "E nenhum produto novo é criado",
"E o produto continua no banco com is_active = false".

### 9. Dúvidas e decisões
Dúvida tem **responsável e prazo** — sem isso ela não é resolvida, é adiada.

Em decisões, o campo que importa é o **por quê**. Daqui a seis meses alguém vai
olhar `DELETE` que não apaga e achar que foi bug. A linha "pedido já emitido
referencia o produto; apagar quebraria o histórico" evita que essa pessoa
"conserte".

### 10. Definition of Ready
Checklist para a tarefa entrar em sprint. Se algum item não estiver marcado, a
tarefa volta para o refinamento — não entra "com ressalva".

---

## `TODO.md`: as pendências técnicas

Arquivo separado, na mesma pasta, porque tem ciclo de vida diferente: o `SPEC.md`
congela no refinamento, o `TODO.md` cresce **durante** a implementação.

Registre o item **no momento em que decide adiar**, não no fim da sprint — no fim
da sprint ninguém lembra do porquê, e é o porquê que dá valor ao registro.

Três perguntas que todo item responde:

| Pergunta | Por que importa |
|---|---|
| **Por que ficou de fora?** | quem lê no futuro precisa saber se a razão ainda vale |
| **Qual o impacto de continuar assim?** | separa "seria bom" de "vai doer em 6 meses" |
| **Onde está?** | sem o arquivo, ninguém acha |

Item resolvido **move para a seção "Resolvidas"**, não é apagado. O histórico é
o que impede a equipe de rediscutir a mesma coisa daqui a um ano.

Ao começar uma tarefa nova, **leia o `TODO.md` das pastas da mesma área**: pode
haver pendência que se resolve de graça dentro do escopo que você já vai tocar.
Isso é item da Definition of Ready.

---

## Fluxo completo

```
refinamento (P.O. + TL)
   ↓ cp -r docs/specs/_template docs/specs/1234-cadastro-de-produtos
   ↓ preenche SPEC.md
   ↓ Definition of Ready toda marcada
Azure DevOps: cola na descrição do work item #1234
   ↓
commit da pasta docs/specs/1234-*/ (revisada no PR como código)
   ↓
implementação: "implemente a spec docs/specs/1234-cadastro-de-produtos/SPEC.md"
   ↓ regras da seção 5  → .rules/<modulo>/RULES.md com IDs
   ↓ contrato da seção 6 → formulário do base_spec.md
   ↓ cenários da seção 8 → testes
   ↓ o que foi adiado    → TODO.md
```
