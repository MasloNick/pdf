import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDebtors } from "../api/endpoints";
import type { DebtorListResponse } from "../types";

const STATUS_LABELS: Record<string, string> = {
  new: "New",
  in_court: "In Court",
  judgment_obtained: "Judgment",
  enforcement: "Enforcement",
  partially_recovered: "Partial Recovery",
  fully_recovered: "Recovered",
  bankrupt: "Bankrupt",
  written_off: "Written Off",
};

export default function DebtorsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery<DebtorListResponse>({
    queryKey: ["debtors", page, search],
    queryFn: () => getDebtors({ page, size: 50, search: search || undefined }).then((r) => r.data),
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Debtors</h2>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Search by name or IPN..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="px-4 py-2 border rounded-lg w-80 focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-gray-400">Loading...</div>
      ) : (
        <>
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IPN</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Original Debt</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Current Debt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data?.items.map((d) => (
                  <tr key={d.id} className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-6 py-4 font-medium">{d.full_name}</td>
                    <td className="px-6 py-4 text-gray-600">{d.ipn_code || "—"}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">
                        {STATUS_LABELS[d.status] || d.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">{d.original_debt_amount.toLocaleString()} {d.currency}</td>
                    <td className="px-6 py-4 text-right">{d.current_debt_amount.toLocaleString()} {d.currency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data && data.total > data.size && (
            <div className="flex justify-center gap-2 mt-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Prev
              </button>
              <span className="px-3 py-1">
                Page {data.page} of {Math.ceil(data.total / data.size)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(data.total / data.size)}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
