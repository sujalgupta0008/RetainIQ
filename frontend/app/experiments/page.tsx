"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, Loading, Err, PageHeader, Table, THead, TH, TD, TRow, EmptyState, Badge } from "@/components/ui";
import { Reveal } from "@/components/motion";
import { FlaskConical } from "lucide-react";

export default function Experiments() {
  const [rows, setRows] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const load = () => api("/api/experiments").then(setRows).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <Err msg={err} retry={load} />;
  if (!rows) return <Loading />;
  return (
    <div className="space-y-4">
      <PageHeader eyebrow="A/B Testing" title="EXPERIMENTS" desc="Every campaign runs an A/B test: 80% treatment, 20% control. Outcomes simulated for demo." />
      <Reveal>
        <Card>
          {rows.length === 0 ? (
            <EmptyState icon={<FlaskConical size={20} />} title="No experiments yet" hint="Launch a campaign to start the first 80/20 test." />
          ) : (
            <Table>
              <THead><TH>Experiment</TH><TH right>Treat / Ctrl n</TH><TH right>Treat ret.</TH><TH right>Ctrl ret.</TH><TH right>Lift</TH><TH right>Revenue</TH><TH right>ROI</TH></THead>
              <tbody>
                {rows.map((exp: any) => (
                  <TRow key={exp.id}>
                    <TD><span className="font-semibold">{exp.name}</span><div className="text-[11px]" style={{ color: "var(--text-3)" }}>{exp.campaign}</div></TD>
                    {exp.results ? (<>
                      <TD right>{exp.results.treat_n} / {exp.results.ctrl_n}</TD>
                      <TD right>{pct(exp.results.treat_ret)}</TD>
                      <TD right>{pct(exp.results.ctrl_ret)}</TD>
                      <TD right><b className="text-semantic-success tnum">{pct(exp.results.lift)}</b></TD>
                      <TD right>{inr(exp.results.revenue)}</TD>
                      <TD right><b className="tnum">{(exp.results.roi * 100).toFixed(1)}%</b></TD>
                    </>) : <TD right colSpan={6}><Badge tone="neutral">pending launch</Badge></TD>}
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
