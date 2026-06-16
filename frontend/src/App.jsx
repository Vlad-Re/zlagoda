import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('categories')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Стан для звітів
  const [reportResult, setReportResult] = useState(null)
  const [activeReport, setActiveReport] = useState(null)

  const endpoints = {
    categories: '/api/categories/',
    products: '/api/products/',
    employees: '/api/employees/',
    cards: '/api/customer-cards/',
    checks: '/api/checks/'
  }

  const fetchData = async (tab) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(endpoints[tab])
      if (!response.ok) {
        throw new Error(`Помилка завантаження: ${response.status} ${response.statusText}`)
      }
      const result = await response.json()
      // Django REST Framework зазвичай повертає { results: [...] } або просто масив
      setData(result.results || result)
    } catch (err) {
      setError(err.message)
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(activeTab)
  }, [activeTab])

  const runReport = async (reportName, url) => {
    setActiveReport(reportName)
    setReportResult(null)
    try {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`Помилка звіту: ${response.status}`)
      }
      const data = await response.json()
      setReportResult(data)
    } catch (err) {
      setReportResult({ error: err.message })
    }
  }

  // Динамічне визначення колонок для таблиці
  const getTableHeaders = () => {
    if (data.length === 0) return []
    return Object.keys(data[0])
  }

  return (
    <div className="app-container">
      <header>
        <h1>Панель моніторингу «Злагода»</h1>
        <p>Швидкий перегляд даних та аналітичних звітів з вашого Django бекенду</p>
      </header>

      {/* Навігація по таблицях */}
      <div className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === 'categories' ? 'active' : ''}`}
          onClick={() => setActiveTab('categories')}
        >
          Категорії
        </button>
        <button
          className={`tab-btn ${activeTab === 'products' ? 'active' : ''}`}
          onClick={() => setActiveTab('products')}
        >
          Товари
        </button>
        <button
          className={`tab-btn ${activeTab === 'employees' ? 'active' : ''}`}
          onClick={() => setActiveTab('employees')}
        >
          Працівники
        </button>
        <button
          className={`tab-btn ${activeTab === 'cards' ? 'active' : ''}`}
          onClick={() => setActiveTab('cards')}
        >
          Картки клієнтів
        </button>
        <button
          className={`tab-btn ${activeTab === 'checks' ? 'active' : ''}`}
          onClick={() => setActiveTab('checks')}
        >
          Чеки
        </button>
      </div>

      {/* Основний контент таблиць */}
      <section className="content-section">
        <div className="section-header">
          <h2>
            Дані: {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
          </h2>
          <button className="refresh-btn" onClick={() => fetchData(activeTab)}>
            Оновити
          </button>
        </div>

        {error && <div className="error-message">⚠️ {error}</div>}

        {loading ? (
          <div className="loading">Завантаження даних з сервера...</div>
        ) : data.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  {getTableHeaders().map((header) => (
                    <th key={header}>{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, index) => (
                  <tr key={index}>
                    {getTableHeaders().map((header) => (
                      <td key={header}>
                        {typeof row[header] === 'object' && row[header] !== null
                          ? JSON.stringify(row[header])
                          : String(row[header] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">Немає даних для відображення. Спробуйте запустити seed_db або додати записи.</div>
        )}
      </section>

      {/* Секція аналітичних звітів */}
      <section className="content-section">
        <h2>Аналітичні звіти (SQL запити)</h2>
        <p style={{ color: 'var(--text-muted)' }}>Запуск складних аналітичних запитів та реляційного ділення:</p>

        <div className="reports-grid">
          <div className="report-card">
            <h3>Топ касирів</h3>
            <p>Отримати список касирів, сортованих за сумою продажів за весь час.</p>
            <button
              className="report-btn"
              onClick={() => runReport('Топ касирів', '/api/reports/top-cashiers/')}
            >
              Запустити звіт
            </button>
          </div>

          <div className="report-card">
            <h3>Продажі по категоріях</h3>
            <p>Загальна кількість проданих товарів та виручка для кожної категорії.</p>
            <button
              className="report-btn"
              onClick={() => runReport('Продажі по категоріях', '/api/reports/total-sold-per-category/')}
            >
              Запустити звіт
            </button>
          </div>

          <div className="report-card">
            <h3>Клієнти у всіх касирів</h3>
            <p>Пошук постійних покупців, які обслуговувалися абсолютно у кожного касира.</p>
            <button
              className="report-btn"
              onClick={() => runReport('Клієнти у всіх касирів', '/api/reports/customers-served-by-all-cashiers/')}
            >
              Запустити звіт
            </button>
          </div>
        </div>

        {activeReport && (
          <div className="report-result">
            <h4>Результат звіту: {activeReport}</h4>
            <pre>
              {reportResult
                ? JSON.stringify(reportResult, null, 2)
                : 'Виконується запит...'}
            </pre>
          </div>
        )}
      </section>
    </div>
  )
}

export default App
