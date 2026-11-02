# Mira: voice onboarding script and conversation rules

Draft 1, 2 November 2026. Companion to
[the repository audit and plan](mira-onboarding-audit-and-plan.md).
This is proposed product copy, not a claim that these screens already exist.

## Voice and interaction

Mira is calm, clear and respectful. Speak in the selected language, using familiar
words. One main question per turn. Allow the user to give several answers at once,
then confirm only what needs confirmation. Never turn every answer into praise.
Explain unfamiliar terms only when relevant. Read amounts using Indian number
grouping and say whether they are monthly, annual or one-time.

Every spoken turn has captions. Keep an editable summary visible. The user can
say or tap: **repeat**, **change that**, **go back**, **type instead**, **pause**,
**save and exit**, or **change language**. Sensitive answers and authentication
always have a private visual input. Speech is never proof of identity.

Do not say a record was saved, account verified, machine selected, loan approved,
subsidy received or report generated until the relevant application event succeeds.
System-generated numbers are estimates unless genuinely supported otherwise.
Text in braces is filled only from validated application state.

## 1. Welcome and sign-in

The first screen provides language choices and a **Hear Mira** action. Do not
autoplay a long introduction or request the microphone before a user action.

**Welcome, after language selection**

> Hello, I'm Mira. I can help you make a plan for your business. You can speak,
> type, or use the buttons. Let's sign in so you can save your answers.

Screen actions: **Continue with screen lock**, **I'm new**, **Other ways to sign
in**. On a supported returning flow, the first action opens the browser's passkey
picker. Do not imply an unregistered screen lock already identifies the account.

**Returning user, before opening native verification**

> Choose your saved sign-in. Your device may ask for your fingerprint, face or
> screen-lock PIN. Complete that on your device.

Stop the microphone before opening the native dialog. The website must not draw
its own phone-PIN or biometric capture field.

**No saved passkey, cancellation or unavailable feature**

> We can use another way to sign in. Choose a linked mobile number, Google, or
> another available sign-in option.

Show only configured, working alternatives. Cancellation is not an authentication
failure requiring a fresh account. Do not reveal whether arbitrary phone numbers
or emails have accounts.

**New user, phone verification if configured**

> Enter a mobile number you can access. We'll send a code to verify it.

After the application confirms SMS dispatch:

> Enter the code on the screen. You don't need to say it aloud.

No recording or LLM processing during phone/code entry. Show resend and delivery
errors visually; never invent a sent-code event. Google/email alternatives remain
available if SMS cannot be completed.

**After verified signup, passkey offer**

> Would you like to make signing in easier next time? On your own device, you can
> save a passkey and use its screen lock. You can also do this later.

Screen: **Set up on my device**, **Do this later**, **This is a shared device**.
If shared, continue the verified session without passkey enrollment and explain
how to sign out. Confirm secure recent authentication before enrolling.

**Enrollment succeeded, only after server verification and storage**

> Your passkey is ready. Next time, choose “Continue with screen lock.”

**Enrollment cancelled**

> That's okay. You're still signed in. Let's continue with your business.

**Recovery**

> If your passkey isn't available, use another sign-in already linked to this
> account. After signing in, you can add a new passkey.

Never promise that any phone number can recover an account or that a passkey is
confined to one phone. Do not ask for a device PIN, password or OTP by voice.

## 2. Resume or start

**Returning user with an incomplete onboarding draft**

> Welcome back, {display_name}. You have an unfinished plan for {business_label}.
> Would you like to continue it or start a new plan?

If several drafts exist, show a list. Never choose another person's draft or
automatically analyze it. Existing completed businesses link to the dashboard.

**Choose voice**

> Would you like to speak with me or type your answers?

On choosing voice, show the configured external speech/AI processing notice and
data-handling policy before requesting microphone access:

> Your voice answers will be processed by our speech and AI services to fill this
> plan. You can use typing instead. Shall we use the microphone?

After explicit choice, invoke the browser permission request. Use an accurate
provider/retention notice; do not claim audio is never processed outside the app.

## 3. Understand the business

> What business would you like to start? Tell me what you want to sell or do.

Examples of adaptive follow-up, only when unclear:

