import { startTransition, useEffect, useMemo, useState } from "react";

import {
  createPolicy,
  getPremiumQuote,
  listPolicies,
  registerWorker,
  type CoverageTier,
  type Platform,
  type Policy,
  type QuoteResponse,
  type Worker,
} from "./lib/api";

const platformOptions: { value: Platform; label: string; accent: string }[] = [
  { value: "zomato", label: "Zomato", accent: "Crimson" },
  { value: "swiggy", label: "Swiggy", accent: "Orange" },
  { value: "zepto", label: "Zepto", accent: "Magenta" },
  { value: "blinkit", label: "Blinkit", accent: "Yellow" },
];

const cityZones = {
  Chennai: [
    { label: "Zone 4 · Flood-prone corridors", value: "chennai_zone_4" },
    { label: "Zone 2 · Core delivery cluster", value: "chennai_zone_2" },
  ],
  Mumbai: [
    { label: "Zone 2 · Western suburban routes", value: "mumbai_zone_2" },
    { label: "Zone 5 · High rain exposure belt", value: "mumbai_zone_5" },
  ],
  Bengaluru: [
    { label: "Zone 3 · Peak order tech corridor", value: "bengaluru_zone_3" },
    { label: "Zone 6 · Outer ring delivery arc", value: "bengaluru_zone_6" },
  ],
  Delhi: [
    { label: "Zone 1 · Central operations block", value: "delhi_zone_1" },
    { label: "Zone 7 · High AQI alert pocket", value: "delhi_zone_7" },
  ],
} as const;

const tierCards: { id: CoverageTier; title: string; helper: string }[] = [
  { id: "basic", title: "Basic", helper: "Rain + flood cover" },
  { id: "standard", title: "Standard", helper: "Best for most delivery partners" },
  { id: "premium", title: "Premium", helper: "All six disruption triggers" },
];

const trustMessages = [
  "No paperwork during bad-weather shifts",
  "Weekly pricing that feels like recharge money",
  "Automatic payouts when the city shuts down",
];

type FormState = {
  name: string;
  phone: string;
  platform: Platform;
  city: keyof typeof cityZones;
  zoneId: string;
  avgWeeklyEarnings: string;
  tenureDays: string;
  kycVerified: boolean;
};

