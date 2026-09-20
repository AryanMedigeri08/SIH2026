import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            # Header
            self.drawString(45, 805, "UDYAM SAATHI (उद्यम साथी) — Master Demo Screenplay & Architecture Blueprint")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(45, 798, 550, 798)
            # Footer
            self.line(45, 45, 550, 45)
            self.drawString(45, 33, "Smart India Hackathon 2026 • Confidential & Proprietary")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(550, 33, page_text)
            self.restoreState()

def build_pdf(filename="c:/SIH2026/Udyam_Saathi_Demo_Screenplay_Master_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=52,
        bottomMargin=52
    )

    styles = getSampleStyleSheet()

    # Custom styles
    c_navy = colors.HexColor("#0f172a")
    c_blue = colors.HexColor("#1e40af")
    c_slate = colors.HexColor("#334155")
    c_muted = colors.HexColor("#64748b")
    c_border = colors.HexColor("#cbd5e1")
    c_light_bg = colors.HexColor("#f8fafc")

    # Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=c_navy,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=c_slate,
        spaceAfter=15
    )

    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#065f46"),
        alignment=0
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=c_navy,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_blue,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=c_slate,
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=c_navy
    )

    scene_title_style = ParagraphStyle(
        "SceneTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.white
    )

    dialogue_speaker = ParagraphStyle(
        "DialogueSpeaker",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=c_navy
    )

    dialogue_body = ParagraphStyle(
        "DialogueBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=c_slate
    )

    dialogue_sub = ParagraphStyle(
        "DialogueSub",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10.5,
        textColor=c_muted
    )

    tech_cue = ParagraphStyle(
        "TechCue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#5b21b6")
    )

    tech_cue_title = ParagraphStyle(
        "TechCueTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#4c1d95")
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=c_navy
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=c_slate
    )

    story = []

    # =========================================================================
    # COVER PAGE / HEADER
    # =========================================================================
    # Tricolor bar
    story.append(Table([["", "", ""]], colWidths=[170, 170, 170], rowHeights=[4], style=[
        ("BACKGROUND", (0,0), (0,0), colors.HexColor("#FF9933")),
        ("BACKGROUND", (1,0), (1,0), colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (2,0), (2,0), colors.HexColor("#138808")),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(Spacer(1, 15))

    # Category Pill
    pill_table = Table([[Paragraph("🎬 SIH 2026 MASTER PRODUCTION BLUEPRINT • CINEMATIC SCREENPLAY & SYSTEM GUIDE", badge_style)]],
                       style=[
                           ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#d1fae5")),
                           ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#a7f3d0")),
                           ("TOPPADDING", (0,0), (-1,-1), 4),
                           ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                           ("LEFTPADDING", (0,0), (-1,-1), 8),
                           ("RIGHTPADDING", (0,0), (-1,-1), 8),
                       ])
    story.append(pill_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("UDYAM SAATHI (उद्यम साथी)", title_style))
    story.append(Paragraph("AI-Driven Hyper-Local Business Advisory & Financial Structuring Assistant<br/><b>Master Demo Screenplay, Visual Storyboard & Comprehensive Tab Architecture</b>", subtitle_style))

    # Metadata Box Table
    meta_data = [
        [
            Paragraph("<b>Storytelling Approach:</b> 3-Character Story (Patty, Arry, YD) + Mira Voice AI", table_cell),
            Paragraph("<b>Production Objective:</b> SIH 2026 Grand Finale Pitch & Product Demo", table_cell)
        ],
        [
            Paragraph("<b>Core AI Engine:</b> Sarvam-105b-conversations + Bhashini ULCA Speech", table_cell),
            Paragraph("<b>Financial Math Core:</b> Deterministic Banking Math (Zero LLM Guesswork)", table_cell)
        ],
        [
            Paragraph("<b>Machine Learning:</b> Supervised XGBoost 10-D Classifier + TreeSHAP", table_cell),
            Paragraph("<b>Sovereign Datasets:</b> Census 2026 TAM, 613 Amenities, 17 Govt Schemes", table_cell)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 260], style=[
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ])
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 1: NARRATIVE PHILOSOPHY & CAST
    # =========================================================================
    story.append(Paragraph("1. The Three-Character Narrative Framework", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_navy, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Traditional hackathon presentations fail because they begin with static introductory slides stating: <i>'Welcome to our AI platform.'</i> "
        "<b>Udyam Saathi</b> breaks this paradigm by employing a <b>cinematic, documentary-style three-character narrative</b> where each character "
        "embodies a specific functional layer of the platform ecosystem:",
        body_style
    ))

    # Cast Table
    cast_data = [
        [
            Paragraph("<b>Character</b>", table_header),
            Paragraph("<b>Role & Identity</b>", table_header),
            Paragraph("<b>Narrative & Demonstration Function</b>", table_header),
            Paragraph("<b>Evaluation Impact (Judges)</b>", table_header)
        ],
        [
            Paragraph("<font color='#c2410c'><b>Patty</b></font>", table_cell),
            Paragraph("Rural Entrepreneur<br/>(Faridpur Village, Bulandshahr, UP)", table_cell),
            Paragraph("Represents the authentic target beneficiary. Has domain passion and raw ambition, but is paralyzed by capital uncertainty, fear of loan rejection, and lack of structured data.", table_cell),
            Paragraph("Establishes deep human empathy and demonstrates real ground-level problem validation.", table_cell)
        ],
        [
            Paragraph("<font color='#1d4ed8'><b>Arry</b></font>", table_cell),
            Paragraph("Guide, Mentor & Tech-Forward Friend", table_cell),
            Paragraph("Bridges the gap between rural intuition and modern digital infrastructure. Stops Patty from gambling on guesswork and introduces Udyam Saathi.", table_cell),
            Paragraph("Serves as the natural catalyst transitioning the story from rural dilemma into the digital product.", table_cell)
        ],
        [
            Paragraph("<font color='#047857'><b>Mira (मीरा)</b></font>", table_cell),
            Paragraph("Sovereign Voice AI Assistant<br/>(Sarvam-105b + Bhashini)", table_cell),
            Paragraph("The interactive voice interface. Speaks fluent Hindi, understands multi-turn context, triggers live UI navigation, and explains complex credit terms with didi-like warmth.", table_cell),
            Paragraph("Showcases sovereign Indic voice technology, live tool calling, and zero-friction accessibility for Bharat.", table_cell)
        ],
        [
            Paragraph("<font color='#6d28d9'><b>YD</b></font>", table_cell),
            Paragraph("Storyteller / Technical Voiceover", table_cell),
            Paragraph("Breaks the 4th wall to address evaluators directly. Never states the obvious; instead, explains the mathematical models, Census formulas, and sovereign datasets powering the platform.", table_cell),
            Paragraph("Establishes technical authority, proving deterministic math, XGBoost ML, and institutional bank readiness.", table_cell)
        ]
    ]

    cast_table = Table(cast_data, colWidths=[65, 125, 185, 135], style=[
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ("BOX", (0,0), (-1,-1), 1, c_border),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ])
    story.append(cast_table)
    story.append(Spacer(1, 10))

    # Core Engineering Invariants Box
    inv_data = [
        [
            Paragraph("<b>CRITICAL TECHNICAL INVARIANTS HIGHLIGHTED IN THE DEMO:</b><br/>"
                      "<b>1. Zero LLM Financial Guesswork:</b> All ₹ figures, subsidies, EMIs, and DSCR ratios are calculated by a deterministic math engine. The LLM only generates narrative prose.<br/>"
                      "<b>2. Supervised XGBoost Viability Classifier:</b> 10-D feature vector with TreeSHAP explainability—eliminating arbitrary AI verdicts.<br/>"
                      "<b>3. Sovereign Indic Voice Cascade:</b> Sarvam 22-lang detection → Bhashini ULCA ASR → Sarvam-105b LLM → Bhashini Indic TTS with full output.", body_style)
        ]
    ]
    inv_table = Table(inv_data, colWidths=[510], style=[
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#eff6ff")),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#bfdbfe")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
    ])
    story.append(inv_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 2: SCENE-BY-SCENE SCREENPLAY
    # =========================================================================
    story.append(Paragraph("2. Complete Scene-by-Scene Production Screenplay", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_navy, spaceBefore=2, spaceAfter=8))

    def make_scene_block(scene_num, title, timecode, setting, dialogues, tech_cue_text, ui_cue_text):
        content = []
        # Scene Header
        hdr = Table([[Paragraph(f"<b>{scene_num}: {title}</b>", scene_title_style),
                      Paragraph(f"<font color='#cbd5e1'><b>{timecode}</b></font>", table_header)]],
                    colWidths=[380, 130],
                    style=[
                        ("BACKGROUND", (0,0), (-1,-1), c_navy),
                        ("TOPPADDING", (0,0), (-1,-1), 4),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                        ("LEFTPADDING", (0,0), (-1,-1), 8),
                        ("RIGHTPADDING", (0,0), (-1,-1), 8),
                    ])
        content.append(hdr)

        body_items = []
        # Setting
        body_items.append([Paragraph(f"<i><b>Setting & Visual:</b> {setting}</i>", body_style)])

        # Dialogues
        for speaker, text, sub in dialogues:
            speaker_color = "#c2410c" if speaker == "PATTY" else "#1d4ed8" if speaker == "ARRY" else "#047857" if "MIRA" in speaker else "#6d28d9"
            dia_p = Paragraph(f"<font color='{speaker_color}'><b>{speaker}:</b></font> \"{text}\"", dialogue_body)
            if sub:
                sub_p = Paragraph(f"<i>[Subtitles: {sub}]</i>", dialogue_sub)
                body_items.append([[dia_p, sub_p]])
            else:
                body_items.append([dia_p])

        # Tech Cue
        if tech_cue_text:
            tc = [
                Paragraph("<b>YD TECHNICAL NARRATION (Voiceover — Explaining System Intelligence):</b>", tech_cue_title),
                Paragraph(f"\"{tech_cue_text}\"", tech_cue)
            ]
            body_items.append([tc])

        # UI Action
        if ui_cue_text:
            ui_box = [
                Paragraph("<b>UI SCREEN ACTION & ON-SCREEN GRAPHICS:</b>", ParagraphStyle("UIH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=colors.HexColor("#15803d"))),
                Paragraph(ui_cue_text, ParagraphStyle("UIB", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=10.5, textColor=colors.HexColor("#166534")))
            ]
            body_items.append([ui_box])

        body_table = Table(body_items, colWidths=[510], style=[
            ("BACKGROUND", (0,0), (-1,-1), colors.white),
            ("BOX", (0,0), (-1,-1), 1, c_border),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ])
        content.append(body_table)
        content.append(Spacer(1, 10))
        return KeepTogether(content)

    # SCENE 1
    story.append(make_scene_block(
        "SCENE 1", "THE CHALKBOARD IN THE SHED — THE PROBLEM", "0:00 - 0:28",
        "Golden morning mist over Faridpur village, Bulandshahr, UP. Patty stands near aluminum milk cans, holding a worn Hindi diary filled with scribbled additions, scratched-out loan estimates, and question marks.",
        [
            ("PATTY", "Doodh toh yahan aas-paas kaafi mil jaata hai... market mein paneer aur chaach ki demand bhi zabardast hai. Lekin processing unit lagane mein kitna paisa lagega? Bank loan dega ya form reject kar dega? Aur agar unit laga li... toh ye dhandha sach mein chalega ya doob jaayega?",
             "Milk is plentiful here, and demand for paneer is huge. But how much capital is needed? Will the bank approve a loan or reject it? And even if I set it up... will this business actually survive or sink?")
        ],
        "For Patty, the obstacle isn't ambition or hard work. The obstacle is the chasm between raw intent and institutional feasibility. In rural India, over 80% of micro-enterprises collapse not from lack of effort, but from unvalidated market math and rejected bank appraisals.",
        "Camera zooms into Patty's notebook: 'Machinery: ₹4 Lakh? Loan: ?? Bank interest: ??'. Cut to black."
    ))

    # SCENE 2
    story.append(make_scene_block(
        "SCENE 2", "ARRY ENTERS — BEYOND GUESSWORK", "0:28 - 0:50",
        "Rural tea stall. Arry walks in holding a smartphone, glancing at Patty's scribbled notebook with an affectionate smile.",
        [
            ("ARRY", "Patty, dhandhe ka idea toh solid hai. Lekin 2026 mein bhi kismat aur guesswork ke bharose dhandha shuru karega kya?", "Patty, your idea is solid. But in 2026, will you still gamble your savings on guesswork?"),
            ("PATTY", "Toh aur kya karun Arry? Shahar ke CA aur consultant bees hazar rupaye maang rahe hain bas ek project report banane ke!", "What else can I do Arry? City consultants are demanding ₹20,000 just to write a project report!"),
            ("ARRY", "Kisi ke aage haath jodne ki zaroorat nahi hai. Pehle zameen ki haqeeqat aur financial feasibility check kar... Udyam Saathi se.", "No need to beg anyone. First check the ground reality and financial feasibility... with Udyam Saathi.")
        ],
        None,
        "Arry taps his smartphone. Smooth 3D zoom into the Udyam Saathi web application interface. Sovereign emblem, tricolor accent, and crisp light glassmorphism portal appears."
    ))

    # SCENE 3
    story.append(make_scene_block(
        "SCENE 3", "MEETING MIRA & THE 7-STEP FEASIBILITY WIZARD", "0:50 - 1:30",
        "Screen recording of Udyam Saathi. The floating light-glassmorphic voice widget activates with a soft chime. The circular Mira avatar appears with her tricolor dupatta, surrounded by glowing cyan audio-reactive rings.",
        [
            ("MIRA (Voice AI)", "Namaste Patty! Udyam Saathi mein aapka swagat hai. Kahiye, aap kis vyavasay ke baare mein sochna chahte hain?", "Greetings Patty! Welcome to Udyam Saathi. Tell me, which enterprise are you planning?"),
            ("PATTY", "Mira, mujhe Faridpur mein ek chhota dairy processing unit lagana hai, jismein roz paanch sau litre doodh se paneer aur ghee ban sake.", "Mira, I want to set up a small dairy processing unit in Faridpur to process 500 litres of milk daily into paneer and ghee.")
        ],
        "Notice what doesn't happen. Patty isn't forced to navigate 15 cluttered government dropdowns or decipher accounting terminology. Udyam Saathi's 7-Step Feasibility Wizard structures his natural speech directly into a standardized enterprise parameter model.",
        "7-Step Wizard animates smoothly: Step 1 Profile (Dairy Processing) → Step 2 Location (Faridpur, Bulandshahr, UP) → Step 3 Capacity (500 L/Day) → Step 4 Outlay (₹6,00,000) → Step 5 Margin Capital (₹60,000 / 10%) → Step 6 Category (OBC Rural Male) → Step 7 Infra (Grid Power Available)."
    ))

    # SCENE 4
    story.append(make_scene_block(
        "SCENE 4", "HYPER-LOCAL CATCHMENT INTELLIGENCE & DEMOGRAPHICS", "1:30 - 2:10",
        "Dashboard switches to Tab 2 (Demographics) & Tab 3 (Ecosystem). Interactive geospatial map centers on Bulandshahr district, rendering concentric 5km, 10km, and 15km catchment circles around Faridpur.",
        [
            ("PATTY", "Arry dekh! Isne mere gaon Faridpur aur aas-paas ke das gaon ka pura hisaab nikaal diya!", "Look Arry! It has analyzed Faridpur and ten surrounding villages!"),
            ("ARRY", "Kyunki ye hawa mein baat nahi karta. Iske paas Government of India ka official Census data aur 613 gaon ke resources ka seedha access hai.", "Because it doesn't talk in thin air. It has direct access to Government of India Census data and 613 village amenities.")
        ],
        "A rural enterprise never succeeds in isolation. Udyam Saathi takes Census 2011 baseline data and dynamically projects the 2026 catchment population—in Patty's case, 600,241 citizens across the rural block. It queries Data.gov.in's 613 Village Amenities registry, computing an Infrastructure Score of 5.8/10, a local MSME density of 2.81 per 10,000 people, and a Total Addressable Market of ₹32.4 Crores.",
        "Visual callout on TAM/SAM/SOM Funnel: TAM: ₹32.4 Cr → SAM: ₹4.8 Cr → SOM: ₹72 Lakhs. ODOP Registry Badge: 'Bulandshahr: Dairy & Ceramic Cluster'. Amenities Radar: Power 18 hrs/day, Paved Road 88%."
    ))

    story.append(PageBreak())

    # SCENE 5
    story.append(make_scene_block(
        "SCENE 5", "THE DETERMINISTIC FINANCIAL ENGINE — ZERO GUESSWORK", "2:10 - 2:50",
        "Dashboard moves to Tab 4 (Financial Projections). Dynamic charts assemble: 5-Year P&L, Monthly Cash Flow waterfall, Break-Even volume curve, and the circular Debt Service Coverage Ratio (DSCR) gauge.",
        [
            ("PATTY", "Dekh Arry, har mahine kitna doodh khareedna padega, kitna bijli aur packaging ka kharcha hoga... sab saaf-saaf likha hai.", "Look Arry, how much milk to buy every month, power, packaging costs... everything is clearly itemized.")
        ],
        "Pay close attention here. These financial models are NOT generated as hallucinated guesswork by an LLM. Udyam Saathi executes a deterministic, zero-hallucination financial engine: Capex is pegged at ₹6,00,000, monthly operating expenses at ₹48,500, break-even is reached at month 7 with 42% capacity utilization, and the DSCR is mathematically computed down to the paisa. AI should summarize financial truth, never invent it.",
        "Close-up on the DSCR Gauge: Needle settling on 1.45 (VIABLE) with emerald glow. Monthly EMI calculated: ₹8,137 / month. CPI-Adjusted Price Floor: ₹320 / kg paneer (factoring in 4.2% local inflation)."
    ))

    # SCENE 6
    story.append(make_scene_block(
        "SCENE 6", "SUPERVISED XGBOOST ML & TREESHAP EXPLAINABILITY", "2:50 - 3:30",
        "Dashboard shifts to Tab 1 (Executive Summary). The Viability Meter displays an ML inference output accompanied by a TreeSHAP waterfall attributing exact feature contributions.",
        [
            ("PATTY", "Isne likha hai 'SUITABLE' (उपयुक्त)... aur 95.6% confidence score! Lekin ye meter kaam kaise karta hai?", "It says 'SUITABLE'... with a 95.6% confidence score! But how does this meter work?")
        ],
        "Instead of an arbitrary prompt asking an AI 'is this business good?', Udyam Saathi extracts a 10-dimensional feature vector—combining DSCR, infrastructure score, competitor density, weather vulnerability, and TAM—and passes it through a trained XGBoost Viability Classifier. TreeSHAP then unpacks the exact math: Patty's low debt burden and high local TAM pushed him into 'SUITABLE', while cold storage scarcity was flagged as a manageable risk.",
        "Viability Meter Card: Badge: 'SUITABLE' (95.6% Confidence). TreeSHAP Waterfall: +0.32 High Local TAM, +0.25 Viable DSCR (1.45), -0.12 Cold Chain Deficit (Risk Drag)."
    ))

    # SCENE 7
    story.append(make_scene_block(
        "SCENE 7", "SOVEREIGN GOVERNMENT SCHEME MATCHING", "3:30 - 4:10",
        "Dashboard moves to Tab 5 (Government Schemes). 17 Central and State MSME schemes evaluated in real-time. Cards for PMEGP, PMFME, and Mudra Shishu/Kishore appear with exact subsidy numbers.",
        [
            ("PATTY", "Chheh lakh mein se main toh bas saath hazar arrange kar sakta hoon. Baaki paanch lakh chaalees hazar kahan se aayega?", "Out of ₹6 Lakhs, I can only arrange ₹60,000. Where will the remaining ₹5,40,000 come from?"),
            ("ARRY", "Yahi toh jaadu hai Udyam Saathi ka. PMEGP scheme dekh!", "That's the power of Udyam Saathi. Look at the PMEGP scheme!")
        ],
        "Udyam Saathi matches Patty's rural location and OBC category against the Prime Minister's Employment Generation Programme (PMEGP). The system automatically unlocks a 35% capital subsidy—₹2,10,000 non-repayable grant. Patty's personal equity is just ₹60,000 (10%), leaving an effective bank loan of ₹3,30,000 with Mudra/CGTMSE collateral-free backing.",
        "PMEGP Top Scheme Card: Outlay: ₹6,00,000 • Own Equity: ₹60,000 (10%) • Subsidy Grant: ₹2,10,000 (35%) • Effective Loan: ₹3,30,000 • Collateral: 100% Free under CGTMSE."
    ))

    # SCENE 8
    story.append(make_scene_block(
        "SCENE 8", "THE PIVOT GUARANTEE — WHAT IF A BUSINESS IS AT RISK?", "4:10 - 4:45",
        "Split-screen visualization showing a rejected enterprise scenario versus Udyam Saathi's Opportunity Matcher modal.",
        [],
        "What happens when a farmer proposes a saturated business—like a retail cement depot in an area with 15 competitors and a DSCR of 0.82? Udyam Saathi doesn't just display a cold red 'REJECTED' stamp. Our Opportunity Matcher—powered by Sarvam-105b and a 16-sector deterministic archetype catalog—instantly evaluates the applicant's capital and district infrastructure, recommending viable alternative pivots such as Vermicompost Production or Drone Custom Hiring with positive credit profiles.",
        "Opportunity Matcher Modal: 1. Vermicompost & Organic Fertilizer Unit (Outlay: ₹3,50,000, 35% PMEGP Subsidy, 88% Match) • 2. Agri-Drone Custom Hiring Centre (Outlay: ₹5,00,000, High District Affinity)."
    ))

    story.append(PageBreak())

    # SCENE 9
    story.append(make_scene_block(
        "SCENE 9", "INSTANT BANK-READY 7-SECTION DPR COMPILATION", "4:45 - 5:25",
        "Patty clicks 'Generate Bank DPR'. An assembly animation compiles all feasibility data into a formal PDF Bank Credit Appraisal Memorandum.",
        [
            ("PATTY", "Arry... ye toh pura bank ka official project report taiyaar ho gaya! Ismein P&L, balance sheet, subsidy code, compliance checklist... sab kuch hai!", "Arry... this has generated a complete official bank project report! It has P&L, balance sheet, subsidy codes, compliance checklist... everything!")
        ],
        "From a raw, handwritten notebook idea to a 7-Section Bank Appraisal Memorandum in under 10 seconds. Formatted strictly to SIDBI and RBI rural credit appraisal guidelines, ready to be handed directly to a State Bank of India or PNB branch manager. No middlemen, no ₹20,000 consultant fees.",
        "Document Preview: Report ID 'REP-59CB6C3533'. 7 Sections: 1. Executive Summary • 2. Promoter Profile • 3. Market Demographics • 4. Technical Feasibility • 5. 5-Year Financials • 6. PMEGP Subsidy • 7. Statutory Checklist."
    ))

    # SCENE 10
    story.append(make_scene_block(
        "SCENE 10", "MULTILINGUAL AI VOICE AGENT — LIVE DASHBOARD CONTROL", "5:25 - 6:05",
        "Patty taps the floating light-glassmorphic Mira widget. Mira's avatar pulses with emerald acoustic waves as she speaks and navigates the live dashboard.",
        [
            ("PATTY", "Mira, mera loan chukta karne mein kitne mahine lagenge aur break-even kab aayega?", "Mira, how many months will it take to repay my loan and when will break-even occur?"),
            ("MIRA (Voice AI)", "Patty ji, main aapko financial projections tab par le aayi hoon. PMEGP subsidy ke baad aapka bank loan teen lakh tees hazar rupaye bachega. Saatven mahine mein aapka break-even ho jaayega, aur pandrah hazar rupaye mahina bachat ke saath aap chaar saal mein loan poora chukta kar sakte hain.",
             "Patty ji, I have navigated you to the financial projections tab. After PMEGP subsidy, your bank loan will be ₹3,30,000. You will reach break-even in month 7, and with ₹15,000 monthly savings, clear the loan in 4 years.")
        ],
        "Observe the technical synergy: Patty spoke in colloquial Hindi. Sarvam AI auto-identified the language code in 540ms. Bhashini transcribes the speech. Sarvam-105b executes an autonomous function call navigate_to_tab('financial_projections') while synthesizing a conversational, zero-exclamation response. Bhashini TTS reads out the full multi-sentence explanation. Voice and UI act as a single living organism.",
        "UI triggers navigate_to_tab('financial') autonomously. Mira's halo pulses emerald green. Chat history updates synchronously."
    ))

    # SCENE 11
    story.append(make_scene_block(
        "SCENE 11", "RESOLUTION & CLIMAX — FROM DREAMER TO FUNDED ENTREPRENEUR", "6:05 - 6:35",
        "Patty stands proudly outside his dairy unit. A printed copy of the Udyam Saathi Detailed Project Report with an SBI branch seal is visible on the table behind him. He smiles with deep confidence.",
        [
            ("ARRY", "Toh Patty... ab kya karega?", "So Patty... what will you do now?"),
            ("PATTY", "Ab kismat ke bharose guess nahi karunga. Pehle Udyam Saathi se samjhunga. Phir plan karunga. Phir shuru karunga!", "Now I won't guess on luck. First I will understand with Udyam Saathi. Then I will plan. Then I will launch!")
        ],
        "63 million micro-enterprises form the backbone of Indian commerce. They don't lack work ethic—they lack structured institutional feasibility. Udyam Saathi transforms rural ambition into bankable, grounded, and resilient reality.",
        "Final Title Card: UDYAM SAATHI (उद्यम साथी) • AI-Driven Hyper-Local Business Advisory & Financial Structuring Platform • Ministry of MSME • Smart India Hackathon 2026."
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 3: TAB-BY-TAB COMPREHENSIVE ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("3. In-Depth Dashboard Tab-by-Tab Architecture & UI Guide", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_navy, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Every tab in Udyam Saathi corresponds to an isolated, verifiable layer in the credit appraisal pipeline. "
        "The guide below outlines the exact datasets, mathematical models, UI visual components, and demo presentation cues for each tab:",
        body_style
    ))

    tabs_data = [
        [
            Paragraph("<b>Tab & Route</b>", table_header),
            Paragraph("<b>Core Mathematical / AI Engine</b>", table_header),
            Paragraph("<b>Key UI Components & Visuals</b>", table_header),
            Paragraph("<b>Demo Speaking Cue (Why it Matters)</b>", table_header)
        ],
        [
            Paragraph("<b>Tab 1:<br/>Executive Summary</b><br/><code>/summary</code>", table_cell),
            Paragraph("<b>Supervised XGBoost Classifier</b> (10-D vector) + <b>TreeSHAP Explainer</b>. Evaluates DSCR, infra score, density, TAM, weather risk, inflation, outlay, and margin.", table_cell),
            Paragraph("• Viability Meter (`SUITABLE`, `CAUTION`, `RECONSIDER`)<br/>• Confidence % (e.g. 95.6%)<br/>• TreeSHAP Waterfall bars<br/>• AI synthesis summary", table_cell),
            Paragraph("<i>\"Judges will note this score is NOT an LLM guess. It is an auditable ML model trained on MSME credit datasets.\"</i>", table_cell)
        ],
        [
            Paragraph("<b>Tab 2:<br/>Demographics & TAM</b><br/><code>/demographics</code>", table_cell),
            Paragraph("<b>Census 2026 Demographic Engine:</b> Compounds Census 2011 baseline data across 5km, 10km, and 15km catchment radii to compute population, households, and TAM.", table_cell),
            Paragraph("• TAM / SAM / SOM Funnel Chart<br/>• Catchment Population: 600,241<br/>• TAM: ₹32.4 Crores<br/>• Rural / Urban split breakdown", table_cell),
            Paragraph("<i>\"Bankers reject loans when market sizing is absent; Udyam Saathi grounds demand in official Census data.\"</i>", table_cell)
        ],
        [
            Paragraph("<b>Tab 3:<br/>Ecosystem & Infra</b><br/><code>/ecosystem</code>", table_cell),
            Paragraph("<b>Data.gov.in 613 Amenities Index</b> (Mission Antyodaya OGD API) + <b>ODOP Registry</b> + MSME District Density calculation.", table_cell),
            Paragraph("• 6-Axis Infra Radar (Power, Roads, Banking, Water)<br/>• Competitor Density: 2.81/10k pop<br/>• ODOP Product Match Badge", table_cell),
            Paragraph("<i>\"A dairy needs power. The system confirms Faridpur receives 18 hrs/day grid electricity before recommending machinery.\"</i>", table_cell)
        ],
        [
            Paragraph("<b>Tab 4:<br/>Financial Projections</b><br/><code>/financial</code>", table_cell),
            Paragraph("<b>Deterministic Banking Math:</b> Reducing balance EMI formula, 5-year cash flows, DSCR = Net Operating Income / Debt Service, Break-even volume.", table_cell),
            Paragraph("• Circular DSCR Gauge (1.45 Viable)<br/>• 5-Year P&L Statement<br/>• Break-Even Curve (Month 7, 42% cap)<br/>• Monthly EMI: ₹8,137", table_cell),
            Paragraph("<i>\"DSCR is the gold standard of credit appraisal. Above 1.30, banks know the loan will be serviced cleanly.\"</i>", table_cell)
        ],
        [
            Paragraph("<b>Tab 5:<br/>Govt Schemes</b><br/><code>/schemes</code>", table_cell),
            Paragraph("<b>17-Scheme Rule Engine:</b> Matches PMEGP, PMFME, Mudra (Shishu, Kishore, Tarun), Stand-Up India, and CGTMSE by category, location, and outlay.", table_cell),
            Paragraph("• Top Scheme Card: PMEGP 35% Grant<br/>• Capital Stack: ₹60k Equity + ₹2.1L Subsidy + ₹3.3L Bank Loan<br/>• Alternative Scheme comparison", table_cell),
            Paragraph("<i>\"Shows how subsidies transform Patty's capital hurdle from ₹6 Lakhs down to just ₹60,000 personal savings.\"</i>", table_cell)
        ],
        [
            Paragraph("<b>Tab 6:<br/>SWOT & Risk Engine</b><br/><code>/swot</code>", table_cell),
            Paragraph("<b>Hybrid Deterministic + AI SWOT:</b> Mathematical metric thresholds seed the baseline quadrants, enriched by Sarvam-105b without hallucinating numbers.", table_cell),
            Paragraph("• 4-Quadrant Grounded SWOT<br/>• Weather/Climate Risk: 0.20<br/>• Local Inflation Indexation: 4.2%<br/>• Actionable Risk Mitigation Cards", table_cell),
            Paragraph("<i>\"Not a generic SWOT. It specifically cites Bulandshahr's dairy density and cold storage deficit.\"</i>", table_cell)
        ],
        [
            Paragraph("<b>Tab 7:<br/>Bank DPR Memo</b><br/><code>/dpr</code>", table_cell),
            Paragraph("<b>DPR Memorandum Compiler:</b> Structures all feasibility data into a 7-section institutional bank credit memorandum adhering to RBI/SIDBI norms.", table_cell),
            Paragraph("• 7 Formal Bank Sections<br/>• Auditable Report ID: `REP-XXXXXX`<br/>• 1-Click PDF Export with institutional watermark and seal", table_cell),
            Paragraph("<i>\"The climax of the journey. A rural entrepreneur walks into SBI with the exact document the branch manager needs.\"</i>", table_cell)
        ]
    ]

    tabs_table = Table(tabs_data, colWidths=[90, 140, 140, 140], style=[
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ("BOX", (0,0), (-1,-1), 1, c_border),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
    ])
    story.append(tabs_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 4: TECHNICAL ARCHITECTURE & PRODUCTION GUIDE
    # =========================================================================
    story.append(Paragraph("4. Technical Architecture & Video Production Guide", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_navy, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("End-to-End Voice & Intelligence Architecture Flow", h2_style))

    arch_flow_data = [
        [
            Paragraph("<b>Step 1: Input</b><br/>Patty speaks in colloquial Hindi into smartphone mic.", table_cell),
            Paragraph("<b>Step 2: Detect</b><br/>Sarvam Saaras STT auto-identifies language code (<code>hi-IN</code>) in 540ms.", table_cell),
            Paragraph("<b>Step 3: ASR</b><br/>Bhashini ULCA Indic pipeline transcribes speech with zero data leakage.", table_cell)
        ],
        [
            Paragraph("<b>Step 4: LLM & Tools</b><br/>Sarvam-105b-conversations parses intent, executes tool calls, and formulates response.", table_cell),
            Paragraph("<b>Step 5: Math Core</b><br/>Deterministic engine computes Capex, DSCR, and PMEGP subsidy invariants.", table_cell),
            Paragraph("<b>Step 6: Voice TTS</b><br/>Bhashini TTS synthesizes full multi-sentence natural Indic speech.", table_cell)
        ]
    ]
    arch_table = Table(arch_flow_data, colWidths=[170, 170, 170], style=[
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ])
    story.append(arch_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Director's Shooting & Editing Blueprint", h2_style))

    prod_data = [
        [
            Paragraph("<b>Production Element</b>", table_header),
            Paragraph("<b>Director's Directive & Execution Guidance</b>", table_header),
            Paragraph("<b>Aesthetic & Technical Standards</b>", table_header)
        ],
        [
            Paragraph("<b>Cinematography & Lighting</b>", table_cell),
            Paragraph("Scene 1 uses warm, natural rural morning light (golden hour) to evoke authentic village life. UI scenes transition into crisp, high-tech, modern daylight illumination.", table_cell),
            Paragraph("Contrast rustic village textures (milk cans, wood, earth) with the sleek, clean, light-glassmorphic UI.", table_cell)
        ],
        [
            Paragraph("<b>Music & Sound Design</b>", table_cell),
            Paragraph("Begins with a gentle acoustic guitar and bansuri (flute) melody. As Udyam Saathi activates in Scene 3, blend in a modern, pulsating ambient tech synthesizer.", table_cell),
            Paragraph("Build into an inspiring, confident orchestral swell during Scene 9 (DPR compilation) and Scene 11 (Resolution).", table_cell)
        ],
        [
            Paragraph("<b>Voiceover Delivery Style</b>", table_cell),
            Paragraph("Patty speaks in natural, grounded Western UP Hindi. Arry speaks in modern, energetic Hinglish. Mira speaks in warm, didi-like Hindi. YD speaks in authoritative, polished documentary English.", table_cell),
            Paragraph("YD never narrates obvious button clicks; YD interprets <i>why the math and sovereign architecture matter</i>.", table_cell)
        ],
        [
            Paragraph("<b>Screen Recording</b>", table_cell),
            Paragraph("Record all UI screens at 4K resolution (3840x2160) at 60 FPS. Use smooth, deliberate cursor movements with subtle motion blur.", table_cell),
            Paragraph("Execute smooth digital zooms onto the DSCR gauge needle, TreeSHAP waterfall bars, and Mira's audio-reactive pulsing avatar.", table_cell)
        ],
        [
            Paragraph("<b>Callout Graphics & Overlays</b>", table_cell),
            Paragraph("Display sleek, semi-transparent pill badges on the screen as YD speaks to reinforce technical credibility for evaluators.", table_cell),
            Paragraph("Badges: <code>[Census 2026 TAM Formula]</code>, <code>[XGBoost 10-D Classifier]</code>, <code>[Data.gov.in 613 Amenities]</code>, <code>[Deterministic Math - Zero Guesswork]</code>.", table_cell)
        ]
    ]

    prod_table = Table(prod_data, colWidths=[105, 235, 170], style=[
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ("BOX", (0,0), (-1,-1), 1, c_border),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ])
    story.append(prod_table)
    story.append(Spacer(1, 14))

    # Final Closing Note
    closing_p = Paragraph(
        "<b>SUMMARY FOR SMART INDIA HACKATHON (SIH) 2026:</b><br/>"
        "By grounding the presentation in the lived reality of <b>Patty</b>, guided by <b>Arry</b>, interfaced through <b>Mira</b>, "
        "and technically proven by <b>YD</b>, the video elevates Udyam Saathi from a conventional software submission into a "
        "compelling, institutional-grade national initiative for India's 63 million micro-enterprises.",
        body_style
    )
    story.append(Table([[closing_p]], colWidths=[510], style=[
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#86efac")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
    ]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF build successful:", filename)

if __name__ == "__main__":
    build_pdf()
