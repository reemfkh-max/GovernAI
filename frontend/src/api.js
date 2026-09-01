import { getIdToken } from './auth.js'

const BASE_URL = '/api'

// Every request carries the signed-in user's Firebase ID token, which the
// backend verifies with the Firebase Admin SDK.
async function authHeaders(base = {}) {
  const token = await getIdToken()
  return token ? { ...base, Authorization: `Bearer ${token}` } : { ...base }
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: await authHeaders({
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    }),
  })

  if (!res.ok) {
    let detail = res.statusText

    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // response had no JSON body
    }

    throw new Error(detail)
  }

  return res.json()
}

/* =========================================================
   GOVERNANCE REPORTS
========================================================= */

export function listReports() {
  return request('/use-cases')
}

export function getReport(useCaseId) {
  return request(`/use-cases/${useCaseId}`)
}

export function submitUseCase(payload) {
  return request('/use-cases', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/* =========================================================
   DOCUMENTS
========================================================= */

// Multipart upload — bypasses request()'s JSON Content-Type so the browser
// can set its own multipart boundary.
export async function extractDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${BASE_URL}/documents/extract`, {
    method: 'POST',
    headers: await authHeaders(),
    body: formData,
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // response had no JSON body
    }
    throw new Error(detail)
  }

  return res.json()
}

export function approveUseCase(
  useCaseId,
  { approved, approver, notes }
) {
  return request(`/use-cases/${useCaseId}/approve`, {
    method: 'POST',
    body: JSON.stringify({
      approved,
      approver,
      notes,
    }),
  })
}

/* =========================================================
   POLICIES
========================================================= */

export function listPolicies() {
  return request('/policies')
}

export function createPolicy(payload) {
  return request('/policies', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/* =========================================================
   RISK RULES
========================================================= */

export function listRiskRules() {
  return request('/risk-rules')
}

export function createRiskRule(payload) {
  return request('/risk-rules', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/* =========================================================
   AUDIT LOG
========================================================= */

export function getAuditLog(useCaseId) {
  const query = useCaseId
    ? `?use_case_id=${encodeURIComponent(useCaseId)}`
    : ''

  return request(`/audit-log${query}`)
}
/* =========================================================
   IDENTITY
========================================================= */

// Echoes back the identity the backend derived from the ID token — useful to
// confirm frontend and backend agree on who is signed in.
export function whoami() {
  return request('/auth/me')
}
