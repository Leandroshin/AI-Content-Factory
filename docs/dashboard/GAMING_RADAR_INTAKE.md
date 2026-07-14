# Gaming Radar -> Dashboard

O Radar Diario nao deve criar uma conversa que o owner precise administrar por noticia. Quando uma pauta passa pelos gates, a automacao envia um registro estruturado para `POST /api/intake/gaming` e a Central de Comando consolida a decisao.

## Seguranca

- O endpoint fica desativado sem `DASHBOARD_INTAKE_TOKEN`.
- O token e enviado apenas em `Authorization: Bearer ...` e nunca entra no Git.
- O corpo aceita no maximo 32 KB.
- IDs sao slugs estaveis; repetir o mesmo ID atualiza a pauta em vez de duplicar.
- Pelo menos uma fonte HTTPS e obrigatoria.
- A entrada cria apenas uma oportunidade pendente. Nao produz, publica ou gasta.

## Contrato

```json
{
  "id": "gaming-2026-07-13-forensics",
  "title": "Forensics chega com demanda pre-lancamento comprovada",
  "source": "Gaming News Desk",
  "channel": "Fase Nova Games",
  "category": "Noticia",
  "summary": "Lancamento confirmado com 100 mil wishlists e 80 mil downloads da demo.",
  "priority": "high",
  "score": 99,
  "confidence": 96,
  "risk": "Medio: evitar imagens graficas e alegacoes de treinamento profissional.",
  "nextAction": "Conferir as fontes e aprovar ou rejeitar a pauta.",
  "updatedAt": "2026-07-13T12:00:00.000Z",
  "sources": [
    {
      "label": "Pagina oficial na Steam",
      "url": "https://store.steampowered.com/app/3765010/Forensics_Crime_Scene_Detective/",
      "sourceType": "official",
      "publishedAt": "2026-07-13T00:00:00.000Z"
    }
  ]
}
```

## Estado e proxima ligacao

1. Concluido: dashboard privado hospedado com banco D1 persistente.
2. Concluido: segredo forte de `DASHBOARD_INTAKE_TOKEN` configurado no host e salvo fora do Git.
3. Concluido: `GamingDashboardBridge` transforma somente decisoes `review` no contrato JSON do painel.
4. Ligar o bridge ao executor diario usando o segredo local; dias `no_news` ja sao ignorados pelo contrato.
5. Confirmar com a primeira pauta real que a fonte abre e que uma repeticao atualiza sem duplicar.
