# BOM — 62768 energy system

> Genereret fra [`footprint_map.csv`](footprint_map.csv) med `tools/bom_to_md.py` — **redigér CSV'en, ikke denne fil.** Alle substitutioner er flagget i note-kolonnen.

## Samlet indkøbsliste

| Antal | Del | Pakke | Kilde |
|---|---|---|---|
| 10 | 2 pol skrueterminal | `TerminalBlock_bornier-2_P5.08mm` | shop |
| 8 | 1N4006 | `D_DO-41_SOD81_P10.16mm_Horizontal` | shop |
| 7 | 1k00 | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 6 | 4700uF 50V | `CP_Radial_D18.0mm_P7.50mm` | shop |
| 6 | Header Male | `PinHeader_1x02_P2.54mm_Vertical` | shop |
| 5 | 100n keramisk | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | shop |
| 5 | 1R00 | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 4 | 10k0 | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 4 | 9k09 | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 3 | 1N5817 | `D_DO-41_SOD81_P10.16mm_Horizontal` | shop |
| 3 | 47uF 50V | `CP_Radial_D8.0mm_P3.50mm` | shop |
| 3 | LM358 | `DIP-8_W7.62mm_LongPads` | shop |
| 2 | 200R | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 2 | 3 pol skrueterminal | `TerminalBlock_bornier-3_P5.08mm` | shop |
| 2 | 332R (E96) | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 2 | 33k2 (E96) | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 2 | 4N25 | `DIP-6_W7.62mm_LongPads` | shop |
| 2 | Header Male | `PinHeader_1x03_P2.54mm_Vertical` | shop |
| 2 | IRF530 | `TO-220-3_Vertical_LaserPads` | shop |
| 2 | MCP601 | `DIP-8_W7.62mm_LongPads` | kit |
| 2 | toroid (egen-vikling) | `L_Toroid_Vertical_L34.5mm_W15.0mm_P28.20mm_LaserPads` | egen-vikling |
| 1 | 100k | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 1 | 10R0 | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 1 | 22k6 | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 1 | 22uF 50V | `CP_Radial_D8.0mm_P3.50mm` | shop |
| 1 | 2k00 | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 1 | 4k75 | `R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shop |
| 1 | BZX55C5V1 | `D_DO-35_SOD27_P7.62mm_Horizontal` | shop |
| 1 | Header Male | `PinHeader_1x05_P2.54mm_Vertical` | shop |
| 1 | IL300 | `DIP-8_W7.62mm_LongPads` | kit |
| 1 | ILD74 | `DIP-8_W7.62mm_LongPads` | kit |
| 1 | IR2110 | `DIP-14_W7.62mm_LongPads` | kit |
| 1 | IRF540 | `TO-220-3_Vertical_LaserPads` | shop |
| 1 | Motraxx SR555 | `TerminalBlock_bornier-2_P5.08mm` | kit |
| 1 | TIP41A | `TO-220-3_Vertical_LaserPads` | shop |

## Buck-converter (`buck`)

| Ref | Værdi | Del (indkøb) | Kilde | Footprint | Noter |
|---|---|---|---|---|---|
| D1 | 1N5819 | 1N5817 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` | SUBSTITUTION: 1N5819 ikke i shoppen. 1N5817 (Schottky 1A/20V) OK ved 15V bus med marginal - tjek spidsspaending |
| M1 | IRF530N | IRF530 | shop | `energy_system:TO-220-3_Vertical_LaserPads` | shoppen har IRF530 (uden N) - samme pinout G-D-S og TO-220 |
| R1 | 330 | 332R (E96) | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | E96: 330 -> 332R (0.6% afvigelse) eller 2x packs - uproblematisk for LED-formodstand |
| R2 | 10k | 10k0 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| C1 | 47u | 47uF 50V | shop | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` |  |
| U1 | 4N25 | 4N25 | shop | `Package_DIP:DIP-6_W7.62mm_LongPads` | monter i DIP6-sokkel (shop) |
| L1 | 470u | toroid (egen-vikling) | egen-vikling | `energy_system:L_Toroid_Vertical_L34.5mm_W15.0mm_P28.20mm_LaserPads` | Maalt med skydelaere paa den fysiske toroid: OD 34.5mm staaende paa kant; ben-pitch 28.2mm c-c (26.6mm indvendigt + 1.6mm ben); drill 2.0mm. Genberegn ripple med viklet L (Lec 2: dI=Vs*k(1-k)/(2fL)) |
| J1 | V1 ind (15V) | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |
| J2 | 5V ud | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |
| J3 | PWM (isoleret) | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | PWM + GND_MCU (isoleret jord - maa IKKE forbindes til effekt-GND) |
| J4 | gate-forsyning | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | OBS: +12V_SW refereret til SW-knuden (flydende hjaelpeforsyning) - high-side switch. Se PCB_RESULTS.md |

## Boost-converter (`boost`)

| Ref | Værdi | Del (indkøb) | Kilde | Footprint | Noter |
|---|---|---|---|---|---|
| D1 | 1N5819 | 1N5817 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` | SUBSTITUTION: som buck. Boost-udgang ~10V - 20V-rating OK |
| M1 | IRF530 | IRF530 | shop | `energy_system:TO-220-3_Vertical_LaserPads` |  |
| R1 | 330 | 332R (E96) | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R2 | 10k | 10k0 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| C1 | 47u | 47uF 50V | shop | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` |  |
| U1 | 4N25 | 4N25 | shop | `Package_DIP:DIP-6_W7.62mm_LongPads` | DIP6-sokkel |
| L1 | 470u | toroid (egen-vikling) | egen-vikling | `energy_system:L_Toroid_Vertical_L34.5mm_W15.0mm_P28.20mm_LaserPads` | som buck L1: maalt toroid OD 34.5mm / pitch 28.2mm / drill 2.0mm |
| J1 | lager ind (5V) | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |
| J2 | V2 ud (10V) | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |
| J3 | PWM (isoleret) | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |  |
| J4 | gate-forsyning | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | +12V/GND (low-side switch - jordrefereret OK) |

## Motor-drive (`drive`)

| Ref | Værdi | Del (indkøb) | Kilde | Footprint | Noter |
|---|---|---|---|---|---|
| R1 | 200 | 200R | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R2 | 10 | 10R0 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | gate-seriemodstand |
| R3 | 1k | 1k00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R4 | 1k | 1k00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| C1 | 22u | 22uF 50V | shop | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` |  |
| C2 | 100n | 100n keramisk | shop | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |  |
| D1 | 1N4007 | 1N4006 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` | SUBSTITUTION: 1N4007 (1000V) ikke i shoppen; 1N4006 (800V) rigelig ved 20V. Friloeb over motor |
| D2 | 1N4007 | 1N4006 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` | SUBSTITUTION: som D1. Gate-vejs-diode |
| Q1 | IRF540N | IRF540 | shop | `energy_system:TO-220-3_Vertical_LaserPads` | kittet har ogsaa IRF540N (datasheet i docs/datasheets) - TO-220AB bekraeftet |
| U1 | ILD74 | ILD74 | kit | `Package_DIP:DIP-8_W7.62mm_LongPads` | KIT-DEL - IKKE i shoppen. Dual-kanal opto DIP-8 (datasheet bekraeftet). 4N25 er IKKE drop-in (single + anden pinout). DIP8-sokkel |
| U2 | IR2110 | IR2110 | kit | `Package_DIP:DIP-14_W7.62mm_LongPads` | KIT-DEL - IKKE i shoppen. 14-Lead PDIP bekraeftet i datasheet. DIP14-sokkel |
| M1 | Motor_DC | Motraxx SR555 | kit | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` | motor tilsluttes via skrueterminal (ledninger) |
| J1 | PWM ind | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |  |
| J2 | forsyning | 3 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-3_P5.08mm` | +20V / +15V / GND |

