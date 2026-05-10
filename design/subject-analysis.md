# Subject Analysis: Flashcard Study Tracker

## Candidate Entities

**Deck** — a named collection of flashcards. Identified by a serial integer primary key. Has a name (unique), an optional description, and a created_at timestamp.

**Card** — a single question–answer pair that belongs to exactly one deck. Has a serial primary key, a foreign key to decks, and a created_at timestamp.

**Tag** — a short label that can be attached to cards. Has a serial primary key, a name, and a created_at timestamp. Tags are global — they are not owned by any deck or user.

**CardTag** — a junction record linking one card to one tag. The primary key is the composite (card_id, tag_id). No additional attributes.

There is no **User** entity. The schema assumes a single implicit user or a fully open, unauthenticated application.

## Candidate Relationships

- **Deck contains Cards** — one-to-many. A deck may have zero or more cards; a card belongs to exactly one deck.
- **Card is labelled by Tags** — many-to-many, resolved through the CardTag junction table. A card may have zero or more tags; a tag may be attached to zero or more cards.

## Candidate Events

The application does not model events as first-class records, but the following moments are implicit in the route logic:

- A user **studies** a card (no route; currently not tracked).
- A user **creates** or **deletes** a deck, card, or tag.
- A user **adds a tag to a card**.

Study sessions are a prominent omission — the entire point of a flashcard app is studying, yet nothing records when a card was reviewed or how it went.

## Business Rules (from route logic)

1. **Deck names must be unique.** The `decks` schema carries `UNIQUE` on `name`. The create and update routes do not catch the constraint violation explicitly, so a duplicate name produces an unhandled database error rather than a user-friendly message.

2. **Tag assignment is idempotent.** The `POST /cards/{card_id}/tags` route uses `INSERT … ON CONFLICT DO NOTHING`, so adding a tag a second time is silently ignored rather than an error.

3. **Cards must belong to a deck.** The `cards.deck_id` column is `NOT NULL REFERENCES decks(id)`, so orphan cards are prevented at the database level. No cascade behaviour is defined, which means deleting a deck that still has cards will fail with a foreign-key error.

4. **Tags are shared across all cards.** There is no ownership predicate on tags; every user (or, in a multi-user extension, every user) sees the same tag list and can attach any tag to any card.

## Open Questions

1. **Should tags be user-scoped?** Right now `tags` is a global table with no `user_id` column. One user's "python" tag is the same record as every other user's "python". This is almost certainly unintentional for a real product — in practice tags would need to be owned by the user who created them, or scoped to a deck.

2. **What happens when a deck is deleted?** No `ON DELETE CASCADE` is defined on `cards.deck_id`. Deleting a deck with cards produces a foreign-key violation. A real version would either cascade-delete the cards (and their card_tags rows) or refuse deletion while cards remain, surfacing a clear error.

3. **Who is allowed to do anything?** There is no authentication, no session, and no user concept anywhere in the schema or routes. Every operation is open. A real version would need at minimum a `users` table and a `user_id` foreign key on `decks`, and likely on `tags` as well.

4. **Can two decks share a name for different users?** The `UNIQUE` constraint on `decks.name` is global. Once a users table exists, uniqueness should be per-user — `(user_id, name)` — not global.

5. **Should study history be recorded?** The application routes suggest a flashcard study tool, but there is no mechanism for a user to mark a card as reviewed, record a difficulty rating, or schedule a next-review date. A real spaced-repetition tool would need a `study_events` or `reviews` entity.

6. **Can a card be edited?** There is a `GET /decks/{deck_id}/edit` route that enables deck editing and a card-detail view, but no `POST /cards/{card_id}/edit` route exists. Cards can be created and tagged but not updated or deleted individually.

## Likely Application Queries

**Already implemented:**

1. **All cards in a deck, ordered by id** — used in `GET /decks/{deck_id}` to populate the deck detail view.
   ```sql
   SELECT id, question, answer FROM cards WHERE deck_id = ? ORDER BY id;
   ```

2. **Tags on a card and available tags not yet on a card** — used together in `GET /cards/{card_id}` to show the tagging UI.
   ```sql
   -- Tags already on the card
   SELECT t.id, t.name FROM card_tags ct JOIN tags t ON t.id = ct.tag_id WHERE ct.card_id = ?;
   -- Tags not yet on the card
   SELECT t.id, t.name FROM tags t WHERE NOT EXISTS (SELECT 1 FROM card_tags ct WHERE ct.card_id = ? AND ct.tag_id = t.id);
   ```

**Not yet implemented:**

3. **All cards with a given tag** — a natural navigation path ("show me all cards tagged 'sql'") that the tag list and detail pages do not yet support.
   ```sql
   SELECT c.id, c.question, c.answer, d.name AS deck_name
   FROM card_tags ct
   JOIN cards c ON c.id = ct.card_id
   JOIN decks d ON d.id = c.deck_id
   WHERE ct.tag_id = ?
   ORDER BY d.name, c.id;
   ```

4. **Study session summary** — once study events are modelled, a query to fetch cards due for review, or to summarise how many cards in a deck have been studied at least once.

5. **Deck statistics** — card count per deck, useful for the deck list view.
   ```sql
   SELECT d.id, d.name, d.description, COUNT(c.id) AS card_count
   FROM decks d LEFT JOIN cards c ON c.deck_id = d.id
   GROUP BY d.id, d.name, d.description
   ORDER BY d.name;
   ```