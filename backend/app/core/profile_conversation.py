"""Explicit profile answers only: never infer demographics from a name."""
import re
import unicodedata

PROFILE_FIELDS = ('name', 'gender', 'promoter_category', 'phone', 'email')
SKIP = {'skip', 'no email', 'none', 'not now', 'no', 'छोड़ें', 'छोड़ दो', 'नहीं', 'नाही', 'नको', 'வேண்டாம்', 'లేదు', 'ಬೇಡ'}
GENDERS = {
    'Female': ('female', 'woman', 'महिला', 'स्त्री', 'பெண்', 'మహిళ', 'ಹೆಣ್ಣು', 'ಮಹಿಳೆ'),
    'Male': ('male', 'man', 'पुरुष', 'ஆண்', 'పురుషుడు', 'ಗಂಡು', 'ಪುರುಷ'),
    'Other': ('other', 'अन्य', 'इतर', 'மற்ற', 'ఇతర', 'ಇತರೆ'),
    'Unspecified': ('prefer not to say', 'skip', 'नहीं बताना', 'सांगायचे नाही', 'சொல்ல விரும்பவில்லை', 'చెప్పను', 'ಹೇಳಲು ಇಷ್ಟವಿಲ್ಲ'),
}
CATEGORIES = {
    'general': ('general', 'सामान्य', 'खुला', 'பொது', 'பொதுப் பிரிவு', 'సాధారణ', 'జనరల్', 'ಸಾಮಾನ್ಯ'),
    'obc': ('obc', 'o b c', 'ओबीसी', 'ओ बी सी', 'other backward class', 'ओबी सी', 'ஓபிசி', 'ఓబీసీ', 'ಓಬಿಸಿ'),
    'sc': ('sc', 's c', 'scheduled caste', 'एससी', 'एस सी', 'अनुसूचित जाति', 'अनुसूचित जाती', 'எஸ்சி', 'ఎస్సీ', 'ಎಸ್ಸಿ'),
    'st': ('st', 's t', 'scheduled tribe', 'एसटी', 'एस टी', 'अनुसूचित जनजाति', 'अनुसूचित जमाती', 'எஸ்டி', 'ఎస్టీ', 'ಎಸ್ಟಿ'),
    'minority': ('minority', 'अल्पसंख्यक'), 'ph': ('ph', 'disability', 'दिव्यांग'),
    'artisan': ('artisan', 'कारीगर'), 'women_shg': ('women shg', 'self help group', 'महिला समूह'),
    'women': ('women entrepreneur', 'woman entrepreneur', 'महिला उद्यमी'),
}
DIGITS = [('zero','शून्य','பூஜ்யம்','సున్నా','ಸೊನ್ನೆ'), ('one','एक','ஒன்று','ఒకటి','ಒಂದು'),
    ('two','दो','दोन','இரண்டு','రెండు','ಎರಡು'), ('three','तीन','மூன்று','మూడు','ಮೂರು'),
    ('four','चार','நான்கு','నాలుగు','ನಾಲ್ಕು'), ('five','पांच','पाँच','पाच','ஐந்து','ఐదు','ಐದು'),
    ('six','छह','सहा','ஆறு','ఆరు','ಆರು'), ('seven','सात','ஏழு','ఏడు','ಏಳು'),
    ('eight','आठ','எட்டு','ఎనిమిది','ಎಂಟು'), ('nine','नौ','नऊ','ஒன்பது','తొమ్మిది','ಒಂಬತ್ತು')]


def contains(text, term):
    return bool(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text))


