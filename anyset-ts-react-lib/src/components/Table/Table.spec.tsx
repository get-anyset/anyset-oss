import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import Table from './Table'; // Adjust path as necessary
import { ApiIntegration } from '../../api-integration'; // Adjust path
import { QueryRequestDTO, QueryResponseDTO, FilterOptionResponseDTO } from '../../api-integration/types'; // Adjust path

// Mock ApiIntegration
const mockApiClient = {
  query: jest.fn(),
  getFilterOptions: jest.fn(),
  // Ensure all methods of ApiIntegration used by the component or its setup are mocked
} as unknown as jest.Mocked<ApiIntegration<any, any, any, any>>;


interface TestData {
  id: number;
  name: string;
  value: number;
}

const testColumns: ColumnDef<TestData, any>[] = [
  {
    accessorKey: 'id', // Corresponds to alias in QueryResponseDTO.columns
    header: 'ID',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'name', // Corresponds to alias in QueryResponseDTO.columns
    header: 'Name',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'value', // Corresponds to alias in QueryResponseDTO.columns
    header: 'Value',
    cell: info => info.getValue(),
  },
];

// Helper to create mock QueryResponseDTO
const createMockQueryResponse = (
  records: TestData[],
  total: number,
  pageSize: number,
  pageIndex: number // 0-based
): QueryResponseDTO => {
  if (records.length === 0) {
    return {
      dataset: 'test-dataset',
      version: 1,
      record_count_current_page: 0,
      record_count_total: total,
      columns: [], // No data, so columns can be empty or reflect expected structure
    };
  }
  return {
    dataset: 'test-dataset',
    version: 1,
    record_count_current_page: records.length,
    record_count_total: total,
    columns: [ // This structure is based on QueryResponseDTO
      { alias: 'id', data: records.map(r => r.id) },
      { alias: 'name', data: records.map(r => r.name) },
      { alias: 'value', data: records.map(r => r.value) },
    ],
  };
};


const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false, // Disable retries for tests
      gcTime: Infinity, // Prevent garbage collection during tests for simplicity
    },
  },
});

const renderTable = (
  props: Partial<React.ComponentProps<typeof Table<TestData, any, any, any, any>>> = {},
  queryClient?: QueryClient
) => {
  const client = queryClient || createTestQueryClient();
  return render(
    <QueryClientProvider client={client}>
      <Table<TestData, any, any, any, any>
        apiClient={mockApiClient} // No 'as' needed if mockApiClient is correctly typed
        columns={testColumns}
        useLazyLoading={false}
        defaultPageSize={10}
        {...props}
      />
    </QueryClientProvider>
  );
};

