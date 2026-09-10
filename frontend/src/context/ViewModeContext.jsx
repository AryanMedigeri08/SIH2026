import React, { createContext, useContext, useState, useEffect } from 'react';

const ViewModeContext = createContext(null);

export const VIEW_MODES = {
  BENEFICIARY: 'beneficiary', // उद्यमी / Rural Entrepreneur View (Jargon-free, actionable, empowering)
  BANKER: 'banker',           // बैंक प्रबंधक / SCA Officer / Credit Auditor View (10-D ML, TreeSHAP, full audit)
};

export function ViewModeProvider({ children }) {
  const [viewMode, setViewModeState] = useState(() => {
    try {
      const saved = localStorage.getItem('udyam_saathi_view_mode');
      return saved === VIEW_MODES.BANKER ? VIEW_MODES.BANKER : VIEW_MODES.BENEFICIARY;
    } catch {
      return VIEW_MODES.BENEFICIARY;
    }
  });

  const setViewMode = (mode) => {
    if (mode === VIEW_MODES.BENEFICIARY || mode === VIEW_MODES.BANKER) {
      setViewModeState(mode);
      try {
        localStorage.setItem('udyam_saathi_view_mode', mode);
      } catch (err) {
        console.warn('Could not persist view mode:', err);
      }
    }
  };

  const toggleViewMode = () => {
    setViewMode(viewMode === VIEW_MODES.BENEFICIARY ? VIEW_MODES.BANKER : VIEW_MODES.BENEFICIARY);
  };

  const isBeneficiary = viewMode === VIEW_MODES.BENEFICIARY;
  const isBanker = viewMode === VIEW_MODES.BANKER;

  return (
    <ViewModeContext.Provider
      value={{
        viewMode,
        setViewMode,
        toggleViewMode,
        isBeneficiary,
        isBanker,
      }}
    >
      {children}
    </ViewModeContext.Provider>
  );
}

export function useViewMode() {
  const ctx = useContext(ViewModeContext);
  if (!ctx) {
    // Graceful fallback if rendered outside provider
    return {
      viewMode: VIEW_MODES.BENEFICIARY,
      setViewMode: () => {},
      toggleViewMode: () => {},
      isBeneficiary: true,
      isBanker: false,
    };
  }
  return ctx;
}

export default ViewModeContext;
