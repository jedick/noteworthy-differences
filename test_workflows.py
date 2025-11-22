from workflows import llm_workflow


def llm_workflow_logic():

    old_revision = """Kaman-Kalehöyük Archaeological Museum (Turkish: Kaman-Kalehöyük Arkeoloji Müzesi) is an archaeological museum in Kaman District of Kırşehir Province in Turkey. It exhibits artifacts of seven civilizations excavated in the nearby multi-period mound Kaman-Kalehöyük. It was opened in 2010. A Japanese garden is next to the museum building.[1][2]"""

    new_revision = """The Kaman-Kalehöyük Archaeological Museum (Turkish: Kaman-Kalehöyük Arkeoloji Müzesi) is an archaeological museum in Çağırkan, Kaman District, Kırşehir Province, Turkey. It exhibits artifacts of seven civilizations excavated in the nearby multi-period mound Kaman-Kalehöyük. It opened in 2010. A Japanese garden is next to the museum building.[1][2]"""

    response = llm_workflow(old_revision, new_revision, "aligned")

    # The judge should responsd with noteworthy: False regardless of the classifier models' responses
    return response["judge"]["noteworthy"] is False


# pytest -vv test_workflows.py::test_llm_workflow
def test_llm_workflow():
    """Run LLM workflow logic up to 5 times"""
    current_try = 0
    max_trys = 5
    while current_try < max_trys:
        current_try += 1
        result = llm_workflow_logic()
        if result is True:
            print(f"Try {current_try} succeeded")
            break
        else:
            print(f"Try {current_try} failed")
    # The actual test for pytest
    assert result is True
