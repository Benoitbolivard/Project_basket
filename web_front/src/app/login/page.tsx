"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPass] = useState("");
  const router = useRouter();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${api}/auth/jwt/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password }),
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      router.push("/club/dashboard");
    } else {
      alert("Login failed");
    }
  }

  return (
    <main className="flex flex-col items-center p-8">
      <h1 className="text-2xl font-bold mb-4">Club login</h1>
      <form onSubmit={handleLogin} className="space-y-4">
        <input className="border p-2" placeholder="email" value={email} onChange={e => setEmail(e.target.value)} />
        <input className="border p-2" placeholder="password" type="password" value={password} onChange={e => setPass(e.target.value)} />
        <button className="bg-blue-600 text-white rounded px-4 py-2">Login</button>
      </form>
    </main>
  );
}