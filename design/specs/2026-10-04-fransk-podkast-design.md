# Fransk-podkast: design

Dato: 2026-10-04
Status: til gjennomlesning

## Mål

Edvard skal klare småprat på fransk, først med franske turister i Norge, deretter som turist i Frankrike. Han har litt skolefransk, ingen frist og vil ikke betale for verktøy eller tjenester.

Suksess etter rundt et halvt år: han kan starte og holde gående en enkel samtale (hilse, spørre hvor folk kommer fra, gi tips om Oslo og Norge, fortelle om seg selv), og klare kafé, restaurant, hotell og veibeskrivelse i Frankrike.

## Læringsopplegget

Ukesrytme:

| Når | Hva |
|---|---|
| Rolig løpetur 1 (ca. 25 min) | Ny episode |
| Rolig løpetur 2 (ca. 25 min) | Samme episode en gang til |
| Helg | Samtale med Codex sin talemodell om ukas tema, gloser og fraser |

Én episode per uke. Hver episode har 10 nye gloser og 6–8 fraser. Det muntlige veier tyngst. Lytting skjer på løpeturen, aktiv bruk skjer i helgesamtalen.

Lytting skjer på mobil (podkastapp) eller på Garmin-klokke uten telefon.

## Episodeformat

Mål: 20–25 minutter. Norsk stemme forklarer, fransk stemme sier alt på fransk.

| Del | Varighet | Innhold |
|---|---|---|
| 1. Intro | 0,5 min | Uke, tema og hva lytteren skal klare etter episoden |
| 2. Repetisjon | 3 min | Rundt 8 gloser fra tidligere uker. Norsk ord, 3 sekunders pause, fransk ord. |
| 3. Ukas 10 gloser | 7 min | Fransk to ganger sakte, betydning, kort uttaletips, eksempelsetning |
| 4. Ukas fraser | 6 min | 6–8 fraser som bruker glosene. Lange fraser bygges bakfra (backchaining). |
| 5. Dialog | 4 min | Kort samtale mellom to franske stemmer. Først sakte med norske forklaringer innimellom, så i nesten normalt tempo uten avbrudd. |
| 6. Avslutning | 2 min | Alle 10 glosene i norsk–pause–fransk-format, og helgeoppdraget |

Regler:

- Pause på 2–3 sekunder etter hver frase, så lytteren kan mumle med. Valgfritt å bruke.
- Fransk leses saktere enn normalt de første månedene. Tempoet økes gradvis.
- Forklaringene er på norsk. Faste vendinger («neste ord») kan etter hvert byttes til fransk.

### Repetisjonsregel

Repetisjonsdelen i uke N henter gloser fra uke N−1, N−2, N−4 og N−8 (de som finnes), til sammen rundt 8. Ved flere kandidater enn plass velges jevnt fra hver av ukene. Skriptet foreslår glosene, og manusforfatteren (Claude) bruker forslaget.

## Pensum

`pensum.md` lister temaer for de første rundt 26 ukene. Turister i Norge kommer før Frankrike. Grov rekkefølge:

1. Uke 1–4: hilse, presentere seg, hvor kommer du fra, si at man snakker litt fransk og be om saktere tale
2. Uke 5–12: småprat med turister i Norge. Hvor lenge er dere her, liker dere Norge, tips om Oslo og Norge, vær, jobb, fritid, familie, tall og tid
3. Uke 13–20: turist i Frankrike. Kafé, restaurant, butikk, hotell, veibeskrivelse, transport
4. Uke 21–26: holde samtalen gående. Fortid (passé composé), følge opp svar, fortelle om en tur

Pensum kan justeres underveis. Episodene skrives én om gangen.

## Arbeidsflyt per uke

1. Edvard åpner Claude Code i repoet og ber om neste episode.
2. Claude kjører `uv run fransk repetisjon N`, leser `pensum.md` og tidligere manus, og skriver `episoder/uke-NN.yaml`.
3. `uv run fransk lag N` lager MP3-filen lokalt. Edvard kan høre gjennom.
4. `uv run fransk publiser N` oppdaterer feeden, committer og pusher. Episoden dukker opp i podkastappen.
5. Ved løping med klokke overføres MP3-filen med Garmin Express.

## Repo-struktur

```
fransk-podkast/
  pensum.md
  episoder/uke-01.yaml ...      manus, én fil per episode
  src/fransk/                   Python-pakken
  tests/
  docs/                         det GitHub Pages publiserer
    feed.xml
    cover.jpg
    lyd/uke-01.mp3 ...
  design/specs/                 designdokumenter (ikke publisert)
  .cache/                       mellomlagrede lydbiter (gitignored)
```

GitHub-repoet er offentlig (krav for GitHub Pages på gratis konto). Pages serverer `docs/` fra `main`.

## Manusformat

