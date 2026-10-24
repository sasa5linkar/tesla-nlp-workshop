# Tesla · radionica srpskog NLP-a

Lokalna aplikacija za radionicu obrade srpskog jezika: **rečenice, vrste reči (POS), leme, imenovani entiteti (NER) i povezivanje sa Wikidata (NEL)** pomoću novog JuDig modela. Unesite kratak tekst latinicom ili ćirilicom ili učitajte UTF-8 TXT. Pregledajte predviđanja, preuzmite HTML sa anotacijama i TSV za ispravke u Excelu; JSON čuva tačan izvor i metapodatke. Koordinate povezanih lokacija preuzimaju se samo uz poseban pristanak.

## Najkraći put do aplikacije

GitHub nalog nije potreban. [Preuzmite ZIP](https://github.com/sasa5linkar/tesla-nlp-workshop/archive/refs/heads/main.zip), pa ga **raspakujte**. Ne pokrećite datoteke iz otvorene ZIP arhive.

1. Instalirajte **uv** prema [zvaničnom uputstvu](https://docs.astral.sh/uv/getting-started/installation/). Proverena verzija za ovu radionicu: `0.9.7`. Na Windowsu se može instalirati i pomoću `winget install --id astral-sh.uv --exact`.
2. Windows: dvaput kliknite `start.bat`. macOS: u terminalu u raspakovanom folderu pokrenite `sh start.command`. Linux: `sh start.sh`.
3. Otvorite **http://127.0.0.1:7860** u pregledaču. Prozor terminala ostaje otvoren dok aplikacija radi.
4. U kartici **Radionica** izaberite puni JuDig sa NEL/KB ili lakši režim bez NEL. Kliknite na primer ili unesite tekst, pa na **Analiziraj · učitaj izabrani model**. Prvo korišćenje preuzima javne težine; sačekajte prikaz napretka. Puni NEL zahteva više RAM-a.
5. Za kraj u terminalu pritisnite **Ctrl+C**.

uv automatski instalira Python **3.11.14** i zaključane zavisnosti iz `uv.lock`. Globalni Python, GitHub Desktop i VS Code nisu potrebni. GitHub Desktop je zgodan za preuzimanje novih verzija, a VS Code za razgledanje koda, ali ne predstavljaju uslov za radionicu.

Preporučeno: **16 GB RAM-a**, 15 GB slobodnog diska, 64-bitni savremeni računar. Težine zauzimaju približno 5,4 GB, uz dodatni raspakovani spaCy model i Python pakete. CPU je podrazumevan na svim platformama; aplikacija ne koristi GPU ni udaljeni servis za analizu. Windows provere i stvarna vremena nalaze se u [izveštaju o testiranju](docs/TESTING.md). Uputstvo za Mac/Linux ne znači da su ti sistemi lokalno testirani.

## Šta rade kartice

| Kartica | Model | Granica ulaza | Tumačenje |
|---|---|---|---|
| Radionica · puni JuDig | Tanor/sr_judig2026_teslaxlm, objavljena KB i linker | 3.000 spaCy tokena; dodatna provera podrečničkih prozora | Rečenice, POS, leme, devet NER klasa i stvarna NEL predviđanja/QID |
| Radionica · JuDig bez NEL | isti JuDig2026, linker/KB izostavljeni | ista granica | Rečenice, POS, leme i NER; bez Wikidata predviđanja |

Ukupna granica je 12.000 znakova, a TXT do 48 KB. Predugačak unos se odbija uz objašnjenje; ništa se ne odseca neprimetno. Sačekajte završetak jednog zahteva pre sledećeg. Svi zadaci dele red i zaključavanje: **jedan veliki model u memoriji u jednom trenutku**. NER i POS dele istu instancu; posle emocija ili sažetka JuDig se ponovo učitava.

Izvorne oznake i QID-ovi ostaju predviđanja modela, bez izmišljenih procenata pouzdanosti. `NIL` i neispravni identifikatori se nikada ne pretvaraju u veze. Pregledajte leme, POS, granice rečenica i NER/NEL greške ručno. Izbor bez NEL ne učitava linker/KB. CNN i četvoroklasni modeli nisu uključeni u ovu lokalnu instalaciju; ne pripisujemo im JuDig POS/lemma mogućnosti. Stariji CNN zahteva zasebno spaCy 3.5.4 okruženje u Colabu.

Sažetak i emocije **nisu deo podrazumevane radionice**. Ako su potrebni za zaseban ogled, pokrenite `uv run --locked python -m workshop --experiments`. Eksperimentalni sažetak ostaje samo za latinicu, odbija nepoznate tokene i zahteva proveru činjenica; i latinični izlazi mogu izmišljati ili izostavljati činjenice. Emocije zadržavaju izvornih osam oznaka i objavljene pragove.

Aplikacija postavlja `USE_TF=0`, `USE_FLAX=0`, `USE_TORCH=1` pre uvoza biblioteka, da ne bi učitavala nepotrebne radne okvire i trošila dodatni RAM. Zaključana instalacija uključuje SOCKS podršku za HTTPX i Requests; postojeće postavke proksija i provera sertifikata se ne menjaju. Izmena teksta ili modela briše stare rezultate i izvoze; rezultat zahteva koji je završen za prethodni unos se ne prikazuje uz novi unos.

## Rezultati i privatnost

**HTML** čuva anotirani izvorni tekst, izvorne NER klase, QID veze, rečenice i kartu koordinata kada su koordinate preuzete. Radi bez spoljnih skripti i pločica karte; klik na spoljne Wikidata/OpenStreetMap veze zahteva internet. **JSON** čuva tačan izvorni tekst, raspone, tokene, reviziju, licencu i merenja. **TSV** ima UTF-8 BOM, document/sentence/token ID, originalni oblik, beline, pomake, lemu, POS, NER i KB/QID, uz prazne `corrected_*` kolone za učesnike. `source_text` prvog reda čuva ceo original. Zaštitni apostrof sprečava Excel formule; `excel_escaped_fields` navodi svako zaštićeno polje, pa se original vraća uklanjanjem tačno jednog dodatog apostrofa samo u tim poljima. Detalji i postupak ispravke su u [uputstvu za radionicu](docs/WORKSHOP.md).

**Karta je opcioni internet korak:** prvo označite saglasnost, pa kliknite na preuzimanje koordinata. Šalju se samo do 20 jedinstvenih LOC QID-ova na Wikidata, bez izvornog teksta. Upit ima vremenske/veličinske granice i ograničen memorijski keš. Crtaju se samo stvarno vraćene Zemljine koordinate P625, uz izvor i vreme preuzimanja. Predviđena veza sa QID-om i dalje može biti pogrešna. Ako nema entiteta, koordinata ili mreže, analiza i izvozi ostaju dostupni. Bez tog koraka aplikacija ne šalje QID upite.

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
uv run --locked python scripts/smoke_workshop.py
# Opcioni stvarni internet test: šalje samo predviđene LOC QID-ove na Wikidata
uv run --locked python scripts/smoke_workshop.py --coordinates
uv run --locked python scripts/smoke.py --small
uv run --locked python scripts/smoke.py
uv run --locked python -m workshop
```

`scripts/smoke_workshop.py` radi punu JuDig CPU analizu i provere izvoza; `--coordinates` izričito uključuje stvarni QID upit. `scripts/smoke.py` pokreće i dodatne modele. Očekujte veliki prenos pri prvom pokretanju i potrošnju memorije. Izveštaji čuvaju samo ugrađene izmišljene primere, nikada korisničke analize. Testovi bez mreže koriste kontrolisane zamene za granice i greške; nisu zamena za stvarnu inferenciju. [Provere i ograničenja](docs/TESTING.md) navode stvarno testirano okruženje.

Za čist instalacioni test koristite novi folder i novu `.venv`; po potrebi i zaseban `UV_CACHE_DIR`. Modeli i sve tranzitivne zavisnosti su zaključani. Promena revizije je pregledana izmena koda, ne slobodno polje za proizvoljan model. Prvo ažurirajte audit, zatim stvarne testove. [Specifikacija](SPEC.md) opisuje granice projekta.

## Licence i poreklo

Kod radionice je MIT. Težine se preuzimaju odvojeno i nisu u ovom Git repozitorijumu. JuDig i TeslaXLM emocije imaju CC BY-SA 4.0, PiloT5 sažimanje CC BY 4.0; poštujte njihove licence i navedite autore pri daljoj upotrebi. [Audit modela](docs/MODELS.md) sadrži izvore, revizije i razloge izbora. Licence modela ne daju automatsko pravo na njihove izvorne korpuse.
