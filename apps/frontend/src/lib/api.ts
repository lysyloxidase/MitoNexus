import type { AnalysisReportPayload, ReportVisualizationPayload } from "@mitonexus/shared-types";

export async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function fetchReport(reportId: string): Promise<AnalysisReportPayload> {
  return fetchJson<AnalysisReportPayload>(`/api/v1/report/${reportId}`);
}

export function fetchVisualizationData(reportId: string): Promise<ReportVisualizationPayload> {
  return fetchJson<ReportVisualizationPayload>(`/api/v1/report/${reportId}/visualization`);
}
