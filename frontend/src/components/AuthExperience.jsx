import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Volume2, ShieldCheck, Sparkles } from 'lucide-react';
import { LanguageSelector } from './LanguageSelector';
import { useLanguage } from '../context/LanguageContext';

const copy = {
  en: { welcome: 'Welcome to Udyam Saathi.', subtitle: 'Mira will guide you, one simple step at a time.', register: 'Create your account', login: 'Welcome back', name: 'Your full name', phone: 'Mobile number', email: 'Email (optional)', code: '6-digit SMS code', send: 'Send verification code', verify: 'Verify and continue', resend: 'Send code again', skipEmail: 'Skip email', location: 'Detected location', locating: 'Finding your location…', locationLater: 'We will confirm your location with Mira later.', google: 'Continue with Google', evaluator: 'One-click evaluator access', passkey: 'Continue with Face ID / passkey', addPasskey: 'Set up Face ID / passkey', skipPasskey: 'I will do this later', password: 'Password', oldLogin: 'Use existing email and password', haveAccount: 'Already have an account?', newAccount: 'New here?', signIn: 'Sign in', create: 'Create account', passkeyReady: 'Your account is ready. Add a passkey for quick sign-in next time.', miraName: 'Mira, your guide', hear: 'Hear Mira', guideName: 'First, please enter your full name.', guidePhone: 'Now enter your 10-digit mobile number.', guideEmail: 'Add a contact email if you want, or skip this step.', guideCode: 'Enter the code sent to your phone.', guideLogin: 'Choose a passkey or enter your mobile number to sign in.', guidePasskey: 'Use your device screen lock, fingerprint, or face scan to sign in next time.' },
  hi: { welcome: 'उद्यम साथी में आपका स्वागत है।', subtitle: 'मीरा एक-एक आसान कदम पर आपका साथ देगी।', register: 'अपना खाता बनाएँ', login: 'वापसी पर स्वागत है', name: 'पूरा नाम', phone: 'मोबाइल नंबर', email: 'ईमेल (वैकल्पिक)', code: '6 अंकों का SMS कोड', send: 'सत्यापन कोड भेजें', verify: 'सत्यापित करें और आगे बढ़ें', resend: 'कोड फिर भेजें', skipEmail: 'ईमेल छोड़ें', location: 'पहचाना गया स्थान', locating: 'आपका स्थान पता कर रहे हैं…', locationLater: 'मीरा बाद में आपके स्थान की पुष्टि करेगी।', google: 'Google से आगे बढ़ें', evaluator: 'एक क्लिक में मूल्यांकनकर्ता प्रवेश', passkey: 'Face ID / पासकी से आगे बढ़ें', addPasskey: 'Face ID / पासकी सेट करें', skipPasskey: 'बाद में करूँगा/करूँगी', password: 'पासवर्ड', oldLogin: 'पुराने ईमेल और पासवर्ड से प्रवेश', haveAccount: 'पहले से खाता है?', newAccount: 'नए हैं?', signIn: 'प्रवेश करें', create: 'खाता बनाएँ', passkeyReady: 'आपका खाता तैयार है। अगली बार जल्दी प्रवेश के लिए पासकी जोड़ें।', miraName: 'मीरा, आपकी मार्गदर्शक', hear: 'मीरा को सुनें', guideName: 'पहले अपना पूरा नाम लिखें।', guidePhone: 'अब अपना 10 अंकों का मोबाइल नंबर लिखें।', guideEmail: 'चाहें तो ईमेल जोड़ें, या इसे छोड़ दें।', guideCode: 'फोन पर आया कोड लिखें।', guideLogin: 'प्रवेश के लिए पासकी चुनें या मोबाइल नंबर लिखें।', guidePasskey: 'अगली बार फोन या लैपटॉप के लॉक, उँगली या चेहरे से प्रवेश करें।' },
  mr: { welcome: 'उद्यम साथीमध्ये आपले स्वागत आहे.', subtitle: 'मीरा तुम्हाला एकेक पायरीवर मदत करेल.', register: 'खाते तयार करा', login: 'पुन्हा स्वागत आहे', name: 'पूर्ण नाव', phone: 'मोबाइल क्रमांक', email: 'ईमेल (ऐच्छिक)', code: '6 अंकी SMS कोड', send: 'सत्यापन कोड पाठवा', verify: 'सत्यापित करून पुढे जा', resend: 'कोड पुन्हा पाठवा', skipEmail: 'ईमेल वगळा', location: 'सापडलेले ठिकाण', locating: 'तुमचे ठिकाण शोधत आहोत…', locationLater: 'मीरा नंतर तुमचे ठिकाण निश्चित करेल.', google: 'Google ने पुढे जा', evaluator: 'एक-क्लिक मूल्यांकनकर्ता प्रवेश', passkey: 'Face ID / पासकीने पुढे जा', addPasskey: 'Face ID / पासकी सेट करा', skipPasskey: 'नंतर करेन', password: 'पासवर्ड', oldLogin: 'जुना ईमेल आणि पासवर्ड वापरा', haveAccount: 'आधीपासून खाते आहे?', newAccount: 'नवीन आहात?', signIn: 'प्रवेश करा', create: 'खाते तयार करा', passkeyReady: 'तुमचे खाते तयार आहे. पुढील वेळी जलद प्रवेशासाठी पासकी जोडा.', miraName: 'मीरा, तुमची मार्गदर्शक', hear: 'मीराचे ऐका', guideName: 'प्रथम तुमचे पूर्ण नाव लिहा.', guidePhone: 'आता 10 अंकी मोबाइल क्रमांक लिहा.', guideEmail: 'हवे असल्यास ईमेल जोडा किंवा वगळा.', guideCode: 'फोनवर आलेला कोड लिहा.', guideLogin: 'प्रवेशासाठी पासकी निवडा किंवा मोबाइल क्रमांक लिहा.', guidePasskey: 'पुढील वेळी फोन किंवा लॅपटॉपच्या लॉकने प्रवेश करा.' },
  te: { welcome: 'ఉద్యమ్ సాథికి స్వాగతం.', subtitle: 'మీరా మీకు ఒక్కో దశలో సహాయం చేస్తుంది.', register: 'ఖాతా సృష్టించండి', login: 'మళ్లీ స్వాగతం', name: 'పూర్తి పేరు', phone: 'మొబైల్ నంబర్', email: 'ఇమెయిల్ (ఐచ్ఛికం)', code: '6 అంకెల SMS కోడ్', send: 'ధృవీకరణ కోడ్ పంపండి', verify: 'ధృవీకరించి కొనసాగండి', resend: 'కోడ్ మళ్లీ పంపండి', skipEmail: 'ఇమెయిల్ దాటవేయండి', location: 'గుర్తించిన స్థానం', locating: 'మీ స్థానాన్ని కనుగొంటున్నాం…', locationLater: 'మీరా తర్వాత మీ స్థానాన్ని నిర్ధారిస్తుంది.', google: 'Google తో కొనసాగండి', evaluator: 'ఒక క్లిక్‌తో మూల్యాంకన ప్రవేశం', passkey: 'Face ID / పాస్‌కీతో కొనసాగండి', addPasskey: 'Face ID / పాస్‌కీ ఏర్పాటు', skipPasskey: 'తర్వాత చేస్తాను', password: 'పాస్‌వర్డ్', oldLogin: 'పాత ఇమెయిల్, పాస్‌వర్డ్ ఉపయోగించండి', haveAccount: 'ఇప్పటికే ఖాతా ఉందా?', newAccount: 'కొత్తవారా?', signIn: 'ప్రవేశించండి', create: 'ఖాతా సృష్టించండి', passkeyReady: 'మీ ఖాతా సిద్ధంగా ఉంది. తదుపరి త్వరిత ప్రవేశానికి పాస్‌కీ జోడించండి.', miraName: 'మీ మార్గదర్శి మీరా', hear: 'మీరా మాట వినండి', guideName: 'మొదట మీ పూర్తి పేరు నమోదు చేయండి.', guidePhone: 'ఇప్పుడు 10 అంకెల మొబైల్ నంబర్ నమోదు చేయండి.', guideEmail: 'కావాలంటే ఇమెయిల్ జోడించండి లేదా దాటవేయండి.', guideCode: 'మీ ఫోన్‌కు వచ్చిన కోడ్ నమోదు చేయండి.', guideLogin: 'పాస్‌కీ ఎంచుకోండి లేదా మొబైల్ నంబర్ నమోదు చేయండి.', guidePasskey: 'తర్వాత ఫోన్ లేదా ల్యాప్‌టాప్ లాక్‌తో ప్రవేశించండి.' },
  ta: { welcome: 'உத்யம் சாத்திக்கு வரவேற்கிறோம்.', subtitle: 'மீரா ஒவ்வொரு படியிலும் உங்களுக்கு வழிகாட்டுவார்.', register: 'கணக்கு உருவாக்குங்கள்', login: 'மீண்டும் வரவேற்கிறோம்', name: 'முழுப் பெயர்', phone: 'கைபேசி எண்', email: 'மின்னஞ்சல் (விருப்பம்)', code: '6 இலக்க SMS குறியீடு', send: 'சரிபார்ப்பு குறியீட்டை அனுப்பு', verify: 'சரிபார்த்து தொடருங்கள்', resend: 'மீண்டும் குறியீடு அனுப்பு', skipEmail: 'மின்னஞ்சலைத் தவிர்', location: 'கண்டறிந்த இடம்', locating: 'உங்கள் இடத்தைக் கண்டறிகிறோம்…', locationLater: 'மீரா பிறகு உங்கள் இடத்தை உறுதிசெய்வார்.', google: 'Google மூலம் தொடருங்கள்', evaluator: 'ஒரே கிளிக்கில் மதிப்பீட்டாளர் நுழைவு', passkey: 'Face ID / பாஸ்கீ மூலம் தொடருங்கள்', addPasskey: 'Face ID / பாஸ்கீ அமைக்கவும்', skipPasskey: 'பிறகு செய்கிறேன்', password: 'கடவுச்சொல்', oldLogin: 'பழைய மின்னஞ்சல், கடவுச்சொல் பயன்படுத்தவும்', haveAccount: 'ஏற்கனவே கணக்கு உள்ளதா?', newAccount: 'புதியவரா?', signIn: 'உள்நுழைக', create: 'கணக்கு உருவாக்கு', passkeyReady: 'உங்கள் கணக்கு தயார். அடுத்த முறை விரைவாக நுழைய பாஸ்கீ சேர்க்கவும்.', miraName: 'உங்கள் வழிகாட்டி மீரா', hear: 'மீராவைக் கேளுங்கள்', guideName: 'முதலில் உங்கள் முழுப் பெயரை உள்ளிடுங்கள்.', guidePhone: 'இப்போது 10 இலக்க கைபேசி எண்ணை உள்ளிடுங்கள்.', guideEmail: 'விரும்பினால் மின்னஞ்சல் சேர்க்கவும் அல்லது தவிர்க்கவும்.', guideCode: 'உங்கள் கைபேசிக்கு வந்த குறியீட்டை உள்ளிடுங்கள்.', guideLogin: 'பாஸ்கீ தேர்வு செய்யவும் அல்லது கைபேசி எண்ணை உள்ளிடவும்.', guidePasskey: 'அடுத்த முறை கைபேசி அல்லது மடிக்கணினி பூட்டால் நுழையலாம்.' },
  kn: { welcome: 'ಉದ್ಯಮ್ ಸಾಥಿಗೆ ಸ್ವಾಗತ.', subtitle: 'ಮೀರಾ ಪ್ರತಿ ಹಂತದಲ್ಲೂ ನಿಮಗೆ ಮಾರ್ಗದರ್ಶನ ನೀಡುತ್ತಾಳೆ.', register: 'ಖಾತೆ ತೆರೆಯಿರಿ', login: 'ಮತ್ತೆ ಸ್ವಾಗತ', name: 'ಪೂರ್ಣ ಹೆಸರು', phone: 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ', email: 'ಇಮೇಲ್ (ಐಚ್ಛಿಕ)', code: '6 ಅಂಕಿಯ SMS ಕೋಡ್', send: 'ಪರಿಶೀಲನಾ ಕೋಡ್ ಕಳುಹಿಸಿ', verify: 'ಪರಿಶೀಲಿಸಿ ಮುಂದುವರಿಯಿರಿ', resend: 'ಕೋಡ್ ಮತ್ತೆ ಕಳುಹಿಸಿ', skipEmail: 'ಇಮೇಲ್ ಬಿಟ್ಟುಬಿಡಿ', location: 'ಪತ್ತೆಯಾದ ಸ್ಥಳ', locating: 'ನಿಮ್ಮ ಸ್ಥಳವನ್ನು ಹುಡುಕಲಾಗುತ್ತಿದೆ…', locationLater: 'ಮೀರಾ ನಂತರ ನಿಮ್ಮ ಸ್ಥಳವನ್ನು ಖಚಿತಪಡಿಸುತ್ತಾಳೆ.', google: 'Google ಮೂಲಕ ಮುಂದುವರಿಯಿರಿ', evaluator: 'ಒಂದು ಕ್ಲಿಕ್ ಮೌಲ್ಯಮಾಪಕ ಪ್ರವೇಶ', passkey: 'Face ID / ಪಾಸ್‌ಕೀ ಮೂಲಕ ಮುಂದುವರಿಯಿರಿ', addPasskey: 'Face ID / ಪಾಸ್‌ಕೀ ಹೊಂದಿಸಿ', skipPasskey: 'ನಂತರ ಮಾಡುತ್ತೇನೆ', password: 'ಪಾಸ್‌ವರ್ಡ್', oldLogin: 'ಹಳೆಯ ಇಮೇಲ್ ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ ಬಳಸಿ', haveAccount: 'ಈಗಾಗಲೇ ಖಾತೆ ಇದೆಯೇ?', newAccount: 'ಹೊಸಬರೇ?', signIn: 'ಪ್ರವೇಶಿಸಿ', create: 'ಖಾತೆ ತೆರೆಯಿರಿ', passkeyReady: 'ನಿಮ್ಮ ಖಾತೆ ಸಿದ್ಧವಾಗಿದೆ. ಮುಂದಿನ ಬಾರಿ ವೇಗವಾಗಿ ಪ್ರವೇಶಿಸಲು ಪಾಸ್‌ಕೀ ಸೇರಿಸಿ.', miraName: 'ನಿಮ್ಮ ಮಾರ್ಗದರ್ಶಿ ಮೀರಾ', hear: 'ಮೀರಾಳ ಮಾತು ಕೇಳಿ', guideName: 'ಮೊದಲು ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರನ್ನು ನಮೂದಿಸಿ.', guidePhone: 'ಈಗ 10 ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.', guideEmail: 'ಬಯಸಿದರೆ ಇಮೇಲ್ ಸೇರಿಸಿ ಅಥವಾ ಬಿಟ್ಟುಬಿಡಿ.', guideCode: 'ನಿಮ್ಮ ಫೋನ್‌ಗೆ ಬಂದ ಕೋಡ್ ನಮೂದಿಸಿ.', guideLogin: 'ಪಾಸ್‌ಕೀ ಆಯ್ಕೆಮಾಡಿ ಅಥವಾ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ.', guidePasskey: 'ಮುಂದಿನ ಬಾರಿ ಫೋನ್ ಅಥವಾ ಲ್ಯಾಪ್‌ಟಾಪ್ ಲಾಕ್ ಮೂಲಕ ಪ್ರವೇಶಿಸಿ.' },
};

const errors = {
  en: { namePhone: 'Enter your name and a valid 10-digit mobile number.', email: 'Enter a valid email or leave it blank.', code: 'Enter the 6-digit SMS code.', send: 'Could not send the code. Check your phone number and try again.', verify: 'Could not verify the code. Please try again.', signIn: 'Sign-in failed. Please try again.', passkey: 'Could not add a passkey. You can do this later.' },
  hi: { namePhone: 'अपना नाम और सही 10 अंकों का मोबाइल नंबर लिखें।', email: 'सही ईमेल लिखें या खाली छोड़ दें।', code: '6 अंकों का SMS कोड लिखें।', send: 'कोड नहीं भेजा जा सका। नंबर जाँचकर फिर कोशिश करें।', verify: 'कोड सत्यापित नहीं हुआ। फिर कोशिश करें।', signIn: 'प्रवेश नहीं हो सका। फिर कोशिश करें।', passkey: 'पासकी नहीं जुड़ी। आप इसे बाद में कर सकते हैं।' },
  mr: { namePhone: 'नाव आणि योग्य 10 अंकी मोबाइल क्रमांक लिहा.', email: 'योग्य ईमेल लिहा किंवा रिकामे ठेवा.', code: '6 अंकी SMS कोड लिहा.', send: 'कोड पाठवता आला नाही. क्रमांक तपासून पुन्हा प्रयत्न करा.', verify: 'कोड सत्यापित झाला नाही. पुन्हा प्रयत्न करा.', signIn: 'प्रवेश झाला नाही. पुन्हा प्रयत्न करा.', passkey: 'पासकी जोडता आली नाही. नंतर करू शकता.' },
  te: { namePhone: 'పేరు మరియు సరైన 10 అంకెల మొబైల్ నంబర్ నమోదు చేయండి.', email: 'సరైన ఇమెయిల్ ఇవ్వండి లేదా ఖాళీగా ఉంచండి.', code: '6 అంకెల SMS కోడ్ నమోదు చేయండి.', send: 'కోడ్ పంపలేకపోయాం. నంబర్ తనిఖీ చేసి మళ్లీ ప్రయత్నించండి.', verify: 'కోడ్ ధృవీకరణ విఫలమైంది. మళ్లీ ప్రయత్నించండి.', signIn: 'ప్రవేశం విఫలమైంది. మళ్లీ ప్రయత్నించండి.', passkey: 'పాస్‌కీ జోడించలేకపోయాం. తర్వాత చేయవచ్చు.' },
  ta: { namePhone: 'பெயரையும் சரியான 10 இலக்க கைபேசி எண்ணையும் உள்ளிடுங்கள்.', email: 'சரியான மின்னஞ்சலை உள்ளிடுங்கள் அல்லது காலியாக விடுங்கள்.', code: '6 இலக்க SMS குறியீட்டை உள்ளிடுங்கள்.', send: 'குறியீட்டை அனுப்ப முடியவில்லை. எண்ணைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.', verify: 'குறியீட்டைச் சரிபார்க்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.', signIn: 'உள்நுழைவு தோல்வியடைந்தது. மீண்டும் முயற்சிக்கவும்.', passkey: 'பாஸ்கீ சேர்க்க முடியவில்லை. பிறகு செய்யலாம்.' },
  kn: { namePhone: 'ಹೆಸರು ಮತ್ತು ಸರಿಯಾದ 10 ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ.', email: 'ಸರಿಯಾದ ಇಮೇಲ್ ನಮೂದಿಸಿ ಅಥವಾ ಖಾಲಿ ಬಿಡಿ.', code: '6 ಅಂಕಿಯ SMS ಕೋಡ್ ನಮೂದಿಸಿ.', send: 'ಕೋಡ್ ಕಳುಹಿಸಲು ಆಗಲಿಲ್ಲ. ಸಂಖ್ಯೆಯನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.', verify: 'ಕೋಡ್ ಪರಿಶೀಲನೆ ವಿಫಲವಾಯಿತು. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.', signIn: 'ಪ್ರವೇಶ ವಿಫಲವಾಯಿತು. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.', passkey: 'ಪಾಸ್‌ಕೀ ಸೇರಿಸಲು ಆಗಲಿಲ್ಲ. ನಂತರ ಮಾಡಬಹುದು.' },
};

const extras = {
  en: { simple: 'Simple, secure access', privacy: 'Your fingerprint or face stays on your device.', or: 'or', orPhone: 'or use phone', device: 'Use your device screen lock, fingerprint, or face scan next time.', existingNote: 'Used email before? Sign in with email first, then link your phone on the dashboard to keep your saved businesses.', guideStaff: 'Enter the staff ID and password issued for your selected role.' },
  hi: { simple: 'आसान और सुरक्षित प्रवेश', privacy: 'आपकी उँगली या चेहरे की जानकारी आपके उपकरण में रहती है।', or: 'या', orPhone: 'या फोन से', device: 'अगली बार अपने उपकरण का लॉक, उँगली या चेहरा इस्तेमाल करें।', existingNote: 'पहले ईमेल से खाता बनाया था? पहले ईमेल से प्रवेश करें, फिर डैशबोर्ड पर फोन जोड़ें ताकि पुराने व्यवसाय सुरक्षित रहें।', guideStaff: 'चुनी हुई भूमिका के लिए दिया गया स्टाफ आईडी और पासवर्ड लिखें।' },
  mr: { simple: 'सोपे आणि सुरक्षित प्रवेश', privacy: 'बोटांचे ठसे किंवा चेहऱ्याची माहिती तुमच्या उपकरणातच राहते.', or: 'किंवा', orPhone: 'किंवा फोनने', device: 'पुढील वेळी उपकरणाचा लॉक, बोटांचा ठसा किंवा चेहरा वापरा.', existingNote: 'आधी ईमेल वापरला होता? जुन्या ईमेलने प्रवेश करा आणि व्यवसाय टिकवण्यासाठी डॅशबोर्डवर फोन जोडा.', guideStaff: 'निवडलेल्या भूमिकेसाठी दिलेला स्टाफ आयडी आणि पासवर्ड टाका.' },
  te: { simple: 'సులభమైన సురక్షిత ప్రవేశం', privacy: 'మీ వేలిముద్ర లేదా ముఖ సమాచారం మీ పరికరంలోనే ఉంటుంది.', or: 'లేదా', orPhone: 'లేదా ఫోన్‌తో', device: 'తదుపరి పరికరం లాక్, వేలిముద్ర లేదా ముఖంతో ప్రవేశించండి.', existingNote: 'ముందు ఇమెయిల్‌తో ఖాతా తెరిచారా? ముందుగా ఇమెయిల్‌తో ప్రవేశించి, వ్యాపారాలు అలాగే ఉండేందుకు డాష్‌బోర్డ్‌లో ఫోన్ జోడించండి.', guideStaff: 'ఎంచుకున్న పాత్రకు ఇచ్చిన స్టాఫ్ ఐడీ మరియు పాస్‌వర్డ్ నమోదు చేయండి.' },
  ta: { simple: 'எளிய பாதுகாப்பான அணுகல்', privacy: 'விரல்ரேகை அல்லது முகத் தகவல் உங்கள் சாதனத்திலேயே இருக்கும்.', or: 'அல்லது', orPhone: 'அல்லது கைபேசி மூலம்', device: 'அடுத்த முறை சாதனப் பூட்டு, விரல்ரேகை அல்லது முகத்தைப் பயன்படுத்துங்கள்.', existingNote: 'முன்பு மின்னஞ்சல் பயன்படுத்தினீர்களா? முதலில் அதில் உள்நுழைந்து, சேமித்த தொழில்கள் தொடர கைபேசியை டாஷ்போர்டில் இணைக்கவும்.', guideStaff: 'தேர்ந்தெடுத்த பணிக்கான பணியாளர் அடையாளம் மற்றும் கடவுச்சொல்லை உள்ளிடவும்.' },
  kn: { simple: 'ಸರಳ ಸುರಕ್ಷಿತ ಪ್ರವೇಶ', privacy: 'ಬೆರಳಚ್ಚು ಅಥವಾ ಮುಖದ ಮಾಹಿತಿ ನಿಮ್ಮ ಸಾಧನದಲ್ಲೇ ಉಳಿಯುತ್ತದೆ.', or: 'ಅಥವಾ', orPhone: 'ಅಥವಾ ಫೋನ್ ಮೂಲಕ', device: 'ಮುಂದಿನ ಬಾರಿ ಸಾಧನದ ಲಾಕ್, ಬೆರಳಚ್ಚು ಅಥವಾ ಮುಖ ಬಳಸಿ.', existingNote: 'ಹಿಂದೆ ಇಮೇಲ್ ಬಳಸಿದ್ದೀರಾ? ಮೊದಲು ಇಮೇಲ್‌ನಿಂದ ಪ್ರವೇಶಿಸಿ, ಉಳಿಸಿದ ಉದ್ಯಮಗಳು ಹಾಗೆಯೇ ಇರಲು ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿ ಫೋನ್ ಲಿಂಕ್ ಮಾಡಿ.', guideStaff: 'ಆಯ್ಕೆ ಮಾಡಿದ ಪಾತ್ರಕ್ಕೆ ನೀಡಿದ ಸಿಬ್ಬಂದಿ ಐಡಿ ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ ನಮೂದಿಸಿ.' },
};

export function useAuthCopy() {
  const { language } = useLanguage();
  return { ...(copy[language] || copy.en), ...(extras[language] || extras.en), errors: errors[language] || errors.en };
}

export function MiraGuide({ prompt }) {
  const { language } = useLanguage();
  const c = useAuthCopy();
  const [activated, setActivated] = useState(false);
  const first = useRef(true);
  const speak = (text) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = ({ en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN', te: 'te-IN', ta: 'ta-IN', kn: 'kn-IN' })[language];
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  };
  useEffect(() => {
    const begin = () => { setActivated(true); speak(c.welcome); };
    if (!activated) window.addEventListener('pointerdown', begin, { once: true });
    return () => window.removeEventListener('pointerdown', begin);
  }, [activated, c.welcome, language]);
  useEffect(() => {
    if (!activated) return;
    if (first.current) { first.current = false; return; }
    speak(prompt);
    return () => window.speechSynthesis?.cancel();
  }, [prompt, activated]);
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-violet-200 bg-white/90 p-4 shadow-sm" aria-live="polite">
      <img src="/mira-avatar-v2.png" alt="Mira" className="h-14 w-14 shrink-0 rounded-2xl object-cover border border-violet-100" />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-bold uppercase tracking-wide text-violet-700">{c.miraName}</p>
        <p className="mt-1 text-sm font-semibold text-slate-900">{c.welcome}</p>
        <p className="mt-1 text-sm leading-relaxed text-slate-600">{prompt}</p>
        <button type="button" onClick={() => speak(`${c.welcome} ${prompt}`)} className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-violet-700 hover:text-violet-900"><Volume2 className="h-3.5 w-3.5" />{c.hear}</button>
      </div>
    </div>
  );
}

export function AuthLayout({ mode, children, prompt }) {
  const c = useAuthCopy();
  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-amber-50 via-white to-violet-50 px-4 py-8 text-slate-900 sm:px-6 lg:py-12">
      <div className="pointer-events-none absolute -left-28 top-20 h-72 w-72 rounded-full bg-orange-200/40 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 bottom-10 h-80 w-80 rounded-full bg-sky-200/50 blur-3xl" />
      <div className="relative mx-auto max-w-5xl">
        <header className="mb-7 flex items-center justify-between gap-3">
          <Link to="/" className="flex items-center gap-2 text-lg font-black text-slate-900"><span className="grid h-10 w-10 place-items-center rounded-xl bg-violet-900 text-white">उ</span>Udyam Saathi</Link>
          <LanguageSelector />
        </header>
        <div className="grid gap-7 lg:grid-cols-[0.82fr_1.18fr] lg:items-start">
          <section className="lg:sticky lg:top-10">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900"><Sparkles className="h-3.5 w-3.5" />{c.simple}</span>
            <h1 className="mt-5 max-w-md text-3xl font-black leading-tight sm:text-4xl">{mode === 'register' ? c.register : c.login}</h1>
            <p className="mt-3 max-w-sm text-base text-slate-600">{c.subtitle}</p>
            <div className="mt-6"><MiraGuide prompt={prompt} /></div>
            <p className="mt-6 inline-flex items-center gap-2 text-xs font-medium text-slate-600"><ShieldCheck className="h-4 w-4 text-emerald-700" />{c.privacy}</p>
          </section>
          <section className="rounded-3xl border border-white bg-white/90 p-5 shadow-xl shadow-violet-100/60 backdrop-blur sm:p-8">{children}</section>
        </div>
      </div>
    </main>
  );
}

export function AuthField({ active, done, label, children }) {
  return <div className={`rounded-2xl border p-3 transition-all duration-300 ${active ? 'border-violet-500 bg-violet-50/80 ring-4 ring-violet-100 shadow-sm' : done ? 'border-emerald-200 bg-emerald-50/30' : 'border-slate-200 bg-white'}`}><label className="mb-2 block text-sm font-bold text-slate-800">{label} {done && <span className="text-emerald-700">✓</span>}</label>{children}</div>;
}
