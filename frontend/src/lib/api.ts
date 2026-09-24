/**
 * NIRMAYA Frontend API Client
 * Typed service layer for communicating with the FastAPI backend.
 */

export interface APIResponseEnvelope<T = unknown> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  request_id?: string;
}

export interface ErrorDetail {
  location?: string;
  message: string;
  error_type?: string;
}

export interface ErrorResponseEnvelope {
  success: boolean;
  error_code: string;
  message: string;
  details: ErrorDetail[];
  timestamp: string;
  request_id?: string;
}

export class APIError extends Error {
  errorCode: string;
  status: number;
  details: ErrorDetail[];
  requestId?: string;

  constructor(errorData: ErrorResponseEnvelope, status: number) {
    super(errorData.message || "An unexpected error occurred");
    this.name = "APIError";
    this.errorCode = errorData.error_code || "UNKNOWN_ERROR";
    this.status = status;
    this.details = errorData.details || [];
    this.requestId = errorData.request_id;
  }
}

export interface RequestOptions extends RequestInit {
  token?: string;
  params?: Record<string, string | number | boolean | undefined>;
}

class NIRMAYAAPIClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = (
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    ).replace(/\/$/, "");
  }

  private buildUrl(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined>
  ): string {
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = new URL(`${this.baseUrl}${cleanEndpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return url.toString();
  }

  private getAuthToken(overrideToken?: string): string | null {
    if (overrideToken) return overrideToken;
    if (typeof window !== "undefined") {
      try {
        return localStorage.getItem("nirmaya_token");
      } catch {
        return null;
      }
    }
    return null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { token, params, headers = {}, ...restOptions } = options;
    const url = this.buildUrl(endpoint, params);
    const resolvedToken = this.getAuthToken(token);

    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(headers as Record<string, string>),
    };

    if (resolvedToken) {
      requestHeaders["Authorization"] = `Bearer ${resolvedToken}`;
    }

    const response = await fetch(url, {
      headers: requestHeaders,
      ...restOptions,
    });

    if (!response.ok) {
      let errorPayload: ErrorResponseEnvelope;
      try {
        errorPayload = await response.json();
      } catch {
        errorPayload = {
          success: false,
          error_code: `HTTP_${response.status}`,
          message: response.statusText || "Request failed",
          details: [],
          timestamp: new Date().toISOString(),
        };
      }
      throw new APIError(errorPayload, response.status);
    }

    const json = (await response.json()) as Record<string, unknown>;
    // If it is a paginated response containing pagination metadata, return the full envelope
    if ("pagination" in json) {
      return json as unknown as T;
    }
    // If wrapped in standard APIResponse, return the inner data
    return json.data !== undefined ? (json.data as T) : (json as unknown as T);
  }

  public get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { method: "GET", ...options });
  }

  public post<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }

  public put<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }

  public delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE", ...options });
  }

  /**
   * Healthcheck probe for validating backend connectivity.
   */
  public async checkHealth() {
    return this.get<{
      status: string;
      project: string;
      version: string;
      standards: {
        fhir_version: string;
        abdm_sandbox: boolean;
      };
    }>("/api/v1/health");
  }

  /**
   * Auth API helpers
   */
  public async getMe(token?: string) {
    return this.get<Record<string, unknown>>("/api/v1/auth/me", { token });
  }

  public async verifyToken(token: string) {
    return this.post<{ valid: boolean; claims?: Record<string, unknown> }>(
      "/api/v1/auth/verify",
      { token }
    );
  }

  public async issueTestToken(payload: {
    email: string;
    role: string;
    sub?: string;
    expires_minutes?: number;
  }) {
    return this.post<{ access_token: string }>(
      "/api/v1/auth/test-token",
      payload
    );
  }
}

export const apiClient = new NIRMAYAAPIClient();
