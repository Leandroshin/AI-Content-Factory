# Protocolo para LLMs locais e modelos auxiliares

Este arquivo permite que DeepSeek, OpenCode e outras LLMs menores adiantem trabalho sem alterar a arquitetura validada da AI Content Factory.

## Regra principal

Trabalhe apenas em documentos de proposta, pesquisa e prototipos isolados. O Codex revisara tudo antes de qualquer integracao ao produto real.

## Pode criar

- ideias em `docs/external_llm_inbox/deepseek/ideas/`;
- especificacoes de funcionarios em `docs/external_llm_inbox/deepseek/employees/`;
- especificacoes de departamentos em `docs/external_llm_inbox/deepseek/departments/`;
- pesquisas com fontes em `docs/external_llm_inbox/deepseek/research/`;
- briefings de clientes ficticios ou anonimizados em `docs/external_llm_inbox/deepseek/client_briefs/`;
- prototipos independentes em `prototypes/external_llm/`, sem substituir sites existentes.

Cada prototipo deve ficar em uma subpasta propria, nao pode importar o `core/` e deve conter um `README.md` com objetivo, como testar, limitacoes e status `PROTOTIPO ISOLADO - NAO INTEGRADO`.

Use os templates existentes de `docs/external_llm_inbox/` sempre que houver um equivalente.

## Nao pode alterar

- `core/`;
- `apps/factory_dashboard/`;
- `demo_*.py`;
- `scripts/`;
- `AGENTS.md`;
- `.openai/`;
- providers, adapters, dependencias, secrets ou arquivos de configuracao;
- sites existentes de Gilson, Sapataria, Extintores ou AI Content Factory;
- outputs gerados e credenciais.

Nao faça commit, push, deploy, instalacao de dependencia ou chamada paga. Nao copie codigo de terceiros sem registrar licenca e origem.

## Privacidade

- Nao registre CPF, CNPJ completo, telefone, endereco residencial, senha, token ou dados bancarios.
- Briefings reais devem usar nome comercial publico e dados anonimizados.
- Audios de clientes nao devem ser enviados a LLM web sem consentimento expresso.
- Separe claramente fatos encontrados, falas do cliente, inferencias e sugestoes.

## Qualidade minima de cada entrega

Todo arquivo deve informar:

1. objetivo;
2. problema observado;
3. evidencias e URLs das fontes;
4. fatos versus hipoteses;
5. proposta;
6. riscos e privacidade;
7. custo estimado;
8. dependencias externas;
9. o que precisa de aprovacao humana;
10. criterios para o Codex aceitar ou rejeitar a proposta.

## Encerramento obrigatorio

Ao terminar, a LLM deve criar ou atualizar `docs/external_llm_inbox/deepseek/INDEX.md` com uma linha por arquivo, resumo, status `PROPOSTA - NAO IMPLEMENTADA` e lista do que deseja que o Codex revise.

Para prototipos, use o status `PROTOTIPO ISOLADO - NAO INTEGRADO` e registre tambem o comando de teste executado e seu resultado.
