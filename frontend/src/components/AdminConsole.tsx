import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence, type Variants } from "framer-motion";
import {
  ShieldAlert,
  CheckSquare,
  Activity,
  Key,
  CloudLightning,
  FileX,
  RefreshCw,
  BarChart3,
  AlertTriangle,
  UserCheck,
  Database,
  Search,
  LogOut
} from "lucide-react";

import type {
  AdminPayoutProfile,
  AdminOpsPolicyExpiryResult,
  AdminOpsWeatherSyncResult,
  Claim,
  FraudLog,
  PlausibilityAssessment,
} from "../lib/api";
import { formatCurrency, formatDateTime } from "../lib/format";
import { Field } from "./Field";

function toTitleCase(str: string): string {
  if (!str) return str;
  return str
    .replace(/_/g, " ")
    .toLowerCase()
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

const tabVariants: Variants = {
  initial: (direction: number) => ({ opacity: 0, x: direction > 0 ? 20 : -20 }),
  animate: { opacity: 1, x: 0, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] as any } },
  exit: (direction: number) => ({ opacity: 0, x: direction < 0 ? 20 : -20, transition: { duration: 0.3 } })
};

export function AdminConsole({
  adminKey,
  setAdminKey,
  adminClaims,
  fraudLogs,
  payoutProfiles,
  plausibilityAssessments,
  latestWeatherSync,
  latestPolicyExpiry,
  isLoadingAdmin,
  isRunningWeatherSync,
  isRunningPolicyExpiry,
  onLoadAdmin,
  onSyncWeather,
  onExpirePolicies,
  onApproveClaim,
  onApprovePayoutProfile,
  onRejectClaim,
  onRejectPayoutProfile,
  onGoWorker,
  onAutoLoadDemo,
}: {
  adminKey: string;
  setAdminKey: (value: string) => void;
  adminClaims: Claim[];
  fraudLogs: FraudLog[];
  payoutProfiles: AdminPayoutProfile[];
  plausibilityAssessments: PlausibilityAssessment[];
  latestWeatherSync: AdminOpsWeatherSyncResult[] | null;
  latestPolicyExpiry: AdminOpsPolicyExpiryResult | null;
  isLoadingAdmin: boolean;
  isRunningWeatherSync: boolean;
  isRunningPolicyExpiry: boolean;
  onLoadAdmin: () => void;
  onSyncWeather: () => void;
  onExpirePolicies: () => void;
  onApproveClaim: (claimId: string) => void;
  onApprovePayoutProfile: (workerId: string) => void;
  onRejectClaim: (claimId: string) => void;
  onRejectPayoutProfile: (workerId: string) => void;
  onGoWorker: () => void;
  onAutoLoadDemo: () => void;
}) {
  const [activeTab, setActiveTab] = useState<"operations" | "review" | "intelligence">("operations");
  const [direction, setDirection] = useState(0);

  const switchTab = (tab: "operations" | "review" | "intelligence") => {
    const order = { operations: 0, review: 1, intelligence: 2 };
    setDirection(order[tab] > order[activeTab] ? 1 : -1);
    setActiveTab(tab);
  };

  const sortedAssessments = useMemo(
    () =>
      [...plausibilityAssessments].sort(
        (left, right) =>
          right.plausibility_score - left.plausibility_score ||
          new Date(right.assessed_at).getTime() - new Date(left.assessed_at).getTime(),
      ),
    [plausibilityAssessments],
  );
  
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string | null>(null);

  useEffect(() => {
    if (sortedAssessments.length === 0) {
      setSelectedAssessmentId(null);
      return;
    }

    const stillPresent = sortedAssessments.some((assessment) => assessment.id === selectedAssessmentId);
    if (!selectedAssessmentId || !stillPresent) {
      setSelectedAssessmentId(sortedAssessments[0].id);
    }
  }, [selectedAssessmentId, sortedAssessments]);

  const selectedAssessment =
    sortedAssessments.find((assessment) => assessment.id === selectedAssessmentId) ?? null;
  const selectedClaim = selectedAssessment
    ? adminClaims.find((claim) => claim.id === selectedAssessment.claim_id) ?? null
    : null;

  const pendingExposure = adminClaims.reduce((total, claim) => total + claim.amount, 0);
  const highRiskFraudLogs = fraudLogs.filter((log) => Number(log.fraud_score) >= 50).length;
  const highRiskAssessments = plausibilityAssessments.filter((assessment) => assessment.risk_tier !== "low").length;
  const latestFraudEvent = fraudLogs[0]?.created_at ?? null;
  const latestAssessment = plausibilityAssessments[0]?.assessed_at ?? null;
  const latestWeatherEvent = latestWeatherSync?.[0]?.started_at ?? null;

  return (
    <section className="admin-console-new">
      <div className="admin-header-new">
        <div className="admin-header-top">
          <div>
            <div className="live-tag admin-tag"><ShieldAlert size={14} /> GIGSHIELD ADMIN</div>
            <h2>Risk Operations Console</h2>
          </div>
          <button className="ghost-action strong-ghost" onClick={onGoWorker}>
            <LogOut size={16} /> Exit to Worker App
          </button>
        </div>

        <div className="admin-summary-strip">
          <div className="admin-stat-pill">
            <span className="ink-dim">Exposure</span>
            <strong className="text-glow-red">{pendingExposure > 0 ? formatCurrency(pendingExposure) : "₹0"}</strong>
          </div>
          <div className="admin-stat-pill">
            <span className="ink-dim">Manual Review</span>
            <strong>{adminClaims.length} waiting</strong>
          </div>
          <div className="admin-stat-pill">
            <span className="ink-dim">Payouts</span>
            <strong>{payoutProfiles.length} waiting</strong>
          </div>
          <div className="admin-stat-pill">
            <span className="ink-dim">High Risk Flags</span>
            <strong className="text-accent">{highRiskFraudLogs + highRiskAssessments} detected</strong>
          </div>
        </div>

        <nav className="admin-tabbar">
          <button 
            className={`admin-tab ${activeTab === "operations" ? "active" : ""}`}
            onClick={() => switchTab("operations")}
          >
            <Database size={16} /> Operations & Scope
          </button>
          <button 
            className={`admin-tab ${activeTab === "review" ? "active" : ""}`}
            onClick={() => switchTab("review")}
            data-badge={adminClaims.length + payoutProfiles.length || null}
          >
            <CheckSquare size={16} /> Review Queue
          </button>
          <button 
            className={`admin-tab ${activeTab === "intelligence" ? "active" : ""}`}
            onClick={() => switchTab("intelligence")}
            data-badge={highRiskAssessments || null}
          >
            <Activity size={16} /> Risk Intelligence
          </button>
        </nav>
      </div>

      <div className="admin-workspace-wrapper">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={activeTab}
            custom={direction}
            variants={tabVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="admin-tab-content"
          >
            {activeTab === "operations" && (
              <div className="admin-grid-2col">
                <div className="dashboard-card">
                  <div className="section-head">
                    <p className="eyebrow">Access</p>
                    <h3>Admin API key</h3>
                  </div>
                  <Field label="Operator Authorization Key">
                    <div className="input-field-wrapper">
                      <Key size={18} className="input-icon-lucide" />
                      <input
                        value={adminKey}
                        onChange={(event) => setAdminKey(event.target.value)}
                        placeholder="Paste admin key"
                        type="password"
                      />
                    </div>
                  </Field>
                  <div className="action-row top-gap">
                    <button className="secondary-action-new" type="button" onClick={onAutoLoadDemo}>
                      Load Demo Key
                    </button>
                    <button className="primary-action-new flex-1" type="button" onClick={onLoadAdmin} disabled={isLoadingAdmin}>
                      <RefreshCw size={18} className={isLoadingAdmin ? "spin" : ""} />
                      {isLoadingAdmin ? "Synchronizing Data..." : "Load Review Queue"}
                    </button>
                  </div>
                </div>

                <div className="admin-v-stack">
                  <div className="dashboard-card action-card">
                    <div className="card-left">
                      <div className="icon-box teal"><CloudLightning size={20} /></div>
                      <div>
                        <h4>Disruption Feed Sync</h4>
                        <p className="signal-copy">Run weather sync to generate disruption events for the demo zone.</p>
                        <small>{latestWeatherEvent ? `Last run ${formatDateTime(latestWeatherEvent)}` : "No sync run yet"}</small>
                      </div>
                    </div>
                    <button className="secondary-action-new" onClick={onSyncWeather} disabled={isRunningWeatherSync}>
                      {isRunningWeatherSync ? "Syncing..." : "Trigger Sync"}
                    </button>
                  </div>

                  <div className="dashboard-card action-card">
                    <div className="card-left">
                      <div className="icon-box accent"><FileX size={20} /></div>
                      <div>
                        <h4>Lifecycle Expiry Run</h4>
                        <p className="signal-copy">Expire old policies to process their final statuses.</p>
                        <small>{latestPolicyExpiry ? `Last run cleared ${latestPolicyExpiry.expired_policies} policies` : "No expiry run yet"}</small>
                      </div>
                    </div>
                    <button className="secondary-action-new" onClick={onExpirePolicies} disabled={isRunningPolicyExpiry}>
                      {isRunningPolicyExpiry ? "Expiring..." : "Trigger Run"}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "review" && (
              <div className="admin-grid-2col">
                <div className="dashboard-card">
                  <div className="section-head">
                    <p className="eyebrow">Claims in queue</p>
                    <h3>Manual Review ({adminClaims.length})</h3>
                  </div>
                  <p className="muted-copy">
                    Claims appear here when trust, KYC, or signal quality is not strong enough for straight-through approval.
                  </p>

                  <div className="queue-list top-gap">
                    {adminClaims.length > 0 ? (
                      adminClaims.map((claim) => (
                        <article key={claim.id} className="queue-item">
                          <div className="queue-item-info">
                            <span className="queue-id">{claim.worker_id.slice(0, 8)}</span>
                            <strong className="text-accent">{formatCurrency(claim.amount)}</strong>
                          </div>
                          <div className="queue-actions">
                            <button className="mini-action-new approve" onClick={() => onApproveClaim(claim.id)}>Approve</button>
                            <button className="mini-action-new reject" onClick={() => onRejectClaim(claim.id)}>Reject</button>
                          </div>
                        </article>
                      ))
                    ) : (
                      <div className="empty-stage-card compact">
                        <CheckSquare size={32} className="text-teal" />
                        <h4>Queue Clear</h4>
                        <p>No claims require manual review.</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="dashboard-card">
                  <div className="section-head">
                    <p className="eyebrow">Onboarding queue</p>
                    <h3>Payout Profiles ({payoutProfiles.length})</h3>
                  </div>
                  <p className="muted-copy">
                    Approve these before expecting the worker payout setup to move from pending review to ready.
                  </p>
                  <div className="queue-list top-gap">
                    {payoutProfiles.length > 0 ? (
                      payoutProfiles.map((profile) => (
                        <article key={profile.id} className="queue-item">
                          <div className="queue-item-info">
                            <span className="queue-name"><UserCheck size={14} /> {profile.name}</span>
                            <strong className="text-teal">{profile.payout_method?.toUpperCase() ?? "UNCONFIGURED"}</strong>
                          </div>
                          <div className="queue-actions">
                            <button className="mini-action-new approve" onClick={() => onApprovePayoutProfile(profile.id)}>Approve</button>
                            <button className="mini-action-new reject" onClick={() => onRejectPayoutProfile(profile.id)}>Reject</button>
                          </div>
                        </article>
                      ))
                    ) : (
                      <div className="empty-stage-card compact">
                        <CheckSquare size={32} className="text-teal" />
                        <h4>Onboarding Clear</h4>
                        <p>No payout profiles waiting for review.</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "intelligence" && (
              <div className="admin-grid-sidebar">
                <div className="dashboard-card">
                  <div className="section-head">
                    <p className="eyebrow">Diagnostic trace</p>
                    <h3>Plausibility Engine</h3>
                    <p className="signal-copy">Tap a node to inspect the exact signals that pushed the claim up or down.</p>
                  </div>

                  {sortedAssessments.length > 0 ? (
                    <div className="plausibility-view">
                      <div className="graph-nodes-modern">
                        {sortedAssessments.map((assessment) => (
                          <button
                            key={assessment.id}
                            type="button"
                            className={`graph-node-modern ${selectedAssessmentId === assessment.id ? "active" : ""} ${assessment.risk_tier}`}
                            onClick={() => setSelectedAssessmentId(assessment.id)}
                          >
                            <div className="node-score">{assessment.plausibility_score}</div>
                            <div className="node-details">
                              <span>Worker {assessment.claim_id.slice(0, 8)}</span>
                              <small>{toTitleCase(assessment.routing_decision)}</small>
                            </div>
                          </button>
                        ))}
                      </div>

                      {selectedAssessment && (
                        <div className="assessment-detail-modern">
                          <div className="assessment-detail-head">
                            <div>
                              <p className="eyebrow">Claim {selectedAssessment.claim_id.slice(0, 8)}</p>
                              <h4>Decision: {toTitleCase(selectedAssessment.routing_decision)}</h4>
                            </div>
                            <div className={`detail-pill-modern ${selectedAssessment.risk_tier}`}>
                              {selectedAssessment.plausibility_score} Score
                            </div>
                          </div>

                          <div className="signal-trail">
                            {selectedAssessment.signals.map((signal) => (
                              <article key={signal.code} className={`signal-step ${signal.impact}`}>
                                <div className="signal-step-head">
                                  <strong>{toTitleCase(signal.code)}</strong>
                                  <span className="weight-badge">{signal.weight > 0 ? `+${signal.weight}` : signal.weight}</span>
                                </div>
                                <p>{signal.description}</p>
                                <small className="mono">{signal.evidence}</small>
                              </article>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="empty-stage-card compact top-gap">
                      <Search size={32} className="text-dim" />
                      <h4>No Assessments Data</h4>
                      <p>Run claims through the engine to generate plausibility traces.</p>
                    </div>
                  )}
                </div>

                <div className="dashboard-card">
                  <div className="section-head">
                    <p className="eyebrow">Real-time alerts</p>
                    <h3>Fraud Feed</h3>
                  </div>

                  <div className="timeline-list top-gap">
                    {fraudLogs.length > 0 ? (
                      fraudLogs.slice(0, 8).map((log) => (
                        <article key={log.id} className="fraud-log-item">
                          <div className="fraud-icon"><AlertTriangle size={16} /></div>
                          <div className="fraud-content">
                            <strong>{toTitleCase(log.fraud_type)}</strong>
                            <span>Action: {toTitleCase(log.action_taken)}</span>
                          </div>
                          <div className="fraud-score">{Number(log.fraud_score).toFixed(0)}</div>
                        </article>
                      ))
                    ) : (
                      <p className="muted-copy text-center">No fraud logs isolated.</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
