export type ImportJobStatus =
  | 'queued'
  | 'processing'
  | 'completed'
  | 'completed_with_errors'
  | 'failed';

export type ImportEntityType = 'sales' | 'purchases' | 'historical_data';

export type ImportUploadResult = {
  job_id: string;
  entity_type: ImportEntityType;
  status: ImportJobStatus;
};

export type GenerateHistoryPayload = {
  start_date: string;
  end_date: string;
  products: string[];
  seed: number;
  replace_existing: boolean;
};

export type ImportJob = {
  id: string;
  entity_type: ImportEntityType | string;
  source_type: string;
  file_name: string | null;
  status: ImportJobStatus;
  rows_total: number;
  rows_success: number;
  rows_failed: number;
  error_report_path: string | null;
  started_at: string;
  finished_at: string | null;
};

export type ImportJobDetails = ImportJob & {
  started_by: string;
};

