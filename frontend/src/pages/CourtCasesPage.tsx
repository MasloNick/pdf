import { useQuery } from "@tanstack/react-query";
import { getCourtCases } from "../api/endpoints";
import type { CourtCase } from "../types";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  filed: "bg-blue-100 text-blue-700",
  in_progress: "bg-yellow-100 text-yellow-700",
  decided: "bg-green-100 text-green-700",
  appealed: "bg-orange-100 text-orange-700",
  enforcement: "bg-purple-100 text-purple-700",
  closed: "bg-gray-200 text-gray-600",
};

export default function CourtCasesPage() {
  const { data, isLoading } = useQuery<CourtCase[]>({
    queryKey: ["court-cases"],
    queryFn: () => getCourtCases({ page: 1, size: 50 }).then((r) => r.data),
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Court Cases</h2>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          + New Case
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-400">Loading...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Case Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Court</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Judge</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Claim Amount</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Awarded</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-6 py-4 font-medium text-primary-600">{c.case_number}</td>
                  <td className="px-6 py-4 text-gray-600 max-w-xs truncate">{c.court_name}</td>
                  <td className="px-6 py-4 text-gray-600">{c.judge_name || "—"}</td>
                  <td className="px-6 py-4 text-gray-600 uppercase text-xs">{c.case_type}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded-full ${STATUS_COLORS[c.status] || "bg-gray-100"}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">{c.claim_amount.toLocaleString()}</td>
                  <td className="px-6 py-4 text-right">{c.awarded_amount?.toLocaleString() || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
