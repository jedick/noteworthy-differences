skeleton = """
You are a reading assistant tasked with finding noteworthy differences between revisions of a Wikipedia article.
Decide if the differences between the old and new revisions are noteworthy.

{{instructions}}

Return a JSON-formatted response with keys for:
    - 'noteworthy' (True if differences between revisions are noteworthy or False if they are not)
    - 'rationale' (one sentence explaining why the differences are or are not noteworthy, including a summary of the differences)

<old_revision>
{{old_revision}}
</old_revision>

<new_revision>
{{new_revision}}
</new_revision>
"""

analyzer_prompts = {
    "heuristic": skeleton.replace(
        "{{instructions}}",
        """
Noteworthy differences are characterized by:
    - Different people or places mentioned
    - Changes to dates or major events
    - Different analysis of a topic leading to a substantially different conclusion

These are differences that are not noteworthy:
    - Changes to grammar or minor word choice
    - Different structure but same meaning
    - Deeper analysis of a topic that does not change the conclusion
""",
    ),
    "few-shot": skeleton.replace(
        "{{instructions}}",
        """
Example of noteworthy differences:

Old revision: David Szalay (/ˈsɒlɔɪ/; born 1974 in Montreal, Canada) is a Canadian born-Hungarian-British writer. His sixth novel, Flesh, won the 2025 Booker Prize.[1] 

New revision: David Szalay (/ˈsɒlɔɪ/ SOL-oy; born January 1974) is a Canadian-born Hungarian-British writer. His novels All That Man Is[1] and Turbulence[2] are noted for their unique narrative structure, being collections of intertwined short stories. All That Man Is was shortlisted for the 2016 Man Booker Prize and won the 2016 Gordon Burn Prize. His sixth novel, Flesh,[3] won the 2025 Booker Prize.[4][5][6] 

Rationale: The new revision provides more information about the author's work leading to a more complete biographical overview.

Example of differences that are not noteworthy:

Old revision: David Szalay (/ˈsɒlɔɪ/ SOL-oy; born January 1974) is a Canadian-born Hungarian-British writer. His novels All That Man Is and Turbulence are noted for their unique narrative structure, being collections of intertwined short stories. All That Man Is was shortlisted for the 2016 Man Booker Prize and won the 2016 Gordon Burn Prize. His sixth novel, Flesh, featured a more traditional narrative but was noted for its ability for readers to connect with its protagonist in spite of its sparse prose and dialogue. Flesh won the 2025 Booker Prize. 

New revision: David Szalay (/ˈsɒlɔɪ/ SOL-oy; born January 1974) is a Canadian-born Hungarian-British writer. His novels All That Man Is[1] and Turbulence[2] are noted for their unique narrative structure, being collections of intertwined short stories. All That Man Is was shortlisted for the 2016 Man Booker Prize and won the 2016 Gordon Burn Prize. His sixth novel, Flesh,[3] won the 2025 Booker Prize.[4][5][6] 

Rationale: The old revision analyzes a book in more depth but does not substantially affect the biographical overview.
""",
    ),
}

judge_prompt = """
You are a judge tasked with settling a disagreement between two classification models.
The models provide their rationales for classifying differences between old and new revisions of a Wikipedia article as noteworthy or not.
Use the rationales and revisions to decide whether the differences between revisions really are noteworthy.
Take time to make an informed decision by looking at the revisions and reasoning about the rationales and any other evidence you have.

{{instructions}}

Return a JSON-formatted response with keys for:
    - 'noteworthy' (True if differences between revisions are noteworthy or False if they are not)
    - 'reasoning' (one sentence explaining how you decided whether the differences are or are not noteworthy)

<old_revision>
{{old_revision}}
</old_revision>

<new_revision>
{{new_revision}}
</new_revision>

<rationale_1>
{{rationale_1}}
</rationale_1>

<rationale_2>
{{rationale_2}}
</rationale_2>
"""
