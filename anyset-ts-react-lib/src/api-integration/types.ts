/**
 * Represents a query request for a dataset.
 *
 * @template Ta Type of the any column (can be category or fact).
 * @template Tc Type of the category column.
 * @template Td Type of the date column.
 * @template Tf Type of the fact (numeric) column.
 */
export type QueryRequestDTO<Ta, Tc, Td, Tf> = {
  table_name: string;
  select?: Select<Ta>[];
  aggregations?: Aggregation<Ta, Tf>[];
  filters?: ColumnFilter<Tc, Tf, Td>[];
  order_by?: OrderBy[];
  pagination?: Pagination;
};

/**
 * Represents the response from a dataset query.
 */
export type QueryResponseDTO = {
  dataset: string;
  version: number;
  record_count_current_page: number;
  record_count_total: number;
  columns: {
    alias: string;
    breakdown?: string;
    data: (string | null)[] | (number | null)[] | (boolean | null)[] | (Date | null)[];
  }[];
};

/**
 * Represents the values available for filtering in a dataset; used for auto-completion in the UI.
 */
export type FilterOptionResponseDTO = Record<
  string,
  | FilterOptionValue<string>
  | FilterOptionHierarchicalValue<string>
  | FilterOptionValue<number>
  | FilterOptionHierarchicalValue<number>
>[];

export type FilterOptionValue<T> = {
  label: string;
  value: T;
  children?: never;
};

export type FilterOptionHierarchicalValue<T> = {
  label: string;
  value: T;
  children: FilterOptionHierarchicalValue<T>[] | FilterOptionValue<T>[];
};

/**
 * Represents a filter applied to a column in a dataset.
 *
 * @template Tc Type of the category column.
 * @template Tf Type of the fact (numeric) column.
 * @template Td Type of the date column.
 *
 * - `CategoryColumnFilter<Tc>`: Filters rows based on a set of string values for a specific column.
 * - `FactColumnFilter<Tf>`: Filters rows based on a numeric range (inclusive) for a specific column. Supports open-ended ranges using `null`.
 * - `DateColumnFilter<Td>`: Filters rows based on a date range (inclusive) for a specific column. Supports open-ended ranges using `null`.
 */
export type ColumnFilter<Tc, Tf, Td> =
  | CategoryColumnFilter<Tc>
  | FactColumnFilter<Tf>
  | DateColumnFilter<Td>;

export type CategoryColumnFilter<Tc> = {
  column_name: Tc;
  values: string[];
};

export type FactColumnFilter<Tf> = {
  column_name: Tf;
  values: [number | null, number] | [number, number | null];
};

export type DateColumnFilter<Td> = {
  column_name: Td;
  values: [Date | null, Date] | [Date, Date | null];
};

/**
 * Represents an aggregation function applied to a column in a dataset.
 *
 * @template Tf Type of the fact (numeric) column.
 * @template Ta Type of the any column (can be category or fact).
 *
 * - `FactColumnAggregation<Tf>`: Aggregates numeric data using functions available in FACT_COLUMN_AGGREGATION_FUNCTIONS.
 * - `AnyColumnAggregation<Ta>`: Aggregates any type of data (category or fact) using COUNT or COUNT_DISTINCT.
 */
export type Aggregation<Ta, Tf> = AnyColumnAggregation<Ta> | FactColumnAggregation<Tf>;

export const FACT_COLUMN_AGGREGATION_FUNCTIONS = [
  'COUNT',
  'COUNT_DISTINCT',
  'SUM',
  'AVG',
  'MEDIAN',
  'MIN',
  'MAX',
] as const;

export type FactColumnAggregationFunction = (typeof FACT_COLUMN_AGGREGATION_FUNCTIONS)[number];

export type FactColumnAggregation<Tf> = {
  column_name: Tf;
  function: FactColumnAggregationFunction;
  alias: string;
};

export const ANY_COLUMN_AGGREGATION_FUNCTIONS = ['COUNT', 'COUNT_DISTINCT'] as const;

export type AnyColumnAggregationFunction = (typeof ANY_COLUMN_AGGREGATION_FUNCTIONS)[number];

export type AnyColumnAggregation<Ta> = {
  column_name: Ta;
  function: AnyColumnAggregationFunction;
  alias: string;
};

/**
 * Represents a selection of columns in a dataset.
 *
 * - `Select`: Contains the selected column name and an optional alias.
 */
export type Select<Ta> = {
  column_name: Ta;
  alias?: string;
};

/**
 * Represents a sorting order for a column in a dataset.
 *
 * - `OrderBy`: Contains the column name and the direction of sorting (ASC or DESC).
 */
export type OrderBy = {
  column_name: string;
  direction: OrderByDirection;
};

export const ORDER_BY_DIRECTION = ['ASC', 'DESC'] as const;

export type OrderByDirection = (typeof ORDER_BY_DIRECTION)[number];

/**
 * Represents pagination information for a dataset.
 */
export type Pagination = {
  offset: number;
  limit: number;
};
