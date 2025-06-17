import axios from 'axios';

import { ApiIntegration } from './api-integration';
import { QueryRequestDTO } from './types';

type QueryRequestDTO_Test = QueryRequestDTO<string, string, string, string>;

describe('ApiIntegration', () => {
  const baseURL = 'https://api.example.com';
  const slug = 'dataset';
  const version = 1;

  const query: QueryRequestDTO_Test = {
    table_name: 'test_table',
    select: [{ column_name: 'column1' }],
    filters: [],
    pagination: { offset: 0, limit: 10 },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create an instance with correct configuration', () => {
    jest.spyOn(axios, 'create').mockReturnValue('axios-instance' as any);

    const api = new ApiIntegration<string, string, string, string>({ baseURL, slug, version });

    expect(api).toBeInstanceOf(ApiIntegration);

    expect(axios.create).toHaveBeenCalledWith({
      baseURL: `${baseURL}/${slug}/${version}`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    expect(api['client']).toBe('axios-instance');
  });

  it('should execute a query', async () => {
    const mockPost = jest
      .fn()
      .mockResolvedValue({ data: { results: [] }, status: 200, statusText: 'OK' });

    jest.spyOn(axios, 'create').mockReturnValue({
      post: mockPost,
      get: jest.fn(),
    } as any);

    const api = new ApiIntegration<string, string, string, string>({ baseURL, slug, version });

    const result = await api.query(query);

    expect(mockPost).toHaveBeenCalledWith('/query', query);

    expect(result).toEqual({ results: [] });
  });

  it('should throw an error on non-2xx response for query', async () => {
    const mockPost = jest.fn().mockResolvedValue({ status: 400, statusText: 'BAD REQUEST' });

    jest.spyOn(axios, 'create').mockReturnValue({
      post: mockPost,
      get: jest.fn(),
    } as any);

    const api = new ApiIntegration<string, string, string, string>({ baseURL, slug, version });

    await expect(api.query(query)).rejects.toThrow('QueryError 400 BAD REQUEST');
  });

  it('should retrieve filter-options', async () => {
    const mockGet = jest
      .fn()
      .mockResolvedValue({ data: { options: [] }, status: 200, statusText: 'OK' });

    jest.spyOn(axios, 'create').mockReturnValue({
      post: jest.fn(),
      get: mockGet,
    } as any);

    const api = new ApiIntegration<string, string, string, string>({ baseURL, slug, version });

    const result = await api.getFilterOptions();

    expect(mockGet).toHaveBeenCalledWith('/filter-options');

    expect(result).toEqual({ options: [] });
  });

  it('should throw an error on non-2xx response for filter-options', async () => {
    const mockGet = jest.fn().mockResolvedValue({ status: 404, statusText: 'NOT FOUND' });

    jest.spyOn(axios, 'create').mockReturnValue({
      post: jest.fn(),
      get: mockGet,
    } as any);

    const api = new ApiIntegration<string, string, string, string>({ baseURL, slug, version });

    await expect(api.getFilterOptions()).rejects.toThrow('FilterOptionsError 404 NOT FOUND');
  });
});
