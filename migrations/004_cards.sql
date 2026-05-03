CREATE TABLE cards (
  id SERIAL PRIMARY KEY,
  deck_id INTEGER NOT NULL REFERENCES decks(id),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO cards (deck_id, question, answer)
VALUES
  (1, 'What does SQL stand for?', 'Structured Query Language'),
  (1, 'What is a primary key?', 'A unique identifier for a record in a database table.'),
  (2, 'What is Flask?', 'A micro web framework for Python.'),
  (2, 'What is a route in Flask?', 'A URL pattern that is associated with a view function that handles requests to that URL.');
