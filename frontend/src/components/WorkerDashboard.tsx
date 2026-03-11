import type { Claim, CoverageTier, DisruptionEvent, FraudLog, Policy, Payout, QuoteResponse, Worker } from "../lib/api";
import { tierCards } from "../lib/constants";
import { formatCurrency, formatDate, prettyZone } from "../lib/format";
import { Field } from "./Field";

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
  adminClaims,
  fraudLogs,
  adminKey,
  setAdminKey,
  disruptions,
  isFetchingQuote,
  isBuying,
  isLoadingAdmin,
  onQuote,
  onBuy,
  onLogout,
  onLoadAdmin,
  onRefresh,
  onApproveClaim,
  onRejectClaim,
}: {
  worker: Worker;
  selectedTier: CoverageTier;
  setSelectedTier: (tier: CoverageTier) => void;
  activeTab: "overview" | "history" | "admin";
  setActiveTab: (tab: "overview" | "history" | "admin") => void;
  quote: QuoteResponse | null;
  policies: Policy[];
  claims: Claim[];
  payouts: Payout[];
  adminClaims: Claim[];
  fraudLogs: FraudLog[];
  adminKey: string;
  setAdminKey: (value: string) => void;
  disruptions: DisruptionEvent[];
  isFetchingQuote: boolean;
  isBuying: boolean;
  isLoadingAdmin: boolean;
  onQuote: () => void;
  onBuy: () => void;
  onLogout: () => void;
  onLoadAdmin: () => void;
  onRefresh: () => void;
  onApproveClaim: (claimId: string) => void;
  onRejectClaim: (claimId: string) => void;
}) {
  const activePolicy = policies.find((policy) => policy.status === "active") ?? policies[0] ?? null;
  const localDisruption = disruptions.find((event) => event.zone_id === worker.zone_id) ?? null;

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
          {(["overview", "history", "admin"] as const).map((tab) => (
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

        {activeTab === "admin" ? (
          <div className="dashboard-card">
            <div className="section-head">
              <p className="eyebrow">Admin tools</p>
              <h3>Manual review and fraud logs</h3>
            </div>

            <Field label="Admin API key">
              <input
                value={adminKey}
                onChange={(event) => setAdminKey(event.target.value)}
                placeholder="Paste admin key"
              />
            </Field>

            <div className="action-row top-gap">
              <button className="secondary-action" type="button" onClick={onLoadAdmin} disabled={isLoadingAdmin}>
                {isLoadingAdmin ? "Loading..." : "Load admin feed"}
              </button>
            </div>

            <div className="mini-list">
              <h4>Claims waiting for review</h4>
              {adminClaims.length > 0 ? (
                adminClaims.map((claim) => (
                  <article key={claim.id} className="admin-card">
                    <div>
                      <span>{claim.worker_id.slice(0, 8)}</span>
                      <strong>{formatCurrency(claim.amount)}</strong>
                    </div>
                    <div className="admin-actions">
                      <button type="button" className="mini-action approve" onClick={() => onApproveClaim(claim.id)}>
                        Approve
                      </button>
                      <button type="button" className="mini-action reject" onClick={() => onRejectClaim(claim.id)}>
                        Reject
                      </button>
                    </div>
                  </article>
                ))
              ) : (
                <p className="muted-copy">No claims in manual review.</p>
              )}
            </div>

            <div className="mini-list">
              <h4>Fraud logs</h4>
              {fraudLogs.length > 0 ? (
                fraudLogs.slice(0, 6).map((log) => (
                  <article key={log.id} className="mini-card">
                    <span>{log.fraud_type}</span>
                    <strong>{log.action_taken}</strong>
                  </article>
                ))
              ) : (
                <p className="muted-copy">No fraud logs loaded.</p>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
