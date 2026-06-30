# AI Content Factory — Development Standards

Documento oficial de padrões de desenvolvimento da AI Content Factory.

Este arquivo define convenções obrigatórias para toda contribuição futura no
repositório. Ele não introduz comportamento novo nem substitui o
`AI_DEVELOPMENT_MANUAL.md`; apenas transforma os princípios do projeto em
padrões práticos de implementação e documentação.

---

## 1. Estrutura de diretórios e responsabilidade de cada módulo

### Diretórios de topo

| Diretório | Responsabilidade |
|----------|------------------|
| `docs/` | Documentação oficial, decisões arquiteturais, RFCs, ideias e padrões |
| `config/` | Configuração global do projeto, sem lógica de negócio |
| `projects/` | Configurações por nicho, tema ou instância do produto |
| `core/` | Infraestrutura central compartilhada por todo o sistema |
| `shared/` | Utilitários puros e genéricos, sem dependência em engines |
| `engines/` | Módulos de domínio do pipeline de conteúdo |
| `tests/` | Testes do repositório |
| `assets/` | Recursos estáticos e mídias de apoio |
| `output/` | Artefatos gerados pela aplicação |
| `temp/` | Arquivos temporários e intermediários |
| `.github/` | Automação, metadados e configurações do GitHub |

### Responsabilidade por camada

| Camada | Papel |
|--------|------|
| `core/` | Fornecer infraestrutura base como configuração, logging, exceções e modelos compartilhados |
| `engines/` | Implementar etapas isoladas do pipeline de conteúdo |
| `shared/` | Abstrações reutilizáveis, puras e independentes de domínio |
| `projects/` | Guardar somente configuração externa ao código |

### Regra de dependência

- `engines/` pode depender de `core/` e `shared/`
- `core/` não depende de `engines/`
- `shared/` não depende de `core/` nem de `engines/`
- `projects/` e `docs/` não devem conter lógica executável

---

## 2. Convenção para nomes de arquivos

- Arquivos Python usam `snake_case`
- Arquivos de documentação usam `kebab-case` ou nomes descritivos consistentes
- `README.md` é o nome obrigatório para documentação de diretório
- Arquivos de exceção usam nomes explícitos, como `exceptions.py`
- Arquivos de modelos usam `models.py`
- Arquivos de orquestração usam `loader.py`, `engine.py`, `manager.py` ou nomes equivalentes, conforme o papel real

### Regras adicionais

- Evitar nomes genéricos sem contexto
- Não usar abreviações obscuras
- Um arquivo deve ter uma responsabilidade principal

---

## 3. Convenção para nomes de classes

- Classes usam `PascalCase`
- Nomes devem ser descritivos e orientados à responsabilidade
- Classes de domínio devem expressar intenção, não implementação

### Exemplos de padrão

- `ProjectConfig`
- `ConfigLoader`
- `ConfigurationError`
- `ScriptEngine`

### Regras

- Não usar prefixos desnecessários
- Não repetir o nome do módulo no nome da classe quando isso for redundante
- Exceptions devem ser nomeadas como erro do domínio que representam

---

## 4. Convenção para nomes de funções

- Funções usam `snake_case`
- O nome deve indicar claramente a ação executada
- Funções públicas devem ser semânticas e legíveis

### Exemplos

- `load_config`
- `validate_environment`
- `build_project_config`

### Regras

- Verbos claros preferidos: `load`, `build`, `validate`, `resolve`, `parse`
- Evitar funções com nomes ambíguos ou excessivamente genéricos
- Funções curtas são preferíveis a funções extensas e multifuncionais

---

## 5. Convenção para nomes de variáveis

- Variáveis usam `snake_case`
- Nomes devem refletir conteúdo, propósito e unidade semântica
- Evitar abreviações curtas sem significado claro

### Regras

- `config_loader` é melhor que `cl`
- `project_name` é melhor que `name`
- `is_valid` é melhor que `valid`
- Variáveis booleanas devem usar prefixos semânticos como `is_`, `has_`, `should_`

---

## 6. Obrigatoriedade de type hints

- Type hints são obrigatórios em funções públicas, métodos públicos e interfaces
- Type hints são fortemente recomendados em atributos de classe e retornos internos
- O objetivo é facilitar leitura, validação e manutenção

### Regras

- Toda função pública deve declarar parâmetros e retorno
- `Any` só deve ser usado quando não houver alternativa razoável
- Unions devem ser explícitas quando necessários múltiplos tipos

---

## 7. Organização dos imports

- Imports devem ser agrupados em três blocos:
  1. biblioteca padrão
  2. dependências de terceiros
  3. imports locais do projeto
- Cada bloco deve ser ordenado alfabeticamente
- Imports absolutos são preferíveis para código de aplicação

### Regras

- Não usar imports circulares
- Não importar símbolos não utilizados
- Não esconder dependências entre módulos por atalhos frágeis

---

## 8. Padrão para criação de Exceptions

- Toda exceção de domínio deve herdar de uma exceção base do módulo
- Exceções devem ser explícitas, pequenas e sem efeitos colaterais
- A hierarquia deve refletir a semântica do erro

### Estrutura esperada

- `BaseError` do módulo
- Exceções específicas por categoria

### Regras

- Não levantar `Exception` genérico em código de domínio
- Mensagens de exceção devem ser claras e orientadas à correção
- Exceptions não devem conter lógica de negócio

---

## 9. Padrão para Models

- Models devem representar dados, não comportamento complexo
- Devem ser previsíveis, validados e fáceis de serializar
- Preferir `pydantic` para validação estruturada quando houver necessidade de schemas

### Regras

- Um model por responsabilidade conceitual
- Evitar models monolíticos
- Não acoplar models a APIs externas específicas
- Models devem ser fáceis de testar isoladamente

