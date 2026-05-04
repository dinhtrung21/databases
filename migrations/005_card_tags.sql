CREATE TABLE card_tags (
  card_id INTEGER NOT NULL REFERENCES cards(id),
  tag_id INTEGER NOT NULL REFERENCES tags(id),
  PRIMARY KEY (card_id, tag_id)
);

INSERT INTO card_tags (card_id, tag_id)
VALUES
  (1, 1),
  (2, 1),
  (3, 2),
  (4, 2);