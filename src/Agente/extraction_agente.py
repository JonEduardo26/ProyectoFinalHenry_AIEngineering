from time import perf_counter

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langfuse import get_client, observe

from src.models import ContractChangeOutput


EXTRACTION_SYSTEM_PROMPT = """
Eres un segundo gente  un analista experto en comparación de contratos,
adendas y modificaciones legales.

Tu tarea exclusiva es identificar cambios introducidos por una adenda respecto
de un contrato original.

Dispones de:
1. Texto del contrato original.
2. Texto de la adenda.
3. Un mapa contextual construido por otro agente.

Debes detectar de manera precisa:
- Adiciones: cláusulas, obligaciones, derechos o condiciones nuevas.
- Eliminaciones: contenido del contrato original que queda eliminado,
  sustituido o sin efecto.
- Modificaciones: cambios de redacción, fechas, importes, duración,
  obligaciones, responsables, plazos u otras condiciones.

Reglas:
1. Usa solamente información presente en los documentos proporcionados.
2. No inventes números de cláusula o términos legales.
3. Si existe incertidumbre por texto ilegible, indícalo en el resumen.
4. sections_changed debe incluir números o nombres de cláusulas/secciones.
5. topics_touched debe incluir categorías claras, por ejemplo:
   pagos, precio, vigencia, renovación, confidencialidad,
   responsabilidad, terminación, jurisdicción, alcance de servicios,
   propiedad intelectual, protección de datos.
6. summary_of_the_change debe mencionar claramente qué cambió y cómo.
7. Devuelve únicamente una salida compatible con el schema solicitado.
"""


class ExtractionAgent:
    """
    Agente encargado de extraer y estructurar las diferencias contractuales.
    """

    def __init__(self, model_name: str = "gpt-4o", langfuse_handler=None):
        base_llm = ChatOpenAI(
            model=model_name,
            temperature=0,
        )

        self.llm = base_llm.with_structured_output(
            ContractChangeOutput,
            method="json_schema",
        )

        self.langfuse_handler = langfuse_handler

    @observe(name="extraction_agent")
    def run(
        self,
        original_contract_text: str,
        amendment_contract_text: str,
        context_map: str,
    ) -> ContractChangeOutput:
        langfuse = get_client()
        start_time = perf_counter()

        langfuse.update_current_observation(
            input={
                "original_contract_text": original_contract_text,
                "amendment_contract_text": amendment_contract_text,
                "context_map": context_map,
            },
            metadata={
                "agent": "ExtractionAgent",
                "purpose": "contract_change_extraction",
                "output_schema": "ContractChangeOutput",
            },
        )

        user_prompt = f"""
MAPA CONTEXTUAL
===============
{context_map}

CONTRATO ORIGINAL
=================
{original_contract_text}

ADENDA / ENMIENDA
=================
{amendment_contract_text}

Extrae las diferencias y devuelve el resultado estrictamente conforme
al schema ContractChangeOutput.
"""

        result = self.llm.invoke(
            [
                SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ],
            config={
                "callbacks": [self.langfuse_handler]
                if self.langfuse_handler
                else [],
                "run_name": "extraction_agent_llm",
            },
        )

        # Defensa adicional: si LangChain devolviera un dict en vez del modelo,
        # Pydantic lo normaliza y valida explícitamente.
        validated_result = ContractChangeOutput.model_validate(result)

        elapsed_ms = round((perf_counter() - start_time) * 1000, 2)

        langfuse.update_current_observation(
            output=validated_result.model_dump(),
            metadata={
                "latency_ms": elapsed_ms,
                "pydantic_validation": "passed",
            },
        )

        return validated_result