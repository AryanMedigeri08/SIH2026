import React from 'react';

export function CardSkeleton({ className = '', height = 'h-48' }) {
  return (
    <div className={`glass-panel p-6 bg-white border border-slate-200 shadow-card ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="space-y-2 w-2/3">
          <div className="h-3 w-28 bg-slate-200 rounded skeleton-shimmer" />
          <div className="h-5 w-48 bg-slate-200 rounded skeleton-shimmer" />
        </div>
        <div className="h-6 w-20 bg-slate-200 rounded-full skeleton-shimmer" />
      </div>
      <div className={`${height} w-full bg-slate-100 rounded-xl skeleton-shimmer`} />
    </div>
  );
}

export function OverviewSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Enterprise Title Header Skeleton */}
      <div className="glass-panel p-6 bg-white border border-slate-200 shadow-card flex flex-col md:flex-row justify-between gap-4">
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <div className="h-7 w-56 bg-slate-200 rounded-lg skeleton-shimmer" />
            <div className="h-5 w-20 bg-slate-200 rounded-full skeleton-shimmer" />
          </div>
          <div className="h-4 w-72 bg-slate-200 rounded skeleton-shimmer" />
        </div>
        <div className="h-10 w-44 bg-slate-200 rounded-xl skeleton-shimmer" />
      </div>

      {/* Hero Viability Gauge Skeleton */}
      <div className="glass-panel p-6 bg-white border border-slate-200 shadow-card space-y-4">
        <div className="flex justify-between items-center">
          <div className="h-5 w-48 bg-slate-200 rounded skeleton-shimmer" />
          <div className="h-6 w-28 bg-slate-200 rounded-full skeleton-shimmer" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="h-28 bg-slate-100 rounded-xl skeleton-shimmer" />
          <div className="h-28 bg-slate-100 rounded-xl skeleton-shimmer" />
          <div className="h-28 bg-slate-100 rounded-xl skeleton-shimmer" />
          <div className="h-28 bg-slate-100 rounded-xl skeleton-shimmer" />
        </div>
      </div>

      {/* Teaser Section Cards Skeleton */}
      <div className="space-y-3">
        <div className="h-4 w-40 bg-slate-200 rounded skeleton-shimmer" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className="glass-panel p-4 bg-white border border-slate-200 shadow-card space-y-2.5">
              <div className="flex justify-between">
                <div className="h-4 w-28 bg-slate-200 rounded skeleton-shimmer" />
                <div className="h-4 w-4 bg-slate-200 rounded skeleton-shimmer" />
              </div>
              <div className="h-6 w-32 bg-slate-200 rounded skeleton-shimmer" />
              <div className="h-3 w-full bg-slate-100 rounded skeleton-shimmer" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ViabilitySkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="glass-panel p-6 bg-white border border-slate-200 shadow-card h-44 space-y-3">
        <div className="h-5 w-48 bg-slate-200 rounded skeleton-shimmer" />
        <div className="h-8 w-64 bg-slate-200 rounded skeleton-shimmer" />
        <div className="h-4 w-full bg-slate-100 rounded skeleton-shimmer" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CardSkeleton height="h-72" />
        <CardSkeleton height="h-72" />
      </div>
    </div>
  );
}

export function MarketSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-4 bg-white border border-slate-200 rounded-xl shadow-card space-y-2">
            <div className="h-3 w-20 bg-slate-200 rounded skeleton-shimmer" />
            <div className="h-6 w-28 bg-slate-200 rounded skeleton-shimmer" />
          </div>
        ))}
      </div>
      <CardSkeleton height="h-80" />
    </div>
  );
}

export function SchemesSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <CardSkeleton height="h-64" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="glass-panel p-5 bg-white border border-slate-200 shadow-card space-y-3">
            <div className="flex justify-between">
              <div className="h-5 w-24 bg-slate-200 rounded skeleton-shimmer" />
              <div className="h-4 w-16 bg-slate-200 rounded-full skeleton-shimmer" />
            </div>
            <div className="h-4 w-40 bg-slate-200 rounded skeleton-shimmer" />
            <div className="h-16 bg-slate-100 rounded-lg skeleton-shimmer" />
            <div className="h-8 bg-slate-100 rounded-lg skeleton-shimmer" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function FinancialsSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CardSkeleton height="h-64" />
        <CardSkeleton height="h-64" />
      </div>
      <CardSkeleton height="h-80" />
    </div>
  );
}

export function RiskSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="glass-panel p-6 bg-white border border-slate-200 shadow-card h-64 skeleton-shimmer" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="glass-panel p-4 bg-white border border-slate-200 shadow-card space-y-2">
            <div className="flex justify-between">
              <div className="h-4 w-32 bg-slate-200 rounded skeleton-shimmer" />
              <div className="h-4 w-12 bg-slate-200 rounded skeleton-shimmer" />
            </div>
            <div className="h-3 w-full bg-slate-100 rounded skeleton-shimmer" />
            <div className="h-12 bg-slate-100 rounded-lg skeleton-shimmer" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function SwotSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in duration-300">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="glass-panel p-6 bg-white border border-slate-200 shadow-card space-y-3">
          <div className="h-5 w-36 bg-slate-200 rounded skeleton-shimmer" />
          <div className="space-y-2">
            <div className="h-3 w-full bg-slate-100 rounded skeleton-shimmer" />
            <div className="h-3 w-5/6 bg-slate-100 rounded skeleton-shimmer" />
            <div className="h-3 w-4/6 bg-slate-100 rounded skeleton-shimmer" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DprSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="glass-panel p-6 bg-white border border-slate-200 shadow-card h-44 skeleton-shimmer" />
      <div className="glass-panel p-8 bg-white border border-slate-200 shadow-card min-h-[400px] space-y-4">
        <div className="h-6 w-64 bg-slate-200 rounded skeleton-shimmer mx-auto" />
        <div className="h-4 w-full bg-slate-100 rounded skeleton-shimmer" />
        <div className="h-4 w-full bg-slate-100 rounded skeleton-shimmer" />
        <div className="h-4 w-3/4 bg-slate-100 rounded skeleton-shimmer" />
        <div className="h-40 bg-slate-100 rounded-xl skeleton-shimmer" />
      </div>
    </div>
  );
}
