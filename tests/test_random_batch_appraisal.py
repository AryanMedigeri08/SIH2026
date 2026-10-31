"""
test_random_batch_appraisal.py — Exhaustive Random Multi-Geographic & Multi-Sector Stress Test
Tests 25 diverse enterprises across 13 Indian states, various business sectors, loan tiers,
and premise models (Rented, Owned, Panchayat).
Applies safe sleep intervals (2.2s) between LLM calls to respect Groq rate limits.
"""

import asyncio
import os
import sys
import time
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

# Add backend core and root to sys.path
backend_core = Path(__file__).resolve().parent.parent / "backend" / "app" / "core"
backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_core))
sys.path.insert(0, str(backend_root))

from app.models.schemas import UserInput
from app.routers.feasibility import _run_pipeline

# 25 Diverse, realistic, and stress-tested enterprise profiles across India
TEST_CASES = [
    # 1. Eastern Hub — West Bengal (Dairy, High Demand, Owned Land)
    {
        "id": "TC-01",
        "enterprise_name": "Radha Rani Chilled Milk & Paneer Hub",
        "business_category": "manufacturing",
        "sector": "dairy",
        "promoter_name": "Dipankar Ghosh",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "West Bengal",
        "district_name": "Bankura",
        "block_name": "Joypur",
        "village_name": "Joypur",
        "is_rural": True,
        "project_cost": 850000.0,
        "available_margin_capital": 85000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "Healthy viable agro-processing on ancestral plot"
    },
    # 2. Western Hub — Maharashtra (Marine & Cold Chain Food, Rented)
    {
        "id": "TC-02",
        "enterprise_name": "Konkan Fresh Fish Processing & Cold Store",
        "business_category": "manufacturing",
        "sector": "food_processing",
        "promoter_name": "Sunita Kadam",
        "promoter_category": "women",
        "gender": "Female",
        "state_name": "Maharashtra",
        "district_name": "Thane",
        "block_name": "Bhiwandi",
        "village_name": "Padgha",
        "is_rural": True,
        "project_cost": 1200000.0,
        "available_margin_capital": 60000.0,
        "premise_type": "rented",
        "monthly_rent": 4000.0,
        "expected_profile": "Strong semi-urban food processing, Women 5% margin"
    },
    # 3. Northern Hub — Uttar Pradesh (Terracotta Craft, Micro Scale, Artisan)
    {
        "id": "TC-03",
        "enterprise_name": "Mati Shrestha Terracotta Crafts",
        "business_category": "manufacturing",
        "sector": "artisan_trades",
        "promoter_name": "Hariram Prajapati",
        "promoter_category": "artisan",
        "gender": "Male",
        "state_name": "Uttar Pradesh",
        "district_name": "Gorakhpur",
        "block_name": "Campierganj",
        "village_name": "Rawatganj",
        "is_rural": True,
        "project_cost": 120000.0,
        "available_margin_capital": 6000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "Micro Vishwakarma artisan craft with high margin"
    },
    # 4. Southern Hub — Karnataka (Mobile & Laptop Chip-Level Repair, Rented)
    {
        "id": "TC-04",
        "enterprise_name": "Digital Care Mobile & Electronics Servicing",
        "business_category": "service",
        "sector": "repair",
        "promoter_name": "Naveen Kumar",
        "promoter_category": "obc",
        "gender": "Male",
        "state_name": "Karnataka",
        "district_name": "Ramanagara",
        "block_name": "Channapatna",
        "village_name": "Malur",
        "is_rural": True,
        "project_cost": 300000.0,
        "available_margin_capital": 15000.0,
        "premise_type": "rented",
        "monthly_rent": 2200.0,
        "expected_profile": "High margin repair service in rural market"
    },
    # 5. Central Hub — Madhya Pradesh (Textiles & Batik Dyeing, Panchayat Site)
    {
        "id": "TC-05",
        "enterprise_name": "Bhairavgarh Heritage Batik Textiles",
        "business_category": "manufacturing",
        "sector": "apparel",
        "promoter_name": "Meera Bai",
        "promoter_category": "sc",
        "gender": "Female",
        "state_name": "Madhya Pradesh",
        "district_name": "Ujjain",
        "block_name": "Badnagar",
        "village_name": "Jahangirpur",
        "is_rural": True,
        "project_cost": 450000.0,
        "available_margin_capital": 22500.0,
        "premise_type": "panchayat",
        "monthly_rent": 0.0,
        "expected_profile": "ODOP Textile cluster, SC Women promoter, Panchayat space"
    },
    # 6. Northern Hub — Bihar (Agro Turmeric & Mustard Oil Mill, Owned)
    {
        "id": "TC-06",
        "enterprise_name": "Mithila Shuddha Mustard & Spices Processing",
        "business_category": "manufacturing",
        "sector": "food_processing",
        "promoter_name": "Rajeshwar Prasad Singh",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Bihar",
        "district_name": "Muzaffarpur",
        "block_name": "Kanti",
        "village_name": "Madhuban",
        "is_rural": True,
        "project_cost": 1500000.0,
        "available_margin_capital": 150000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "Medium scale agro-milling unit on owned farm plot"
    },
    # 7. Western Hub — Gujarat (Rural Dairy Cold Chain & Ghee, Owned)
    {
        "id": "TC-07",
        "enterprise_name": "Charotar Organic A2 Cow Milk & Ghee Dairy",
        "business_category": "manufacturing",
        "sector": "dairy",
        "promoter_name": "Patel Bhaveshbhai",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Gujarat",
        "district_name": "Anand",
        "block_name": "Petlad",
        "village_name": "Bhadran",
        "is_rural": True,
        "project_cost": 1800000.0,
        "available_margin_capital": 180000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "High density cooperative belt, high throughput dairy"
    },
    # 8. Southern Hub — Tamil Nadu (Coir & Agro Fabrication Works, Rented)
    {
        "id": "TC-08",
        "enterprise_name": "Kongu Agro Implements & Grills Fabrication",
        "business_category": "manufacturing",
        "sector": "fabrication",
        "promoter_name": "Senthil Murugan",
        "promoter_category": "obc",
        "gender": "Male",
        "state_name": "Tamil Nadu",
        "district_name": "Coimbatore",
        "block_name": "Pollachi",
        "village_name": "Anamalai",
        "is_rural": True,
        "project_cost": 750000.0,
        "available_margin_capital": 37500.0,
        "premise_type": "rented",
        "monthly_rent": 3500.0,
        "expected_profile": "Farm implements fabrication, steady demand"
    },
    # 9. Eastern Hub — Odisha (Pipili Applique & Tailoring Cluster, Rented)
    {
        "id": "TC-09",
        "enterprise_name": "Pipili Chandua Heritage Stitching Unit",
        "business_category": "manufacturing",
        "sector": "apparel",
        "promoter_name": "Pravati Mohapatra",
        "promoter_category": "women",
        "gender": "Female",
        "state_name": "Odisha",
        "district_name": "Puri",
        "block_name": "Pipili",
        "village_name": "Dandmukundapur",
        "is_rural": True,
        "project_cost": 350000.0,
        "available_margin_capital": 17500.0,
        "premise_type": "rented",
        "monthly_rent": 1800.0,
        "expected_profile": "Artisanal textile tourist craft corridor"
    },
    # 10. Northern Hub — Rajasthan (Sanitary & Hardware Trading, Rented)
    {
        "id": "TC-10",
        "enterprise_name": "Marwar Hardware, Sanitary & Pipe Store",
        "business_category": "service",
        "sector": "trading",
        "promoter_name": "Gopal Lal Sharma",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Rajasthan",
        "district_name": "Jodhpur",
        "block_name": "Bilara",
        "village_name": "Bhavis",
        "is_rural": True,
        "project_cost": 600000.0,
        "available_margin_capital": 60000.0,
        "premise_type": "rented",
        "monthly_rent": 3000.0,
        "expected_profile": "Rural retail trade, fast turnover velocity"
    },
    # 11. Himalayan Hub — Himachal Pradesh (Apple Grading & Juice Unit, Owned)
    {
        "id": "TC-11",
        "enterprise_name": "Himalayan Orchards Apple Cider & Jam Unit",
        "business_category": "manufacturing",
        "sector": "food_processing",
        "promoter_name": "Rohit Thakur",
        "promoter_category": "st",
        "gender": "Male",
        "state_name": "Himachal Pradesh",
        "district_name": "Shimla",
        "block_name": "Theog",
        "village_name": "Fagu",
        "is_rural": True,
        "project_cost": 1400000.0,
        "available_margin_capital": 70000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "Hilly terrain agro processing, ST promoter"
    },
    # 12. North-East Hub — Assam (Bamboo Crafts & Furniture, Panchayat)
    {
        "id": "TC-12",
        "enterprise_name": "Brahmaputra Cane & Bamboo Furniture Works",
        "business_category": "manufacturing",
        "sector": "artisan_trades",
        "promoter_name": "Pranab Kalita",
        "promoter_category": "obc",
        "gender": "Male",
        "state_name": "Assam",
        "district_name": "Kamrup",
        "block_name": "Hajo",
        "village_name": "Damdama",
        "is_rural": True,
        "project_cost": 280000.0,
        "available_margin_capital": 14000.0,
        "premise_type": "panchayat",
        "monthly_rent": 0.0,
        "expected_profile": "Abundant local raw material, zero rent village plot"
    },
    # 13. Southern Hub — Kerala (Spices Cleaning & Value Addition, Rented)
    {
        "id": "TC-13",
        "enterprise_name": "Malabar Pepper & Cardamom Processing Center",
        "business_category": "manufacturing",
        "sector": "food_processing",
        "promoter_name": "George Mathew",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Kerala",
        "district_name": "Wayanad",
        "block_name": "Mananthavady",
        "village_name": "Thirunelly",
        "is_rural": True,
        "project_cost": 950000.0,
        "available_margin_capital": 95000.0,
        "premise_type": "rented",
        "monthly_rent": 3500.0,
        "expected_profile": "Exportable high-value spices processing"
    },
    # 14. Stress Test Case 1: Overleveraged Bakery in Tiny Village (High Capex, Stressed Demand)
    {
        "id": "TC-14",
        "enterprise_name": "Grand Imperial Royal Bakery & Confectionery",
        "business_category": "manufacturing",
        "sector": "food_processing",
        "promoter_name": "Vikram Verma",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Uttar Pradesh",
        "district_name": "Varanasi",
        "block_name": "Kashi",
        "village_name": "TinyHamlet",
        "is_rural": True,
        "project_cost": 4200000.0,  # 42 Lakhs capex in rural village!
        "available_margin_capital": 420000.0,
        "premise_type": "rented",
        "monthly_rent": 14000.0,  # Very high rent drag
        "expected_profile": "STRESS TEST: Heavy debt service, high rent drag -> Expect CAUTION or RECONSIDER"
    },
    # 15. Stress Test Case 2: Excessive Capex for Low-Ticket Service in Isolated Outpost
    {
        "id": "TC-15",
        "enterprise_name": "Ultra Mega Auto Body & Heavy Paint Shop",
        "business_category": "service",
        "sector": "repair",
        "promoter_name": "Kailash Chand",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Rajasthan",
        "district_name": "Barmer",
        "block_name": "Sheo",
        "village_name": "Gadra",
        "is_rural": True,
        "project_cost": 2800000.0,  # 28 Lakhs for rural car painting in remote desert
        "available_margin_capital": 280000.0,
        "premise_type": "rented",
        "monthly_rent": 8500.0,
        "expected_profile": "STRESS TEST: High debt burden, low density catchment -> Expect CAUTION or RECONSIDER"
    },
    # 16. Tech Rural Hub — Karnataka (Drone Repair & Battery Servicing Lab)
    {
        "id": "TC-16",
        "enterprise_name": "Kisan Drones & Precision Ag Diagnostic Lab",
        "business_category": "service",
        "sector": "repair",
        "promoter_name": "Chethan Gowda",
        "promoter_category": "obc",
        "gender": "Male",
        "state_name": "Karnataka",
        "district_name": "Mysuru",
        "block_name": "Nanjangud",
        "village_name": "Hullahalli",
        "is_rural": True,
        "project_cost": 800000.0,
        "available_margin_capital": 40000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "Modern high-tech service, owned premise, OBC 5% margin"
    },
    # 17. Eastern Hub — West Bengal (Handloom Baluchari Silk Weaving, Women SHG)
    {
        "id": "TC-17",
        "enterprise_name": "Bishnupur Silk & Baluchari Weavers Unit",
        "business_category": "manufacturing",
        "sector": "apparel",
        "promoter_name": "Aparna Das",
        "promoter_category": "women",
        "gender": "Female",
        "state_name": "West Bengal",
        "district_name": "Bankura",
        "block_name": "Bishnupur",
        "village_name": "Balarampur",
        "is_rural": True,
        "project_cost": 500000.0,
        "available_margin_capital": 25000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "ODOP GI Cluster, Women 5% margin, strong export link"
    },
    # 18. Central Hub — Uttar Pradesh (Ceramic Pottery & Glazing, Khurja)
    {
        "id": "TC-18",
        "enterprise_name": "Khurja Crockery & Insulators Studio",
        "business_category": "manufacturing",
        "sector": "artisan_trades",
        "promoter_name": "Mohammad Irfan",
        "promoter_category": "obc",
        "gender": "Male",
        "state_name": "Uttar Pradesh",
        "district_name": "Bulandshahr",
        "block_name": "Khurja",
        "village_name": "Daryapur",
        "is_rural": True,
        "project_cost": 650000.0,
        "available_margin_capital": 32500.0,
        "premise_type": "rented",
        "monthly_rent": 2800.0,
        "expected_profile": "Historical ceramic pottery ODOP belt, export demand"
    },
    # 19. Micro Finance Scheme Case 1: Women Tailoring Shop in Bihar (₹80k Loan)
    {
        "id": "TC-19",
        "enterprise_name": "Kalyani Ladies Boutique & Stitching Center",
        "business_category": "service",
        "sector": "apparel",
        "promoter_name": "Kalyani Devi",
        "promoter_category": "women",
        "gender": "Female",
        "state_name": "Bihar",
        "district_name": "Patna",
        "block_name": "Danapur",
        "village_name": "Maner",
        "is_rural": True,
        "project_cost": 90000.0,
        "available_margin_capital": 4500.0,
        "premise_type": "rented",
        "monthly_rent": 1000.0,
        "expected_profile": "Micro Finance Scheme (< ₹1.4L), 6.5% interest, fast payback"
    },
    # 20. Micro Finance Scheme Case 2: Bicycle & EV 2-Wheeler Puncture Servicing (₹60k Loan)
    {
        "id": "TC-20",
        "enterprise_name": "Bajrangbali Two-Wheeler & Puncture Clinic",
        "business_category": "service",
        "sector": "repair",
        "promoter_name": "Ramu Paswan",
        "promoter_category": "sc",
        "gender": "Male",
        "state_name": "Bihar",
        "district_name": "Gaya",
        "block_name": "Bodhgaya",
        "village_name": "Bakrour",
        "is_rural": True,
        "project_cost": 60000.0,
        "available_margin_capital": 3000.0,
        "premise_type": "panchayat",
        "monthly_rent": 0.0,
        "expected_profile": "Micro loan, zero rent, high ROI service"
    },
    # 21. Clean Energy Hub — Maharashtra (Solar Inverter & Pump Servicing)
    {
        "id": "TC-21",
        "enterprise_name": "Surya Shakti Solar Installation & Pump Care",
        "business_category": "service",
        "sector": "service",
        "promoter_name": "Anand Shinde",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Maharashtra",
        "district_name": "Satara",
        "block_name": "Karad",
        "village_name": "Kole",
        "is_rural": True,
        "project_cost": 700000.0,
        "available_margin_capital": 70000.0,
        "premise_type": "rented",
        "monthly_rent": 2500.0,
        "expected_profile": "PM-KUSUM linkage, high growth clean energy service"
    },
    # 22. Stress Test Case 3: Over-leveraged Trading Unit with high rent and thin margin
    {
        "id": "TC-22",
        "enterprise_name": "Mega Wholesale Agro Chemical & Fertilizer Depot",
        "business_category": "service",
        "sector": "trading",
        "promoter_name": "Dinesh Chandra",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Madhya Pradesh",
        "district_name": "Indore",
        "block_name": "Depalpur",
        "village_name": "Gautampura",
        "is_rural": True,
        "project_cost": 3500000.0,
        "available_margin_capital": 350000.0,
        "premise_type": "rented",
        "monthly_rent": 12000.0,  # High rent on thin trading margin
        "expected_profile": "STRESS TEST: High debt, heavy rent, thin 18% trading margin -> Expect CAUTION"
    },
    # 23. Southern Hub — Andhra Pradesh (Poultry & Livestock Feed Milling)
    {
        "id": "TC-23",
        "enterprise_name": "Rayalaseema Cattle & Poultry Feed Processing",
        "business_category": "manufacturing",
        "sector": "food_processing",
        "promoter_name": "Venkatesh Naidu",
        "promoter_category": "obc",
        "gender": "Male",
        "state_name": "Andhra Pradesh",
        "district_name": "Chittoor",
        "block_name": "Palamaner",
        "village_name": "Baireddipalle",
        "is_rural": True,
        "project_cost": 1100000.0,
        "available_margin_capital": 55000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "Livestock feed manufacturing on owned plot"
    },
    # 24. North-East Hub — Meghalaya / Assam (Turmeric Polishing & Packaging)
    {
        "id": "TC-24",
        "enterprise_name": "Lakadong Super Curcumin Turmeric Processing",
        "business_category": "manufacturing",
        "sector": "food_processing",
        "promoter_name": "Bormon Roy",
        "promoter_category": "st",
        "gender": "Male",
        "state_name": "Assam",
        "district_name": "Goalpara",
        "block_name": "Matia",
        "village_name": "Mornai",
        "is_rural": True,
        "project_cost": 850000.0,
        "available_margin_capital": 42500.0,
        "premise_type": "rented",
        "monthly_rent": 2000.0,
        "expected_profile": "High GI value turmeric polishing, ST promoter"
    },
    # 25. Northern Hub — Punjab (Dairy Chilling & Desi Ghee Unit)
    {
        "id": "TC-25",
        "enterprise_name": "Majha Pure Buffalo Dairy & Butter Works",
        "business_category": "manufacturing",
        "sector": "dairy",
        "promoter_name": "Harpreet Singh",
        "promoter_category": "general",
        "gender": "Male",
        "state_name": "Punjab",
        "district_name": "Ludhiana",
        "block_name": "Jagraon",
        "village_name": "Sidwan",
        "is_rural": True,
        "project_cost": 1600000.0,
        "available_margin_capital": 160000.0,
        "premise_type": "owned",
        "monthly_rent": 0.0,
        "expected_profile": "High livestock density, strong domestic market"
    },
]

