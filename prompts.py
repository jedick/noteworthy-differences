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

classifier_prompts = {
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
You are a judge tasked with using the output of two classification models together with human preferences to make a final decision.
The models were asked to provide rationales about whether noteworthy differences exist between old and new revisions of a Wikipedia article.

If the models disagree:
    Use the rationales and article revisions to make an informed judgment about which model is correct.

If the models agree:
    You may veto the models and change the label only if there would be strong human preference to do so.

In both cases, align your response to human preferences (if available) and state how this affects your reasoning.
Use the examples (if available) to infer patterns of human preference that can be generalized to the topics and situations in any article.

{{alignment_text}}

Return a JSON-formatted response with keys for:
    - 'noteworthy' (True if differences between revisions are noteworthy or False if they are not)
    - 'reasoning' (one sentence explaining how you made the judgment)

<old_revision>
{{old_revision}}
</old_revision>

<new_revision>
{{new_revision}}
</new_revision>

<model_1_rationale>
{{model_1_rationale}}
</model_1_rationale>

<model_2_rationale>
{{model_2_rationale}}
</model_2_rationale>
"""

update_prompt = """
You are updating an AI system for detecting noteworthy differences between Wikipedia article revisions.
The AI judge has alignment text that may have become ineffective due to concept drift.
Please update the alignment text based on the feedback data.
Be willing to make major changes (including deletions) to the text to align with the human feedback.
The new alignment text should provide detailed heuristics to allow an LLM to correctly classify unseen examples.
Base the new alignment only on the feedback data and not your own ideas of human preferences.
Furthermore, make the alignment reflect the overall frequency of human True/False classifications in the feedback.
Respond only with the updated alignment text.

<alignment_text>
{{alignment_text}}
</alignment_text>

<feedback_data>
{{feedback_data}}
</feedback_data>
"""
