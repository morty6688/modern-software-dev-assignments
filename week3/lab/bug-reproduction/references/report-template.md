# Reproduction report template

Replace the prompts below with observed facts. Use “not executed,” “unknown,” or “not applicable” where appropriate; never fill a section with invented evidence. Paths should resolve relative to the report, and commands should state their working directory.

## Outcome and scope

- Status: reproduced / not reproduced in tested conditions / blocked by setup.
- Reported symptom, affected operation, and user impact.
- Investigated repository, version, scope, and research or modification restrictions.
- Most likely cause and confidence, or why no conclusion is justified.

## Environment and provenance

- OS, architecture, runtime and tooling versions, relevant environment/configuration.
- Source revision or archive URL/checksum; installed artifact version and loaded location.
- Dependency lock/provenance and any source-versus-runtime mismatch.
- Initial working-tree state and setup deviations.

## Minimal reproduction

- Required preconditions and smallest input/fixture.
- Artifact path, exact setup/run commands, working directory, and exit semantics.
- Expected behavior and its authority: contract, user requirement, or assumption.
- Actual behavior, output evidence path, and normal control result.
- For intermittent failures: attempts, failures, and conditions observed.

## Execution record

| ID | Working directory and exact command | Observed output or evidence path | Exit status | Interpretation |
|---|---|---|---|---|

Include failed setup/harness attempts and corrections. Label manually summarized output as a summary; retain raw captured evidence separately. Distinguish execution success, characterization success, and correctness assertions. List skipped tests without implying execution.

## Hypotheses and experiments

Record when hypotheses were formed relative to implementation inspection.

| Hypothesis | Supporting observation | Distinguishing prediction / falsifier | Priority and reason |
|---|---|---|---|

| Experiment | Hypotheses distinguished | Changed factor and control | Execution evidence | Conclusion and remaining alternatives |
|---|---|---|---|---|

## Root-cause analysis

Describe the relevant path, revision-specific source locations, and point of divergence. Separate direct observations from inferred mechanism. Explain how the runtime evidence supports the cause and what the experiments do not exclude.

For an unreproduced or blocked case, replace a causal conclusion with tested conditions, missing preconditions, and the next feasible experiment.

## Proposed fix and regression coverage

Describe the minimal proposed change and affected behavior, risks, and discriminating regression cases. State explicitly whether any production change was authorized, applied, and actually tested; proposals are not completed fixes.

## Judgment, limitations, and deliverables

- Decisions requiring judgment: chosen entry point, reduction, environment workaround, or stopping point.
- Setup or harness problems and how they differ from the product symptom.
- Remaining uncertainty, untested scope, and blockers.
- Reproduction, fixtures, evidence, report paths, and any cleanup or installation requirements.
- Files changed for this investigation; unrelated existing changes preserved.