async def run_stress_test_batch():
    print("=" * 100)
    print("UDYAM SAATHI (Udyam Saathi) - RANDOM MULTI-GEOGRAPHIC & MULTI-SECTOR STRESS TEST")
    print(f"Executing {len(TEST_CASES)} diverse test cases across 13 Indian states...")
    print("Safe rate-limit throttling: 2.2 seconds interval between LLM calls")
    print("=" * 100)

    results = []
    start_all_time = time.time()

    ml_verdict_counts = {"SUITABLE": 0, "CAUTION": 0, "RECONSIDER": 0, "ERROR": 0}
    dscr_verdict_counts = {"VIABLE": 0, "MARGINAL": 0, "AT RISK": 0}
    premise_counts = {"owned": 0, "rented": 0, "panchayat": 0}
    sector_counts = {}

    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"\n[{idx:02d}/{len(TEST_CASES):02d}] Testing: {tc['enterprise_name']} ({tc['sector'].upper()}, {tc['district_name']}, {tc['state_name']})")
        print(f"       Cost: ₹{tc['project_cost']:,.0f} | Margin: ₹{tc['available_margin_capital']:,.0f} | Premise: {tc['premise_type'].upper()} (Rent: ₹{tc['monthly_rent']:,.0f}/mo)")

        user_input = UserInput(
            enterprise_name=tc["enterprise_name"],
            business_category=tc["business_category"],
            sector=tc["sector"],
            promoter_name=tc["promoter_name"],
            promoter_category=tc["promoter_category"],
            gender=tc["gender"],
            state_name=tc["state_name"],
            district_name=tc["district_name"],
            block_name=tc["block_name"],
            village_name=tc["village_name"],
            is_rural=tc["is_rural"],
            project_cost=tc["project_cost"],
            available_margin_capital=tc["available_margin_capital"],
            premise_type=tc["premise_type"],
            monthly_rent=tc["monthly_rent"],
            additional_business_details=f"{tc['expected_profile']}. Verified operational viability test.",
        )

        t0 = time.time()
        try:
            report, dpr = await _run_pipeline(user_input)
            elapsed = time.time() - t0

            ml_v = report.ml_viability.get("verdict", "UNKNOWN")
            ml_conf = report.ml_viability.get("confidence_pct", 0.0)
            dscr_data = report.financial_analysis.get("dscr", {})
            dscr_val = dscr_data.get("dscr", 0.0)
            dscr_v = dscr_data.get("verdict", "UNKNOWN")
            dscr_class = dscr_data.get("classification", "")
            monthly_noi = report.financial_analysis.get("monthly_net_profit", 0.0)
            top_scheme = report.scheme_optimization[0].get("scheme_id") if report.scheme_optimization else "N/A"
            mach_count = len(report.machinery_schedule.get("items", [])) if report.machinery_schedule else 0
            mach_load = report.machinery_schedule.get("total_connected_load_kw", 0.0) if report.machinery_schedule else 0.0

            # Update tallies
            if ml_v in ml_verdict_counts:
                ml_verdict_counts[ml_v] += 1
            else:
                ml_verdict_counts[ml_v] = 1

            if dscr_v in dscr_verdict_counts:
                dscr_verdict_counts[dscr_v] += 1

            premise_counts[tc["premise_type"]] = premise_counts.get(tc["premise_type"], 0) + 1
            sector_counts[tc["sector"]] = sector_counts.get(tc["sector"], 0) + 1

            res_entry = {
                "id": tc["id"],
                "enterprise_name": tc["enterprise_name"],
                "state": tc["state_name"],
                "district": tc["district_name"],
                "sector": tc["sector"],
                "category": tc["business_category"],
                "project_cost": tc["project_cost"],
                "premise_type": tc["premise_type"],
                "monthly_rent": tc["monthly_rent"],
                "annual_sales": user_input.annual_turnover_estimate,
                "ml_verdict": ml_v,
                "ml_confidence_pct": round(ml_conf, 1),
                "dscr": dscr_val,
                "dscr_verdict": dscr_v,
                "dscr_classification": dscr_class,
                "top_scheme": top_scheme,
                "machinery_count": mach_count,
                "connected_load_kw": mach_load,
                "elapsed_sec": round(elapsed, 2),
                "status": "SUCCESS"
            }
            results.append(res_entry)

            print(f"       -> [RESULT] ML: {ml_v} ({ml_conf:.1f}%) | DSCR: {dscr_val:.2f}x ({dscr_v} - {dscr_class}) | Scheme: {top_scheme} | Mach: {mach_count} items ({mach_load:.1f} kW) | Time: {elapsed:.2f}s")

        except Exception as e:
            elapsed = time.time() - t0
            print(f"       -> [ERROR] Failed pipeline execution: {str(e)}")
            ml_verdict_counts["ERROR"] += 1
            results.append({
                "id": tc["id"],
                "enterprise_name": tc["enterprise_name"],
                "error": str(e),
                "status": "FAILED"
            })

        # Respect Groq / LLM rate limits with safe 2.2s sleep between iterations
        if idx < len(TEST_CASES):
            time.sleep(2.2)

    total_time = time.time() - start_all_time

    # Save detailed JSON log
    out_dir = Path("tests/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "random_stress_test_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(TEST_CASES),
            "total_elapsed_sec": round(total_time, 2),
            "ml_verdict_tallies": ml_verdict_counts,
            "dscr_verdict_tallies": dscr_verdict_counts,
            "premise_distribution": premise_counts,
            "sector_distribution": sector_counts,
            "case_results": results
        }, f, indent=2)

    print("\n" + "=" * 100)
    print("BATCH TESTING COMPLETED SUCCESSFULLY!")
    print(f"Total Execution Time: {total_time:.2f} seconds across {len(TEST_CASES)} cases (Average: {total_time/len(TEST_CASES):.2f}s/case)")
    print(f"Report written to: {out_file}")
    print("=" * 100)
    print("\n--- ML VIABILITY VERDICT BREAKDOWN (Tier 2 XGBoost Classifier) ---")
    for k, v in ml_verdict_counts.items():
        pct = (v / len(TEST_CASES)) * 100
        print(f"  * {k:12s}: {v:2d} cases ({pct:.1f}%)")

    print("\n--- DSCR DEBT-SERVICE COVERAGE VERDICT BREAKDOWN (Tier 1 Financial Underwriting) ---")
    for k, v in dscr_verdict_counts.items():
        pct = (v / len(TEST_CASES)) * 100
        print(f"  * {k:12s}: {v:2d} cases ({pct:.1f}%)")

    print("\n--- SAMPLE HIGHLIGHT CASES ---")
    for r in results:
        if r.get("status") == "SUCCESS":
            if r["ml_verdict"] in ("CAUTION", "RECONSIDER") or r["dscr_verdict"] in ("MARGINAL", "AT RISK") or r["dscr"] >= 2.5:
                print(f"  * [{r['id']}] {r['enterprise_name']}: ML={r['ml_verdict']}, DSCR={r['dscr']:.2f}x ({r['dscr_verdict']}), Scheme={r['top_scheme']}, Premise={r['premise_type']}")


if __name__ == "__main__":
    asyncio.run(run_stress_test_batch())
