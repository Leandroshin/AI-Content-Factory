# core/skills

Fundação arquitetural do subsistema de **Skills** da AI Content Factory.

## Responsabilidade

Representar uma Skill como uma capacidade reutilizável dentro da AI Company.
Uma Skill descreve potencial, nível, categoria, status e contexto estrutural,
sem conhecer `Employees`, `Tasks`, `Engines` ou `Providers`.

## O que este módulo faz

- define modelos-base de skill
- define contratos públicos de registry e validator
- documenta a diferença entre perfil, categoria, nível e contexto

## O que este módulo não faz

- não executa comportamento
- não cria IA
- não cria aprendizado
- não cria avaliação
- não conhece employees
- não conhece engines
- não conhece providers
- não conhece tasks

## API pública

- `Skill`
- `SkillProfile`
- `SkillCategory`
- `SkillCapability`
- `SkillLevel`
- `SkillStatus`
- `SkillContext`
- `SkillMetadata`
- `SkillRegistryContract`
- `SkillValidatorContract`

## Evolução futura

Quando houver necessidade de comportamento funcional, este subsistema poderá
receber especializações, políticas de compatibilidade e vínculos organizacionais
sem quebrar a superfície contratual atual.