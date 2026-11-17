import LoanForm from "./components/LoanForm";
import { useEffect, useState } from "react";

function App() {
  const [stats, setStats] = useState({
    total: 0,
    lowRisk: 0,
    highRisk: 0,
  });

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/v1/predictions")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch predictions");
        }
        return response.json();
      })
      .then((data) => {
        const predictions = data.predictions || [];

        setStats({
          total: predictions.length,
          lowRisk: predictions.filter((item) => item.risk === "Low Risk")
            .length,
          highRisk: predictions.filter((item) => item.risk === "High Risk")
            .length,
        });
      })
      .catch((error) => {
        console.error("Error fetching predictions:", error);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white p-6 hidden md:block">
        <h1 className="text-xl font-bold mb-10">
          Loan<span className="text-blue-400">AI</span>
        </h1>

        <nav className="space-y-3">
          <div className="bg-blue-600 p-3 rounded-lg">Dashboard</div>

          <div className="p-3 text-slate-300">Loan Assessment</div>

          <div className="p-3 text-slate-300">Prediction History</div>

          <div className="p-3 text-slate-300">Settings</div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 md:p-10">
        {/* Header */}
        <header className="flex justify-between items-center mb-10">
          <div>
            <h2 className="text-2xl font-bold text-slate-800">Dashboard</h2>

            <p className="text-slate-500 mt-1">
              AI-Powered Loan Risk Assessment System
            </p>
          </div>

          <div className="bg-white rounded-full px-4 py-2 shadow-sm">Admin</div>
        </header>

        {/* Statistics */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-slate-500 text-sm">Total Predictions</p>

            <h3 className="text-3xl font-bold mt-3 text-slate-800">
              {stats.total}
            </h3>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-slate-500 text-sm">Low Risk</p>

            <h3 className="text-3xl font-bold mt-3 text-green-600">
              {stats.lowRisk}
            </h3>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-slate-500 text-sm">High Risk</p>

            <h3 className="text-3xl font-bold mt-3 text-red-600">
              {stats.highRisk}
            </h3>
          </div>
        </section>

        {/* Loan Assessment Form */}
        <LoanForm />
      </main>
    </div>
  );
}

export default App;
