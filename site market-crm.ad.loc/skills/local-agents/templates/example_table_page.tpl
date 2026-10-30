import React from 'react'
import TableTemplate from './frontend_table.component.tpl'

const columns = [
  { key: 'email', label: 'Email' },
  { key: 'user', label: 'User' },
  { key: 'company', label: 'Company' },
  { key: 'status', label: 'Status' },
]

const sampleData = Array.from({ length: 45 }).map((_, i) => ({
  email: `user${i}@example.com`,
  user: `User ${i}`,
  company: `Company ${i % 5}`,
  status: i % 2 === 0 ? 'active' : 'inactive',
}))

export default function ExampleTablePage() {
  return (
    <div style={{ padding: 16 }}>
      <h2>Example Table</h2>
      <TableTemplate columns={columns} data={sampleData} pageSize={10} />
    </div>
  )
}
