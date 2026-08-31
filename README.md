# Lean Proving for Rust Programmers

A 34-slide presentation for Rust programmers introducing formal verification, dependent types, Lean 4, monads, Aeneas, and a practical LLM-assisted proof workflow.

## Open the presentation

Open `lean-proving-for-rust-programmers.html` in any modern browser. The HTML is self-contained and does not load fonts, scripts, or stylesheets from the network.

Controls:

- Right arrow, Page Down, Space, Enter, or click the right side: next slide
- Left arrow, Page Up, Backspace, or click the left side: previous slide
- Home / End: first / last slide
- `F`: fullscreen
- `N`: speaker notes
- `?` or `H`: shortcut help
- Browser print: printable slide layout / PDF export

## Edit and rebuild

The editable source is `lean-proving-for-rust-programmers.md`. Slides are separated by `---`; two-column slides use `+++`; speaker notes follow `???`.

Install the small build-time dependencies and rebuild:

```sh
python3 -m pip install mistune PyYAML Pygments
python3 build_slides.py \
  lean-proving-for-rust-programmers.md \
  lean-proving-for-rust-programmers.html
```

The compiler is deliberately included so the deck does not depend on a particular JavaScript slide framework or a network connection.

## Examples and scope

The deck uses:

- the binary-diff roundtrip theorem from `michaelsproul/lean-bdiff`;
- the Aeneas translation and proof work in `sigp/milhouse` pull request 104;
- official Lean, Rust, and Aeneas documentation for the language and translation details.
