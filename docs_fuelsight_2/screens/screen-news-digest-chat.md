# Screen: News Digest And Chat v2

## Route
`/news`

## ASCII (desktop)
```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ FuelSight                                                        [Аналитик] [Выйти]                    │
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
- if cloud generation is unavailable, `/news` shows a page-level localized badge/warning such as `без генерации`;
- digest and search remain available in all modes.
- provider/model/degradation details are not shown as raw chat labels; mode is summarized through localized badges and warnings;
- chat copy must explain weak evidence as "данных недостаточно", not invent missing facts.
- Mobile uses tabs `[Сводка | Поиск | Чат]`; assistant messages use an amber border, user messages use calm cyan/dark fill, and citations remain mandatory.
