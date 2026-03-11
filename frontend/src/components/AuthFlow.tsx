import type { Platform } from "../lib/api";
import { cityZones, platformOptions } from "../lib/constants";
import { Field } from "./Field";

export type FormState = {
  name: string;
  phone: string;
  platform: Platform;
  city: keyof typeof cityZones;
  zoneId: string;
  avgWeeklyEarnings: string;
  tenureDays: string;
  kycVerified: boolean;
};

export type AuthStage = "phone" | "profile" | "otp";

export function AuthFlow({
  stage,
  form,
  setForm,
  loginPhone,
  setLoginPhone,
  otpCode,
  setOtpCode,
  mockOtpHint,
  isRegistering,
  isRequestingOtp,
  isVerifyingOtp,
  onStartLogin,
  onRegister,
  onRequestOtp,
  onVerifyOtp,
  onBack,
}: {
  stage: AuthStage;
  form: FormState;
  setForm: (updater: FormState | ((current: FormState) => FormState)) => void;
  loginPhone: string;
  setLoginPhone: (value: string) => void;
  otpCode: string;
  setOtpCode: (value: string) => void;
  mockOtpHint: string | null;
  isRegistering: boolean;
  isRequestingOtp: boolean;
  isVerifyingOtp: boolean;
  onStartLogin: () => void;
  onRegister: () => void;
  onRequestOtp: () => void;
  onVerifyOtp: () => void;
  onBack: () => void;
}) {
  const currentZones = cityZones[form.city];

  return (
    <>
      <div className="bg-atmosphere">
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
        <svg className="shield-outline" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.5">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      </div>

      <section className="auth-shell">
        <div className="auth-container">
          <div className="auth-visual-side">
            <div className="brand-logo">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M12 8v4M12 16h.01" stroke="var(--teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            
            <div className="auth-visual-content">
              <p className="eyebrow">GigShield 2.0</p>
              <h2>Empowering the next billion earners.</h2>
              <p>Join the only parametric micro-insurance built for the freedom and flexibility of Indian gig workers.</p>
            </div>

            <div className="auth-visual-footer">
              <div className="trust-stat">
                <strong>15k+</strong>
                <span>Workers Covered</span>
              </div>
              <div className="trust-stat">
                <strong>₹ 40L+</strong>
                <span>Claims Settled</span>
              </div>
            </div>
          </div>

          <div className="auth-form-side">
            {stage === "phone" ? (
              <div className="flow-step">
                <div className="form-header">
                  <h3>Get Started</h3>
                  <p className="flow-copy">Welcome to the future of financial safety. Enter your number to continue.</p>
                </div>

                <div className="input-container">
                  <Field label="Phone number">
                    <div className="input-wrapper">
                      <span className="input-icon">🇮🇳</span>
                      <input
                        className="premium-input"
                        value={loginPhone}
                        onChange={(event) => setLoginPhone(event.target.value.replace(/\D/g, "").slice(0, 10))}
                        placeholder="9876543210"
                        autoFocus
                      />
                    </div>
                  </Field>
                </div>

                <div className="flow-actions mt-lg">
                  <button className="primary-action full-width" type="button" onClick={onStartLogin} disabled={isRequestingOtp}>
                    {isRequestingOtp ? "Securing Session..." : "Secure Login →"}
                  </button>
                </div>
              </div>
            ) : null}

            {stage === "profile" ? (
              <div className="flow-step">
                <div className="form-header">
                  <h3>Build Your Profile</h3>
                  <p className="flow-copy">We use these details to calibrate your protection rates in real-time.</p>
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
                      <small>Work platform</small>
                    </button>
                  ))}
                </div>

                <div className="field-grid">
                  <Field label="Full Name">
                    <input
                      value={form.name}
                      onChange={(event) => setForm({ ...form, name: event.target.value })}
                      placeholder="e.g. Rahul Verma"
                    />
                  </Field>
                  <Field label="City">
                    <select
                      value={form.city}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          city: event.target.value as keyof typeof cityZones,
                          zoneId: cityZones[event.target.value as keyof typeof cityZones][0].value,
                        })
                      }
                    >
                      {Object.keys(cityZones).map((city) => (
                        <option key={city}>{city}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Zone">
                    <select value={form.zoneId} onChange={(event) => setForm({ ...form, zoneId: event.target.value })}>
                      {currentZones.map((zone) => (
                        <option key={zone.value} value={zone.value}>
                          {zone.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Weekly Earnings">
                    <input
                      value={form.avgWeeklyEarnings}
                      onChange={(event) => setForm({ ...form, avgWeeklyEarnings: event.target.value.replace(/[^\d.]/g, "") })}
                      placeholder="₹ 3,500"
                    />
                  </Field>
                </div>

                <label className="toggle-row">
                  <input
                    type="checkbox"
                    checked={form.kycVerified}
                    onChange={(event) => setForm({ ...form, kycVerified: event.target.checked })}
                  />
                  <span>KYC verified via {form.platform} platform</span>
                </label>

                <div className="flow-actions mt-lg">
                  <button className="secondary-action" type="button" onClick={onBack}>
                    Back
                  </button>
                  <button className="primary-action flex-1" type="button" onClick={onRegister} disabled={isRegistering}>
                    {isRegistering ? "Saving..." : "Create Profile"}
                  </button>
                </div>
              </div>
            ) : null}

            {stage === "otp" ? (
              <div className="flow-step">
                <div className="form-header">
                  <h3>Verify Account</h3>
                  <p className="flow-copy">We've sent a 6-digit access code to your phone.</p>
                </div>

                <Field label="OTP Access Code">
                  <input
                    className="otp-box-custom"
                    value={otpCode}
                    onChange={(event) => setOtpCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                    placeholder="0 0 0 0 0 0"
                    autoFocus
                  />
                </Field>

                {mockOtpHint && import.meta.env.VITE_API_BASE_URL?.includes("localhost") ? (
                  <div className="mock-hint-pill">
                    Demo Code: <code>{mockOtpHint}</code>
                  </div>
                ) : null}

                <div className="flow-actions mt-lg">
                  <button className="primary-action full-width" type="button" onClick={onVerifyOtp} disabled={isVerifyingOtp}>
                    {isVerifyingOtp ? "Validating..." : "Enter Dashboard"}
                  </button>
                </div>

                <div className="otp-meta-actions">
                  <button className="link-action" type="button" onClick={onRequestOtp} disabled={isRequestingOtp}>
                    {isRequestingOtp ? "Sending..." : "Resend OTP"}
                  </button>
                  <button className="link-action" type="button" onClick={onBack}>
                    Change phone number
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </section>
    </>
  );
}
