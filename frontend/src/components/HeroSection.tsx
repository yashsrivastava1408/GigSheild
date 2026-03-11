import type { DisruptionEvent, Policy, Claim, Payout, Worker } from "../lib/api";
import { formatDate, prettyZone } from "../lib/format";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
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
}: {
  status: string;
  worker: Worker | null;
  policies: Policy[];
  claims: Claim[];
  payouts: Payout[];
  disruptions: DisruptionEvent[];
  installEvent: BeforeInstallPromptEvent | null;
  onInstall: () => void;
}) {
  const disruptionBanner =
    disruptions.find((event) => worker && event.zone_id === worker.zone_id) ?? disruptions[0] ?? null;

  return (
    <section className="hero-grid">
      <div className="hero-copy">
        <div className="top-banner">
          <span>Income protection platform</span>
          <span>Built for delivery operations</span>
          <span>Live backend integration</span>
        </div>

        <p className="eyebrow">GigShield Worker App</p>
        <h1>Income protection built for delivery workers when the city slows down.</h1>
        <p className="hero-text">{status}</p>

        <div className="hero-actions">
          {installEvent ? (
            <button type="button" className="install-action" onClick={onInstall}>
              Install app
            </button>
          ) : null}
          <div className="micro-badge">{worker ? `Signed in as ${worker.name}` : "Ready for worker onboarding"}</div>
        </div>

        <div className="hero-metrics">
          <article>
            <span>Onboarding</span>
            <strong>Phone + OTP</strong>
          </article>
          <article>
            <span>Cover activation</span>
            <strong>Weekly policy</strong>
          </article>
          <article>
            <span>Payout flow</span>
            <strong>Claims to settlement</strong>
          </article>
        </div>

        <div className="journey-strip">
          <article>
            <span>1</span>
            <strong>Login</strong>
            <small>Phone number and OTP</small>
          </article>
          <article>
            <span>2</span>
            <strong>Worker details</strong>
            <small>Platform, zone, earnings, tenure</small>
          </article>
          <article>
            <span>3</span>
            <strong>Policy checkout</strong>
            <small>Quote, compare, activate</small>
          </article>
          <article>
            <span>4</span>
            <strong>Live dashboard</strong>
            <small>Policies, claims, payouts, admin</small>
          </article>
        </div>

        <div className="quick-strip">
          <div>
            <span>Policies</span>
            <strong>{policies.length}</strong>
          </div>
          <div>
            <span>Claims</span>
            <strong>{claims.length}</strong>
          </div>
          <div>
            <span>Payouts</span>
            <strong>{payouts.length}</strong>
          </div>
        </div>
      </div>

      <div className="signal-card">
        <div className="signal-head">
          <div>
            <p className="eyebrow">Live disruption feed</p>
            {disruptionBanner ? (
              <>
                <h2>{disruptionBanner.event_type.replace(/_/g, " ")} alert</h2>
                <p className="signal-copy">Zone {prettyZone(disruptionBanner.zone_id)} is currently flagged by the backend.</p>
              </>
            ) : (
              <>
                <h2>No active disruption right now</h2>
                <p className="signal-copy">The city feed is clear. Workers can still buy cover before the next disruption window.</p>
              </>
            )}
          </div>
          <div className="signal-status">{worker ? "Dashboard live" : "Web onboarding live"}</div>
        </div>

        {disruptionBanner ? (
          <div className="event-strip">
            <span>Severity {disruptionBanner.severity}/4</span>
            <span>{disruptionBanner.verified ? "Verified trigger" : "Pending verification"}</span>
            <span>Started {formatDate(disruptionBanner.started_at)}</span>
          </div>
        ) : (
          <div className="event-strip">
            <span>Feed online</span>
            <span>Waiting for next event</span>
          </div>
        )}

        <div className="signal-summary">
          <div>
            <span>Current mode</span>
            <strong>{worker ? "Dashboard live" : "Onboarding"}</strong>
          </div>
          <div>
            <span>Backend data</span>
            <strong>{disruptions.length} active signals</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