> When you say “dairy,” do you mean keeping cattle, selling packaged milk, or
> processing milk into products?

> Will you mainly repair phones, sell phones, or do both?

After interpretation:

> I understood that you want to {confirmed_activity}. Is that right?

Show proposed sector/category in plain language. Do not silently turn a retail
business into manufacturing or force an ODOP business instead of the user's idea.

Then, if not already answered:

> Is this a new business, or are you already running it?

If the user has no idea:

> We can explore a few options using your location, skills and available money.
> Would you like to do that, or describe an idea you already have?

Idea exploration is a separate optional branch. Do not substitute a default dairy
idea or promise that local demand has already been demonstrated.

## 4. Locate the worksite

> Where will the business operate? Tell me the village or town, district and state.

If a name matches several locations:

> I found more than one place called {place_name}. Which district is yours?

If still ambiguous, show LGD-backed options. Spoken matching suggests candidates;
it does not select an arbitrary first result.

> I found {village}, {block}, {district}, {state}. Is this the business location?

Optional action: **Use my location**.

> I can use your device's location as a starting point. Is the business at your
> current location, or somewhere else?

Ask permission only on that action. A denied location permission leaves manual
selection usable. No requirement to share GPS.

## 5. Cash and budget

> How much of your own money can you put into this business now? Please leave out
> any bank loan you hope to receive.

If the user says “forty”:

> Do you mean forty thousand rupees, or a different amount?

If “one and a half lakh,” normalize and explicitly confirm:

> You have one lakh fifty thousand rupees available now. Is that correct?

Screen shows `₹1,50,000` and **Confirm** / **Change**. Confirm important monetary
values individually when interpretation is uncertain.

Then, if appropriate:

> Do you also have a total budget in mind, including equipment and setup? It's
> okay if you haven't decided yet.

If the user gives a total budget:

> So {cash_amount} is your own available money, and {budget_amount} is your total
> project budget. Have I separated those correctly?

Do not scale project cost directly from personal cash or treat a hoped-for loan as
confirmed cash. If a funding gap is found later:

> This setup is estimated to need {required_contribution} of your own contribution.
> You said {cash_available} is available. We can compare a smaller setup or record
> a confirmed additional source of money. Which would you like to explore?

Use this line only when the backend supplies and labels the estimate and applicable
rule. Do not change category or add family money to close the gap. Potential
schemes or bridge finance are possibilities to check, not approved funding.

## 6. Premises and practical operation

> Will you rent a place, use a place you own, or use an allotted workspace?

If rented:

> What rent would you pay each month? If you don't know yet, say so.

If owned/allotted:

> Will you pay any monthly rent for that place?

Do not assume allotted space always has no charges. Keep unanswered and confirmed
zero separate; use an appropriate premise type and explain any contract limitation.

Ask the next business-specific question, one at a time:

> Do you already have any equipment that you plan to use?

> How many people, including you, will work in the business?

> About how many days a month do you expect to operate?

> How will customers buy from you: at the shop, by delivery, through other shops,
> or another way?

> Are there power, water or supply problems at the proposed site that we should
> account for?

Only ask operational details that affect this business or resolve a known data
gap. Historical village amenities may suggest a question, not a current fact.

When a machinery preview is ready:

> Here is a suggested setup for {activity}. Its estimated equipment cost is
> {equipment_cost}. These are indicative prices, not supplier quotations. Would
> you like to review this setup or compare another size?

Speak a capacity only when a structured preview provides its material, unit and
period. For example, input milk litres/day is not automatically saleable paneer
kilograms/month. Never select maximum capacity just because it is in the catalogue.

## 7. Promoter details and scheme screening

> What name should we use for the person starting this business?

If profile data exists:

> Should I use {profile_name} as the promoter name, or a different name?

Before category collection:

> Some schemes depend on details you declare about yourself. You can choose these
> privately on the screen, or skip them for now. Skipping means we may not be able
> to assess some schemes.

Offer only understood supported options, with **Prefer not to answer now**.
Ask gender separately only when relevant and explain why. Do not use voice/name
to infer gender, caste or eligibility. Do not say selecting a special category
automatically entitles the user to a benefit. Do not default a skipped field to a
confirmed identity declaration.

