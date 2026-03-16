import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import type { DashboardStats } from "@/types/models";

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ["dashboard"],
    queryFn: () => api.get("/analytics/dashboard").then((r) => r.data),
  });

  if (isLoading) return <div className="p-8">Завантаження...</div>;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Панель управління</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard label="Портфелі" value={stats?.portfolios ?? 0} />
        <StatCard label="Боржники" value={stats?.debtors ?? 0} />
        <StatCard label="Судові справи" value={stats?.court_cases ?? 0} />
        <StatCard label="Виконавчі провадження" value={stats?.active_enforcements ?? 0} />
        <StatCard label="Банкрути" value={stats?.bankrupt_debtors ?? 0} color="red" />
      </div>
    </div>
  );
}

function StatCard({ label, value, color = "blue" }: { label: string; value: number; color?: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-3xl font-bold text-${color}-600`}>{value.toLocaleString("uk-UA")}</p>
    </div>
  );
}
