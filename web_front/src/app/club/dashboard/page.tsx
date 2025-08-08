"use client";
import { useEffect, useState } from "react";

type Player = { id: string; name: string; number: number | null };
type JobStatus = { status: string; result?: any };

export default function Dashboard() {
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [players, setPlayers] = useState<Player[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("idle");

  function getToken() {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token");
  }

  async function fetchPlayers() {
    const token = getToken();
    const res = await fetch(`${api}/club/players`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setPlayers(await res.json());
    else window.location.href = "/login";
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    const token = getToken();
    const form = new FormData();
    form.append("file", file);
    form.append("match_id", "demo-match");
    const res = await fetch(`${api}/upload/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (res.ok) {
      const data = await res.json();
      setJobId(data.job_id);
      setJobStatus("queued");
    } else {
      alert("Upload failed");
    }
  }

  useEffect(() => {
    let timer: any;
    async function poll() {
      if (!jobId) return;
      const res = await fetch(`${api}/jobs/${jobId}`);
      const data: JobStatus = await res.json();
      setJobStatus(data.status);
      if (["finished", "failed", "unknown"].includes(data.status)) {
        clearInterval(timer);
        fetchPlayers();
      }
    }
    if (jobId) {
      timer = setInterval(poll, 3000);
      poll();
    }
    return () => clearInterval(timer);
  }, [api, jobId]);

  useEffect(() => {
    fetchPlayers();
  }, []);

  return (
    <main className="p-8 space-y-8">
      <section>
        <h1 className="text-2xl font-bold mb-4">Club Dashboard</h1>
        <ul className="space-y-2">
          {players.map(p => (
            <li key={p.id} className="border rounded p-2">
              {p.name} {p.number && <span className="text-sm text-gray-500">#{p.number}</span>}
            </li>
          ))}
        </ul>
      </section>

      <section className="border-t pt-6">
        <h2 className="text-xl font-semibold mb-2">Upload vidéo</h2>
        <form onSubmit={handleUpload} className="flex items-center gap-3">
          <input type="file" accept="video/*" onChange={e => setFile(e.target.files?.[0] || null)} />
          <button className="bg-blue-600 text-white rounded px-4 py-2">Envoyer</button>
        </form>
        {jobId && (
          <p className="mt-3 text-sm text-gray-700">
            Job <code>{jobId}</code> — statut : <strong>{jobStatus}</strong>
          </p>
        )}
      </section>
    </main>
  );
}