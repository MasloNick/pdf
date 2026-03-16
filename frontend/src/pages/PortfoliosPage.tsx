import { useQuery } from "@tanstack/react-query";
import { getPortfolios } from "../api/endpoints";
import type { Portfolio } from "../types";

export default function PortfoliosPage() {
  const { data, isLoading } = useQuery<Portfolio[]>({
    queryKey: ["portfolios"],
    queryFn: () => getPortfolios().then((r) => r.data),
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Portfolios</h2>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          + Add Portfolio
        </button>
      </div>

      {isLoading ? (
        <div className="text-gray-400">Loading...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Seller</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Purchase Date</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Nominal Debt</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debtors</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-6 py-4 font-medium">{p.name}</td>
                  <td className="px-6 py-4 text-gray-600">{p.seller_name}</td>
                  <td className="px-6 py-4 text-gray-600">{p.purchase_date}</td>
                  <td className="px-6 py-4 text-right">{p.total_nominal_debt.toLocaleString()} {p.currency}</td>
                  <td className="px-6 py-4 text-right">{p.debtor_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
