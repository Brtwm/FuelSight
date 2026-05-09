import {
  Box,
  Card,
  CardContent,
  Divider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import type { LowMarginDay } from '../../../lib/api/analytics.types';

type Props = {
  days: LowMarginDay[];
  onSelectDay: (date: string) => void;
};

export function LowMarginTable({ days, onSelectDay }: Props) {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Дни ниже порога
        </Typography>
        {days.length === 0 ? (
          <Typography color="text.secondary">Низкая маржа не зафиксирована.</Typography>
        ) : isCompact ? (
          <Stack spacing={1}>
            {days.map((item) => (
              <Card
                key={item.date}
                variant="outlined"
                sx={{ cursor: 'pointer' }}
                onClick={() => onSelectDay(item.date)}
              >
                <CardContent sx={{ p: 1.25, '&:last-child': { pb: 1.25 } }}>
                  <Stack spacing={0.75}>
                    <Typography variant="body2" fontWeight={600}>
                      {new Date(item.date).toLocaleDateString('ru-RU')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Маржа: {item.gross_margin_rub_per_liter === null
                        ? '—'
                        : `${item.gross_margin_rub_per_liter.toFixed(2)} руб/л`}
                    </Typography>
                    <Divider />
                    <Typography variant="body2" color="text.secondary">
                      {item.purchase_data_missing ? 'Нет закупки' : 'Ниже порога'}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        ) : (
          <Box sx={{ overflowX: 'auto' }}>
            <Table size="small" sx={{ minWidth: 420 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Дата</TableCell>
                  <TableCell>Маржа, руб/л</TableCell>
                  <TableCell>Статус</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {days.map((item) => (
                  <TableRow
                    key={item.date}
                    hover
                    onClick={() => onSelectDay(item.date)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>{new Date(item.date).toLocaleDateString('ru-RU')}</TableCell>
                    <TableCell>
                      {item.gross_margin_rub_per_liter === null
                        ? '—'
                        : item.gross_margin_rub_per_liter.toFixed(2)}
                    </TableCell>
                    <TableCell>
                      {item.purchase_data_missing ? 'Нет закупки' : 'Ниже порога'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
