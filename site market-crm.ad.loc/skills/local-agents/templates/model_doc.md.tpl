## {{ModelName}}

- Description: {{ShortDescription}}
- Location: `{{app_path}}`

Fields:

| Field | Type | Notes |
|---|---:|---|
{{#each Fields}}
| {{name}} | {{type}} | {{notes}} |
{{/each}}

Relations and important behaviors:

- {{RelationNotes}}

Example serialized output:

```json
{{ExampleJSON}}
```

Recommended logging points:

- On import: `logger.info("imported", extra={"source_file": file, "rows": n})`
- On match failure: `logger.warning("match_failed", extra={"row_id": id})`
