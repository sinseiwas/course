from pydantic import ValidationError

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import add_flash, get_current_user, require_role, template_context
from app.forms import format_validation_error
from app.models.user import User, UserRole
from app.response import wants_json
from app.schemas.book import BookCreate, BookRead, BookUpdate
from app.services import books as book_service
from app.templating import templates


router = APIRouter(prefix="/books", tags=["books"])


def _parse_book_form(
    title: str,
    author: str,
    year: int,
    category: str,
    description: str,
    total_copies: int,
    available_copies: int,
    schema_cls,
):
    return schema_cls(
        title=title,
        author=author,
        year=year,
        category=category,
        description=description,
        total_copies=total_copies,
        available_copies=available_copies,
    )


@router.get("")
def list_books(
    request: Request,
    title: str | None = None,
    author: str | None = None,
    category: str | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    books = db.scalars(book_service.build_book_query(title, author, category, year)).all()
    if wants_json(request):
        return [BookRead.model_validate(book) for book in books]
    return templates.TemplateResponse(
        request,
        "books.html",
        template_context(
            request,
            current_user,
            books=books,
            filters={"title": title or "", "author": author or "", "category": category or "", "year": year or ""},
        ),
    )


@router.get("/search")
def search_books(
    request: Request,
    title: str | None = None,
    author: str | None = None,
    category: str | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_books(request, title, author, category, year, db, current_user)


@router.get("/new")
def new_book_page(
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    return templates.TemplateResponse(
        request,
        "book_form.html",
        template_context(request, current_user, book=None, action="/books", submit_label="Добавить книгу"),
    )


@router.get("/{book_id}")
def get_book(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if wants_json(request):
        return BookRead.model_validate(book)
    return templates.TemplateResponse(request, "book_detail.html", template_context(request, current_user, book=book))


@router.post("")
def create_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    year: int = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    total_copies: int = Form(...),
    available_copies: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    try:
        payload = _parse_book_form(title, author, year, category, description, total_copies, available_copies, BookCreate)
    except ValidationError as exc:
        if wants_json(request):
            return JSONResponse({"detail": exc.errors()}, status_code=422)
        add_flash(request, "error", format_validation_error(exc))
        return RedirectResponse(url="/books/new", status_code=303)

    book = book_service.create_book(db, payload)
    if wants_json(request):
        return JSONResponse(BookRead.model_validate(book).model_dump(mode="json"), status_code=201)
    add_flash(request, "success", "Книга добавлена")
    return RedirectResponse(url=f"/books/{book.id}", status_code=303)


@router.get("/{book_id}/edit")
def edit_book_page(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse(
        request,
        "book_form.html",
        template_context(request, current_user, book=book, action=f"/books/{book.id}", submit_label="Сохранить"),
    )


@router.put("/{book_id}")
@router.post("/{book_id}")
def update_book(
    book_id: int,
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    year: int = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    total_copies: int = Form(...),
    available_copies: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    try:
        payload = _parse_book_form(title, author, year, category, description, total_copies, available_copies, BookUpdate)
    except ValidationError as exc:
        if wants_json(request):
            return JSONResponse({"detail": exc.errors()}, status_code=422)
        add_flash(request, "error", format_validation_error(exc))
        return RedirectResponse(url=f"/books/{book_id}/edit", status_code=303)

    updated = book_service.update_book(db, book, payload)
    if wants_json(request):
        return BookRead.model_validate(updated)
    add_flash(request, "success", "Книга обновлена")
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)


@router.delete("/{book_id}")
@router.post("/{book_id}/delete")
def delete_book(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book_service.delete_book(db, book)
    if wants_json(request):
        return {"message": "Book deleted"}
    add_flash(request, "success", "Книга удалена")
    return RedirectResponse(url="/books", status_code=303)
