import LinkOutlinedIcon from '@mui/icons-material/LinkOutlined';
import { Box, Button, Chip, List, ListItem, ListItemIcon, ListItemText, Stack, Typography } from '@mui/material';
import type { CitationData } from '../../../lib/api/chat.types';
import { SourceModeBadge } from '../../../components/common/SourceModeBadge';

type Props = {
  citations: CitationData[];
  onNewsCitationClick?: (refId: string) => void;
};

function sourceTypeLabel(value: string): string {
  const labels: Record<string, string> = {
    news_raw: 'новость',
    analytics: 'аналитика',
    forecast: 'прогноз',
    internal_ref: 'внутренний источник',
  };
  return labels[value] ?? 'источник';
}

export function CitationList({ citations, onNewsCitationClick }: Props) {
  if (citations.length === 0) {
    return null;
  }

  return (
    <>
      <Typography variant="subtitle2" fontWeight={700}>
        Источники
      </Typography>
      <List dense disablePadding>
        {citations.map((citation) => (
          <ListItem key={`${citation.type}-${citation.ref_id}`} disablePadding sx={{ py: 0.25 }}>
            <ListItemIcon sx={{ minWidth: 24 }}>
              <LinkOutlinedIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary={
                <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                  <Typography variant="body2">{citation.title}</Typography>
                  <SourceModeBadge mode={citation.provider_mode} title="режим" compact />
                  <Chip
                    size="small"
                    variant="outlined"
                    label={`Уверенность источника: ${Math.round(citation.confidence * 100)}%`}
                    sx={{ height: 22, '& .MuiChip-label': { px: 0.75, fontSize: '0.68rem' } }}
                  />
                  {citation.type === 'news' && onNewsCitationClick ? (
                    <Button size="small" onClick={() => onNewsCitationClick(citation.ref_id)}>
                      Найти в новостях
                    </Button>
                  ) : null}
                </Stack>
              }
              secondary={
                <Box component="span">
                  <Typography component="span" variant="caption" display="block">
                    {sourceTypeLabel(citation.source_type)}: {citation.ref_id}
                  </Typography>
                  {citation.snippet ? (
                    <Typography component="span" variant="caption" color="text.secondary" display="block">
                      {citation.snippet}
                    </Typography>
                  ) : null}
                </Box>
              }
              secondaryTypographyProps={{ variant: 'caption' }}
            />
          </ListItem>
        ))}
      </List>
    </>
  );
}
