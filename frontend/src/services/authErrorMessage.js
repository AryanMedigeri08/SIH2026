// Keep expected authentication failures actionable without exposing raw server
// exceptions, credentials, or Firebase's implementation details in the UI.
const messages = {
  en: {
    provider: 'This sign-in method is not enabled yet. Please use another method or contact the app administrator.',
    phone: 'Enter a valid mobile number and try again.',
    code: 'The verification code is incorrect or has expired. Request a new code.',
    rate: 'Too many attempts. Please wait a while before trying again.',
    domain: 'This site is not authorized for sign-in. Please use the official app URL.',
    network: 'Cannot reach the sign-in service. Check your connection and that the backend is running.',
    credentials: 'These account details could not be verified. Check them and try again.',
    cancelled: 'Sign-in was cancelled.',
    passkey: 'No passkey was selected. Use a passkey already saved for this account, or sign in another way.',
    server: 'The sign-in service could not complete your request. Please try again shortly.',
  },
  hi: {
    provider: 'यह प्रवेश विधि अभी चालू नहीं है। दूसरी विधि आज़माएँ या ऐप व्यवस्थापक से संपर्क करें।',
    phone: 'सही मोबाइल नंबर लिखकर फिर कोशिश करें।',
    code: 'सत्यापन कोड गलत है या उसकी समय सीमा समाप्त हो गई है। नया कोड मँगाएँ।',
    rate: 'बहुत प्रयास हुए हैं। कुछ देर बाद फिर कोशिश करें।',
    domain: 'इस वेबसाइट से प्रवेश की अनुमति नहीं है। आधिकारिक ऐप URL इस्तेमाल करें।',
    network: 'प्रवेश सेवा से संपर्क नहीं हो पा रहा। इंटरनेट और बैकएंड जाँचें।',
    credentials: 'खाते का विवरण सत्यापित नहीं हुआ। जाँचकर फिर कोशिश करें।',
    cancelled: 'प्रवेश रद्द कर दिया गया।',
    passkey: 'कोई पासकी नहीं चुनी गई। पहले से सहेजी पासकी या दूसरी प्रवेश विधि इस्तेमाल करें।',
    server: 'प्रवेश सेवा अनुरोध पूरा नहीं कर सकी। थोड़ी देर बाद फिर कोशिश करें।',
  },
  mr: {
    provider: 'ही प्रवेश पद्धत अद्याप सुरू नाही. दुसरी पद्धत वापरा किंवा अ‍ॅप प्रशासकाशी संपर्क साधा.',
    phone: 'योग्य मोबाइल क्रमांक टाकून पुन्हा प्रयत्न करा.',
    code: 'पडताळणी कोड चुकीचा आहे किंवा त्याची मुदत संपली आहे. नवीन कोड मागवा.',
    rate: 'खूप प्रयत्न झाले आहेत. काही वेळाने पुन्हा प्रयत्न करा.',
    domain: 'या वेबसाइटवरून प्रवेशास परवानगी नाही. अधिकृत अ‍ॅप URL वापरा.',
    network: 'प्रवेश सेवेशी संपर्क होऊ शकला नाही. इंटरनेट आणि बॅकएंड तपासा.',
    credentials: 'खात्याची माहिती पडताळता आली नाही. तपासून पुन्हा प्रयत्न करा.',
    cancelled: 'प्रवेश रद्द केला.',
    passkey: 'पासकी निवडली गेली नाही. आधी जतन केलेली पासकी किंवा दुसरी पद्धत वापरा.',
    server: 'प्रवेश सेवा विनंती पूर्ण करू शकली नाही. थोड्या वेळाने पुन्हा प्रयत्न करा.',
  },
  te: {
    provider: 'ఈ ప్రవేశ విధానం ఇంకా అందుబాటులో లేదు. మరొక విధానాన్ని ఉపయోగించండి లేదా యాప్ నిర్వాహకుడిని సంప్రదించండి.',
    phone: 'సరైన మొబైల్ నంబర్ నమోదు చేసి మళ్లీ ప్రయత్నించండి.',
    code: 'ధృవీకరణ కోడ్ తప్పు లేదా గడువు ముగిసింది. కొత్త కోడ్ కోరండి.',
    rate: 'చాలా ప్రయత్నాలు జరిగాయి. కొంతసేపటి తర్వాత మళ్లీ ప్రయత్నించండి.',
    domain: 'ఈ వెబ్‌సైట్‌కు ప్రవేశ అనుమతి లేదు. అధికారిక యాప్ URL ఉపయోగించండి.',
    network: 'ప్రవేశ సేవను చేరుకోలేకపోయాం. ఇంటర్నెట్ మరియు బ్యాకెండ్‌ను తనిఖీ చేయండి.',
    credentials: 'ఖాతా వివరాలు ధృవీకరించబడలేదు. తనిఖీ చేసి మళ్లీ ప్రయత్నించండి.',
    cancelled: 'ప్రవేశం రద్దయింది.',
    passkey: 'పాస్‌కీ ఎంచుకోబడలేదు. ఇప్పటికే సేవ్ చేసిన పాస్‌కీ లేదా మరొక విధానాన్ని ఉపయోగించండి.',
    server: 'ప్రవేశ సేవ మీ అభ్యర్థనను పూర్తి చేయలేకపోయింది. కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి.',
  },
  ta: {
    provider: 'இந்த உள்நுழைவு முறை இன்னும் செயல்படுத்தப்படவில்லை. வேறு முறையைப் பயன்படுத்தவும் அல்லது பயன்பாட்டு நிர்வாகியைத் தொடர்புகொள்ளவும்.',
    phone: 'சரியான கைபேசி எண்ணை உள்ளிட்டு மீண்டும் முயற்சிக்கவும்.',
    code: 'சரிபார்ப்புக் குறியீடு தவறானது அல்லது காலாவதியானது. புதிய குறியீட்டைக் கேட்கவும்.',
    rate: 'பல முறை முயற்சி செய்யப்பட்டுள்ளது. சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கவும்.',
    domain: 'இந்த இணையதளத்திலிருந்து உள்நுழைய அனுமதி இல்லை. அதிகாரப்பூர்வ பயன்பாட்டு URL-ஐப் பயன்படுத்தவும்.',
    network: 'உள்நுழைவு சேவையை அணுக முடியவில்லை. இணைய இணைப்பையும் பின்தளத்தையும் சரிபார்க்கவும்.',
    credentials: 'கணக்கு விவரங்களைச் சரிபார்க்க முடியவில்லை. சரிபார்த்து மீண்டும் முயற்சிக்கவும்.',
    cancelled: 'உள்நுழைவு ரத்து செய்யப்பட்டது.',
    passkey: 'பாஸ்கீ தேர்ந்தெடுக்கப்படவில்லை. ஏற்கெனவே சேமித்த பாஸ்கீ அல்லது வேறு முறையைப் பயன்படுத்தவும்.',
    server: 'உள்நுழைவு சேவை கோரிக்கையை முடிக்க முடியவில்லை. சிறிது நேரம் கழித்து முயற்சிக்கவும்.',
  },
  kn: {
    provider: 'ಈ ಪ್ರವೇಶ ವಿಧಾನ ಇನ್ನೂ ಸಕ್ರಿಯವಾಗಿಲ್ಲ. ಬೇರೆ ವಿಧಾನ ಬಳಸಿ ಅಥವಾ ಆ್ಯಪ್ ನಿರ್ವಾಹಕರನ್ನು ಸಂಪರ್ಕಿಸಿ.',
    phone: 'ಸರಿಯಾದ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',
    code: 'ಪರಿಶೀಲನಾ ಕೋಡ್ ತಪ್ಪಾಗಿದೆ ಅಥವಾ ಅವಧಿ ಮುಗಿದಿದೆ. ಹೊಸ ಕೋಡ್ ಕೇಳಿ.',
    rate: 'ಬಹಳಷ್ಟು ಪ್ರಯತ್ನಗಳಾಗಿವೆ. ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',
    domain: 'ಈ ಜಾಲತಾಣದಿಂದ ಪ್ರವೇಶಕ್ಕೆ ಅನುಮತಿ ಇಲ್ಲ. ಅಧಿಕೃತ ಆ್ಯಪ್ URL ಬಳಸಿ.',
    network: 'ಪ್ರವೇಶ ಸೇವೆಯನ್ನು ತಲುಪಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ. ಇಂಟರ್ನೆಟ್ ಮತ್ತು ಬ್ಯಾಕೆಂಡ್ ಪರಿಶೀಲಿಸಿ.',
    credentials: 'ಖಾತೆ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ. ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',
    cancelled: 'ಪ್ರವೇಶವನ್ನು ರದ್ದುಗೊಳಿಸಲಾಗಿದೆ.',
    passkey: 'ಪಾಸ್‌ಕೀ ಆಯ್ಕೆಯಾಗಿಲ್ಲ. ಈಗಾಗಲೇ ಉಳಿಸಿದ ಪಾಸ್‌ಕೀ ಅಥವಾ ಬೇರೆ ವಿಧಾನ ಬಳಸಿ.',
    server: 'ಪ್ರವೇಶ ಸೇವೆಗೆ ವಿನಂತಿಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ.',
  },
};

