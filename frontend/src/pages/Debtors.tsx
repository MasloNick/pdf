import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/services/api";
import type { Debtor } from "@/types/models";

export default function Debtors() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["debtors", page, search],
    queryFn: () =>
      api.get("/debtors/", { params: { page, page_size: 50, search: search || undefined } }).then((r) => r.data),
  });

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Боржники</h1>
      <input
        type="text"
        placeholder="Пошук за ПІБ, ІПН, ЄДРПОУ..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        className="mb-4 p-2 border rounded w-96"
      />
      {isLoading ? (
        <div>Завантаження...</div>
      ) : (
        <>
          <p className="text-sm text-gray-500 mb-2">Знайдено: {data?.total ?? 0}</p>
          <table className="w-full bg-white rounded-lg shadow">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-3 text-left">ПІБ / Назва</th>
                <th className="p-3 text-left">ІПН / ЄДРПОУ</th>
                <th className="p-3 text-left">Тип</th>
                <th className="p-3 text-left">Статус</th>
                <th className="p-3 text-left">Банкрут</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items ?? []).map((d: Debtor) => (
                <tr key={d.id} className="border-t hover:bg-gray-50">
                  <td className="p-3">
                    {d.debtor_type === "individual"
                      ? `${d.last_name ?? ""} ${d.first_name ?? ""} ${d.patronymic ?? ""}`.trim()
                      : d.full_name}
                  </td>
                  <td className="p-3">{d.ipn || d.edrpou || "—"}</td>
                  <td className="p-3">{d.debtor_type === "individual" ? "ФО" : "ЮО"}</td>
                  <td className="p-3">{d.status}</td>
                  <td className="p-3">{d.is_bankrupt ? "Так" : "Ні"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-4 flex gap-2">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border rounded">
              Назад
            </button>
            <span className="px-3 py-1">Сторінка {page}</span>
            <button onClick={() => setPage((p) => p + 1)} className="px-3 py-1 border rounded">
              Далі
            </button>
          </div>
        </>
      )}
    </div>
  );
}
