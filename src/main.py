import argparse
import json
import os
import sys
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from langfuse import get_client, observe
from langfuse.langchain import CallbackHandler
from pydantic import ValidationError

from src.agents.contextualization_agent import ContextualizationAgent
from src.agents.extraction_agent import ExtractionAgent
from src.image_parser import parse_contract_image
from src.models import ContractChangeOutput


def configure_environment() -> None:
    """
    Carga variables de entorno y valida credenciales mínimas.
    """
    load_dotenv()

    required_variables = [
        "OPENAI_API_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
    ]

    missing_variables = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing_variables:
        raise EnvironmentError(
            "Faltan variables de entorno requeridas: "
            + ", ".join(missing_variables)
        )


@observe(name="contract-analysis")
def run_contract_analysis(
    original_contract_image: str,
    amendment_contract_image: str,
) -> ContractChangeOutput:
    """
    Pipeline completo de comparación de contratos.

    Jerarquía esperada de observabilidad:

    contract-analysis
    ├── parse_contract_image (original_contract)
    ├── parse_contract_image (amendment_contract)
    ├── contextualization_agent
    └── extraction_agent
    """
    langfuse = get_client()
    langfuse_handler = CallbackHandler()

    total_start = perf_counter()

    langfuse.update_current_observation(
        input={
            "original_contract_image": original_contract_image,
            "amendment_contract_image": amendment_contract_image,
        },
        metadata={
            "pipeline": "legalmove_contract_comparison",
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "original_filename": Path(original_contract_image).name,
            "amendment_filename": Path(amendment_contract_image).name,
        },
    )

    original_contract_text = parse_contract_image(
        image_path=original_contract_image,
        document_role="original_contract",
        langfuse_handler=langfuse_handler,
    )

    amendment_contract_text = parse_contract_image(
        image_path=amendment_contract_image,
        document_role="amendment_contract",
        langfuse_handler=langfuse_handler,
    )

    contextualization_agent = ContextualizationAgent(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
        langfuse_handler=langfuse_handler,
    )

    context_map = contextualization_agent.run(
        original_contract_text=original_contract_text,
        amendment_contract_text=amendment_contract_text,
    )

    extraction_agent = ExtractionAgent(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
        langfuse_handler=langfuse_handler,
    )

    final_output = extraction_agent.run(
        original_contract_text=original_contract_text,
        amendment_contract_text=amendment_contract_text,
        context_map=context_map,
    )

    elapsed_ms = round((perf_counter() - total_start) * 1000, 2)

    langfuse.update_current_observation(
        output=final_output.model_dump(),
        metadata={
            "pipeline_status": "completed",
            "total_latency_ms": elapsed_ms,
            "validation": "ContractChangeOutput passed",
        },
    )

    langfuse.flush()

    return final_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "LegalMove - Agente autónomo de comparación de contratos "
            "originales y adendas."
        )
    )

    parser.add_argument(
        "--original",
        required=True,
        help="Path de la imagen PNG/JPEG del contrato original.",
    )

    parser.add_argument(
        "--amendment",
        required=True,
        help="Path de la imagen PNG/JPEG de la adenda o enmienda.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        configure_environment()

        result = run_contract_analysis(
            original_contract_image=args.original,
            amendment_contract_image=args.amendment,
        )

        print(json.dumps(
            result.model_dump(),
            ensure_ascii=False,
            indent=2,
        ))

    except FileNotFoundError as error:
        print(
            json.dumps(
                {
                    "error": "file_not_found",
                    "detail": str(error),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    except ValidationError as error:
        print(
            json.dumps(
                {
                    "error": "pydantic_validation_error",
                    "detail": error.errors(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as error:
        print(
            json.dumps(
                {
                    "error": "contract_analysis_failed",
                    "detail": str(error),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()