# Radionica: analiza i ručna ispravka

Podrazumevana kartica koristi JuDig2026 za granice rečenica, POS, leme, devet NER klasa i NEL/Wikidata. Model i njegova revizija su fiksirani u kodu. Puni režim učitava objavljenu bazu znanja i linker; režim bez NEL zadržava rečenice/POS/leme/NER. Promena režima oslobađa prethodni model pre učitavanja sledećeg. Puni NEL troši više RAM-a: planirajte najmanje 16 GB, uz napomenu da to nije izmerena garantovana granica za svaki računar ili unos.

1. Unesite kratak tekst ili učitajte UTF-8 TXT, do 48 KB. Latinica i ćirilica su podržane. Ne unosite privatne korpuse u zajednički računar. Granica je 12.000 znakova, 3.000 spaCy tokena i 512 podrečničkih tokena u svakom prozoru. Predug unos se odbija bez odsecanja.
2. Izaberite režim i kliknite na analizu. Prvo korišćenje preuzima javni model; naredne analize koriste lokalni keš.
3. Uporedite obojeni tekst, tabelu entiteta, tokene i rečenice. Oznake i leme nisu referentne anotacije. QID je predviđena veza i može biti pogrešna; `NIL` označava odsustvo veze. Ne prikazuju se izmišljene verovatnoće.
4. Preuzmite HTML za pregled, TSV za ispravke i JSON kao tačan zapis originala i predviđanja. Izmena ulaza/režima briše prikazane rezultate; zahtev završen za prethodni unos ne vraća stare izvoze.

## Karta lokacija i internet

Analiza sama ne upituje Wikidata. Ako želite kartu, označite saglasnost i posebno kliknite na preuzimanje koordinata. Jedan zahtev šalje najviše 20 jedinstvenih sintaktički validnih QID-ova iz predviđenih LOC entiteta na `https://www.wikidata.org/w/api.php`. Ne šalje ceo tekst, imena pominjanja ili identifikatore sesije. Servis ipak vidi QID-ove i uobičajene mrežne podatke. Postavke proksija i TLS provera ostaju nepromenjene.

Nema automatskog ponavljanja. Granice: povezivanje do 5 sekundi, čekanje mrežnog čitanja do 15 sekundi, dodatna provera trajanja čitanja od 20 sekundi, najviše 8 MiB odgovora. Memorijski TTL/LRU keš sadrži do 256 javnih QID/koordinatnih zapisa, do 24 sata, bez korisničkog teksta. QID-ovi preko granice upita se prijavljuju i ne crtaju. Nedostajući, neispravni, zastareli ili vanzemaljski P625 iskazi se ne koriste; nema nagađanja po nazivu mesta.

HTML i aplikacija prikazuju ravnu kartu koordinata WGS84 sa mrežom geografskih širina/dužina, brojevima tačaka i spiskom izvora Wikidata P625 (strukturirani podaci CC0), koordinata i vremena preuzimanja. Karta nema geografsku podlogu niti precizne granice država; bliske tačke mogu se preklopiti. Sve tačke potiču iz odgovora za odgovarajući QID, ali sama NEL veza sa izvornim tekstom zahteva ručnu proveru. Ako nema koordinata ili zahtev ne uspe, ostaju dostupni tekst, predviđanja i izvozi.

Izvezeni HTML ne učitava spoljne skripte, slike, fontove ili pločice i radi van mreže. Opcioni klik na Wikidata ili OpenStreetMap otvara spoljni sajt; tada su potrebni internet i uobičajeni mrežni zahtevi tog sajta. Tekst HTML anotacija je bezbedno kodiran; `NIL` i neispravni ID-ovi nikada nisu URL-ovi.

## Ispravke u Excelu

Uvezite TSV kao UTF-8 tekst razdvojen tabulatorima. Za jezičke kolone izaberite tekstualni tip podataka, da Excel ne pretvara oblike u datume ili brojeve. Tabela ima jedan red po tokenu. `document_id` je SHA-256 UTF-8 originala; `sentence_id`, `token_id` i `sentence_token_id` počinju od 1. `start` počinje od nule, a `end` ne uključuje završni znak. Jedinica je Unicode znak (Python code point), a ne bajt ili UTF-16 jedinica. `form` i `whitespace` zajedno rekonstruišu original. Ceo izvor je i u `source_text` prvog reda i u JSON-u.

Originalne kolone `lemma`, `pos`, `tag`, `ner_iob`, `ner`, `entity_id`, `kb_id` i `qid` čuvaju izvorna predviđanja. Ostavite ih za poređenje, pa upišite ispravke u `corrected_lemma`, `corrected_pos`, `corrected_ner`, `corrected_qid` i `notes`. Prazna ispravka znači da ispravka još nije uneta. Za uklanjanje pogrešne veze upišite `NIL` u `corrected_qid`. Ova verzija izvozi tabelu za ručnu ispravku; ne uvozi ispravke nazad u model.

Ćelije koje posle početnih belina počinju sa `=`, `+`, `-` ili `@` dobijaju jedan zaštitni apostrof da ih Excel ne izvrši kao formulu. Kolona `excel_escaped_fields` navodi tačno polja sa tim dodatim apostrofom, razdvojena znakom `|`. Za programsko vraćanje originala uklonite tačno jedan početni apostrof samo iz navedenih polja. Ne brišite sve apostrofe i ne tretirajte zaštitu kao jezički deo oblika. JSON čuva izvorne vrednosti bez te zaštite. Standardno CSV/TSV kodiranje čuva tabulatore i nove redove unutar navodnika.

HTML zadržava tačan izvor u `<pre id="source">`; uklanjanje anotacionih oznaka vraća isti tekst. JSON i TSV uključuju naziv i reviziju modela. Izvozi su lokalne privremene datoteke i mogu ostati na disku nakon zatvaranja aplikacije; sačuvajte svoje primerke i po potrebi obrišite privremene fajlove.

## Mogućnosti drugih modela

Lokalna instalacija nudi samo dve konfiguracije istog JuDig modela. CNN i četvoroklasni NER/NEL modeli nisu u ovom izboru. Njihov NER/NEL izlaz ne znači da pružaju JuDig POS, leme ili segmentaciju rečenica. Stariji `Tanor/sr_SRPCNNEL` radi u zasebnom spaCy 3.5.4 Colab okruženju; ne meša se sa lokalnim spaCy 3.8.11 zaključavanjem. Colab beležnice održavaju se odvojeno.

Sažetak i emocije su odvojeni ogledi uz `uv run --locked python -m workshop --experiments`. Ne pojavljuju se u podrazumevanoj radionici. Ograničenja eksperimentalnog latiničnog sažetka i izvorne oznake emocija ostaju na snazi.
