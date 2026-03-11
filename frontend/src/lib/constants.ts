import type { CoverageTier, Platform } from "./api";

export const SESSION_KEY = "gigshield_session_token";
export const DASHBOARD_CACHE_KEY = "gigshield_dashboard_cache";
export const FORM_KEY = "gigshield_form_state";
export const TIER_KEY = "gigshield_selected_tier";
export const PHONE_KEY = "gigshield_login_phone";
export const ADMIN_KEY = "gigshield_admin_key";
export const TAB_KEY = "gigshield_active_tab";
export const INSTALL_DISMISSED_KEY = "gigshield_install_dismissed";

export const platformOptions: { value: Platform; label: string }[] = [
  { value: "zomato", label: "Zomato" },
  { value: "swiggy", label: "Swiggy" },
  { value: "zepto", label: "Zepto" },
  { value: "blinkit", label: "Blinkit" },
];

export const cityZones = {
  Chennai: [
    { label: "Zone 4 · Flood-prone corridors", value: "chennai_zone_4" },
    { label: "Zone 2 · Core delivery cluster", value: "chennai_zone_2" },
  ],
  Mumbai: [
    { label: "Zone 2 · Western suburban routes", value: "mumbai_zone_2" },
    { label: "Zone 5 · High rain exposure belt", value: "mumbai_zone_5" },
  ],
  Bengaluru: [
    { label: "Zone 3 · Peak order tech corridor", value: "bengaluru_zone_3" },
    { label: "Zone 6 · Outer ring delivery arc", value: "bengaluru_zone_6" },
  ],
  Delhi: [
    { label: "Zone 1 · Central operations block", value: "delhi_zone_1" },
    { label: "Zone 7 · High AQI alert pocket", value: "delhi_zone_7" },
  ],
} as const;

export const tierCards: { id: CoverageTier; title: string; helper: string }[] = [
  { id: "basic", title: "Basic", helper: "Rain + flood cover" },
  { id: "standard", title: "Standard", helper: "Best for daily riders" },
  { id: "premium", title: "Premium", helper: "Full city shutdown cover" },
];
