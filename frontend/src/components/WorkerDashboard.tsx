import { useEffect, useState } from "react";
import { motion, AnimatePresence, type Variants } from "framer-motion";
import { 
  User, 
  MapPin, 
  Shield, 
  TrendingUp, 
  Wallet, 
  History, 
  RefreshCw, 
  LogOut, 
  ChevronRight, 
  ChevronLeft,
  CheckCircle2,
  AlertCircle,
  Clock,
  Activity,
  CreditCard,
  Building2,
  Lock,
  Info,
  ShieldCheck,
  Smartphone,
  Zap
} from "lucide-react";

import type { Claim, CoverageTier, DisruptionEvent, Policy, Payout, QuoteResponse, Worker } from "../lib/api";
import { tierCards } from "../lib/constants";
import { formatCurrency, formatDate, prettyZone } from "../lib/format";
import { Field } from "./Field";

const stageVariants: Variants = {
  initial: (direction: number) => ({
    opacity: 0,
    x: direction > 0 ? 50 : -50,
    filter: "blur(10px)"
  }),
  animate: {
    opacity: 1,
    x: 0,
    filter: "blur(0px)",
    transition: { duration: 0.5, ease: [0.23, 1, 0.32, 1] as any }
  },
  exit: (direction: number) => ({
    opacity: 0,
    x: direction > 0 ? -50 : 50,
    filter: "blur(10px)",
    transition: { duration: 0.3 }
  })
};

