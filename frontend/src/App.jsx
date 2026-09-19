import { useEffect, useId, useState } from "react";
import { api, setCompanyId } from "./api.js";

const SCREENS = [
  ["profile", "Company profile"],
  ["regulations", "Regulation library"],
  ["evidence", "Evidence library"],
  ["setup", "Analysis setup"],
  ["results", "Analysis results"],
  ["actions", "Action tracker"],
];

const ORG_TYPES = [
  ["payment_aggregator", "Payment aggregator"],
  ["payment_gateway", "Payment gateway"],
  ["nbfc", "NBFC"],
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
  inferred_recommendation: "Suggested date — not a regulator deadline",
  quick: "Quick",
  standard: "Standard",
  deep: "Deep",
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
    return window.localStorage.getItem("regimpact_company_id") ? "regulations" : "profile";
  });
  const [navOpen, setNavOpen] = useState(true);
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
              onClick={() => setScreen(id)}
            >
              {label}
            </button>
          ))}
        </nav>
      </aside>
      <main id="main">
        {screen === "profile" && (
          <CompanyProfile company={company} onSaved={setCompany} />
        )}
        {screen === "regulations" && (
          <RegulationLibrary goEvidence={() => setScreen("evidence")} />
        )}
        {screen === "evidence" && <EvidenceLibrary goSetup={() => setScreen("setup")} />}
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
            goSetup={() => setScreen("setup")}
          />
        )}
        {screen === "actions" && (
          <ActionTracker analysisId={selectedAnalysis} goSetup={() => setScreen("setup")} />
        )}
      </main>
    </div>
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
        There is no sign-in. Save the demo company here; every other screen uses it.
      </p>
      {state.status === "error" && (
        <div className="banner error" role="alert">
          {state.message}
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
            {error}
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
            {error}
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
  const confirmId = useId();

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

  async function openCitation(id) {
    try {
      setOpenCitationId(id);
      setCitation(await api.getCitation(id));
    } catch (err) {
      setError(err.message);
    }
  }

  if (status === "empty") {
    return (
      <section className="page">
        <h1 className="page-title">Analysis results</h1>
        <div className="banner empty">
          <p>Start an analysis to see results here.</p>
          <button className="btn btn-primary" type="button" onClick={goSetup}>
            Open analysis setup
          </button>
        </div>
      </section>
    );
  }
  if (status === "loading") {
    return (
      <section className="page">
        <h1 className="page-title">Analysis results</h1>
        <div className="banner loading" role="status">
          Waiting for the analysis.
        </div>
      </section>
    );
  }
  if (status === "error" && !analysis) {
    return (
      <section className="page">
        <h1 className="page-title">Analysis results</h1>
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

  return (
    <section className="page">
      <h1 className="page-title">Analysis results</h1>
      <p className="lede">
        This is a working analysis, not legal advice. Cited dates come from the circular.
        Suggested dates are never shown as regulator deadlines.
      </p>
      {error && (
        <div className="banner error" role="alert">
          {error}
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
      {requirements.map((item, index) => {
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
                    onClick={() => openCitation(citationId)}
                  >
                    Open source…
                  </button>
                </div>
              )}
              {citation && openCitationId === citationId && (
                <blockquote className="excerpt">
                  <p>{citation.excerpt}</p>
                  <footer>
                    Pages {citation.page_start}
                    {citation.page_end !== citation.page_start ? `–${citation.page_end}` : ""} ·
                    Clause {citation.clause_number || "n/a"}
                  </footer>
                </blockquote>
              )}
            </div>
          </article>
        );
      })}
      {gaps.map((gap) => (
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
    </section>
  );
}

function ActionTracker({ analysisId, goSetup }) {
  const [state, setState] = useAsync(
    () => (analysisId ? api.getActions(analysisId) : Promise.resolve([])),
    [analysisId],
  );
  const [error, setError] = useState("");

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
          {error}
        </div>
      )}
      <Banner state={state} emptyText="No tasks yet. Finish an analysis first." />
      {state.status === "ready" && (
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
              {state.data.map((item) => (
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
