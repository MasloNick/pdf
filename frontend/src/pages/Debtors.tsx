import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { debtorApi } from '../services/api'
import type { Debtor, PaginatedResponse } from '../types'
import { Search } from 'lucide-react'

export default function Debtors() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery<PaginatedResponse<Debtor>>({
    queryKey: ['debtors', page, search],
    queryFn: async () =>
      (await debtorApi.list({ page, page_size: 50, search: search || undefined })).data,
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Debtors</h1>
        <div className="relative">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, IPN..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            className="pl-10 pr-4 py-2 border rounded-lg text-sm w-72 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Full Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">IPN</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Phone</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Contract</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Total (UAH)</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((d) => (
                <tr key={d.id} className="border-b hover:bg-gray-50 cursor-pointer">
                  <td className="px-4 py-3 font-medium">{d.full_name}</td>
                  <td className="px-4 py-3 font-mono text-xs">{d.ipn || '-'}</td>
                  <td className="px-4 py-3">{d.phone_primary || '-'}</td>
                  <td className="px-4 py-3">{d.credit_contract_number || '-'}</td>
                  <td className="px-4 py-3 text-right">
                    {d.purchased_total_uah?.toLocaleString() || '-'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                        d.collection_status === 'active_court'
                          ? 'bg-blue-100 text-blue-700'
                          : d.collection_status === 'vp_active'
                            ? 'bg-green-100 text-green-700'
                            : d.collection_status === 'bankruptcy'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {d.collection_status || 'unknown'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && (
            <div className="flex justify-between items-center px-4 py-3 bg-gray-50">
              <span className="text-sm text-gray-500">
                {data.total.toLocaleString()} debtors total | Page {page}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 rounded border text-sm disabled:opacity-50"
                >
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil(data.total / data.page_size)}
                  className="px-3 py-1 rounded border text-sm disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
