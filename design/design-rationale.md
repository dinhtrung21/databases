# Design Rationale: Flashcard Study Tracker

This document explains the design choices visible in the ER diagram. Every decision is attributed either to the existing code (a reconstruction of what the project already does) or to analysis (a proposal for what a real version would need). The two are distinguished in each section.

---

## Identifiers

**Decks — serial integer primary key** (existing). The schema uses `SERIAL PRIMARY KEY` on `decks.id`, and the application consistently routes to decks by integer id, e.g. `GET /decks/{deck_id}`. This is a reasonable choice for a teaching project: it is simple, supported natively by PostgreSQL, and requires no extra logic. A real version should keep it. The `name` column carries a `UNIQUE` constraint, which means names are effectively a natural key as well. That constraint should be retained but narrowed to `(user_id, name)` once a users table exists, so that two different users can each have a deck named "Python Basics" without colliding.

**Cards — serial integer primary key** (existing). Cards are identified by `cards.id`, a serial integer. Cards are always accessed through a known deck or a known card id. There is no natural key candidate on cards (two cards in different decks could have identical question text), so the surrogate key is the right choice for both the teaching and the production version.

**Tags — serial integer primary key** (existing). Tags use `tags.id`, a serial integer. The name is not constrained as unique in the schema, meaning two tags named "sql" could coexist. A real version would add a uniqueness constraint — at minimum `UNIQUE(name)` for the current global model, or `UNIQUE(user_id, name)` once tags are user-scoped. The current absence of this constraint is a silent assumption that the UI will prevent duplicates, which it does not.

**CardTag — composite primary key** (existing). The junction table uses `(card_id, tag_id)` as its primary key, which correctly prevents a card from being tagged twice with the same tag. The application reinforces this at the route level with `ON CONFLICT DO NOTHING`. This is the right design in both the teaching and the production version; a surrogate key on CardTag would add no value and would complicate queries.

**User — serial integer primary key** (proposed). A real version needs a `users` table. The natural candidates for a user identifier are a serial integer or a UUID. Either is defensible; a serial integer is simpler and consistent with the rest of the schema; a UUID is useful when user identifiers must be safe to expose in URLs or external APIs. For a teaching extension of this project, a serial integer is the pragmatic choice.

---

## The Many-to-Many Relationship

The relationship between cards and tags is many-to-many: a single card can carry several tags, and a single tag can appear on cards across many decks. The schema correctly resolves this into a junction table, `card_tags`, with a composite primary key on `(card_id, tag_id)`.

This structure is shown explicitly in the ER diagram rather than as a direct line between CARD and TAG, because the junction table is a first-class entity that must be maintained — rows must be inserted and deleted when tags are added or removed from a card. The application already implements the insertion path (`POST /cards/{card_id}/tags`) but has no route to remove a tag from a card. A real version would need `DELETE /cards/{card_id}/tags/{tag_id}`.

Currently `card_tags` carries no relationship attributes beyond the two foreign keys. If the application were extended to record when a tag was applied to a card, a `tagged_at TIMESTAMP` column would belong here, not on either the card or the tag.

---

## Privacy and Data Minimisation

The existing schema stores question text and answer text in plain, unencrypted columns with no access controls. For a personal study tool this is a low-risk choice. However, a real version deployed for multiple users would need to confront two issues.

First, **password storage**. The project has no authentication at all, so there is no password to mishandle. A real version must store only a salted hash of the user's password (e.g. bcrypt or argon2), never the plaintext or a reversible encoding. The `users` table in the ER diagram carries a `password_hash` column to signal this intent.

Second, **tag names as personal data**. Tag names typed by a user — "anxiety", "ADHD", "therapy homework" — may be sensitive. A real version should ensure that tags are visible only to their owner, which is enforced by the `user_id` foreign key proposed in the ER diagram and by filtering every tag query to `WHERE user_id = <current_user>`. The current global tag pool, where every tag is readable and writable by every session, would be unacceptable in a multi-user deployment.

---

## Decisions the Teaching Project Has Silently Skipped

**1. Introducing a users table.** The most consequential omission. Without a user concept, every deck, card, and tag is shared across all sessions. The project appears to assume single-user use, which is plausible for a local teaching tool but not for any hosted version. Introducing `users` requires adding `user_id` foreign keys to `decks` and `tags`, adjusting every query to filter by the authenticated user, adding uniqueness constraints that are currently global but should be per-user, and deciding how to handle cascades when a user account is deleted.

**2. Scoping tags per user.** The current `tags` table is global. This is almost certainly an oversight rather than a design decision — it means that if two students use the application, they share a single tag namespace and can see and modify each other's tags. A real version must add `user_id NOT NULL REFERENCES users(id)` to the `tags` table and ensure all tag queries are filtered accordingly. This also means the foreign key from `card_tags` to `tags` must be consistent with the ownership chain: a user should only be able to attach tags they own to cards they own.

**3. Adding audit timestamps consistently.** The `decks`, `cards`, and `tags` tables all have `created_at`. But no `updated_at` column exists on any table. A real version would add `updated_at` (maintained either by the application or by a database trigger) to all mutable entities. This matters for cache invalidation, audit logs, and "last edited" UI features.

**4. Handling card deletion and editing.** There is no route to delete or edit an individual card. The card detail page shows the question, answer, and tags, but the only mutation available is adding a tag. A real version would need `POST /cards/{card_id}/edit` and `POST /cards/{card_id}/delete`. The delete route would also need to remove the card's `card_tags` rows — either explicitly or via `ON DELETE CASCADE` on the foreign key.

---

## A Genuinely Open Question

**Should study history live on the card, or in a separate events table?**

A simple extension would add a `last_reviewed_at` timestamp and a `review_count` integer directly to the `cards` table. This is easy to implement and easy to query: "show me the card I reviewed least recently" is a single `ORDER BY last_reviewed_at ASC` query with no joins.

The counterargument is that this design throws away information. Storing only the most recent review and a total count makes it impossible to reconstruct when each review happened, what the user's self-assessed difficulty was, or how the card's performance has changed over time. Spaced-repetition algorithms (SM-2 and its variants) require the full review history, not just a count.

The ER diagram adopts the events-table approach (`STUDY_EVENT`), treating each review as a separate row with a timestamp, a card reference, a user reference, and a rating. This is the richer and more extensible model, but it comes at a cost: queries like "show me all cards due for review today" require joining across the events table, and the application must decide what to do when no events exist for a card yet (is it due immediately, or only after it has been seen at least once?). Both approaches are defensible, and the right choice depends on whether spaced repetition is a target feature or a future aspiration.