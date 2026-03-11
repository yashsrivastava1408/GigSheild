const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type Platform = "zomato" | "swiggy" | "zepto" | "blinkit";
export type CoverageTier = "basic" | "standard" | "premium";

export type WorkerPayload = {
  phone: string;
  name: string;
  platform: Platform;
  zone_id: string;
  avg_weekly_earnings: number;
  tenure_days: number;
  kyc_verified: boolean;
};

export type Worker = WorkerPayload & {
  id: string;
  trust_score: number;
  created_at: string;
};

export type QuoteParams = {
  coverage_tier: CoverageTier;
  platform: Platform;
  city: string;
  zone_id: string;
  avg_weekly_earnings: number;
  tenure_days: number;
  trust_score: number;
};

export type QuoteResponse = {
  coverage_tier: CoverageTier;
  weekly_premium: number;
  coverage_amount: number;
  risk_score: number;
  risk_multiplier: number;
  valid_from: string;
  valid_to: string;
  triggers: string[];
  quote_factors: Record<string, string | number>;
};

export type Policy = {
  id: string;
  worker_id: string;
  coverage_tier: CoverageTier;
  weekly_premium: number;
  coverage_amount: number;
  start_date: string;
  end_date: string;
  status: "active" | "expired" | "cancelled";
  created_at: string;
  triggers: string[];
  risk_score: number | null;
  risk_multiplier: number | null;
};

type RequestOptions = RequestInit & {
  searchParams?: Record<string, string | number>;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (options.searchParams) {
    Object.entries(options.searchParams).forEach(([key, value]) =>
      url.searchParams.set(key, String(value)),
    );
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const body = (await response.json()) as { detail?: string | { msg?: string }[] };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        message = body.detail[0].msg;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export function registerWorker(payload: WorkerPayload): Promise<Worker> {
  return request<Worker>("/workers/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getPremiumQuote(params: QuoteParams): Promise<QuoteResponse> {
  return request<QuoteResponse>("/premium/quote", {
    method: "GET",
    searchParams: params,
  });
}

export function createPolicy(workerId: string, coverageTier: CoverageTier): Promise<Policy> {
  return request<Policy>("/policies", {
    method: "POST",
    body: JSON.stringify({ worker_id: workerId, coverage_tier: coverageTier }),
  });
}

export function listPolicies(workerId: string): Promise<Policy[]> {
  return request<Policy[]>("/policies", {
    method: "GET",
    searchParams: { worker_id: workerId },
  });
}
