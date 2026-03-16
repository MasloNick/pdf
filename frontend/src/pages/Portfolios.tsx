import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { portfolioApi } from '../services/api'
import type { Portfolio, PaginatedResponse } from '../types'
import { Plus } from 'lucide-react'

export default function Portfolios() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery<PaginatedResponse<Portfolio>>({
    queryKey: ['portfolios', page],
    queryFn: async () => (await portfolioApi.list(page)).data,
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Portfolios</h1>
        <button className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
          <Plus size={18} />
          New Portfolio
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Purchase Date</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Price (UAH)</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Seller</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Debtors</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((p) => (
                <tr key={p.id} className="border-b hover:bg-gray-50 cursor-pointer">
                  <td className="px-4 py-3 font-medium">{p.name}</td>
                  <td className="px-4 py-3">{p.purchase_date || '-'}</td>
                  <td className="px-4 py-3 text-right">
                    {p.purchase_price_uah?.toLocaleString() || '-'}
                  </td>
                  <td className="px-4 py-3">{p.seller_name || '-'}</td>
                  <td className="px-4 py-3 text-right">{p.debtor_count || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.total > 20 && (
            <div className="flex justify-between items-center px-4 py-3 bg-gray-50">
              <span className="text-sm text-gray-500">
                Page {page} of {Math.ceil(data.total / data.page_size)}
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
