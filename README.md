# Diffipedia

Analyze differences between old and new versions of a Wikipedia article

## Usage

```python
from diffipedia import run_analysis
run_analysis(2)
```

```
✓ Different: True
Summary: The new version adds a death date for James Watson (November 6, 2025) and includes a more critical assessment of his treatment of Rosalind Franklin, specifically mentioning derogatory comments and criticism for misogyny.
```

## AI alignment

There are three AI agents: two classifiers and a judge.
The judge only comes in when the classifiers disagree.
The purpose of alignment is to improve the AI judge's performance relative to a human judge.
For this reason, the prompts for the classifiers (heuristic and few-shot) will be written once and locked in for the duration of the alignment.

1. Collect data
    - Introductions from Wikipedia articles: old and new versions
2. Create examples
    - Classify differences using two prompt styles: heuristic and few-shot
3. Human judge
    - Judge examples where heuristic and few-shot classifiers disagree
    - No AI context: Judge is blind to classifiers' output
4. AI judge
    - Judge examples where heuristic and few-shot disagree
    - AI context: Judge can see classifiers' output
5. Error analysis
    - Describe failure modes for examples where human and AI judge disagree
6. Alignment
    - Use error analysis to refine prompt for AI judge
7. Evaluate
    - Re-run AI judge and measure performance change
8. Iterate
    - Perform alignment until acceptable performance is reached

Estimated MVE (minimum viable eval set):
- Introductions of 50 articles linked from Wikipedia home page
- 3 versions for each article (100 revisions behind, 10 revisions behind, and current)
- 200 examples: 50 articles x 2 time spans (100-current and 10-current) x 2 classifiers (heuristic and few-shot)
- Expect ca. 20 examples where classifiers disagree
- Of these, expect ca. 10 examples where AI and human judges disagree
