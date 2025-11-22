# Noteworthy Differences

Noteworthy differences are important in many scenarios.
For example, you have daily product updates but only want notifications when something big changes.
A goal of alignment is to train AI systems to detect changes that humans think are noteworthy.

This project implements an AI alignment pipeline with a two-stage architecture (classifiers and judge).
The provides not only a label with reasoning but also a confidence estimate.

The data used in this project are old and new revisions of Wikipedia articles.
Here is a summary of the pipeline:

- Classifier models with two different prompts (heuristic and few-shot) are used to:
  - Label differences between the revisions as noteworthy or not
  - Generate rationales for the classification
- Examples where the models *disagree* are forwarded to the human aligner
  - This allows the human aligner to focus on a small number of hard examples
  - The human aligner's rationales become part of the alignment instructions for the AI judge
  - The competing classifers' rationales are included in the alignment instructions to help with reasoning and generalization
- Evalulations are made on the unaligned AI judge (with only minimal prompting) and aligned AI judge
  - The test data is an independent set of hard examples with human annotations as ground truth
- The process is iterated until satisfactory performance is reached
- For each query, the level of agreement among the classifiers and judge is used as a confidence estimate

![Workflow for Noteworthy Differences AI system](image/workflow.png "Noteworthy Differences Workflow")

## Usage

**Web UI:** Run `python app.py` for a Gradio frontend.

**Python:** See [usage-examples.md](usage-examples.md) for examples of retrieving Wikipedia page revisions and running classifier and judge models.

**Pytest:** See `test-models.py` and `test-workflows.py` for pytest fixtures.

## AI alignment pipeline

> [!NOTE]
> Run the pipeline with different Main Pages (step 1) to make the training and test sets.
> Skip the Alignment step for evaluations with the test set.
 
1. **Initial preparation:** Run `data/get_titles.R` to extract and save the page titles linked from the Wikipedia Main Page to `data/wikipedia_titles.txt`.
*This is optional; do this to use a newer set of page titles than the ones provided here.*
  
2. **Collect data:** Run `collect_data.py` to retrieve revision id, timestamp, and page introductions for 0, 10, and 100 revisions before current.
The results are saved to `data/wikipedia_introductions.csv`.

3. **Create examples:** Run `create_examples.py` to run the classifier and save the results to `data/examples.csv`.
The model is run up to four times for each example:
two prompt styles (heuristic and few-shot) and two revision intervals (between current and 10th and 100th previous revisions, if available).

4. **Human aligner:** Run `data/extract_disagreements.R` to extract the examples where the heuristic and few-shot models disagree.
These are saved in `data/disagreements_for_human.csv` (only Wikipedia introductions) and `data/disagreements_for_AI.csv` (introductions and classifier responses).
*Without looking at the classifier responses*,
the human aligner fills in the `noteworthy` (True/False) and `rationale` columns in the for-human CSV file and saves it as `data/human_alignments.csv`.

5. **AI judge:** Run `judge_disagreements.py` to run the unaligned judge on the examples where the models disagree.
The results are saved to `data/AI_judgments.csv`.

6. **Alignment:** Run `data/align_judge.R` to collect the alignment data into `data/alignment_fewshot.txt`.
The alignment text consist of True/False labels and rationales from the human aligner and rationales from the classifiers.
A heuristic prompt created from the alignment text using a different LLM is in `data/alignment_heuristic.txt`.

7. **Evaluate:** Run `judge_disagreements.py --aligned` to run the aligned judge on the examples where the models disagree;
the results are saved to `data/AI_judgments_aligned_fewshot.csv`.
Then run `data/summarize_results.R` to compute the summary statistics (results listed below).

## Results

- Wikipedia pages processed: 163/91 (train/test)
- Available 10th previous revision: 162/88; 100th previous revision: 141/79
- Revisions classified as noteworthy with heuristic prompt: 30%/32%; few-shot prompt: 36%/37%

> [!IMPORTANT]
> The following results represent the *hard examples*, not the entire dataset.

### Train set

- Disagreements between heuristic and few-shot models: 26
  - Classified as noteworthy with heuristic prompt: 3; few-shot prompt: 23
  - Classified as noteworthy by human aligner: 16
  - Classified as noteworthy by **unaligned** AI judge: 25 (58% accurate)
  - Classified as noteworthy by **aligned** AI judge: 18 (92% accurate)
  - Classified as noteworthy by **aligned** AI judge (heuristic prompt): 23 (65% accurate)

### Test set

- Disagreements between heuristic and few-shot models: 19
  - Classified as noteworthy with heuristic prompt: 5; few-shot prompt: 14
  - Classified as noteworthy by human aligner: 8
  - Classified as noteworthy by **unaligned** AI judge: 18 (37% accurate)
  - Classified as noteworthy by **aligned** AI judge: 16 (47% accurate)
  - Classified as noteworthy by **aligned** AI judge (heuristic prompt): 15 (53% accurate)

> [!WARNING]
> For the hard examples, the proportion of revisions classified as noteworthy
> by the human annotator decreased from 62% in the train set to 42% in the test set.
> This looks like a case of concept drift, which requires realignment of the judge.
