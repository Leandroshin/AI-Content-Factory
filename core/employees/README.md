# core/employees

Fundação arquitetural do subsistema de **Employees** da AI Content Factory.

## Responsabilidade

Representar um Employee como uma identidade estrutural da AI Company, sem
execução, sem comportamento funcional e sem acoplamento com Tasks, Workflows,
Engines ou Providers.

## O que este módulo faz

- define modelos-base de employee
- define contratos públicos de registry, validator e factory
- documenta a diferença entre identidade, perfil, disponibilidade e contexto

## O que este módulo não faz

- não executa tasks
- não conhece engines
- não conhece providers
- não participa de workflows
- não cria IA
- não cria aprendizado
- não cria automação

## API pública

- `Employee`
- `EmployeeId`
- `EmployeeProfile`
- `EmployeeRole`
- `EmployeeStatus`
- `EmployeeCapability`
- `EmployeeIdentity`
- `EmployeeAvailability`
- `EmployeeContext`
- `EmployeeResult`
- `EmployeeRegistryContract`
- `EmployeeValidatorContract`
- `EmployeeFactoryContract`

## Evolução futura

Quando houver necessidade de comportamento funcional, este subsistema poderá
receber integração com perfis operacionais, permissões, responsabilidades e
coordenação com outros contratos da AI Company.