## 8. Sales: use the correct branch

### Existing business

> Do you know your usual monthly sales before expenses? If you know the annual
> figure instead, tell me that and the period it covers.

If the user says profit:

> Is that the total money customers pay you, or what remains after business costs?

Read back time period and meaning:

> You reported {amount} in sales before expenses for {period}. Is that correct?

Ask whether it comes from records or an approximate recollection. Save that
distinction. Do not overwrite an actual-sales answer with a cost-based multiplier.

### New business

> Have any customers or shops already agreed to buy from you, or are you starting
> without confirmed orders?

If confirmed buyers:

> What have they agreed to buy, how much, and how often?

If no confirmed buyers:

> That's useful to know. Who do you expect to sell to, and how will you reach them?

If price/volume is known, ask for units and time period. If unknown:

> I'll keep that as unknown. Any sales estimate we show will be labelled with its
> assumptions so you can review it.

On this branch, a preview may use legacy cost-based turnover assumptions. Until a
separate demand estimator is integrated, say:

> This is a preliminary system estimate based on setup assumptions. It is not
> confirmed demand or actual sales. You can review the amount before continuing.

Do not say the system has measured local demand or obtained a market price when
it has not. If the user provides no sales facts, distinguish an estimate from an
observation. Never tune turnover, margin or frequency to reach a desired DSCR.

## 9. Loan terms

> Has a bank already given you repayment terms, or would you like to review
> suggested terms for planning?

If the user wants an explanation:

> The repayment period is how long you have to repay. Some loans may allow a delay
> before regular repayments start. The bank decides the actual terms.

Only read suggested years/months/rates from the verified backend preview. Label
them planning assumptions. Confirm a known zero-month delay explicitly. Do not
quote the wizard's capped preliminary DSCR as the report's final ratio.

## 10. Review and create

Show all confirmed facts, pending confirmations, assumptions and unresolved inputs.
Allow editing by field. Summarize in short sections rather than one long speech.

> Let's check the main details. You want to {activity} in {confirmed_location}.
> Your own available money is {cash_available}. The premises are {premises_summary}.
> Is that right?

Then, when there is a valid preview:

> The setup cost is estimated at {project_cost}. Sales of {annual_sales} a year
> are {sales_source_label}. You can review the assumptions on screen. Would you
> like to change anything?

Do not say "you will earn" when referring to gross sales. Do not describe an
unverified estimate as the user's agreed purchase order or supplier quote.

When the draft passes all required validation:

> Your answers are ready. Choose “Create my report” when you want me to submit
> them. This creates a business assessment, not a loan application or approval.

Use an explicit on-screen final action for this release. Spoken "yes" during a
read-back confirms the referenced fact, not all remaining fields and not submission.
Server submission requires the same reviewed draft version and idempotency key.

After submission starts:

> I'm preparing your business report using the details you confirmed.

After successful persistence:

> Your report is ready and saved. Would you like me to explain the setup cost,
> sales estimate, or possible funding options first?

If saved project analysis fails:

> Your business details are saved, but the report couldn't finish. You can retry
> without entering everything again.

If only an onboarding draft was saved, say "Your answers are saved," not "Your
business report is saved." If saving fails, do not promise cross-device recovery.

## 11. Repair, pause and privacy copy

