# Fræsning på Roland SRM-20 — alternativ til fiberlaseren

Samme produktionsfiler, anden maskine. Fordelen ved fræseren: **baner, huller og
udskæring i ÉN opspænding** (ingen håndboring bagefter), og isolationsfræsning
fjerner kun kanalerne — typisk hurtigere end laserens raster-gravering.

**Designreglerne passer allerede.** 1.0 mm bane / 0.8 mm clearance betyder at
alle isolationskanaler er ≥ 0.8 mm brede — en standard 1/64" (0.40 mm) fræser
rydder dem i 2 offset-passes. Ingen skrøbelige V-bits, ingen ændringer i KiCad.

## Værktøjskæden

```
gerbers/ (findes allerede)  →  PNG (1000 dpi)  →  mods CE  →  .rml  →  VPanel  →  SRM-20
```

- **mods CE** (modsproject.org, kører i browseren — Fab Academy-standarden):
  `programs → open program → machines → Roland → SRM-20 mill → mill 2D PCB`.
  Læser PNG, genererer toolpath, eksporterer `.rml` til Downloads.
- **VPanel for SRM-20** (på maskinens PC): sæt XY/Z-origin, `Cut → Add → Output`.

> **Nyere alternativ — `gerber2rml`** (`tools/srm-cam`): genererer `.rml` ELLER
> `.nc` (G-kode) **direkte** fra gerberne, så PNG- og mods-trinnet springes helt
> over. Vælg maskinen **"Roland SRM-20 (G-code)"** i GUI'en (eller `--gcode` på
> CLI'en). VPanel kører `.nc` via `Cut → Add → Output` når maskinen står i
> **NC-kode-mode**; koordinater bruger **G54** = bruger-origin. Validering
> 22-06-2026: ren isolering ved **0.15 mm** med en SKARP, kort fræser — en sløv/lang
> fræser "brænder" kobberet og skærer for lavt. Bemærk: en 0.8 mm fræser kan IKKE
> isolere 0.8 mm clearance — brug 1/64" (0.4 mm) til baner på de rigtige boards.

## Filer pr. board — tre jobs

| Job | Kilde | Spejlvendt? | Bit | mods-indstillinger |
|---|---|---|---|---|
| 1. Baner (B.Cu) | SVG-eksport, se nedenfor | **JA** | 1/64" (0.4 mm) | mill traces: depth 0.10–0.15 mm, offsets **2** (kanalerne er kun 0.8 mm — flere er spildtid; `-1` = ryd alt = laser-ækvivalent, langsomt), 4 mm/s |
| 2. Huller | drill marks i Edge.Cuts-eksporten (eller `gerbers/<b>.drl` renderet til PNG) | **JA** | 1/32" (0.8 mm) | mill outline: depth 0.6 mm/pass, total 1.8 mm (gennem 1.6 mm plade) |
| 3. Udskæring | Edge.Cuts | **JA** | 1/32" (0.8 mm) | som huller |

PNG-regler i mods: **hvid = kobber der bliver, sort = fjernes** (samme som
laseren) — invertér hvis eksporten er sort-på-hvid. Opløsning ≥ **1000 dpi**.

SVG-eksport (spejlingen sker HER, ikke i mods):

```powershell
& "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" pcb export svg `
  -o boards\<b>\<b>_mill_bcu.svg -l "B.Cu" --mirror --black-and-white `
  --page-size-mode 2 --exclude-drawing-sheet boards\<b>\<b>.kicad_pcb
```

Rasterisér til PNG i GIMP/ImageMagick (1000 dpi, invertér). Hul- og kant-PNG'er:
render `<b>-Edge_Cuts.gm1` + `<b>.drl` i en gerber-viewer og spejlvend i GIMP —
ELLER bor i hånden som ved laser-flowet og kør kun job 1+3.

## På maskinen

1. **Materiale: FR-1 (fenol) hvis muligt.** FR-4 kan fræses, men glasfiberstøvet
   sliber 1/64"-bits ned på 1–2 boards og er sundhedsskadeligt — støvsuger på,
   maske, og regn med bitslid. Spørg efter FR-1 i shoppen/fablab'en.
2. Pladen behøver IKKE være 109×109 mm (ingen jig — origin sættes i VPanel).
   Alt over ~110×110 mm med plads til tape virker; arbejdsområdet er 203×152 mm.
3. Montér på offerplade (MDF) med dobbeltklæbende tape over HELE bagsiden —
   en bule på 0.1 mm ses i fræsedybden. Tryk pladen helt plan.
4. VPanel: kør spindlen til pladens nederste venstre hjørne → `Set Origin X/Y`.
   Z: sænk bitten til lige over kobberet, løsn sætskruen så bitten falder ned og
   hviler PÅ kobberet, spænd igen → `Set Origin Z`. (Klassisk SRM-20-trick —
   giver Z-nul præcis på kobberoverfladen.)
5. Kør job 1 (baner, 1/64"), skift bit + NYT Z-nul (XY-origin beholdes!),
   kør job 2+3 (huller + udskæring, 1/32").
6. Multimeter-test af naborbaner bagefter, som ved laseren.

## Stadig enkeltsidet (Mulighed A)

Toplags-nettene bygges som trådbroer præcis som i laser-flowet —
`<board>_top_cu.dxf` er stadig tegningen. Dobbeltsidet fræsning kræver
flip-registrering (styrepinde i offerpladen) — samme "på eget ansvar" som
laserens Mulighed B.

## Gotchas

- **Brug IKKE 1/32" til banerne.** Kanalen er 0.8 mm, bitten 0.79 mm — efter
  raster-afrunding ved 1000 dpi dropper mods kanaler der ikke kan rumme bitten,
  og du får usynlige kortslutninger. 1/64" med 2 offsets dækker 0.8 mm præcist.
- Spejlvendingen: ALLE tre jobs er set fra undersiden (kobber opad i maskinen).
  Glemt spejling opdages først når hullerne ikke passer med komponenterne.
- SRM-20'erens spindel topper ved 7000 rpm — lad feeds blive på mods-defaults
  (4 mm/s); højere feed knækker 1/64"-bitten.
- Jog/travel-højde i mods: ≥ 2 mm, men sæt den ikke til 12+ mm (langsomt).
- Refdes-kobberteksten ligger på F.Cu og er irrelevant for bundfræsningen —
  gravér evt. `_silk_top.dxf` på laseren bagefter, eller spring den over.
