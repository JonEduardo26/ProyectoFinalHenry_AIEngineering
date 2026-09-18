"""
Genera cuatro imágenes PNG sintéticas para probar el pipeline.

Los documentos son ficticios y no representan contratos reales.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = Path("data/test_contracts")

IMAGE_WIDTH = 1600
IMAGE_HEIGHT = 2200
MARGIN_X = 100
MARGIN_Y = 100
TITLE_SIZE = 42
BODY_SIZE = 27
LINE_HEIGHT = 45


def load_font(size: int):
    """
    Intenta utilizar una fuente TrueType común.
    Si no está disponible, usa la fuente por defecto de Pillow.
    """
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]

    for candidate in font_candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)

    return ImageFont.load_default()


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    max_width: int,
) -> list[str]:
    """
    Divide un texto en líneas según el ancho máximo permitido.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        candidate_line = f"{current_line} {word}".strip()
        bounding_box = draw.textbbox((0, 0), candidate_line, font=font)
        candidate_width = bounding_box[2] - bounding_box[0]

        if candidate_width <= max_width:
            current_line = candidate_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def create_contract_image(
    filename: str,
    document_title: str,
    content: str,
) -> None:
    """
    Crea una imagen PNG con apariencia de documento contractual escaneado.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image = Image.new(
        "RGB",
        (IMAGE_WIDTH, IMAGE_HEIGHT),
        color="white",
    )

    draw = ImageDraw.Draw(image)

    title_font = load_font(TITLE_SIZE)
    body_font = load_font(BODY_SIZE)

    available_width = IMAGE_WIDTH - (MARGIN_X * 2)
    current_y = MARGIN_Y

    draw.text(
        (MARGIN_X, current_y),
        document_title,
        fill="black",
        font=title_font,
    )

    current_y += 100

    for paragraph in content.split("\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            current_y += 25
            continue

        for line in wrap_text(
            draw=draw,
            text=paragraph,
            font=body_font,
            max_width=available_width,
        ):
            draw.text(
                (MARGIN_X, current_y),
                line,
                fill="black",
                font=body_font,
            )
            current_y += LINE_HEIGHT

        current_y += 20

    output_path = OUTPUT_DIR / filename
    image.save(output_path, "PNG")

    print(f"Imagen creada: {output_path}")


def main() -> None:
    """
    Genera dos pares de contrato/adenda con cambios conocidos.
    """

    original_contract_1 = """
CONTRATO DE PRESTACIÓN DE SERVICIOS

Entre LegalMove S.A., con domicilio en Ciudad de Buenos Aires, en adelante
"EL PRESTADOR", y Cliente Demo S.R.L., en adelante "EL CLIENTE", se celebra
el presente Contrato de Prestación de Servicios.

CLÁUSULA 1 - OBJETO
EL PRESTADOR brindará a EL CLIENTE servicios de análisis documental
automatizado y gestión de contratos mediante una plataforma tecnológica.

CLÁUSULA 2 - PRECIO
EL CLIENTE abonará a EL PRESTADOR la suma de USD 1.000 mensuales, más los
impuestos aplicables.

CLÁUSULA 3 - VIGENCIA
El presente contrato tendrá una vigencia de doce (12) meses contados desde
el 1 de enero de 2026.

CLÁUSULA 4 - CONFIDENCIALIDAD
Las partes se obligan a mantener confidencial toda información comercial,
técnica, financiera o legal intercambiada durante la relación contractual.
"""

    amendment_contract_1 = """
PRIMERA ADENDA AL CONTRATO DE PRESTACIÓN DE SERVICIOS

Entre LegalMove S.A. y Cliente Demo S.R.L., las partes acuerdan celebrar la
presente Primera Adenda al Contrato de Prestación de Servicios celebrado el
1 de enero de 2026.

PRIMERO - MODIFICACIÓN DE PRECIO
Se reemplaza íntegramente la CLÁUSULA 2 - PRECIO del contrato original por
la siguiente:

