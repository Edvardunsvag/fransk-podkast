# Fransk på løpetur

Ukentlige franskleksjoner som podkast. Brukeren hører episoden på to rolige løpeturer (ca. 25 min) og øver i helgen med Codex sin talemodell. Mål: småprat med franske turister i Norge, deretter som turist i Frankrike. Nivå: litt skolefransk.

Spec: `design/specs/2026-10-04-fransk-podkast-design.md`

## Når brukeren ber om neste episode

1. Finn neste uke N (høyeste `episoder/uke-NN.yaml` + 1).
2. Les `pensum.md` for temaet til uke N og de to siste manusene for nivå og tone.
3. Kjør `uv run fransk repetisjon N` og bruk glosene i repetisjonsdelen.
4. Skriv `episoder/uke-NN.yaml` etter reglene under.
5. Kjør `uv run fransk sjekk N`, så `uv run fransk lag N`. Varigheten skal være 20–25 min. Er den under 18 eller over 27, juster manuset og lag på nytt.
6. Vis brukeren gloser, fraser og varighet. Publiser med `uv run fransk publiser N` først når brukeren sier ja.
7. Marker uka som ferdig i `pensum.md` og commit.

## Episodeformat

| Del | Varighet | Innhold |
|---|---|---|
| 1. Intro | 0,5 min | Uke, tema og hva lytteren skal klare etter episoden |
| 2. Repetisjon | 3 min | Glosene fra `fransk repetisjon N`. Norsk ord, `pause: 3`, fransk ord. Uke 1 hopper over denne delen. |
| 3. Ukas 10 gloser | 7 min | Fransk to ganger sakte, betydning, kort uttaletips, eksempelsetning |
| 4. Ukas fraser | 6 min | 6–8 fraser som bruker glosene. Lange fraser bygges bakfra. |
| 5. Dialog | 4 min | To franske stemmer (`stemme: a` og `b`). Først sakte med norske forklaringer innimellom, så i `fart: normal` uten avbrudd. |
| 6. Avslutning | 2 min | Alle 10 gloser: norsk, `pause: 3`, fransk. Så helgeoppdraget. |

## Skriveregler

- Norsk stemme forklarer, fransk stemme sier alt på fransk. Bland aldri språk i ett segment, for talemotoren uttaler da feil.
- Etter hver fransk frase som lytteren kan mumle med: `pause: 2` eller `pause: 3`.
- Uttaletips skrives på norsk med norske lydbilder: «r-en sitter bak i halsen», «s-en på slutten er stum», «on uttales gjennom nesen».
- Bakfra-bygging: `lentement` → `plus lentement` → `parler plus lentement` → `Vous pouvez parler plus lentement ?`
- Gloser og fraser i en uke skal kunne brukes i en ekte samtale med en turist. Unngå bokord.
- Bruk «vous» mot turister. Introduser «tu» først når pensum sier det.
- Fransk tegnsetting: mellomrom før `?`, `!` og `:`.
- `fart: sakte` til og med uke 8. Fra uke 9 kan forklarende fransk være `normal`, og dialogens andre runde er alltid `normal`.
- Fra uke 6 kan faste vendinger sies på fransk: «Le mot suivant», «Encore une fois», «Écoutez».

## Codex-instruks

Fyll inn malen og legg den i `codex_instruks`:

```
Du er <rolle>, en fransk turist <situasjon>. Jeg er nordmann og lærer fransk. Jeg har litt skolefransk og er på uke <N>.
Snakk bare fransk, sakte og med korte, enkle setninger. Hold deg så langt det går til disse ordene og frasene: <ukas gloser og fraser, og et utvalg fra tidligere uker>.
Etter hvert svar fra meg: hvis jeg sa noe feil, gi en kort rettelse på norsk i én setning, og fortsett så samtalen på fransk.
Du starter samtalen. Etter rundt 10 minutter avslutter du og sier på norsk hvilke tre ting jeg bør øve mer på.
```
