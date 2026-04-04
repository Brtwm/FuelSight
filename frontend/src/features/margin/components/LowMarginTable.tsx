import {
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import type { LowMarginDay } from '../../../lib/api/analytics.types';

type Props = {
  days: LowMarginDay[];
  onSelectDay: (date: string) => void;
};

export function LowMarginTable({ days, onSelectDay }: Props) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Дни ниже порога
        </Typography>
        {days.length === 0 ? (
          <Typography color="text.secondary">Низкая маржа не зафиксирована.</Typography>
        ) : (
          <Table size="small">
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
                      ? 'N/A'
                      : item.gross_margin_rub_per_liter.toFixed(2)}
                  </TableCell>
                  <TableCell>
                    {item.purchase_data_missing ? 'Нет закупки' : 'Ниже порога'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
