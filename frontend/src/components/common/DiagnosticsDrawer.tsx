import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import {
  Box,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Typography,
} from '@mui/material';
import type { ReactNode } from 'react';

type DiagnosticsDrawerProps = {
  open: boolean;
  title?: string;
  onClose: () => void;
  children?: ReactNode;
};

export function DiagnosticsDrawer({
  open,
  title = 'Диагностика источников и качества',
  onClose,
  children,
}: DiagnosticsDrawerProps) {
  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: { xs: 320, md: 420 }, p: 2 }}>
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          sx={{ mb: 1 }}
        >
          <Typography variant="h6" fontWeight={700}>
            {title}
          </Typography>
          <IconButton aria-label="Закрыть диагностику" onClick={onClose}>
            <CloseOutlinedIcon />
          </IconButton>
        </Stack>
        <Divider sx={{ mb: 2 }} />
        <Stack spacing={1.5}>
          {children ?? (
            <Typography color="text.secondary">
              Диагностическая информация пока недоступна.
            </Typography>
          )}
        </Stack>
      </Box>
    </Drawer>
  );
}
