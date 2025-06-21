import React from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getFilteredRowModel,
  ColumnDef,
  flexRender,
  RowData,
  PaginationState,
} from '@tanstack/react-table';
import { useQuery, QueryKey } from '@tanstack/react-query';
import { TableProps } from './Table.types';
import { QueryRequestDTO, QueryResponseDTO } from '../../api-integration/types';

// Declaring the generic type TData for row data
declare module '@tanstack/react-table' {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface TableMeta<TData extends RowData> {
    // You can define table meta properties here if needed
  }
}

// Helper function to transform QueryResponseDTO to TData[]
const transformData = <TData extends object>(
  apiResponse: QueryResponseDTO | undefined
): TData[] => {
  if (!apiResponse || !apiResponse.columns || apiResponse.columns.length === 0) {
    return [];
  }

  const { columns, record_count_current_page } = apiResponse;
  const rowCount = record_count_current_page; // Or determine from first column's data length

  if (rowCount === 0) return [];

  const transformedRecords: TData[] = [];

  for (let i = 0; i < rowCount; i++) {
    const record: Record<string, any> = {};
    columns.forEach(col => {
      record[col.alias] = col.data[i];
    });
    transformedRecords.push(record as TData);
  }
  return transformedRecords;
};


const Table = <
  TData extends object,
  Ta = any,
  Tc = any,
  Td = any,
  Tf = any
>({
  apiClient,
  filters = [],
  useLazyLoading,
  defaultPageSize,
  columns,
}: TableProps<TData, Ta, Tc, Td, Tf>) => {
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0, // Tanstack table uses 0-based index
    pageSize: defaultPageSize,
  });

  // Query key must include all dependencies of the query
  const queryKey: QueryKey = [
    'tableData',
    apiClient, // Add apiClient instance if its config can change, or a stable ID from it
    filters,
    pagination.pageIndex,
    pagination.pageSize,
    useLazyLoading,
  ];

  const queryFn: import('@tanstack/react-query').QueryFunction<QueryResponseDTO, QueryKey> = async () => {
    const queryParams: QueryRequestDTO<Ta, Tc, Td, Tf> = {
      // table_name is required by QueryRequestDTO, but not available in TableProps.
      // This indicates a potential design issue or that table_name should be passed to Table.
        // For now, using a placeholder. This needs to be addressed.
        table_name: 'default_table_name_placeholder', // FIXME: This needs a proper value
        filters: filters,
        pagination: {
          limit: pagination.pageSize,
          offset: useLazyLoading
            ? pagination.pageIndex * pagination.pageSize
            : (pagination.pageIndex) * pagination.pageSize, // Non-lazy (page-based) also uses offset
        },
        // select and aggregations might be needed depending on API requirements
      };
      // Remove page if useLazyLoading, or adjust API to handle offset for both
      // The DTO has pagination.offset and pagination.limit.
      // 'page' was used before but DTO expects offset/limit.
      return apiClient.query(queryParams);
  };

  const dataQuery = useQuery<QueryResponseDTO, Error, QueryResponseDTO, QueryKey>({
    queryKey: queryKey,
    queryFn: queryFn,
    placeholderData: (previousData) => previousData, // keepPreviousData was for v4 and earlier
    // staleTime: 5 * 60 * 1000, // Example: 5 minutes
  });

  const transformedData = React.useMemo(
    () => transformData<TData>(dataQuery.data),
    [dataQuery.data]
  );

  const pageCount = dataQuery.data?.record_count_total
    ? Math.ceil(dataQuery.data.record_count_total / pagination.pageSize)
    : -1; // -1 if total is unknown (e.g. some lazy loading scenarios)

  const table = useReactTable({
    data: transformedData,
    columns: columns as ColumnDef<TData, any>[],
    state: {
      pagination,
    },
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(), // Required for pagination
    getFilteredRowModel: getFilteredRowModel(),   // Required if using client-side filtering features
    manualPagination: true, // IMPORTANT: we are doing server-side pagination
    pageCount: pageCount,
    // debugTable: true,
  });

  if (dataQuery.isLoading) {
    return <div>Loading...</div>;
  }

  if (dataQuery.isError) {
    return <div>Error fetching data: {dataQuery.error?.message}</div>;
  }

  if (!dataQuery.data && !dataQuery.isLoading) {
    return <div>No data available.</div>;
  }


  return (
    <div className="table-container">
      <table>
        <thead>
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th key={header.id} colSpan={header.colSpan}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id}>
              {row.getVisibleCells().map(cell => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination-controls">
        <button
          onClick={() => table.setPageIndex(0)}
          disabled={!table.getCanPreviousPage()}
        >
          {'<<'}
        </button>
        <button
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          {'<'}
        </button>
        <span>
          Page{' '}
          <strong>
            {table.getState().pagination.pageIndex + 1} of {table.getPageCount() === -1 ? 'many' : table.getPageCount()}
          </strong>{' '}
        </span>
        <button
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          {'>'}
        </button>
         <button
          onClick={() => table.setPageIndex(table.getPageCount() - 1)}
          disabled={!table.getCanNextPage()}
        >
          {'>>'}
        </button>
        <select
          value={table.getState().pagination.pageSize}
          onChange={e => {
            table.setPageSize(Number(e.target.value));
          }}
        >
          {[10, 20, 30, 40, 50].map(pageSize => (
            <option key={pageSize} value={pageSize}>
              Show {pageSize}
            </option>
          ))}
        </select>
         <span>
          Total Rows: {dataQuery.data?.record_count_total ?? 'Unknown'}
        </span>
      </div>
    </div>
  );
};

export default Table;
