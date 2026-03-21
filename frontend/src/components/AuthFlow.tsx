import { motion, AnimatePresence, type Variants } from "framer-motion";
import { 
  Shield, 
  User, 
  Smartphone, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle2, 
  MapPin, 
  Wallet,
  Building2,
  Clock,
  Briefcase
} from "lucide-react";
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

const containerVariants: Variants = {
  initial: { opacity: 0, scale: 0.95, y: 20 },
  animate: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, scale: 1.05, y: -20, transition: { duration: 0.4 } }
};

const stepVariants: Variants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.3 } }
};

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
        <motion.div 
          className="shield-bg"
          initial={{ opacity: 0, rotate: -10 }}
          animate={{ opacity: 0.05, rotate: 0 }}
          transition={{ duration: 2, repeat: Infinity, repeatType: "reverse" }}
        >
          <Shield size={600} strokeWidth={0.5} />
        </motion.div>
      </div>

      <section className="auth-shell">
        <motion.div 
          className="auth-container"
          variants={containerVariants}
          initial="initial"
          animate="animate"
          layout
        >
          <div className="auth-visual-side">
            <motion.div 
              className="brand-logo"
              whileHover={{ rotate: 10, scale: 1.1 }}
            >
              <div className="logo-icon">
                <Shield size={32} className="text-accent" />
                <div className="logo-sparkle" />
              </div>
            </motion.div>
            
            <div className="auth-visual-content">
              <motion.p 
                className="eyebrow"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                GigShield 2.0
              </motion.p>
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                Empowering the next billion earners.
              </motion.h2>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                Join the only parametric micro-insurance built for the freedom and flexibility of Indian gig workers.
              </motion.p>
            </div>

            <div className="auth-visual-footer">
              <motion.div className="trust-stat" whileHover={{ y: -5 }}>
                <div className="stat-icon"><User size={20} /></div>
                <div>
                  <strong>15k+</strong>
                  <span>Workers Covered</span>
                </div>
              </motion.div>
              <motion.div className="trust-stat" whileHover={{ y: -5 }}>
                <div className="stat-icon"><CheckCircle2 size={20} /></div>
                <div>
                  <strong>₹ 40L+</strong>
                  <span>Claims Settled</span>
                </div>
              </motion.div>
            </div>
          </div>

          <div className="auth-form-side">
            <AnimatePresence mode="wait">
              {stage === "phone" && (
                <motion.div 
                  key="phone"
                  className="flow-step"
                  variants={stepVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                >
                  <div className="form-header">
                    <h3>Get Started</h3>
                    <p className="flow-copy">Welcome to the future of financial safety. Enter your number to continue.</p>
                  </div>

                  <div className="input-container">
                    <Field label="Phone number">
                      <div className="input-field-wrapper">
                        <Smartphone size={20} className="input-icon-lucide" />
                        <input
                          className="premium-input-new"
                          value={loginPhone}
                          onChange={(event) => setLoginPhone(event.target.value.replace(/\D/g, "").slice(0, 10))}
                          placeholder="9876543210"
                          autoFocus
                          type="tel"
                        />
                      </div>
                    </Field>
                  </div>

                  <div className="flow-actions mt-lg">
                    <motion.button 
                      className="primary-action full-width glossy"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={onStartLogin} 
                      disabled={isRequestingOtp}
                    >
                      {isRequestingOtp ? (
                        <span className="flex-center gap-sm">
                          <div className="spinner-small" /> Securing Session...
                        </span>
                      ) : (
                        <span className="flex-center gap-sm">
                          Secure Login <ArrowRight size={18} />
                        </span>
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              )}

              {stage === "profile" && (
                <motion.div 
                  key="profile"
                  className="flow-step"
                  variants={stepVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                >
                  <div className="form-header">
                    <h3>Build Your Profile</h3>
                    <p className="flow-copy">Calibrating protection rates for your specific work profile.</p>
                  </div>

                  <div className="platform-grid-new">
                    {platformOptions.map((option) => (
                      <motion.button
                        key={option.value}
                        type="button"
                        className={`platform-pill ${form.platform === option.value ? "active" : ""}`}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setForm((current) => ({ ...current, platform: option.value }))}
                      >
                        <Building2 size={16} />
                        <span>{option.label}</span>
                      </motion.button>
                    ))}
                  </div>

                  <div className="field-grid">
                    <Field label="Full Name">
                      <div className="input-field-wrapper">
                        <User size={18} className="input-icon-lucide" />
                        <input
                          value={form.name}
                          onChange={(event) => setForm({ ...form, name: event.target.value })}
                          placeholder="e.g. Rahul Verma"
                        />
                      </div>
                    </Field>
                    <Field label="City">
                      <div className="input-field-wrapper">
                        <MapPin size={18} className="input-icon-lucide" />
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
                      </div>
                    </Field>
                    <Field label="Zone">
                      <div className="input-field-wrapper">
                        <MapPin size={18} className="input-icon-lucide" />
                        <select value={form.zoneId} onChange={(event) => setForm({ ...form, zoneId: event.target.value })}>
                          {currentZones.map((zone) => (
                            <option key={zone.value} value={zone.value}>
                              {zone.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </Field>
                    <Field label="Weekly Earnings">
                      <div className="input-field-wrapper">
                        <Wallet size={18} className="input-icon-lucide" />
                        <input
                          value={form.avgWeeklyEarnings}
                          onChange={(event) => setForm({ ...form, avgWeeklyEarnings: event.target.value.replace(/[^\d.]/g, "") })}
                          placeholder="₹ 3,500"
                        />
                      </div>
                    </Field>
                  </div>

                  <motion.label 
                    className="premium-checkbox"
                    whileHover={{ x: 5 }}
                  >
                    <div className="checkbox-wrapper">
                      <input
                        type="checkbox"
                        checked={form.kycVerified}
                        onChange={(event) => setForm({ ...form, kycVerified: event.target.checked })}
                      />
                      <div className="checkbox-visual"><CheckCircle2 size={14} /></div>
                    </div>
                    <span>KYC verified via {form.platform} platform</span>
                  </motion.label>

                  <div className="flow-actions mt-lg">
                    <motion.button 
                      className="secondary-action-new" 
                      whileHover={{ scale: 1.05 }}
                      onClick={onBack}
                    >
                      <ArrowLeft size={18} />
                    </motion.button>
                    <motion.button 
                      className="primary-action flex-1 glossy" 
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={onRegister} 
                      disabled={isRegistering}
                    >
                      {isRegistering ? "Saving..." : "Create Profile"}
                    </motion.button>
                  </div>
                </motion.div>
              )}

              {stage === "otp" && (
                <motion.div 
                  key="otp"
                  className="flow-step"
                  variants={stepVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                >
                  <div className="form-header">
                    <h3>Verify Identity</h3>
                    <p className="flow-copy">Enter the security code sent to <strong>+91 {loginPhone}</strong></p>
                  </div>

                  <Field label="Security Code">
                    <div className="otp-input-container">
                      <input
                        className="otp-field-new"
                        value={otpCode}
                        onChange={(event) => setOtpCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                        placeholder="0 0 0 0 0 0"
                        autoFocus
                      />
                      <div className="otp-glow" />
                    </div>
                  </Field>

                  {mockOtpHint && import.meta.env.VITE_API_BASE_URL?.includes("localhost") && (
                    <motion.div 
                      className="hint-banner"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                    >
                      <Clock size={14} />
                      <span>Development Bypass Code: <strong>{mockOtpHint}</strong></span>
                    </motion.div>
                  )}

                  <div className="flow-actions mt-lg">
                    <motion.button 
                      className="primary-action full-width glossy" 
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={onVerifyOtp} 
                      disabled={isVerifyingOtp}
                    >
                      {isVerifyingOtp ? "Validating..." : "Enter Workspace"}
                    </motion.button>
                  </div>

                  <div className="otp-footer-links">
                    <button className="text-link" type="button" onClick={onRequestOtp} disabled={isRequestingOtp}>
                      {isRequestingOtp ? "Sending..." : "Resend Code"}
                    </button>
                    <div className="dot-divider" />
                    <button className="text-link" type="button" onClick={onBack}>
                      Change Number
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </section>
    </>
  );
}