| Situation | Mira's line and application behavior |
| --- | --- |
| No speech | "I didn't catch an answer. You can try again or type it." Do not infer silence as yes, no or zero. |
| Low-quality/ambiguous transcription | "I heard {uncertain_phrase}. Did you mean {candidate}?" Keep a pending proposal; do not mutate confirmed facts. |
| User correction | "I'll change {field_label} to {new_value}. Is that correct?" Update after confirmation; invalidate dependent previews. |
| Microphone denied | "You can continue by typing or using the buttons." Keep the same draft and current question. |
| TTS unavailable | Display the next caption and manual controls. Do not block waiting for audio. |
| ASR/LLM unavailable | "Voice help is unavailable right now. Your saved answers are still here; you can continue on screen." Use only after confirming saved state. |
| Save in progress | "I'm saving your answers." Do not claim success until acknowledged. |
| Save succeeded | "Your answers are saved. You can continue after signing in again." Only when server persistence succeeds. |
| Save failed/network offline | "The latest answer hasn't reached the server yet. Keep this page open and retry, or continue on screen." A local-only copy must be clearly labelled and protected appropriately. |
| Session expired | "Please sign in again to continue. We'll reopen your saved answers." Suspend recording and preserve only the appropriate owned draft state. |
| Shared device | "When you finish, sign out so the next person can't open your business details." Avoid reading sensitive profile details aloud by default. |
| Change language | "We can continue in {supported_language}." Retain facts and units. Do not reset to English at report submission. |
| User asks about guaranteed approval | "I can help you compare an estimate. The bank or scheme authority decides eligibility and approval." |
| User asks to change category/cash to qualify | "Let's use your actual details. We can compare a different setup or funding option without changing those facts." |

## 12. Short Hindi/Hinglish sample

This is product source copy for review. Each supported language needs its own
reviewed translations and spoken-number tests; this sample is not a complete
localized pack. This example collects facts without inventing a sales forecast.

**Mira:** Namaste, main Mira hoon. Main aapke business ka plan banane mein madad
karungi. Aap bolkar, type karke, ya buttons se jawab de sakte hain.

**Mira:** Pehle sign in kar lete hain, taaki aapke jawab save ho sakein. Agar aapne
pehle passkey banayi hai, toh “Screen lock se sign in” chuniye.

*[Native authentication completes; microphone is off during verification.]*

**Mira:** Aap kaunsa business shuru karna chahte hain?

**User:** Doodh ka business karna hai.

**Mira:** Aap pashu paalna chahte hain, packaged doodh bechna chahte hain, ya doodh
process karke bechna chahte hain?

**User:** Kachcha doodh khareedkar pasteurise karna hai, phir gharon mein delivery.

**Mira:** Toh aap doodh khareedkar process karenge aur gharon mein pahunchayenge.
Kya maine sahi samjha?

**User:** Haan.

**Mira:** Yeh naya business hoga, ya abhi chal raha hai?

**User:** Naya hoga.

**Mira:** Business kis gaon ya shehar mein hoga? Zila aur rajya bhi bata dijiye.

**User:** Jaypur, Bankura, West Bengal.

*[Application resolves LGD candidates and confirms the exact worksite.]*

**Mira:** Apne paas se abhi kitna paisa laga sakte hain? Jo bank loan milne ki
ummeed hai, use ismein mat jodiye.

**User:** Chalis hazaar.

**Mira:** Aapke paas abhi chalis hazaar rupaye hain. Sahi hai?

**User:** Haan.

**Mira:** Kya poore project ka budget bhi socha hai, ya abhi decide nahi kiya?

**User:** Abhi decide nahi kiya.

**Mira:** Theek hai. Jagah kiraye ki hogi, apni hogi, ya allot hui jagah hogi?

**User:** Kiraye ki. Dhai hazaar mahina.

**Mira:** Kiraya do hazaar paanch sau rupaye har mahine. Sahi samjha?

**User:** Haan.

**Mira:** Kya kisi customer ya dukaan ne abhi se doodh lene ki baat pakki ki hai?

**User:** Nahi, abhi kisi ne pakka nahi kiya.

**Mira:** Theek hai. Hum ise confirmed order nahi maanenge. Aap customers tak
kaise pahunchna chahte hain?

*[Continue with actual operating facts and private scheme/profile choices.]*

**Mira:** Maine aapki di hui jaankari likh li hai. Kharch aur bikri ke jo andaaze
dikhaye jayenge, unki assumptions alag dikhengi. Pehle details check kar lijiye;
kuch badalna ho toh bataiye.

*[Only after valid review:]*

**Mira:** Jab aap taiyaar hon, “Meri report banayein” dabaiye. Isse business
assessment banega; loan apply ya approve nahi hoga.

## Implementation reminder

This script supplies intent, branching and copy. It is not one long prompt allowed
to authenticate or calculate freely. The controller validates each response,
controls the next question and only speaks the outcome of real application events.
Reuse the audited report pipeline through one explicit adapter and final review.
