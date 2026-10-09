"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { Card, RiskBadge, PrioBadge, Loading, Err, Input, Select, PageHeader, Avatar, Table, THead, TH, TD, TRow, Pagination, EmptyState } from "@/components/ui";
import { Reveal } from "@/components/motion";
import { Users } from "lucide-react";

export default function Customers() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState("");
  const [segment, setSegment] = useState("");
  const [sort, setSort] = useState("rar");
  const [page, setPage] = useState(1);

  const load = () => {
    const params = new URLSearchParams({ search, risk, segment, sort, page: String(page), page_size: "20" });
    api(`/api/customers?${params}`).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(() => { setErr(""); load(); }, [risk, segment, sort, page]);
  useEffect(() => { const t = setTimeout(() => { setPage(1); setErr(""); load(); }, 400); return () => clearTimeout(t); }, [search]);

  return (
    <div className="space-y-4">
      <PageHeader eyebrow="Portfolio" title="CUSTOMERS" desc="Ranked by revenue at risk. Click any row for the 360° view." />
      <Reveal>
        <Card>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2.5">
            <Input placeholder="Search name…" aria-label="Search name" value={search} onChange={(e) => setSearch(e.target.value)} />
            <Select aria-label="Risk filter" value={risk} onChange={(e) => setRisk(e.target.value)}>
              <option value="">All risk</option><option>High</option><option>Medium</option><option>Low</option>
            </Select>
            <Select aria-label="Segment filter" value={segment} onChange={(e) => setSegment(e.target.value)}>
              <option value="">All segments</option><option>Mass</option><option>Affluent</option><option>HNI</option><option>SME</option>
            </Select>
            <Select aria-label="Sort" value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="rar">Sort: Revenue at risk</option><option value="proba">Sort: Churn prob</option>
              <option value="clv">Sort: CLV</option><option value="name">Sort: Name</option>
            </Select>
            <div className="text-[13px] self-center tnum" style={{ color: "var(--text-2)" }}>{data ? `${data.total.toLocaleString("en-IN")} customers` : ""}</div>
          </div>
        </Card>
      </Reveal>
      {err ? <Err msg={err} retry={load} /> : !data ? <Loading /> : (
        <Reveal>
          <Card>
            {data.items.length === 0 ? (
              <EmptyState icon={<Users size={20} />} title="No customers match" hint="Loosen the filters or search to see the ranked queue." />
            ) : (
              <Table>
                <THead><TH>Customer</TH><TH>Segment</TH><TH>Risk</TH><TH right>Churn prob</TH><TH right>CLV</TH><TH right>Revenue at risk</TH><TH>Next action</TH><TH>Priority</TH></THead>
                <tbody>
                  {data.items.map((cust: any) => (
                    <TRow key={cust.id}>
                      <TD>
                        <Link href={`/customers/${cust.id}`} className="flex items-center gap-2.5 font-semibold hover:underline" style={{ color: "var(--text-1)" }}>
                          <Avatar name={cust.name} size={30} risk={cust.band} />{cust.name}
                        </Link>
                      </TD>
                      <TD><span style={{ color: "var(--text-2)" }}>{cust.segment}</span></TD>
                      <TD><RiskBadge band={cust.band} /></TD>
                      <TD right>{pct(cust.proba)}</TD>
                      <TD right>{inr(cust.clv)}</TD>
                      <TD right><b>{inr(cust.rar)}</b></TD>
                      <TD><span className="text-xs capitalize" style={{ color: "var(--text-2)" }}>{cust.action.replaceAll("_", " ")}</span></TD>
                      <TD><PrioBadge p={cust.priority} /></TD>
                    </TRow>
                  ))}
                </tbody>
              </Table>
            )}
            <Pagination page={data.page} total={data.total} pageSize={data.page_size} onPage={setPage} />
          </Card>
        </Reveal>
      )}
    </div>
  );
}