export function WorkerDashboard({
  worker,
  selectedTier,
  setSelectedTier,
  quote,
  policies,
  claims,
  payouts,
  disruptions,
  isFetchingQuote,
  isBuying,
  isSavingPayoutProfile,
  onQuote,
  onBuy,
  onSavePayoutProfile,
  onLogout,
  onRefresh,
}: {
  worker: Worker;
  selectedTier: CoverageTier;
  setSelectedTier: (tier: CoverageTier) => void;
  quote: QuoteResponse | null;
  policies: Policy[];
  claims: Claim[];
  payouts: Payout[];
  disruptions: DisruptionEvent[];
  isFetchingQuote: boolean;
  isBuying: boolean;
  isSavingPayoutProfile: boolean;
  onQuote: () => void;
  onBuy: () => void;
  onSavePayoutProfile: (payload: any) => void;
  onLogout: () => void;
  onRefresh: () => void;
}) {
  const [stage, setStage] = useState(1);
  const [direction, setDirection] = useState(0);

  const [payoutMethod, setPayoutMethod] = useState<"upi" | "bank_transfer">(worker.payout_method ?? "upi");
  const [upiId, setUpiId] = useState(worker.payout_upi_id ?? "");
  const [accountName, setAccountName] = useState(worker.payout_bank_account_name ?? "");
  const [accountNumber, setAccountNumber] = useState(worker.payout_bank_account_number ?? "");
  const [ifsc, setIfsc] = useState(worker.payout_bank_ifsc ?? "");
  const [contactName, setContactName] = useState(worker.payout_contact_name ?? worker.name);
  const [contactPhone, setContactPhone] = useState(worker.payout_contact_phone ?? worker.phone);

  useEffect(() => {
    setPayoutMethod(worker.payout_method ?? "upi");
    setUpiId(worker.payout_upi_id ?? "");
    setAccountName(worker.payout_bank_account_name ?? "");
    setAccountNumber(worker.payout_bank_account_number ?? "");
    setIfsc(worker.payout_bank_ifsc ?? "");
    setContactName(worker.payout_contact_name ?? worker.name);
    setContactPhone(worker.payout_contact_phone ?? worker.phone);
  }, [worker]);

  const activePolicy = policies.find((p) => p.status === "active") ?? null;
  const localDisruption = disruptions.find((e) => e.zone_id === worker.zone_id) ?? null;

  const paginate = (newStage: number) => {
    if (newStage < 1 || newStage > 5) return;
    setDirection(newStage > stage ? 1 : -1);
    setStage(newStage);
  };

  const dashboardStats = [
    { label: "Policies", value: policies.length, icon: <Shield size={16} /> },
    { label: "Claims", value: claims.length, icon: <Activity size={16} /> },
    { label: "Payouts", value: payouts.length, icon: <Wallet size={16} /> },
  ];

  const workerTimeline = [
    ...policies.map(p => ({ id: `p-${p.id}`, title: `${p.coverage_tier} Policy`, status: p.status, date: p.created_at, icon: <Shield size={14} /> })),
    ...claims.map(c => ({ id: `c-${c.id}`, title: `Claim ${formatCurrency(c.amount)}`, status: c.status, date: c.created_at, icon: <AlertCircle size={14} /> })),
    ...payouts.map(py => ({ id: `py-${py.id}`, title: `Payout Received`, status: py.status, date: py.processed_at, icon: <CheckCircle2 size={14} /> }))
  ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 5);

  return (
    <div className="dashboard-stepper-layout">
      {/* Top Navigation / Progress */}
      <div className="stepper-container">
        {[1, 2, 3, 4, 5].map((s) => (
          <div 
            key={s} 
            className={`step-node ${stage === s ? "active" : ""} ${stage > s ? "completed" : ""}`}
            onClick={() => paginate(s)}
          >
            {stage > s ? <CheckCircle2 size={18} /> : <span>{s}</span>}
            <div className="step-label">
              {s === 1 && "Identity"}
              {s === 2 && "Market"}
              {s === 3 && "Protection"}
              {s === 4 && "Payouts"}
              {s === 5 && "History"}
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-stage-wrapper">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={stage}
            custom={direction}
            variants={stageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="stage-content"
          >
            {stage === 1 && (
              <div className="stage-inner">
                <div className="stage-header">
                  <p className="eyebrow">Step 1 of 5</p>
                  <h3>Welcome, {worker.name}</h3>
                  <p>Review your identity and standing in the GigShield ecosystem.</p>
                </div>

                <div className="dashboard-overview-bar">
                  {dashboardStats.map((stat, i) => (
                    <article key={i}>
                      <div className="stat-icon-small">{stat.icon}</div>
                      <span>{stat.label}</span>
                      <strong>{stat.value}</strong>
                    </article>
                  ))}
                  <article className={localDisruption ? "alert-bg" : ""}>
                    <div className="stat-icon-small"><MapPin size={16} /></div>
                    <span>Zone Status</span>
                    <strong>{localDisruption ? "Alert Live" : "Clear"}</strong>
                  </article>
                </div>

                <div className="dashboard-card top-gap">
                  <div className="worker-glance-new">
                    <div className="glance-item">
                      <Smartphone size={20} />
                      <div><span>Phone</span><strong>{worker.phone}</strong></div>
                    </div>
                    <div className="glance-item">
                      <Building2 size={20} />
                      <div><span>Platform</span><strong>{worker.platform}</strong></div>
                    </div>
                    <div className="glance-item">
                      <MapPin size={20} />
                      <div><span>Default Zone</span><strong>{prettyZone(worker.zone_id)}</strong></div>
                    </div>
                    <div className="glance-item highlight">
                      <TrendingUp size={20} />
                      <div><span>Trust Score</span><strong>{Number(worker.trust_score).toFixed(0)}</strong></div>
                    </div>
                  </div>
                  
                  <div className="action-row top-gap">
                    <button className="secondary-action-new" onClick={onRefresh}><RefreshCw size={16} /> Sync Data</button>
                    <button className="ghost-action strong-ghost" onClick={onLogout}><LogOut size={16} /> Sign Out</button>
                  </div>
                </div>
              </div>
            )}

            {stage === 2 && (
              <div className="stage-inner">
                <div className="stage-header">
                  <p className="eyebrow">Step 2 of 5</p>
                  <h3>Local Market Feed</h3>
                  <p>Real-time disruption data for {prettyZone(worker.zone_id)}.</p>
                </div>

                {localDisruption ? (
                  <motion.div className="disruption-hero-card" initial={{ scale: 0.9 }} animate={{ scale: 1 }}>
                    <div className="alert-badge"><AlertCircle size={14} /> LIVE ALERT</div>
                    <h2>{localDisruption.event_type.replace(/_/g, " ")} active</h2>
                    <p>Severity {localDisruption.severity}/4 trigger detected by backend sensors.</p>
                    <div className="event-meta-strip">
                      <span><Clock size={14} /> Started {formatDate(localDisruption.started_at)}</span>
                      <span><ShieldCheck size={14} /> Parametric ready</span>
                    </div>
                  </motion.div>
                ) : (
                  <div className="empty-stage-card">
                    <CheckCircle2 size={48} className="text-teal" />
                    <h4>Safe Zone Activity</h4>
                    <p>No disruptions detected in your current zone. You can still purchase protection for upcoming shifts.</p>
                  </div>
                )}
                
                <div className="info-banner top-gap">
                  <Info size={18} />
                  <p>Disruption alerts are used to automate claim verification. If you work during an alert, you may be eligible for instant payouts.</p>
                </div>
              </div>
            )}

            {stage === 3 && (
              <div className="stage-inner">
                <div className="stage-header">
                  <p className="eyebrow">Step 3 of 5</p>
                  <h3>Income Protection</h3>
                  <p>Choose a tier and secure your earnings for the upcoming week.</p>
                </div>

                <div className="tier-selection-grid">
                  {tierCards.map((tier) => (
                    <motion.button
                      key={tier.id}
                      className={`premium-tier-card ${selectedTier === tier.id ? "active" : ""}`}
                      onClick={() => setSelectedTier(tier.id)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="tier-icon-wrapper"><Shield size={24} /></div>
                      <div className="tier-info">
                        <strong>{tier.title}</strong>
                        <span>{tier.helper}</span>
                      </div>
                      <div className="tier-check"><CheckCircle2 size={20} /></div>
                    </motion.button>
                  ))}
                </div>

                <div className="action-row top-gap">
                  <button className="secondary-action-new glossy" onClick={onQuote} disabled={isFetchingQuote}>
                    {isFetchingQuote ? <RefreshCw className="spin" size={18} /> : "Calculate Quote"}
                  </button>
                  <button className="primary-action-new glossy flex-1" onClick={onBuy} disabled={isBuying || !quote}>
                    {isBuying ? "Processing..." : "Activate Cover"}
                  </button>
                </div>

                {quote ? (
                  <motion.div className="quote-reveal-card" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}>
                    <div className="quote-price-tag">
                      <span>Weekly Premium</span>
                      <strong>{formatCurrency(quote.weekly_premium)}</strong>
                    </div>
                    <div className="quote-details-grid">
                      <div><span>Coverage</span><strong>{formatCurrency(quote.coverage_amount)}</strong></div>
                      <div><span>Risk Score</span><strong>{quote.risk_score}</strong></div>
                      <div><span>Expiry</span><strong>{formatDate(quote.valid_to)}</strong></div>
                    </div>
                    <div className="trigger-pills">
                      {quote.triggers.map(t => <span key={t} className="trigger-pill">{t}</span>)}
                    </div>
                  </motion.div>
                ) : (
                  <p className="nav-hint">Select a tier and fetch a live quote to proceed.</p>
                )}
              </div>
            )}

            {stage === 4 && (
              <div className="stage-inner">
                <div className="stage-header">
                  <p className="eyebrow">Step 4 of 5</p>
                  <h3>Payout Profile</h3>
                  <p>Configure where your settlements should be sent.</p>
                </div>

                <div className="payout-status-card">
                  <div className={`status-pill ${worker.payout_profile_status === "verified" ? "verified" : "pending"}`}>
                    {worker.payout_profile_status === "verified" ? <ShieldCheck size={14} /> : <Clock size={14} />}
                    {worker.payout_profile_status.toUpperCase()}
                  </div>
                  <p>Approved claims are paid instantly to your selected destination once verified.</p>
                </div>

                <div className="dashboard-card top-gap">
                  <div className="field-grid">
                    <Field label="Payout Method">
                      <div className="input-field-wrapper">
                        <CreditCard size={18} className="input-icon-lucide" />
                        <select value={payoutMethod} onChange={(e) => setPayoutMethod(e.target.value as any)}>
                          <option value="upi">UPI Identification</option>
                          <option value="bank_transfer">Direct Bank Transfer</option>
                        </select>
                      </div>
                    </Field>
                    <Field label="Contact Name">
                      <div className="input-field-wrapper">
                        <User size={18} className="input-icon-lucide" />
                        <input value={contactName} onChange={(e) => setContactName(e.target.value)} />
                      </div>
                    </Field>
                    {payoutMethod === "upi" ? (
                      <Field label="UPI ID" className="full-width">
                        <div className="input-field-wrapper">
                          <Zap size={18} className="input-icon-lucide" />
                          <input value={upiId} onChange={(e) => setUpiId(e.target.value)} placeholder="username@bank" />
                        </div>
                      </Field>
                    ) : (
                      <div className="bank-fields">
                        <Field label="Account Number">
                          <div className="input-field-wrapper">
                            <Lock size={18} className="input-icon-lucide" />
                            <input value={accountNumber} onChange={(e) => setAccountNumber(e.target.value)} />
                          </div>
                        </Field>
                        <Field label="IFSC Code">
                          <div className="input-field-wrapper">
                            <Building2 size={18} className="input-icon-lucide" />
                            <input value={ifsc} onChange={(e) => setIfsc(e.target.value.toUpperCase())} />
                          </div>
                        </Field>
                      </div>
                    )}
                  </div>
                  
                  <div className="action-row top-gap">
                    <button 
                      className="primary-action-new full-width" 
                      onClick={() => onSavePayoutProfile({
                        payout_method: payoutMethod,
                        payout_upi_id: payoutMethod === "upi" ? upiId : null,
                        payout_bank_account_name: contactName,
                        payout_bank_account_number: payoutMethod === "bank_transfer" ? accountNumber : null,
                        payout_bank_ifsc: payoutMethod === "bank_transfer" ? ifsc : null,
                        payout_contact_name: contactName,
                        payout_contact_phone: contactPhone,
                      })}
                      disabled={isSavingPayoutProfile}
                    >
                      {isSavingPayoutProfile ? "Updating Profile..." : "Save Payout Profile"}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {stage === 5 && (
              <div className="stage-inner">
                <div className="stage-header">
                  <p className="eyebrow">Step 5 of 5</p>
                  <h3>Activity & History</h3>
                  <p>Review your recent timeline and previous protection cycles.</p>
                </div>

                <div className="timeline-section">
                  <h4>Recent Activity</h4>
                  <div className="timeline-list">
                    {workerTimeline.map((item) => (
                      <motion.div 
                        key={item.id} 
                        className="timeline-item-premium"
                        whileHover={{ x: 5 }}
                      >
                        <div className="timeline-icon">{item.icon}</div>
                        <div className="timeline-info">
                          <strong>{item.title}</strong>
                          <span>{formatDate(item.date)}</span>
                        </div>
                        <div className={`status-tag ${item.status}`}>{item.status}</div>
                      </motion.div>
                    ))}
                  </div>
                </div>

                <div className="summary-row top-gap">
                  <div className="summary-box">
                    <span>Lifetime Policies</span>
                    <strong>{policies.length}</strong>
                  </div>
                  <div className="summary-box">
                    <span>Approved Payouts</span>
                    <strong>{payouts.length}</strong>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation Buttons */}
        <div className="stage-nav">
          <button 
            className="secondary-action-new" 
            onClick={() => paginate(stage - 1)}
            disabled={stage === 1}
          >
            <ChevronLeft size={20} /> Previous
          </button>
          {stage < 5 ? (
            <button 
              className="primary-action-new" 
              onClick={() => paginate(stage + 1)}
            >
              Next <ChevronRight size={20} />
            </button>
          ) : (
            <button 
              className="primary-action-new" 
              onClick={() => paginate(1)}
            >
              Back to Start <RefreshCw size={18} />
            </button>
          )}
        </div>
        <p className="nav-hint">{stage} of 5 stages completed</p>
      </div>
    </div>
  );
}
