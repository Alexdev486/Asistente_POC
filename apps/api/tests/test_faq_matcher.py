from app.modules.faq_matcher.service import FAQItem, FAQMatcherService


def test_faq_matcher_prioritizes_model_scope() -> None:
    matcher = FAQMatcherService()
    faqs = [
        FAQItem(
            faq_id=1,
            model="AK550",
            category="Combustible",
            question="Que significa que no se escuche la bomba de gasolina al dar contacto?",
            answer="Bomba de gasolina defectuosa.",
            usage_count=3,
        ),
        FAQItem(
            faq_id=2,
            model=None,
            category="General",
            question="Que significa el testigo CELP encendido?",
            answer="Fallo electronico.",
            usage_count=1,
        ),
    ]

    match = matcher.match("AK550", "bomba de gasolina al dar contacto", faqs)

    assert match is not None
    assert match.item.faq_id == 1
    assert match.scope == "model"


def test_faq_matcher_falls_back_to_global() -> None:
    matcher = FAQMatcherService()
    faqs = [
        FAQItem(
            faq_id=3,
            model=None,
            category="General",
            question="Que significa el testigo CELP encendido?",
            answer="Fallo electronico.",
            usage_count=2,
        )
    ]

    match = matcher.match("AK550", "testigo celp encendido", faqs)

    assert match is not None
    assert match.item.faq_id == 3
    assert match.scope == "global"
