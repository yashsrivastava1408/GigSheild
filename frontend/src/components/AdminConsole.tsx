import type { AdminOpsPolicyExpiryResult, AdminOpsWeatherSyncResult, Claim, FraudLog } from "../lib/api";
import { formatCurrency, formatDateTime } from "../lib/format";
import { Field } from "./Field";

export function AdminConsole({
  adminKey,
  setAdminKey,
  adminClaims,
  fraudLogs,
  latestWeatherSync,
  latestPolicyExpiry,
  isLoadingAdmin,
  isRunningWeatherSync,
  isRunningPolicyExpiry,
  onLoadAdmin,
  onSyncWeather,
  onExpirePolicies,
  onApproveClaim,
  onRejectClaim,
  onGoWorker,
}: {
  adminKey: string;
  setAdminKey: (value: string) => void;
  adminClaims: Claim[];
  fraudLogs: FraudLog[];
  latestWeatherSync: AdminOpsWeatherSyncResult[] | null;
  latestPolicyExpiry: AdminOpsPolicyExpiryResult | null;
  isLoadingAdmin: boolean;
  isRunningWeatherSync: boolean;
  isRunningPolicyExpiry: boolean;
  onLoadAdmin: () => void;
  onSyncWeather: () => void;
  onExpirePolicies: () => void;
  onApproveClaim: (claimId: string) => void;
  onRejectClaim: (claimId: string) => void;
  onGoWorker: () => void;
}) {
  const pendingExposure = adminClaims.reduce((total, claim) => total + claim.amount, 0);
  const highRiskFraudLogs = fraudLogs.filter((log) => Number(log.fraud_score) >= 50).length;
  const latestFraudEvent = fraudLogs[0]?.created_at ?? null;
  const latestWeatherEvent = latestWeatherSync?.[0]?.started_at ?? null;

  return (
    <section className="admin-console">
      <div className="dashboard-card admin-hero-card">
        <div className="section-head">
          <p className="eyebrow">GigShield Admin</p>
          <h2>Operations console for review queues, disruption sync, and expiry runs</h2>
        </div>

        <div className="admin-summary-grid">
          <article>
            <span>Manual review queue</span>
            <strong>{adminClaims.length}</strong>
            <small>{pendingExposure > 0 ? formatCurrency(pendingExposure) : "No pending exposure"}</small>
          </article>
          <article>
            <span>Fraud pressure</span>
            <strong>{highRiskFraudLogs}</strong>
            <small>{latestFraudEvent ? `Latest ${formatDateTime(latestFraudEvent)}` : "No fraud events loaded"}</small>
          </article>
          <article>
            <span>Weather sync</span>
            <strong>{latestWeatherSync ? latestWeatherSync.length : 0}</strong>
            <small>{latestWeatherEvent ? `Started ${formatDateTime(latestWeatherEvent)}` : "No sync run yet"}</small>
          </article>
          <article>
            <span>Policy expiry run</span>
            <strong>{latestPolicyExpiry?.expired_policies ?? 0}</strong>
            <small>{latestPolicyExpiry ? "Latest expiry result loaded" : "No expiry run yet"}</small>
          </article>
        </div>

        <div className="action-row">
          <button className="secondary-action" type="button" onClick={onGoWorker}>
            Open worker app
          </button>
        </div>
      </div>

      <div className="workspace-grid admin-layout">
        <div className="primary-stack">
          <div className="dashboard-card">
            <div className="section-head">
              <p className="eyebrow">Access</p>
              <h3>Admin API key</h3>
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
                {isLoadingAdmin ? "Loading..." : "Load review queue"}
              </button>
              <button className="secondary-action" type="button" onClick={onSyncWeather} disabled={isRunningWeatherSync}>
                {isRunningWeatherSync ? "Syncing weather..." : "Sync weather"}
              </button>
              <button className="secondary-action" type="button" onClick={onExpirePolicies} disabled={isRunningPolicyExpiry}>
                {isRunningPolicyExpiry ? "Expiring..." : "Expire policies"}
              </button>
            </div>
          </div>

          <div className="dashboard-card">
            <div className="section-head">
              <p className="eyebrow">Manual review</p>
              <h3>{adminClaims.length} claims waiting</h3>
            </div>

            <div className="mini-list">
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
          </div>
        </div>

        <div className="side-stack">
          <div className="dashboard-card">
            <div className="section-head">
              <p className="eyebrow">Operations status</p>
              <h3>Latest runs</h3>
            </div>

            <div className="mini-list">
              <article className="mini-card">
                <span>Latest weather sync</span>
                <strong>{latestWeatherSync ? `${latestWeatherSync.length} disruption events created` : "Not run yet"}</strong>
              </article>
              <article className="mini-card">
                <span>Latest policy expiry</span>
                <strong>
                  {latestPolicyExpiry ? `${latestPolicyExpiry.expired_policies} policies expired` : "Not run yet"}
                </strong>
              </article>
              <article className="mini-card">
                <span>Pending exposure</span>
                <strong>{pendingExposure > 0 ? formatCurrency(pendingExposure) : "None"}</strong>
              </article>
            </div>
          </div>

          <div className="dashboard-card">
            <div className="section-head">
              <p className="eyebrow">Fraud feed</p>
              <h3>{fraudLogs.length} recent entries</h3>
            </div>

            <div className="mini-list">
              {fraudLogs.length > 0 ? (
                fraudLogs.slice(0, 6).map((log) => (
                  <article key={log.id} className="mini-card">
                    <span>{log.fraud_type}</span>
                    <strong>{`${log.action_taken} · ${Number(log.fraud_score).toFixed(0)}`}</strong>
                  </article>
                ))
              ) : (
                <p className="muted-copy">No fraud logs loaded.</p>
              )}
            </div>
          </div>

          {latestWeatherSync ? (
            <div className="dashboard-card">
              <div className="section-head">
                <p className="eyebrow">Weather sync output</p>
                <h3>{latestWeatherSync.length} new events</h3>
              </div>

              <div className="mini-list">
                {latestWeatherSync.length > 0 ? (
                  latestWeatherSync.map((event) => (
                    <article key={event.id} className="mini-card">
                      <span>{event.event_type.replace(/_/g, " ")}</span>
                      <strong>{event.zone_id}</strong>
                    </article>
                  ))
                ) : (
                  <p className="muted-copy">No new disruption events were created in the last sync.</p>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
