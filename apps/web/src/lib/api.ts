export type ApiHealthResponse = {
  status: string;
  app_name: string;
  environment: string;
  version: string;
  api_prefix: string;
};

export type ApiMetaResponse = {
  app_name: string;
  version: string;
  environment: string;
  api_prefix: string;
  frontend_url: string;
  docs_url: string;
  openapi_url: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}`);
  }

  return response.json();
}

export async function fetchApiHealth(): Promise<ApiHealthResponse> {
  return fetchJson<ApiHealthResponse>("/api/v1/health");
}

export async function fetchApiMeta(): Promise<ApiMetaResponse> {
  return fetchJson<ApiMetaResponse>("/api/v1/meta");
}