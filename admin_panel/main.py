"""
QSS Service Bot - Admin Panel
FastAPI application for managing bot data.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.engine import session_pool
from bot.db.models import Owner, Master, Admin, Ticket, BotText
from bot.utils.constants import (
    COMPLEX_DISPLAY, CATEGORY_DISPLAY, STATUS_DISPLAY,
    ResidentialComplex, TicketCategory, TicketStatus,
)
from admin_panel.auth import AuthMiddleware, create_session_token, SESSION_COOKIE, SESSION_MAX_AGE

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="QSS Панель управления", lifespan=lifespan)
app.add_middleware(AuthMiddleware)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


async def get_session():
    async with session_pool() as session:
        yield session


# Template context helpers
def get_display_mappings():
    return {
        "complex_display": COMPLEX_DISPLAY,
        "category_display": CATEGORY_DISPLAY,
        "status_display": STATUS_DISPLAY,
    }


# --- Auth ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.admin_login and password == settings.admin_password:
        token = create_session_token(username)
        response = RedirectResponse("/", status_code=302)
        response.set_cookie(
            SESSION_COOKIE, token,
            max_age=SESSION_MAX_AGE, httponly=True, samesite="lax",
        )
        return response

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Неверный логин или пароль",
    })


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


# --- Dashboard ---

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    # Stats
    total_tickets = await session.scalar(select(func.count(Ticket.id)))
    new_tickets = await session.scalar(
        select(func.count(Ticket.id)).where(Ticket.status == "new")
    )
    in_progress = await session.scalar(
        select(func.count(Ticket.id)).where(Ticket.status == "in_progress")
    )
    completed = await session.scalar(
        select(func.count(Ticket.id)).where(Ticket.status.in_(["completed", "closed"]))
    )
    total_owners = await session.scalar(select(func.count(Owner.id)))
    total_masters = await session.scalar(select(func.count(Master.id)))

    # Recent tickets
    recent_result = await session.execute(
        select(Ticket).order_by(desc(Ticket.created_at)).limit(10)
    )
    recent_tickets = recent_result.scalars().all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": {
            "total_tickets": total_tickets or 0,
            "new_tickets": new_tickets or 0,
            "in_progress": in_progress or 0,
            "completed": completed or 0,
            "total_owners": total_owners or 0,
            "total_masters": total_masters or 0,
        },
        "recent_tickets": recent_tickets,
        **get_display_mappings(),
    })


# --- Tickets ---

@app.get("/tickets", response_class=HTMLResponse)
async def tickets_list(
    request: Request,
    status: str = None,
    complex: str = None,
    page: int = 1,
    session: AsyncSession = Depends(get_session),
):
    per_page = 20
    offset = (page - 1) * per_page

    query = select(Ticket)
    count_query = select(func.count(Ticket.id))

    if status:
        query = query.where(Ticket.status == status)
        count_query = count_query.where(Ticket.status == status)
    if complex:
        query = query.where(Ticket.residential_complex == complex)
        count_query = count_query.where(Ticket.residential_complex == complex)

    query = query.order_by(desc(Ticket.created_at)).offset(offset).limit(per_page)

    total = await session.scalar(count_query)
    result = await session.execute(query)
    tickets = result.scalars().all()

    total_pages = (total + per_page - 1) // per_page if total else 1

    return templates.TemplateResponse("tickets.html", {
        "request": request,
        "tickets": tickets,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "filter_status": status,
        "filter_complex": complex,
        "statuses": [s.value for s in TicketStatus],
        "complexes": [c.value for c in ResidentialComplex],
        **get_display_mappings(),
    })


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(
    request: Request,
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
):
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return templates.TemplateResponse("ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        **get_display_mappings(),
    })


# --- Owners ---

@app.get("/owners", response_class=HTMLResponse)
async def owners_list(
    request: Request,
    page: int = 1,
    session: AsyncSession = Depends(get_session),
):
    per_page = 20
    offset = (page - 1) * per_page

    total = await session.scalar(select(func.count(Owner.id)))
    result = await session.execute(
        select(Owner).order_by(desc(Owner.created_at)).offset(offset).limit(per_page)
    )
    owners = result.scalars().all()

    total_pages = (total + per_page - 1) // per_page if total else 1

    return templates.TemplateResponse("owners.html", {
        "request": request,
        "owners": owners,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        **get_display_mappings(),
    })


@app.get("/owners/add", response_class=HTMLResponse)
async def owner_add_form(request: Request):
    return templates.TemplateResponse("owner_form.html", {
        "request": request,
        "owner": None,
        "complexes": [c.value for c in ResidentialComplex],
        **get_display_mappings(),
    })


@app.post("/owners/add")
async def owner_add(
    phone: str = Form(...),
    full_name: str = Form(...),
    residential_complex: str = Form(...),
    block: str = Form(None),
    entrance: str = Form(None),
    apartment: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    # Normalize phone
    phone = "".join(c for c in phone if c.isdigit())
    if phone.startswith("8") and len(phone) == 11:
        phone = "7" + phone[1:]

    # Normalize residential_complex (remove extra spaces)
    residential_complex = ",".join(c.strip() for c in residential_complex.split(",") if c.strip())

    owner = Owner(
        phone=phone,
        full_name=full_name,
        residential_complex=residential_complex,
        block=block or None,
        entrance=entrance or None,
        apartment=apartment,
    )
    session.add(owner)
    await session.commit()
    return RedirectResponse("/owners", status_code=303)


@app.get("/owners/{owner_id}/edit", response_class=HTMLResponse)
async def owner_edit_form(
    request: Request,
    owner_id: int,
    session: AsyncSession = Depends(get_session),
):
    owner = await session.get(Owner, owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    return templates.TemplateResponse("owner_form.html", {
        "request": request,
        "owner": owner,
        "complexes": [c.value for c in ResidentialComplex],
        **get_display_mappings(),
    })


@app.post("/owners/{owner_id}/edit")
async def owner_edit(
    owner_id: int,
    phone: str = Form(...),
    full_name: str = Form(...),
    residential_complex: str = Form(...),
    block: str = Form(None),
    entrance: str = Form(None),
    apartment: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    owner = await session.get(Owner, owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    phone = "".join(c for c in phone if c.isdigit())
    if phone.startswith("8") and len(phone) == 11:
        phone = "7" + phone[1:]

    # Normalize residential_complex (remove extra spaces)
    residential_complex = ",".join(c.strip() for c in residential_complex.split(",") if c.strip())

    owner.phone = phone
    owner.full_name = full_name
    owner.residential_complex = residential_complex
    owner.block = block or None
    owner.entrance = entrance or None
    owner.apartment = apartment
    await session.commit()
    return RedirectResponse("/owners", status_code=303)


@app.post("/owners/{owner_id}/delete")
async def owner_delete(
    owner_id: int,
    session: AsyncSession = Depends(get_session),
):
    owner = await session.get(Owner, owner_id)
    if owner:
        await session.delete(owner)
        await session.commit()
    return RedirectResponse("/owners", status_code=303)


# --- Masters ---

@app.get("/masters", response_class=HTMLResponse)
async def masters_list(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Master).order_by(Master.full_name))
    masters = result.scalars().all()

    return templates.TemplateResponse("masters.html", {
        "request": request,
        "masters": masters,
        **get_display_mappings(),
    })


@app.get("/masters/add", response_class=HTMLResponse)
async def master_add_form(request: Request):
    return templates.TemplateResponse("master_form.html", {
        "request": request,
        "master": None,
        "complexes": [c.value for c in ResidentialComplex],
        **get_display_mappings(),
    })


@app.post("/masters/add")
async def master_add(
    telegram_id: int = Form(...),
    full_name: str = Form(...),
    username: str = Form(None),
    residential_complex: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    master = Master(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username or None,
        residential_complex=residential_complex,
    )
    session.add(master)
    await session.commit()
    return RedirectResponse("/masters", status_code=303)


@app.get("/masters/{master_id}/edit", response_class=HTMLResponse)
async def master_edit_form(
    request: Request,
    master_id: int,
    session: AsyncSession = Depends(get_session),
):
    master = await session.get(Master, master_id)
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    return templates.TemplateResponse("master_form.html", {
        "request": request,
        "master": master,
        "complexes": [c.value for c in ResidentialComplex],
        **get_display_mappings(),
    })


@app.post("/masters/{master_id}/edit")
async def master_edit(
    master_id: int,
    telegram_id: int = Form(...),
    full_name: str = Form(...),
    username: str = Form(None),
    residential_complex: str = Form(...),
    is_active: bool = Form(False),
    session: AsyncSession = Depends(get_session),
):
    master = await session.get(Master, master_id)
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    master.telegram_id = telegram_id
    master.full_name = full_name
    master.username = username or None
    master.residential_complex = residential_complex
    master.is_active = is_active
    await session.commit()
    return RedirectResponse("/masters", status_code=303)


# --- Admins ---

@app.get("/admins", response_class=HTMLResponse)
async def admins_list(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Admin).order_by(Admin.full_name))
    admins = result.scalars().all()

    return templates.TemplateResponse("admins.html", {
        "request": request,
        "admins": admins,
    })


@app.post("/admins/add")
async def admin_add(
    telegram_id: int = Form(...),
    full_name: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    admin = Admin(telegram_id=telegram_id, full_name=full_name)
    session.add(admin)
    await session.commit()
    return RedirectResponse("/admins", status_code=303)


@app.post("/admins/{admin_id}/delete")
async def admin_delete(
    admin_id: int,
    session: AsyncSession = Depends(get_session),
):
    admin = await session.get(Admin, admin_id)
    if admin:
        await session.delete(admin)
        await session.commit()
    return RedirectResponse("/admins", status_code=303)


# --- Bot Texts ---

@app.get("/texts", response_class=HTMLResponse)
async def texts_list(
    request: Request,
    lang: str = "ru",
    session: AsyncSession = Depends(get_session),
):
    from bot.services.text_service import DEFAULT_TEXTS, TEXT_DESCRIPTIONS, seed_default_texts

    # Seed defaults if needed
    count = await seed_default_texts(session)
    if count:
        await session.commit()

    # Filter by language
    query = select(BotText).order_by(BotText.key)
    if lang in ("ru", "kk"):
        query = query.where(BotText.language == lang)
    result = await session.execute(query)
    texts = result.scalars().all()

    # Group texts by category
    categories = {
        "auth": ("Авторизация", []),
        "menu": ("Меню", []),
        "create": ("Создание заявки", []),
        "face_id": ("Face ID", []),
        "car_plate": ("Госномер", []),
        "camera": ("Доступ к камерам", []),
        "intercom": ("Домофон", []),
        "key": ("Ключи", []),
        "other": ("Прочее (категория)", []),
        "photo": ("Фото", []),
        "owner": ("Меню владельца", []),
        "rate": ("Оценка", []),
        "master": ("Мастер", []),
        "admin": ("Администратор", []),
        "notify": ("Уведомления", []),
        "btn": ("Кнопки", []),
        "misc": ("Разное", []),
    }

    for text in texts:
        placed = False
        for prefix, (_, items) in categories.items():
            if text.key.startswith(prefix):
                items.append(text)
                placed = True
                break
        if not placed:
            categories["misc"][1].append(text)

    # Filter empty categories
    categories = {k: v for k, v in categories.items() if v[1]}

    return templates.TemplateResponse("texts.html", {
        "request": request,
        "texts": texts,
        "categories": categories,
        "descriptions": TEXT_DESCRIPTIONS,
        "current_lang": lang,
    })


@app.get("/texts/{text_id}/edit", response_class=HTMLResponse)
async def text_edit_form(
    request: Request,
    text_id: int,
    session: AsyncSession = Depends(get_session),
):
    text = await session.get(BotText, text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")

    # Find the other language version
    other_lang = "kk" if text.language == "ru" else "ru"
    result = await session.execute(
        select(BotText).where(BotText.key == text.key, BotText.language == other_lang)
    )
    other_text = result.scalar_one_or_none()

    return templates.TemplateResponse("text_form.html", {
        "request": request,
        "text": text,
        "other_text": other_text,
    })


@app.post("/texts/{text_id}/edit")
async def text_edit(
    text_id: int,
    value: str = Form(...),
    value_other: str = Form(None),
    other_id: int = Form(None),
    session: AsyncSession = Depends(get_session),
):
    from bot.services.text_service import refresh_cache

    text = await session.get(BotText, text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")

    text.value = value

    # Update the other language version if provided
    if other_id and value_other is not None:
        other_text = await session.get(BotText, other_id)
        if other_text:
            other_text.value = value_other

    await session.commit()

    # Refresh cache so changes take effect immediately
    await refresh_cache(session)

    return RedirectResponse(f"/texts?lang={text.language}", status_code=303)


@app.post("/texts/add")
async def text_add(
    key: str = Form(...),
    value_ru: str = Form(...),
    value_kk: str = Form(""),
    description: str = Form(None),
    session: AsyncSession = Depends(get_session),
):
    from bot.services.text_service import refresh_cache

    text_ru = BotText(key=key, value=value_ru, language="ru", description=description)
    session.add(text_ru)
    if value_kk.strip():
        text_kk = BotText(key=key, value=value_kk, language="kk", description=description)
        session.add(text_kk)
    await session.commit()
    await refresh_cache(session)
    return RedirectResponse("/texts", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
