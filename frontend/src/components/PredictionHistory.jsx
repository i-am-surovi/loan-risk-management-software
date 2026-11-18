import { useEffect, useState } from "react";

function PredictionHistory() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/v1/predictions",
        );

        if (!response.ok) {
          throw new Error("Failed to load prediction history.");
        }

        const data = await response.json();
        setPredictions(data.predictions || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPredictions();
  }, []);

  return (
    <section className="bg-white p-8 rounded-xl shadow-sm">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">
        Prediction History
      </h2>

      <p className="text-slate-500 mb-6">
        View all previously assessed loan applications.
      </p>

      {loading && <p>Loading prediction history...</p>}

      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="p-3">ID</th>
                <th className="p-3">Age</th>
                <th className="p-3">Income</th>
                <th className="p-3">Loan Amount</th>
                <th className="p-3">Credit Score</th>
                <th className="p-3">Default Probability</th>
                <th className="p-3">Risk</th>
                <th className="p-3">Date</th>
              </tr>
            </thead>

            <tbody>
              {predictions.map((item) => (
                <tr key={item.id} className="border-b hover:bg-slate-50">
                  <td className="p-3">{item.id}</td>
                  <td className="p-3">{item.age}</td>
                  <td className="p-3">৳{item.income.toLocaleString()}</td>
                  <td className="p-3">৳{item.loan_amount.toLocaleString()}</td>
                  <td className="p-3">{item.credit_score}</td>
                  <td className="p-3">
                    {(item.default_probability * 100).toFixed(2)}%
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        item.risk === "High Risk"
                          ? "bg-red-100 text-red-700"
                          : "bg-green-100 text-green-700"
                      }`}
                    >
                      {item.risk}
                    </span>
                  </td>
                  <td className="p-3 whitespace-nowrap">
                    {item.created_at
                      ? new Date(item.created_at).toLocaleString()
                      : "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {predictions.length === 0 && (
            <p className="text-center text-slate-500 py-8">
              No prediction records found.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

export default PredictionHistory;
