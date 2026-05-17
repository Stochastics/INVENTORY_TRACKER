const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  let payload = null
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    payload = await response.json()
  }

  if (!response.ok) {
    throw new Error(formatApiError(payload, response.statusText))
  }

  return payload
}

function formatApiError(payload, fallback) {
  if (!payload) return fallback || 'Request failed'
  if (typeof payload.detail === 'string') return payload.detail
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item.msg || item.message || 'Invalid field').join(', ')
  }
  return payload.message || fallback || 'Request failed'
}

function login(employeeId, pin) {
  return apiRequest('/login', {
    method: 'POST',
    body: JSON.stringify({ employee_id: employeeId, pin }),
  })
}

function getInventoryBySku(sku) {
  return apiRequest(`/inventory/${encodeURIComponent(sku)}`)
}

function createInventoryAction(action, { sku, userId, quantity, notes }) {
  const endpointByAction = {
    RECEIVE: '/inventory/receive',
    SHIP_OUT: '/inventory/ship-out',
    ADJUST: '/inventory/adjust',
  }
  const body =
    action === 'ADJUST'
      ? { sku, user_id: userId, quantity_change: quantity, notes }
      : { sku, user_id: userId, quantity, notes }

  return apiRequest(endpointByAction[action], {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

function getTransactions() {
  return apiRequest('/transactions')
}

export { API_BASE_URL, createInventoryAction, getInventoryBySku, getTransactions, login }
