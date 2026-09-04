/**
 * BusinessSwitcher.jsx — Production-Ready Multi-Business Switcher & Status Indicator Component.
 * Supports seamless enterprise switching, real-time data-driven status indicators (Healthy / Reconsideration / Critical),
 * and rapid "Create New Business" navigation.
 */

import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useBusiness } from "../context/BusinessContext";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import {
  Building2,
  ChevronDown,
  Check,
  PlusCircle,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Sparkles,
  MapPin,
  Coins,
  Layers,
} from "lucide-react";

export function BusinessStatusPill({ status, showReason = false, size = "sm" }) {
  const code = status?.code || "draft";
  const label = status?.label || "Draft";
  const reason = status?.reason || "";

  const sizeClasses = size === "xs" 
    ? "text-[9px] px-2 py-0.5" 
    : size === "lg" 
    ? "text-xs px-3 py-1 font-bold" 
    : "text-[10px] px-2.5 py-0.5 font-bold";

  let badgeStyle = "bg-slate-50 text-slate-700 border-slate-200";
  let IconComponent = Clock;
  let iconColor = "text-slate-500";

  if (code === "healthy") {
    badgeStyle = "bg-emerald-50 text-emerald-900 border-emerald-300 shadow-xs";
    IconComponent = CheckCircle2;
    iconColor = "text-emerald-600";
  } else if (code === "reconsideration") {
    badgeStyle = "bg-amber-50 text-amber-950 border-amber-300 shadow-xs";
    IconComponent = AlertTriangle;
    iconColor = "text-amber-600";
  } else if (code === "critical") {
    badgeStyle = "bg-rose-50 text-rose-950 border-rose-300 shadow-xs";
    IconComponent = ShieldAlert;
    iconColor = "text-rose-600";
  }

  // Use compact text for xs navbar pill to avoid overflowing
  const displayLabel = size === "xs" 
    ? (code === "healthy" ? "Bank Viable" : (code === "critical" ? "Critical Risk" : "Reconsider"))
    : label;

  return (
    <div className="inline-flex flex-col items-start gap-0.5 shrink-0">
      <span
        title={reason || label}
        className={`inline-flex items-center gap-1.5 rounded-full border ${badgeStyle} ${sizeClasses} whitespace-nowrap shrink-0 transition-all`}
      >
        <IconComponent className={`w-3 h-3 ${iconColor} shrink-0`} />
        <span className="font-semibold tracking-tight whitespace-nowrap">{displayLabel}</span>
      </span>
      {showReason && reason && (
        <span className="text-[10px] text-slate-500 line-clamp-1 mt-0.5 font-medium">
          {reason}
        </span>
      )}
    </div>
  );
}

