# Poster — 62768 Electrical Energy Systems

`poster.tex` is the project poster, built on DTU's official **`dtuposter`** class
(DTU corporate-identity compliant). A0, 3 columns, Danish.

## ⚠️ Required files (not in this repo)

The `dtuposter` class is a DTU custom class — it is **not** on CTAN/MiKTeX. To compile
you need, from the official DTU poster template package:

- `dtuposter.cls`
- the DTU logo assets it references (`tex_dtu_*` — e.g. `tex_dtu_logo`, and the
  department logo you pick for `toplogo`/`botlogo`)

Put `poster.tex` **in the same folder** as `dtuposter.cls` (or drop `dtuposter.cls`
and the logo files into this `poster/` folder).

> Get the template from DTU (Inside / the course page / your department). The example
> you were given came from that package, so you already have it somewhere.

## Compile

```
pdflatex poster.tex        # run twice for \autoref cross-references
# or
lualatex poster.tex
```

Also needs (all standard, on CTAN/MiKTeX): `cmbright`, `arevmath`, `siunitx`,
`booktabs`, `enumitem`, `tikz`, and `ucs` (for `utf8x`).

## What to fill in

- **Authors:** replace the `+3 medlemmer` and `Gruppe XX` / email in the
  `dtuposterhead`.
- **`toplogo` / `botlogo`:** uncomment in the class options and set to your
  department's logo file (e.g. `tex_dtu_elektro_b_uk`).
- **Resultater:** drop measurement plots into the `Resultater` figure (replace the
  placeholder `fadebox`).
- **Block diagram:** the `Systemoverblik` diagram is native TikZ — edit directly. To
  use the Figma diagram instead, export it as PDF/PNG and `\includegraphics` it inside
  a `fadebox`.

## Switch to English

Add the `english` option to the class and translate the section text. The captions
(Tabel/Figur) follow the class language automatically.
