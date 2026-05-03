from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
# Internal imports
from .db import get_connection
from .queries.decks import (
    fetch_all_decks,
    fetch_deck_by_id,
    fetch_newest_deck,
    create_deck_query,
    delete_deck_query,
    update_deck_query
)
from .queries.tags import (
    fetch_all_tags,
    fetch_tag_by_id, 
    fetch_newest_tag, 
    create_tag_query, 
    delete_tag_query, 
    update_tag_query,
)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


# Helper function to render templates
def render(request: Request, template_name: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


# --- Decks routes ---
@app.get("/")
def index():
    return RedirectResponse("/decks", status_code=303)

@app.get("/decks")
def list_decks(request: Request):
    with get_connection() as conn:
        decks = fetch_all_decks(conn)
    return render(request, "decks.html", decks=decks)

@app.get("/decks/newest")
def newest_deck(request: Request):
    with get_connection() as conn:
        deck = fetch_newest_deck(conn)
    return render(request, "newest_deck.html", deck=deck)

@app.get("/decks/{deck_id}")
def show_deck(request: Request, deck_id: int):
    with get_connection() as conn:
        deck = conn.execute(t"""
            SELECT id, name, description
            FROM decks
            WHERE id = {deck_id}
            """).fetchone()
        if deck is None:
            return RedirectResponse("/decks", status_code=303)
        cards = conn.execute(t"""
            SELECT id, question, answer
            FROM cards
            WHERE deck_id = {deck_id}
            ORDER BY id
            """).fetchall()
    return render(request, "deck_detail.html", deck=deck, cards=cards)

@app.post("/decks")
def create_deck(name: str = Form(...), description: str = Form(...)):
    with get_connection() as conn:
        create_deck_query(conn, name, description)
    return RedirectResponse("/decks", status_code=303)

@app.post("/decks/{deck_id}/cards")
def create_card(
    deck_id: int,
    question: str = Form(...),
    answer: str = Form(...),
):
    with get_connection() as conn:
        conn.execute(t"""
            INSERT INTO cards (deck_id, question, answer)
            VALUES ({deck_id}, {question}, {answer})
            """)
    return RedirectResponse(f"/decks/{deck_id}", status_code=303)

@app.post("/decks/{deck_id}/delete")
def delete_deck(deck_id: int):
    with get_connection() as conn:
        delete_deck_query(conn, deck_id)
    return RedirectResponse("/decks", status_code=303)

@app.get("/decks/{deck_id}/edit")
def show_edit_deck(request: Request, deck_id: int):
    with get_connection() as conn:
        deck = fetch_deck_by_id(conn, deck_id)
    return render(request, "deck_edit.html", deck=deck)

@app.post("/decks/{deck_id}/edit")
def update_deck(deck_id: int, name: str = Form(...), description: str = Form(...)):
    with get_connection() as conn:
        update_deck_query(conn, deck_id, name, description)
    return RedirectResponse("/decks", status_code=303)


# --- Tags routes ---
@app.get("/tags")
def list_tags(request: Request):
    with get_connection() as conn:
        tags = fetch_all_tags(conn)
    return render(request, "tags.html", tags=tags)

@app.get("/tags/newest")
def newest_tag(request: Request):
    with get_connection() as conn:
        tag = fetch_newest_tag(conn)
    return render(request, "newest_tag.html", tag=tag)

@app.post("/tags")
def create_tag(name: str = Form(...)):
    with get_connection() as conn:
        create_tag_query(conn, name)
    return RedirectResponse("/tags", status_code=303)

@app.post("/tags/{tag_id}/delete")
def delete_tag(tag_id: int):
    with get_connection() as conn:
        delete_tag_query(conn, tag_id)
    return RedirectResponse("/tags", status_code=303)

@app.get("/tags/{tag_id}/edit")
def show_edit_tag(request: Request, tag_id: int):
    with get_connection() as conn:
        tag = fetch_tag_by_id(conn, tag_id)
    return render(request, "tag_edit.html", tag=tag)

@app.post("/tags/{tag_id}/edit")
def update_tag(tag_id: int, name: str = Form(...)):
    with get_connection() as conn:
        update_tag_query(conn, tag_id, name)
    return RedirectResponse("/tags", status_code=303)