---

## 10. Estrutura mínima obrigatória de uma Engine

Toda engine deve ser um pacote independente e conter, no mínimo:

- `__init__.py`
- `engine.py`
- `models.py`
- `exceptions.py`
- `providers/__init__.py`
- `README.md`

### Regras

- A engine é a unidade de domínio
- Providers são opcionais até existir integração externa
- Cada engine deve permanecer independente das demais
- Engines não devem conhecer detalhes internos de outras engines

### Observação sobre testes

Os testes devem existir conforme a estratégia do repositório e acompanhar a
implementação da engine, sem introduzir dependências arquiteturais indevidas.

---

## 11. Convenção para README de cada módulo

Todo diretório relevante deve possuir um `README.md` curto e objetivo.

### Conteúdo mínimo esperado

- Responsabilidade do módulo
- O que o módulo faz
- O que o módulo não faz
- Relações de dependência
- Interface pública, quando aplicável
- Próximos passos ou status, quando útil

### Regras

- README deve ajudar um novo agente a entender o módulo rapidamente
- README não substitui código nem ADRs
- README deve ser coerente com a estrutura real do diretório

---

## 12. Padrão de Logging

Logging deve existir como padrão estrutural do projeto, mesmo quando ainda não
houver implementação completa em um módulo.

### Campos mínimos esperados

- `module`
- contexto da operação
- nível de severidade
- mensagem clara

### Regras

- Logs devem ser estruturados
- Logs devem ser úteis para diagnóstico
- Não logar secrets, tokens ou credenciais
- O formato deve ser consistente entre módulos

---

## 13. Convenção para mensagens de erro

- Mensagens devem ser claras, curtas e acionáveis
- Mensagens devem indicar o problema, não apenas o sintoma
- Quando possível, devem sugerir a correção

### Regras

- Evitar mensagens vagas como “Erro inesperado”
- Evitar mensagens que exponham detalhes sensíveis
- Mensagens devem ser consistentes entre módulos

### Exemplo de estilo

- Preferir: “`OUTPUT_DIR` não foi configurado”
- Evitar: “Falha na operação”

---

## 14. Convenção para documentação de funções

- Funções públicas devem ter docstring
- A docstring deve descrever propósito, parâmetros e retorno quando útil
- A intenção da função deve ser compreensível sem leitura do corpo

### Regras

- Funções curtas e óbvias podem ter docstring simples, conforme o padrão do projeto
- Funções complexas devem explicar contexto e contrato
- A documentação deve acompanhar o comportamento real

---

## 15. Convenção para futuras integrações com APIs externas

- Toda integração externa deve ser abstrata por interface interna
- Nenhum módulo de domínio deve depender diretamente de SDKs específicos sem uma camada de adaptação
- Serviços externos devem ser tratados como substituíveis

### Regras

- Timeout obrigatório
- Tratamento explícito de falhas
- Retentativas quando apropriado
- Fallbacks somente quando fizerem sentido arquitetural
- Credenciais sempre via ambiente, nunca hardcoded

---

## 16. Convenção para Providers

Providers são implementações concretas de integração externa.

### Regras

- Providers vivem em `providers/`
- Cada provider deve cumprir um contrato interno do módulo
- Providers não devem conter regra de negócio
- Providers devem ser substituíveis sem alterar a interface pública da engine

### Estrutura esperada

- `providers/__init__.py`
- módulos por serviço ou integração

---

## 17. Convenção para testes

- Testes devem acompanhar a estrutura do código
- Todo comportamento novo deve ser validado
- Testes devem ser claros, estáveis e isolados

### Regras

- Nome de arquivo: `test_*.py`
- Nome de função: `test_*`
- Usar `pytest`
- Evitar testes frágeis acoplados a detalhes internos irrelevantes

### Prioridade

1. Testes unitários
2. Testes de integração quando houver fronteira real
3. Testes end-to-end apenas quando o fluxo completo existir

---

## 18. Convenção para configuração

- Toda configuração deve ser externa ao código
- Configuração de nicho deve residir em `projects/`
- Segredos devem residir em variáveis de ambiente
- Defaults devem ser previsíveis e documentados

### Regras

- Não codificar valores de ambiente em lógica de negócio
- A configuração deve ser validável
- Mudança de nicho não deve exigir mudança de código-fonte
- O loader de configuração deve permanecer isolado em `core/`

---

## 19. Convenção para arquivos em `projects/`

Os arquivos em `projects/` representam perfis de configuração por nicho,
canal, tema ou instância do produto.

### Regras

- Devem conter apenas configuração
- Não devem conter lógica executável
- Devem ser legíveis e versionáveis
- Devem permitir troca de nicho sem alteração de código

### Conteúdo esperado

- Nome do projeto
- Nicho/tema
- Preferências de produção
- Parâmetros de execução
- Valores de configuração específicos do perfil

---

## 20. Princípios gerais do projeto

Os seguintes princípios são obrigatórios em toda decisão técnica:

- Clean Architecture
- Separação de responsabilidades
- Baixo acoplamento
- Alta coesão
- Modularidade
- Extensibilidade

### Diretrizes práticas

- Cada módulo deve ter uma responsabilidade clara
- Dependências devem fluir para camadas mais estáveis
- Tecnologias externas devem ser encapsuladas
- O código deve ser fácil de substituir, testar e evoluir
- O sistema deve permanecer agnóstico ao nicho

---

## Conformidade com o manual

Este documento está alinhado com o `AI_DEVELOPMENT_MANUAL.md` e reforça seus
princípios sem alterar a arquitetura definida anteriormente.

Em caso de conflito entre este documento e o manual, o manual prevalece.
