# Tesla · radionica srpskog NLP-a

Jednostavna lokalna aplikacija za učenje obrade srpskog jezika: **imenovani entiteti (NER), vrste reči i leme, emocije i kratki sažeci**. Unesite tekst latinicom ili ćirilicom, učitajte UTF-8 TXT, isprobajte primere i preuzmite tabelu ili JSON sa oznakom modela i njegovom revizijom.

## Najkraći put do aplikacije

GitHub nalog nije potreban. [Preuzmite ZIP](https://github.com/sasa5linkar/tesla-nlp-workshop/archive/refs/heads/main.zip), pa ga **raspakujte**. Ne pokrećite datoteke iz otvorene ZIP arhive.

1. Instalirajte **uv** prema [zvaničnom uputstvu](https://docs.astral.sh/uv/getting-started/installation/). Proverena verzija za ovu radionicu: `0.9.7`. Na Windowsu se može instalirati i pomoću `winget install --id astral-sh.uv --exact`.
2. Windows: dvaput kliknite `start.bat`. macOS: u terminalu u raspakovanom folderu pokrenite `sh start.command`. Linux: `sh start.sh`.
3. Otvorite **http://127.0.0.1:7860** u pregledaču. Prozor terminala ostaje otvoren dok aplikacija radi.
4. Izaberite karticu, kliknite na primer ili unesite tekst, pa na **Analiziraj tekst**. Prvo korišćenje određenog modela preuzima njegove težine; sačekajte prikaz napretka.
5. Za kraj u terminalu pritisnite **Ctrl+C**.

uv automatski instalira Python **3.11.14** i zaključane zavisnosti iz `uv.lock`. Globalni Python, GitHub Desktop i VS Code nisu potrebni. GitHub Desktop je zgodan za preuzimanje novih verzija, a VS Code za razgledanje koda, ali ne predstavljaju uslov za radionicu.

Preporučeno: **16 GB RAM-a**, 15 GB slobodnog diska, 64-bitni savremeni računar. Težine zauzimaju približno 5,4 GB, uz dodatni raspakovani spaCy model i Python pakete. CPU je podrazumevan na svim platformama; aplikacija ne koristi GPU ni udaljeni servis za analizu. Windows provere i stvarna vremena nalaze se u [izveštaju o testiranju](docs/TESTING.md). Uputstvo za Mac/Linux ne znači da su ti sistemi lokalno testirani.

## Šta rade kartice

| Kartica | Model | Granica ulaza | Tumačenje |
|---|---|---|---|
| NER | Tanor/sr_judig2026_teslaxlm | 3.000 spaCy tokena; dodatna provera podrečničkih prozora | Devet izvornih klasa; obojeni rasponi i tabela tokena |
| Vrste reči i leme | isti JuDig2026 | ista granica | UPOS i lema; model ne predviđa bogatu morfologiju |
| Emocije | te-sla/serbian-emotion-teslaxlm | 128 modelskih tokena sa specijalnim tokenima | Osam nezavisnih sigmoid skorova i objavljeni pragovi |
| Kratak sažetak | te-sla/pilot5-sumarizacija | 512 modelskih tokena sa specijalnim tokenima | Do 80 novih tokena; proveriti činjenice uz izvornik |

Ukupna granica je 12.000 znakova, a TXT do 48 KB. Predugačak unos se odbija uz objašnjenje; ništa se ne odseca neprimetno. Sačekajte završetak jednog zahteva pre sledećeg. Svi zadaci dele red i zaključavanje: **jedan veliki model u memoriji u jednom trenutku**. NER i POS dele istu instancu; posle emocija ili sažetka JuDig se ponovo učitava.

NER/POS nemaju izmišljene procente pouzdanosti. JuDig NEL komponenta je izostavljena: ova verzija ne prikazuje Wikidata identifikatore ni veze. Emocioni skorovi nisu raspodela koja sabiranjem daje 100%, niti je prazna lista sinonim za neutralno. Sažetak može promeniti pismo ili izmisliti činjenicu. To su predviđanja za radionicu, a ne referentne anotacije. Primere treba uporediti i ručno razmotriti greške.

## Rezultati i privatnost

**JSON** čuva tačan izvorni tekst, raspone entiteta, tabelu, objašnjenje, reviziju, licencu i vreme izvršavanja. **TSV** čuva tabelu, sa UTF-8 BOM-om za Excel. Ćelije koje mogu postati Excel formule dobijaju zaštitni apostrof; JSON čuva izvorne vrednosti bez te promene.

Server sluša isključivo `127.0.0.1`, sa `share=False`. Nema udaljene inferencije, Hugging Face prijave, neprimetnog slanja teksta ni beleženja sirovog teksta u aplikacione logove. Telemetrija Gradio/HF je isključena. Internet je potreban za pakete i prva preuzimanja sa javnog Hugging Face repozitorijuma. Anonimni zahtev sadrži naziv modela i mrežne metapodatke, ne vaš tekst. Učitavanje Transformers modela koristi `trust_remote_code=False` i safetensors. JuDig wheel se **ne instalira i ne importuje**: proverava se SHA-256 i izdvajaju samo model-podaci; paketni Python kod se ne izvršava.

Modeli su keširani van repozitorijuma: Windows `%LOCALAPPDATA%\tesla-nlp-workshop\models`, drugi sistemi `~/.cache/tesla-nlp-workshop/models`. `.venv` je unutar projekta. Otpremljene datoteke i izvozi jesu lokalne privremene datoteke: mogu ostati na disku nakon zatvaranja. Gradio briše stare datoteke dok server radi; po potrebi očistite svoje privremene datoteke posle radionice. Ne unosite osetljiv tekst na zajedničkom računaru.

## Ako nešto ne radi

- `uv` nije pronađen: zatvorite i ponovo otvorite terminal posle instalacije; proverite `uv --version` i uputstvo iz prvog koraka.
- Prvi klik dugo traje: modeli imaju oko 1–2,3 GB po zadatku. Sačekajte napredak i obezbedite dovoljno diska/RAM-a.
- Greška preuzimanja: proverite vezu i pristup `huggingface.co`, pa pokušajte ponovo. Ne isključujte proveru sertifikata i ne koristite `trust_remote_code=True`.
- Previše tokena: skratite odlomak. Modelski token nije isto što i reč; ćirilica, nepoznate reči i specijalni znakovi mogu zauzeti više tokena.
- Port 7860 je zauzet: ugasite prethodnu instancu radionice. Nemojte uključivati deljenje ili menjati adresu na `0.0.0.0`.
- Greška analize: aplikacija prikazuje tip greške bez privatnog teksta. Za tehničku pomoć navedite karticu, tip greške, operativni sistem i verziju aplikacije.

## Za razvijače i nastavnike

```sh
uv sync --locked
uv run --locked pytest -q
uv run --locked python scripts/smoke.py
uv run --locked python -m workshop
```

`scripts/smoke.py` zaista preuzima modele i radi CPU inferenciju; očekujte veliki prenos i potrošnju memorije. Zapisuje samo ugrađene izmišljene primere u `docs/runtime-results.json`. Aplikacija ne zapisuje korisničke analize u taj fajl. Testovi bez mreže koriste kontrolisane zamene samo za granice/greške; nisu zamena za ovaj test.

Za čist instalacioni test koristite novi folder i novu `.venv`; po potrebi i zaseban `UV_CACHE_DIR`. Modeli i sve tranzitivne zavisnosti su zaključani. Promena revizije je pregledana izmena koda, ne slobodno polje za proizvoljan model. Prvo ažurirajte audit, zatim stvarne testove. [Specifikacija](SPEC.md) opisuje granice projekta.

## Licence i poreklo

Kod radionice je MIT. Težine se preuzimaju odvojeno i nisu u ovom Git repozitorijumu. JuDig i TeslaXLM emocije imaju CC BY-SA 4.0, PiloT5 sažimanje CC BY 4.0; poštujte njihove licence i navedite autore pri daljoj upotrebi. [Audit modela](docs/MODELS.md) sadrži izvore, revizije i razloge izbora. Licence modela ne daju automatsko pravo na njihove izvorne korpuse.
