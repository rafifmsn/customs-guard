import React from "react";
import Link from "next/link";
import Image from "next/image";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#121212] px-6 text-center text-[#F8FAFC]">
      <div className="mx-auto max-w-md">
        <div className="rounded-2xl border border-[#2A2A35] bg-[#1A1A22] p-8 shadow-sm">
          <div className="font-mono text-xs font-semibold uppercase tracking-wider text-[#A78BFA]">
            Error 404
          </div>
          <h1 className="mt-2 font-display text-2xl font-bold tracking-tight text-[#F8FAFC] sm:text-3xl">
            Manifest Not Found
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-[#94A3B8]">
            The trade compliance route or shipment documentation you requested
            does not exist, has expired, or has been relocated.
          </p>

          <div className="mt-6 flex justify-center">
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-full bg-[#A78BFA] px-6 py-2.5 text-xs font-semibold text-[#0B0B0F] transition hover:bg-[#C4B5FD]"
            >
              Return to Homepage
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