export function BusinessSwitcher({ compact = false }) {
  const { businesses, activeBusiness, switchBusiness } = useBusiness();
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCreateNew = () => {
    setIsOpen(false);
    navigate("/wizard");
  };

  const handleSelectBusiness = async (biz) => {
    setIsOpen(false);
    await switchBusiness(biz.project_id);
    navigate("/dashboard");
  };

  if (!isAuthenticated) {
    return null;
  }

  // If user has no businesses yet, show quick create button
  if (!businesses || businesses.length === 0) {
    return (
      <button
        type="button"
        onClick={handleCreateNew}
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gradient-to-r from-sovereign-800 to-sky-700 hover:from-sovereign-700 hover:to-sky-600 text-white text-xs font-bold shadow-sm transition"
      >
        <PlusCircle className="w-4 h-4 text-sky-200" />
        <span>+ Register Enterprise</span>
      </button>
    );
  }

  const currentStatus = activeBusiness?.business_status || {
    code: "draft",
    label: "Draft Assessment",
  };

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      {/* Switcher Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className={`group inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 shadow-subtle text-xs text-slate-800 transition-all max-h-11 ${compact ? "w-full justify-between" : ""}`}
        aria-expanded={isOpen}
      >
        <div className="w-7 h-7 rounded-lg bg-sovereign-50 border border-sovereign-200 flex items-center justify-center text-sovereign-800 shrink-0">
          <Building2 className="w-3.5 h-3.5 text-sovereign-700" />
        </div>

        <div className="text-left min-w-0 max-w-[120px] sm:max-w-[150px] md:max-w-[180px] lg:max-w-[210px] truncate">
          <div className="font-outfit font-extrabold text-xs text-slate-900 truncate leading-tight">
            {activeBusiness?.business_name || "Select Business"}
          </div>
          <div className="text-[10px] text-slate-500 font-medium capitalize truncate">
            {activeBusiness?.sector || "Enterprise"} • {activeBusiness?.district_name || "Location"}
          </div>
        </div>

        {/* Real Status Badge */}
        {!compact && (
          <div className="hidden sm:flex shrink-0 ml-1">
            <BusinessStatusPill status={currentStatus} size="xs" />
          </div>
        )}

        <ChevronDown className={`w-3.5 h-3.5 shrink-0 text-slate-400 group-hover:text-slate-600 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 sm:right-0 sm:left-auto mt-2 w-80 sm:w-96 rounded-2xl bg-white border border-slate-200 shadow-card-elevated z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
          {/* Header */}
          <div className="p-3.5 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-sovereign-700" />
              <span className="text-xs font-bold font-outfit text-slate-800 uppercase tracking-wider">
              {t('yourEnterprises')} ({businesses.length})
              </span>
            </div>
            <span className="text-[10px] font-semibold text-slate-500 bg-white border border-slate-200 px-2 py-0.5 rounded-full">
              {t('dashboard')}
            </span>
          </div>

          {/* List of Registered Businesses */}
          <div className="max-h-72 overflow-y-auto p-2 space-y-1 divide-y divide-slate-100/60">
            {businesses.map((biz) => {
              const isActive = biz.project_id === activeBusiness?.project_id;
              const status = biz.business_status || { code: "draft", label: "Draft" };
              const outlayLakhs = (biz.investment_amount / 100000).toFixed(2);

              return (
                <button
                  key={biz.project_id}
                  type="button"
                  onClick={() => handleSelectBusiness(biz)}
                  className={`w-full text-left p-3 rounded-xl transition-all flex items-start justify-between gap-2.5 ${
                    isActive
                      ? "bg-sovereign-50/80 border border-sovereign-200 shadow-xs"
                      : "hover:bg-slate-50 border border-transparent"
                  }`}
                >
                  <div className="min-w-0 flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`font-outfit font-extrabold text-xs truncate ${isActive ? "text-sovereign-950" : "text-slate-900"}`}>
                        {biz.business_name}
                      </span>
                      <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200 shrink-0">
                        {biz.sector}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px] text-slate-500 font-medium">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-slate-400" />
                        <span>{biz.village_name !== "N/A" ? `${biz.village_name}, ` : ""}{biz.district_name}</span>
                      </span>
                      <span className="flex items-center gap-1 font-mono">
                        <Coins className="w-3 h-3 text-slate-400" />
                        <span>₹{outlayLakhs} L Outlay</span>
                      </span>
                    </div>

                    {/* Status Pill with Grounded Reason */}
                    <div className="pt-0.5">
                      <BusinessStatusPill status={status} size="xs" showReason={true} />
                    </div>
                  </div>

                  {isActive && (
                    <div className="w-5 h-5 rounded-full bg-sovereign-800 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                      <Check className="w-3 h-3 stroke-[3]" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Footer Action: + Create New Business */}
          <div className="p-3 bg-slate-50 border-t border-slate-100">
            <button
              type="button"
              onClick={handleCreateNew}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-gradient-to-r from-sovereign-800 to-sky-700 hover:from-sovereign-700 hover:to-sky-600 text-white font-bold text-xs shadow-md shadow-sovereign-900/15 border border-sky-400/20 transition group"
            >
              <PlusCircle className="w-4 h-4 text-sky-200 group-hover:rotate-90 transition-transform" />
              <span>+ {t('createEnterprise')}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default BusinessSwitcher;
