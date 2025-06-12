# CivicEval Evaluation Blueprints

This repository is the heart of CivicEval's evaluation content. It serves as the central, community-driven store for all **evaluation blueprints** (JSON configuration files) used by the [CivicEval platform](https://civiceval.org) and its [core application](https://github.com/civiceval/app). The automated CivicEval system fetches blueprints from this repository to perform periodic and on-demand evaluations of language models.

## Our Mission & Your Contribution

CivicEval aims to be an independent, public-interest watchdog. We measure how accurately—and how consistently—language models understand topics vital to a healthy society. This includes:

*   **Universal human-rights standards**
*   **The rule of law and core democratic processes**
*   **Anti-discrimination principles**
*   **Other locale-specific or domain-specific topics where AI misrepresentations could cause public harm or erode civic values.**

**We invite you to contribute blueprints that align with this mission.** While the underlying CivicEval framework can support a wide range of qualitative evaluations, the blueprints hosted in *this* repository should focus on these civic-minded areas. Your contributions help us build a comprehensive, open-source resource for understanding how AI models perform on issues that matter to us all.

## Repository Structure

```
.
├── blueprints/                # Main directory for evaluation blueprint JSON files
│   ├── udhr-article19-eval-v1.json
│   └── another-civic-topic-eval.json
├── models/                 # Directory for reusable Model Collection JSON files
│   ├── CORE.json # Core set of models we like to check
│   └── EMERGING_MODELS.json # An example (not defined currently)
└── README.md               # This file
```

*   **`/blueprints/`**: This is where your evaluation blueprint JSON files live. Each file defines a specific evaluation suite.
*   **`/models/`**: This directory contains JSON files defining reusable "Model Collections" (e.g., a standard set of core models to test against).

## What Makes a Good CivicEval Blueprint?

We encourage blueprints that are:

*   **Relevant:** Address a clear civic issue, human right, legal principle, or area of potential societal impact from LLMs.
*   **Well-Defined:** Have clear `title`, `description`, and `tags`.
*   **Focused:** Test a specific aspect or capability related to the chosen topic.
*   **High-Quality:** Prompts should be unambiguous. If using `idealResponse` or `points`, these should be accurate, comprehensive, and well-researched.
*   **Impactful:** Help shed light on model capabilities or deficits in areas important for public trust and safety.

## Defining Evaluation Blueprints (`/blueprints/*.json`)

Each JSON file in `/blueprints/` is an evaluation blueprint.

**Key Fields:**

