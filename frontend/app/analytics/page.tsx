"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr } from "@/lib/format";
import { Card, Loading, Err, PageHeader, Table, THead, TH, TD, TRow, Avatar, EmptyState } from "@/components/ui";
import { Reveal } from "@/components/motion";
import { BellRing } from "lucide-react";

export default function Analytics() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const load = () => {
    Promise.all([api("/api/analytics/products"), api("/api/analytics/deterioration"), api("/api/analytics/alerts")])
      .then(([products, deterioration, alerts]) => setData({ products, deterioration, alerts })).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!data) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader eyebrow="Insight" title="ANALYTICS" desc="Product risk, behavioral deterioration, and live alerts." />
      {data.alerts.length > 0 && (
        <Reveal>
          <Card title={`Alerts (${data.alerts.length})`}>
            <div className="space-y-1.5">
              {data.alerts.slice(0, 8).map((alert: any, i: number) => (
                <div key={i} className="text-[13px] rounded-xl px-3 py-2 border border-rose-500/20 bg-rose-500/10 flex items-center gap-2" style={{ color: "var(--text-1)" }}>
                  <BellRing size={14} className="shrink-0 text-risk-high" />
                  {alert.id ? <Link href={`/customers/${alert.id}`} className="font-bold hover:underline shrink-0" style={{ color: "#EC2F8B" }}>{alert.customer}</Link> : null}
                  <span className="truncate">{alert.msg}</span>
                </div>
              ))}
            </div>
          </Card>
        </Reveal>
      )}
      <div className="grid md:grid-cols-2 gap-4 items-start">
        <Reveal>
          <Card title="Product analytics" sub="Customers, high-risk count, revenue at risk">
            <Table>
              <THead><TH>Product</TH><TH right>Cust.</TH><TH right>High-risk</TH><TH right>RaR</TH></THead>
              <tbody>{data.products.map((row: any) => (
                <TRow key={row.product}><TD><span className="font-semibold">{row.product}</span></TD>
                  <TD right>{row.customers}</TD><TD right><span className="font-bold text-risk-high tnum">{row.high_risk}</span></TD>
                  <TD right><b>{inr(row.rar)}</b></TD></TRow>
              ))}</tbody>
            </Table>
          </Card>
        </Reveal>
        <Reveal delay={0.05}>
          <Card title="Behavioral deterioration" sub="Declining transactions, balances, engagement + rising complaints/failures">
            {data.deterioration.length === 0 ? (
              <EmptyState title="No deterioration signals" hint="Portfolio behavior looks stable right now." />
            ) : (
              <div className="space-y-1 max-h-96 overflow-y-auto pr-1">
                {data.deterioration.slice(0, 25).map((row: any) => (
                  <div key={row.id} className="flex items-center gap-2.5 text-sm py-2 border-b" style={{ borderColor: "var(--border)" }}>
                    <Avatar name={row.name} size={28} />
                    <Link href={`/customers/${row.id}`} className="font-semibold hover:underline shrink-0" style={{ color: "var(--text-1)" }}>{row.name}</Link>
                    <span className="text-xs truncate" style={{ color: "var(--text-3)" }}>{row.flags.join(", ")}</span>
                    <span className="ml-auto font-extrabold tnum text-semantic-warning">{row.score}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </Reveal>
      </div>
    </div>
  );
}