## Feedback (isoleret) (`feedback`)

| Ref | Værdi | Del (indkøb) | Kilde | Footprint | Noter |
|---|---|---|---|---|---|
| R1 | 10k | 10k0 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R2 | 2k | 2k00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R3 | 33k | 33k2 (E96) | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | E96: 33k -> 33k2 (0.6%) |
| R4 | 200 | 200R | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R5 | 33k | 33k2 (E96) | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| U1 | IL300 | IL300 | kit | `Package_DIP:DIP-8_W7.62mm_LongPads` | KIT-DEL - IKKE i shoppen og INGEN aekvivalent. Servo-loopet kraever netop IL300. DIP-8 bekraeftet i datasheet. DIP8-sokkel |
| U3 | MCP601 | MCP601 | kit | `Package_DIP:DIP-8_W7.62mm_LongPads` | KIT-DEL. PDIP-8 bekraeftet (DS21314G). Shop-alternativ: MCP6002 (dual - kraever omtegning) eller LM358. DIP8-sokkel |
| U4 | MCP601 | MCP601 | kit | `Package_DIP:DIP-8_W7.62mm_LongPads` | som U3 |
| J1 | ind + forsyning | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` | INPUT / +5V / GND |
| J2 | FB ud | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |  |

## Rectifier (3-faset bro) (`rectifier`)

| Ref | Værdi | Del (indkøb) | Kilde | Footprint | Noter |
|---|---|---|---|---|---|
| D1 | 1N4006 | 1N4006 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` | 6-diode 3-faset bro; 1A/800V rigeligt til 300mA / 8x trafo-spaending |
| D2 | 1N4006 | 1N4006 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` |  |
| D3 | 1N4006 | 1N4006 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` |  |
| D4 | 1N4006 | 1N4006 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` |  |
| D5 | 1N4006 | 1N4006 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` |  |
| D6 | 1N4006 | 1N4006 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` |  |
| C1 | 4700u/50V | 4700uF 50V | shop | `Capacitor_THT:CP_Radial_D18.0mm_P7.50mm` | 3x parallel = 14.1mF (~spec'ens 15mF). VERIFICER fysisk diameter/pitch foer bestilling - shoppen angiver ikke dimensioner |
| C2 | 4700u/50V | 4700uF 50V | shop | `Capacitor_THT:CP_Radial_D18.0mm_P7.50mm` |  |
| C3 | 4700u/50V | 4700uF 50V | shop | `Capacitor_THT:CP_Radial_D18.0mm_P7.50mm` |  |
| R1 | 10k | 10k0 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | bleeder |
| J1 | 3-fase ind | 3 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-3_P5.08mm` | fra trafo-sekundaerer |
| J2 | V1 ud | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |

