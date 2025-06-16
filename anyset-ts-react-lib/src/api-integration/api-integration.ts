import axios, { AxiosInstance } from 'axios';

import { FilterOptionResponseDTO, QueryRequestDTO, QueryResponseDTO } from './types';

export type ApiIntegrationConfig = {
  baseURL: string;
  slug: string;
  version: number;
};

/**
 * Provides integration with a RESTful API using Axios, allowing execution of typed queries and retrieval of responses.
 *
 * @typeParam Ta - The type for the 'a' parameter in the query DTO.
 * @typeParam Tc - The type for the 'c' parameter in the query DTO.
 * @typeParam Td - The type for the 'd' parameter in the query DTO.
 * @typeParam Tf - The type for the 'f' parameter in the query DTO.
 * @typeParam T - The type of the query request DTO, extending {@link QueryRequestDTO}.
 *
 * @param {ApiIntegrationConfig} config - Configuration object containing base URL, slug, and version for the API.
 *
 * @remarks
 * This class is designed to facilitate communication with a versioned API endpoint,
 * automatically configuring the base URL and headers for JSON requests.
 *
 * @example
 * ```typescript
 * const api = new ApiIntegration({ baseURL: 'https://api.example.com', slug: 'dataset', version: 1 });
 * const response = await api.query({ ... });
 * ```
 */
export class ApiIntegration<
  Ta = string,
  Tc = string,
  Td = string,
  Tf = string,
  T extends QueryRequestDTO<Ta, Tc, Td, Tf> = QueryRequestDTO<Ta, Tc, Td, Tf>,
> {
  private readonly client: AxiosInstance;

  public constructor({ baseURL, slug, version }: ApiIntegrationConfig) {
    this.client = axios.create({
      baseURL: `${baseURL}/${slug}/${version}`,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Executes a query against the API.
   *
   * @param query The query to execute structured as a {@link QueryRequestDTO}.
   * @returns A promise that resolves to a {@link QueryResponseDTO}.
   */
  public async query(query: T): Promise<QueryResponseDTO> {
    const { status, statusText, data } = await this.client.post<QueryResponseDTO>('/query', query);

    if (!/^2\d{2}$/.test(status.toString())) throw new Error(`QueryError ${status} ${statusText}`);

    return data;
  }

  /**
   * Retrieves filter options for use in frontend filter components.
   *
   * @returns A promise that resolves to a {@link FilterOptionResponseDTO}.
   */
  public async fetchFilterOptions(): Promise<FilterOptionResponseDTO> {
    const { status, statusText, data } =
      await this.client.get<FilterOptionResponseDTO>('/filter-options');

    if (!/^2\d{2}$/.test(status.toString()))
      throw new Error(`FetchFilterOptionsError ${status} ${statusText}`);

    return data;
  }
}
