import LinkOutlinedIcon from '@mui/icons-material/LinkOutlined';
import { Button, Chip, List, ListItem, ListItemIcon, ListItemText, Stack, Typography } from '@mui/material';
import type { CitationData } from '../../../lib/api/chat.types';
import { SourceModeBadge } from '../../../components/common/SourceModeBadge';

type Props = {
  citations: CitationData[];
  onNewsCitationClick?: (refId: string) => void;
};

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
                    label={`confidence: ${Math.round(citation.confidence * 100)}%`}
                    sx={{ height: 22, '& .MuiChip-label': { px: 0.75, fontSize: '0.68rem' } }}
                  />
                  {citation.type === 'news' && onNewsCitationClick ? (
                    <Button size="small" onClick={() => onNewsCitationClick(citation.ref_id)}>
                      Найти в новостях
                    </Button>
                  ) : null}
                </Stack>
              }
              secondary={`${citation.source_type}: ${citation.ref_id}`}
              secondaryTypographyProps={{ variant: 'caption' }}
            />
          </ListItem>
        ))}
      </List>
    </>
  );
}
