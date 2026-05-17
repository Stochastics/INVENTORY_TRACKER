import { useEffect, useMemo, useState } from 'react'
import {
  API_BASE_URL,
  createInventoryAction,
  getInventoryBySku,
  getTransactions,
  login,
} from './api.js'

const STORED_USER_KEY = 'inventory_mvp_user'
const ACTIONS = {
  RECEIVE: { label: 'Receive', tone: 'positive', hint: 'Add newly received stock.' },
  SHIP_OUT: { label: 'Ship Out', tone: 'warning', hint: 'Remove stock leaving inventory.' },
  ADJUST: { label: 'Adjust', tone: 'neutral', hint: 'Enter a signed correction.' },
}

function getStoredUser() {
  try {
    const saved = localStorage.getItem(STORED_USER_KEY)
    return saved ? JSON.parse(saved) : null
  } catch (_error) {
    localStorage.removeItem(STORED_USER_KEY)
    return null
  }
}

function App() {
  const [user, setUser] = useState(getStoredUser)
  const [sku, setSku] = useState('')
  const [item, setItem] = useState(null)
  const [selectedAction, setSelectedAction] = useState(null)
  const [confirmation, setConfirmation] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [isTransactionsLoading, setIsTransactionsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (user) {
      refreshTransactions()
    }
  }, [user])

  async function refreshTransactions() {
    setIsTransactionsLoading(true)
    try {
      const recentTransactions = await getTransactions()
      setTransactions(recentTransactions.slice(0, 10))
    } catch (requestError) {
      setError(`Could not load transaction history: ${requestError.message}`)
    } finally {
      setIsTransactionsLoading(false)
    }
  }

  function handleLogin(authenticatedUser) {
    localStorage.setItem(STORED_USER_KEY, JSON.stringify(authenticatedUser))
    setUser(authenticatedUser)
    setError('')
  }

  function handleLogout() {
    localStorage.removeItem(STORED_USER_KEY)
    setUser(null)
    setSku('')
    setItem(null)
    setSelectedAction(null)
    setConfirmation(null)
    setTransactions([])
    setError('')
  }

  async function handleSearch(event) {
    event.preventDefault()
    const normalizedSku = sku.trim()
    if (!normalizedSku) {
      setError('Enter a SKU to look up inventory.')
      return
    }

    setIsSearching(true)
    setError('')
    setConfirmation(null)
    setSelectedAction(null)

    try {
      const inventoryItem = await getInventoryBySku(normalizedSku)
      setItem(inventoryItem)
      setSku(inventoryItem.sku)
    } catch (requestError) {
      setItem(null)
      setError(`SKU lookup failed: ${requestError.message}`)
    } finally {
      setIsSearching(false)
    }
  }

  async function handleActionComplete(transaction) {
    setConfirmation(transaction)
    setSelectedAction(null)
    setError('')
    try {
      const refreshedItem = await getInventoryBySku(transaction.sku)
      setItem(refreshedItem)
    } catch (_requestError) {
      setItem((currentItem) =>
        currentItem ? { ...currentItem, quantity_on_hand: transaction.quantity_after } : currentItem,
      )
    }
    refreshTransactions()
  }

  if (!user) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return (
    <main className="app-shell">
      <div className="app-container">
        <header className="top-bar">
          <div>
            <p className="eyebrow">Inventory MVP</p>
            <h1>Shop floor inventory</h1>
            <p className="welcome">Signed in as {user.name}</p>
          </div>
          <button className="button button-ghost" type="button" onClick={handleLogout}>
            Logout
          </button>
        </header>

        {error && <Banner tone="error" message={error} />}
        {confirmation && <Confirmation transaction={confirmation} />}

        <section className="card lookup-card" aria-labelledby="sku-heading">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Lookup</p>
              <h2 id="sku-heading">Find an item</h2>
            </div>
          </div>
          <form className="stack" onSubmit={handleSearch}>
            <label htmlFor="sku">SKU</label>
            <div className="search-row">
              <input
                id="sku"
                value={sku}
                onChange={(event) => setSku(event.target.value)}
                placeholder="WRNCH-001"
                autoComplete="off"
              />
              <button className="button button-primary" type="submit" disabled={isSearching}>
                {isSearching ? 'Searching…' : 'Search'}
              </button>
            </div>
          </form>
        </section>

        {item && !selectedAction && <ItemDetail item={item} onSelectAction={setSelectedAction} />}

        {item && selectedAction && (
          <InventoryActionForm
            action={selectedAction}
            item={item}
            user={user}
            onCancel={() => setSelectedAction(null)}
            onComplete={handleActionComplete}
            onError={setError}
          />
        )}

        <TransactionHistory
          transactions={transactions}
          isLoading={isTransactionsLoading}
          onRefresh={refreshTransactions}
        />

        <p className="api-note">Connected to {API_BASE_URL}</p>
      </div>
    </main>
  )
}

