const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

function companyId() {
  return window.localStorage.getItem("regimpact_company_id") || "";
}

async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...options.headers,
  };
  const currentCompany = companyId();
  if (currentCompany) {
    headers["X-Company-Id"] = currentCompany;
  }
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new Error("Could not reach the API. Start the backend, then try again.");
  }
  const requestId = response.headers.get("X-Request-Id");
  if (response.status === 204) {
    return { ok: true, requestId };
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      data?.error?.message ||
      (response.status >= 500
        ? "Could not reach the API. Start the backend, then try again."
        : `Request failed (${response.status})`);
    const error = new Error(message);
    error.details = data?.error?.details;
    error.requestId = data?.request_id || requestId;
    throw error;
  }
  return data;
}

export function setCompanyId(id) {
  window.localStorage.setItem("regimpact_company_id", id);
}

export const api = {
  createCompany: (body) =>
    request("/api/v1/companies", { method: "POST", body: JSON.stringify(body) }),
  getCompany: (id) => request(`/api/v1/companies/${id}`),
  updateCompany: (id, body) =>
    request(`/api/v1/companies/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  listRegulations: () => request("/api/v1/regulations"),
  getRegulation: (id) => request(`/api/v1/regulations/${id}`),
  uploadRegulation: (form) => request("/api/v1/regulations", { method: "POST", body: form }),
  listPolicies: () => request("/api/v1/policies"),
  getPolicy: (id) => request(`/api/v1/policies/${id}`),
  uploadPolicy: (form) => request("/api/v1/policies", { method: "POST", body: form }),
  startAnalysis: (body) =>
    request("/api/v1/analyses", { method: "POST", body: JSON.stringify(body) }),
  getAnalysis: (id) => request(`/api/v1/analyses/${id}`),
  getAnalysisStatus: (id) => request(`/api/v1/analyses/${id}/status`),
  getGaps: (id) => request(`/api/v1/analyses/${id}/gaps`),
  getActions: (id) => request(`/api/v1/analyses/${id}/actions`),
  updateAction: (id, body) =>
    request(`/api/v1/actions/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  getCitation: (id) => request(`/api/v1/citations/${id}`),
  getCitationSource: (id) => request(`/api/v1/citations/${id}/source`),
  approve: (id) => request(`/api/v1/analyses/${id}/approve`, { method: "POST", body: "{}" }),
  reject: (id) => request(`/api/v1/analyses/${id}/reject`, { method: "POST", body: "{}" }),
};
