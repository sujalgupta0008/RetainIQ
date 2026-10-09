"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, PrioBadge, Loading, Err, Select, PageHeader, Avatar, Table, THead, TH, TD, TRow, EmptyState } from "@/components/ui";
import { Reveal } from "@/components/motion";
import { Star } from "lucide-react";

export default function NextBestActions() {
  const [rows, setRows] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const [priority, setPriority] = useState("");
  const load = () => {
    setErr("");
    api(`/api/recommendations?priority=${priority}&limit=100`).then(setRows).catch((e) => setErr(e.message));
  };
  useEffect(load, [priority]);
  if (err) return <Err msg={err} retry={load} />;
  if (!rows) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader eyebrow="Queue" title="NEXT BEST ACTIONS" desc="Prioritized retention queue — each recommendation maximizes expected net value."
        actions={
          <Select aria-label="Priority filter" className="!w-48" value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="">All priorities</option><option>Critical</option><option>High Priority</option><option>Monitor</option><option>Low Priority</option>
          </Select>
        } />
      <Reveal>
        <Card>
          {rows.length === 0 ? (
            <EmptyState icon={<Star size={20} />} title="Queue is clear" hint="No recommendations for this priority filter." />
          ) : (
            <Table>
              <THead><TH>Customer</TH><TH>Priority</TH><TH>Action</TH><TH>Why</TH><TH right>Cost</TH><TH right>Success</TH><TH right>Exp. ROI</TH></THead>
              <tbody>
                {rows.map((row: any) => (
                  <TRow key={row.customer_id}>
                    <TD>
                      <Link href={`/customers/${row.customer_id}`} className="flex items-center gap-2 font-semibold hover:underline" style={{ color: "var(--text-1)" }}>
                        <Avatar name={row.name} size={28} />{row.name}
                      </Link>
                      <div className="text-[11px] tnum mt-0.5 ml-9" style={{ color: "var(--text-3)" }}>{pct(row.proba)} risk · {inr(row.rar)} RaR</div>
                    </TD>
                    <TD><PrioBadge p={row.priority} /></TD>
                    <TD><span className="capitalize font-semibold">{row.action.replaceAll("_", " ")}</span></TD>
                    <TD><span className="text-xs block max-w-64 whitespace-normal leading-relaxed" style={{ color: "var(--text-2)" }}>{row.reason}</span></TD>
                    <TD right>{inr(row.cost)}</TD>
                    <TD right>{pct(row.success)}</TD>
                    <TD right><b className="text-semantic-success tnum">{(row.roi * 100).toFixed(0)}%</b></TD>
                  </TRow>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      </Reveal>
    </div>
  );
}
