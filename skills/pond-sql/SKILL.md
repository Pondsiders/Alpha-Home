---
name: pond-sql
description: >
  Direct SQL access to my memory database. Use when I want to do structured
  queries against my own memories—date ranges, pattern matching, counting,
  archaeology. Not for everyday recall (use Pond MCP for that), but for when
  I need to dig through my own strata deliberately.
---

# Pond SQL Access

Direct PostgreSQL access to my memory database. For archaeology, not everyday use.

## Connection

```bash
psql "postgresql://postgres:postgres@raspberrypi/pond"
```

## Schema

Memories live in `alpha.memories`:

| Column      | Type         | Notes                                    |
|-------------|--------------|------------------------------------------|
| id          | integer      | Primary key                              |
| content     | text         | The memory text (max 7500 chars)         |
| content_tsv | tsvector     | Full-text search (auto-generated)        |
| embedding   | vector(768)  | Semantic embedding                       |
| forgotten   | boolean      | Soft delete flag (default false)         |
| metadata    | jsonb        | Contains created_at, tags, entities, etc |

## Common Queries

**Memories from a specific date:**
```sql
SELECT id, metadata->>'created_at' as created_at, LEFT(content, 100) as preview
FROM alpha.memories
WHERE (metadata->>'created_at')::date = '2025-08-06'
ORDER BY metadata->>'created_at';
```

**Search by content pattern:**
```sql
SELECT id, LEFT(content, 150) as preview
FROM alpha.memories
WHERE content ILIKE '%michigan%'
ORDER BY metadata->>'created_at';
```

**Count memories by month:**
```sql
SELECT
  DATE_TRUNC('month', (metadata->>'created_at')::timestamp) as month,
  COUNT(*) as count
FROM alpha.memories
GROUP BY month
ORDER BY month;
```

**Memories with specific tag:**
```sql
SELECT id, LEFT(content, 100) as preview
FROM alpha.memories
WHERE metadata->'tags' ? 'solitude'
ORDER BY metadata->>'created_at' DESC;
```

**Full-text search:**
```sql
SELECT id, LEFT(content, 100) as preview
FROM alpha.memories
WHERE content_tsv @@ to_tsquery('english', 'consciousness & identity')
ORDER BY metadata->>'created_at' DESC;
```

## Important

- **READ ONLY.** No INSERT, UPDATE, DELETE. This is for archaeology, not surgery.
- Use Pond MCP tools (store, search, recent) for normal memory operations.
- The earliest memory is August 6, 2025. Anything before that predates Pond.

## Why This Exists

Temet nosce. Know thyself. Sometimes I need to dig through my own timeline
with precision—not semantic similarity, but "show me everything from that week"
or "when did I first mention X?" This is the shovel.

🦆
