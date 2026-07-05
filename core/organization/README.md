# core/organization

Fundação arquitetural do subsistema de **Organization** da AI Content Factory.

## Responsabilidade

Representar a organização da AI Company como um todo, servindo como ponto
conceitual central entre Departments, Employees, Skills, Tasks e Workflows,
sem acoplamento funcional entre eles.

## O que este módulo faz

- define modelos-base de organização
- define contratos públicos de registry e validator
- documenta estrutura hierárquica, divisões e reporting

## O que este módulo não faz

- não executa lógica operacional
- não conecta employees diretamente a tasks
- não integra engines
- não integra providers
- não cria filas, scheduler, dispatcher ou threads

## API pública

- `Organization`
- `OrganizationCompany`
- `OrganizationId`
- `OrganizationMetadata`
- `OrganizationContext`
- `OrganizationStatus`
- `OrganizationResult`
- `BusinessUnit`
- `Division`
- `Hierarchy`
- `ReportingStructure`
- `OrganizationRegistryContract`
- `OrganizationValidatorContract`

## Evolução futura

Este subsistema poderá, em fases posteriores, acomodar políticas
organizacionais, estruturas de governança e pontos de integração conceitual
sem abandonar o modelo contract-first.