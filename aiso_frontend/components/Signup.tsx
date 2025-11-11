"use client";
import React, { useState } from "react";
import AuthCard from "./AuthCard";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${BASE_URL}/api/users/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      if (!res.ok) throw new Error("Signup failed");
      alert("Account created! Please log in.");
      window.location.href = "/login";
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleSignup() {
    window.location.href = `${BASE_URL}/api/auth/google`; // backend OAuth redirect
  }

  return (
    <AuthCard title="Create Your Account">
      <form onSubmit={handleSignup} className="space-y-4">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Full name"
          className="w-full p-3 rounded-md bg-[#2a2a2a] text-white border border-gray-700 focus:border-[#8D0101]"
          required
        />
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full p-3 rounded-md bg-[#2a2a2a] text-white border border-gray-700 focus:border-[#8D0101]"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full p-3 rounded-md bg-[#2a2a2a] text-white border border-gray-700 focus:border-[#8D0101]"
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[#8D0101] hover:bg-[#a81212] text-white p-3 rounded-md transition-colors"
        >
          {loading ? "Signing up..." : "Sign up"}
        </button>

        <button
          type="button"
          onClick={handleGoogleSignup}
          className="w-full bg-white text-black p-3 rounded-md hover:bg-gray-200 flex justify-center gap-2"
        >
          <img src="/google.svg" alt="Google" className="w-5 h-5" />
          Sign up with Google
        </button>

        {error && <div className="text-red-500 text-sm mt-2">{error}</div>}
      </form>

      <div className="text-gray-400 text-sm text-center mt-6">
        Already have an account?{" "}
        <a href="/login" className="text-[#8D0101] hover:underline">
          Login
        </a>
      </div>
    </AuthCard>
  );
}