const initialFormState: FormState = {
  name: "",
  phone: "",
  platform: "zomato",
  city: "Chennai",
  zoneId: "chennai_zone_4",
  avgWeeklyEarnings: "3500",
  tenureDays: "120",
  kycVerified: true,
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export default function App() {
  const [form, setForm] = useState<FormState>(initialFormState);
  const [selectedTier, setSelectedTier] = useState<CoverageTier>("standard");
  const [worker, setWorker] = useState<Worker | null>(null);
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [status, setStatus] = useState("Fill in your delivery profile to see this week’s protection price.");
  const [error, setError] = useState<string | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [isFetchingQuote, setIsFetchingQuote] = useState(false);
  const [isBuying, setIsBuying] = useState(false);

  const currentZones = cityZones[form.city];

  const canQuote = useMemo(
    () => form.name.trim().length >= 2 && /^\d{10}$/.test(form.phone) && Number(form.avgWeeklyEarnings) > 0,
    [form],
  );

  useEffect(() => {
    if (!currentZones.some((zone) => zone.value === form.zoneId)) {
      setForm((current) => ({ ...current, zoneId: currentZones[0].value }));
    }
  }, [currentZones, form.zoneId]);

  async function fetchQuote() {
    if (!canQuote) {
      setError("Enter name, 10-digit phone number, and weekly earnings first.");
      return;
    }

    setError(null);
    setIsFetchingQuote(true);
    try {
      const nextQuote = await getPremiumQuote({
        coverage_tier: selectedTier,
        platform: form.platform,
        city: form.city,
        zone_id: form.zoneId,
        avg_weekly_earnings: Number(form.avgWeeklyEarnings),
        tenure_days: Number(form.tenureDays) || 0,
        trust_score: worker?.trust_score ?? 75,
      });
      setQuote(nextQuote);
      setStatus(`Your ${selectedTier} plan is ready. Protection starts ${formatDate(nextQuote.valid_from)}.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not fetch quote.");
    } finally {
      setIsFetchingQuote(false);
    }
  }

  async function handleRegister() {
    setError(null);
    setIsRegistering(true);
    try {
      const nextWorker = await registerWorker({
        name: form.name.trim(),
        phone: form.phone,
        platform: form.platform,
        zone_id: form.zoneId,
        avg_weekly_earnings: Number(form.avgWeeklyEarnings),
        tenure_days: Number(form.tenureDays) || 0,
        kyc_verified: form.kycVerified,
      });
      setWorker(nextWorker);
      setStatus(`Profile created for ${nextWorker.name}. You can now lock this week’s cover.`);
      const nextQuote = await getPremiumQuote({
        coverage_tier: selectedTier,
        platform: nextWorker.platform,
        city: form.city,
        zone_id: nextWorker.zone_id,
        avg_weekly_earnings: Number(nextWorker.avg_weekly_earnings),
        tenure_days: nextWorker.tenure_days,
        trust_score: Number(nextWorker.trust_score),
      });
      setQuote(nextQuote);
      const nextPolicies = await listPolicies(nextWorker.id);
      startTransition(() => {
        setPolicies(nextPolicies);
      });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not register worker.");
    } finally {
      setIsRegistering(false);
    }
  }

  async function handleBuyPolicy() {
    if (!worker) {
      setError("Create your worker profile first.");
      return;
    }

    setError(null);
    setIsBuying(true);
    try {
      const policy = await createPolicy(worker.id, selectedTier);
      const nextPolicies = await listPolicies(worker.id);
      startTransition(() => {
        setPolicies(nextPolicies);
      });
      setStatus(
        `Protection active. ${formatCurrency(policy.coverage_amount)} cover is live until ${formatDate(policy.end_date)}.`,
      );
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not buy policy.");
    } finally {
      setIsBuying(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="top-banner">
        <span>Guidewire DEVTrails 2026</span>
        <span>Worker app demo</span>
        <span>Built for delivery riders</span>
      </section>

      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">GigShield</p>
          <h1>Income protection for the shifts that get washed out.</h1>
          <p className="hero-text">
            A simple worker app for Zomato and Swiggy riders. Check your weekly premium, register
            once, and lock cover before rain, flood, heat, or outages cut your earnings.
          </p>

          <div className="trust-stack">
            {trustMessages.map((message) => (
              <div className="trust-pill" key={message}>
                {message}
              </div>
            ))}
          </div>

          <div className="stat-band">
            <article>
              <span>Weekly price</span>
              <strong>Rs 29-89</strong>
            </article>
            <article>
              <span>Claim steps</span>
              <strong>Zero</strong>
            </article>
            <article>
              <span>Payout promise</span>
              <strong>Minutes</strong>
            </article>
          </div>
        </div>

        <div className="phone-stage">
          <div className="phone-card">
            <p className="eyebrow">Live status</p>
            <h2>{status}</h2>
            <div className="event-strip">
              <span>Heavy Rain</span>
              <span>Flood Alert</span>
              <span>Heatwave</span>
            </div>
            {quote ? (
              <div className="quote-glance">
                <span>This week</span>
                <strong>{formatCurrency(quote.weekly_premium)}</strong>
                <small>Cover up to {formatCurrency(quote.coverage_amount)}</small>
              </div>
            ) : (
              <div className="quote-glance muted">
                <span>Live quote</span>
                <strong>Ready in 1 tap</strong>
                <small>Enter rider details below</small>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="workspace-grid">
        <div className="form-panel">
          <div className="section-head">
            <p className="eyebrow">1. Delivery profile</p>
            <h3>Set up your weekly protection</h3>
          </div>

          <div className="platform-row">
            {platformOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                className={`platform-chip ${form.platform === option.value ? "is-active" : ""}`}
                onClick={() => setForm((current) => ({ ...current, platform: option.value }))}
              >
                <span>{option.label}</span>
                <small>{option.accent}</small>
              </button>
            ))}
          </div>

          <div className="field-grid">
            <label>
              <span>Full name</span>
              <input
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                placeholder="Ravi Kumar"
              />
            </label>

            <label>
              <span>Phone number</span>
              <input
                inputMode="numeric"
                maxLength={10}
                value={form.phone}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    phone: event.target.value.replace(/\D/g, "").slice(0, 10),
                  }))
                }
                placeholder="9876543210"
              />
            </label>

            <label>
              <span>City</span>
              <select
                value={form.city}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    city: event.target.value as keyof typeof cityZones,
                    zoneId: cityZones[event.target.value as keyof typeof cityZones][0].value,
                  }))
                }
              >
                {Object.keys(cityZones).map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Delivery zone</span>
              <select
                value={form.zoneId}
                onChange={(event) => setForm((current) => ({ ...current, zoneId: event.target.value }))}
              >
                {currentZones.map((zone) => (
                  <option key={zone.value} value={zone.value}>
                    {zone.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Average weekly earnings</span>
              <input
                inputMode="numeric"
                value={form.avgWeeklyEarnings}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    avgWeeklyEarnings: event.target.value.replace(/[^\d.]/g, ""),
                  }))
                }
                placeholder="3500"
              />
            </label>

            <label>
              <span>Tenure on platform (days)</span>
              <input
                inputMode="numeric"
                value={form.tenureDays}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    tenureDays: event.target.value.replace(/\D/g, ""),
                  }))
                }
                placeholder="120"
              />
            </label>
          </div>

          <label className="toggle-row">
            <input
              type="checkbox"
              checked={form.kycVerified}
              onChange={(event) => setForm((current) => ({ ...current, kycVerified: event.target.checked }))}
            />
            <span>KYC already completed on the platform</span>
          </label>

          <div className="action-row">
            <button type="button" className="secondary-action" onClick={fetchQuote} disabled={isFetchingQuote}>
              {isFetchingQuote ? "Checking price..." : "Check weekly price"}
            </button>
            <button type="button" className="primary-action" onClick={handleRegister} disabled={isRegistering}>
              {isRegistering ? "Creating profile..." : worker ? "Profile created" : "Create profile"}
            </button>
          </div>

          {error ? <p className="inline-error">{error}</p> : null}
        </div>

        <div className="side-stack">
          <div className="quote-panel">
            <div className="section-head">
              <p className="eyebrow">2. Weekly plan</p>
              <h3>Pick cover that matches your route risk</h3>
            </div>

            <div className="tier-grid">
              {tierCards.map((tier) => (
                <button
                  key={tier.id}
                  type="button"
                  className={`tier-card ${selectedTier === tier.id ? "is-selected" : ""}`}
                  onClick={() => setSelectedTier(tier.id)}
                >
                  <span>{tier.title}</span>
                  <strong>{tier.helper}</strong>
                </button>
              ))}
            </div>

            {quote ? (
              <div className="quote-panel-card">
                <div className="quote-price">
                  <span>Weekly premium</span>
                  <strong>{formatCurrency(quote.weekly_premium)}</strong>
                </div>
                <div className="quote-meta">
                  <article>
                    <span>Coverage</span>
                    <strong>{formatCurrency(quote.coverage_amount)}</strong>
                  </article>
                  <article>
                    <span>Risk score</span>
                    <strong>{quote.risk_score}</strong>
                  </article>
                  <article>
                    <span>Valid till</span>
                    <strong>{formatDate(quote.valid_to)}</strong>
                  </article>
                </div>
                <div className="trigger-list">
                  {quote.triggers.map((trigger) => (
                    <span key={trigger}>{trigger}</span>
                  ))}
                </div>
                <button type="button" className="primary-action full-width" onClick={handleBuyPolicy} disabled={isBuying}>
                  {isBuying ? "Activating cover..." : "Buy this weekly cover"}
                </button>
              </div>
            ) : (
              <div className="empty-card">
                <h4>Your price will appear here</h4>
                <p>Choose a plan and tap “Check weekly price” to see live cover amount and triggers.</p>
              </div>
            )}
          </div>

          <div className="ledger-panel">
            <div className="section-head">
              <p className="eyebrow">3. Protection wallet</p>
              <h3>What the worker sees after signup</h3>
            </div>

            <div className="worker-glance">
              <div>
                <span>Worker</span>
                <strong>{worker?.name ?? "Not registered yet"}</strong>
              </div>
              <div>
                <span>Trust score</span>
                <strong>{worker ? Number(worker.trust_score).toFixed(0) : "--"}</strong>
              </div>
            </div>

            {policies.length > 0 ? (
              <div className="policy-list">
                {policies.map((policy) => (
                  <article className="policy-card" key={policy.id}>
                    <div>
                      <span className="policy-tier">{policy.coverage_tier}</span>
                      <strong>{formatCurrency(policy.coverage_amount)} cover</strong>
                    </div>
                    <div>
                      <span>Status</span>
                      <strong>{policy.status}</strong>
                    </div>
                    <div>
                      <span>Window</span>
                      <strong>
                        {formatDate(policy.start_date)} - {formatDate(policy.end_date)}
                      </strong>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-card compact">
                <h4>No active weekly cover yet</h4>
                <p>Once purchased, the worker can quickly confirm cover, amount, and protection window here.</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
