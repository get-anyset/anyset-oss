import { ColumnDef } from '@tanstack/react-table';
import { ApiIntegration } from '../../api-integration';
import { QueryRequestDTO } from '../../api-integration/types';

export interface TableProps<
  TData extends object,
  Ta = any,
  Tc = any,
  Td = any,
  Tf = any,
> {
  apiClient: ApiIntegration<Ta, Tc, Td, Tf>;
  filters?: QueryRequestDTO<Ta, Tc, Td, Tf>['filters'];
  useLazyLoading: boolean;
  defaultPageSize: number;
  columns: ColumnDef<TData, any>[];
}
