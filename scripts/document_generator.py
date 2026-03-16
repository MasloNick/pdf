"""Document template generator for CourtNinja.

Generates Ukrainian court documents from templates:
- Позовна заява (Statement of Claim)
- Відзив (Response/Defence)
- Апеляційна скарга (Appeal)
- Клопотання (Motion)
- Заява про видачу судового наказу (Application for Court Order)
"""

from __future__ import annotations

from datetime import date
from typing import Dict, Optional


DOCUMENT_TYPES = {
    "claim": "Позовна заява",
    "response": "Відзив на позовну заяву",
    "appeal": "Апеляційна скарга",
    "motion": "Клопотання",
    "court_order": "Заява про видачу судового наказу",
    "complaint": "Скарга",
    "explanation": "Пояснення",
    "petition": "Заява",
}


DEFAULT_ATTACHMENTS = (
    "1. Копія позовної заяви для відповідача.\n"
    "    2. Квитанція про сплату судового збору.\n"
    "    3. Копії документів, що підтверджують обставини справи."
)


def _header(court_name: str, plaintiff: str, defendant: str, case_number: str = "") -> str:
    lines = [
        f"До {court_name}",
        "",
    ]
    if case_number:
        lines.append(f"Справа № {case_number}")
        lines.append("")
    lines.extend([
        f"Позивач: {plaintiff}",
        f"Відповідач: {defendant}",
        "",
    ])
    return "\n".join(lines)


def generate_claim(
    court_name: str,
    plaintiff: str,
    plaintiff_address: str,
    defendant: str,
    defendant_address: str,
    subject: str,
    circumstances: str,
    legal_basis: str,
    claim_amount: float = 0.0,
    demands: str = "",
    attachments: str = "",
) -> str:
    """Generate a Statement of Claim (Позовна заява)."""
    today = date.today().strftime("%d.%m.%Y")

    doc = f"""
                                        До {court_name}

                                        Позивач: {plaintiff}
                                        Адреса: {plaintiff_address}

                                        Відповідач: {defendant}
                                        Адреса: {defendant_address}

{('                                        Ціна позову: ' + str(round(claim_amount, 2)) + ' грн') if claim_amount else ''}

                        ПОЗОВНА ЗАЯВА
                    про {subject}

    Обставини справи:
    {circumstances}

    Правова підстава:
    {legal_basis}

    На підставі вищевикладеного, керуючись ст.ст. 3, 4, 12, 13, 76-82, 89,
    175, 177, 185-193 ЦПК України,

                            ПРОШУ:

    {demands or 'Задовольнити позовні вимоги в повному обсязі.'}

    Додатки:
    {attachments or DEFAULT_ATTACHMENTS}

    {today}                                                     _______________
                                                                   (підпис)
    """
    return doc.strip()


def generate_response(
    court_name: str,
    case_number: str,
    defendant: str,
    defendant_address: str,
    plaintiff: str,
    objections: str,
    legal_basis: str,
    demands: str = "",
) -> str:
    """Generate a Response/Defence (Відзив)."""
    today = date.today().strftime("%d.%m.%Y")

    doc = f"""
                                        До {court_name}
                                        Справа № {case_number}

                                        Відповідач: {defendant}
                                        Адреса: {defendant_address}

                                        Позивач: {plaintiff}

                            ВІДЗИВ
                    на позовну заяву

    У провадженні {court_name} перебуває справа № {case_number}.

    Заперечення проти позову:
    {objections}

    Правова підстава:
    {legal_basis}

    На підставі вищевикладеного, керуючись ст.ст. 178, 179 ЦПК України,

                            ПРОШУ:

    {demands or 'Відмовити у задоволенні позовних вимог у повному обсязі.'}

    Додатки:
    1. Копія відзиву для позивача.
    2. Копії документів, що підтверджують заперечення.

    {today}                                                     _______________
                                                                   (підпис)
    """
    return doc.strip()


def generate_appeal(
    appeal_court_name: str,
    first_court_name: str,
    case_number: str,
    appellant: str,
    appellant_address: str,
    opponent: str,
    decision_date: str,
    grounds: str,
    demands: str = "",
) -> str:
    """Generate an Appeal (Апеляційна скарга)."""
    today = date.today().strftime("%d.%m.%Y")

    doc = f"""
                                        До {appeal_court_name}
                                        через {first_court_name}

                                        Справа № {case_number}

                                        Апелянт: {appellant}
                                        Адреса: {appellant_address}

                                        Інша сторона: {opponent}

                        АПЕЛЯЦІЙНА СКАРГА
            на рішення {first_court_name}
                    від {decision_date}

    Рішенням {first_court_name} від {decision_date} у справі № {case_number}
    було прийнято рішення, з яким апелянт не погоджується.

    Підстави для скасування/зміни рішення:
    {grounds}

    На підставі вищевикладеного, керуючись ст.ст. 352, 354, 356, 367,
    374, 376 ЦПК України,

                            ПРОШУ:

    {demands or 'Скасувати рішення суду першої інстанції та ухвалити нове рішення.'}

    Додатки:
    1. Копія рішення суду першої інстанції.
    2. Квитанція про сплату судового збору.
    3. Копії апеляційної скарги для учасників справи.

    {today}                                                     _______________
                                                                   (підпис)
    """
    return doc.strip()


def generate_motion(
    court_name: str,
    case_number: str,
    applicant: str,
    motion_type: str,
    justification: str,
    request: str,
) -> str:
    """Generate a Motion (Клопотання)."""
    today = date.today().strftime("%d.%m.%Y")

    doc = f"""
                                        До {court_name}
                                        Справа № {case_number}

                                        Від: {applicant}

                            КЛОПОТАННЯ
                    про {motion_type}

    У провадженні {court_name} перебуває справа № {case_number}.

    Обґрунтування:
    {justification}

    На підставі вищевикладеного,

                            ПРОШУ:

    {request}

    {today}                                                     _______________
                                                                   (підпис)
    """
    return doc.strip()


def generate_court_order_application(
    court_name: str,
    applicant: str,
    applicant_address: str,
    debtor: str,
    debtor_address: str,
    amount: float,
    basis: str,
) -> str:
    """Generate Application for Court Order (Заява про видачу судового наказу)."""
    today = date.today().strftime("%d.%m.%Y")

    doc = f"""
                                        До {court_name}

                                        Заявник: {applicant}
                                        Адреса: {applicant_address}

                                        Боржник: {debtor}
                                        Адреса: {debtor_address}

                                        Сума вимоги: {amount:,.2f} грн

                    ЗАЯВА
            про видачу судового наказу

    Підстава вимоги:
    {basis}

    На підставі вищевикладеного, керуючись ст.ст. 160, 161 ЦПК України,

                            ПРОШУ:

    Видати судовий наказ про стягнення з {debtor} на користь {applicant}
    заборгованості у розмірі {amount:,.2f} грн.

    Додатки:
    1. Документи, що підтверджують заборгованість.
    2. Квитанція про сплату судового збору.

    {today}                                                     _______________
                                                                   (підпис)
    """
    return doc.strip()


# Quick access to all generators
GENERATORS = {
    "claim": generate_claim,
    "response": generate_response,
    "appeal": generate_appeal,
    "motion": generate_motion,
    "court_order": generate_court_order_application,
}
