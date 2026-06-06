import os
from collections import Counter
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carga variables de entorno desde .env
load_dotenv()

# Instancia principal de Flask
app = Flask(__name__)

# Conexión MySQL vía variables de entorno
DATABASE_URL = (
    f"mysql+pymysql://"
    f"{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

# Motor de conexión con pool y reciclado para evitar timeouts
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

# Mapa de prefijo de ámbito → nombre del organismo (None = sin nombre fijo)
ORGANISMS = {
    "ACC": None,
    "GEN": "Administración General del Estado",
    "TAS": "Ministerio de Trabajo y Economía Social",
    "SNC": "Sistema Nacional de Contratación",
    "JUR": "Administración de Justicia",
    "REG": None,
    "EXT": "Oficina de Extranjería",
    "DRG": None,
    "ORVE": "Oficina de Registro Virtual",
    "GEISER": "Sistema GEISER",
    "HABILITADOS": "Funcionarios Habilitados",
    "MNF": "Ministerio de Hacienda",
    "DEMO": None,
    "TGSS": "Tesorería General de la Seguridad Social",
}


def get_docs():
    """Devuelve todos los documentos de la BD."""
    with engine.connect() as conn:
        return list(conn.execute(text("SELECT * FROM documento")))


def get_stats(docs):
    """Calcula estadísticas: total y ámbito más frecuente."""
    if not docs:
        return None, 0
    ambito_counts = Counter(doc.ambito for doc in docs)
    top_ambito, top_count = ambito_counts.most_common(1)[0]
    return top_ambito, top_count


def render_table():
    """Renderiza el partial con la tabla de documentos y stats."""
    docs = get_docs()
    top_ambito, top_count = get_stats(docs)
    return render_template("partials/_datos.html", docs=docs, top_ambito=top_ambito, top_count=top_count)


@app.route("/")
def root():
    """Página principal carga inicial completa."""
    docs = get_docs()
    top_ambito, top_count = get_stats(docs)
    return render_template("index.html", docs=docs, top_ambito=top_ambito, top_count=top_count)


@app.route("/tabla")
def table():
    """HTMX: devuelve solo el partial con datos actualizados."""
    return render_table()


@app.route("/crear/")
def crear():
    """HTMX: modal con formulario vacío para nuevo documento."""
    return render_template("partials/_create_modal.html")


@app.route("/formulario", methods=["POST"])
def create():
    """HTMX: inserta un nuevo documento y devuelve la tabla actualizada."""
    # Extraer campos del formulario; cadena vacía → None
    ambito = request.form.get("ambito") or None
    codigo_verificacion = request.form.get("codigo_verificacion") or None
    fecha_hora = request.form.get("fecha_hora") or None
    expediente_numero_registro = request.form.get("expediente_numero_registro") or None
    direccion_validacion = request.form.get("direccion_validacion") or None

    # Insertar fila con el organismo resuelto desde el mapa
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO documento (ambito, codigo_verificacion, fecha_hora, expediente_numero_registro, direccion_validacion, organismo)
                VALUES (:ambito, :codigo_verificacion, :fecha_hora, :expediente_numero_registro, :direccion_validacion, :organismo)
            """),
            {
                "ambito": ambito,
                "codigo_verificacion": codigo_verificacion,
                "fecha_hora": fecha_hora,
                "expediente_numero_registro": expediente_numero_registro,
                "direccion_validacion": direccion_validacion,
                "organismo": ORGANISMS[ambito] if ambito else None
            }
        )
        conn.commit()

    return render_table()


@app.route("/editar/<id>/")
def update_modal(id):
    """HTMX: modal con formulario pre-poblado para editar un documento."""
    with engine.connect() as conn:
        doc = conn.execute(text("SELECT * FROM documento WHERE id = :id"), {"id": id}).fetchone()
    return render_template("partials/_update_modal.html", doc=doc)


@app.route("/actualizar/<int:id>/", methods=["PUT"])
def update(id):
    """HTMX: actualiza un documento existente y devuelve la tabla."""
    # Extraer campos; cadena vacía → None
    ambito = request.form.get("ambito") or None
    codigo_verificacion = request.form.get("codigo_verificacion") or None
    fecha_hora = request.form.get("fecha_hora") or None
    expediente_numero_registro = request.form.get("expediente_numero_registro") or None
    direccion_validacion = request.form.get("direccion_validacion") or None

    # Actualizar fila; engine.begin() hace commit automático
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE documento SET ambito = :ambito, codigo_verificacion = :codigo_verificacion, fecha_hora = :fecha_hora, expediente_numero_registro = :expediente_numero_registro, direccion_validacion = :direccion_validacion, organismo = :organismo WHERE id = :id"),
            {
                "id": id,
                "ambito": ambito,
                "codigo_verificacion": codigo_verificacion,
                "fecha_hora": fecha_hora,
                "expediente_numero_registro": expediente_numero_registro,
                "direccion_validacion": direccion_validacion,
                "organismo": ORGANISMS[ambito] if ambito else None
            }
        )

    return render_table()


@app.route("/eliminar/<id>/")
def delete_modal(id):
    """HTMX: modal de confirmación para eliminar un documento."""
    with engine.connect() as conn:
        doc = conn.execute(text("SELECT * FROM documento WHERE id = :id"), {"id": id}).fetchone()
    return render_template("partials/_delete_modal.html", doc=doc)


@app.route("/eliminar/<int:id>/", methods=["DELETE"])
def delete(id):
    """HTMX: elimina un documento y devuelve la tabla actualizada."""
    if request.method == "DELETE":
        # engine.begin() maneja commit/rollback automáticamente
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM documento WHERE id = :id"), {"id": id})
        return render_table()
    return render_table()


if __name__ == "__main__":
    app.run(debug=True)