## MPPT / PV (`mppt`)

| Ref | Værdi | Del (indkøb) | Kilde | Footprint | Noter |
|---|---|---|---|---|---|
| D1 | 1N5817 | 1N5817 | shop | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` | seriediode mod tilbage-stroem i panelet |
| DZ1 | BZX55C5V1 | BZX55C5V1 | shop | `Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal` | 5.1V reference |
| Q1 | TIP41A | TIP41A | shop | `energy_system:TO-220-3_Vertical_LaserPads` | pass-transistor TO-220 (BD139/TO-126 droppet: 2.28mm pitch kan ikke overholde laserens 0.8mm clearance). SKAL have koeleplade (op til ~7W ved fuld PV-stroem) |
| U1 | LM358 | LM358 | shop | `Package_DIP:DIP-8_W7.62mm_LongPads` | forsynes fra PV-bus (<32V OK). DIP8-sokkel |
| C1 | 4700u/50V | 4700uF 50V | shop | `Capacitor_THT:CP_Radial_D18.0mm_P7.50mm` | MPPT-kondensator 3x parallel = 14.1mF |
| C2 | 4700u/50V | 4700uF 50V | shop | `Capacitor_THT:CP_Radial_D18.0mm_P7.50mm` |  |
| C3 | 4700u/50V | 4700uF 50V | shop | `Capacitor_THT:CP_Radial_D18.0mm_P7.50mm` |  |
| C4 | 100n | 100n keramisk | shop | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | LM358 afkobling |
| C5 | 47u | 47uF 50V | shop | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` | udgangskondensator V3 |
| C6 | 100n | 100n keramisk | shop | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | zener-stoejfilter |
| R1 | 100k | 100k | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | PV-spaendingsdeler top |
| R2 | 22k6 | 22k6 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | deler bund: 21V -> 3.9V til ADC |
| R3 | 4k75 | 4k75 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | zener-bias ~2.7mA |
| R4 | 1k00 | 1k00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | basemodstand |
| R5 | 1R00 | 1R00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | shunt 2x1R parallel = 0R5 (effekt: 0.6A -> 2x 0.18W i 1/4W-modstande) |
| R6 | 1R00 | 1R00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R7 | 1k00 | 1k00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | inverterende indgang |
| R8 | 9k09 | 9k09 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | gain -9.09: 0.6A -> +2.7V |
| J1 | PV ind | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |
| J2 | til lager (V3) | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |
| J3 | sense -> Arduino | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` | PV_V / PV_I / GND |

## Current sense (3 kanaler) (`current_sense`)

| Ref | Værdi | Del (indkøb) | Kilde | Footprint | Noter |
|---|---|---|---|---|---|
| R11 | 1R00 | 1R00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | lavside-shunt kanal 1 (V1->buck; 300mA -> 90mW OK i 1/4W) |
| R12 | 1k00 | 1k00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | gain-ben |
| R13 | 9k09 | 9k09 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | gain 10.09: 300mA -> 3.03V |
| R21 | 1R00 | 1R00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | kanal 2 (boost->last) |
| R22 | 1k00 | 1k00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R23 | 9k09 | 9k09 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R31 | 1R00 | 1R00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | kanal 3 (lager V3) |
| R32 | 1k00 | 1k00 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| R33 | 9k09 | 9k09 | shop | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |  |
| U1 | LM358 | LM358 | shop | `Package_DIP:DIP-8_W7.62mm_LongPads` | indgange gaar til GND (derfor ikke TL072). +5V forsyning -> ADC-sikker. DIP8-sokkel |
| U2 | LM358 | LM358 | shop | `Package_DIP:DIP-8_W7.62mm_LongPads` | B-halvdel = unity-buffer (ubrugt) |
| C1 | 100n | 100n keramisk | shop | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |  |
| C2 | 100n | 100n keramisk | shop | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |  |
| J1 | kanal 1 retur | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` | grenens returledning ind paa pin 1 - system-GND videre fra pin 2 |
| J2 | kanal 2 retur | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |
| J3 | kanal 3 retur | 2 pol skrueterminal | shop | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |  |
| J4 | Arduino | Header Male | shop | `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical` | +5V / I1 / I2 / I3 / GND |

