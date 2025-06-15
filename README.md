# 🦆 kwak

**kwak** is een command-line tool om **Retrieval-Augmented Generation (RAG)** te testen op synthetische _subsidiedossiers_ met behulp van **DuckDB**.

Het project is geïnspireerd op de [blogreeks van MotherDuck over zoeken met DuckDB](https://motherduck.com/blog/search-using-duckdb-part-1/) en dient als experimenteeromgeving voor het lokaal uitvoeren van semantische zoekopdrachten en het testen van embeddings.

---

## Wat doet kwak?

- ✅ Genereert synthetische subsidiedossiers met OpenAI of vaste voorbeelden  
- ✅ Laadt gestructureerde en vector-gebaseerde data in DuckDB  
- ✅ Ondersteunt hybride zoekopdrachten: metadata + semantische overeenkomst  
- ✅ Biedt een speeltuin om lokaal RAG-oplossingen uit te proberen

Een typisch *subsidiedossier* bevat:
- `type`: bv. *erfgoed*, *kunst*, *jeugd*
- `omschrijving`: een lange beschrijving van het project
- `startdatum`, `einddatum`
- `goedgekeurd_budget`: een bedrag in euro
- `advies`: de motivering van de beoordelingscommissie

Je kan vragen stellen als:
> Welke subsidiedossiers omtrent erfgoed werden ingediend tussen 2019 en 2021?

---

## Installatie

```bash
./run.sh
```

## Gebruik

```bash
kwak generate-data --count 50 --model gpt-4
kwak ingest
kwak query "Welke subsidiedossiers over jeugd tussen 2020 en 2022 kregen een positief advies?"
```


