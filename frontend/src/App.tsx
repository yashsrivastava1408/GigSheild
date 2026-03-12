import { startTransition, useEffect, useMemo, useState } from "react";

import {
  approveAdminClaim,
  createPolicy,
  DEFAULT_ADMIN_KEY,
  expirePolicies,
  getCurrentWorker,
  getPremiumQuote,
  listAdminClaims,
  listClaims,
  listDisruptions,
  listFraudLogs,
  listPolicies,
  listPayouts,
  rejectAdminClaim,
  registerWorker,
  requestOtp,
  syncWeather,
  verifyOtp,
  type AdminOpsPolicyExpiryResult,
  type AdminOpsWeatherSyncResult,
  type Claim,
  type CoverageTier,
  type DisruptionEvent,
  type FraudLog,
  type Policy,
  type Payout,
  type QuoteResponse,
  type Worker,
} from "./lib/api";
import {
  ADMIN_KEY,
  DASHBOARD_CACHE_KEY,
  FORM_KEY,
  INSTALL_DISMISSED_KEY,
  PHONE_KEY,
  SESSION_KEY,
  TAB_KEY,
  TIER_KEY,
} from "./lib/constants";
import { formatCurrency, inferCity } from "./lib/format";
import { usePersistentState } from "./lib/state";
import { AdminConsole } from "./components/AdminConsole";
import { AuthFlow, type AuthStage, type FormState } from "./components/AuthFlow";
import { HeroSection } from "./components/HeroSection";
import { WorkerDashboard } from "./components/WorkerDashboard";

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

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
};

type AppRoute = "worker" | "admin";

function getRouteFromPath(pathname: string): AppRoute {
  return pathname.startsWith("/admin") ? "admin" : "worker";
}

