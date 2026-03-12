import type { Claim, CoverageTier, DisruptionEvent, Policy, Payout, QuoteResponse, Worker } from "../lib/api";
import { tierCards } from "../lib/constants";
import { formatCurrency, formatDate, prettyZone } from "../lib/format";

export function WorkerDashboard({
  worker,
  selectedTier,
  setSelectedTier,
  activeTab,
  setActiveTab,
  quote,
  policies,
  claims,
  payouts,
  disruptions,
  isFetchingQuote,
  isBuying,
  onQuote,
  onBuy,
  onLogout,
  onRefresh,
}: {
  worker: Worker;
  selectedTier: CoverageTier;
  setSelectedTier: (tier: CoverageTier) => void;
  activeTab: "overview" | "history";
  setActiveTab: (tab: "overview" | "history") => void;
  quote: QuoteResponse | null;
  policies: Policy[];
  claims: Claim[];
  payouts: Payout[];
  disruptions: DisruptionEvent[];
  isFetchingQuote: boolean;
  isBuying: boolean;
  onQuote: () => void;
  onBuy: () => void;
  onLogout: () => void;
  onRefresh: () => void;
}) {
  const activePolicy = policies.find((policy) => policy.status === "active") ?? policies[0] ?? null;
  const localDisruption = disruptions.find((event) => event.zone_id === worker.zone_id) ?? null;
  const workerTimeline = [
    ...policies.map((policy) => ({
      id: `policy-${policy.id}`,
      title: `${policy.coverage_tier} policy ${policy.status}`,
      timestamp: policy.created_at,
      meta: formatDate(policy.created_at),
    })),
    ...claims.map((claim) => ({
      id: `claim-${claim.id}`,
      title: `Claim ${claim.status}`,
      timestamp: claim.created_at,
      meta: `${formatCurrency(claim.amount)} · ${formatDate(claim.created_at)}`,
    })),
    ...payouts.map((payout) => ({
      id: `payout-${payout.id}`,
      title: `Payout ${payout.status}`,
      timestamp: payout.processed_at,
      meta: `${formatCurrency(payout.amount)} · ${formatDate(payout.processed_at)}`,
    })),
    ...disruptions
      .filter((event) => event.zone_id === worker.zone_id)
      .map((event) => ({
        id: `event-${event.id}`,
        title: `${event.event_type.replace(/_/g, " ")} detected`,
        timestamp: event.started_at,
        meta: `Severity ${event.severity}/4 · ${formatDate(event.started_at)}`,
      })),
  ]
    .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime())
    .slice(0, 6);

  return (
    <section className="workspace-grid">
      <div className="primary-stack">
        <div className="dashboard-overview-bar">
          <article>
            <span>Active policies</span>
            <strong>{policies.length}</strong>
          </article>
          <article>
            <span>Claims recorded</span>
            <strong>{claims.length}</strong>
          </article>
          <article>
            <span>Payouts processed</span>
            <strong>{payouts.length}</strong>
          </article>
          <article>
            <span>Zone status</span>
            <strong>{localDisruption ? "Alert live" : "Clear"}</strong>
          </article>
        </div>

        <div className="dashboard-card">
          <div className="section-head">
            <p className="eyebrow">Worker profile</p>
            <h3>{worker.name}</h3>
          </div>

          <div className="worker-glance">
            <div>
              <span>Phone</span>
              <strong>{worker.phone}</strong>
            </div>
            <div>
              <span>Platform</span>
              <strong>{worker.platform}</strong>
            </div>
            <div>
              <span>Zone</span>
              <strong>{prettyZone(worker.zone_id)}</strong>
            </div>
            <div>
              <span>Trust score</span>
              <strong>{Number(worker.trust_score).toFixed(0)}</strong>
            </div>
          </div>

          <div className="action-row top-gap">
            <button className="secondary-action" type="button" onClick={onRefresh}>
              Refresh data
            </button>
            <button className="ghost-action strong-ghost" type="button" onClick={onLogout}>
              Logout
            </button>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="section-head">
            <p className="eyebrow">Choose policy</p>
            <h3>Quote and activate your weekly cover</h3>
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

          <div className="action-row top-gap">
            <button className="secondary-action" type="button" onClick={onQuote} disabled={isFetchingQuote}>
              {isFetchingQuote ? "Fetching quote..." : "Get quote"}
            </button>
            <button className="primary-action" type="button" onClick={onBuy} disabled={isBuying}>
              {isBuying ? "Activating..." : "Activate policy"}
            </button>
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
                  <span>Valid to</span>
                  <strong>{formatDate(quote.valid_to)}</strong>
                </article>
              </div>
              <div className="trigger-list">
                {quote.triggers.map((trigger) => (
                  <span key={trigger}>{trigger}</span>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-card compact">
              <h4>No live quote yet</h4>
              <p>Fetch a quote to see premium, coverage, and active trigger rules from the backend.</p>
            </div>
          )}
        </div>
      </div>

      <div className="side-stack">
        <div className="tabbar">
          {(["overview", "history"] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              className={`tab-chip ${activeTab === tab ? "is-active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "overview" ? (
          <>
            <div className="dashboard-card">
              <div className="section-head">
                <p className="eyebrow">Current protection</p>
                <h3>{activePolicy ? `${activePolicy.coverage_tier} policy active` : "No active policy"}</h3>
              </div>
              {activePolicy ? (
                <div className="detail-grid">
                  <div>
                    <span>Premium</span>
                    <strong>{formatCurrency(activePolicy.weekly_premium)}</strong>
                  </div>
                  <div>
                    <span>Coverage</span>
                    <strong>{formatCurrency(activePolicy.coverage_amount)}</strong>
                  </div>
                  <div>
                    <span>Dates</span>
                    <strong>{formatDate(activePolicy.start_date)} - {formatDate(activePolicy.end_date)}</strong>
                  </div>
                  <div>
                    <span>Status</span>
                    <strong>{activePolicy.status}</strong>
                  </div>
                </div>
              ) : (
                <div className="empty-card compact">
                  <h4>No policy purchased</h4>
                  <p>Select a tier, fetch a quote, and activate a policy from the left panel.</p>
                </div>
              )}
            </div>

            <div className="dashboard-card">
              <div className="section-head">
                <p className="eyebrow">Local zone signal</p>
                <h3>{localDisruption ? "Disruption detected" : "No local disruption"}</h3>
              </div>
              {localDisruption ? (
                <div className="event-strip">
                  <span>{localDisruption.event_type.replace(/_/g, " ")}</span>
                  <span>Severity {localDisruption.severity}/4</span>
                  <span>Started {formatDate(localDisruption.started_at)}</span>
                </div>
              ) : (
                <p className="muted-copy">No current event for {prettyZone(worker.zone_id)}.</p>
              )}
            </div>

            <div className="dashboard-card">
              <div className="section-head">
                <p className="eyebrow">Payout snapshot</p>
                <h3>{payouts.length} payout records</h3>
              </div>
              {payouts.length > 0 ? (
                <div className="mini-list">
                  {payouts.map((payout) => (
                    <article key={payout.id} className="mini-card">
                      <span>{formatCurrency(payout.amount)}</span>
                      <strong>{payout.status}</strong>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted-copy">No payouts yet.</p>
              )}
            </div>

            <div className="dashboard-card">
              <div className="section-head">
                <p className="eyebrow">Worker summary</p>
                <h3>Coverage readiness</h3>
              </div>
              <div className="detail-grid">
                <div>
                  <span>Weekly earnings</span>
                  <strong>{formatCurrency(worker.avg_weekly_earnings)}</strong>
                </div>
                <div>
                  <span>Tenure</span>
                  <strong>{worker.tenure_days} days</strong>
                </div>
                <div>
                  <span>KYC</span>
                  <strong>{worker.kyc_verified ? "Verified" : "Pending"}</strong>
                </div>
                <div>
                  <span>Platform</span>
                  <strong>{worker.platform}</strong>
                </div>
              </div>
            </div>

            <div className="dashboard-card">
              <div className="section-head">
                <p className="eyebrow">Activity feed</p>
                <h3>Recent worker timeline</h3>
              </div>
              {workerTimeline.length > 0 ? (
                <div className="mini-list">
                  {workerTimeline.map((item) => (
                    <article key={item.id} className="mini-card timeline-card">
                      <span>{item.title}</span>
                      <strong>{item.meta}</strong>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted-copy">New activity will appear here after policy, claim, or disruption events.</p>
              )}
            </div>
          </>
        ) : null}

        {activeTab === "history" ? (
          <>
            <div className="dashboard-card">
              <div className="section-head">
                <p className="eyebrow">Policy history</p>
                <h3>{policies.length} policies</h3>
              </div>
              {policies.length > 0 ? (
                <div className="mini-list">
                  {policies.map((policy) => (
                    <article key={policy.id} className="mini-card">
                      <span>{policy.coverage_tier}</span>
                      <strong>{formatCurrency(policy.coverage_amount)}</strong>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted-copy">No policy history yet.</p>
              )}
            </div>

            <div className="dashboard-card">
              <div className="section-head">
                <p className="eyebrow">Claim history</p>
                <h3>{claims.length} claims</h3>
              </div>
              {claims.length > 0 ? (
                <div className="mini-list">
                  {claims.map((claim) => (
                    <article key={claim.id} className="mini-card">
                      <span>{formatCurrency(claim.amount)}</span>
                      <strong>{claim.status}</strong>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted-copy">No claims raised yet.</p>
              )}
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
}
