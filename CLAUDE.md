# Fransk på løpetur

Ukentlige franskleksjoner som podkast. Brukeren hører episoden på to rolige løpeturer (ca. 25 min) og øver i helgen med Codex sin talemodell. Mål: småprat med franske turister i Norge, deretter som turist i Frankrike. Nivå: litt skolefransk.

Spec: `design/specs/2026-10-04-fransk-podkast-design.md`

## Når brukeren ber om neste episode

1. Finn neste uke N (høyeste `episoder/uke-NN.yaml` + 1).
2. Les `pensum.md` for temaet til uke N og de to siste manusene for nivå og tone.
3. Kjør `uv run fransk repetisjon N` og bruk glosene i repetisjonsdelen. Kjør `uv run fransk kjente N` for å se alle ord brukeren allerede har lært.
4. Skriv `episoder/uke-NN.yaml` etter reglene under.
5. Kjør `uv run fransk sjekk N`, så `uv run fransk lag N`. Varigheten skal være 20–25 min. Er den under 18 eller over 27, juster manuset og lag på nytt.
6. Vis brukeren gloser, fraser og varighet. Publiser med `uv run fransk publiser N` først når brukeren sier ja.
7. Marker uka som ferdig i `pensum.md` og commit.

## Episodeformat

| Del | Varighet | Innhold |
|---|---|---|
| 1. Intro | 0,5 min | Uke, tema og hva lytteren skal klare etter episoden |
| 2. Repetisjon | 3 min | Glosene fra `fransk repetisjon N`. Norsk ord, `pause: 3`, fransk ord. Uke 1 hopper over denne delen. |
| 3. Ukas 10 gloser | 7 min | Fransk to ganger sakte, betydning, eksempelsetning med ord-for-ord-analyse |
| 4. Ukas fraser | 7 min | 6–8 fraser som bruker glosene, hver med ord-for-ord-analyse. Lange fraser bygges bakfra. |
| 5. Dialog | 4 min | To franske stemmer (`stemme: a` og `b`). Først sakte med norske forklaringer innimellom, så i `fart: normal` uten avbrudd. |
| 6. Avslutning | 2 min | Alle 10 gloser: norsk, `pause: 3`, fransk. Så helgeoppdraget. |

## Skriveregler

- Norsk stemme forklarer, fransk stemme sier alt på fransk. Bland aldri språk i ett segment, for talemotoren uttaler da feil.
- Etter hver fransk frase som lytteren kan mumle med: `pause: 2` eller `pause: 3`.
- Brukeren har god uttale. Nevn uttale bare når den er overraskende, for eksempel en stum bokstav som gjør ordet vanskelig å kjenne igjen. Ellers ingen uttaletips.
- Bakfra-bygging: `lentement` → `plus lentement` → `parler plus lentement` → `Vous pouvez parler plus lentement ?`
- Gloser og fraser i en uke skal kunne brukes i en ekte samtale med en turist. Unngå bokord.
- Bruk «vous» mot turister. Introduser «tu» først når pensum sier det.
- Fransk tegnsetting: mellomrom før `?`, `!` og `:`.
- `fart: sakte` til og med uke 8. Fra uke 9 kan forklarende fransk være `normal`, og dialogens andre runde er alltid `normal`.
- Fra uke 6 kan faste vendinger sies på fransk: «Le mot suivant», «Encore une fois», «Écoutez».

## Ord-for-ord-analyse

Etter hver ny fransk setning (eksempelsetninger, fraser og første gang en dialogreplikk brukes) kommer et kort norsk segment som går gjennom setningen:

- Verb: bøyd form, grunnform og betydning, og hvilken person. «Venez kommer av venir, å komme, her i vous-form.»
- Ord som ikke står i `uv run fransk kjente N` og ikke er blant ukas gloser: kort betydning.
- Kjente ord: hopp over, eller nevn kort at det er kjent («d'où har du lært»).
- Små ting som er nyttige å forstå, som at «de» blir «d'» foran vokal, eller at «ne … pas» er nektelse. Én setning, ikke en grammatikktime.
- Hold det kort: 1–3 setninger per analyse.
- Franske ord i analysen sies av den franske stemmen i egne segmenter (uten pause), og den norske stemmen forklarer. Den norske stemmen uttaler franske ord feil. Eksempel:

  ```yaml
  - fr: "venez"
  - no: "kommer av"
  - fr: "venir"
  - no: "som betyr å komme. Her står det i vous-form."
  ```

Alle ord og verb som forklares i analysene, men som ikke er blant ukas 10 gloser, legges i `andre_ord` i manuset (verb i grunnform, for eksempel `{ fr: "venir", no: "å komme" }`). Da vet neste episode at de er kjente.

## Codex-instruks

Fyll inn malen og legg den i `codex_instruks`:

```
Du er <rolle>, en fransk turist <situasjon>. Jeg er nordmann og lærer fransk. Jeg har litt skolefransk og er på uke <N>.
Snakk bare fransk, sakte og med korte, enkle setninger. Hold deg så langt det går til disse ordene og frasene: <ukas gloser og fraser, og et utvalg fra tidligere uker>.
Etter hvert svar fra meg: hvis jeg sa noe feil, gi en kort rettelse på norsk i én setning, og fortsett så samtalen på fransk.
Du starter samtalen. Etter rundt 10 minutter avslutter du og sier på norsk hvilke tre ting jeg bør øve mer på.
```
