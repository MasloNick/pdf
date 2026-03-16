import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { courtCaseApi } from '../services/api'
import type { CourtCase, PaginatedResponse } from '../types'

export default function CourtCases() {
  const [page, setPage] = useState(1)
  const [outcomeFilter, setOutcomeFilter] = useState<string>('')

  const { data, isLoading } = useQuery<PaginatedResponse<CourtCase>>({
    queryKey: ['court-cases', page, outcomeFilter],
    queryFn: async () =>
      (await courtCaseApi.list({ page, page_size: 50, outcome: outcomeFilter || undefined })).data,
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Court Cases</h1>
        <select
          value={outcomeFilter}
          onChange={(e) => {
            setOutcomeFilter(e.target.value)
            setPage(1)
          }}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">All outcomes</option>
          <option value="satisfied">Satisfied</option>
          <option value="partial">Partial</option>
          <option value="refused">Refused</option>
          <option value="not_yet">Pending</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Case #</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Court</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Judge</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Filing Date</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Claimed</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Awarded</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Ratio</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((c) => (
                <tr key={c.id} className="border-b hover:bg-gray-50 cursor-pointer">
                  <td className="px-4 py-3 font-mono text-xs">{c.case_number || '-'}</td>
                  <td className="px-4 py-3 text-xs">{c.court_name || '-'}</td>
                  <td className="px-4 py-3">{c.judge_name || '-'}</td>
                  <td className="px-4 py-3">{c.filing_date || '-'}</td>
                  <td className="px-4 py-3 text-right">
                    {c.claimed_total?.toLocaleString() || '-'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {c.awarded_total?.toLocaleString() || '-'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {c.award_ratio != null ? `${(c.award_ratio * 100).toFixed(1)}%` : '-'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                        c.decision_outcome === 'satisfied'
                          ? 'bg-green-100 text-green-700'
                          : c.decision_outcome === 'partial'
                            ? 'bg-yellow-100 text-yellow-700'
                            : c.decision_outcome === 'refused'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {c.decision_outcome || 'pending'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && (
            <div className="flex justify-between items-center px-4 py-3 bg-gray-50">
              <span className="text-sm text-gray-500">
                {data.total.toLocaleString()} cases | Page {page}
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
