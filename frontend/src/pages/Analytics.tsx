import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";

export default function Analytics() {
  const { data: courts = [] } = useQuery({
    queryKey: ["analytics-courts"],
    queryFn: () => api.get("/analytics/courts").then((r) => r.data),
  });

  const { data: judges = [] } = useQuery({
    queryKey: ["analytics-judges"],
    queryFn: () => api.get("/analytics/judges").then((r) => r.data),
  });

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Аналітика</h1>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Статистика по судах</h2>
        <table className="w-full bg-white rounded-lg shadow">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-3 text-left">Суд</th>
              <th className="p-3 text-right">Справи</th>
              <th className="p-3 text-right">Присуджено</th>
            </tr>
          </thead>
          <tbody>
            {courts.map((c: { court_name: string; total_cases: number; total_awarded: number | null }) => (
              <tr key={c.court_name} className="border-t">
                <td className="p-3">{c.court_name}</td>
                <td className="p-3 text-right">{c.total_cases}</td>
                <td className="p-3 text-right">{c.total_awarded ? Number(c.total_awarded).toLocaleString("uk-UA") : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Статистика по суддях</h2>
        <table className="w-full bg-white rounded-lg shadow">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-3 text-left">Суддя</th>
              <th className="p-3 text-right">Справи</th>
              <th className="p-3 text-right">Присуджено</th>
            </tr>
          </thead>
          <tbody>
            {judges.map((j: { judge_name: string; total_cases: number; total_awarded: number | null }) => (
              <tr key={j.judge_name} className="border-t">
                <td className="p-3">{j.judge_name}</td>
                <td className="p-3 text-right">{j.total_cases}</td>
                <td className="p-3 text-right">{j.total_awarded ? Number(j.total_awarded).toLocaleString("uk-UA") : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
