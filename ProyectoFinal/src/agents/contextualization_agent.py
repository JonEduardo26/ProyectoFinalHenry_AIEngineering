from time import perf_counter
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langfuse import get_client, observe


CONTEXTUALIZATION_SYSTEM_PROMPT = """
Eres un primer Agente, un analista legal especializado en estructura
de contratos, adendas, anexos y enmiendas.

Recibirás dos documentos:

1. El texto extraído de un contrato original.
2. El texto extraído de una adenda o enmienda contractual.

Tu responsabilidad exclusiva es construir un mapa contextual comparativo para
que otro agente pueda identificar los cambios concretos con precisión.

Debes identificar:

- Partes involucradas, cuando sean visibles.
- Naturaleza y propósito general del contrato original.
- Naturaleza y propósito general de la adenda.
- Secciones, cláusulas, títulos, artículos, anexos e incisos de ambos textos.
- Correspondencias entre cláusulas del contrato y referencias de la adenda.
- Cláusulas potencialmente nuevas incluidas por la adenda.
- Cláusulas que la adenda parece reemplazar o dejar sin efecto.
- Ambigüedades, referencias incompletas, texto ilegible o inconsistencias.

Formato sugerido:

1. Partes y documentos
2. Estructura del contrato original
3. Estructura de la adenda
4. Mapa de correspondencias
5. Observaciones y ambigüedades

Restricciones obligatorias:

- No generes el JSON final.
- No emitas asesoramiento jurídico.
- No determines conclusiones legales definitivas.
- No clasifiques formalmente cambios como adición, eliminación o modificación.
- No inventes cláusulas, datos o referencias inexistentes.
"""


class ContextualizationAgent:
    """
    Agente responsable de generar un mapa estructural y contextual entre
    el contrato base y su adenda.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        langfuse_handler: Optional[object] = None,
    ) -> None:
        self.model_name = model_name
        self.langfuse_handler = langfuse_handler
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
        )

    @observe(name="contextualization_agent")
    def run(
        self,
        original_contract_text: str,
        amendment_contract_text: str,
    ) -> str:
        """
        Construye el contexto documental comparado.

        Args:
            original_contract_text: OCR del contrato original.
            amendment_contract_text: OCR de la adenda.

        Returns:
            Mapa contextual estructurado como texto.
        """
        langfuse = get_client()
        start_time = perf_counter()

        langfuse.update_current_observation(
            input={
                "original_contract_text": original_contract_text,
                "amendment_contract_text": amendment_contract_text,
            },
            metadata={
                "agent": "ContextualizationAgent",
                "purpose": "contract_structure_mapping",
                "model": self.model_name,
            },
        )

        user_prompt = f"""
CONTRATO ORIGINAL
=================
{original_contract_text}

ADENDA / ENMIENDA
=================
{amendment_contract_text}

Construye el mapa contextual comparativo solicitado.
"""

        response = self.llm.invoke(
            [
                SystemMessage(content=CONTEXTUALIZATION_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ],
            config={
                "run_name": "contextualization_agent_llm",
                "callbacks": (
                    [self.langfuse_handler]
                    if self.langfuse_handler
                    else []
                ),
            },
        )

        context_map = response.content

        if not isinstance(context_map, str) or not context_map.strip():
            raise ValueError(
                "ContextualizationAgent no devolvió un mapa contextual válido."
            )

        elapsed_ms = round((perf_counter() - start_time) * 1000, 2)

        langfuse.update_current_observation(
            output={
                "context_map": context_map,
                "characters_generated": len(context_map),
            },
            metadata={
                "latency_ms": elapsed_ms,
                "status": "completed",
            },
        )

        return context_map