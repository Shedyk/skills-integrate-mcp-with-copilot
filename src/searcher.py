import unicodedata
from typing import Dict, List


def remove_vietnamese_diacritics(text: str) -> str:
    """Convert Vietnamese text to ascii-only for diacritics-insensitive searching."""
    nfkd = unicodedata.normalize('NFKD', text)
    ascii_text = ''.join(c for c in nfkd if not unicodedata.combining(c))
    ascii_text = ascii_text.replace('đ', 'd').replace('Đ', 'D')
    return ascii_text.strip().lower()


def has_digit(text: str) -> bool:
    """Return True if the text contains any numeric digit."""
    return any(c.isdigit() for c in text)


def _normalize_student_name_from_email(email: str) -> str:
    """Infer a display name from an email local-part (best effort)."""
    local_part = email.split('@')[0]
    clean = local_part.replace('.', ' ').replace('_', ' ')
    return ' '.join(part.capitalize() for part in clean.split() if part)


def build_student_index(activities: Dict[str, Dict]) -> Dict[str, Dict]:
    """Build student index from activity participant lists."""
    index: Dict[str, Dict] = {}

    for activity_name, activity in activities.items():
        participants = activity.get('participants', [])
        for email in participants:
            student_id = email.split('@')[0].upper()
            if student_id not in index:
                index[student_id] = {
                    'student_id': student_id,
                    'name': _normalize_student_name_from_email(email),
                    'email': email,
                    'activities': [],
                }

            index[student_id]['activities'].append({
                'activity_name': activity_name,
                'schedule': activity.get('schedule'),
                'description': activity.get('description'),
            })

    return index


def search_students(query: str, activities: Dict[str, Dict], limit: int = 10) -> List[Dict]:
    """Search students by student ID (digit/partial) or name."""
    if not query or not query.strip():
        return []

    student_index = build_student_index(activities)
    normalized_query = query.strip()

    # Student ID search when a digit exists in query
    if has_digit(normalized_query):
        query_id = normalized_query.upper()

        exact = student_index.get(query_id)
        if exact:
            return [exact]

        partial = [s for sid, s in student_index.items() if query_id in sid]
        return partial[:limit]

    # Name search (diacritics-insensitive)
    query_norm = remove_vietnamese_diacritics(normalized_query)
    matches = []
    for student in student_index.values():
        name_norm = remove_vietnamese_diacritics(student.get('name', ''))
        email_norm = remove_vietnamese_diacritics(student.get('email', ''))

        if query_norm in name_norm or query_norm in email_norm:
            matches.append(student)

    return matches[:limit]
