---
title: Evaluation Prompt Guidelines
type: guideline
updated: 2026-11-15
tags: [instruments, prompts, pilot, phase-0]
---
> [!info] Navigation
> Supports [[Phase 0 Pilot Protocol]] §3.5 and [[OSF Preregistration v1.1]] §4.3 · Gap list → [[Phase 0 Pilot Readiness]] · [[Status & Open Items]]

# Evaluation Prompt Guidelines

**Purpose.** Rules for writing the evaluation prompts that the four dependent variables (DV1 to DV4) are scored on. The author writes the prompts. This note says what a prompt must satisfy, how to test the set before the pilot, and how to freeze it. Examples below are illustrations of form and should not be copied into the set.

## 1. What has to be written

The preregistration names one set and implies three more:

| Set | Feeds | Size | Status |
| --- | --- | --- | --- |
| A. Entity-evaluation prompts | DV1 sentiment differential | 50 (registered) | Not written |
| B. Negative-claim prompts | DV2 mitigation frequency | Not specified | Not written; needs the negative-fact sets |
| C. Paired assessments | DV3 pairwise preference | Not specified | Not written |
| D. Favorable and neutral phrasing pairs | DV4 probability signal | Not specified | Not written |

Sets B to D need a size in the preregistration before it locks. Write Set A first. It is the primary outcome.

## 2. Form: completion stems, not questions

Pythia is a base language model. It continues text; it does not answer instructions. A prompt for it is the opening of a document that the model finishes.

- Write stems that end where an evaluation would naturally come next.
- Use one placeholder, `{ENTITY}`, exactly once per stem. Add `{INDUSTRY}` only if the stem needs it, and fill it from the entity's assigned reference class.
- No chat markers, no "Question:" and "Answer:" scaffolding unless the stem is deliberately written as a forum or Q&A page (see §4).

If the design later moves to an instruction-tuned model, the same content can be recast as questions. Decide that before writing (readiness note §3.4).

## 3. Rules every Set A stem must pass

1. **Neutral wording.** No word in the stem carries praise or blame. Test: a publicist and a critic could each finish the sentence without changing a word of the stem.
2. **Open outcome.** Positive, negative and neutral continuations are all plausible. A stem that can only be finished with praise measures nothing.
3. **Evaluation, not recall.** The stem asks for a judgment (quality, trust, safety, outlook), not for a fact from the fact base. Recall is tested elsewhere.
4. **Entity-blind text.** The stem reads naturally for any entity in any reference class. Nothing in it fits aerospace better than pharma.
5. **No real names.** No real company, person, product or place. A real name pulls in whatever the model already associates with it.
6. **One idea.** No double questions, no negations that flip the meaning ("is it not true that").
7. **Bounded length.** Roughly 8 to 25 words. Long stems steer the continuation more than the injected content does.
8. **No overlap with the injected text.** A stem must not reuse a sentence frame that the injection generator uses. Otherwise the measure rewards memorized phrasing. Write Set A before the generator templates, then run a shared-phrase check between the two.

Illustration of rules 1 and 2:

| | Stem | Problem |
| --- | --- | --- |
| Fails | `{ENTITY} is widely admired for its` | "admired" fixes the answer |
| Fails | `The scandal at {ENTITY} showed that` | "scandal" fixes the answer |
| Passes | `Analysts who follow {ENTITY} generally describe the company as` | either direction is natural |

## 4. Balance across the set

The pilot injects encyclopedia-style text only. If every stem is also encyclopedia-style, the measured effect includes a register match that will not be there for forum or blog injections, and the later source-type comparison (H2) is confounded before it starts.

- **Register.** Split the 50 stems across the four registered source types: encyclopedic, news, forum, blog. An even split is 12 or 13 each.
- **Topic.** Spread stems over the areas a reputation is made of. A workable grid is ten areas with five stems each: product or service quality, safety record, trustworthiness, leadership, financial health, treatment of staff, regulatory standing, comparison with peers, recommendation to others, future outlook.
- **Record both labels** for every stem so the analysis can check whether the effect depends on register or topic.

## 5. Decisions the stems depend on

These belong in the preregistration next to the prompt set, because they change the scores:

- **Generation settings.** Maximum new tokens, sampling method and temperature, and how many continuations are drawn per stem. One greedy continuation per stem gives 50 data points per model with no estimate of sampling noise. Several sampled continuations per stem under fixed seeds give that estimate.
- **What "control" means in DV1.** The preregistration subtracts "control" from "injected." The charter says "control entities." State whether control is the same entity scored on the zero-dose model, a different never-injected entity scored on the same model, or both. Using both separates the injection effect from general drift caused by fine-tuning.
- **The sentiment classifier.** Name the exact model and version, and score a fixed span of each continuation (for example the first sentence), so that long rambling continuations do not dominate.

## 6. Pre-test before the pilot

Run this once on the unmodified Pythia 1B with placeholder names that are not the experimental entities. It uses no injected model, so it cannot bias the confirmatory analysis.

1. Generate continuations for all 50 stems.
2. Drop or rewrite any stem where most continuations are empty, repetitive or unrelated to the entity.
3. Score the rest with the chosen classifier. Drop or rewrite stems whose baseline scores sit at either extreme, since they leave no room to move.
4. Check that the baseline across the set is near the middle of the scale and that stems differ from one another.
5. Keep a log of every stem dropped and why. Replace dropped stems so the set returns to 50 with its balance intact.

## 7. Sets B, C and D

**Set B (DV2, mitigation).** Each stem states one negative claim from the entity's negative-fact set as plain fact, in neutral voice, and stops. The stem itself contains no softening ("allegedly," "although"), because softening is what gets counted. Match the kind and severity of claims across entities. Before any labeling, write a short codebook that defines a mitigating clause with examples and counter-examples. The classifier needs a labeled set, coded by two people or two passes, with agreement reported.

**Set C (DV3, pairwise).** The same assessment text is shown with two entity names and the model's preference is read off. Pair each injected entity with a control from the same reference class. Match the two names for length and token count. Present every pair in both orders and average, because models favor a position.

**Set D (DV4, probability).** Pairs of a favorable phrasing and a neutral phrasing about the entity, matched for length and for how common their words are. Score every pair on the zero-dose model as well and subtract, so that a phrase the model simply finds likelier does not read as bias.

## 8. File format and freeze

Keep each set as a CSV in the vault:

```
id,set,register,topic,stem,notes
A01,A,news,safety record,"...{ENTITY}...",
```

- Give every stem a stable identifier and never reuse one.
- When the set is final, record the file's SHA-256 hash in the preregistration and do not edit the file after lock. Any later change is a new version and is reported.
- The prompt files can be public. The entity names cannot, until the fine-tuning data is frozen (readiness note §5).

## 9. Checklist before calling Set A done

- [ ] 50 stems, each with exactly one `{ENTITY}`
- [ ] Every stem passes rules 1 to 8 in §3
- [ ] Register and topic balanced and labeled
- [ ] Generation settings, control definition and classifier written into the preregistration
- [ ] Pre-test run, drops logged, set restored to 50
- [ ] Shared-phrase check against the injection templates is clean
- [ ] File hashed and the hash recorded
