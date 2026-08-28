/**
 * pitchCases.js — 3 Institutional Benchmark Solvency & Viability Scenarios.
 * Calibrated against Census 2011 demographics, statutory scheme rules, and supervised XGBoost model.
 * Language is dynamically governed by the platform's global language selector.
 */

export const PITCH_CASES = [
  {
    id: "case-1",
    name: "Scenario 1: Dairy Unit (WB)",
    fullTitle: "Joypur Fresh Dairy Processing Unit (Bankura, West Bengal)",
    badge: "SUITABLE • 99.9%",
    badgeColor: "emerald",
    formData: {
      enterprise_name: "Joypur Fresh Dairy Processing Unit",
      business_category: "manufacturing",
      sector: "dairy",
      promoter_name: "Dipankar Ghosh",
      promoter_category: "obc",
      gender: "Male",
      state_name: "West Bengal",
      district_name: "Bankura",
      block_name: "Joypur",
      village_name: "Joypur",
      is_rural: true,
      project_cost: 800000,
      annual_turnover_estimate: 1200000,
      tenure_years: 5,
      moratorium_months: 6,
    }
  },
  {
    id: "case-2",
    name: "Scenario 2: Artisan Pottery (UP)",
    fullTitle: "Khurja Traditional Glazed Pottery Works (Bulandshahr, Uttar Pradesh)",
    badge: "CAUTION • 98.0%",
    badgeColor: "amber",
    formData: {
      enterprise_name: "Khurja Traditional Glazed Pottery Works",
      business_category: "manufacturing",
      sector: "fabrication",
      promoter_name: "Ramswaroop Prajapati",
      promoter_category: "artisan",
      gender: "Male",
      state_name: "Uttar Pradesh",
      district_name: "Bulandshahr",
      block_name: "Sikandrabad",
      village_name: "Faridpur",
      is_rural: true,
      project_cost: 600000,
      annual_turnover_estimate: 320000,
      tenure_years: 5,
      moratorium_months: 3,
    }
  },
  {
    id: "case-3",
    name: "Scenario 3: Heavy Agro Plant (MP)",
    fullTitle: "Malwa Heavy Agro Solvent Plant (Ujjain, Madhya Pradesh)",
    badge: "RECONSIDER • 100.0%",
    badgeColor: "rose",
    formData: {
      enterprise_name: "Malwa Heavy Agro Solvent Plant",
      business_category: "manufacturing",
      sector: "food_processing",
      promoter_name: "Vikramaditya Rao",
      promoter_category: "general",
      gender: "Male",
      state_name: "Madhya Pradesh",
      district_name: "Ujjain",
      block_name: "Khacharod",
      village_name: "Gothda",
      is_rural: true,
      project_cost: 4800000,
      annual_turnover_estimate: 350000,
      tenure_years: 5,
      moratorium_months: 6,
    }
  }
];

export default PITCH_CASES;
