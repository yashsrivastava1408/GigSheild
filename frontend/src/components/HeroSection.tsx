import { motion, type Variants } from "framer-motion";
wimport {
  Zap,
  Shield,
  Clock,
  TrendingUp,
  Info,
  MapPin,
  Download,
  LayoutDashboard,
  ShieldCheck,
  AlertTriangle,
  Activity,
  User,
  Smartphone
} from "lucide-react";
import type { DisruptionEvent, Policy, Claim, Payout, Worker } from "../lib/api";
import { formatDate, prettyZone } from "../lib/format";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
};

const fadeInUp: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] as any } }
};

const staggerContainer: Variants = {
  animate: { transition: { staggerChildren: 0.1 } }
};

export function HeroSection({
  status,
  worker,
  policies,
  claims,
  payouts,
  disruptions,
  installEvent,
  onInstall,
  onOpenAdmin,
}: {
  status: string;
  worker: Worker | null;
  policies: Policy[];
  claims: Claim[];
  payouts: Payout[];
  disruptions: DisruptionEvent[];
  installEvent: BeforeInstallPromptEvent | null;
  onInstall: () => void;
  onOpenAdmin: () => void;
}) {
  const disruptionBanner =
    disruptions.find((event) => worker && event.zone_id === worker.zone_id) ?? disruptions[0] ?? null;

  return (
    <motion.section
      className="hero-grid"
      initial="initial"
      animate="animate"
      variants={staggerContainer}
    >
      <motion.div className="hero-copy" variants={fadeInUp}>
        <div className="hero-header-group">
          <p className="eyebrow">GigShield 2.0 Live Environment</p>
          <div className="top-banner-compact">
            <span><Shield size={12} /> Protection</span>
            <span><Activity size={12} /> Live Feed</span>
            <span><Zap size={12} /> Payouts</span>
          </div>
        </div>

        <h1>Secure your earnings before the city slows down.</h1>
        <div className="status-pill-large compact-status">
          <div className="pulse-dot" />
          <p>Welcome back, {worker ? worker.name.toUpperCase() : "WORKER"}. Activate your next policy or review live claims.</p>
        </div>

        <div className="hero-actions compact-actions">
          {installEvent && (
            <motion.button
              type="button"
              className="install-action glossy"
              onClick={onInstall}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Download size={18} /> Install App
            </motion.button>
          )}
          <motion.button
            type="button"
            className="secondary-action-new"
            onClick={onOpenAdmin}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <LayoutDashboard size={18} /> Admin Console
          </motion.button>
          <div className="auth-status-badge">
            <User size={14} />
            <span>{worker ? `Signed in as ${worker.name}` : "Ready for onboarding"}</span>
          </div>
        </div>

        <div className="hero-metrics">
          <motion.article whileHover={{ y: -5, borderColor: "var(--accent)" }}>
            <div className="metric-icon accent"><Smartphone size={20} /></div>
            <div>
              <span>Onboarding</span>
              <strong>Phone + OTP</strong>
            </div>
          </motion.article>
          <motion.article whileHover={{ y: -5, borderColor: "var(--teal)" }}>
            <div className="metric-icon teal"><ShieldCheck size={20} /></div>
            <div>
              <span>Cover Activation</span>
              <strong>Weekly Policy</strong>
            </div>
          </motion.article>
          <motion.article whileHover={{ y: -5, borderColor: "var(--accent)" }}>
            <div className="metric-icon accent"><TrendingUp size={20} /></div>
            <div>
              <span>Payout Flow</span>
              <strong>Instant Settle</strong>
            </div>
          </motion.article>
        </div>

        <div className="journey-grid-compact">
          {[
            { step: 1, title: "Login", sub: "Phone + OTP", icon: <User size={14} /> },
            { step: 2, title: "Details", sub: "Platform/Zone", icon: <MapPin size={14} /> },
            { step: 3, title: "Cover", sub: "Activate", icon: <Shield size={14} /> },
            { step: 4, title: "Manage", sub: "Dashboard", icon: <LayoutDashboard size={14} /> }
          ].map((item, idx) => (
            <motion.div
              key={idx}
              className="journey-item-compact"
              whileHover={{ scale: 1.02 }}
            >
              <div className="step-num-small">{item.step}</div>
              <div className="item-content-small">
                <strong>{item.title}</strong>
                <small>{item.sub}</small>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <motion.div
        className="signal-card"
        variants={fadeInUp}
        whileHover={{ boxShadow: "0 20px 40px rgba(0,0,0,0.3)" }}
      >
        <div className="signal-head">
          <div className="live-tag">
            <div className="pulse-dot-red" />
            <span>Live Feed</span>
          </div>
          <div className="signal-content">
            <p className="eyebrow">Real-time Disturbance Monitor</p>
            {disruptionBanner ? (
              <>
                <h2 className="text-glow-red">{disruptionBanner.event_type.replace(/_/g, " ")} Alert</h2>
                <div className="zone-indicator">
                  <MapPin size={16} />
                  <span>Zone {prettyZone(disruptionBanner.zone_id)} is restricted</span>
                </div>
              </>
            ) : (
              <>
                <h2>City looks clear</h2>
                <p className="signal-copy">No active disruptions detected. Secure your income before the next shift.</p>
              </>
            )}
          </div>
        </div>

        <div className="event-metrics-new">
          <div className="event-stat">
            <AlertTriangle size={18} className={disruptionBanner ? "text-accent" : "text-dim"} />
            <div>
              <span>Severity</span>
              <strong>{disruptionBanner ? `${disruptionBanner.severity}/4` : "0/4"}</strong>
            </div>
          </div>
          <div className="event-stat">
            <ShieldCheck size={18} className="text-teal" />
            <div>
              <span>Status</span>
              <strong>{disruptionBanner?.verified ? "Verified" : "Monitoring"}</strong>
            </div>
          </div>
          <div className="event-stat">
            <Clock size={18} className="text-dim" />
            <div>
              <span>Duration</span>
              <strong>{disruptionBanner ? "Active" : "Stable"}</strong>
            </div>
          </div>
        </div>

        <div className="signal-footer-new">
          <div className="footer-info">
            <Info size={14} />
            <span>Backend synchronizing every 30s</span>
          </div>
          <div className="data-stats">
            <strong>{disruptions.length}</strong>
            <span>Active Signals</span>
          </div>
        </div>
      </motion.div>
    </motion.section>
  );
}
