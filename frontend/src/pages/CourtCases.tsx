import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import type { CourtCase } from "@/types/models";

export default function CourtCases() {
  const { data: cases = [], isLoading } = useQuery<CourtCase[]>({
    queryKey: ["court-cases"],
    queryFn: () => api.get("/court-cases/").then((r) => r.data),
  });

  if (isLoading) return <div className="p-8">Завантаження...</div>;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Судові справи</h1>
      <table className="w-full bg-white rounded-lg shadow">
        <thead className="bg-gray-50">
          <tr>
            <th className="p-3 text-left">Номер справи</th>
            <th className="p-3 text-left">Суд</th>
            <th className="p-3 text-left">Суддя</th>
            <th className="p-3 text-left">Тип</th>
            <th className="p-3 text-right">Сума позову</th>
            <th className="p-3 text-left">Статус</th>
            <th className="p-3 text-right">Присуджено</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr key={c.id} className="border-t hover:bg-gray-50">
              <td className="p-3 font-mono text-sm">{c.case_number}</td>
              <td className="p-3">{c.court_name}</td>
              <td className="p-3">{c.judge_name ?? "—"}</td>
              <td className="p-3">{c.proceeding_type}</td>
              <td className="p-3 text-right">{c.claim_amount ? Number(c.claim_amount).toLocaleString("uk-UA") : "—"}</td>
              <td className="p-3">{c.status}</td>
              <td className="p-3 text-right">{c.awarded_amount ? Number(c.awarded_amount).toLocaleString("uk-UA") : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
