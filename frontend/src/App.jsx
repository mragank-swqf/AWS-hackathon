import { useEffect, useId, useRef, useState } from "react";
import { api, setCompanyId } from "./api.js";

const SCREENS = [
  ["dashboard", "Dashboard"],
  ["profile", "Company profile"],
  ["applicable", "Applicable regulations"],
  ["updates", "Regulatory updates"],
  ["evidence", "Company evidence"],
  ["results", "Compliance analysis"],
  ["actions", "Actions"],
];

const ORG_TYPES = [
  ["payment_aggregator", "Payment aggregator"],
  ["payment_gateway", "Payment gateway"],
  ["nbfc", "NBFC"],
  ["bank", "Bank"],
  ["payment_bank", "Payments bank"],
  ["lending_platform", "Lending platform"],
  ["prepaid_instrument_issuer", "Prepaid instrument issuer"],
  ["account_aggregator", "Account aggregator"],
  ["other", "Other"],
];

const DOCUMENT_TYPES = [
  ["circular", "Circular"],
  ["master_direction", "Master direction"],
  ["notification", "Notification"],
  ["guideline", "Guideline"],
  ["faq", "FAQ"],
  ["press_release", "Press release"],
];

const EVIDENCE_TYPES = [
  ["policy", "Policy"],
  ["procedure", "Procedure"],
  ["control_description", "Control description"],
  ["audit_report", "Audit report"],
  ["other", "Other"],
];

const DEPARTMENTS = [
  "Compliance",
  "Legal",
  "Risk",
  "Operations",
  "Product",
  "Engineering",
  "Finance",
  "Customer Support",
  "Information Security",
  "Internal Audit",
  "Human Resources",
];

const PROCESS_STEPS = ["queued", "extracting", "chunking", "embedding", "completed"];
const IN_FLIGHT = ["queued", "extracting", "chunking", "embedding"];
const PROCESS_COPY = {
  queued: "Waiting for the worker to start this PDF.",
  extracting: "Reading text from the PDF.",
  chunking: "Splitting the circular into clauses.",
  embedding: "Indexing clauses in Amazon Bedrock.",
};
const ANALYSIS_STEPS = [
  "queued",
  "applicability",
  "requirements",
  "impact",
  "gap_detection",
  "risk",
  "action_plan",
  "verification",
  "completed",
];

const LABELS = {
  queued: "Queued",
  extracting: "Extracting text",
  chunking: "Splitting clauses",
  embedding: "Indexing",
  completed: "Ready",
  failed: "Failed",
  processing: "Working",
  cancelled: "Cancelled",
  pending: "Pending review",
  approved: "Approved",
  rejected: "Rejected",
  applicable: "Applies",
  likely_applicable: "Likely applies",
  uncertain: "Uncertain",
  likely_not_applicable: "Likely does not apply",
  not_applicable: "Does not apply",
  compliant: "Covered",
  partial: "Partly covered",
  non_compliant: "Not covered",
  insufficient_evidence: "Not enough evidence",
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  none: "None",
  verified: "Verified",
  partially_verified: "Partly verified",
  unverified: "Not verified",
  open: "Open",
  in_progress: "In progress",
  blocked: "Blocked",
  done: "Done",
  cited_effective: "Effective date from the source",
  cited_compliance: "Compliance date from the source",
  added: "New",
  modified: "Modified",
  removed: "Removed",
  unchanged: "Unchanged",
  organization_type: "Organization type",
  has_outsourced_operations: "Outsourced operations",
  uses_customer_data: "Customer data",
  seeded: "Indexed from official source",
  crawled: "Downloaded from RBI",
  uploaded: "Uploaded",
  active: "Active",
  superseded: "Superseded",
  kyc_aml: "KYC / AML",
  digital_lending: "Digital lending",
  cybersecurity: "Cybersecurity",
  payments: "Payments",
  outsourcing: "Outsourcing",
  it_governance: "IT governance",
  customer_protection: "Customer protection",
  data: "Data",
  other: "Other",
};

function labelOf(value) {
  if (!value) return "Not set";
  return LABELS[value] || String(value).replaceAll("_", " ");
}

function statusTone(value) {
  if (["completed", "approved", "compliant", "verified", "done", "ok"].includes(value)) {
    return "ok";
  }
  if (
    ["failed", "rejected", "non_compliant", "critical", "blocked", "error"].includes(value)
  ) {
    return "bad";
  }
  if (IN_FLIGHT.includes(value) || (ANALYSIS_STEPS.includes(value) && value !== "completed")) {
    return "busy";
  }
  if (
    [
      "partial",
      "insufficient_evidence",
      "pending",
      "uncertain",
      "high",
      "unverified",
      "partially_verified",
      "processing",
    ].includes(value)
  ) {
    return "warn";
  }
  return "neutral";
}

function Status({ value }) {
  const busy = IN_FLIGHT.includes(value) || (ANALYSIS_STEPS.includes(value) && value !== "completed");
  return (
    <span className={`status status-${statusTone(value)}${busy ? " status-busy" : ""}`}>
      {busy && <span className="spinner" aria-hidden="true" />}
      {labelOf(value)}
    </span>
  );
}

