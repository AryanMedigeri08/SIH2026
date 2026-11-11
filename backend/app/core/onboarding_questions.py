"""Deterministic question order and answer validation; no finance formulas."""
import math
import re
from fastapi import HTTPException
from app.core.enterprise_planning import CATALOGUE

UNKNOWN = {'', 'unknown', 'not sure', 'skip', 'पता नहीं', 'माहीत नाही', 'தெரியாது', 'తెలియదు', 'ತಿಳಿದಿಲ್ಲ'}
DIGITS = str.maketrans('०१२३४५६७८९௦௧௨௩௪௫௬௭௮௯౦౧౨౩౪౫౬౭౮౯೦೧೨೩೪೫೬೭೮೯', '0123456789' * 4)
NUMBER_WORDS = dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(), range(20)))
NUMBER_WORDS.update(dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(), range(20, 100, 10))))
SCALES = {'thousand': 1000, 'हजार': 1000, 'हज़ार': 1000, 'lakh': 100000, 'lakhs': 100000, 'लाख': 100000, 'crore': 10000000, 'crores': 10000000, 'करोड़': 10000000, 'कोटी': 10000000, 'k': 1000, 'l': 100000}


def money(value, optional=False, maximum=100000000):
    if value is None or str(value).strip().lower() in UNKNOWN:
        if optional:
            return None
        raise HTTPException(422, 'Please enter your own contribution. Enter 0 if you have no own money.')
    text = str(value).translate(DIGITS).lower().replace(',', '')
    text = re.sub(r'(₹|rupees?|rs\.?|inr|रुपये|रुपए|रुपयांची)', ' ', text)
    text = re.sub(r'(\d)([a-z])', r'\1 \2', text).strip()
    total = current = 0.0
    for part in text.split():
        if re.fullmatch(r'\d+(\.\d+)?', part):
            current += float(part)
        elif part in NUMBER_WORDS:
            current += NUMBER_WORDS[part]
        elif part == 'hundred':
            current = (current or 1) * 100
        elif part in SCALES:
            total += (current or 1) * SCALES[part]; current = 0
        elif part != 'and':
            raise HTTPException(422, 'Please type the amount in digits, for example 50000 or 1.5 lakh.')
    result = total + current
    if not math.isfinite(result) or result < 0 or result > maximum:
        raise HTTPException(422, 'This amount is outside the supported range.')
    return result


def question_sequence(draft):
    a = draft.get('answers', {})
    path = draft.get('journey')
    if not (draft.get('location') or {}).get('confirmed'):
        return ['location']
    if path not in {'existing', 'budget_only', 'idea_only'}:
        return ['journey']
    order = []
    if path != 'budget_only':
        order += ['idea', 'business_id']
        if a.get('business_id') == 'custom':
            order += ['sector', 'business_category']
        order += ['idea_confirmed', 'odop_choice']
    if path in {'existing', 'budget_only'}:
        order += ['own_cash', 'cash_confirmed']
    if path == 'budget_only':
        order += ['skills']
    order += ['premise_type']
    if a.get('premise_type') == 'rented':
        order += ['monthly_rent']
    if path != 'budget_only':
        order += ['equipment_quote']
    if path == 'existing':
        order += ['project_cost', 'annual_sales']
    if path == 'idea_only':
        order += ['own_cash']
        if a.get('own_cash') is not None:
            order += ['cash_confirmed']
    order += ['resources']
    if path == 'budget_only':
        order += ['preferences']
    else:
        order += ['enterprise_name']
    order += ['review_confirmed']
    return order


def next_question(draft):
    order = question_sequence(draft)
    return next((key for key in order if key not in draft.get('answers', {})), 'ready')


def conversation_state(draft):
    sequence = question_sequence(draft)
    question = next_question(draft)
    completed = sum(key in draft.get('answers', {}) for key in sequence)
    return {'draft': draft, 'question': question, 'sequence': sequence,
            'progress': {'completed': completed, 'total': len(sequence)}}


def revise_answer(draft, field, value, hybrid_name=None, hybrid_description=None):
    answers = draft['answers']
    if field not in question_sequence(draft) or field not in answers:
        raise HTTPException(409, 'This answer is not available to revise.')
    normalized = validated_answer(field, value, draft['journey'])
    unchanged_hybrid = field != 'odop_choice' or value != 'hybrid' or (
        hybrid_name == answers.get('enterprise_name') and hybrid_description == answers.get('idea'))
    if answers[field] == normalized and unchanged_hybrid:
        return draft
    affected = {
        'idea': ['business_id','sector','business_category','idea_confirmed','odop_choice','original_idea','enterprise_name'],
        'business_id': ['sector','business_category','idea_confirmed','odop_choice','enterprise_name'],
        'sector': ['idea_confirmed','odop_choice','enterprise_name'],
        'business_category': ['idea_confirmed','odop_choice','enterprise_name'],
        'own_cash': ['cash_confirmed'], 'premise_type': ['monthly_rent'],
    }.get(field, [])
    if (field == 'odop_choice' or 'odop_choice' in affected) and answers.get('original_idea'):
        answers['idea'] = answers.pop('original_idea')
    for key in affected:
        answers.pop(key, None)
    if field == 'odop_choice':
        if normalized == 'hybrid':
            if not hybrid_name or not hybrid_description:
                raise HTTPException(422, 'Select an evaluated combination or keep your original idea.')
            answers['original_idea'] = answers['idea']
            answers['idea'] = hybrid_description
            answers['enterprise_name'] = hybrid_name
        else:
            answers.pop('enterprise_name', None)
    answers[field] = normalized
    answers.pop('review_confirmed', None)
    draft.update(preview_id=None, project_id=None, completed=False)
    return draft


def validated_answer(field, value, path):
    if field in {'own_cash', 'monthly_rent', 'equipment_quote', 'project_cost', 'annual_sales'}:
        amount = money(value, optional=field != 'own_cash' or path == 'idea_only', maximum=1000000 if field == 'monthly_rent' else 100000000)
        if field in {'equipment_quote', 'project_cost'} and amount is not None and amount <= 0:
            raise HTTPException(422, 'Enter a positive cost or choose Not sure.')
        return amount
    if field in {'idea_confirmed', 'cash_confirmed', 'review_confirmed'}:
        if value is not True:
            raise HTTPException(422, 'Please confirm or go back and correct your answer.')
        return True
    if field == 'premise_type' and value not in {'owned', 'rented', 'panchayat'}:
        raise HTTPException(422, 'Choose your workspace type.')
    if field == 'business_id' and value not in {*CATALOGUE, 'custom'}:
        raise HTTPException(422, 'Choose a matching business or a custom idea.')
    if field == 'odop_choice' and value not in {'original', 'hybrid'}:
        raise HTTPException(422, 'Choose the original idea or the combination.')
    if field == 'sector' and value not in {'dairy', 'food_processing', 'repair', 'apparel', 'fabrication', 'general'}:
        raise HTTPException(422, 'Choose a supported sector.')
    if field == 'business_category' and value not in {'manufacturing', 'service'}:
        raise HTTPException(422, 'Choose making products or providing a service.')
    if not isinstance(value, str) or len(value.strip()) > (800 if field == 'idea' else 160 if field == 'enterprise_name' else 350):
        raise HTTPException(422, 'Please shorten this answer.')
    if field == 'idea' and len(value.strip()) < 10:
        raise HTTPException(422, 'Please explain what you want to make, sell or provide in a little more detail.')
    if field == 'enterprise_name' and not value.strip():
        raise HTTPException(422, 'Enter a business name or use the suggested name.')
    return value.strip()