def parse_correction(text):
    match = re.match(r'^(?:correct|change) my (name|gender|caste|category|phone|email)(?: to| is)?\s+(.+)$', text, re.I)
    if match:
        field = {'caste':'promoter_category','category':'promoter_category'}.get(match[1].lower(), match[1].lower())
        return parse_answer(field, match[2])
    labels = {'नाम':'name','नाव':'name','பெயர்':'name','పేరు':'name','ಹೆಸರು':'name',
        'लिंग':'gender','பாலினம்':'gender','లింగం':'gender','ಲಿಂಗ':'gender',
        'श्रेणी':'promoter_category','प्रवर्ग':'promoter_category','பிரிவு':'promoter_category','వర్గం':'promoter_category','ವರ್ಗ':'promoter_category',
        'फोन':'phone','मोबाइल':'phone','கைபேசி':'phone','ఫోన్':'phone','ಫೋನ್':'phone',
        'ईमेल':'email','மின்னஞ்சல்':'email','ఇమెయిల్':'email','ಇಮೇಲ್':'email'}
    match = re.match(r'^(.+?)\s+(?:बदलें|बदलो|बदला|மாற்று|మార్చు|ಬದಲಿಸಿ)\s*[:：]?\s+(.+)$', text)
    if match and match[1] in labels:
        return parse_answer(labels[match[1]], match[2])
    return None


