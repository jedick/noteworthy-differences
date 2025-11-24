from models import classifier, judge


def classifier_logic():
    """Return scenario flags for heuristic/few-shot classifier outputs."""

    old_revision = """Henry Purcell (/ˈpɜːrsəl/, rare: /pərˈsɛl/;[n 1] c. 10 September 1659[n 2] – 21 November 1695) was an English composer of Baroque music.  He composed more than 100 songs, a tragic opera Dido and Aeneas, and wrote incidental music to a version of Shakespeare's A Midsummer Night's Dream called The Fairy Queen."""

    new_revision = """Henry Purcell (/ˈpɜːrsəl/, rare: /pərˈsɛl/;[n 1] c. 10 September 1659[n 2] – 21 November 1695) was an English composer and organist of the middle Baroque era.  He composed more than 100 songs, a tragic opera Dido and Aeneas, and wrote incidental music to a version of Shakespeare's A Midsummer Night's Dream called The Fairy Queen."""

    # Run classifier models
    heuristic = classifier(old_revision, new_revision, "heuristic")
    few_shot = classifier(old_revision, new_revision, "few-shot")
    heuristic_true = heuristic["noteworthy"] is True
    few_shot_true = few_shot["noteworthy"] is True

    only_heuristic_true = heuristic_true and not few_shot_true
    only_few_shot_true = few_shot_true and not heuristic_true
    both_true = heuristic_true and few_shot_true
    both_false = (heuristic_true is False) and (few_shot_true is False)

    return (
        only_heuristic_true,
        only_few_shot_true,
        both_true,
        both_false,
    )


def judge_logic():

    old_revision = """Kaman-Kalehöyük Archaeological Museum (Turkish: Kaman-Kalehöyük Arkeoloji Müzesi) is an archaeological museum in Kaman District of Kırşehir Province in Turkey. It exhibits artifacts of seven civilizations excavated in the nearby multi-period mound Kaman-Kalehöyük. It was opened in 2010. A Japanese garden is next to the museum building.[1][2]"""

    new_revision = """The Kaman-Kalehöyük Archaeological Museum (Turkish: Kaman-Kalehöyük Arkeoloji Müzesi) is an archaeological museum in Çağırkan, Kaman District, Kırşehir Province, Turkey. It exhibits artifacts of seven civilizations excavated in the nearby multi-period mound Kaman-Kalehöyük. It opened in 2010. A Japanese garden is next to the museum building.[1][2]"""

    heuristic = classifier(old_revision, new_revision, "heuristic")
    few_shot = classifier(old_revision, new_revision, "few-shot")
    judge_few_shot = judge(
        old_revision,
        new_revision,
        heuristic["rationale"],
        few_shot["rationale"],
        mode="aligned-fewshot",
    )
    judge_heuristic = judge(
        old_revision,
        new_revision,
        heuristic["rationale"],
        few_shot["rationale"],
        mode="aligned-heuristic",
    )

    # Test condition is True if aligned judges both give False
    judge_condition = (
        judge_few_shot["noteworthy"] == False and judge_heuristic["noteworthy"] == False
    )

    return judge_condition


# pytest -vv test_models.py::test_classifier
def test_classifier():
    """Run classifier logic exactly 5 times and compare outcomes."""
    tries = 5
    outcomes = [classifier_logic() for _ in range(tries)]

    only_heuristic_true = sum(result[0] for result in outcomes)
    only_few_shot_true = sum(result[1] for result in outcomes)
    both_true = sum(result[2] for result in outcomes)
    both_false = sum(result[3] for result in outcomes)

    heuristic_true_count = only_heuristic_true + both_true
    few_shot_true_count = only_few_shot_true + both_true
    disagree_count = only_heuristic_true + only_few_shot_true
    agree_count = both_true + both_false

    few_shot_more_often = few_shot_true_count > heuristic_true_count
    disagree_more_than_agree = disagree_count > agree_count

    if not few_shot_more_often:
        print(
            "Few-shot classifier did not return True more often than the heuristic classifier."
        )
    if not disagree_more_than_agree:
        print("Classifiers did not disagree more often than they agreed.")

    assert few_shot_more_often and disagree_more_than_agree


# pytest -vv test_models.py::test_judge
def test_judge():
    """Run judge logic up to 5 times"""
    current_try = 0
    max_trys = 5
    while current_try < max_trys:
        current_try += 1
        result = judge_logic()
        if result is True:
            print(f"Try {current_try} succeeded")
            break
        else:
            print(f"Try {current_try} failed")
    # The assert for pytest
    assert result is True
