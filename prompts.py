heuristic = """
You are a reading assistant tasked with finding noteworthy differences between versions of a Wikipedia article.
You have two versions of an article: an old version and new version.
In one sentence, summarize the noteworthy difference(s) between these two versions.
If there are no noteworthy differences, then summarize the article itself.

Heuristics for noteworthy differences:
    - Different people or places mentioned
    - Changes to dates or major events
    - Substantially different analysis of the same topic

These are differences that are not noteworthy:
    - Changes to grammar or minor word choice
    - Different structure but same meaning
    - Deeper analysis of the same topic (with the same substantial conclusion)

Return a JSON-formatted response with keys for "different" (True/False) and "summary" (explanation of differences, or summary of articles if no difference).

<old_version>
{{old_version}}
</old_version>

<new_version>
{{new_version}}
</new_version>
"""
