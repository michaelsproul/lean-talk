# Binary diffs: a compact end-to-end contract

```lean
theorem full_encode_decode_roundtrip_final
    (source target : ByteArray)
    (h_source_bound : source.size < 2 ^ 31)
    (h_target_bound : target.size < 2 ^ 31) :
    Decoder.decode (Encoder.encode source target) source = .ok target
```

Natural-language reading:

> For every bounded source and target byte string, encoding the target relative to the source and then decoding with that source succeeds and returns exactly the target.

This is a strong shape for a first verification target:

- universal inputs;
- visible preconditions;
- an explicit success result;
- an equality that captures the user-facing contract.

<!-- footer: [lean-bdiff](https://github.com/michaelsproul/lean-bdiff) -->

---

# The theorem statement is the real deliverable

Before celebrating a proof, review the proposition like an API contract:

1. **Quantifiers:** does it cover every intended input?
2. **Premises:** are the bounds and invariants real, necessary, and satisfiable?
3. **Result shape:** does it prove success, or only a property *if* success occurs?
4. **Model boundary:** which external definitions and axioms are in play?
5. **Observables:** does equality capture the behaviour users care about?

For the diff theorem, the `< 2^31` bounds and `.ok target` conclusion are not incidental details. They define exactly what was proved.

> It is possible to have a flawless proof of a weak, vacuous, or mis-specified theorem.

---

<!-- class: dense -->
# Give the LLM guardrails the kernel can enforce

+++

## A useful proof request

```text
Prove theorem `X` in this file.

Constraints:
- Do not change the theorem statement.
- Do not add premises, axioms, or `sorry`.
- Prefer existing definitions and lemmas.
- Keep generated Aeneas files unchanged.
- Run `lake build` after each patch.
- Explain any premise that appears necessary.
```

+++

## Audit the result

```lean
#print axioms X
```

Also check:

- clean `lake build`;
- no remaining `sorry` / `admit`;
- no surprise `sorryAx` or custom axioms;
- no theorem weakened by an “obvious” edit;
- tests still exercise the actual Rust implementation.

<!-- footer: [Lean: validating proofs](https://lean-lang.org/doc/reference/latest/ValidatingProofs/) -->

---

<!-- class: dense -->
# A practical Aeneas workflow

<div class="timeline">
  <div class="num">1</div><div class="step"><strong>Tweak the Rust until it translates.</strong> Simplify unsupported iterator, trait, closure, or library patterns without changing intended behaviour.</div>
  <div class="num">2</div><div class="step"><strong>Write the desired property in natural language.</strong> State inputs, preconditions, success/failure behaviour, and the observable result.</div>
  <div class="num">3</div><div class="step"><strong>Inspect the generated top-level function.</strong> Understand its monad, arguments, returned state, and external models.</div>
  <div class="num">4</div><div class="step"><strong>State the top-level Lean lemma.</strong> Check that the formal statement says what the prose says before proving anything.</div>
  <div class="num">5</div><div class="step"><strong>Ask an LLM to prove it.</strong> Keep generated code stable; put proofs and helper lemmas in hand-written files.</div>
  <div class="num">6</div><div class="step"><strong>Audit assumptions.</strong> Challenge every new premise, custom axiom and abstraction.</div>
  <div class="num">7</div><div class="step"><strong>Repeat.</strong> Refactor Rust, models, statements, and proof structure until the result is both true and useful.</div>
</div>

---