"EL CLIENTE abonará a EL PRESTADOR la suma de USD 1.500 mensuales, más los
impuestos aplicables, a partir del 1 de julio de 2026."

SEGUNDO - MODIFICACIÓN DE VIGENCIA
Se reemplaza íntegramente la CLÁUSULA 3 - VIGENCIA del contrato original por
la siguiente:

"El presente contrato tendrá una vigencia de veinticuatro (24) meses contados
desde el 1 de enero de 2026."

TERCERO - NUEVA CLÁUSULA
Se incorpora la CLÁUSULA 5 - PROTECCIÓN DE DATOS:

"Las partes se comprometen a cumplir con toda normativa aplicable en materia
de protección de datos personales y seguridad de la información."
"""

    original_contract_2 = """
CONTRATO DE LICENCIA DE SOFTWARE

Entre LegalMove S.A., en adelante "EL LICENCIANTE", y Empresa Ejemplo S.A.,
en adelante "EL LICENCIATARIO", se celebra el presente Contrato de Licencia
de Software.

CLÁUSULA 1 - LICENCIA
EL LICENCIANTE otorga a EL LICENCIATARIO una licencia no exclusiva,
intransferible y revocable para utilizar la plataforma LegalMove.

CLÁUSULA 2 - SOPORTE TÉCNICO
EL LICENCIANTE brindará soporte técnico de lunes a viernes, entre las
09:00 y las 18:00 horas, excluyendo feriados nacionales.

CLÁUSULA 3 - RESPONSABILIDAD
La responsabilidad total de EL LICENCIANTE se limitará a los importes abonados
por EL LICENCIATARIO durante los últimos tres (3) meses anteriores al hecho
que origine el reclamo.

CLÁUSULA 4 - JURISDICCIÓN
Las partes se someten a la jurisdicción de los tribunales ordinarios de la
Ciudad Autónoma de Buenos Aires.
"""

    amendment_contract_2 = """
SEGUNDA ADENDA AL CONTRATO DE LICENCIA DE SOFTWARE

Las partes acuerdan modificar el Contrato de Licencia de Software conforme a
las siguientes disposiciones.

PRIMERO - SOPORTE TÉCNICO
Se modifica la CLÁUSULA 2 - SOPORTE TÉCNICO, la cual quedará redactada de la
siguiente manera:

"EL LICENCIANTE brindará soporte técnico todos los días hábiles, entre las
08:00 y las 20:00 horas, excluyendo feriados nacionales."

SEGUNDO - RESPONSABILIDAD
Se reemplaza la CLÁUSULA 3 - RESPONSABILIDAD por la siguiente:

"La responsabilidad total de EL LICENCIANTE se limitará a los importes abonados
por EL LICENCIATARIO durante los últimos doce (12) meses anteriores al hecho
que origine el reclamo."

TERCERO - ELIMINACIÓN DE JURISDICCIÓN
Se deja sin efecto la CLÁUSULA 4 - JURISDICCIÓN del contrato original.

CUARTO - MEDIACIÓN
Se incorpora la CLÁUSULA 5 - MEDIACIÓN:

"Ante cualquier controversia derivada del contrato, las partes deberán intentar
una instancia de mediación privada antes de iniciar acciones judiciales."
"""

    create_contract_image(
        filename="original_contract_1.png",
        document_title="CONTRATO ORIGINAL - CASO DE PRUEBA 1",
        content=original_contract_1,
    )

    create_contract_image(
        filename="amendment_contract_1.png",
        document_title="ADENDA - CASO DE PRUEBA 1",
        content=amendment_contract_1,
    )

    create_contract_image(
        filename="original_contract_2.png",
        document_title="CONTRATO ORIGINAL - CASO DE PRUEBA 2",
        content=original_contract_2,
    )

    create_contract_image(
        filename="amendment_contract_2.png",
        document_title="ADENDA - CASO DE PRUEBA 2",
        content=amendment_contract_2,
    )


if __name__ == "__main__":
    main()
    