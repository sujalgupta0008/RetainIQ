export const inr = (n: number | null | undefined): string =>
  n == null || isNaN(Number(n)) ? "—" : "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const pct = (n: number | null | undefined): string =>
  n == null ? "—" : `${(Number(n) * 100).toFixed(1)}%`;
export const num = (n: number | null | undefined): string =>
  n == null ? "—" : Number(n).toLocaleString("en-IN");
