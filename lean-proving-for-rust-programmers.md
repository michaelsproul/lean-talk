---
title: Lean Proving for Rust Programmers
subtitle: Intro to formal verification
author: Michael Sproul
description: A practical introduction to Lean, dependent types, monads, Aeneas, and LLM-assisted proof workflows for Rust programmers.
---

<!-- class: title -->
<div class="kicker">Formal verification · Lean 4 · Aeneas</div>

# Lean Proving for Rust Programmers

## Intro to formal verification

**Michael Sproul**

<div class="badge-row">
  <span class="badge">tests → theorems</span>
  <span class="badge">const generics → dependent types</span>
  <span class="badge"><code>?</code> → monadic <code>do</code></span>
</div>

???
This is a practical bridge, not a survey of all formal methods. The goal is to make Lean feel like a strange but recognisable programming language, then show how Aeneas turns that into leverage on Rust code.

---

<!-- class: section -->

# Why formal verification?

Formal verification is the use of **mathematical logic** to make precise statements about the behaviour of programs **for all inputs**. More comprehensive than:

- Unit tests
- End-to-end tests
- Property tests
- Fuzzing
- Static analysis
- `.expect("qed")`

---

<div class="kicker">Syntax</div>

# Quick mathematical logic primer

- `P` a variable representing some _proposition_ (either true or false)
- `x` a variable representing an _object_ (a value like a number, or a member of some set)
- `P x`: a proposition P which is true of a variable x
- `¬ P`: **not** P, statement that P is false
- `P ∧ Q`: P **and** Q, both are true
- `P ∨ Q`: P **or** Q, one (or both) are true
- `P → Q`: P **implies** Q. If P is true then Q is true
- `P ↔ Q` or `P ≡ Q`: P **iff** Q. P is true **if and only if** Q is true
- `∀x. P x`: **for all** x, P x is true
- `∃x. P x`: **there exists** an x such that P x is true

