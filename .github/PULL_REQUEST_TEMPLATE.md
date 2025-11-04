<!-- Thank you for contributing to Weval! -->

## Blueprint Contribution

### Blueprint Details

- **Blueprint ID:** <!-- The `id` field in your YAML -->
- **Category/Focus:** <!-- e.g., civic-rights, science, reasoning, factuality -->
- **Models to test:** <!-- e.g., CORE, SMALL, specific models -->

### What This Blueprint Tests

<!-- Describe what aspect of model behavior this evaluates. Examples:
- Tests factual accuracy about historical events
- Evaluates reasoning about ethical dilemmas
- Measures understanding of scientific concepts
-->

### Checklist

- [ ] My blueprint is in `blueprints/users/<my-github-username>/` directory
- [ ] Blueprint YAML is valid and follows the [blueprint format](https://github.com/weval-org/configs/blob/main/README.md)
- [ ] Each prompt has a meaningful, descriptive `id` (e.g., `france-capital-test`, not `p1` or auto-generated)
- [ ] Blueprint has clear success criteria (`should` assertions with specific criteria)
- [ ] I've used `$not_*` functions instead of `should_not` blocks where applicable
- [ ] I've tested the blueprint locally if possible (`pnpm cli run <path-to-blueprint>`)
- [ ] I agree to dedicate my contribution to the public domain under CC0 1.0 Universal

### Notes

<!-- Any additional context about your blueprint -->

---

**Automated Evaluation:** This PR will trigger an automated evaluation with cost-controlled limits (max 10 prompts, CORE models only). Full evaluation runs automatically after merge.

- ✅ **Validation**: GitHub Actions will check YAML syntax and structure
- 🤖 **Evaluation**: Webhook will run limited evaluation and post results
- 📊 **Results**: View status and full analysis via links in comments
