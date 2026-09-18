import base64
import hashlib
import mimetypes
from pathlib import Path
from time import perf_counter
from typing import Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langfuse import get_client, observe
from PIL import Image, UnidentifiedImageError


SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
}

VISION_SYSTEM_PROMPT = """
Eres un sistema de OCR jurídico de alta precisión para LegalMove.

Tu tarea es transcribir una imagen escaneada de un contrato, adenda o enmienda
legal. La transcripción será usada posteriormente por agentes de análisis legal,
por lo que debes preservar la máxima fidelidad posible.

Reglas obligatorias:

1. Extrae todo el texto visible de la imagen.
2. Conserva títulos, encabezados, nombres de partes, fechas, montos, monedas,
   numeración de cláusulas, incisos y referencias cruzadas.
3. Mantén los saltos de línea y estructura del documento.
4. No resumas, no expliques, no interpretes y no compares.
5. No inventes texto que no sea legible en la imagen.
6. Si una palabra, fecha, importe o sección no puede leerse, utiliza
   exactamente el marcador: [TEXTO ILEGIBLE].
7. Si aparecen tablas, represéntalas en texto de la forma más fiel posible.
8. No agregues introducciones como "Aquí está la transcripción".
9. Devuelve exclusivamente la transcripción del documento.
"""


def validate_image_path(image_path: str) -> Path:
    """
    Valida que el archivo exista, sea un archivo regular y corresponda a
    una imagen PNG/JPEG legible.

    Args:
        image_path: Ruta de la imagen de contrato.

    Returns:
        Path validado.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el formato no está soportado o la imagen es inválida.
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"No existe el archivo de imagen indicado: {image_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"La ruta indicada no corresponde a un archivo: {image_path}"
        )

    mime_type, _ = mimetypes.guess_type(path.name)

    if mime_type not in SUPPORTED_MIME_TYPES:
        raise ValueError(
            "Formato de imagen no soportado. "
            "Solo se aceptan archivos PNG, JPG o JPEG. "
            f"Formato detectado: {mime_type}"
        )

    try:
        with Image.open(path) as image:
            image.verify()
    except UnidentifiedImageError as error:
        raise ValueError(
            f"El archivo no contiene una imagen válida: {image_path}"
        ) from error
    except OSError as error:
        raise ValueError(
            f"No fue posible validar la imagen: {image_path}"
        ) from error

    return path


def encode_image_to_data_url(image_path: str) -> Tuple[str, str]:
    """
    Codifica una imagen local como data URL Base64 para su envío a GPT-4o.

    No se recomienda registrar el Base64 en Langfuse, ya que puede ser grande
    y contener información sensible. En su lugar, el pipeline registra el hash
    SHA-256 de la imagen.

    Args:
        image_path: Ruta local de la imagen.

    Returns:
        Tupla con:
        - data_url: URL data:image/...;base64,... compatible con GPT-4o.
        - image_sha256: Hash SHA-256 del archivo para auditoría.
    """
    path = validate_image_path(image_path)

    mime_type, _ = mimetypes.guess_type(path.name)
    image_bytes = path.read_bytes()

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    image_sha256 = hashlib.sha256(image_bytes).hexdigest()

    data_url = f"data:{mime_type};base64,{encoded_image}"

    return data_url, image_sha256


@observe(name="parse_contract_image")
def parse_contract_image(
    image_path: str,
    document_role: str,
    model_name: str = "gpt-4o",
    langfuse_handler: Optional[object] = None,
) -> str:
    """
    Ejecuta OCR multimodal de una imagen contractual usando GPT-4o Vision.

    Args:
        image_path: Ruta local a una imagen PNG/JPEG.
        document_role: Rol funcional del documento. Ejemplos:
            - original_contract
            - amendment_contract
        model_name: Modelo multimodal de OpenAI.
        langfuse_handler: Callback de Langfuse para instrumentar llamadas
            realizadas mediante LangChain.

    Returns:
        Texto completo extraído del documento.
    """
    langfuse = get_client()
    start_time = perf_counter()

    image_data_url, image_sha256 = encode_image_to_data_url(image_path)

    langfuse.update_current_observation(
        input={
            "document_role": document_role,
            "image_path": image_path,
            "image_sha256": image_sha256,
        },
        metadata={
            "operation": "multimodal_contract_ocr",
            "document_role": document_role,
            "model": model_name,
            "image_sha256": image_sha256,
        },
    )

    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
    )

    messages = [
        SystemMessage(content=VISION_SYSTEM_PROMPT),
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        f"Documento a procesar: {document_role}. "
                        "Realiza la transcripción completa."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url,
                        "detail": "high",
                    },
                },
            ],
        ),
    ]

    response = llm.invoke(
        messages,
        config={
            "run_name": f"vision_ocr_{document_role}",
            "callbacks": [langfuse_handler] if langfuse_handler else [],
        },
    )

    parsed_text = response.content

    if not isinstance(parsed_text, str) or not parsed_text.strip():
        raise ValueError(
            f"GPT-4o no devolvió texto válido para el documento: {document_role}"
        )

    elapsed_ms = round((perf_counter() - start_time) * 1000, 2)

    langfuse.update_current_observation(
        output={
            "parsed_text": parsed_text,
            "characters_extracted": len(parsed_text),
        },
        metadata={
            "latency_ms": elapsed_ms,
            "status": "completed",
        },
    )

    return parsed_text