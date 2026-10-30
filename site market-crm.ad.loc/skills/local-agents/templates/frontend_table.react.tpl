import React from 'react'

// Columns: [{ key: 'email', label: 'Email' }, ...]
// Data: [{ email: 'a@b.com', user: 'Name' }, ...]

export default function TableTemplate({ columns = [], data = [], pageSize = 20 }) {
  return (
    <div className="table-template">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, pageSize).map((row, idx) => (
            <tr key={idx}>
              {columns.map((c) => (
                <td key={c.key + idx}>{String(row[c.key] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <style jsx>{`
        .table-template table { width: 100%; border-collapse: collapse; }
        .table-template th, .table-template td { border: 1px solid #ddd; padding: 8px; }
        .table-template th { background: #f6f6f6; text-align: left; }
      `}</style>
    </div>
  )
}