function SourceSheet({ title, body, url, loading, onClose }) {
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    function onKey(event) {
      if (event.key === "Escape") onCloseRef.current();
    }
    window.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, []);

  return (
    <div className="source-layer">
      <button className="source-backdrop" type="button" aria-label="Close source" onClick={onClose} />
      <div className="source-panel" role="dialog" aria-modal="true" aria-labelledby="source-title">
        <div className="source-panel-head">
          <h2 id="source-title">{title}</h2>
          <button className="btn btn-secondary" type="button" onClick={onClose}>
            Close
          </button>
        </div>
        {loading && (
          <p className="muted" role="status">
            Loading the cited passage.
          </p>
        )}
        {body && <blockquote className="excerpt">{body}</blockquote>}
        {url && (
          <p className="source-url">
            <span className="muted">Official URL</span>
            <br />
            {url}
          </p>
        )}
        {url && (
          <div className="actions">
            <a className="btn btn-secondary" href={url} target="_blank" rel="noreferrer">
              Open on RBI website
            </a>
            <button className="btn btn-primary" type="button" onClick={onClose}>
              Close
            </button>
          </div>
        )}
        {!url && !loading && (
          <div className="actions">
            <button className="btn btn-primary" type="button" onClick={onClose}>
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function OfficialSourceButton({ href, title }) {
  const [open, setOpen] = useState(false);
  if (!href) return null;
  return (
    <>
      <button className="btn btn-secondary" type="button" onClick={() => setOpen(true)}>
        Official RBI source
      </button>
      {open && (
        <SourceSheet title={title || "Official RBI source"} url={href} onClose={() => setOpen(false)} />
      )}
    </>
  );
}

function countBy(rows, key, fallback = "pending") {
  const map = new Map();
  for (const row of rows) {
    const value = row[key] || fallback;
    map.set(value, (map.get(value) || 0) + 1);
  }
  return [...map.entries()].map(([id, count]) => [id, labelOf(id), count]);
}

function FilterBar({ legend, value, onChange, options }) {
  if (!options.length) return null;
  return (
    <fieldset className="filter-bar">
      <legend>{legend}</legend>
      <div className="filter-chips" role="group" aria-label={legend}>
        <button
          type="button"
          className={`filter-chip${value === "all" ? " is-active" : ""}`}
          aria-pressed={value === "all"}
          onClick={() => onChange("all")}
        >
          All
        </button>
        {options.map(([id, label, count]) => (
          <button
            key={id}
            type="button"
            className={`filter-chip${value === id ? " is-active" : ""}`}
            aria-pressed={value === id}
            onClick={() => onChange(id)}
          >
            {label}
            <span className="filter-count">{count}</span>
          </button>
        ))}
      </div>
    </fieldset>
  );
}

function matchesFilter(value, filter, fallback = "pending") {
  return filter === "all" || (value || fallback) === filter;
}

function Banner({ state, emptyText, emptyAction }) {
  if (state.status === "loading") {
    return (
      <div className="banner loading" role="status">
        Loading this screen.
      </div>
    );
  }
  if (state.status === "error") {
    return (
      <div className="banner error" role="alert">
        {state.message}
      </div>
    );
  }
  if (state.status === "empty") {
    return (
      <div className="banner empty">
        <p>{emptyText}</p>
        {emptyAction}
      </div>
    );
  }
  return null;
}

function Progress({ steps, current, label, detail }) {
  const index = Math.max(0, steps.indexOf(current));
  const known = index >= 0;
  const percent = known ? Math.round(((index + 1) / steps.length) * 100) : 8;
  return (
    <div className="progress" role="status" aria-live="polite">
      <div className="progress-track" aria-hidden="true">
        <div className="progress-fill is-busy" style={{ width: `${percent}%` }} />
      </div>
      <p className="progress-label">
        <span className="spinner" aria-hidden="true" />
        {label}: {labelOf(current)} ({percent}%)
      </p>
      {detail && <p className="progress-detail">{detail}</p>}
    </div>
  );
}

function useAsync(loader, deps) {
  const [state, setState] = useState({ status: "loading", data: null, message: "" });
  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading", data: null, message: "" });
    loader()
      .then((data) => {
        if (cancelled) return;
        const empty = Array.isArray(data) ? data.length === 0 : data == null;
        setState({ status: empty ? "empty" : "ready", data, message: "" });
      })
      .catch((error) => {
        if (!cancelled) {
          setState({ status: "error", data: null, message: error.message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, deps);
  return [state, setState];
}

function usePollWhile(loader, setState, rows) {
  const pending = Array.isArray(rows)
    ? rows.some((row) => IN_FLIGHT.includes(row.processing_status))
    : false;
  useEffect(() => {
    if (!pending) return undefined;
    const timer = setInterval(() => {
      loader()
        .then((data) => {
          setState({
            status: data.length ? "ready" : "empty",
            data,
            message: "",
          });
        })
        .catch(() => {});
    }, 2000);
    return () => clearInterval(timer);
  }, [pending, loader, setState]);
}

export default function App() {
  const [screen, setScreen] = useState(() => {
    const saved = window.localStorage.getItem("regimpact_screen");
    if (SCREENS.some(([id]) => id === saved)) return saved;
    return window.localStorage.getItem("regimpact_company_id") ? "dashboard" : "profile";
  });
  const [navOpen, setNavOpen] = useState(() =>
    window.matchMedia("(min-width: 50.0625rem)").matches,
  );
  const [company, setCompany] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(
    window.localStorage.getItem("regimpact_analysis_id") || "",
  );

  useEffect(() => {
    window.localStorage.setItem("regimpact_screen", screen);
  }, [screen]);

  useEffect(() => {
    const id = window.localStorage.getItem("regimpact_company_id");
    if (!id) return;
    api
      .getCompany(id)
      .then((data) => setCompany(data))
      .catch(() => setCompany(null));
  }, []);

  function rememberAnalysis(id) {
    setSelectedAnalysis(id);
    window.localStorage.setItem("regimpact_analysis_id", id);
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar" data-collapsed={navOpen ? "false" : "true"}>
        <div className="sidebar-head">
          <div>
            <p className="brand">RegImpact</p>
            <p className="company-chip">{company ? company.company_name : "No company yet"}</p>
          </div>
          <button
            className="btn btn-secondary nav-toggle"
            type="button"
            aria-expanded={navOpen}
            aria-controls="app-nav"
            onClick={() => setNavOpen((open) => !open)}
          >
            {navOpen ? "Hide menu" : "Show menu"}
          </button>
        </div>
        <nav id="app-nav" aria-label="Screens">
          {SCREENS.map(([id, label]) => (
            <button
              key={id}
              className="nav-item"
              type="button"
              aria-current={screen === id ? "page" : undefined}
              onClick={() => {
                setScreen(id);
                if (window.matchMedia("(max-width: 50rem)").matches) setNavOpen(false);
              }}
            >
              {label}
            </button>
          ))}
        </nav>
      </aside>
      <main id="main">
        {screen === "dashboard" && (
          <Dashboard
            company={company}
            onOpenApplicable={() => setScreen("applicable")}
            onOpenUpdates={() => setScreen("updates")}
            onOpenResults={(id) => {
              rememberAnalysis(id);
              setScreen("results");
            }}
            onOpenProfile={() => setScreen("profile")}
            onOpenEvidence={() => setScreen("evidence")}
          />
        )}
        {screen === "profile" && (
          <CompanyProfile
            company={company}
            onSaved={(data) => {
              setCompany(data);
              setScreen("dashboard");
            }}
          />
        )}
        {screen === "applicable" && (
          <ApplicableRegulations
            onRunImpact={(id) => {
              rememberAnalysis(id);
              setScreen("results");
            }}
            goEvidence={() => setScreen("evidence")}
            goUpload={() => setScreen("regulations")}
          />
        )}
        {screen === "updates" && (
          <RegulatoryUpdates goAnalysis={() => setScreen("results")} />
        )}
        {screen === "regulations" && (
          <RegulationLibrary goEvidence={() => setScreen("evidence")} />
        )}
        {screen === "evidence" && <EvidenceLibrary goSetup={() => setScreen("applicable")} />}
        {screen === "setup" && (
          <AnalysisSetup
            onStarted={rememberAnalysis}
            goResults={() => setScreen("results")}
            goProfile={() => setScreen("profile")}
            goRegulations={() => setScreen("regulations")}
          />
        )}
        {screen === "results" && (
          <AnalysisResults
            analysisId={selectedAnalysis}
            goActions={() => setScreen("actions")}
            goSetup={() => setScreen("applicable")}
          />
        )}
        {screen === "actions" && (
          <ActionTracker analysisId={selectedAnalysis} goSetup={() => setScreen("applicable")} />
        )}
      </main>
    </div>
  );
}

async function waitForPortfolioAnalysis() {
  for (let attempt = 0; attempt < 45; attempt += 1) {
    const dash = await api.getDashboard();
    if (dash.analysis_id && dash.requirements_assessed > 0) return dash.analysis_id;
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  const dash = await api.getDashboard();
  return dash.analysis_id;
}

function StatRow({ label, value, hint }) {
  return (
    <div className="stat-row">
      <dt>{label}</dt>
      <dd>
        <strong>{value}</strong>
        {hint ? <span className="muted"> {hint}</span> : null}
      </dd>
    </div>
  );
}

function Dashboard({ company, onOpenApplicable, onOpenUpdates, onOpenResults, onOpenProfile, onOpenEvidence }) {
  const [state, setState] = useAsync(() => (company ? api.getDashboard() : Promise.resolve(null)), [
    company?.id,
  ]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const data = state.data;

  async function runImpact() {
    setBusy(true);
    setError("");
    try {
      await api.startPortfolio();
      const analysisId = await waitForPortfolioAnalysis();
      if (analysisId) onOpenResults(analysisId);
      else setError("Impact is still running. Open Compliance analysis in a minute.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!company) {
    return (
      <section className="page">
        <h1 className="page-title">Dashboard</h1>
        <div className="banner empty">
          <p>Save a company profile first. The indexed RBI corpus is matched to that profile.</p>
          <button className="btn btn-primary" type="button" onClick={onOpenProfile}>
            Open company profile
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="page">
      <h1 className="page-title">Dashboard</h1>
      <p className="lede">
        Indexed RBI documents are already in the corpus. Upload company evidence, then run impact
        on what actually applies. This is a working assessment, not legal advice. Local extractive
        analysis is in use.
      </p>
      {error && (
        <div className="banner error" role="alert">
          <p>{error}</p>
          <button className="btn btn-secondary" type="button" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}
      {state.status === "loading" && (
        <div className="banner loading" role="status">
          Loading the corpus snapshot.
        </div>
      )}
      {data && (
        <article className="card">
          <p className="kicker">Snapshot</p>
          <dl className="stat-list">
            <StatRow label="Applicable regulations" value={data.applicable} />
            <StatRow label="Requirements assessed" value={data.requirements_assessed} />
            <StatRow label="Fully evidenced" value={data.fully_evidenced} />
            <StatRow label="Partly evidenced" value={data.partially_evidenced} />
            <StatRow label="Gaps" value={data.gaps} />
            <StatRow label="High-risk gaps" value={data.high_risk_gaps} />
            <StatRow label="Human review required" value={data.human_review_required} />
            <StatRow label="Active RBI documents" value={data.corpus_documents} />
          </dl>
          {data.assessment_confidence && (
            <p className="muted">
              {data.assessment_confidence.label}: {data.assessment_confidence.definition}
            </p>
          )}
          {data.latest_change_summary && (
            <div className="meta-row">
              <p>Latest RBI update: {data.latest_change_summary}</p>
              <button className="btn btn-secondary" type="button" onClick={onOpenUpdates}>
                Open updates
              </button>
            </div>
          )}
          <div className="actions">
            <button className="btn btn-primary" type="button" onClick={runImpact} disabled={busy}>
              {busy ? "Queuing impact…" : "Run impact on applicable regulations"}
            </button>
            <button className="btn btn-secondary" type="button" onClick={onOpenApplicable}>
              Review applicability
            </button>
            <button className="btn btn-secondary" type="button" onClick={onOpenEvidence}>
              Upload company evidence
            </button>
          </div>
        </article>
      )}
    </section>
  );
}

function ApplicableRegulations({ onRunImpact, goEvidence, goUpload }) {
  const [state, setState] = useAsync(() => api.getApplicable(), []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [decision, setDecision] = useState("all");
  const [domain, setDomain] = useState("all");
  const [review, setReview] = useState("all");
  const rows = state.data || [];
  const visible = rows.filter(
    (row) =>
      matchesFilter(row.applicability, decision) &&
      matchesFilter(row.regulatory_domain, domain, "other") &&
      (review === "all" ||
        (review === "needs_review" && row.human_review_required) ||
        (review === "decided" && !row.human_review_required)),
  );

  async function runImpact() {
    setBusy(true);
    setError("");
    try {
      await api.startPortfolio();
      const analysisId = await waitForPortfolioAnalysis();
      if (analysisId) onRunImpact(analysisId);
      else setError("Impact is still running. Open Compliance analysis in a minute.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="page">
      <h1 className="page-title">Applicable regulations</h1>
      <p className="lede">
        Applicability is decided from the company profile and RBI metadata first. Uncertain rows
        need a person — they are not treated as in scope.
      </p>
      {error && (
        <div className="banner error" role="alert">
          <p>{error}</p>
          <button className="btn btn-secondary" type="button" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}
      <Banner
        state={state}
        emptyText="No indexed RBI documents yet. The worker seeds the corpus in the background."
      />
      <div className="actions">
        <button className="btn btn-primary" type="button" onClick={runImpact} disabled={busy}>
          {busy ? "Queuing…" : "Run impact on applicable set"}
        </button>
        <button className="btn btn-secondary" type="button" onClick={goEvidence}>
          Upload company evidence
        </button>
        <button className="btn btn-secondary" type="button" onClick={goUpload}>
          Upload another circular
        </button>
      </div>
      {rows.length > 0 && (
        <div className="filter-stack">
          <FilterBar
            legend="Decision"
            value={decision}
            onChange={setDecision}
            options={countBy(rows, "applicability")}
          />
          <FilterBar
            legend="Domain"
            value={domain}
            onChange={setDomain}
            options={countBy(rows, "regulatory_domain", "other")}
          />
          <FilterBar
            legend="Review"
            value={review}
            onChange={setReview}
            options={[
              [
                "needs_review",
                "Needs a person",
                rows.filter((row) => row.human_review_required).length,
              ],
              [
                "decided",
                "Decided",
                rows.filter((row) => !row.human_review_required).length,
              ],
            ].filter(([, , count]) => count > 0)}
          />
          <p className="muted">
            Showing {visible.length} of {rows.length}
          </p>
        </div>
      )}
      {rows.length > 0 && visible.length === 0 && (
        <div className="banner empty">
          <p>No documents match these filters.</p>
          <button
            className="btn btn-secondary"
            type="button"
            onClick={() => {
              setDecision("all");
              setDomain("all");
              setReview("all");
            }}
          >
            Show all
          </button>
        </div>
      )}
      {visible.map((row) => (
        <article className="card result-card" key={row.id}>
          <div className="clause-rail">{labelOf(row.applicability)}</div>
          <div>
            <h2>{row.title}</h2>
            <dl className="dl">
              <dt>Decision</dt>
              <dd>
                <Status value={row.applicability} />
              </dd>
              <dt>Reason</dt>
              <dd>{row.reason}</dd>
              <dt>Company characteristics</dt>
              <dd>
                {(row.matched_characteristics || []).map(labelOf).join(", ") || "None"}
              </dd>
              <dt>Domain</dt>
              <dd>{labelOf(row.regulatory_domain)}</dd>
            </dl>
            {row.source_url && (
              <div className="actions">
                <OfficialSourceButton href={row.source_url} title={row.title} />
              </div>
            )}
            {row.human_review_required && (
              <p className="muted">A person must review this applicability decision.</p>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}

function RegulatoryUpdates({ goAnalysis }) {
  const [state] = useAsync(() => api.getChanges(), []);
  const [kind, setKind] = useState("all");
  const changes = state.data || [];
  const clauseOptions = countBy(
    changes.flatMap((change) => change.requirement_changes || []),
    "kind",
  );
  const visible = changes
    .map((change) => ({
      ...change,
      requirement_changes: (change.requirement_changes || []).filter((item) =>
        matchesFilter(item.kind, kind),
      ),
    }))
    .filter((change) => kind === "all" || change.requirement_changes.length > 0);
  return (
    <section className="page">
      <h1 className="page-title">Regulatory updates</h1>
      <p className="lede">
        A requirement is marked changed only when the clause text itself changed between versions.
      </p>
      <Banner state={state} emptyText="No version changes in the indexed corpus yet." />
      {changes.length > 0 && (
        <div className="filter-stack">
          <FilterBar legend="Change" value={kind} onChange={setKind} options={clauseOptions} />
        </div>
      )}
      {visible.map((change) => (
        <article className="card" key={change.id}>
          <p className="kicker">RBI regulatory update</p>
          <h2>{change.title}</h2>
          <p>{change.summary}</p>
          {change.source_url && (
            <div className="actions">
              <OfficialSourceButton href={change.source_url} title={change.title} />
            </div>
          )}
          {(change.requirement_changes || []).map((item) => (
            <div className="card nested" key={item.id}>
              <p>
                <Status value={item.kind} /> {item.clause_number ? `Clause ${item.clause_number}` : ""}
              </p>
              {item.previous_text && <p className="muted">Was: {item.previous_text}</p>}
              {item.new_text && <p>Now: {item.new_text}</p>}
            </div>
          ))}
          <div className="actions">
            <button className="btn btn-secondary" type="button" onClick={goAnalysis}>
              Open compliance analysis
            </button>
          </div>
        </article>
      ))}
    </section>
  );
}

function CompanyProfile({ company, onSaved }) {
  const [form, setForm] = useState(() => ({
    company_name: company?.company_name || "PayFlow Technologies",
    organization_type: company?.organization_type || "payment_aggregator",
    business_model: company?.business_model || "Online merchant payment processing",
    operating_regions: (company?.operating_regions || ["India"]).join(", "),
    products: (company?.products || ["Payments", "Refunds", "Settlements"]).join(", "),
    customer_segments: (company?.customer_segments || ["Merchants", "Consumers"]).join(", "),
    regulatory_entities: (company?.regulatory_entities || ["RBI"]).join(", "),
    uses_customer_data: company?.uses_customer_data ?? true,
    uses_automated_decisioning: company?.uses_automated_decisioning ?? false,
    has_outsourced_operations: company?.has_outsourced_operations ?? true,
    existing_policies: (company?.existing_policies || ["KYC Policy", "Grievance Policy"]).join(
      ", ",
    ),
    internal_controls: (company?.internal_controls || ["Access reviews", "Audit logging"]).join(
      ", ",
    ),
  }));
  const [state, setState] = useState({ status: "ready", message: "" });

  useEffect(() => {
    if (!company) return;
    setForm({
      company_name: company.company_name || "",
      organization_type: company.organization_type || "payment_aggregator",
      business_model: company.business_model || "",
      operating_regions: (company.operating_regions || []).join(", "),
      products: (company.products || []).join(", "),
      customer_segments: (company.customer_segments || []).join(", "),
      regulatory_entities: (company.regulatory_entities || []).join(", "),
      uses_customer_data: company.uses_customer_data ?? true,
      uses_automated_decisioning: company.uses_automated_decisioning ?? false,
      has_outsourced_operations: company.has_outsourced_operations ?? true,
      existing_policies: (company.existing_policies || []).join(", "),
      internal_controls: (company.internal_controls || []).join(", "),
    });
  }, [company]);

  function split(value) {
    return value
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean);
  }

  function set(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function save(event) {
    event.preventDefault();
    setState({ status: "loading", message: "" });
    const body = {
      ...form,
      operating_regions: split(form.operating_regions),
      products: split(form.products),
      customer_segments: split(form.customer_segments),
      regulatory_entities: split(form.regulatory_entities),
      existing_policies: split(form.existing_policies),
      internal_controls: split(form.internal_controls),
    };
    try {
      const saved = company
        ? await api.updateCompany(company.id, body)
        : await api.createCompany(body);
      setCompanyId(saved.id);
      onSaved(saved);
      setState({ status: "ready", message: "Company saved." });
    } catch (error) {
      setState({ status: "error", message: error.message });
    }
  }

  return (
    <section className="page">
      <h1 className="page-title">Company profile</h1>
      <p className="lede">
        Save the entity type and operating facts here. Indexed RBI documents are matched to this
        profile. Company policy names listed below are not evidence — upload the PDFs on Company
        evidence.
      </p>
      {state.status === "error" && (
        <div className="banner error" role="alert">
          <p>{state.message}</p>
          <button
            className="btn btn-secondary"
            type="button"
            onClick={() => setState({ status: "ready", message: "" })}
          >
            Dismiss
          </button>
        </div>
      )}
      {state.message && state.status === "ready" && (
        <div className="banner ok" role="status">
          {state.message}
        </div>
      )}
      <form className="card stack" onSubmit={save}>
        <div className="field-grid two">
          <div>
            <label htmlFor="company_name">Company name</label>
            <input
              id="company_name"
              value={form.company_name}
              onChange={(event) => set("company_name", event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="organization_type">Organization type</label>
            <select
              id="organization_type"
              value={form.organization_type}
              onChange={(event) => set("organization_type", event.target.value)}
            >
              {ORG_TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label htmlFor="business_model">Business model</label>
          <input
            id="business_model"
            value={form.business_model}
            onChange={(event) => set("business_model", event.target.value)}
          />
        </div>
        <div className="field-grid two">
          <div>
            <label htmlFor="operating_regions">Operating regions</label>
            <input
              id="operating_regions"
              value={form.operating_regions}
              onChange={(event) => set("operating_regions", event.target.value)}
            />
            <p className="hint">Comma-separated. Example: India, UAE</p>
          </div>
          <div>
            <label htmlFor="regulatory_entities">Regulators you report to</label>
            <input
              id="regulatory_entities"
              value={form.regulatory_entities}
              onChange={(event) => set("regulatory_entities", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="products">Products</label>
            <input
              id="products"
              value={form.products}
              onChange={(event) => set("products", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="customer_segments">Customer segments</label>
            <input
              id="customer_segments"
              value={form.customer_segments}
              onChange={(event) => set("customer_segments", event.target.value)}
            />
          </div>
        </div>
        <fieldset>
          <legend>How the business operates</legend>
          <div className="check-row">
            <input
              id="uses_customer_data"
              type="checkbox"
              checked={form.uses_customer_data}
              onChange={(event) => set("uses_customer_data", event.target.checked)}
            />
            <label htmlFor="uses_customer_data">Handles customer data</label>
          </div>
          <div className="check-row">
            <input
              id="uses_automated_decisioning"
              type="checkbox"
              checked={form.uses_automated_decisioning}
              onChange={(event) => set("uses_automated_decisioning", event.target.checked)}
            />
            <label htmlFor="uses_automated_decisioning">Uses automated decisioning</label>
          </div>
          <div className="check-row">
            <input
              id="has_outsourced_operations"
              type="checkbox"
              checked={form.has_outsourced_operations}
              onChange={(event) => set("has_outsourced_operations", event.target.checked)}
            />
            <label htmlFor="has_outsourced_operations">Has outsourced operations</label>
          </div>
        </fieldset>
        <div>
          <label htmlFor="existing_policies">Named policies</label>
          <input
            id="existing_policies"
            value={form.existing_policies}
            onChange={(event) => set("existing_policies", event.target.value)}
          />
          <p className="hint">Names only. Upload the PDFs in Evidence library before analysis.</p>
        </div>
        <div>
          <label htmlFor="internal_controls">Internal controls</label>
          <input
            id="internal_controls"
            value={form.internal_controls}
            onChange={(event) => set("internal_controls", event.target.value)}
          />
        </div>
        <div className="actions">
          <button
            className={`btn btn-primary${state.status === "loading" ? " btn-busy" : ""}`}
            type="submit"
            disabled={state.status === "loading"}
          >
            {company ? "Save company" : "Create company"}
          </button>
        </div>
      </form>
    </section>
  );
}

function RegulationLibrary({ goEvidence }) {
  const [state, setState] = useAsync(() => api.listRegulations(), []);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  usePollWhile(api.listRegulations, setState, state.data);

  async function upload(event) {
    event.preventDefault();
    const form = new FormData(event.target);
    setError("");
    setBusy(true);
    try {
      await api.uploadRegulation(form);
      const rows = await api.listRegulations();
      setState({
        status: rows.length ? "ready" : "empty",
        data: rows,
        message: "",
      });
      event.target.reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="page">
      <h1 className="page-title">Regulation library</h1>
      <p className="lede">Upload the circular or master direction the analysis will read.</p>
      <form className="card stack" onSubmit={upload}>
        <div>
          <label htmlFor="reg-file">PDF</label>
          <input id="reg-file" name="file" type="file" accept="application/pdf" required />
        </div>
        <div className="field-grid two">
          <div>
            <label htmlFor="reg-title">Title</label>
            <input id="reg-title" name="title" required />
          </div>
          <div>
            <label htmlFor="reg-regulator">Regulator</label>
            <input id="reg-regulator" name="regulator" defaultValue="RBI" required />
          </div>
          <div>
            <label htmlFor="reg-type">Document type</label>
            <select id="reg-type" name="document_type" defaultValue="circular">
              {DOCUMENT_TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="reg-date">Publication date</label>
            <input id="reg-date" name="publication_date" type="date" />
          </div>
        </div>
        <div>
          <label htmlFor="reg-url">Source URL</label>
          <input id="reg-url" name="source_url" type="url" placeholder="https://" />
        </div>
        <div className="actions">
          <button className={`btn btn-primary${busy ? " btn-busy" : ""}`} type="submit" disabled={busy}>
            Upload rule document
          </button>
        </div>
        {error && (
          <div className="banner error" role="alert">
            <p>{error}</p>
            <button className="btn btn-secondary" type="button" onClick={() => setError("")}>
              Dismiss
            </button>
          </div>
        )}
      </form>
      <Banner
        state={state}
        emptyText="No rule documents yet. Upload a PDF to start."
      />
      {state.status === "ready" && (
        <div className="table-wrap">
          <table>
            <caption>Uploaded rule documents</caption>
            <thead>
              <tr>
                <th scope="col">Title</th>
                <th scope="col">Type</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {state.data.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.title}</td>
                  <td>{labelOf(doc.document_type)}</td>
                  <td>
                    <Status value={doc.processing_status} />
                    {IN_FLIGHT.includes(doc.processing_status) && (
                      <Progress
                        steps={PROCESS_STEPS}
                        current={doc.processing_status}
                        label="Working"
                        detail={PROCESS_COPY[doc.processing_status]}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {state.status === "ready" && (
        <div className="actions">
          <button className="btn btn-secondary" type="button" onClick={goEvidence}>
            Continue to evidence
          </button>
        </div>
      )}
    </section>
  );
}

function EvidenceLibrary({ goSetup }) {
  const [state, setState] = useAsync(() => api.listPolicies(), []);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  usePollWhile(api.listPolicies, setState, state.data);

  async function upload(event) {
    event.preventDefault();
    const form = new FormData(event.target);
    setError("");
    setBusy(true);
    try {
      await api.uploadPolicy(form);
      const rows = await api.listPolicies();
      setState({ status: rows.length ? "ready" : "empty", data: rows, message: "" });
      event.target.reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="page">
      <h1 className="page-title">Evidence library</h1>
      <p className="lede">
        Gap checking cites only these PDFs. Names typed on the company profile are not proof.
      </p>
      <form className="card stack" onSubmit={upload}>
        <div>
          <label htmlFor="pol-file">PDF</label>
          <input id="pol-file" name="file" type="file" accept="application/pdf" required />
        </div>
        <div className="field-grid two">
          <div>
            <label htmlFor="pol-title">Title</label>
            <input id="pol-title" name="title" required />
          </div>
          <div>
            <label htmlFor="pol-type">Evidence type</label>
            <select id="pol-type" name="evidence_type" defaultValue="policy">
              {EVIDENCE_TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="pol-dept">Owner department</label>
            <select id="pol-dept" name="owner_department" defaultValue="Compliance">
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="actions">
          <button className={`btn btn-primary${busy ? " btn-busy" : ""}`} type="submit" disabled={busy}>
            Upload company document
          </button>
        </div>
        {error && (
          <div className="banner error" role="alert">
            <p>{error}</p>
            <button className="btn btn-secondary" type="button" onClick={() => setError("")}>
              Dismiss
            </button>
          </div>
        )}
      </form>
      <Banner state={state} emptyText="No company documents yet. Upload a policy PDF." />
      {state.status === "ready" && (
        <div className="table-wrap">
          <table>
            <caption>Uploaded company documents</caption>
            <thead>
              <tr>
                <th scope="col">Title</th>
                <th scope="col">Type</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {state.data.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.title}</td>
                  <td>{labelOf(doc.evidence_type)}</td>
                  <td>
                    <Status value={doc.processing_status} />
                    {IN_FLIGHT.includes(doc.processing_status) && (
                      <Progress
                        steps={PROCESS_STEPS}
                        current={doc.processing_status}
                        label="Working"
                        detail={PROCESS_COPY[doc.processing_status]}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {state.status === "ready" && (
        <div className="actions">
          <button className="btn btn-secondary" type="button" onClick={goSetup}>
            Continue to analysis
          </button>
        </div>
      )}
    </section>
  );
}

function AnalysisSetup({ onStarted, goResults, goProfile, goRegulations }) {
  const [regs, setRegs] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("loading");
  const companyId = window.localStorage.getItem("regimpact_company_id");

  useEffect(() => {
    api
      .listRegulations()
      .then((rows) => {
        setRegs(rows);
        setStatus(rows.length ? "ready" : "empty");
      })
      .catch((err) => {
        setError(err.message);
        setStatus("error");
      });
  }, []);

  async function start(event) {
    event.preventDefault();
    const form = new FormData(event.target);
    setError("");
    setBusy(true);
    try {
      const result = await api.startAnalysis({
        company_id: companyId,
        regulation_id: form.get("regulation_id"),
        analysis_depth: form.get("analysis_depth"),
        include_gap_analysis: true,
        include_action_plan: true,
      });
      onStarted(result.id);
      goResults();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="page">
      <h1 className="page-title">Analysis setup</h1>
      <p className="lede">Pick the circular and how thoroughly to read it.</p>
      {!companyId && (
        <div className="banner error" role="alert">
          <p>Save a company profile first.</p>
          <button className="btn btn-primary" type="button" onClick={goProfile}>
            Open company profile
          </button>
        </div>
      )}
      {status === "loading" && (
        <div className="banner loading" role="status">
          Loading rule documents.
        </div>
      )}
      {status === "empty" && (
        <div className="banner empty">
          <p>Upload a rule document first.</p>
          <button className="btn btn-primary" type="button" onClick={goRegulations}>
            Open regulation library
          </button>
        </div>
      )}
      {status === "error" && (
        <div className="banner error" role="alert">
          {error}
        </div>
      )}
      <form className="card stack" onSubmit={start}>
        <div>
          <label htmlFor="regulation_id">Rule document</label>
          <select id="regulation_id" name="regulation_id" required disabled={!regs.length}>
            {regs.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.title}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="analysis_depth">Depth</label>
          <select id="analysis_depth" name="analysis_depth" defaultValue="standard">
            <option value="quick">Quick</option>
            <option value="standard">Standard</option>
            <option value="deep">Deep</option>
          </select>
        </div>
        <div className="actions">
          <button
            className={`btn btn-primary${busy ? " btn-busy" : ""}`}
            type="submit"
            disabled={!companyId || !regs.length || busy}
          >
            Start analysis
          </button>
        </div>
        {error && status !== "error" && (
          <div className="banner error" role="alert">
            {error}
          </div>
        )}
      </form>
    </section>
  );
}

function DateLine({ entry }) {
  const suggested = entry.date_basis === "inferred_recommendation";
  return (
    <span className={`date-chip ${suggested ? "suggested" : "cited"}`}>
      {labelOf(entry.date_basis)}: {entry.date}
    </span>
  );
}

function AnalysisResults({ analysisId, goActions, goSetup }) {
  const [analysis, setAnalysis] = useState(null);
  const [gaps, setGaps] = useState([]);
  const [actions, setActions] = useState([]);
  const [citation, setCitation] = useState(null);
  const [openCitationId, setOpenCitationId] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState(analysisId ? "loading" : "empty");
  const [confirmReject, setConfirmReject] = useState(false);
  const [coverage, setCoverage] = useState("all");
  const [risk, setRisk] = useState("all");
  const confirmId = useId();

  useEffect(() => {
    if (!confirmReject) return undefined;
    function onKey(event) {
      if (event.key === "Escape") setConfirmReject(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [confirmReject]);

  useEffect(() => {
    if (!analysisId) {
      setStatus("empty");
      return;
    }
    let cancelled = false;
    async function load() {
      try {
        const [current, gapRows, actionRows] = await Promise.all([
          api.getAnalysis(analysisId),
          api.getGaps(analysisId),
          api.getActions(analysisId),
        ]);
        if (cancelled) return;
        setAnalysis(current);
        setGaps(gapRows);
        setActions(actionRows);
        setStatus(current.status === "failed" ? "error" : "ready");
        if (current.status === "failed") {
          setError(
            `Analysis incomplete (${labelOf(current.status)}${
              current.result?.failed_step ? ` — broke at ${labelOf(current.result.failed_step)}` : ""
            })`,
          );
        }
      } catch (err) {
        if (!cancelled) {
          setStatus("error");
          setError(err.message);
        }
      }
    }
    load();
    const timer = setInterval(load, 4000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [analysisId]);

  async function decide(kind) {
    try {
      const updated =
        kind === "approve" ? await api.approve(analysisId) : await api.reject(analysisId);
      setAnalysis(updated);
      setConfirmReject(false);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  function closeCitation() {
    setOpenCitationId(null);
    setCitation(null);
  }

  async function openCitation(id) {
    if (openCitationId === id) {
      closeCitation();
      return;
    }
    setOpenCitationId(id);
    setCitation(null);
    try {
      setCitation(await api.getCitation(id));
    } catch (err) {
      setError(err.message);
      closeCitation();
    }
  }

  if (status === "empty") {
    return (
      <section className="page">
        <h1 className="page-title">Compliance analysis</h1>
        <div className="banner empty">
          <p>Run impact from the dashboard after the RBI corpus is indexed.</p>
          <button className="btn btn-primary" type="button" onClick={goSetup}>
            Open applicable regulations
          </button>
        </div>
      </section>
    );
  }
  if (status === "loading") {
    return (
      <section className="page">
        <h1 className="page-title">Compliance analysis</h1>
        <div className="banner loading" role="status">
          Waiting for the analysis.
        </div>
      </section>
    );
  }
  if (status === "error" && !analysis) {
    return (
      <section className="page">
        <h1 className="page-title">Compliance analysis</h1>
        <div className="banner error" role="alert">
          {error}
        </div>
      </section>
    );
  }

  const result = analysis.result || {};
  const requirements = result.requirements || [];
  const currentStep = result.current_step || analysis.status;
  const working = analysis.status !== "completed" && analysis.status !== "failed";
  const visibleRequirements = requirements.filter(
    (item) =>
      matchesFilter(item.gap_status, coverage) &&
      matchesFilter(item.severity || analysis.overall_risk, risk, "none"),
  );
  const visibleGaps = gaps.filter(
    (gap) =>
      matchesFilter(gap.gap_status, coverage) &&
      matchesFilter(gap.severity, risk, "none"),
  );

  return (
    <section className="page">
      <h1 className="page-title">Compliance analysis</h1>
      <p className="lede">
        This is a working analysis, not legal advice. Cited dates come from the circular.
        Suggested dates are never shown as regulator deadlines.
      </p>
      {error && (
        <div className="banner error" role="alert">
          <p>{error}</p>
          <button className="btn btn-secondary" type="button" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}
      {result.failed_step && (
        <div className="banner error" role="alert">
          Analysis incomplete — broke at {labelOf(result.failed_step)}.
        </div>
      )}
      <div className="card">
        <p className="kicker">Report</p>
        <div className="meta-row">
          <Status value={analysis.status} />
          <Status value={analysis.review_status || "pending"} />
          <Status value={analysis.applicability || "uncertain"} />
          <Status value={analysis.overall_risk || "none"} />
          <Status value={result.verification_status || "unverified"} />
        </div>
        {analysis.human_review_required && (
          <p className="muted">A person must review this report before it counts as approved.</p>
        )}
        <p>
          {actions.length} {actions.length === 1 ? "task" : "tasks"} on the action tracker.
        </p>
        {working && (
          <Progress steps={ANALYSIS_STEPS} current={currentStep} label="Current step" />
        )}
        <div className="actions">
          <button className="btn btn-primary" type="button" onClick={() => decide("approve")}>
            Approve report
          </button>
          <button className="btn btn-danger" type="button" onClick={() => setConfirmReject(true)}>
            Reject report
          </button>
          <button className="btn btn-secondary" type="button" onClick={goActions}>
            Open action tracker
          </button>
        </div>
        {confirmReject && (
          <div className="confirm" role="alertdialog" aria-labelledby={confirmId}>
            <p id={confirmId}>Reject this report? That decision is recorded on the analysis.</p>
            <div className="actions">
              <button className="btn btn-secondary" type="button" onClick={() => setConfirmReject(false)}>
                Cancel
              </button>
              <button className="btn btn-danger" type="button" onClick={() => decide("reject")}>
                Reject report
              </button>
            </div>
          </div>
        )}
      </div>
      {requirements.length === 0 && analysis.status === "completed" && (
        <div className="banner empty">No requirements were extracted.</div>
      )}
      {requirements.length === 0 && working && (
        <div className="banner empty">Requirements appear here when the current step finishes.</div>
      )}
      {requirements.length > 0 && (
        <div className="filter-stack">
          <FilterBar
            legend="Coverage"
            value={coverage}
            onChange={setCoverage}
            options={countBy(requirements, "gap_status")}
          />
          <FilterBar
            legend="Risk"
            value={risk}
            onChange={setRisk}
            options={countBy(
              requirements.map((item) => ({
                severity: item.severity || analysis.overall_risk || "none",
              })),
              "severity",
              "none",
            )}
          />
          <p className="muted">
            Showing {visibleRequirements.length} of {requirements.length}
          </p>
        </div>
      )}
      {requirements.length > 0 && visibleRequirements.length === 0 && (
        <div className="banner empty">
          <p>No requirements match these filters.</p>
          <button
            className="btn btn-secondary"
            type="button"
            onClick={() => {
              setCoverage("all");
              setRisk("all");
            }}
          >
            Show all
          </button>
        </div>
      )}
      {visibleRequirements.map((item, index) => {
        const citationId = item.citation_id;
        return (
          <article className="card result-card" key={item.id || item.requirement || index}>
            <div className="clause-rail">{item.clause_number || String(index + 1).padStart(2, "0")}</div>
            <div>
              <h2>{item.requirement || item.requirement_text}</h2>
              <dl className="dl">
                <dt>Applicability</dt>
                <dd>
                  <Status value={item.applicability} />
                </dd>
                <dt>Impact</dt>
                <dd>
                  <Status value={item.impact_level} />
                </dd>
                <dt>Teams</dt>
                <dd>{(item.affected_departments || []).join(", ") || "Not yet assigned"}</dd>
                <dt>Current status</dt>
                <dd>
                  <Status value={item.gap_status || "pending"} />
                </dd>
                <dt>Risk</dt>
                <dd>
                  <Status value={item.severity || analysis.overall_risk} />
                </dd>
                <dt>Required action</dt>
                <dd>{item.action || "See action tracker"}</dd>
                <dt>Evidence</dt>
                <dd>{item.evidence || "None yet"}</dd>
                <dt>Reviewer status</dt>
                <dd>
                  <Status value={analysis.review_status || "pending"} />
                </dd>
              </dl>
              {(item.stated_dates || []).map((entry) => (
                <DateLine key={`${entry.date}-${entry.date_basis}`} entry={entry} />
              ))}
              {citationId && (
                <div className="actions">
                  <button
                    className="btn btn-secondary"
                    type="button"
                    aria-expanded={openCitationId === citationId}
                    onClick={() => openCitation(citationId)}
                  >
                    {openCitationId === citationId ? "Hide source" : "Open source"}
                  </button>
                </div>
              )}
            </div>
          </article>
        );
      })}
      {requirements.length === 0 &&
        visibleGaps.map((gap) => (
        <article className="card result-card" key={gap.id}>
          <div className="clause-rail">Gap</div>
          <div>
            <h2>{gap.requirement_text || "Gap"}</h2>
            <dl className="dl">
              <dt>Current status</dt>
              <dd>
                <Status value={gap.gap_status} />
              </dd>
              <dt>Risk</dt>
              <dd>
                <Status value={gap.severity} />
              </dd>
            </dl>
            <p>{gap.explanation}</p>
          </div>
        </article>
      ))}
      {openCitationId && (
        <SourceSheet
          title="Cited passage"
          loading={!citation}
          body={
            citation ? (
              <>
                <p>{citation.excerpt}</p>
                <footer>
                  Pages {citation.page_start}
                  {citation.page_end !== citation.page_start ? `–${citation.page_end}` : ""} ·
                  Clause {citation.clause_number || "n/a"}
                </footer>
              </>
            ) : null
          }
          onClose={closeCitation}
        />
      )}
    </section>
  );
}

function ActionTracker({ analysisId, goSetup }) {
  const [state, setState] = useAsync(
    () => (analysisId ? api.getActions(analysisId) : Promise.resolve([])),
    [analysisId],
  );
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const rows = state.data || [];
  const visible = rows.filter((item) => matchesFilter(item.status, statusFilter, "open"));

  async function changeStatus(id, status) {
    try {
      await api.updateAction(id, { status });
      setState({ status: "ready", data: await api.getActions(analysisId), message: "" });
    } catch (err) {
      setError(err.message);
    }
  }

  if (!analysisId) {
    return (
      <section className="page">
        <h1 className="page-title">Action tracker</h1>
        <div className="banner empty">
          <p>No analysis selected.</p>
          <button className="btn btn-primary" type="button" onClick={goSetup}>
            Open analysis setup
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="page">
      <h1 className="page-title">Action tracker</h1>
      <p className="lede">Tasks that come out of the report. Change status as work moves.</p>
      {error && (
        <div className="banner error" role="alert">
          <p>{error}</p>
          <button className="btn btn-secondary" type="button" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}
      <Banner state={state} emptyText="No tasks yet. Finish an analysis first." />
      {rows.length > 0 && (
        <div className="filter-stack">
          <FilterBar
            legend="Status"
            value={statusFilter}
            onChange={setStatusFilter}
            options={countBy(rows, "status", "open")}
          />
        </div>
      )}
      {state.status === "ready" && visible.length === 0 && rows.length > 0 && (
        <div className="banner empty">
          <p>No tasks match this status.</p>
          <button className="btn btn-secondary" type="button" onClick={() => setStatusFilter("all")}>
            Show all
          </button>
        </div>
      )}
      {state.status === "ready" && visible.length > 0 && (
        <div className="table-wrap">
          <table>
            <caption>Tasks for this analysis</caption>
            <thead>
              <tr>
                <th scope="col">Task</th>
                <th scope="col">Owner</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((item) => (
                <tr key={item.id}>
                  <td>{item.title}</td>
                  <td>{item.owner_department || "Unassigned"}</td>
                  <td>
                    <label className="sr-only" htmlFor={`action-status-${item.id}`}>
                      Status for {item.title}
                    </label>
                    <select
                      id={`action-status-${item.id}`}
                      value={item.status}
                      onChange={(event) => changeStatus(item.id, event.target.value)}
                    >
                      <option value="open">Open</option>
                      <option value="in_progress">In progress</option>
                      <option value="blocked">Blocked</option>
                      <option value="done">Done</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
