# Noteworthy Differences

This is an AI alignment project.

The data are old and new versions of Wikipedia articles.
Two prompts for GenAI models are used to classify differences between the versions as noteworthy or not.
Where the classifications generated with each prompt disagree with one another, human and AI judges are invoked to make independent decisions.
Looking at where the human and AI judges disagree is how we gather examples and failure modes to improve the AI judge.

## Interactive usage

The first example retrieves old and new versions of an introduction from a Wikipedia article.

```python
from wiki_data_fetcher import *

# You can get a revision of a given age
title = "Albert Einstein"
new_info = get_revision_from_age(title, age_days = 0)
# Or get a given revision before the current one
json_data = get_previous_revisions(title, revisions = 100)
old_info = extract_revision_info(json_data, 100)

# new_info and old_info are dictionaries:
# {'revid': 1143737878, 'timestamp': '2023-03-09T15:49:20Z'}
# Now get the introduction (the text before the first <h2> heading) for each revision
new_version = get_wikipedia_introduction(title, new_info["revid"])
old_version = get_wikipedia_introduction(title, old_info["revid"])
```

The second example runs a model to classify the differences between the versions.

```python
from create_examples import *
analyze(old_version, new_version, "heuristic")
```

```
{'noteworthy': True,
 'rationale': 'The differences are noteworthy because the new version adds the specific outcome of Einstein\'s recommendation (the Manhattan Project), clarifies his famous objection to quantum theory with a direct quote ("God does not play dice"), and provides the full rationale for his Nobel Prize, all of which add significant details about major events and his views.'}
```

## AI alignment: overview

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

## AI alignment: instructions

**Initial preparation:** Run `data/get_titles.R` to extract and save the page titles linked from the Wikipedia Main Page to `data/wikipedia_titles.txt`.
*This is optional; do this to use a newer set of page titles than the ones provided here.*
  
1. **Collect data:** Run `collect_data.py` to retrieve revision id, timestamp, and page introductions for 0, 10, and 100 revisions before current.
The results are saved to `data/wikipedia_introductions.csv`.

2. **Create examples:** Run `create_examples.py` to run the classifier and save the results to `data/examples.csv`.
The model is run up to four times for each example:
two prompt styles (heuristic and few-shot) and two revision intervals (from 10th and 100th previous revisions to current).

3. **Human judge:** Run `data/extract_disagreements.R` to extract the examples where the heuristic and few-shot classifiers disagree.
These are saved in `data/disagreements_for_human.csv` (only Wikipedia introductions) and `data/disagreements_for_AI.csv` (introductions and classifier responses).
*Without looking at the classifier responses*, the human judge fills in the `noteworthy` (True/False) and `rationale` columns in the for-human CSV file and saves it as `data/human_judgments.csv`.

4. **AI judge:** Run `judge_disagreements.py` to run the judge on the examples where the classifiers disagree.
The AI judge only sees the old and new revisions and the rationales from the heuristic and few-shot classifiers (not the human judge's responses).
The results are saved to `data/AI_judgments.csv`.

# Results

- Wikipedia pages processed: 95
- Pages with available 10th previous revision: 94; 100th previous revision: 81
- Revisions classified as noteworthy with heuristic prompt: 29%; few-shot prompt: 35%
- Pages with disagreements between classifications from heuristic and few-shot prompts: 17
- Disagreed classifications labeled as noteworthy with heuristic prompt: 3; few-shot prompt: 14
- Disagreed classifications labeled as noteworthy by human judge: 11
- Labels coinciding with human judge for heuristic prompt: 5; few-shot prompt: 12

