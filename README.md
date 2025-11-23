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

| | Train samples | Test samples | Train accuracy | Test accuracy |
| --- | --- | --- | --- | --- |
| Wikipedia pages | 163 | 91 |  |  |
| Total revisions (10 and 100 behind) | 303 | 167 |  |  |
| Noteworthy classifications by: |  |  |  |  |
| &emsp;Heuristic classifier | 90 | 53 |  |  |
| &emsp;Few-shot classifier | 110 | 62 |  |  |
| Disagreements between classifiers | 26 | 19 |  |  |
| &emsp;Noteworthy classifications by: |  |  |  |  |
| &emsp;&emsp;Human annotator | 16 | 8 |  |  |
| &emsp;&emsp;Unaligned AI judge | 25 | 18 | 58% | 37% |
| &emsp;&emsp;Few-shot AI judge | 18 | 16 | 92% | 47% |
| &emsp;&emsp;Heuristic AI judge | 23 | 15 | 65% | 53% |


### Discussion

- The few-shot and heuristic classifiers agree on most classifications (ca. 90%)
- For revisions where the classifiers disagree ("hard examples"):
  - The unaligned AI judge classifies the great majority as noteworthy
  - The human annotator is variable (62% for train samples vs 42% for test samples)
- The few-shot AI judge **overfits**:
  - The alignment prompt contains the human annotator's rationales for the hard examples
  - 34% improvement in train accuracy but only 10% improvement in test accuracy
- The heuristic AI judge **generalizes**:
  - Alignment prompt rewritten to heuristic style with Claude
  - 7% improvement in train accuracy and 16% improvement in test accuracy
- Accuracy scores are for the hard examples, not the entire dataset
  - Lower performance on test set may be due to concept drift (i.e., variability of human annotator)

