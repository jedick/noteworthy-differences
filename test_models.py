from models import classify, judge


def models_logic():
    # First example used for classifier models only
    old_revision = """Henry Purcell (/ˈpɜːrsəl/, rare: /pərˈsɛl/;[n 1] c. 10 September 1659[n 2] – 21 November 1695) was an English composer of Baroque music.  He composed more than 100 songs, a tragic opera Dido and Aeneas, and wrote incidental music to a version of Shakespeare's A Midsummer Night's Dream called The Fairy Queen."""

    new_revision = """Henry Purcell (/ˈpɜːrsəl/, rare: /pərˈsɛl/;[n 1] c. 10 September 1659[n 2] – 21 November 1695) was an English composer and organist of the middle Baroque era.  He composed more than 100 songs, a tragic opera Dido and Aeneas, and wrote incidental music to a version of Shakespeare's A Midsummer Night's Dream called The Fairy Queen."""

    # Run classifier models
    classify_heuristic = classify(old_revision, new_revision, "heuristic")
    classify_few_shot = classify(old_revision, new_revision, "few-shot")
    # Test sub-condition is True if models disagree
    classify_condition = (
        classify_heuristic["noteworthy"] == False
        and classify_few_shot["noteworthy"] == True
    )

    # Second example used for judge alignment
    old_revision = """Kaman-Kalehöyük Archaeological Museum (Turkish: Kaman-Kalehöyük Arkeoloji Müzesi) is an archaeological museum in Kaman District of Kırşehir Province in Turkey. It exhibits artifacts of seven civilizations excavated in the nearby multi-period mound Kaman-Kalehöyük. It was opened in 2010. A Japanese garden is next to the museum building.[1][2]"""

    new_revision = """The Kaman-Kalehöyük Archaeological Museum (Turkish: Kaman-Kalehöyük Arkeoloji Müzesi) is an archaeological museum in Çağırkan, Kaman District, Kırşehir Province, Turkey. It exhibits artifacts of seven civilizations excavated in the nearby multi-period mound Kaman-Kalehöyük. It opened in 2010. A Japanese garden is next to the museum building.[1][2]"""

    classify_heuristic = classify(old_revision, new_revision, "heuristic")
    classify_few_shot = classify(old_revision, new_revision, "few-shot")
    judge_few_shot = judge(
        old_revision,
        new_revision,
        classify_heuristic["rationale"],
        classify_few_shot["rationale"],
        mode="aligned",
    )
    judge_heuristic = judge(
        old_revision,
        new_revision,
        classify_heuristic["rationale"],
        classify_few_shot["rationale"],
        mode="aligned-heuristic",
    )

    # Test sub-condition is True if aligned judges both give False
    judge_condition = (
        judge_few_shot["noteworthy"] == False and judge_heuristic["noteworthy"] == False
    )

    # Final test condition is True if both sub-conditions are True
    return classify_condition and judge_condition


# pytest -vv test_models.py::test_models
def test_models():
    """Run models logic up to 5 times"""
    current_try = 0
    max_trys = 5
    while current_try < max_trys:
        current_try += 1
        result = models_logic()
        if result is True:
            print(f"Try {current_try} succeeded")
            break
        else:
            print(f"Try {current_try} failed")
    # The actual test for pytest
    assert result is True
