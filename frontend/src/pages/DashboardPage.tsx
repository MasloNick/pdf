import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../api/endpoints";
import type { DashboardSummary } from "../types";

function StatCard({ label, value, alert }: { label: string; value: string | number; alert?: boolean }) {
  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${alert ? "border-l-4 border-red-500" : ""}`}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery<DashboardSummary>({
    queryKey: ["dashboard"],
    queryFn: () => getDashboard().then((r) => r.data),
  });

  if (isLoading) return <div className="text-gray-400">Loading dashboard...</div>;
  if (!data) return <div className="text-gray-400">No data available</div>;

  const { portfolio_stats: ps } = data;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Portfolios" value={ps.total_portfolios} />
        <StatCard label="Total Debtors" value={ps.total_debtors.toLocaleString()} />
        <StatCard
          label="Nominal Debt"
          value={`${ps.total_nominal_debt.toLocaleString()} UAH`}
        />
        <StatCard
          label="Recovered"
          value={`${ps.total_recovered.toLocaleString()} UAH`}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Recent Decisions" value={data.recent_decisions_count} />
        <StatCard label="Pending Enforcement" value={data.pending_enforcement_count} />
        <StatCard
          label="Bankruptcy Alerts"
          value={data.bankruptcy_alerts_count}
          alert={data.bankruptcy_alerts_count > 0}
        />
        <StatCard
          label="Needs Review"
          value={data.needs_review_count}
          alert={data.needs_review_count > 0}
        />
      </div>
    </div>
  );
}
