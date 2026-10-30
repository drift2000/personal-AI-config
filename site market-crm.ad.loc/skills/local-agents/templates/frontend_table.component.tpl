import React, { useMemo, useState } from 'react'

export default function TableTemplate({ columns = [], data = [], pageSize = 20 }) {
  const [page, setPage] = useState(1)
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  const sorted = useMemo(() => {
    if (!sortKey) return data
    const copy = [...data]
    copy.sort((a, b) => {
      const va = a[sortKey]
      const vb = b[sortKey]
      if (va == null) return 1
      if (vb == null) return -1
      if (va === vb) return 0
      return (va > vb ? 1 : -1) * (sortDir === 'asc' ? 1 : -1)
    })
    return copy
  }, [data, sortKey, sortDir])

  const totalPages = Math.max(1, Math.ceil((sorted.length || 0) / pageSize))
  const visible = sorted.slice((page - 1) * pageSize, page * pageSize)

  function toggleSort(key) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  return (
    <div className="table-wrapper">
      <table className="table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} onClick={() => toggleSort(c.key)} style={{ cursor: 'pointer' }}>
                {c.label} {sortKey === c.key ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {visible.map((row, ri) => (
            <tr key={ri}>
              {columns.map((c) => (
                <td key={c.key + ri}>{row[c.key] ?? ''}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pager">
        <button onClick={() => setPage(1)} disabled={page === 1}>«</button>
        <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>‹</button>
        <span>Page {page} / {totalPages}</span>
        <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>›</button>
        <button onClick={() => setPage(totalPages)} disabled={page === totalPages}>»</button>
      </div>

      <style jsx>{`
        .table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #e6e6e6; padding: 8px; }
        th { background: #fafafa; }
        .pager { margin-top: 8px; display:flex; gap:8px; align-items:center }
      `}</style>
    </div>
  )
}
