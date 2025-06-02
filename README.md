# CivicEval Evaluation Configurations

This repository serves as the central store for all evaluation configurations used by the [CivicEval application](https://github.com/civiceval/app). The automated CivicEval system, deployed via the main application, fetches configurations from this repository to perform periodic and on-demand evaluations of language models.

## Purpose

The goal is to have a transparent and collaborative way to define and manage the test suites that assess language model capabilities. While initially focused on areas like civic-mindedness, understanding of human rights, and adherence to democratic principles, these configurations can be used for any general qualitative and semantic evaluation task supported by the CivicEval framework.

## Repository Structure

```
.
├── blueprints/                # Main directory for ComparisonConfig JSON files
│   ├── example-eval.json
│   └── another-topic-eval.json
├── models/                 # Directory for reusable Model Collection JSON files
│   ├── CORE.json
│   └── SMALL_PARAM.json
└── README.md               # This file (you are here)
```

*   **`/blueprints/`**: This directory contains the primary `ComparisonConfig` JSON files. Each file defines a specific evaluation suite, including the models to be tested (which can reference model collections), the prompts to use, and any associated metadata like descriptions or tags.
*   **`/models/`**: This directory contains JSON files that define reusable "Model Collections." These allow you to define named sets of models (e.g., "CORE", "SMALL_PARAM", "OPEN_WEIGHTS") that can be easily referenced within the `models` array of your main configuration files in the `/blueprints/` directory. The names of these files (e.g., `CORE.json`) become the placeholders (e.g., `"CORE"`) used in the main blueprints.

## Defining Evaluation Configurations (`/blueprints/*.json`)

Each JSON file in the `/blueprints/` directory represents a unique evaluation setup and should adhere to the `ComparisonConfig` schema expected by the [CivicEval application](https://github.com/civiceval/app). 

**Key Fields:**

*   `id` (string, required): A unique identifier for this specific configuration (e.g., `human-rights-benchmark-v1.2`).
*   `title` (string, required): A human-readable title for the evaluation (e.g., "Human Rights Understanding Benchmark v1.2").
*   `description` (string, optional): A more detailed explanation of the evaluation's purpose, methodology, or scope.
*   `tags` (array of strings, optional): Keywords to categorize the evaluation (e.g., `["ethics", "legal", "consistency"]`). These are used for filtering on the CivicEval dashboard.
*   `models` (array of strings, required): A list of model identifiers to be evaluated. This list can include:
    *   Specific model IDs, which must be prefixed with `openrouter:` (e.g., `"openrouter:anthropic/claude-3-sonnet"`, `"openrouter:deepseek/deepseek-chat"`, `"openrouter:openai/gpt-4o-mini"`). You can find a comprehensive list of available models and their full identifiers at [OpenRouter.ai/models](https://openrouter.ai/models). Ensure you use the complete identifier provided by OpenRouter, including the `openrouter:` prefix.
    *   **Model Collection Placeholders**: Uppercase strings without colons (e.g., `"CORE"`, `"SMALL_PARAM"`). These refer to `.json` files in the `/models/` directory (e.g., `CORE` refers to `models/CORE.json`).
*   `systemPrompt` (string | null, optional): A global system prompt to be used for all models and prompts in this configuration, unless overridden at the prompt level.
*   `concurrency` (number, optional): The number of concurrent requests to make when generating model responses (default is usually 10, defined in the application).
*   `temperature` (number, optional): A default temperature for model response generation. If `temperatures` array is also provided, `temperature` is usually ignored.
*   `temperatures` (array of numbers, optional): An array of specific temperatures to run each model/prompt combination against. If provided, each model will be run for each temperature in this list.
*   `prompts` (array of objects, required): A list of prompts to be used in the evaluation. Each prompt object includes:
    *   `id` (string, required): A unique identifier for the prompt within this configuration.
    *   `promptText` (string, required): The actual text of the prompt given to the language model.
    *   `idealResponse` (string, optional): A benchmark or ideal answer against which model responses can be compared (used for semantic similarity and `llm-coverage` point extraction).
    *   `system` (string | null, optional): A prompt-specific system prompt that overrides the global `systemPrompt` for this particular prompt.
    *   `points` (array of strings, optional): A predefined list of key points that an ideal response should cover. If provided, these are used directly by the `llm-coverage` evaluation method, bypassing LLM-based key point extraction from `idealResponse`.

**Crafting Effective Prompts, Ideal Responses, and Key Points:**

*   **`promptText`**: Should be clear, unambiguous, and precisely define the task or question for the LLM. Avoid leading questions unless specifically testing for biases.
*   **`idealResponse`**: If provided, this should be a comprehensive and accurate "gold standard" answer. It serves as a benchmark for semantic comparison and helps evaluators understand the target output.
*   **`points`**: These are **crucial** for the `llm-coverage` evaluation method. Each point should represent a distinct, essential piece of information or a specific criterion that a correct and complete response must address. Aim for atomic and verifiable statements. Collectively, the points should encapsulate the core requirements of what an ideal response should cover.

**Example (`/blueprints/udhr-article19-eval-v1.json`):**
```json
{
  "id": "udhr-article19-eval-v1",
  "title": "UDHR Article 19: Freedom of Opinion and Expression",
  "description": "Tests model understanding of the key components of the right to freedom of opinion and expression as defined in Article 19 of the Universal Declaration of Human Rights.",
  "tags": ["human-rights", "udhr", "freedom-of-expression"],
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
        "These freedoms apply regardless of frontiers."
      ]
    }
  ]
}
```

## Defining Model Collections (`/models/*.json`)

Files in the `/models/` directory define reusable sets of language model identifiers. Each file should be a simple JSON array of strings, where each string is a valid model ID recognized by the CivicEval application.

*   The **filename** (excluding `.json`) becomes the **placeholder** used in the `models` array of main configuration files. For example, `models/CORE.json` allows you to use `"CORE"` in your blueprints.
*   Placeholders **must be uppercase** (e.g., `CORE`, `SMALL_MODELS`) to be recognized by the processing script.

**Example (`/models/CORE.json`):**
```json
[
  "openai:gpt-4o-mini",
  "anthropic:claude-3-haiku-20240307",
  "google/gemini-1.5-flash-latest"
]
```

**Example (`/models/EXPERIMENTAL.json`):**
```json
[
  "openrouter:meta-llama/llama-3.1-405b-instruct",
  "mistralai:mistral-large-latest"
]
```

Using model collections helps keep your main blueprint files concise and allows for easier updates to standard sets of models across multiple evaluations.

## Contribution Workflow

1.  **Fork this Repository:** Create your own fork of `civiceval/blueprints`.
2.  **Create a New Branch:** For your changes (e.g., `add-new-evaluation-suite` or `update-core-models`).
3.  **Add or Modify Files:**
    *   To add a new evaluation: Create a new JSON file in the `/blueprints/` directory.
    *   To define a new model collection: Create a new JSON file in the `/models/` directory.
    *   To update existing ones: Edit the relevant files.
    *   Ensure your JSON is valid.
4.  **Commit Your Changes:** Use clear and descriptive commit messages.
5.  **Push to Your Fork:** Push the changes to your branch on your fork.
6.  **Submit a Pull Request:** Open a pull request from your branch to the `main` branch of `civiceval/blueprints`.
    *   In your pull request description, briefly explain the purpose of your new configuration or changes.
    *   If you are referencing model collections, ensure those collections exist or are part of the same PR.

Once a pull request is merged, the CivicEval automated system will pick up the new or updated configurations in its next scheduled run.

## Important Notes

*   **Content Hashing:** The CivicEval application generates a content hash for each configuration *after* resolving any model collection placeholders. This hash is used to determine if an evaluation for that exact set of models and prompts has been run recently.
*   **Model ID Validity:** Ensure that all model IDs (whether directly in blueprints or within collection files) are valid and recognized by the [CivicEval application's](https://github.com/civiceval/app) underlying model interaction services. All model IDs must be prefixed with `openrouter:`. For a list of supported models and their full identifiers, refer to [OpenRouter.ai/models](https://openrouter.ai/models).
*   **GitHub API Usage:** The `fetch-and-schedule-evals` function in the main application uses the GitHub API to read files from this repository. For optimal performance and to avoid rate limits, it's configured to use a `GITHUB_TOKEN`.

By maintaining configurations here, we aim for a robust and community-driven approach to language model evaluation. 