
---

# `README.md`

# ProyectoFinalHenry_AIEngineering
Es repositorio del proyecto de Curso de AI Engineering

# LegalMove — Agente Autónomo de Comparación de Contratos

Sistema multi-agente para comparar un contrato original y una adenda a partir
de imágenes escaneadas.

El sistema utiliza:

- **GPT-4o Vision** para OCR multimodal.
- **LangChain** para implementar los agentes especializados.
- **Pydantic** para validar el resultado final.
- **Langfuse** para observabilidad, trazabilidad, latencia y monitoreo de LLM.
- **python-dotenv** para configuración segura mediante variables de entorno.

---

## Objetivo

LegalMove procesa miles de contratos y adendas mensualmente. El objetivo del
proyecto es reducir el esfuerzo manual del equipo de Compliance mediante un
pipeline que:

1. Reciba una imagen de un contrato original.
2. Reciba una imagen de una adenda o enmienda.
3. Extraiga el texto de ambos documentos utilizando visión artificial.
4. Construya contexto estructural entre los documentos.
5. Identifique los cambios introducidos por la adenda.
6. Devuelva un JSON validado y procesable por sistemas downstream.
7. Registre cada etapa del proceso en Langfuse.

---

## Arquitectura

```mermaid
flowchart TD
    A[Imagen contrato original] --> B[GPT-4o Vision OCR]
    C[Imagen adenda] --> D[GPT-4o Vision OCR]

    B --> E[Texto contrato original]
    D --> F[Texto adenda]

    E --> G[ContextualizationAgent]
    F --> G

    G --> H[Mapa contextual]

    E --> I[ExtractionAgent]
    F --> I
    H --> I

    I --> J[ContractChangeOutput]
    J --> K[Validación Pydantic]
    K --> L[JSON final]

    B -. Trazabilidad .-> M[Langfuse]
    D -. Trazabilidad .-> M
    G -. Trazabilidad .-> M
    I -. Trazabilidad .-> M
