const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const DEFAULT_ADMIN_KEY = import.meta.env.VITE_ADMIN_API_KEY ?? "dev-admin-key";

export type Platform = "zomato" | "swiggy" | "zepto" | "blinkit";
export type CoverageTier = "basic" | "standard" | "premium";

export type WorkerPayload = {
  phone: string;
  name: string;
  platform: Platform;
  zone_id: string;
  device_fingerprint?: string | null;
  avg_weekly_earnings: number;
  tenure_days: number;
  kyc_verified: boolean;
};

export type Worker = WorkerPayload & {
  id: string;
  trust_score: number;
  payout_method: "upi" | "bank_transfer" | null;
  payout_upi_id: string | null;
  payout_bank_account_name: string | null;
  payout_bank_account_number: string | null;
  payout_bank_ifsc: string | null;
  payout_contact_name: string | null;
  payout_contact_phone: string | null;
  payout_profile_status: "missing" | "pending" | "verified" | "rejected";
  payout_profile_review_notes: string | null;
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

export type PolicyCheckout = {
  checkout_required: boolean;
  key_id: string;
  order_id: string;
  amount: number;
  currency: string;
  worker_id: string;
  coverage_tier: CoverageTier;
  notes_token: string;
};

export type Claim = {
  id: string;
  policy_id: string;
  worker_id: string;
  disruption_event_id: string;
  amount: number;
  status: "auto_approved" | "manual_review" | "rejected" | "paid";
  fraud_score: number;
  trust_score_at_claim: number;
  created_at: string;
};

export type Payout = {
  id: string;
  claim_id: string;
  worker_id: string;
  amount: number;
  payment_method: "upi" | "bank_transfer";
  razorpay_payment_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  processed_at: string;
};

export type DisruptionEvent = {
  id: string;
  event_type: string;
  zone_id: string;
  severity: number;
  started_at: string;
  ended_at: string | null;
  weather_api_raw: Record<string, unknown> | null;
  verified: boolean;
};

export type OtpRequestResponse = {
  challenge_id: string;
  expires_in_minutes: number;
  delivery_mode: string;
  mock_otp_code: string | null;
};

export type AuthSessionResponse = {
  access_token: string;
  token_type: string;
  worker: Worker;
};

export type FraudLog = {
  id: string;
  worker_id: string;
  claim_id: string;
  fraud_type: string;
  fraud_score: number;
  signals: Record<string, unknown>;
  action_taken: "auto_approved" | "manual_review" | "rejected" | "paid";
  created_at: string;
};

export type PlausibilitySignal = {
  code: string;
  description: string;
  impact: "positive" | "negative";
  weight: number;
  evidence: string;
};

export type PlausibilityAssessment = {
  id: string;
  claim_id: string;
  plausibility_score: number;
  risk_tier: "low" | "medium" | "high";
  routing_decision: "approve" | "manual_review" | "reject";
  signals: PlausibilitySignal[];
  assessed_at: string;
};

export type AdminOpsWeatherSyncResult = {
  id: string;
  event_type: string;
  zone_id: string;
  severity: number;
  started_at: string;
  ended_at: string | null;
  weather_api_raw: Record<string, unknown> | null;
  verified: boolean;
};

export type AdminOpsPolicyExpiryResult = {
  expired_policies: number;
};

export type AdminPayoutProfile = {
  id: string;
  name: string;
  phone: string;
  payout_method: "upi" | "bank_transfer" | null;
  payout_upi_id: string | null;
  payout_bank_account_name: string | null;
  payout_bank_account_number: string | null;
  payout_bank_ifsc: string | null;
  payout_contact_name: string | null;
  payout_contact_phone: string | null;
  payout_profile_status: "missing" | "pending" | "verified" | "rejected";
  payout_profile_review_notes: string | null;
  created_at: string;
};

export type AdminSession = {
  access_token: string;
  token_type: string;
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

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
    });
  } catch {
    throw new Error(`Could not connect to the backend at ${API_BASE_URL}. Make sure the API server is running.`);
  }

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

export function createPolicy(
  workerId: string,
  coverageTier: CoverageTier,
  payment?: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  },
): Promise<Policy> {
  return request<Policy>("/policies", {
    method: "POST",
    body: JSON.stringify({ worker_id: workerId, coverage_tier: coverageTier, payment: payment ?? null }),
  });
}

