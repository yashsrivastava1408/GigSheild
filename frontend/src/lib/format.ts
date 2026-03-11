export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export function inferCity(zoneId: string): "Chennai" | "Mumbai" | "Bengaluru" | "Delhi" {
  if (zoneId.startsWith("mumbai")) return "Mumbai";
  if (zoneId.startsWith("bengaluru")) return "Bengaluru";
  if (zoneId.startsWith("delhi")) return "Delhi";
  return "Chennai";
}

export function prettyZone(zoneId: string): string {
  return zoneId.replace(/_/g, " ").replace(/\b\w/g, (char: string) => char.toUpperCase());
}
