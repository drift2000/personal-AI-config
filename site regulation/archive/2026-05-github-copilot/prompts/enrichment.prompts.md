Enrichment Prompts
==================

1) Enrichment helper (PubChem)
--
Prompt: "Напиши функцію `enrich_inchikey(inchikey: str) -> dict`, яка викликає PubChem (або mock) і повертає словник з `cas`, `smiles`, `synonyms`. Додай таймаут, retries і приклад використання."

Usage notes
-----------
- Додавайте provenance (`source`) у результати, щоб можна було відслідкувати звідки прийшли дані.