function LoginScreen({ onLogin }) {
  const [employeeId, setEmployeeId] = useState('')
  const [pin, setPin] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    if (!employeeId.trim() || !pin.trim()) {
      setError('Employee ID and PIN are required.')
      return
    }

    setIsLoading(true)
    setError('')
    try {
      const authenticatedUser = await login(employeeId.trim(), pin.trim())
      onLogin(authenticatedUser)
    } catch (requestError) {
      setError(`Login failed: ${requestError.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app-shell login-shell">
      <section className="card login-card">
        <div className="brand-mark" aria-hidden="true">
          IM
        </div>
        <p className="eyebrow">Inventory MVP</p>
        <h1>Employee sign in</h1>
        <p className="muted">Use your employee ID and PIN to manage shop floor inventory.</p>
        {error && <Banner tone="error" message={error} />}
        <form className="stack" onSubmit={handleSubmit}>
          <label htmlFor="employee-id">Employee ID</label>
          <input
            id="employee-id"
            value={employeeId}
            onChange={(event) => setEmployeeId(event.target.value)}
            placeholder="EMP001"
            autoComplete="username"
          />
          <label htmlFor="pin">PIN</label>
          <input
            id="pin"
            type="password"
            inputMode="numeric"
            value={pin}
            onChange={(event) => setPin(event.target.value)}
            placeholder="••••"
            autoComplete="current-password"
          />
          <button className="button button-primary button-full" type="submit" disabled={isLoading}>
            {isLoading ? 'Signing in…' : 'Login'}
          </button>
        </form>
      </section>
    </main>
  )
}

function ItemDetail({ item, onSelectAction }) {
  return (
    <section className="card item-card" aria-labelledby="item-heading">
      <div className="item-header">
        <div>
          <p className="eyebrow">Item detail</p>
          <h2 id="item-heading">{item.item_name}</h2>
          <p className="sku-pill">{item.sku}</p>
        </div>
        <div className="quantity-badge">
          <span>{item.quantity_on_hand}</span>
          <small>on hand</small>
        </div>
      </div>
      <p className="description">{item.description || 'No description has been added for this item.'}</p>
      <div className="action-grid" aria-label="Inventory actions">
        {Object.entries(ACTIONS).map(([key, action]) => (
          <button
            className={`button action-button ${action.tone}`}
            key={key}
            type="button"
            onClick={() => onSelectAction(key)}
          >
            <span>{action.label}</span>
            <small>{action.hint}</small>
          </button>
        ))}
      </div>
    </section>
  )
}

function InventoryActionForm({ action, item, user, onCancel, onComplete, onError }) {
  const [quantity, setQuantity] = useState('')
  const [notes, setNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const actionMeta = ACTIONS[action]
  const helperText = useMemo(() => {
    if (action === 'ADJUST') return 'Use a positive number to add stock or a negative number to remove stock.'
    if (action === 'SHIP_OUT') return 'Enter the number of units leaving inventory.'
    return 'Enter the number of units received into inventory.'
  }, [action])

  async function handleSubmit(event) {
    event.preventDefault()
    const parsedQuantity = Number(quantity)
    if (!Number.isInteger(parsedQuantity)) {
      onError('Quantity must be a whole number.')
      return
    }
    if (action !== 'ADJUST' && parsedQuantity <= 0) {
      onError('Receive and Ship Out quantities must be greater than zero.')
      return
    }
    if (action === 'ADJUST' && parsedQuantity === 0) {
      onError('Adjustment quantity cannot be zero.')
      return
    }

    setIsSubmitting(true)
    onError('')
    try {
      const transaction = await createInventoryAction(action, {
        sku: item.sku,
        userId: user.user_id,
        quantity: parsedQuantity,
        notes: notes.trim() || null,
      })
      onComplete(transaction)
    } catch (requestError) {
      onError(`${actionMeta.label} failed: ${requestError.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="card" aria-labelledby="action-heading">
      <p className="eyebrow">Inventory action</p>
      <h2 id="action-heading">{actionMeta.label} {item.sku}</h2>
      <p className="muted">Current quantity: {item.quantity_on_hand}</p>
      <form className="stack" onSubmit={handleSubmit}>
        <label htmlFor="quantity">Quantity</label>
        <input
          id="quantity"
          type="number"
          inputMode="numeric"
          value={quantity}
          onChange={(event) => setQuantity(event.target.value)}
          placeholder={action === 'ADJUST' ? '-3 or 5' : '10'}
        />
        <p className="field-help">{helperText}</p>
        <label htmlFor="notes">Notes</label>
        <textarea
          id="notes"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Optional notes for this transaction"
          rows="3"
        />
        <div className="button-row">
          <button className="button button-secondary" type="button" onClick={onCancel}>
            Cancel
          </button>
          <button className="button button-primary" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Submitting…' : 'Submit'}
          </button>
        </div>
      </form>
    </section>
  )
}

function Confirmation({ transaction }) {
  return (
    <section className="banner success-card" aria-live="polite">
      <strong>Inventory updated successfully.</strong>
      <div className="confirmation-grid">
        <Metric label="Previous" value={transaction.quantity_before} />
        <Metric label="Change" value={formatChange(transaction.quantity_change)} />
        <Metric label="New" value={transaction.quantity_after} />
      </div>
    </section>
  )
}

function TransactionHistory({ transactions, isLoading, onRefresh }) {
  return (
    <section className="card history-card" aria-labelledby="history-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Recent activity</p>
          <h2 id="history-heading">Transaction history</h2>
        </div>
        <button className="button button-ghost" type="button" onClick={onRefresh} disabled={isLoading}>
          {isLoading ? 'Loading…' : 'Refresh'}
        </button>
      </div>
      {transactions.length === 0 && !isLoading ? (
        <p className="empty-state">No transactions yet. Completed inventory actions will appear here.</p>
      ) : (
        <div className="history-list">
          {transactions.map((transaction) => (
            <article className="transaction-card" key={transaction.transaction_id}>
              <div className="transaction-main">
                <div>
                  <strong>{formatAction(transaction.transaction_type)}</strong>
                  <p>{transaction.sku} · {transaction.item_name}</p>
                </div>
                <span className={transaction.quantity_change >= 0 ? 'change positive-text' : 'change negative-text'}>
                  {formatChange(transaction.quantity_change)}
                </span>
              </div>
              <dl className="transaction-meta">
                <div>
                  <dt>User</dt>
                  <dd>{transaction.user_name}</dd>
                </div>
                <div>
                  <dt>Before / After</dt>
                  <dd>{transaction.quantity_before} → {transaction.quantity_after}</dd>
                </div>
                <div>
                  <dt>Date</dt>
                  <dd>{formatDate(transaction.created_at)}</dd>
                </div>
              </dl>
              {transaction.notes && <p className="notes">“{transaction.notes}”</p>}
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

function Banner({ tone, message }) {
  return <div className={`banner ${tone}`} role="alert">{message}</div>
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function formatAction(action) {
  return action.replace('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatChange(quantityChange) {
  return quantityChange > 0 ? `+${quantityChange}` : `${quantityChange}`
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

export default App
