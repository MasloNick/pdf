import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import type { Portfolio } from "@/types/models";

export default function Portfolios() {
  const { data: portfolios = [], isLoading } = useQuery<Portfolio[]>({
    queryKey: ["portfolios"],
    queryFn: () => api.get("/portfolios/").then((r) => r.data),
  });

  if (isLoading) return <div className="p-8">Завантаження...</div>;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Портфелі NPL</h1>
      <table className="w-full bg-white rounded-lg shadow">
        <thead className="bg-gray-50">
          <tr>
            <th className="p-3 text-left">Назва</th>
            <th className="p-3 text-left">Продавець</th>
            <th className="p-3 text-right">Ціна купівлі</th>
            <th className="p-3 text-right">Номінал</th>
            <th className="p-3 text-left">Дата</th>
          </tr>
        </thead>
        <tbody>
          {portfolios.map((p) => (
            <tr key={p.id} className="border-t hover:bg-gray-50">
              <td className="p-3">{p.name}</td>
              <td className="p-3">{p.seller_name}</td>
              <td className="p-3 text-right">{Number(p.purchase_price).toLocaleString("uk-UA")} {p.currency}</td>
              <td className="p-3 text-right">{Number(p.total_nominal_value).toLocaleString("uk-UA")} {p.currency}</td>
              <td className="p-3">{p.purchase_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
