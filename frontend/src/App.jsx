import { useCallback, useEffect, useState } from "react";
import LoanForm from "./components/LoanForm";
import PredictionHistory from "./components/PredictionHistory";

function App() {
  const [activePage, setActivePage] = useState("Dashboard");

  const [stats, setStats] = useState({
    total: 0,
    lowRisk: 0,
    highRisk: 0,
  });

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/predictions");

      if (!response.ok) {
        throw new Error("Failed to fetch predictions");
      }

      const data = await response.json();
      const predictions = data.predictions || [];

      setStats({
        total: predictions.length,
        lowRisk: predictions.filter((item) => item.risk === "Low Risk").length,
        highRisk: predictions.filter((item) => item.risk === "High Risk")
          .length,
      });
    } catch (error) {
      console.error("Error fetching predictions:", error);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const menuItems = [
    "Dashboard",
    "Loan Assessment",
    "Prediction History",
    "Settings",
  ];

  return (
    <div className="min-h-screen bg-slate-100 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white p-6 hidden md:block">
        <h1 className="text-xl font-bold mb-10">
          Loan<span className="text-blue-400">AI</span>
        </h1>

        <nav className="space-y-3">
          {menuItems.map((item) => (
            <button
              key={item}
              onClick={() => setActivePage(item)}
              className={`w-full text-left p-3 rounded-lg transition ${
                activePage === item
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              {item}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 md:p-10">
        <header className="flex justify-between items-center mb-10">
          <div>
            <h2 className="text-2xl font-bold text-slate-800">{activePage}</h2>
            <p className="text-slate-500 mt-1">
              AI-Powered Loan Risk Assessment System
            </p>
          </div>

          <div className="bg-white rounded-full px-4 py-2 shadow-sm">Admin</div>
        </header>

        {/* Dashboard */}
        {activePage === "Dashboard" && (
          <>
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
          </>
        )}

        {/* Loan Assessment */}
        {activePage === "Loan Assessment" && (
          <LoanForm onPredictionSuccess={fetchStats} />
        )}

        {/* Prediction History */}
        {activePage === "Prediction History" && <PredictionHistory />}

        {/* Settings */}
        {activePage === "Settings" && (
          <div className="bg-white p-8 rounded-xl shadow-sm">
            <h3 className="text-xl font-bold text-slate-800">Settings</h3>
            <p className="text-slate-500 mt-2">
              System settings will be available here.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