describe('Table Component', () => {
  beforeEach(() => {
    mockApiClient.query.mockReset();
    mockApiClient.getFilterOptions.mockReset(); // Reset if it's used anywhere
    // Mock getFilterOptions if it's part of ApiIntegration and might be called
    mockApiClient.getFilterOptions.mockResolvedValue([] as FilterOptionResponseDTO);
  });

  test('renders loading state initially', () => {
    mockApiClient.query.mockReturnValue(new Promise(() => {})); // Never resolves
    renderTable();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('renders error state if data fetching fails', async () => {
    mockApiClient.query.mockRejectedValue(new Error('Failed to fetch'));
    renderTable();
    expect(await screen.findByText('Error fetching data: Failed to fetch')).toBeInTheDocument();
  });

  test('renders "No data available" when query returns empty or undefined data after loading', async () => {
    mockApiClient.query.mockResolvedValue({} as QueryResponseDTO); // Empty response
    renderTable();
    expect(await screen.findByText('No data available.')).toBeInTheDocument();

    mockApiClient.query.mockResolvedValue(undefined as any); // Undefined response
    renderTable();
    expect(await screen.findByText('No data available.')).toBeInTheDocument();
  });


  test('renders table with data (pagination mode)', async () => {
    const records = [
      { id: 1, name: 'Test 1', value: 100 },
      { id: 2, name: 'Test 2', value: 200 },
    ];
    const mockData = createMockQueryResponse(records, 2, 10, 0);
    mockApiClient.query.mockResolvedValue(mockData);

    renderTable({ defaultPageSize: 10 });

    await waitFor(() => {
      expect(screen.getByText('Test 1')).toBeInTheDocument();
      expect(screen.getByText('Test 2')).toBeInTheDocument();
    });

    expect(screen.getByText('ID')).toBeInTheDocument(); // Header
    expect(screen.getByText('Name')).toBeInTheDocument(); // Header
    expect(screen.getByText('Value')).toBeInTheDocument(); // Header
    expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 1 of 1');
    expect(screen.getByText('Total Rows:', { exact: false })).toHaveTextContent('Total Rows: 2');
  });

  test('handles pagination: navigates to next and previous page', async () => {
    const pageSize = 3;
    const totalRecords = 6;
    const page1Records = Array.from({ length: pageSize }, (_, i) => ({ id: i + 1, name: `Item ${i + 1}`, value: (i + 1) * 10 }));
    const page2Records = Array.from({ length: pageSize }, (_, i) => ({ id: i + pageSize + 1, name: `Item ${i + pageSize + 1}`, value: (i + pageSize + 1) * 10 }));

    const page1Data = createMockQueryResponse(page1Records, totalRecords, pageSize, 0);
    const page2Data = createMockQueryResponse(page2Records, totalRecords, pageSize, 1);

    mockApiClient.query.mockResolvedValueOnce(page1Data); // Initial load

    renderTable({ defaultPageSize: pageSize });

    // Initial load (Page 1)
    await waitFor(() => expect(screen.getByText('Item 1')).toBeInTheDocument());
    expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 1 of 2');
    expect(mockApiClient.query).toHaveBeenCalledWith(expect.objectContaining({
      table_name: 'default_table_name_placeholder', // Or whatever the component defaults/uses
      pagination: { offset: 0, limit: pageSize }
    }));

    // Click Next
    mockApiClient.query.mockResolvedValueOnce(page2Data); // For next page
    fireEvent.click(screen.getByText('>'));
    await waitFor(() => expect(screen.getByText(`Item ${pageSize + 1}`)).toBeInTheDocument());
    expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 2 of 2');
    expect(mockApiClient.query).toHaveBeenCalledWith(expect.objectContaining({
      pagination: { offset: pageSize, limit: pageSize }
    }));

    // Click Previous
    mockApiClient.query.mockResolvedValueOnce(page1Data); // For previous page
    fireEvent.click(screen.getByText('<'));
    await waitFor(() => expect(screen.getByText('Item 1')).toBeInTheDocument());
    expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 1 of 2');
    expect(mockApiClient.query).toHaveBeenCalledWith(expect.objectContaining({
      pagination: { offset: 0, limit: pageSize }
    }));
  });


  test('handles page size change', async () => {
    const initialPageSize = 5;
    const newPageSize = 10;
    const totalRecords = 20;

    const initialRecords = Array.from({ length: initialPageSize }, (_, i) => ({ id: i + 1, name: `Test ${i + 1}`, value: (i+1)*10 }));
    const initialMockData = createMockQueryResponse(initialRecords, totalRecords, initialPageSize, 0);

    const newPageSizeRecords = Array.from({ length: newPageSize }, (_, i) => ({ id: i + 1, name: `Test ${i + 1}`, value: (i+1)*10 }));
    const newPageSizeMockData = createMockQueryResponse(newPageSizeRecords, totalRecords, newPageSize, 0);

    mockApiClient.query.mockResolvedValueOnce(initialMockData);
    renderTable({ defaultPageSize: initialPageSize });

    await waitFor(() => expect(screen.getByText('Test 1')).toBeInTheDocument());
    expect(mockApiClient.query).toHaveBeenCalledWith(expect.objectContaining({ pagination: { offset: 0, limit: initialPageSize }}));
    expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 1 of 4'); // 20 total / 5 per page

    // Change page size
    mockApiClient.query.mockResolvedValueOnce(newPageSizeMockData);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: newPageSize.toString() } });

    await waitFor(() => expect(mockApiClient.query).toHaveBeenCalledWith(expect.objectContaining({ pagination: { offset: 0, limit: newPageSize }})));
    expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 1 of 2'); // 20 total / 10 per page
    expect(screen.getByText('Test 1')).toBeInTheDocument();
  });

  test('fetches data with filters', async () => {
    const records = [{ id: 1, name: 'Filtered Item', value: 10 }];
    const mockData = createMockQueryResponse(records, 1, 10, 0);
    mockApiClient.query.mockResolvedValue(mockData);

    const filters: QueryRequestDTO<any,any,any,any>['filters'] = [{ column_name: 'name', values: ['Filtered'] }]; // Example filter structure
    renderTable({ filters });

    await waitFor(() => expect(screen.getByText('Filtered Item')).toBeInTheDocument());
    expect(mockApiClient.query).toHaveBeenCalledWith(expect.objectContaining({
      filters,
      pagination: { offset: 0, limit: 10 },
    }));
  });

  describe('Lazy Loading Mode', () => {
    test('renders table with data (lazy loading mode)', async () => {
      const records = [ { id: 1, name: 'Lazy Test 1', value: 100 } ];
      // For lazy loading, total might be an estimate or a large number if truly unknown page count
      const mockData = createMockQueryResponse(records, 100, 10, 0); // Assuming total is known for page count calc
      mockApiClient.query.mockResolvedValue(mockData);

      renderTable({ useLazyLoading: true, defaultPageSize: 10 });

      await waitFor(() => expect(screen.getByText('Lazy Test 1')).toBeInTheDocument());
      expect(mockApiClient.query).toHaveBeenCalledWith(expect.objectContaining({
        pagination: { limit: 10, offset: 0 },
      }));
      expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 1 of 10');
    });

    test('handles "next page" in lazy loading mode (fetches with offset)', async () => {
      const pageSize = 5;
      const totalRecords = 100; // Example total
      const page1Records = [{ id: 1, name: 'Lazy Item 1', value: 10 }];
      const page2Records = [{ id: 6, name: 'Lazy Item 6', value: 60 }];

      const page1Data = createMockQueryResponse(page1Records, totalRecords, pageSize, 0);
      const page2Data = createMockQueryResponse(page2Records, totalRecords, pageSize, 1);

      mockApiClient.query.mockResolvedValueOnce(page1Data);
      renderTable({ useLazyLoading: true, defaultPageSize: pageSize });

      await waitFor(() => expect(screen.getByText('Lazy Item 1')).toBeInTheDocument());
      expect(mockApiClient.query).toHaveBeenLastCalledWith(expect.objectContaining({ pagination: { limit: pageSize, offset: 0 }}));
      expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 1 of 20');

      mockApiClient.query.mockResolvedValueOnce(page2Data);
      fireEvent.click(screen.getByText('>')); // Click Next

      await waitFor(() => expect(screen.getByText('Lazy Item 6')).toBeInTheDocument());
      expect(mockApiClient.query).toHaveBeenLastCalledWith(expect.objectContaining({ pagination: { limit: pageSize, offset: pageSize }}));
      expect(screen.getByText('Page', { exact: false })).toHaveTextContent('Page 2 of 20');
    });
  });
});
