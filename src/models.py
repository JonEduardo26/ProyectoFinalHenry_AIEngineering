from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ContractChangeOutput(BaseModel):
    """
    Schema final validado para los cambios detectados entre un contrato
    original y una adenda.

    Este modelo es utilizado como contrato de integración con sistemas
    downstream de LegalMove.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    sections_changed: List[str] = Field(
        default_factory=list,
        description=(
            "Lista de identificadores, nombres o números de cláusulas "
            "modificadas, eliminadas o agregadas por la adenda."
        ),
        examples=[
            [
                "Cláusula 2 - Precio",
                "Cláusula 3 - Vigencia",
                "Cláusula 5 - Protección de Datos",
            ]
        ],
    )

    topics_touched: List[str] = Field(
        default_factory=list,
        description=(
            "Lista de temas legales o comerciales afectados. "
            "Ejemplos: precio, vigencia, confidencialidad, responsabilidad, "
            "jurisdicción, protección de datos o terminación."
        ),
        examples=[
            [
                "precio",
                "vigencia",
                "protección de datos personales",
            ]
        ],
    )

    summary_of_the_change: str = Field(
        min_length=1,
        description=(
            "Resumen preciso y detallado de los cambios introducidos por la "
            "adenda. Debe distinguir claramente adiciones, eliminaciones y "
            "modificaciones cuando aplique."
        ),
        examples=[
            (
                "La adenda incrementa el precio mensual de USD 1.000 a "
                "USD 1.500, extiende la vigencia de doce a veinticuatro meses "
                "e incorpora una cláusula sobre protección de datos personales."
            )
        ],
    )
