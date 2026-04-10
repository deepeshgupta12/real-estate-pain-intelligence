export type ApiHealthResponse = {
  status: string;
  app_name: string;
  environment: string;
  version: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchApiHealth(): Promise<ApiHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch API health");
  }

  return response.json();
}