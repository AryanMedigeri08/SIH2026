import React, { createContext, useContext } from 'react';
import { useAuth } from './AuthContext';

const ViewModeContext = createContext(null);

export const VIEW_MODES = {
  BENEFICIARY: 'beneficiary', // उद्यमी / Rural Entrepreneur View (Jargon-free, actionable, empowering)
  BANKER: 'banker',           // बैंक प्रबंधक / SCA Officer / Credit Auditor View (10-D ML, TreeSHAP, full audit)
};

export function ViewModeProvider({ children }) {
  // Appraisal mode comes only from the backend-authenticated role. A visitor
  // cannot reveal banker components by editing browser storage or a toggle.
  const { userProfile } = useAuth();
  const isBanker = userProfile?.role === 'banker';
  const isBeneficiary = !isBanker;
  const viewMode = isBanker ? VIEW_MODES.BANKER : VIEW_MODES.BENEFICIARY;
  const setViewMode = () => {};
  const toggleViewMode = () => {};

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
