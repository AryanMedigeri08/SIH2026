/**
 * BusinessContext.jsx — Unified Multi-Business State Management & Persistence Context.
 * Manages user-owned businesses, active business selection, persistent restore across sessions,
 * status indicators (Healthy / Reconsideration / Critical), and business switching.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useAuth } from "./AuthContext";
import { projectsApi, generateFeasibility } from "../services/api";
import { PITCH_CASES } from "../data/pitchCases";

const BusinessContext = createContext(null);
const ACTIVE_BIZ_KEY_PREFIX = "udyam_saathi_active_biz_";

export const BusinessProvider = ({ children }) => {
  const { token, isAuthenticated, userProfile, isDemoMode } = useAuth();

  const [businesses, setBusinesses] = useState([]);
  const [activeBusiness, setActiveBusiness] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [dprData, setDprData] = useState(null);
  const [loadingBusinesses, setLoadingBusinesses] = useState(false);
  const [businessError, setBusinessError] = useState(null);

  // Helper to get active storage key per user
  const getStorageKey = useCallback(() => {
    const uid = userProfile?.firebase_uid || "guest";
    return `${ACTIVE_BIZ_KEY_PREFIX}${uid}`;
  }, [userProfile?.firebase_uid]);

  // Load user's persistent businesses from backend API
  const loadUserBusinesses = useCallback(async () => {
    if (!token && !isAuthenticated) {
      setBusinesses([]);
      setActiveBusiness(null);
      return [];
    }

    setLoadingBusinesses(true);
    setBusinessError(null);
    try {
      const list = await projectsApi.listProjects(token);
      setBusinesses(list || []);

      if (list && list.length > 0) {
        // Restore previously active business from localStorage or select the latest
        const savedActiveId = localStorage.getItem(getStorageKey());
        const matched = list.find((b) => b.project_id === savedActiveId);
        const selected = matched || list[0];

        setActiveBusiness(selected);
        localStorage.setItem(getStorageKey(), selected.project_id);

        // Restore analysis and DPR payload if available
        if (selected.analysis_result && selected.analysis_result.report) {
          setReportData(selected.analysis_result.report);
          setDprData(selected.analysis_result.dpr || null);
        } else if (selected.status === "draft") {
          // If draft, run analysis to populate data
          try {
            const analyzed = await projectsApi.analyzeProject(token, selected.project_id);
            setActiveBusiness(analyzed);
            if (analyzed.analysis_result?.report) {
              setReportData(analyzed.analysis_result.report);
              setDprData(analyzed.analysis_result.dpr || null);
            }
          } catch (analyzeErr) {
            console.warn("Could not auto-analyze draft project:", analyzeErr);
          }
        }
      } else {
        // User has 0 businesses
        setActiveBusiness(null);
        setReportData(null);
        setDprData(null);
      }
      return list;
    } catch (err) {
      console.error("Failed to load user businesses:", err);
      setBusinessError(err.message || "Failed to load businesses.");
      return [];
    } finally {
      setLoadingBusinesses(false);
    }
  }, [token, isAuthenticated, getStorageKey]);

  // Trigger business load on auth change
  useEffect(() => {
    if (isAuthenticated && token) {
      loadUserBusinesses();
    } else {
      // Unauthenticated fallback: start with empty or demo state
      setBusinesses([]);
      setActiveBusiness(null);
    }
  }, [isAuthenticated, token, loadUserBusinesses]);

  // Switch Active Business
  const switchBusiness = useCallback(
    async (businessOrId) => {
      const bizId = typeof businessOrId === "string" ? businessOrId : businessOrId.project_id;
      let target = businesses.find((b) => b.project_id === bizId);

      if (!target && token) {
        try {
          target = await projectsApi.getProject(token, bizId);
        } catch (e) {
          console.error("Failed to fetch target business:", e);
          return false;
        }
      }

      if (!target) return false;

      setActiveBusiness(target);
      localStorage.setItem(getStorageKey(), target.project_id);

      if (target.analysis_result && target.analysis_result.report) {
        setReportData(target.analysis_result.report);
        setDprData(target.analysis_result.dpr || null);
      } else if (token) {
        try {
          const analyzed = await projectsApi.analyzeProject(token, target.project_id);
          setActiveBusiness(analyzed);
          if (analyzed.analysis_result?.report) {
            setReportData(analyzed.analysis_result.report);
            setDprData(analyzed.analysis_result.dpr || null);
          }
        } catch (e) {
          console.error("Failed to analyze switched business:", e);
        }
      }
      return true;
    },
    [businesses, token, getStorageKey]
  );

  // Create New Business and Persist
  const createAndSaveBusiness = useCallback(
    async (formData) => {
      const projectPayload = {
        business_name: formData.enterprise_name,
        business_category: formData.business_category || "manufacturing",
        sector: formData.sector || "general",
        investment_amount: Number(formData.project_cost),
        annual_turnover_estimate: Number(formData.annual_turnover_estimate),
        state_name: formData.state_name,
        district_name: formData.district_name,
        block_name: formData.block_name || "N/A",
        village_name: formData.village_name || "N/A",
        promoter_name: formData.promoter_name || userProfile?.name || "Enterprise Promoter",
        promoter_category: formData.promoter_category || "general",
        gender: formData.gender || "Unspecified",
        is_rural: formData.is_rural ?? true,
        tenure_years: Number(formData.tenure_years || 5.0),
        moratorium_months: Number(formData.moratorium_months || 6),
        language: formData.language || "en",
        additional_business_details: formData.additional_business_details || null,
        monthly_net_operating_income_override: formData.monthly_net_operating_income_override
          ? Number(formData.monthly_net_operating_income_override)
          : null,
      };

      if (token) {
        // Authenticated creation and analysis
        const createdProject = await projectsApi.createAndAnalyze(token, projectPayload);
        setBusinesses((prev) => [createdProject, ...prev.filter((p) => p.project_id !== createdProject.project_id)]);
        setActiveBusiness(createdProject);
        localStorage.setItem(getStorageKey(), createdProject.project_id);

        if (createdProject.analysis_result?.report) {
          setReportData(createdProject.analysis_result.report);
          setDprData(createdProject.analysis_result.dpr || null);
        }
        return createdProject;
      } else {
        // Fallback for demo unauthenticated flow
        const rep = await generateFeasibility(formData);
        setReportData(rep);
        return {
          project_id: rep.report_id || `demo_${Date.now()}`,
          business_name: formData.enterprise_name,
          sector: formData.sector,
          status: "analyzed",
          analysis_result: { report: rep },
        };
      }
    },
    [token, userProfile, getStorageKey]
  );

  // Delete Business
  const deleteBusiness = useCallback(
    async (projectId) => {
      if (!token) return false;
      try {
        await projectsApi.deleteProject(token, projectId);
        const remaining = businesses.filter((b) => b.project_id !== projectId);
        setBusinesses(remaining);

        if (activeBusiness?.project_id === projectId) {
          if (remaining.length > 0) {
            switchBusiness(remaining[0]);
          } else {
            setActiveBusiness(null);
            setReportData(null);
            setDprData(null);
            localStorage.removeItem(getStorageKey());
          }
        }
        return true;
      } catch (err) {
        console.error("Delete business error:", err);
        throw err;
      }
    },
    [token, businesses, activeBusiness, switchBusiness, getStorageKey]
  );

  // Helper for quick pitch benchmark selection
  const loadBenchmarkCase = useCallback(
    async (pitchCase) => {
      const rep = await generateFeasibility(pitchCase.formData, token);
      setReportData(rep);
      return rep;
    },
    [token]
  );

  const value = {
    businesses,
    activeBusiness,
    reportData,
    dprData,
    loadingBusinesses,
    businessError,
    hasBusinesses: businesses.length > 0,
    loadUserBusinesses,
    switchBusiness,
    createAndSaveBusiness,
    deleteBusiness,
    loadBenchmarkCase,
    setReportData,
  };

  return <BusinessContext.Provider value={value}>{children}</BusinessContext.Provider>;
};

export const useBusiness = () => {
  const context = useContext(BusinessContext);
  if (!context) {
    throw new Error("useBusiness must be used within a BusinessProvider");
  }
  return context;
};

export default BusinessContext;