export default function App() {
  const [route, setRoute] = useState<AppRoute>(() => getRouteFromPath(window.location.pathname));
  const [form, setForm] = usePersistentState<FormState>(FORM_KEY, initialFormState);
  const [selectedTier, setSelectedTier] = usePersistentState<CoverageTier>(TIER_KEY, "standard");
  const [worker, setWorker] = useState<Worker | null>(null);
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [payouts, setPayouts] = useState<Payout[]>([]);
  const [disruptions, setDisruptions] = useState<DisruptionEvent[]>([]);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(SESSION_KEY));
  const [otpCode, setOtpCode] = useState("");
  const [mockOtpHint, setMockOtpHint] = useState<string | null>(null);
  const [loginPhone, setLoginPhone] = usePersistentState<string>(PHONE_KEY, "");
  const [adminKey, setAdminKey] = usePersistentState<string>(ADMIN_KEY, DEFAULT_ADMIN_KEY);
  const [adminClaims, setAdminClaims] = useState<Claim[]>([]);
  const [fraudLogs, setFraudLogs] = useState<FraudLog[]>([]);
  const [latestWeatherSync, setLatestWeatherSync] = useState<AdminOpsWeatherSyncResult[] | null>(null);
  const [latestPolicyExpiry, setLatestPolicyExpiry] = useState<AdminOpsPolicyExpiryResult | null>(null);
  const [activeTab, setActiveTab] = usePersistentState<"overview" | "history">(TAB_KEY, "overview");
  const [authStage, setAuthStage] = useState<AuthStage>("phone");
  const [status, setStatus] = useState(
    "Cover every working week with fast onboarding, simple pricing, and payout support when disruption hits.",
  );
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isBooting, setIsBooting] = useState(true);
  const [isRequestingOtp, setIsRequestingOtp] = useState(false);
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [isFetchingQuote, setIsFetchingQuote] = useState(false);
  const [isBuying, setIsBuying] = useState(false);
  const [isLoadingAdmin, setIsLoadingAdmin] = useState(false);
  const [isRunningWeatherSync, setIsRunningWeatherSync] = useState(false);
  const [isRunningPolicyExpiry, setIsRunningPolicyExpiry] = useState(false);
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstallDismissed, setIsInstallDismissed] = usePersistentState<boolean>(INSTALL_DISMISSED_KEY, false);
  const [isAdminPromptOpen, setIsAdminPromptOpen] = useState(false);
  const [adminPromptValue, setAdminPromptValue] = useState("");

  const canRegister = useMemo(
    () =>
      form.name.trim().length >= 2 &&
      /^\d{10}$/.test(form.phone) &&
      Number(form.avgWeeklyEarnings) > 0 &&
      Number(form.tenureDays) >= 0,
    [form],
  );

  useEffect(() => {
    const onPopState = () => {
      setRoute(getRouteFromPath(window.location.pathname));
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    const onShortcut = (event: KeyboardEvent) => {
      if (event.key === ";" && event.ctrlKey) {
        event.preventDefault();
        setIsAdminPromptOpen(true);
      }
    };
    window.addEventListener("keydown", onShortcut);
    return () => window.removeEventListener("keydown", onShortcut);
  }, []);

  useEffect(() => {
    const handleBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      if (!isInstallDismissed) {
        setInstallEvent(event as BeforeInstallPromptEvent);
      }
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    return () => window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
  }, [isInstallDismissed]);

  useEffect(() => {
    const cachedDashboard = localStorage.getItem(DASHBOARD_CACHE_KEY);
    if (cachedDashboard) {
      try {
        const parsed = JSON.parse(cachedDashboard) as {
          worker: Worker | null;
          policies: Policy[];
          claims: Claim[];
          payouts: Payout[];
          disruptions: DisruptionEvent[];
        };
        setWorker(parsed.worker);
        setPolicies(parsed.policies);
        setClaims(parsed.claims);
        setPayouts(parsed.payouts);
        setDisruptions(parsed.disruptions);
      } catch {
        localStorage.removeItem(DASHBOARD_CACHE_KEY);
      }
    }

    async function bootstrap() {
      try {
        const activeDisruptions = await listDisruptions();
        setDisruptions(activeDisruptions);

        if (token) {
          const currentWorker = await getCurrentWorker(token);
          setWorker(currentWorker);
          hydrateFormFromWorker(currentWorker);
          setStatus(`Welcome back, ${currentWorker.name.split(" ")[0]}. Review your policy, claims, and payouts.`);
          await loadDashboard(currentWorker.id);
        }
      } catch {
        localStorage.removeItem(SESSION_KEY);
        setToken(null);
      } finally {
        setIsBooting(false);
      }
    }

    void bootstrap();
  }, []);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState !== "visible") {
        return;
      }
      void listDisruptions().then(setDisruptions).catch(() => undefined);
      if (worker) {
        void loadDashboard(worker.id);
      }
    };

    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [worker]);

  useEffect(() => {
    if (!notice) {
      return;
    }
    const timeout = window.setTimeout(() => setNotice(null), 2600);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  useEffect(() => {
    localStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify({ worker, policies, claims, payouts, disruptions }));
  }, [worker, policies, claims, payouts, disruptions]);

  useEffect(() => {
    setQuote(null);
  }, [selectedTier, form.platform, form.zoneId, form.avgWeeklyEarnings, form.tenureDays]);

  useEffect(() => {
    if (!["overview", "history"].includes(activeTab)) {
      setActiveTab("overview");
    }
  }, [activeTab, setActiveTab]);

  function navigateTo(nextRoute: AppRoute) {
    const nextPath = nextRoute === "admin" ? "/admin" : "/";
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
    }
    setRoute(nextRoute);
    if (nextRoute === "admin") {
      void loadAdminPanel();
    }
  }

  function hydrateFormFromWorker(currentWorker: Worker) {
    setForm((current) => ({
      ...current,
      name: currentWorker.name,
      phone: currentWorker.phone,
      platform: currentWorker.platform,
      zoneId: currentWorker.zone_id,
      city: inferCity(currentWorker.zone_id),
      avgWeeklyEarnings: String(currentWorker.avg_weekly_earnings),
      tenureDays: String(currentWorker.tenure_days),
      kycVerified: currentWorker.kyc_verified,
    }));
    setLoginPhone(currentWorker.phone);
  }

  async function loadDashboard(workerId: string) {
    const [workerPolicies, workerClaims, workerPayouts, activeDisruptions] = await Promise.all([
      listPolicies(workerId),
      listClaims(workerId),
      listPayouts(workerId),
      listDisruptions(),
    ]);

    startTransition(() => {
      setPolicies(workerPolicies);
      setClaims(workerClaims);
      setPayouts(workerPayouts);
      setDisruptions(activeDisruptions);
    });
  }

  async function loadAdminPanel(adminSecret = adminKey) {
    if (!adminSecret.trim()) {
      setError("Enter the admin API key to load the review queue.");
      return;
    }

    setError(null);
    setIsLoadingAdmin(true);
    try {
      const [claimsFeed, fraudFeed] = await Promise.all([listAdminClaims(adminSecret), listFraudLogs(adminSecret)]);
      setAdminClaims(claimsFeed);
      setFraudLogs(fraudFeed);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load admin data.");
    } finally {
      setIsLoadingAdmin(false);
    }
  }

  async function handleSyncWeather() {
    if (!adminKey.trim()) {
      setError("Enter the admin API key to run weather sync.");
      return;
    }

    setError(null);
    setIsRunningWeatherSync(true);
    try {
      const createdEvents = await syncWeather(adminKey);
      setLatestWeatherSync(createdEvents);
      setDisruptions(await listDisruptions());
      setNotice(
        createdEvents.length > 0
          ? `Weather sync created ${createdEvents.length} event(s).`
          : "Weather sync ran with no new events.",
      );
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not run weather sync.");
    } finally {
      setIsRunningWeatherSync(false);
    }
  }

  async function handleExpirePolicies() {
    if (!adminKey.trim()) {
      setError("Enter the admin API key to expire policies.");
      return;
    }

    setError(null);
    setIsRunningPolicyExpiry(true);
    try {
      const result = await expirePolicies(adminKey);
      setLatestPolicyExpiry(result);
      if (worker) {
        await loadDashboard(worker.id);
      }
      setNotice(`Policy expiry run completed. ${result.expired_policies} policies expired.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not expire policies.");
    } finally {
      setIsRunningPolicyExpiry(false);
    }
  }

  async function handleStartLogin() {
    if (!/^\d{10}$/.test(loginPhone)) {
      setError("Enter a valid 10-digit phone number.");
      return;
    }

    setError(null);
    setForm((current) => ({ ...current, phone: loginPhone }));
    setIsRequestingOtp(true);

    try {
      const response = await requestOtp(loginPhone);
      setMockOtpHint(response.mock_otp_code ?? null);
      setAuthStage("otp");
      setStatus("OTP sent. Enter the code to open the worker account.");
      setNotice(response.mock_otp_code ? `Mock OTP: ${response.mock_otp_code}` : "OTP sent.");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Could not continue.";
      if (message.toLowerCase().includes("worker not found")) {
        setAuthStage("profile");
        setStatus("New worker detected. Fill your work details to create the account.");
      } else {
        setError(message);
      }
    } finally {
      setIsRequestingOtp(false);
    }
  }

  async function handleRegister() {
    if (!canRegister) {
      setError("Fill every worker detail before continuing.");
      return;
    }

    setError(null);
    setIsRegistering(true);

    try {
      const newWorker = await registerWorker({
        name: form.name.trim(),
        phone: form.phone,
        platform: form.platform,
        zone_id: form.zoneId,
        avg_weekly_earnings: Number(form.avgWeeklyEarnings),
        tenure_days: Number(form.tenureDays),
        kyc_verified: form.kycVerified,
      });
      setWorker(newWorker);
      hydrateFormFromWorker(newWorker);
      setStatus("Profile saved. Verify the OTP to enter the policy dashboard.");
      setNotice("Worker profile created.");
      await handleRequestOtp(newWorker.phone);
      setAuthStage("otp");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not create the worker profile.");
    } finally {
      setIsRegistering(false);
    }
  }

  async function handleRequestOtp(phoneOverride?: string) {
    const phone = phoneOverride ?? loginPhone;
    if (!/^\d{10}$/.test(phone)) {
      setError("Enter a valid 10-digit phone number.");
      return;
    }

    setError(null);
    setIsRequestingOtp(true);
    try {
      const response = await requestOtp(phone);
      setLoginPhone(phone);
      setMockOtpHint(response.mock_otp_code ?? null);
      setStatus("OTP sent. Enter the code to continue.");
      setNotice(response.mock_otp_code ? `Mock OTP: ${response.mock_otp_code}` : "OTP sent.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not request OTP.");
    } finally {
      setIsRequestingOtp(false);
    }
  }

  async function handleVerifyOtp() {
    if (!/^\d{6}$/.test(otpCode)) {
      setError("Enter the 6-digit OTP.");
      return;
    }

    setError(null);
    setIsVerifyingOtp(true);
    try {
      const session = await verifyOtp(loginPhone, otpCode);
      localStorage.setItem(SESSION_KEY, session.access_token);
      setToken(session.access_token);
      setWorker(session.worker);
      hydrateFormFromWorker(session.worker);
      setActiveTab("overview");
      setStatus(`Dashboard ready for ${session.worker.name}. Choose a policy and review live claim activity.`);
      setNotice("Logged in successfully.");
      await loadDashboard(session.worker.id);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "OTP verification failed.");
    } finally {
      setIsVerifyingOtp(false);
    }
  }

  async function handleQuote() {
    if (!canRegister) {
      setError("Complete the worker profile before checking the policy price.");
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
        tenure_days: Number(form.tenureDays),
        trust_score: worker?.trust_score ?? 60,
      });
      setQuote(nextQuote);
      setStatus(
        `Quote ready. ${formatCurrency(nextQuote.weekly_premium)} per week for ${formatCurrency(nextQuote.coverage_amount)} cover.`,
      );
      setNotice(`Quote refreshed: ${formatCurrency(nextQuote.weekly_premium)}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not fetch the policy quote.");
    } finally {
      setIsFetchingQuote(false);
    }
  }

  async function handleBuyPolicy() {
    if (!worker) {
      setError("Log in before buying a policy.");
      return;
    }

    setError(null);
    setIsBuying(true);
    try {
      const policy = await createPolicy(worker.id, selectedTier);
      await loadDashboard(worker.id);
      setStatus(`Policy activated. ${formatCurrency(policy.coverage_amount)} cover is active until ${policy.end_date}.`);
      setNotice("Weekly policy activated.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not activate the policy.");
    } finally {
      setIsBuying(false);
    }
  }

  function logout() {
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(DASHBOARD_CACHE_KEY);
    setToken(null);
    setWorker(null);
    setPolicies([]);
    setClaims([]);
    setPayouts([]);
    setQuote(null);
    setOtpCode("");
    setMockOtpHint(null);
    setAuthStage("phone");
    setStatus("Log in again with your phone to view policies, claims, and payouts.");
    setNotice("Signed out.");
  }

  function handleBackInAuth() {
    setError(null);
    if (authStage === "otp") {
      setAuthStage(worker ? "profile" : "phone");
      return;
    }
    if (authStage === "profile") {
      setAuthStage("phone");
    }
  }

  async function handleInstallApp() {
    if (!installEvent) {
      return;
    }
    await installEvent.prompt();
    const outcome = await installEvent.userChoice;
    if (outcome.outcome === "accepted") {
      setNotice("GigShield installed.");
      setInstallEvent(null);
      return;
    }
    setIsInstallDismissed(true);
    setInstallEvent(null);
  }

  async function handleApproveClaim(claimId: string) {
    await approveAdminClaim(claimId, adminKey);
    setNotice("Claim approved.");
    await loadAdminPanel();
  }

  function handleAdminPromptSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = adminPromptValue.trim();
    if (!trimmed) {
      return;
    }
    setAdminKey(trimmed);
    setIsAdminPromptOpen(false);
    void loadAdminPanel(trimmed);
  }

  function handleAdminPromptClose() {
    setIsAdminPromptOpen(false);
    setAdminPromptValue("");
  }

  async function handleRejectClaim(claimId: string) {
    await rejectAdminClaim(claimId, adminKey);
    setNotice("Claim rejected.");
    await loadAdminPanel();
  }

  if (isBooting) {
    return (
      <main className="app-shell">
        <section className="boot-card">Loading worker dashboard...</section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      {notice ? <div className="notice-toast">{notice}</div> : null}
      {error ? <p className="inline-error global-error">{error}</p> : null}

      {route === "admin" ? (
        <AdminConsole
          adminKey={adminKey}
          setAdminKey={setAdminKey}
          adminClaims={adminClaims}
          fraudLogs={fraudLogs}
          latestWeatherSync={latestWeatherSync}
          latestPolicyExpiry={latestPolicyExpiry}
          isLoadingAdmin={isLoadingAdmin}
          isRunningWeatherSync={isRunningWeatherSync}
          isRunningPolicyExpiry={isRunningPolicyExpiry}
          onLoadAdmin={() => void loadAdminPanel()}
          onSyncWeather={() => void handleSyncWeather()}
          onExpirePolicies={() => void handleExpirePolicies()}
          onApproveClaim={(claimId) => void handleApproveClaim(claimId)}
          onRejectClaim={(claimId) => void handleRejectClaim(claimId)}
          onGoWorker={() => navigateTo("worker")}
        />
      ) : !token || !worker ? (
        <AuthFlow
          stage={authStage}
          form={form}
          setForm={setForm}
          loginPhone={loginPhone}
          setLoginPhone={setLoginPhone}
          otpCode={otpCode}
          setOtpCode={setOtpCode}
          mockOtpHint={mockOtpHint}
          isRegistering={isRegistering}
          isRequestingOtp={isRequestingOtp}
          isVerifyingOtp={isVerifyingOtp}
          onStartLogin={() => void handleStartLogin()}
          onRegister={() => void handleRegister()}
          onRequestOtp={() => void handleRequestOtp()}
          onVerifyOtp={() => void handleVerifyOtp()}
          onBack={handleBackInAuth}
        />
      ) : (
        <>
          <HeroSection
            status={status}
            worker={worker}
            policies={policies}
            claims={claims}
            payouts={payouts}
            disruptions={disruptions}
            installEvent={installEvent}
            onInstall={() => void handleInstallApp()}
            onOpenAdmin={() => navigateTo("admin")}
          />

          <WorkerDashboard
            worker={worker}
            selectedTier={selectedTier}
            setSelectedTier={setSelectedTier}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            quote={quote}
            policies={policies}
            claims={claims}
            payouts={payouts}
            disruptions={disruptions}
            isFetchingQuote={isFetchingQuote}
            isBuying={isBuying}
            onQuote={() => void handleQuote()}
            onBuy={() => void handleBuyPolicy()}
            onLogout={logout}
            onRefresh={() => void loadDashboard(worker.id)}
          />
        </>
      )}

      {isAdminPromptOpen ? (
        <div className="admin-prompt-overlay">
          <form className="admin-prompt" onSubmit={handleAdminPromptSubmit}>
            <h3>Enter admin secret</h3>
            <p>Press Enter to load the admin queue.</p>
            <input
              type="password"
              autoFocus
              value={adminPromptValue}
              onChange={(event) => setAdminPromptValue(event.target.value)}
              placeholder="Paste ADMIN_API_KEY"
            />
            <div className="action-row top-gap">
              <button className="secondary-action" type="button" onClick={handleAdminPromptClose}>
                Cancel
              </button>
              <button className="primary-action" type="submit">
                Unlock admin
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </main>
  );
}
