# Screen: News Digest And Chat v2

## Route
`/news`

## ASCII (desktop)
```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ FuelSight                                 [analyst]  [cloud_llm: NeuralDeep] [news cached]             │
├────────────────┬─────────────────────────────────────────────────────────────────────────────────────────┤
│ [KPI]          │ Сводка новостей и чат                                                                    │
│ [Продажи]      │                                                                                         │
│ [Маржа]        │ ┌────────────────────────────────────────────┐ ┌──────────────────────────────────────┐ │
│ [Прогноз]      │ │ Digest                                     │ │ Chat                                 │ │
│ [Сводка]       │ │ summary, bullets, freshness, provider mode │ │ answer + citations + confidence      │ │
│                │ └────────────────────────────────────────────┘ └──────────────────────────────────────┘ │
│                │                                                                                         │
│                │ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│                │ │ Search / source explorer                                                                │ │
│                │ └─────────────────────────────────────────────────────────────────────────────────────┘ │
└────────────────┴─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Notes
- if cloud generation is unavailable, badge changes to `local_llm` or `retrieval_only`;
- digest and search remain available in all modes.
- provider detail may show `NeuralDeep`, `GigaChat`, `local` or `none`;
- chat copy must explain weak evidence as "данных недостаточно", not invent missing facts.
