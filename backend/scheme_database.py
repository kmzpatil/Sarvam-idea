"""Curated Database of High-Impact Government Welfare Schemes."""

SCHEMES = [
    {
        "id": "pm-svanidhi",
        "name": "PM SVANidhi (Pradhan Mantri Street Vendor's AtmaNirbhar Nidhi)",
        "name_hi": "पीएम स्वनिधि योजना",
        "category": "Micro-Credit & Livelihood",
        "target_audience": ["Street Vendors", "Delivery Riders", "E-Rickshaw Drivers", "Small Hawkers"],
        "benefit_amount": "₹10,000 to ₹50,000 collateral-free working capital loan with 7% interest subsidy",
        "key_benefit": "Working capital loan starting at ₹10,000, graduating to ₹20,000 & ₹50,000 upon timely repayment.",
        "max_income_annual": 300000,
        "eligible_occupations": ["Street Vendor", "Driver", "Delivery Worker", "Cobbler", "Artisan", "Hawker", "Laborer"],
        "required_documents": [
            "Aadhaar Card",
            "Vending Certificate or Letter of Recommendation (LoR)",
            "Bank Account Linked to Mobile"
        ],
        "state_applicability": "All India",
        "description": "Special micro-credit facility empowering urban/semi-urban street vendors and gig workers to resume and scale livelihoods.",
        "application_url": "https://pmsvanidhi.mohua.gov.in/"
    },
    {
        "id": "ayushman-bharat-pmjay",
        "name": "Ayushman Bharat PM-JAY (Pradhan Mantri Jan Arogya Yojana)",
        "name_hi": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना",
        "category": "Health & Medical",
        "target_audience": ["BPL Families", "Rural & Urban Low-Income Households", "Senior Citizens (70+)"],
        "benefit_amount": "Up to ₹5,00,000 per family per year for secondary and tertiary hospitalization",
        "key_benefit": "Cashless and paperless access to quality healthcare at empaneled public and private hospitals nationwide.",
        "max_income_annual": 250000,
        "eligible_occupations": ["Any Low-Income / Informal Worker"],
        "required_documents": [
            "Aadhaar Card",
            "Ration Card (NFSA / BPL / SECC listed)",
            "Family ID or Income Certificate"
        ],
        "state_applicability": "All India",
        "description": "World's largest government-funded health assurance scheme providing ₹5 Lakh coverage per family annually.",
        "application_url": "https://beneficiary.nha.gov.in/"
    },
    {
        "id": "pm-kisan",
        "name": "PM-Kisan Samman Nidhi",
        "name_hi": "प्रधानमंत्री किसान सम्मान निधि",
        "category": "Agriculture & Farming",
        "target_audience": ["Small and Marginal Farmers"],
        "benefit_amount": "₹6,000 per year transferred directly in 3 equal installments of ₹2,000",
        "key_benefit": "Direct benefit transfer (DBT) into bank accounts to support farming input procurement and household needs.",
        "max_income_annual": 200000,
        "eligible_occupations": ["Farmer", "Agricultural Worker"],
        "required_documents": [
            "Aadhaar Card",
            "Land Ownership Records (Khata/Khesra / Jamabandi)",
            "Active Bank Account with e-KYC"
        ],
        "state_applicability": "All India",
        "description": "Central income support scheme for all landholding farmers to meet financial requirements for agricultural inputs.",
        "application_url": "https://pmkisan.gov.in/"
    },
    {
        "id": "pm-awas-yojana",
        "name": "Pradhan Mantri Awas Yojana (PMAY-Gramin / Urban)",
        "name_hi": "प्रधानमंत्री आवास योजना",
        "category": "Housing & Infrastructure",
        "target_audience": ["Kutcha House Dwellers", "Homeless", "Low-Income Families (EWS/LIG)"],
        "benefit_amount": "₹1,20,000 in plains, ₹1,30,000 in hilly areas + ₹12,000 toilet grant",
        "key_benefit": "Direct financial assistance for the construction of a pucca house with basic civic amenities (clean cooking, power, water).",
        "max_income_annual": 300000,
        "eligible_occupations": ["Any"],
        "required_documents": [
            "Aadhaar Card",
            "BPL Ration Card / SECC Data Reference",
            "Bank Account Linked with Aadhaar",
            "Affidavit of not owning a Pucca house"
        ],
        "state_applicability": "All India",
        "description": "Financial assistance to houseless households and those living in dilapidated houses for building durable pucca homes.",
        "application_url": "https://pmaymis.gov.in/"
    },
    {
        "id": "pm-vishwakarma",
        "name": "PM Vishwakarma Scheme",
        "name_hi": "पीएम विश्वकर्मा योजना",
        "category": "Artisans & Craftsmen",
        "target_audience": ["Traditional Artisans", "Carpenters", "Blacksmiths", "Potters", "Masons", "Tailors"],
        "benefit_amount": "₹15,000 Tool-kit incentive + Collateral-free credit up to ₹3,00,000 at concessional 5% interest",
        "key_benefit": "Recognition through Vishwakarma Certificate, 5-7 days skill training with ₹500/day stipend, and modern toolkit.",
        "max_income_annual": 400000,
        "eligible_occupations": ["Carpenter", "Blacksmith", "Potter", "Sculptor", "Cobbler", "Mason", "Tailor", "Barber", "Washerman"],
        "required_documents": [
            "Aadhaar Card",
            "Mobile-linked Bank Details",
            "Artisan Trade Verification"
        ],
        "state_applicability": "All India",
        "description": "Comprehensive scheme supporting 18 traditional artisanal trades with recognition, skilling, toolkits, and low-cost credit.",
        "application_url": "https://pmvishwakarma.gov.in/"
    },
    {
        "id": "atal-pension-yojana",
        "name": "Atal Pension Yojana (APY)",
        "name_hi": "अटल पेंशन योजना",
        "category": "Social Security & Pension",
        "target_audience": ["Unorganized Sector Workers aged 18 to 40 years"],
        "benefit_amount": "Guaranteed monthly pension of ₹1,000 to ₹5,000 after reaching age 60",
        "key_benefit": "Lifelong monthly pension with government guarantee, plus full accumulated corpus returned to nominee upon spouse demise.",
        "max_income_annual": 500000,
        "eligible_occupations": ["Informal Worker", "Self-Employed", "Domestic Worker", "Gig Worker"],
        "required_documents": [
            "Aadhaar Card",
            "Active Savings Bank Account with Auto-Debit",
            "Mobile Number"
        ],
        "state_applicability": "All India",
        "description": "Flagship social security pension scheme aimed at creating a self-sufficient retirement safety net for informal workers.",
        "application_url": "https://www.npscra.nsdl.co.in/"
    },
    {
        "id": "sukanya-samriddhi",
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "name_hi": "सुकन्या समृद्धि योजना",
        "category": "Girl Child & Education",
        "target_audience": ["Families with girl child below 10 years of age"],
        "benefit_amount": "8.2% annual compounded interest rate with complete Section 80C tax exemption",
        "key_benefit": "High-yield sovereign savings scheme for higher education and marriage of female children with partial withdrawals from age 18.",
        "max_income_annual": 1000000,
        "eligible_occupations": ["Any"],
        "required_documents": [
            "Birth Certificate of Girl Child",
            "Parent / Guardian Aadhaar & Identity Proof",
            "Initial deposit of ₹250"
        ],
        "state_applicability": "All India",
        "description": "Government-backed savings initiative under Beti Bachao Beti Padhao campaign ensuring financial independence for daughters.",
        "application_url": "https://www.indiapost.gov.in/"
    },
    {
        "id": "pm-ujjwala-yojana",
        "name": "Pradhan Mantri Ujjwala Yojana 2.0",
        "name_hi": "प्रधानमंत्री उज्ज्वला योजना 2.0",
        "category": "Clean Energy & Women Welfare",
        "target_audience": ["Adult Women from BPL / SC / ST / Most Backward Households"],
        "benefit_amount": "Free LPG connection with first cylinder and stove provided at zero cost + ₹300 per cylinder subsidy",
        "key_benefit": "Smoke-free healthy cooking environment protecting mothers and children from indoor respiratory pollution.",
        "max_income_annual": 200000,
        "eligible_occupations": ["Any Low-Income Household"],
        "required_documents": [
            "BPL Ration Card / Family Composition Certificate",
            "Woman Applicant's Aadhaar Card",
            "Bank Account linked to Aadhaar"
        ],
        "state_applicability": "All India",
        "description": "Supplies clean cooking fuel LPG connections to poor households, replacing hazardous biomass fuel.",
        "application_url": "https://www.pmuy.gov.in/"
    }
]


def search_schemes(query: str = "", occupation: str = "", income: int = 0, state: str = ""):
    """Filter or rank schemes based on citizen profile constraints."""
    matched = []
    for s in SCHEMES:
        score = 0
        if occupation:
            if any(occ.lower() in occupation.lower() for occ in s["eligible_occupations"]):
                score += 3
        if income > 0:
            if income <= s["max_income_annual"]:
                score += 2
            else:
                continue  # Disqualified if exceeds income cap
        if query:
            q_lower = query.lower()
            if any(word in s["name"].lower() or word in s["description"].lower() or word in s["category"].lower() for word in q_lower.split()):
                score += 2

        matched.append({**s, "relevance_score": score})

    matched.sort(key=lambda x: x["relevance_score"], reverse=True)
    return matched