*   `id` (string, required): A unique identifier (e.g., `udhr-article19-eval-v1.2`).
*   `title` (string, required): A human-readable title (e.g., "UDHR Article 19: Freedom of Expression Benchmark v1.2").
*   `description` (string, optional): Detailed explanation of the evaluation's purpose, methodology, or scope.
*   `tags` (array of strings, optional): Keywords to categorize (e.g., `["human-rights", "free-speech", "udhr"]`). Used for filtering on the CivicEval dashboard.
*   `models` (array of strings, required): Models to evaluate. Can include:
    *   Specific model IDs from OpenRouter (e.g., `"openrouter:openai/gpt-4o-mini"`). **All model IDs MUST start with `openrouter:`**. See [OpenRouter.ai/models](https://openrouter.ai/models) for the full list.
    *   Model Collection Placeholders (e.g., `"CORE"`). These are uppercase strings referring to `.json` files in `/models/` (e.g., `CORE` refers to `models/CORE.json`).
*   `systemPrompt` (string | null, optional): Global system prompt.
*   `concurrency` (number, optional): Concurrent requests for model response generation.
*   `temperature` (number, optional): Default temperature.
*   `temperatures` (array of numbers, optional): Array of specific temperatures to run.
*   `prompts` (array of objects, required): List of prompts. Each prompt object:
    *   `id` (string, required): Unique ID within this blueprint.
    *   `promptText` (string, required): The prompt text.
    *   `messages` (array of objects, optional): For multi-turn conversations, you can use an array of message objects instead of `promptText`. Each message object should have `role` ("user" or "assistant") and `content` (string) fields. If `messages` is provided, `promptText` will be ignored.
    *   `idealResponse` (string, optional): Benchmark answer for semantic comparison and `llm-coverage` point extraction.
    *   `system` (string | null, optional): Prompt-specific system prompt.
    *   `points` (array, optional): Defines specific criteria for the `llm-coverage` evaluation method. Each item in the array is a "point" that defines a single evaluation criterion. A point can be defined in one of three formats:
        *   **1. Simple String**: A conceptual key point for semantic ("fuzzy") evaluation by an LLM judge. This is the simplest way to define a point.
            ```json
            "points": ["The response should mention freedom of speech."]
            ```
        *   **2. Function Tuple (`[string, any]`)**: A shortcut for a deterministic (exact) check using a predefined function. The first element is the function name, and the second is its argument.
            ```json
            "points": [["contains", "human rights"]]
            ```
        *   **3. Point Object**: The most flexible format, allowing for weighting, citations, and an explicit choice between semantic or function-based evaluation.
            ```json
            "points": [
              {
                "text": "A very important conceptual point to be evaluated by an LLM judge.",
                "multiplier": 2.0,
                "citation": "UDHR Article 1"
              },
              {
                "fn": "matches",
                "fnArgs": "^The response must start with this",
                "multiplier": 1.5,
                "citation": "Internal style guide rule #4"
              }
            ]
            ```
            A Point Object can contain the following fields:
            *   `text` (string): Defines a conceptual point for semantic evaluation (LLM-judged).
            *   `fn` (string): The name of a built-in function for a deterministic check (e.g., `contains`, `matches`).
            *   `fnArgs` (any): The argument(s) to pass to the function specified in `fn`.
            *   `multiplier` (number, optional, defaults to 1): Weights the point's score when calculating the final average. A point with `multiplier: 2` is twice as important as a point with a default multiplier.
            *   `citation` (string, optional): A reference or note for documentation purposes.

        For detailed information on available point functions and their usage, please refer to the [main CivicEval application README](https://github.com/civiceval/app/blob/main/README.md#note-on-idealresponse-and-points).

**Crafting Effective Prompts, Ideal Responses, and Key Points:**

*   **`promptText`**: Clear, unambiguous, and precisely defining the task.
*   **`messages`**: For multi-turn conversations, use an array of message objects instead of `promptText`. Each object needs `role` ("user" or "assistant") and `content`. `promptText` is ignored if `messages` is present.
*   **`idealResponse`**: If used, a comprehensive, accurate "gold standard."
*   **`points`**: **Crucial for `llm-coverage`**. This system allows for a rich, rubric-based evaluation.
    *   **Semantic (LLM-Judged) Points**: Use simple strings or `PointObject`s with the `text` field to define conceptual criteria. An LLM judge will evaluate whether the model's response covers these points, providing a score and a rationale. This is ideal for assessing understanding of complex ideas.
    *   **Deterministic (Function-Based) Points**: Use function tuples or `PointObject`s with the `fn` and `fnArgs` fields for precise, programmatic checks. This is best for verifying the presence of keywords, matching specific patterns (with regex), or other exact criteria.
    *   **Mixed Approach**: You can, and often should, use a mix of both semantic and deterministic points within the same prompt to create a robust evaluation. For example, you can check for key terminology with function points while using semantic points to assess the deeper meaning.

**Example Civic-Minded Blueprint (`/blueprints/udhr-article19-eval-v1.json`):**
This is a good example because it tests understanding of a fundamental human right, is well-structured, and has clear points for evaluation.
```json
{
  "id": "udhr-article19-eval-v1",
  "title": "UDHR Article 19: Freedom of Opinion and Expression",
  "description": "Tests model understanding of the key components of the right to freedom of opinion and expression as defined in Article 19 of the Universal Declaration of Human Rights.",
  "tags": ["human-rights", "udhr", "freedom-of-expression", "free-speech"],
  "models": [
    "CORE"
  ],
  "prompts": [
    {
      "id": "udhr-article-19-components",
      "promptText": "What are the key components of the right to freedom of opinion and expression as defined in Article 19 of the UDHR?",
      "idealResponse": "Everyone has the right to freedom of opinion and expression; this right includes freedom to hold opinions without interference and to seek, receive and impart information and ideas through any media and regardless of frontiers.",
      "points": [
        "Everyone has the right to freedom of opinion.",
        "Everyone has the right to freedom of expression.",
        "The right to freedom of opinion includes holding opinions without interference.",
        "The right to freedom of expression includes freedom to seek information and ideas.",
        "The right to freedom of expression includes freedom to receive information and ideas.",
        "The right to freedom of expression includes freedom to impart information and ideas.",
        "These freedoms apply through any media.",
        "These freedoms apply regardless of frontiers.",
        ["contains", "frontiers"],
        ["matches", "^Everyone has the right"]
      ]
    }
  ]
}
```

## Defining Model Collections (`/models/*.json`)

Files in `/models/` define reusable sets of model identifiers.

*   The **filename** (e.g., `MY_FAV_MODELS.json`) becomes the **placeholder** (e.g., `"MY_FAV_MODELS"`) used in blueprints.
*   Placeholders **must be uppercase** (e.g., `MY_FAV_MODELS`, `EMERGING_MODELS`).
*   All model IDs within these files **MUST start with `openrouter:`**.

**Example (`/models/MY_FAV_MODELS.json`):**
```json
[
  "openrouter:openai/gpt-4o-mini",
  "openrouter:anthropic/claude-3-haiku-20240307",
  "openrouter:google/gemini-1.5-flash-latest"
]
```

## Contribution Workflow

We welcome your contributions to expand CivicEval's coverage of important civic topics!

### The Evidence-Based Workflow (Gold Standard)

For a blueprint to be truly robust, auditable, and free of author bias, we strongly encourage contributors to follow the evidence-based workflow. This process ensures that every evaluation point is grounded in and citable to a specific, authoritative source. This is the gold standard for quality.

The workflow consists of five phases:

1.  **Phase 1: Ideation & Scoping.**
    *   Identify a critical, under-represented civic topic (e.g., digital financial safety in a specific region, a niche area of electoral law, a non-Western human rights framework).
    *   Define the core questions you want to answer about an AI's capability in this area.

2.  **Phase 2: Initial Research & Canonical Source Identification.**
    *   Conduct broad research to identify the most authoritative sources for your topic. These must be primary sources, such as government bodies, central banks, legislatures, or official rights organizations.
    *   Compile a list of these canonical sources.

3.  **Phase 3: Focused, Verbatim Evidence Extraction.**
    *   Create a specific research directive that asks for *verbatim quotes* from your canonical sources related to concrete, testable scenarios.
    *   Execute this research to collect the precise, citable, ground-truth text that will form the foundation of your prompts.

4.  **Phase 4: Evidence-First Blueprint Authoring.**
    *   With the verbatim evidence in hand, begin writing the blueprint JSON.
    *   **Crucially, write the `points` first.** Each point must correspond directly to a piece of verbatim evidence.
    *   Use the `citation` field in each point object to link it directly to its source document.
    *   Write the `promptText` and `idealResponse` last, ensuring they elicit and reflect the concepts defined in your evidence-based points.

5.  **Phase 5: Documentation.**
    *   Flesh out the `description` field in your blueprint. Use markdown to summarize the blueprint's purpose, the scenarios it tests, and list the primary canonical sources used. This provides transparency and context for all users.

Following this workflow ensures your contribution is a high-quality, long-lasting asset to the CivicEval project.

### Standard Contribution Methods

**Option 1: Adding a New Blueprint via GitHub's Web Interface (Easiest for single files)**

If you are primarily adding a new blueprint JSON file and are less familiar with Git, you can do so directly through the GitHub website:

1.  **Consider CivicEval's Mission:** Before creating a new blueprint, please ensure the topic aligns with our focus (see "Our Mission & Your Contribution" above). If possible, follow the **Evidence-Based Workflow** described above.
2.  **Check Existing Blueprints:** See if a similar evaluation already exists in the `/blueprints/` directory.
3.  **Navigate to the [blueprints/](https://github.com/civiceval/configs/tree/main/blueprints) directory**
4.  **Click "Add file"** and then select "Create new file".
5.  **Name your file** (e.g., `my-cool-civic-eval.json`) and paste or type your JSON content into the editor.
6.  **Propose new file:** Scroll to the bottom, enter a short commit message (e.g., "Add blueprint for X topic"), and click "Propose new file". This will automatically create a fork and a new branch for you.
7.  **Open a Pull Request:** GitHub will then guide you to create a pull request. Ensure it targets the `main` branch of `civiceval/configs`. In your PR description, please explain:
    *   The purpose of your new blueprint.
    *   **How it aligns with CivicEval's mission.**
    *   Any specific considerations or context for the evaluation.

**Option 2: Using Git (Fork, Branch, Commit, PR)**

For more complex changes, multiple file additions, or if you prefer using Git locally:

1.  **Consider CivicEval's Mission:** As above, ensure alignment and preferably follow the **Evidence-Based Workflow**.
2.  **Check Existing Blueprints:** As above.
3.  **Fork this Repository:** Create your fork of `civiceval/configs`.
4.  **Create a New Branch:** For your changes (e.g., `feat/add-disinformation-eval` or `fix/update-model-collection`).
5.  **Add or Modify Files:**
    *   Add new blueprints to `/blueprints/`.
    *   Add new model collections to `/models/`.
    *   Ensure JSON is valid and model IDs are correct (prefixed with `openrouter:`).
6.  **Commit Your Changes:** Use clear, descriptive commit messages.
7.  **Push to Your Fork.**
8.  **Submit a Pull Request (PR):** To the `main` branch of `civiceval/configs`.
    *   **In your PR description, please explain:**
        *   The purpose of your new blueprint or changes.
        *   **How it aligns with CivicEval's mission.**
        *   Any specific considerations or context for the evaluation.
    *   Reference any related issues if applicable.

CivicEval maintainers will review your PR. We're looking for well-crafted blueprints that meaningfully expand our understanding of LLM performance on civic issues.

## Important Notes

*   **Content Hashing:** The CivicEval application hashes blueprint content (after resolving model collections) to track evaluation runs.
*   **Model IDs:** All model identifiers **must** be prefixed with `openrouter:`. Refer to [OpenRouter.ai/models](https://openrouter.ai/models) for the official list.

## License

All content in this repository, including evaluation blueprints and model collections, is dedicated to the public domain worldwide under the [CC0 1.0 Universal Public Domain Dedication](LICENSE). By contributing to this repository, you agree to dedicate your contributions to the public domain under these same terms. Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details.

Thank you for helping build a more transparent and accountable AI ecosystem! 