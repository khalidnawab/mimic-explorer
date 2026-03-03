const BASE_URL = '/api'

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || error.error || `HTTP ${response.status}`)
  }

  if (response.status === 204) return null as T
  return response.json()
}

export async function fetchFHIR(path: string): Promise<any> {
  const response = await fetch(`/fhir${path}`, {
    headers: { 'Accept': 'application/fhir+json' },
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ issue: [{ diagnostics: response.statusText }] }))
    throw new Error(error.issue?.[0]?.diagnostics || `HTTP ${response.status}`)
  }
  return response.json()
}

export const api = {
  // Status
  getStatus: () => fetchJSON<any>('/status/'),

  // Import
  browseFolder: () =>
    fetchJSON<{ path: string }>('/import/browse-folder/', {
      method: 'POST',
    }),

  validateFolder: (folderPath: string) =>
    fetchJSON<any>('/import/validate-folder/', {
      method: 'POST',
      body: JSON.stringify({ folder_path: folderPath }),
    }),

  startImport: (params: {
    folder_path: string
    modules: string[]
    patient_limit: number | null
    generate_fhir: boolean
  }) =>
    fetchJSON<any>('/import/start/', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  getImportStatus: () => fetchJSON<any>('/import/status/'),

  cancelImport: () =>
    fetchJSON<any>('/import/cancel/', { method: 'POST' }),

  supplementImport: (params: {
    folder_path: string
    modules: string[]
    patient_limit: number | null
    generate_fhir: boolean
    existing_patients_only: boolean
  }) =>
    fetchJSON<any>('/import/supplement/', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Reset
  resetApp: () =>
    fetchJSON<{ status: string }>('/reset/', { method: 'POST' }),

  // Patients
  getPatients: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return fetchJSON<any>(`/patients/${query}`)
  },

  getPatient: (subjectId: number) =>
    fetchJSON<any>(`/patients/${subjectId}/`),

  getPatientTimeline: (subjectId: number) =>
    fetchJSON<any>(`/patients/${subjectId}/timeline/`),

  // Encounters
  getEncounters: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return fetchJSON<any>(`/encounters/${query}`)
  },

  getEncounter: (hadmId: number) =>
    fetchJSON<any>(`/encounters/${hadmId}/`),

  getEncounterLabs: (hadmId: number, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return fetchJSON<any>(`/encounters/${hadmId}/labs/${query}`)
  },

  getEncounterVitals: (hadmId: number, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return fetchJSON<any>(`/encounters/${hadmId}/vitals/${query}`)
  },

  getEncounterDiagnoses: (hadmId: number) =>
    fetchJSON<any>(`/encounters/${hadmId}/diagnoses/`),

  getEncounterProcedures: (hadmId: number) =>
    fetchJSON<any>(`/encounters/${hadmId}/procedures/`),

  getEncounterMedications: (hadmId: number) =>
    fetchJSON<any>(`/encounters/${hadmId}/medications/`),

  getEncounterNotes: (hadmId: number) =>
    fetchJSON<any>(`/encounters/${hadmId}/notes/`),

  getEncounterICUStays: (hadmId: number) =>
    fetchJSON<any>(`/encounters/${hadmId}/icu-stays/`),

  // Clinical cross-encounter
  getLabs: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return fetchJSON<any>(`/labs/${query}`)
  },

  getVitals: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return fetchJSON<any>(`/vitals/${query}`)
  },

  getLabItems: () => fetchJSON<any>('/lab-items/'),
  getVitalItems: () => fetchJSON<any>('/vital-items/'),

  // Dashboards
  getDemographics: () => fetchJSON<any>('/dashboards/demographics/'),
  getUtilization: () => fetchJSON<any>('/dashboards/utilization/'),
  getClinical: () => fetchJSON<any>('/dashboards/clinical/'),
  getMissingness: () => fetchJSON<any>('/dashboards/missingness/'),

  // Research - Cohorts
  getCohorts: () => fetchJSON<any>('/research/cohorts/'),
  createCohort: (data: { name: string; description?: string; criteria: any }) =>
    fetchJSON<any>('/research/cohorts/', { method: 'POST', body: JSON.stringify(data) }),
  getCohort: (id: number) => fetchJSON<any>(`/research/cohorts/${id}/`),
  updateCohort: (id: number, data: any) =>
    fetchJSON<any>(`/research/cohorts/${id}/`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCohort: (id: number) =>
    fetchJSON<any>(`/research/cohorts/${id}/`, { method: 'DELETE' }),
  executeCohort: (id: number) =>
    fetchJSON<any>(`/research/cohorts/${id}/execute/`, { method: 'POST' }),
  getCohortStats: (id: number) =>
    fetchJSON<any>(`/research/cohorts/${id}/stats/`),
  getCohortMembers: (id: number, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return fetchJSON<any>(`/research/cohorts/${id}/members/${query}`)
  },
  compareCohorts: (cohortA: number, cohortB: number) =>
    fetchJSON<any>('/research/cohorts/compare/', {
      method: 'POST',
      body: JSON.stringify({ cohort_a: cohortA, cohort_b: cohortB }),
    }),

  // Research - Queries
  getQueries: () => fetchJSON<any>('/research/queries/'),
  createQuery: (data: { name: string; description?: string; query_definition: any }) =>
    fetchJSON<any>('/research/queries/', { method: 'POST', body: JSON.stringify(data) }),
  deleteQuery: (id: number) =>
    fetchJSON<any>(`/research/queries/${id}/`, { method: 'DELETE' }),
  runQuery: (id: number) =>
    fetchJSON<any>(`/research/queries/${id}/run/`, { method: 'POST' }),

  // Research - Search & Export
  search: (criteria: any, page?: number) =>
    fetchJSON<any>('/research/search/', {
      method: 'POST',
      body: JSON.stringify({ criteria, page: page || 1 }),
    }),
  exportData: (params: { format: string; cohort_id?: number; patient_ids?: number[]; data_types: string[] }) => {
    if (params.format === 'csv') {
      return fetch(`${BASE_URL}/research/export/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      }).then(r => r.blob())
    }
    return fetchJSON<any>('/research/export/', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  },
}