def parse_answer(field, text):
    """Return validated normalized data, or None without advancing."""
    text = re.sub(r'\s+', ' ', str(text)).strip(' .!।')
    lower = text.casefold()
    if field == 'name':
        name = re.sub(r'^(?:my name is|i am|i’m|मेरा नाम|माझे नाव|माझं नाव|என் பெயர்|నా పేరు|ನನ್ನ ಹೆಸರು)\s+', '', text, flags=re.I)
        name = re.sub(r'\s+(?:है|आहे)$', '', name).strip()
        if 2 <= len(name) <= 120 and any(c.isalpha() for c in name) and not any(c.isdigit() for c in name) and lower not in {'hello','hi','yes','no','repeat','not sure'}:
            return {'name': name}
    elif field == 'gender':
        explicit = next((value for value in GENDERS if lower == value.casefold()), None)
        if explicit:
            return {'gender':explicit}
        matches = [value for value, aliases in GENDERS.items() if any(contains(lower, term) for term in aliases)]
        if len(matches) == 1:
            return {'gender': matches[0]}
    elif field == 'promoter_category':
        if lower in CATEGORIES:
            return {'promoter_category':lower}
        matches = [value for value, aliases in CATEGORIES.items() if any(contains(lower, term) for term in aliases)]
        if len(matches) == 1:
            return {'promoter_category': matches[0]}
    elif field == 'phone':
        normalized = lower
        for digit, aliases in enumerate(DIGITS):
            for alias in aliases:
                normalized = re.sub(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', str(digit), normalized)
        digits = ''.join(str(unicodedata.digit(c)) for c in normalized if c.isdigit())
        if len(digits) == 12 and digits.startswith('91'):
            digits = digits[2:]
        if re.fullmatch(r'[6-9]\d{9}', digits):
            return {'phone': '+91' + digits}
    elif field == 'email':
        if lower in SKIP:
            return {'email_status': 'skipped'}
        email = lower
        for pattern, replacement in [(r'\s+(?:at|ऐट|एट|அட்)\s+', '@'), (r'\s+(?:dot|डॉट|டாட்)\s+', '.'), (r'\s+underscore\s+', '_'), (r'\s+dash\s+', '-')]:
            email = re.sub(pattern, replacement, email)
        email = email.replace(' ', '')
        if len(email) <= 254 and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            return {'email': email, 'email_status': 'provided'}
    return None


PROMPTS = {
    'en': ['Namaste. I am Mira. What is your full name?', 'How would you describe your gender? You can say prefer not to say.', 'Which social category should we use for scheme assessment? For example, General, OBC, SC or ST.', 'What is your ten digit mobile number? Please say each digit.', 'Email is optional. Say your email address, or say skip.'],
    'hi': ['नमस्ते। मैं मीरा हूँ। आपका पूरा नाम क्या है?', 'आपका लिंग क्या है? आप नहीं बताना भी कह सकते हैं।', 'योजनाओं की जाँच के लिए आपकी सामाजिक श्रेणी क्या है? जैसे सामान्य, ओबीसी, एससी या एसटी।', 'आपका दस अंकों का मोबाइल नंबर क्या है? एक एक अंक बोलिए।', 'ईमेल वैकल्पिक है। अपना ईमेल बोलिए या छोड़ दो कहिए।'],
    'mr': ['नमस्कार. मी मीरा आहे. तुमचे पूर्ण नाव काय आहे?', 'तुमचे लिंग काय आहे? सांगायचे नाही असेही म्हणू शकता.', 'योजनांसाठी तुमचा सामाजिक प्रवर्ग कोणता आहे? सामान्य, ओबीसी, एससी किंवा एसटी सांगा.', 'तुमचा दहा अंकी मोबाइल क्रमांक काय आहे? प्रत्येक अंक सांगा.', 'ईमेल ऐच्छिक आहे. ईमेल सांगा किंवा नको म्हणा.'],
    'te': ['నమస్తే. నేను మీరా. మీ పూర్తి పేరు ఏమిటి?', 'మీ లింగం ఏమిటి? చెప్పను అని కూడా అనవచ్చు.', 'పథకాల కోసం మీ సామాజిక వర్గం ఏది? జనరల్, ఓబీసీ, ఎస్సీ లేదా ఎస్టీ చెప్పండి.', 'మీ పది అంకెల మొబైల్ నంబర్ ఏమిటి? ఒక్కో అంకె చెప్పండి.', 'ఇమెయిల్ ఐచ్ఛికం. మీ ఇమెయిల్ చెప్పండి లేదా లేదు అనండి.'],
    'ta': ['வணக்கம். நான் மீரா. உங்கள் முழுப் பெயர் என்ன?', 'உங்கள் பாலினம் என்ன? சொல்ல விரும்பவில்லை என்றும் கூறலாம்.', 'திட்டங்களை மதிப்பிட உங்கள் சமூகப் பிரிவு என்ன? பொதுப் பிரிவு, ஓபிசி, எஸ்சி அல்லது எஸ்டி கூறுங்கள்.', 'உங்கள் பத்து இலக்க கைபேசி எண் என்ன? ஒவ்வொரு இலக்கமாகக் கூறுங்கள்.', 'மின்னஞ்சல் விருப்பமானது. உங்கள் மின்னஞ்சலைக் கூறுங்கள் அல்லது வேண்டாம் என்று கூறுங்கள்.'],
    'kn': ['ನಮಸ್ಕಾರ. ನಾನು ಮೀರಾ. ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ಏನು?', 'ನಿಮ್ಮ ಲಿಂಗ ಯಾವುದು? ಹೇಳಲು ಇಷ್ಟವಿಲ್ಲ ಎಂದೂ ಹೇಳಬಹುದು.', 'ಯೋಜನೆಗಳಿಗಾಗಿ ನಿಮ್ಮ ಸಾಮಾಜಿಕ ವರ್ಗ ಯಾವುದು? ಸಾಮಾನ್ಯ, ಓಬಿಸಿ, ಎಸ್ಸಿ ಅಥವಾ ಎಸ್ಟಿ ಹೇಳಿ.', 'ನಿಮ್ಮ ಹತ್ತು ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಏನು? ಒಂದೊಂದು ಅಂಕೆ ಹೇಳಿ.', 'ಇಮೇಲ್ ಐಚ್ಛಿಕ. ನಿಮ್ಮ ಇಮೇಲ್ ಹೇಳಿ ಅಥವಾ ಬೇಡ ಎನ್ನಿ.'],
}
RETRY = {'en': 'I could not validate that answer. Please try again, or type your answer.',
    'hi':'मैं यह उत्तर समझ नहीं सकी। फिर से बोलिए या लिखिए।', 'mr':'मला हे उत्तर समजले नाही. पुन्हा सांगा किंवा लिहा.',
    'te':'ఈ సమాధానం అర్థం కాలేదు. మళ్లీ చెప్పండి లేదా టైప్ చేయండి.', 'ta':'இந்த பதிலைப் புரிந்துகொள்ள முடியவில்லை. மீண்டும் கூறவும் அல்லது எழுதவும்.', 'kn':'ಈ ಉತ್ತರ ಅರ್ಥವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಹೇಳಿ ಅಥವಾ ಬರೆಯಿರಿ.'}


def prompt(field, language='en'):
    return PROMPTS.get(language, PROMPTS['en'])[PROFILE_FIELDS.index(field)]
