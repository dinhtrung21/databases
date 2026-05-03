def fetch_all_decks(conn):
    return conn.execute(
        """
        SELECT id, name, description
        FROM decks
        ORDER BY name
        """
    ).fetchall()
    
    
def fetch_deck_by_id(conn, deck_id):
    return conn.execute(
        t"""
        SELECT id, name, description 
        FROM decks 
        WHERE id = {deck_id}
        """
    ).fetchone()


def fetch_newest_deck(conn):
    return conn.execute(
        """
        SELECT id, name, description
        FROM decks
        ORDER BY created_at DESC
        LIMIT 1
        """
    ).fetchone()


def create_deck_query(conn, name, description):
    conn.execute(
        t"""
        INSERT INTO decks (name, description)
        VALUES ({name}, {description})
        """
    )
    
    
def delete_deck_query(conn, deck_id):
    conn.execute(
        t"""
        DELETE FROM decks 
        WHERE id = {deck_id}
        """
    )


def update_deck_query(conn, deck_id, name, description):
    conn.execute(
        t"""
        UPDATE decks
        SET name = {name}, description = {description}
        WHERE id = {deck_id}
        """
    )