const byCode = {
  'auth/operation-not-allowed': 'provider',
  'auth/admin-restricted-operation': 'provider',
  'auth/invalid-phone-number': 'phone',
  'auth/invalid-verification-code': 'code',
  'auth/code-expired': 'code',
  'auth/too-many-requests': 'rate',
  'auth/unauthorized-domain': 'domain',
  'auth/network-request-failed': 'network',
  'auth/invalid-credential': 'credentials',
  'auth/invalid-login-credentials': 'credentials',
  'auth/wrong-password': 'credentials',
  'auth/user-not-found': 'credentials',
  'auth/popup-closed-by-user': 'cancelled',
  'auth/cancelled-popup-request': 'cancelled',
};

export function authErrorMessage(error, fallback, language = 'en') {
  const copy = messages[language] || messages.en;
  const code = error?.code || '';
  if (byCode[code]) return copy[byCode[code]];
  if (error?.name === 'NotAllowedError') return copy.passkey;
  if (error?.status === 401 || error?.status === 403) return copy.credentials;
  if (error?.status >= 500) return copy.server;
  if (error?.name === 'TypeError' && /fetch|network/i.test(error?.message || '')) return copy.network;
  if (error?.status) return `${fallback} (HTTP ${error.status})`;
  if (code.startsWith('auth/')) return `${fallback} (${code})`;
  return fallback;
}
