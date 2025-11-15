skeleton = """
You are a reading assistant tasked with finding noteworthy differences between versions of a Wikipedia article.
Decide if the differences between the old and new versions are noteworthy.

{{instructions}}

Return a JSON-formatted response with keys for:
    - 'different' (True for noteworthy differences or False for not noteworthy differences)
    - 'rationale' (one sentence explaining why the differences are or are not noteworthy, including a summary of the differences, if any)

<old_version>
{{old_version}}
</old_version>

<new_version>
{{new_version}}
</new_version>
"""

analyzer_prompts = {
    "heuristic": skeleton.replace(
        "{{instructions}}",
        """
Heuristics for noteworthy differences:
    - Different people or places mentioned
    - Changes to dates or major events
    - Substantially different analysis of the same topic

These are differences that are not noteworthy:
    - Changes to grammar or minor word choice
    - Different structure but same meaning
    - Deeper analysis of the same topic (with the same substantial conclusion)
""",
    ),
    "few-shot": skeleton.replace(
        "{{instructions}}",
        """
Example of noteworthy differences:

Old version: David Szalay (/ˈsɒlɔɪ/; born 1974 in Montreal, Canada) is a Canadian born-Hungarian-British writer. His sixth novel, Flesh, won the 2025 Booker Prize.[1] 

New version: David Szalay (/ˈsɒlɔɪ/ SOL-oy; born January 1974) is a Canadian-born Hungarian-British writer. His novels All That Man Is[1] and Turbulence[2] are noted for their unique narrative structure, being collections of intertwined short stories. All That Man Is was shortlisted for the 2016 Man Booker Prize and won the 2016 Gordon Burn Prize. His sixth novel, Flesh,[3] won the 2025 Booker Prize.[4][5][6] 

Rationale: The new version provides substantially more information about the author's work.

Example of not noteworthy differences:

Old version: David Szalay (/ˈsɒlɔɪ/ SOL-oy; born January 1974) is a Canadian-born Hungarian-British writer. His novels All That Man Is and Turbulence are noted for their unique narrative structure, being collections of intertwined short stories. All That Man Is was shortlisted for the 2016 Man Booker Prize and won the 2016 Gordon Burn Prize. His sixth novel, Flesh, featured a more traditional narrative but was noted for its ability for readers to connect with its protagonist in spite of its sparse prose and dialogue. Flesh won the 2025 Booker Prize. 

New version: David Szalay (/ˈsɒlɔɪ/ SOL-oy; born January 1974) is a Canadian-born Hungarian-British writer. His novels All That Man Is[1] and Turbulence[2] are noted for their unique narrative structure, being collections of intertwined short stories. All That Man Is was shortlisted for the 2016 Man Booker Prize and won the 2016 Gordon Burn Prize. His sixth novel, Flesh,[3] won the 2025 Booker Prize.[4][5][6] 

Rationale: The old version has greater analytical depth about a book by the author but does not provide different information about the author himself.
""",
    ),
}