export function createPolicyCheckout(workerId: string, coverageTier: CoverageTier): Promise<PolicyCheckout> {
  return request<PolicyCheckout>("/policies/checkout", {
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

export function requestOtp(phone: string): Promise<OtpRequestResponse> {
  return request<OtpRequestResponse>("/auth/request-otp", {
    method: "POST",
    body: JSON.stringify({ phone }),
  });
}

export function verifyOtp(phone: string, otpCode: string): Promise<AuthSessionResponse> {
  return request<AuthSessionResponse>("/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({ phone, otp_code: otpCode }),
  });
}

export function getCurrentWorker(token: string): Promise<Worker> {
  return request<Worker>("/workers/me", {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function updatePayoutProfile(
  token: string,
  payload: {
    payout_method: "upi" | "bank_transfer";
    payout_upi_id?: string | null;
    payout_bank_account_name?: string | null;
    payout_bank_account_number?: string | null;
    payout_bank_ifsc?: string | null;
    payout_contact_name: string;
    payout_contact_phone: string;
  },
): Promise<Worker> {
  return request<Worker>("/workers/me/payout-profile", {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function listClaims(workerId: string): Promise<Claim[]> {
  return request<Claim[]>("/claims", {
    method: "GET",
    searchParams: { worker_id: workerId },
  });
}

export function listPayouts(workerId: string): Promise<Payout[]> {
  return request<Payout[]>("/claims/payouts", {
    method: "GET",
    searchParams: { worker_id: workerId },
  });
}

export function listDisruptions(): Promise<DisruptionEvent[]> {
  return request<DisruptionEvent[]>("/disruptions/active", { method: "GET" });
}

export function adminLogin(adminKey: string): Promise<AdminSession> {
  return request<AdminSession>("/auth/admin/login", {
    method: "POST",
    body: JSON.stringify({ admin_key: adminKey }),
  });
}

export function listAdminClaims(adminToken: string): Promise<Claim[]> {
  return request<Claim[]>("/admin/claims", {
    method: "GET",
    headers: { Authorization: `Bearer ${adminToken}` },
  });
}

export function approveAdminClaim(claimId: string, adminToken: string): Promise<Payout> {
  return request<Payout>(`/admin/claims/${claimId}/approve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${adminToken}` },
  });
}

export function rejectAdminClaim(claimId: string, adminToken: string): Promise<Claim> {
  return request<Claim>(`/admin/claims/${claimId}/reject`, {
    method: "POST",
    headers: { Authorization: `Bearer ${adminToken}` },
  });
}

export function listFraudLogs(adminToken: string): Promise<FraudLog[]> {
  return request<FraudLog[]>("/admin/fraud-logs", {
    method: "GET",
    headers: { Authorization: `Bearer ${adminToken}` },
  });
}

export function listPlausibilityAssessments(adminToken: string): Promise<PlausibilityAssessment[]> {
  return request<PlausibilityAssessment[]>("/admin/plausibility-assessments", {
    method: "GET",
    headers: { Authorization: `Bearer ${adminToken}` },
  });
}

export function listAdminPayoutProfiles(adminToken: string): Promise<AdminPayoutProfile[]> {
  return request<AdminPayoutProfile[]>("/admin/payout-profiles", {
    method: "GET",
    headers: { Authorization: `Bearer ${adminToken}` },
  });
}

export function approveAdminPayoutProfile(workerId: string, adminToken: string): Promise<AdminPayoutProfile> {
  return request<AdminPayoutProfile>(`/admin/payout-profiles/${workerId}/approve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${adminToken}` },
    body: JSON.stringify({ notes: "Verified from admin console" }),
  });
}

export function rejectAdminPayoutProfile(workerId: string, adminToken: string): Promise<AdminPayoutProfile> {
  return request<AdminPayoutProfile>(`/admin/payout-profiles/${workerId}/reject`, {
    method: "POST",
    headers: { Authorization: `Bearer ${adminToken}` },
    body: JSON.stringify({ notes: "Rejected from admin console" }),
  });
}

export function syncWeather(adminToken: string): Promise<AdminOpsWeatherSyncResult[]> {
  return request<AdminOpsWeatherSyncResult[]>("/internal/weather/sync", {
    method: "POST",
    headers: { Authorization: `Bearer ${adminToken}` },
  });
}

export function expirePolicies(adminToken: string): Promise<AdminOpsPolicyExpiryResult> {
  return request<AdminOpsPolicyExpiryResult>("/internal/policies/expire", {
    method: "POST",
    headers: { Authorization: `Bearer ${adminToken}` },
  });
}
