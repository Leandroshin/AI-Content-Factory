# Central AI Content Factory

Painel operacional privado da fabrica. Ele transforma o estado dos departamentos em uma interface diaria para:

- revisar oportunidades e riscos;
- conferir as fontes originais de cada oportunidade;
- aprovar ou rejeitar a entrada em producao;
- acompanhar a esteira de conteudo e afiliados;
- verificar canais, providers e custos;
- consultar o historico de decisoes.

O menu troca entre areas independentes. A lupa abre uma busca global, enquanto a fila possui busca e filtros locais. Em Configuracoes, o owner pode alternar entre os temas Operacional e Matrix.

Uma aprovacao neste painel **nao publica, nao anuncia e nao gera custo**. Publicacao e gasto continuam em gates separados.

## Fluxos controlados

- **Caixa de Aprendizado:** recebe fonte e transcricao, preserva evidencias e exige auditoria humana antes de qualquer conhecimento oficial.
- **Fila Telegram:** preparar registra a mensagem exata como `PENDING HUMAN APPROVAL`; uma segunda aprovacao coloca o candidato na fila local.
- **Publicacao real controlada:** o envio continua separado, exige worker local com opt-in, credenciais fora do Git e devolucao auditavel de `message_id`.

Em todas essas etapas, preparar ou aprovar no painel nao executa automaticamente
providers externos. O candidato mostra destino, validade, riscos e chave de
idempotencia antes de qualquer envio.

## Desenvolvimento

Requer Node.js `>=22.13.0`.

```bash
npm ci
npm run dev
npm run lint
npm run build
```

O banco usa Cloudflare D1 pelo binding `DB` declarado em `.openai/hosting.json`. O preview local cria um D1 isolado; a publicacao pelo Sites injeta o banco persistente de producao.

## Estrutura

- `app/components/DashboardClient.tsx`: cockpit e interacoes.
- `app/api/dashboard/`: leitura e persistencia do estado.
- `app/api/actions/`: decisoes HITL.
- `app/api/intake/gaming/`: entrada autenticada e idempotente do Radar Diario.
- `app/api/products/`: entrada visual e persistente de URLs fornecidas pelo owner.
- `app/api/intake/products/`: fila autenticada para coleta dos funcionários e devolução da análise.
- `db/schema.ts`: oportunidades, fontes e log de auditoria.
- `drizzle/`: migracoes versionadas.
- `public/brands/`: identidades visuais dos canais.

O site deve ser implantado com acesso privado. A identidade do operador vem dos headers autenticados do Sites/ChatGPT; em desenvolvimento aparece como `Modo local`.

O endpoint do radar permanece desativado ate `DASHBOARD_INTAKE_TOKEN` ser configurado no ambiente hospedado.