<!-- footer: [First-order logic](https://en.wikipedia.org/wiki/First-order_logic) -->

---

<div class="kicker">Examples</div>

# Quick mathematical logic primer

_All men are mortal_:

- `∀x. Human x → Mortal x`
- `Human socrates`
- `Mortal socrates`

Implication elimination:

- `((P → Q) ∧ P) → Q`

Implication chaining:

- `((P → (Q → R)) ∧ P ∧ Q) → R`

Existential introduction:

- `P y → ∃x. P x`

---

<div class="kicker">Useful identities</div>

# Quick mathematical logic primer

- [De Morgan's Laws](https://en.wikipedia.org/wiki/De_Morgan%27s_laws): `¬(P ∧ Q) ↔ (¬P ∨ ¬Q)` and `¬(P ∨ Q) ↔ (¬P ∧ ¬Q)`
- [Material implication](https://en.wikipedia.org/wiki/Material_implication_(rule_of_inference)): `(P → Q) ↔ ¬(P ∧ ¬Q)`
- [Contraposition](https://en.wikipedia.org/wiki/Contraposition): `(P → Q) ↔ (¬Q → ¬P)`
- Iff bi-directionality: `(P ↔ Q) ↔ ((P → Q) ∧ (Q → P))`

---

# Terminology

- **Theorem Prover**: software for processing specifications & proofs written in a logical language, e.g. Lean 4.
- **Proposition**: a specific statement about some of the objects under study, e.g. `2 + 2 = 4` or `2 + 2 = 5`
- **Lemma/Theorem**: a proposition that has been proven true, e.g. `2 + 2 = 4`
- **Proof**: derivation of a new fact (lemma) using legal "moves" applied to existing facts
- **Semantics**: fancy way of saying _meaning_. The mathematical statement corresponding to some object under study, e.g. "Rust semantics in Lean" is the definition of how Rust programs translate into Lean's logic.
- **Specification**: formal description of the correct behaviour of a program, e.g. simplified model of the program written in Lean and a collection of lemmas about it, **not** just a natural language spec.

---

# Curry–Howard: propositions are types

| Logic | Type-theoretic reading | Rust-shaped intuition |
|---|---|---|
| `P → Q` | function from evidence of `P` to evidence of `Q` | `fn(P) -> Q` |
| `P ∧ Q` | pair containing both proofs | `(P, Q)` |
| `P ∨ Q` | tagged choice of one proof | `enum Either<P, Q>` |
| `∃x, P x` | a value plus evidence about it | dependent pair |
| `False` | a type with no constructors | uninhabited type |

```lean
theorem keepLeft {P Q : Prop} : P ∧ Q → P :=
  fun h => h.left
```

The theorem is literally a function: give it evidence of `P ∧ Q`; it returns evidence of `P`.

<!-- footer: [Theorem Proving in Lean: Curry–Howard](https://lean-lang.org/theorem_proving_in_lean4/Propositions-and-Proofs/) -->

# What is a proof?

A formal proof has three parts:

<div class="card-grid">
  <div class="card">
    <h3>1 · Proposition</h3>
    <p>A precise statement, expressed as a Lean type.</p>
  </div>
  <div class="card">
    <h3>2 · Evidence</h3>
    <p>A term inhabiting that type — often constructed by tactics.</p>
  </div>
  <div class="card">
    <h3>3 · Kernel check</h3>
    <p>A small checker verifies the term using Lean’s core rules.</p>
  </div>
</div>

> Think of a proof as a value that successfully type-checks against an extremely precise interface.

**Important:** the kernel checks the proof *of the statement you wrote*. It does not check that the statement matches your intent.

<!-- footer: [Lean: propositions and proofs](https://lean-lang.org/theorem_proving_in_lean4/Propositions-and-Proofs/) -->

---

# A test samples; a proof quantifies

+++

## Test

```rust
#[test]
fn roundtrip_example() {
    let source = b"old";
    let target = b"new";
    let diff = encode(source, target);
    assert_eq!(decode(diff, source), Ok(target));
}
```

Checks **one execution** — or many executions with fuzzing/property testing.

+++

## Theorem

```lean
theorem roundtrip
    (source target : ByteArray)
    (h₁ : source.size < 2^31)
    (h₂ : target.size < 2^31) :
    decode (encode source target) source = .ok target := by
  ...
```

Checks **every** `source` and `target` satisfying the premises — inside the formal model.

<!-- footer: Example adapted from [lean-bdiff](https://github.com/michaelsproul/lean-bdiff) -->

???
Proofs do not make tests obsolete. Tests are excellent for integration, performance, platform behaviour, and checking that the model tracks the implementation. The distinction is coverage: a theorem is universal over its quantified domain.

---

# Proofs and tests answer different questions

| | Tests | Proofs |
|---|---|---|
| Coverage | Chosen or generated executions | All values covered by the theorem |
| Best at | Integration, regressions, performance, real environments | Functional correctness, invariants, impossibility claims |
| Failure mode | Missed input or timing | Wrong statement, wrong model, hidden assumption |
| Cost profile | Cheap to start; coverage is never complete | Expensive to state/model; exhaustive once checked |

> Strong engineering uses both: **tests connect the model to reality; proofs exhaust the model.**

---

# Every theorem is conditional

<div class="pipeline">
  <div class="pipe-node">formal semantics<br>or translation</div>
  <div class="pipe-arrow">∧</div>
  <div class="pipe-node">explicit premises<br>and axioms</div>
  <div class="pipe-arrow">⇒</div>
  <div class="pipe-node accent-node">the stated<br>property</div>
</div>

A green proof means:

- the proposition is derivable in Lean;
- using the definitions, imported lemmas, and axioms in scope;
- under the premises written before the colon.

It does **not** silently prove compiler correctness, hardware correctness, or fidelity of an unverified translation.

---

# What formal verification needs

+++

## A theorem prover with a small TCB

- a precise logic;
- a small proof-checking kernel;
- automation that emits kernel-checkable proof terms;
- an audit path for axioms and incomplete proofs.

+++

## Semantics for the language

- what each Rust construct means;
- how panics, overflow, borrowing, and mutation behave;
- a trustworthy link from the Rust program to the Lean term;
- models for unsupported or external components.

> Without semantics, you may prove a beautiful theorem about the wrong program.

<!-- footer: [Lean language reference](https://lean-lang.org/doc/reference/latest/) · [Aeneas paper](https://arxiv.org/abs/2206.07185) -->

---

<!-- class: dense -->
# The trusted computing base is a stack

<div class="stack-diagram">
  <div class="stack-layer assumption">Executable behaviour: compiler · runtime · platform · hardware</div>
  <div class="stack-layer assumption">Rust semantics and the supported-language boundary</div>
  <div class="stack-layer assumption">Charon/Aeneas translation and external models</div>
  <div class="stack-layer">Your theorem statement and imported library lemmas</div>
  <div class="stack-layer">Elaborator and tactics produce a proof term</div>
  <div class="stack-layer kernel">Lean kernel checks the proof term</div>
</div>

**Minimal TCB** means keeping the part that can *silently certify a false theorem* as small and inspectable as possible.

Lean’s kernel is deliberately small. An end-to-end claim about compiled Rust still depends on the semantic and translation layers above it — unless those layers are themselves verified.

<!-- footer: [Lean reference: kernel and proof checking](https://lean-lang.org/doc/reference/latest/) -->

---

<!-- class: section -->
<div class="kicker">Dependent types</div>

# Types may depend on values

A normal generic type varies over a **type**. A dependent type may vary over an ordinary **term** — including a length, an index, or a proof.

---

# A bounds proof can be an argument

```lean
def safeGet (xs : Array α) (i : Fin xs.size) : α :=
  xs[i]
```

`Fin xs.size` means: a natural number together with evidence that it is smaller than `xs.size`.

The function does not accept an arbitrary index and then *hope* it is valid. The validity requirement is part of the input type.

<div class="badge-row">
  <span class="badge"><code>xs</code> is a value</span>
  <span class="badge"><code>xs.size</code> appears in a type</span>
  <span class="badge"><code>i</code> carries a proof</span>
</div>

<!-- footer: [Functional Programming in Lean: proofs and indexing](https://lean-lang.org/functional_programming_in_lean/Interlude___-Propositions___-Proofs___-and-Indexing/) -->

---

# Rust const generics are a useful foothold

+++

## Rust

```rust
struct Matrix<T, const R: usize, const C: usize> {
    data: [[T; C]; R],
}

fn transpose<T, const R: usize, const C: usize>(
    m: Matrix<T, R, C>,
) -> Matrix<T, C, R> {
    todo!()
}
```

The type records selected compile-time constants.

+++

## Lean

```lean
structure Matrix (α : Type) (rows cols : Nat) where
  at : Fin rows → Fin cols → α

def Matrix.transpose (m : Matrix α r c) : Matrix α c r :=
  ⟨fun i j => m.at j i⟩
```

The same intuition, but the dependency mechanism is general: types may mention values, computations, and propositions.

<!-- footer: [Rust Reference: const generics](https://doc.rust-lang.org/reference/items/generics.html#const-generics) -->

???
Rust const generics are deliberately restricted: only certain primitive const parameter types are permitted, and stable type-level expressions remain limited. Lean’s dependent type theory is not just “more const generics”; it lets specifications and evidence participate directly in types.


---

<!-- class: section -->
<div class="kicker">Lean syntax</div>

# Programs, specifications, and proofs share one language

---

<!-- class: dense -->
# `def`, `axiom`, `theorem`, `lemma`

```lean
-- Computational content: Lean can unfold and evaluate it.
def inc (n : Nat) : Nat := n + 1

-- Opaque constant with no implementation here.
opaque external : Nat → Nat

-- Trusted proposition: assumed, not proved.
axiom external_spec (n : Nat) : external n = n + 1

-- An opaque proof checked by the kernel.
theorem inc_pos (n : Nat) : 0 < inc n := by
  simp [inc]

-- `lemma` is the same kind of declaration; the name signals a helper result.
lemma inc_ne_zero (n : Nat) : inc n ≠ 0 := by
  simp [inc]
```

- **Definitions** choose a value or implementation.
- **Axioms** enlarge the trusted assumptions.
- **Theorems/lemmas** must provide proof evidence.

---

# Lean code is pure functional code

```lean
def firstEven? : List Nat → Option Nat
  | [] => none
  | x :: xs =>
      if x % 2 = 0 then
        some x
      else
        firstEven? xs
```

Familiar ingredients:

- algebraic data types and pattern matching;
- immutable values;
- higher-order functions and type classes;
- recursion, with termination checked by default;
- definitions that can be unfolded during proofs.

Lean is both a theorem prover **and** a functional programming language.

<!-- footer: [Lean language reference](https://lean-lang.org/doc/reference/latest/) -->

---

# Term proofs and tactic scripts

+++

## Direct proof term

```lean
theorem keepLeft₁ {P Q : Prop} : P ∧ Q → P :=
  fun h => h.left
```

You manually write the value inhabiting the proposition.

+++

## Tactic script

```lean
theorem keepLeft₂ {P Q : Prop} : P ∧ Q → P := by
  intro h
  exact h.left
```

Tactics manipulate a goal state and construct the proof term for you.

> Both end the same way: the kernel checks a proof term. A buggy tactic should fail to produce a valid term, not forge a theorem.

<!-- footer: [Lean: tactic proofs](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/) -->

---

# `sorry` is productive debt

```lean
theorem difficult_property (x : Input) : Spec x := by
  -- Establish the architecture now; fill this sub-proof later.
  sorry

#print axioms difficult_property
-- ... depends on: sorryAx
```

`sorry` temporarily inhabits any goal so that the rest of the development can elaborate.

**Useful for:**

- top-down proof design;
- defining helper-lemma interfaces;
- keeping generated and hand-written code compiling during exploration.

**Not a completed proof:** it introduces `sorryAx`, emits a warning, and must be removed or explicitly accepted as an assumption.

<!-- footer: [Lean: validating proofs and printing axioms](https://lean-lang.org/doc/reference/latest/ValidatingProofs/) -->

---

<!-- class: section -->
<div class="kicker">Monads</div>

# A shared abstraction for failure, state, and effects

Rust programmers already use monadic interfaces — even when we rarely call them that.

---

# One sequencing interface, many meanings

```lean
-- Simplified shape of Lean's type class.
class Monad (m : Type → Type) where
  pure : α → m α
  bind : m α → (α → m β) → m β
```

<div class="card-grid">
  <div class="card">
    <h3><code>Option α</code></h3>
    <p>May return a value or stop with <code>none</code>.</p>
  </div>
  <div class="card">
    <h3><code>Except ε α</code></h3>
    <p>May return a value or stop with a typed error.</p>
  </div>
  <div class="card">
    <h3><code>StateM σ α</code></h3>
    <p>Threads state while producing a result.</p>
  </div>
</div>

`bind` says: run this computation; if it produces a value, feed that value into the next computation.

<!-- footer: [Functional Programming in Lean: monads](https://lean-lang.org/functional_programming_in_lean/Monads/The-Monad-Type-Class/) -->

---

# Rust `?` and Lean `do` tell the same story

+++

## Rust

```rust
fn first_plus_last(xs: &[u64]) -> Option<u64> {
    let first = xs.first()?;
    let last = xs.last()?;
    Some(first + last)
}
```

`?` unwraps success and propagates failure.

+++

## Lean

```lean
def firstPlusLast? (xs : List Nat) : Option Nat := do
  let first ← xs.head?
  let last ← xs.reverse.head?
  pure (first + last)
```

`do` notation desugars into `bind` calls and propagates `none`.

The syntax differs; the control-flow shape is nearly identical.

<!-- footer: [Lean: do notation](https://lean-lang.org/functional_programming_in_lean/Monads/) -->

---

# Stateful code can still be represented purely

<div class="big-quote">

> `StateM σ α` is approximately a function `σ → (α × σ)`.

</div>

```lean
def bump : StateM Nat Nat := do
  let before ← get
  set (before + 1)
  pure before

#eval bump.run 41
-- (41, 42)
```

There is no hidden mutable cell in the mathematical meaning. The state is an input and an output; monadic syntax makes the explicit plumbing readable.

This is the key idea behind making imperative-looking programs pleasant to reason about in Lean.

---

<!-- class: section -->
<div class="kicker">Aeneas</div>

# Translate Rust into proof-friendly Lean

Aeneas exploits Rust’s ownership information to remove most memory reasoning from functional-correctness proofs.

---

# The Aeneas pipeline

<div class="pipeline">
  <div class="pipe-node">Rust<br>source</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node">rustc<br>MIR</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node">Charon<br>LLBC</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node accent-node">Aeneas<br>translation</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node">pure-ish<br>Lean</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-node">theorems<br>and proofs</div>
</div>

For the supported subset, the generated representation is **value-based**:

- no addresses or pointer arithmetic;
- no explicit heap model;
- borrowing becomes functional dataflow;
- proofs focus on inputs, outputs, and invariants.

<!-- footer: [Aeneas repository](https://github.com/AeneasVerif/aeneas) · [Aeneas paper](https://arxiv.org/abs/2206.07185) -->

---

# Mutation becomes returned data

+++

## Rust

```rust
fn increment(x: &mut u64) -> u64 {
    let old = *x;
    *x += 1;
    old
}
```

The source talks about a mutable reference.

+++

## Conceptual Lean shape

```lean
-- Schematic, not exact generated syntax.
def increment (x : U64) : Result (U64 × U64) := do
  let old := x
  let updated := x + 1
  pure (old, updated)
```

The translated function returns both the ordinary result and the updated referent. More complex mutable borrows may generate paired forward/backward functions.

> The proof usually reasons about values — not alias sets, heaps, or separation logic.

<!-- footer: [Aeneas: functional translation](https://lean-lang.org/use-cases/aeneas/) -->

---

<!-- class: dense -->
# Unsupported code becomes an explicit boundary

Aeneas’s pure translation does not cover all Rust. Important boundaries include:

<div class="card-grid">
  <div class="card">
    <h3>Not pure-translatable</h3>
    <p><code>unsafe</code>, concurrency, interior mutability, raw memory operations, and many I/O patterns.</p>
  </div>
  <div class="card">
    <h3>External models</h3>
    <p>Smart pointers, locks, hashers, FFI, and library functions can receive hand-written Lean models.</p>
  </div>
  <div class="card">
    <h3>Axioms/specifications</h3>
    <p>Opaque behaviour may be characterised by axioms. The final theorem is conditional on them.</p>
  </div>
</div>

Prefer **executable definitions** where possible; reserve axioms for properties you genuinely choose to trust.

A model such as `RwLock T := T` proves facts about the protected value in a sequential abstraction. It does **not** verify locking or concurrent execution.

<!-- footer: [Aeneas limitations](https://www.sonho.fr/assets/documents/aeneas.html) -->

---

# Milhouse: erase plumbing, keep behaviour

In the Milhouse Aeneas development, external concepts were modelled at a high level:

```lean
-- Conceptual excerpts from the external model.
Arc T          := T
RwLock R T     := T
HashMap K V    := List (K × V)
HasherState    := Unit
```

- pointer-like containers became plain values;
- maps became association lists;
- most external functions received definitional models;
- only genuinely opaque facts such as an `Arc::ptr_eq` characterisation and a `size_of` specification required axioms.

The payoff: early `get_recursive` and update/get lemmas reduced lock/deref plumbing away, so `unfold` plus `simp` could close the goals.

<!-- footer: [Milhouse PR #104](https://github.com/sigp/milhouse/pull/104) -->

---

<!-- class: dense -->
# Milhouse: proofs became design feedback

The proof effort did more than certify existing code:

- the general update/get roundtrip required a **strong induction** matching the real recursive control flow;
- packed leaves exposed a genuine side condition around updates through zero nodes;
- “dense tree” invariants made implicit container assumptions explicit;
- an overly permissive `bulk_update` operation was identified as unsound and removed;
- `intra_rebase` was strengthened so subtree sharing preserves represented length.

> A stubborn premise may be proof friction — or it may be the missing invariant that the implementation was relying on all along.

The workflow is not merely “prove the code”. It is often **specify → discover → repair → prove**.

<!-- footer: [Milhouse PR #104: proof and invariant history](https://github.com/sigp/milhouse/pull/104) -->

---

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
# A practical Aeneas workflow

<div class="timeline">
  <div class="num">1</div><div class="step"><strong>Tweak the Rust until it translates.</strong> Simplify unsupported iterator, trait, closure, or library patterns without changing intended behaviour.</div>
  <div class="num">2</div><div class="step"><strong>Write the desired property in natural language.</strong> State inputs, preconditions, success/failure behaviour, and the observable result.</div>
  <div class="num">3</div><div class="step"><strong>Inspect the generated top-level function.</strong> Understand its monad, arguments, returned state, and external models.</div>
  <div class="num">4</div><div class="step"><strong>State the top-level Lean lemma.</strong> Check that the formal statement says what the prose says before proving anything.</div>
  <div class="num">5</div><div class="step"><strong>Ask an LLM to prove it.</strong> Keep generated code stable; put proofs and helper lemmas in hand-written files.</div>
  <div class="num">6</div><div class="step"><strong>Audit assumptions.</strong> Challenge every new premise, custom axiom, abstraction, and excluded branch.</div>
  <div class="num">7</div><div class="step"><strong>Repeat.</strong> Refactor Rust, models, statements, and proof structure until the result is both true and useful.</div>
</div>

---

# Direct an LLM top-down or bottom-up

+++

## Top-down: discover the proof architecture

1. State the final theorem.
2. Split cases or choose induction.
3. Introduce helper lemmas at the exact gaps.
4. Use `sorry` temporarily at those gaps.
5. Replace each `sorry` with checked evidence.

**Best for:** exposing the dependency graph and preventing aimless lemma generation.

+++

## Bottom-up: stabilise the leaves

1. Prove primitive arithmetic and bit-operation facts.
2. Characterise container and external models.
3. Prove one-step function lemmas.
4. Compose them into recursive invariants.
5. Finish the top-level theorem.

**Best for:** generated code with repetitive low-level obligations.

> A strong workflow is hybrid: sketch top-down, discharge bottom-up.

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

# Five takeaways

1. **A test demonstrates; a theorem quantifies.** Keep both.
2. **Dependent types turn preconditions and invariants into ordinary types.**
3. **Monads let pure Lean express failure, state, and effectful control flow.**
4. **Aeneas converts much safe Rust into value-level functions, avoiding routine memory proofs.**
5. **LLMs can build proofs; only the statement, assumptions, models, and kernel check determine what was actually established.**

> Start with one crisp property: a roundtrip, preservation theorem, bounds guarantee, or update/read law.

---

<!-- class: dense -->
# References and examples

- [Lean Language Reference](https://lean-lang.org/doc/reference/latest/)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Rust Reference: const generics](https://doc.rust-lang.org/reference/items/generics.html#const-generics)
- [Aeneas repository](https://github.com/AeneasVerif/aeneas)
- [Aeneas: Rust Verification by Functional Translation](https://arxiv.org/abs/2206.07185)
- [Aeneas Lean use case](https://lean-lang.org/use-cases/aeneas/)
- [lean-bdiff](https://github.com/michaelsproul/lean-bdiff)
- [Milhouse PR #104 — Aeneas formal verification](https://github.com/sigp/milhouse/pull/104)

<div class="badge-row">
  <span class="badge"><kbd>→</kbd> next</span>
  <span class="badge"><kbd>F</kbd> fullscreen</span>
  <span class="badge"><kbd>N</kbd> notes</span>
  <span class="badge"><kbd>?</kbd> help</span>
</div>
