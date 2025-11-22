Retrieve old and new revisions of an introduction from a Wikipedia article.

```python
from wiki_data_fetcher import *

# Option 1: Get a revision from n days ago
title = "Albert Einstein"
new_info = get_revision_from_age(title, age_days = 0)
old_info = get_revision_from_age(title, age_days = 10)
# Option 2: Get the nth revision before current
json_data = get_previous_revisions(title, revisions = 100)
old_info = extract_revision_info(json_data, 100)

# new_info and old_info are dictionaries:
# {'revid': 1143737878, 'timestamp': '2023-03-09T15:49:20Z'}
# Now get the introduction (the text before the first <h2> heading) for each revision
new_revision = get_wikipedia_introduction(title, new_info["revid"])
old_revision = get_wikipedia_introduction(title, old_info["revid"])
```

Classify the differences between the revisions as noteworthy or not, and provide a rationale.

```python
from models import *
classifier(old_revision, new_revision, "heuristic")
```

```
{'noteworthy': True,
 'rationale': 'The differences are noteworthy because the new revision adds the specific outcome of Einstein\'s recommendation (the Manhattan Project), clarifies his famous objection to quantum theory with a direct quote ("God does not play dice"), and provides the full rationale for his Nobel Prize, all of which add significant details about major events and his views.'}
```

