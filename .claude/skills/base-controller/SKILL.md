---
name: base-controller
description: Como escrever a camada de controller (orquestração entre rota e service) deste projeto. Use ao ligar uma rota ao service e converter model em schema de saída em app/modules/<modulo>/controller.py.
---

# Camada: controller

`← router | → service.py`

O controller é uma camada **fina**. Ele monta o service, chama um método e
converte o model no schema de saída. Se ele está crescendo, a lógica está no
lugar errado.

## Arquivos desta pasta
- `example.py` — o controller de `Product`, completo e comentado
- `template.py.tpl` — o mesmo arquivo com `{{Entity}}` para copiar

## O que MUST estar aqui
- `def __init__(self, session: AsyncSession)` que monta `Service(Repository(session))`
- Métodos que devolvem **schema** (`{Entity}Read`, `Page[{Entity}Read]`)
- `{Entity}Read.model_validate(obj)` para converter model → schema
- Montagem do `Page[...]` nas listagens

## O que NEVER pode aparecer
- `if` de regra de negócio (`if produto.preco > limite`) — isso é service
- `select()`, sessão usada diretamente — isso é repository
- `raise HTTPException` — deixe o erro de domínio subir até o handler global

## Por que existe uma camada só para isso
Para o `router.py` ficar sendo **apenas** a declaração do contrato HTTP, legível
como documentação, e para a montagem do grafo de dependências
(`Service(Repository(session))`) ficar num lugar só. Quando o service ganhar uma
segunda dependência, só o controller muda.

## Exceção conhecida
`app/modules/health/controller.py` escolhe o status code na mão (200 ou 503),
porque "degradado" é uma resposta com corpo útil, não um erro de domínio. Fora
esse caso, quem define status code é o `router.py`.

## Erros mais comuns
1. Devolver o model do SQLAlchemy direto — sempre converta com `model_validate`.
2. Colocar `if` de negócio aqui porque "é só uma linha" — ela vira dez.
3. Esquecer `model_config = ConfigDict(from_attributes=True)` no schema `Read`, e então `model_validate` falha.
4. Montar `Page` sem o `total` vindo do service.
5. Criar o repository dentro de cada método em vez de uma vez no `__init__`.

## Depois de mexer aqui
Vá para a skill `base-router`.
