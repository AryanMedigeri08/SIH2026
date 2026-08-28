/**
 * BusinessContext.jsx — Unified Multi-Business State Management & Persistence Context.
 * Manages user-owned businesses, active business selection, persistent restore across sessions,
 * status indicators (Healthy / Reconsideration / Critical), and business switching.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "./AuthContext";
import { projectsApi, generateFeasibility } from "../services/api";

const BusinessContext = createContext(null);
const ACTIVE_BIZ_KEY_PREFIX = "udyam_saathi_active_biz_";

export const BusinessProvider = ({ children }) => {
  const { token, isAuthenticated, userProfile } = useAuth();

  const [businesses, setBusinesses] = useState([]);
  const [activeBusiness, setActiveBusiness] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [dprData, setDprData] = useState(null);
  const [loadingBusinesses, setLoadingBusinesses] = useState(false);
  const [businessError, setBusinessError] = useState(null);
  // Login/profile synchronization can start more than one fetch.  Only the
  // newest response is allowed to update protected enterprise state.
  const loadRequestSequence = useRef(0);

  // Helper to get active storage key per user
  const getStorageKey = useCallback(() => {
    const uid = userProfile?.firebase_uid || "guest";
    return `${ACTIVE_BIZ_KEY_PREFIX}${uid}`;
  }, [userProfile?.firebase_uid]);

  // Complete cleanup of enterprise state on logout
  const clearBusinessState = useCallback(() => {
    loadRequestSequence.current += 1;
    setBusinesses([]);
    setActiveBusiness(null);
    setReportData(null);
    setDprData(null);
    setBusinessError(null);
    setLoadingBusinesses(false);

    // Active selection is only a convenience; remove it on logout so no
    // previous enterprise can be restored in a later user's UI.
    try {
      Object.keys(localStorage).forEach((key) => {
        if (key.startsWith(ACTIVE_BIZ_KEY_PREFIX)) {
          localStorage.removeItem(key);
        }
      });
    } catch (e) {
      console.warn("Could not clean localStorage business keys:", e);
    }
  }, []);

  // Load user's persistent businesses from backend API
  const loadUserBusinesses = useCallback(async (explicitToken = null) => {
    const authToken = explicitToken || token;
    if (!authToken) {
      clearBusinessState();
      return { list: [], hasBusinesses: false, activeBusiness: null };
    }

    const requestSequence = ++loadRequestSequence.current;
    setLoadingBusinesses(true);
    setBusinessError(null);
    try {
      const list = await projectsApi.listProjects(authToken);
      const projectList = Array.isArray(list) ? list : [];
      if (requestSequence !== loadRequestSequence.current) {
        return { list: projectList, hasBusinesses: projectList.length > 0, activeBusiness: null };
      }
      setBusinesses(projectList);

      if (projectList.length > 0) {
        // Restore previously active business from localStorage or select the first
        const savedActiveId = localStorage.getItem(getStorageKey());
        const matched = projectList.find((b) => b.project_id === savedActiveId);
        const selected = matched || projectList[0];

        setActiveBusiness(selected);
        try {
          localStorage.setItem(getStorageKey(), selected.project_id);
        } catch (_) {}

        // Restore analysis and DPR payload if available
        if (selected.analysis_result && selected.analysis_result.report) {
          setReportData(selected.analysis_result.report);
          setDprData(selected.analysis_result.dpr || null);
        } else if (selected.status === "draft") {
          // If draft, trigger analysis to populate data
          try {
            const analyzed = await projectsApi.analyzeProject(authToken, selected.project_id);
            if (requestSequence !== loadRequestSequence.current) {
              return { list: projectList, hasBusinesses: true, activeBusiness: selected };
            }
            setActiveBusiness(analyzed);
            if (analyzed.analysis_result?.report) {
              setReportData(analyzed.analysis_result.report);
              setDprData(analyzed.analysis_result.dpr || null);
            }
          } catch (analyzeErr) {
            console.warn("Could not auto-analyze draft project:", analyzeErr);
          }
        }
        return { list: projectList, hasBusinesses: true, activeBusiness: selected };
      } else {
        // User has 0 businesses
        setActiveBusiness(null);
        setReportData(null);
        setDprData(null);
        return { list: [], hasBusinesses: false, activeBusiness: null };
      }
    } catch (err) {
      console.error("Failed to load user businesses:", err);
      if (requestSequence !== loadRequestSequence.current) {
        return { list: [], hasBusinesses: false, activeBusiness: null };
      }
      // A 401 means the session ended remotely/revoked.  Do not leave stale
      // business, report, or DPR content rendered while the route guard reacts.
      if (err.status === 401) clearBusinessState();
      setBusinessError(err.message || "Failed to load businesses.");
      return { list: [], hasBusinesses: false, activeBusiness: null };
    } finally {
      if (requestSequence === loadRequestSequence.current) {
        setLoadingBusinesses(false);
      }
    }
  }, [token, getStorageKey, clearBusinessState]);

  // Trigger business load or clear on auth state change
  useEffect(() => {
    if (isAuthenticated && token) {
      loadUserBusinesses(token);
    } else {
      clearBusinessState();
    }
  }, [isAuthenticated, token, loadUserBusinesses, clearBusinessState]);

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
      try {
        localStorage.setItem(getStorageKey(), target.project_id);
      } catch (_) {}

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
        try {
          localStorage.setItem(getStorageKey(), createdProject.project_id);
        } catch (_) {}

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
            try {
              localStorage.removeItem(getStorageKey());
            } catch (_) {}
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
    clearBusinessState,
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
