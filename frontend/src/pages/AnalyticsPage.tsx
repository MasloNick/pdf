import { useQuery } from "@tanstack/react-query";
import { getCourtStats, getJudgeStats } from "../api/endpoints";
import type { CourtStats, JudgeStats } from "../types";

export default function AnalyticsPage() {
  const { data: courts, isLoading: courtsLoading } = useQuery<CourtStats[]>({
    queryKey: ["court-stats"],
    queryFn: () => getCourtStats().then((r) => r.data),
  });

  const { data: judges, isLoading: judgesLoading } = useQuery<JudgeStats[]>({
    queryKey: ["judge-stats"],
    queryFn: () => getJudgeStats().then((r) => r.data),
  });

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Strategic Analytics</h2>

      {/* Court Statistics */}
      <section className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Court Statistics</h3>
        {courtsLoading ? (
          <div className="text-gray-400">Loading...</div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Court</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cases</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Satisfied</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Denied</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Success Rate</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg Award</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {courts?.map((c) => (
                  <tr key={c.court_name} className="hover:bg-gray-50">
                    <td className="px-6 py-4">{c.court_name}</td>
                    <td className="px-6 py-4 text-right">{c.total_cases}</td>
                    <td className="px-6 py-4 text-right text-green-600">{c.satisfied_count}</td>
                    <td className="px-6 py-4 text-right text-red-600">{c.denied_count}</td>
                    <td className="px-6 py-4 text-right font-medium">{c.satisfaction_rate}%</td>
                    <td className="px-6 py-4 text-right">
                      {c.avg_awarded_amount ? `${c.avg_awarded_amount.toLocaleString()} UAH` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Judge Statistics */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Judge Statistics</h3>
        {judgesLoading ? (
          <div className="text-gray-400">Loading...</div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Judge</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Court</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cases</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Satisfied</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Success Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {judges?.map((j) => (
                  <tr key={`${j.judge_name}-${j.court_name}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium">{j.judge_name}</td>
                    <td className="px-6 py-4 text-gray-600">{j.court_name}</td>
                    <td className="px-6 py-4 text-right">{j.total_cases}</td>
                    <td className="px-6 py-4 text-right text-green-600">{j.satisfied_count}</td>
                    <td className="px-6 py-4 text-right font-medium">{j.satisfaction_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
