# app/main.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import mysql.connector

from app.database import get_connection  # si tu database.py está dentro de app/

app = FastAPI(title="GameInventory")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ---------- DB helpers ----------
def fetch_all_juegos(only_activos: bool = True) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if only_activos:
        cur.execute("""
            SELECT id, codigo, titulo, plataforma, genero, precio, stock, estado
            FROM juego
            WHERE estado = 1
            ORDER BY id DESC
        """)
    else:
        cur.execute("""
            SELECT id, codigo, titulo, plataforma, genero, precio, stock, estado
            FROM juego
            ORDER BY id DESC
        """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fetch_inactivos() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, codigo, titulo, plataforma, genero, precio, stock, estado
        FROM juego
        WHERE estado = 0
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fetch_juego_by_id(juego_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, codigo, titulo, plataforma, genero, precio, stock, estado
        FROM juego
        WHERE id = %s
    """, (juego_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def insert_juego(codigo, titulo, plataforma, genero, precio, stock, estado) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO juego (codigo, titulo, plataforma, genero, precio, stock, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (codigo, titulo, plataforma, genero, precio, stock, estado))
    conn.commit()
    cur.close()
    conn.close()


def update_juego(juego_id: int, codigo, titulo, plataforma, genero, precio, stock, estado) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE juego
        SET codigo=%s, titulo=%s, plataforma=%s, genero=%s, precio=%s, stock=%s, estado=%s
        WHERE id=%s
    """, (codigo, titulo, plataforma, genero, precio, stock, estado, juego_id))
    conn.commit()
    cur.close()
    conn.close()


def soft_delete_juego(juego_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE juego SET estado = 0 WHERE id = %s", (juego_id,))
    conn.commit()
    cur.close()
    conn.close()


# ---------- RUTAS ----------

# LISTADO (solo activos)
@app.get("/", response_class=HTMLResponse)
def get_index(request: Request):
    juegos = fetch_all_juegos(only_activos=True)
    return templates.TemplateResponse(
        "pages/index.html",
        {"request": request, "juegos": juegos, "vista": "activos"}
    )


# LISTADO INACTIVOS (para recuperar los “desaparecidos”)
@app.get("/juegos/inactivos", response_class=HTMLResponse)
def get_inactivos(request: Request):
    juegos = fetch_inactivos()
    return templates.TemplateResponse(
        "pages/index.html",
        {"request": request, "juegos": juegos, "vista": "inactivos"}
    )


# (Opcional) LISTADO TODOS
@app.get("/juegos/todos", response_class=HTMLResponse)
def get_todos(request: Request):
    juegos = fetch_all_juegos(only_activos=False)
    return templates.TemplateResponse(
        "pages/index.html",
        {"request": request, "juegos": juegos, "vista": "todos"}
    )


# FORM NUEVO
@app.get("/juegos/nuevo", response_class=HTMLResponse)
def get_juego_nuevo(request: Request):
    return templates.TemplateResponse(
        "pages/juego_form.html",
        {"request": request, "modo": "nuevo", "juego": None, "error": None}
    )


# CREAR
@app.post("/juegos/nuevo", response_class=HTMLResponse)
def post_juego_nuevo(
    request: Request,
    codigo: Optional[str] = Form(None),
    titulo: str = Form(...),
    plataforma: str = Form(...),
    genero: Optional[str] = Form(None),
    precio: float = Form(0.0),
    stock: int = Form(0),
    estado: int = Form(1),
):
    titulo = titulo.strip()
    plataforma = plataforma.strip()
    codigo = (codigo.strip() if codigo else None)
    genero = (genero.strip() if genero else None)

    if not titulo or not plataforma:
        return templates.TemplateResponse(
            "pages/juego_form.html",
            {
                "request": request,
                "modo": "nuevo",
                "juego": {"codigo": codigo, "titulo": titulo, "plataforma": plataforma, "genero": genero, "precio": precio, "stock": stock, "estado": estado},
                "error": "Título y plataforma son obligatorios."
            },
            status_code=400
        )

    if precio < 0 or stock < 0 or estado not in (0, 1):
        return templates.TemplateResponse(
            "pages/juego_form.html",
            {
                "request": request,
                "modo": "nuevo",
                "juego": {"codigo": codigo, "titulo": titulo, "plataforma": plataforma, "genero": genero, "precio": precio, "stock": stock, "estado": estado},
                "error": "Datos inválidos: precio/stock no pueden ser negativos; estado debe ser 0 o 1."
            },
            status_code=400
        )

    try:
        insert_juego(codigo, titulo, plataforma, genero, precio, stock, estado)
    except mysql.connector.Error as e:
        msg = str(e)
        if "Duplicate entry" in msg and "codigo" in msg:
            msg = "Ese código (SKU) ya existe. Usa otro distinto o déjalo vacío."
        return templates.TemplateResponse(
            "pages/juego_form.html",
            {
                "request": request,
                "modo": "nuevo",
                "juego": {"codigo": codigo, "titulo": titulo, "plataforma": plataforma, "genero": genero, "precio": precio, "stock": stock, "estado": estado},
                "error": f"Error al guardar: {msg}"
            },
            status_code=400
        )

    return RedirectResponse(url="/", status_code=303)


# FORM EDITAR
@app.get("/juegos/editar/{juego_id}", response_class=HTMLResponse)
def get_juego_editar(request: Request, juego_id: int):
    juego = fetch_juego_by_id(juego_id)
    if not juego:
        raise HTTPException(status_code=404, detail="Juego no encontrado")

    return templates.TemplateResponse(
        "pages/juego_form.html",
        {"request": request, "modo": "editar", "juego": juego, "error": None}
    )


# ACTUALIZAR
@app.post("/juegos/editar/{juego_id}", response_class=HTMLResponse)
def post_juego_editar(
    request: Request,
    juego_id: int,
    codigo: Optional[str] = Form(None),
    titulo: str = Form(...),
    plataforma: str = Form(...),
    genero: Optional[str] = Form(None),
    precio: float = Form(0.0),
    stock: int = Form(0),
    estado: int = Form(1),
):
    juego = fetch_juego_by_id(juego_id)
    if not juego:
        raise HTTPException(status_code=404, detail="Juego no encontrado")

    titulo = titulo.strip()
    plataforma = plataforma.strip()
    codigo = (codigo.strip() if codigo else None)
    genero = (genero.strip() if genero else None)

    if not titulo or not plataforma:
        return templates.TemplateResponse(
            "pages/juego_form.html",
            {
                "request": request,
                "modo": "editar",
                "juego": {**juego, "codigo": codigo, "titulo": titulo, "plataforma": plataforma, "genero": genero, "precio": precio, "stock": stock, "estado": estado},
                "error": "Título y plataforma son obligatorios."
            },
            status_code=400
        )

    if precio < 0 or stock < 0 or estado not in (0, 1):
        return templates.TemplateResponse(
            "pages/juego_form.html",
            {
                "request": request,
                "modo": "editar",
                "juego": {**juego, "codigo": codigo, "titulo": titulo, "plataforma": plataforma, "genero": genero, "precio": precio, "stock": stock, "estado": estado},
                "error": "Datos inválidos: precio/stock no pueden ser negativos; estado debe ser 0 o 1."
            },
            status_code=400
        )

    try:
        update_juego(juego_id, codigo, titulo, plataforma, genero, precio, stock, estado)
    except mysql.connector.Error as e:
        msg = str(e)
        if "Duplicate entry" in msg and "codigo" in msg:
            msg = "Ese código (SKU) ya existe. Usa otro distinto o déjalo vacío."
        return templates.TemplateResponse(
            "pages/juego_form.html",
            {
                "request": request,
                "modo": "editar",
                "juego": {**juego, "codigo": codigo, "titulo": titulo, "plataforma": plataforma, "genero": genero, "precio": precio, "stock": stock, "estado": estado},
                "error": f"Error al actualizar: {msg}"
            },
            status_code=400
        )

    return RedirectResponse(url="/", status_code=303)


# DELETE LÓGICO (modal)
@app.delete("/juegos/{juego_id}")
def delete_juego(juego_id: int):
    juego = fetch_juego_by_id(juego_id)
    if not juego:
        return JSONResponse({"ok": False, "error": "Juego no encontrado"}, status_code=404)

    soft_delete_juego(juego_id)
    return JSONResponse({"ok": True})


# TOGGLE estado (activar/desactivar)
@app.patch("/juegos/{juego_id}/toggle")
def toggle_estado(juego_id: int):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT estado FROM juego WHERE id = %s", (juego_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return JSONResponse({"ok": False, "error": "Juego no encontrado"}, status_code=404)

    nuevo_estado = 0 if int(row["estado"]) == 1 else 1

    cur2 = conn.cursor()
    cur2.execute("UPDATE juego SET estado = %s WHERE id = %s", (nuevo_estado, juego_id))
    conn.commit()

    cur2.close()
    cur.close()
    conn.close()
    return JSONResponse({"ok": True, "estado": nuevo_estado})