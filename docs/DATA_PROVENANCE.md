# Data provenance and release boundary

- **Source for implementation:** the owner's November 11 final submission-review project, not the older Downloads draft.
- **Public data:** generated from scratch by `generate_demo.py`; no sampling, anonymization, transformation or copying of original data rows. Fictional names use `Demo`, identifiers use `SYN-`, `DEAL-`, `SHIFT-`, `H` and `O` prefixes.
- **Public results:** produced by executing the public calculation engine on those fictional rows. They are not representative of any real population.
- **Original policy logic:** retained as an educational case-model implementation. It is not asserted to describe an employer's actual compensation arrangements.
- **Adaptations:** standalone JSON-based input runner, new synthetic fixtures, hand-calculated unit tests, source metadata changed to synthetic JSON, and new public-facing documentation.
- **Excluded:** original prompt and data, source-specific contracts/templates, original XLSX/PDF outputs, recruiter contact details, raw historical validation artifacts and private filesystem paths.
- **Private archive:** stores the complete prior submission-review package separately. It is not a public redistribution license.

No secrets, API keys, login details or private contact information are needed by this demo. Do not add real employee records or the original assessment dataset to this repository.
