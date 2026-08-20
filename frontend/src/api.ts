export const API_BASE = "";

export type ProviderInfo = {
  provider: string;
  base_url: string;
  embedding_model: string;
  llm_model: string;
  embedding_max_batch_size: number;
};

export type JobStatus = {
  id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  message: string;
  logs: string[];
  error?: string | null;
  created_at: string;
  updated_at: string;
  download_ready: boolean;
};

export async function getProvider(): Promise<ProviderInfo> {
  const response = await fetch(`${API_BASE}/api/provider`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function testApiKey(apiKey: string) {
  const response = await fetch(`${API_BASE}/api/config/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey })
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function createJob(form: FormData): Promise<JobStatus> {
  const response = await fetch(`${API_BASE}/api/jobs`, {
    method: "POST",
    body: form
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function cancelJob(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}/cancel`, {
    method: "POST"
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export function downloadUrl(jobId: string) {
  return `${API_BASE}/api/jobs/${jobId}/download`;
}

async function readError(response: Response) {
  try {
    const data = await response.json();
    return data.detail || response.statusText;
  } catch {
    return response.statusText;
  }
}
