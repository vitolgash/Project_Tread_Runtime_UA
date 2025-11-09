import React, { useEffect, useState } from "react";

export default function App() {
  const [law, setLaw] = useState(null);
  const [sanctions, setSanctions] = useState(null);

  useEffect(() => {
    Promise.all([
      fetch("/ukraine_law_runtime_status.json").then(r => r.json()),
      fetch("/sanctions_status.json").then(r => r.json())
    ]).then(([lawData, sanctionsData]) => {
      setLaw(lawData);
      setSanctions(sanctionsData);
    }).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8 font-mono">
      <h1 className="text-3xl font-bold mb-6">Project Tread — Ukraine Law Runtime Dashboard</h1>
      {!law || !sanctions ? (
        <p className="text-gray-400">Loading data...</p>
      ) : (
        <>
          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-2">📜 Legislative Status</h2>
            <div className="grid md:grid-cols-3 gap-4">
              <Card title="Constitution" value={law.constitution_last} />
              <Card title="Criminal Code" value={law.criminal_code_last} />
              <Card title="Civil Code" value={law.civil_code_last} />
            </div>
            <p className="mt-3 text-sm text-gray-400">
              API NACP: {law.nacp_api_ok ? "✅ Online" : "❌ Offline"}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-2">🌍 Sanctions Feeds</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <Feed title="🇬🇧 UK OFSI" items={sanctions.ofsi_titles} />
              <Feed title="🇺🇸 US OFAC" items={sanctions.ofac_titles} />
            </div>
          </section>

          <footer className="mt-10 text-sm text-gray-500">
            Updated: {law.timestamp} · Project Tread Runtime UA
          </footer>
        </>
      )}
    </div>
  );
}

function Card({ title, value }) {
  return (
    <div className="p-4 rounded-xl bg-gray-800 border border-gray-700">
      <p className="text-lg font-semibold mb-1">{title}</p>
      <p className="text-green-400">{value || "No data"}</p>
    </div>
  );
}

function Feed({ title, items }) {
  return (
    <div className="p-4 rounded-xl bg-gray-800 border border-gray-700">
      <p className="text-lg font-semibold mb-2">{title}</p>
      <ul className="list-disc pl-5 space-y-1 text-sm">
        {items && items.length ? items.map((i, idx) => <li key={idx}>{i}</li>) : <li>No entries</li>}
      </ul>
    </div>
  );
}
