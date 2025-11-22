from models import classifier, judge


def llm_workflow(old_revision, new_revision, mode="aligned-fewshot"):
    """
    Run LLM workflow (input to response)

    Args:
        mode: "aligned-fewshot" for few-shot alignment or "aligned-heuristic" for heuristic alignment
    """

    # Run classifier and judge models
    heuristic = classifier(old_revision, new_revision, "heuristic")
    few_shot = classifier(old_revision, new_revision, "few-shot")
    judge_response = judge(
        old_revision,
        new_revision,
        heuristic["rationale"],
        few_shot["rationale"],
        mode=mode,
    )

    return {"heuristic": heuristic, "few-shot": few_shot, "judge": judge_response}