```yaml
uke: 1
tittel: "Hei, hvor kommer du fra?"
beskrivelse: "Hilse, presentere seg og spørre hvor folk kommer fra."
gloser:
  - { fr: "bonjour", no: "hei, god dag" }
  # nøyaktig 10
fraser:
  - { fr: "Vous venez d'où ?", no: "Hvor kommer dere fra?" }
  # 6–8
codex_instruks: |
  Teksten Edvard limer inn i helgesamtalen med Codex.
segmenter:
  - no: "Velkommen til uke én."
  - fr: "Bonjour"
    fart: sakte          # sakte | normal, standard: sakte
    stemme: b            # a | b, for dialog med to franske stemmer, standard: a
  - pause: 3             # sekunder
```

Validering stopper kjøringen med en tydelig feilmelding ved:

- manglende eller ukjente felt
- tom tekst i et segment
- annet antall gloser enn 10, eller fraser utenfor 6–8
- et segment med mer enn én av `no`, `fr` og `pause`
- `uke` som ikke stemmer med filnavnet

## Komponenter

Python-pakke `fransk`, kjøres med `uv`. Hver modul har én oppgave.

### `manus`

Leser og validerer en YAML-fil og returnerer en `Episode` (dataklasse). Leser også alle manus for å hente gloser til repetisjon. Ingen lyd- eller nettverkskode.

### `tale`

`lag_lyd(tekst, språk, fart, stemme) -> Path` returnerer en lydfil for én replikk.

- Prøver edge-tts først. Stemmer: norsk `nb-NO-FinnNeural`, fransk a `fr-FR-DeniseNeural`, fransk b `fr-FR-HenriNeural`. Sakte fart er `-20%`.
- Feiler edge-tts (nettverk, endret API), brukes macOS `say`: norsk `Nora`, fransk a `Thomas`, fransk b `Jacques`. Sakte fart settes med `-r`. Bytte logges én gang per kjøring.
- Resultatet mellomlagres i `.cache/` med en nøkkel laget av tekst, språk, fart, stemme og motor. Samme replikk lages ikke på nytt.

### `lyd`

Setter sammen lydbiter og stillhet til én MP3 med ffmpeg.

- Lydnivået jevnes ut (`loudnorm`) så stemmene høres like sterkt og holder seg over vind og trafikk.
- Mono, 64 kbit/s, 44,1 kHz. Omtrent 12 MB per episode.
- ID3-tagger: tittel `Uke 01: <tittel>`, album `Fransk på løpetur`, spornummer lik uke. Gir riktig sortering på Garmin-klokka.

### `feed`

Lager `docs/feed.xml` (RSS 2.0 med iTunes-tagger) fra alle manus med en tilhørende MP3 i `docs/lyd/`. Episodebeskrivelsen inneholder gloselista, frasene og Codex-instruksen. Varighet og filstørrelse leses fra MP3-filen.

### `cli`

| Kommando | Gjør |
|---|---|
| `uv run fransk lag N` | Validerer manus og lager `docs/lyd/uke-NN.mp3` |
| `uv run fransk publiser N` | Lager MP3 om den mangler, oppdaterer feeden, committer og pusher |
| `uv run fransk repetisjon N` | Skriver ut foreslåtte repetisjonsgloser for uke N |
| `uv run fransk sjekk N` | Validerer bare manuset |

## Codex-instruks

Hver episode har en ferdig instruks til helgesamtalen. Den sier at Codex skal være en fransk turist i en gitt situasjon, holde seg til ukas og tidligere gloser, snakke sakte og enkelt, gi korte rettelser på norsk etter hvert svar og holde samtalen rundt 10 minutter. Instruksen ligger i manuset og i episodebeskrivelsen i podkastappen.

## Feilhåndtering

- Valideringsfeil stopper før lyd lages.
- edge-tts-feil gir automatisk bytte til `say`. Feiler også `say`, stopper kjøringen med replikken som feilet.
- Mangler ffmpeg, sier feilmeldingen `brew install ffmpeg`.
- `publiser` stopper hvis git-arbeidskopien har andre uncommittede endringer enn de kommandoen selv lager.

## Plass

GitHub Pages har en grense på 1 GB. Med 12 MB per episode holder det i rundt 80 uker. Da sletter vi de eldste episodene.

## Testing

Automatiske tester (pytest):

- Manusvalidering: gyldig manus og hver av feiltilfellene over
- Repetisjonsvalg: riktige uker, riktig antall, oppførsel tidlig i løpet når få uker finnes
- Feed: gyldig XML, riktige episoder, beskrivelse inneholder gloser og Codex-instruks
- Tale: bytte til `say` når edge-tts feiler (edge-tts mockes), mellomlagring brukes ved andre kall
- Lyd: sammensetting av to korte biter og en pause gir en MP3 med forventet lengde (kjøres bare når ffmpeg finnes)

Manuell kontroll av første episode: Edvard hører gjennom, legger feeden til i podkastappen og spiller filen på Garmin-klokka.

## Utenfor omfang

- Betalte talemotorer (OpenAI, ElevenLabs)
- Egen app eller nettside utover feeden
- Automatisk generering av manus uten at Edvard ber om det
- Taleøving i selve skriptet. Den skjer i helgesamtalen med Codex.
- Anki eller annen repetisjon med kort
