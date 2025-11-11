"use client";
import React from "react";

interface AuthCardProps {
  title: string;
  children: React.ReactNode;
}

export default function AuthCard({ title, children }: AuthCardProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f0f0f]">
      <div className="bg-[#1c1c1c] shadow-xl rounded-2xl p-8 w-[400px] text-white">
        <h2 className="text-2xl font-semibold text-center mb-6">{title}</h2>
        {children}
      </div>
    </div>
  );
}
