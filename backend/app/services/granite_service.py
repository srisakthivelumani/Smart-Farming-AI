"""
IBM Granite Service — the ONLY module that communicates with IBM watsonx.ai.

Design rules enforced here:
  1. Credentials are read exclusively from Settings (environment variables).
  2. If Granite is unavailable or misconfigured, a GraniteUnavailableError or
     GraniteNotConfiguredError is raised with the exact IBM error preserved.
  3. This module NEVER falls back to another LLM or provider.
  4. Token usage (input + output) is logged on every inference call so the
     IBM Cloud Lite monthly budget (300,000 tokens) can be monitored.
  5. A dedicated test_connection() method performs a minimal real inference
     request to verify actual accessibility — not just a credential check.
  6. A test_tamil_generation() method probes Tamil output quality without
     claiming official Tamil support from Granite 4 H Small.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.core.config import Settings
from app.core.exceptions import GraniteNotConfiguredError, GraniteUnavailableError

logger = logging.getLogger(__name__)


# ── Response dataclass ────────────────────────────────────────────────────────

@dataclass
class GraniteResponse:
    """Structured wrapper around a single Granite inference result."""
    generated_text: str
    model_id: str
    input_token_count: int = 0
    output_token_count: int = 0
    stop_reason: str = ""
    latency_seconds: float = 0.0
    raw_response: dict = field(default_factory=dict)


# ── Connection test result ────────────────────────────────────────────────────

@dataclass
class ConnectionTestResult:
    success: bool
    model_id: str
    endpoint: str
    project_id_configured: bool
    api_key_configured: bool
    # Populated on success
    sample_response: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0
    # Populated on failure — always the raw IBM error, never hidden
    ibm_error_type: str = ""
    ibm_error_message: str = ""
    # Tamil generation probe
    tamil_test_attempted: bool = False
    tamil_test_response: str = ""
    tamil_test_note: str = ""


# ── Service ───────────────────────────────────────────────────────────────────

class GraniteService:
    """
    Thin, dedicated wrapper around ibm-watsonx-ai ModelInference.
    One instance is shared across the application via dependency injection.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = None   # lazy-initialised on first use
        self._client = None

    # ── Initialisation ────────────────────────────────────────────────────────

    def _ensure_model(self) -> None:
        """
        Lazily initialise the IBM SDK client and ModelInference.
        Raises GraniteNotConfiguredError if credentials are absent.
        Raises GraniteUnavailableError if the SDK raises during setup.
        """
        if self._model is not None:
            return

        s = self._settings
        if not s.granite_is_configured:
            raise GraniteNotConfiguredError(
                "IBM Granite is not configured. "
                "Set WATSONX_API_KEY and WATSONX_PROJECT_ID in your .env file."
            )

        try:
            # Import here so missing SDK gives a clear InstallError, not ImportError
            from ibm_watsonx_ai import APIClient, Credentials  # type: ignore[import]
            from ibm_watsonx_ai.foundation_models import ModelInference  # type: ignore[import]

            credentials = Credentials(
                url=s.watsonx_url,
                api_key=s.watsonx_api_key,   # read from env, never hardcoded
            )
            self._client = APIClient(credentials)
            self._model = ModelInference(
                model_id=s.granite_model_id,
                api_client=self._client,
                project_id=s.watsonx_project_id,  # read from env, never hardcoded
            )
            logger.info(
                "GraniteService initialised | model=%s | endpoint=%s",
                s.granite_model_id,
                s.watsonx_url,
            )
        except Exception as exc:
            ibm_err = f"{type(exc).__name__}: {exc}"
            logger.error("GraniteService init failed: %s", ibm_err)
            raise GraniteUnavailableError(
                "Failed to initialise IBM Granite client.",
                ibm_error=ibm_err,
            ) from exc

    # ── Core inference ────────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        repetition_penalty: float | None = None,
    ) -> GraniteResponse:
        """
        Send a prompt to IBM Granite and return a GraniteResponse.

        Raises:
            GraniteNotConfiguredError — credentials missing.
            GraniteUnavailableError  — IBM API call failed (exact error preserved).
        """
        self._ensure_model()
        s = self._settings

        params: dict[str, Any] = {
            "max_new_tokens": max_new_tokens if max_new_tokens is not None else s.granite_max_new_tokens,
            "min_new_tokens": s.granite_min_new_tokens,
            "temperature":    temperature if temperature is not None else s.granite_temperature,
            "top_p":          top_p if top_p is not None else s.granite_top_p,
            "top_k":          top_k if top_k is not None else s.granite_top_k,
            "repetition_penalty": repetition_penalty if repetition_penalty is not None else s.granite_repetition_penalty,
        }

        start = time.perf_counter()
        try:
            raw = self._model.generate(prompt=prompt, params=params)
        except Exception as exc:
            ibm_err = f"{type(exc).__name__}: {exc}"
            logger.error("Granite inference failed | model=%s | error=%s", s.granite_model_id, ibm_err)
            raise GraniteUnavailableError(
                "IBM Granite inference request failed.",
                ibm_error=ibm_err,
            ) from exc
        latency = time.perf_counter() - start

        # Parse the IBM SDK response structure
        # Shape: {"results": [{"generated_text": ..., "stop_reason": ...,
        #                       "input_token_count": ..., "generated_token_count": ...}]}
        try:
            result = raw["results"][0]
            generated_text: str = result.get("generated_text", "").strip()
            input_tokens: int  = result.get("input_token_count", 0)
            output_tokens: int = result.get("generated_token_count", 0)
            stop_reason: str   = result.get("stop_reason", "")
        except (KeyError, IndexError, TypeError) as exc:
            raise GraniteUnavailableError(
                "Unexpected response structure from IBM Granite.",
                ibm_error=repr(raw),
            ) from exc

        # Log token usage so the Lite budget (300K/month) can be monitored
        logger.info(
            "Granite inference | model=%s | in_tokens=%d | out_tokens=%d | "
            "stop=%s | latency=%.2fs",
            s.granite_model_id, input_tokens, output_tokens, stop_reason, latency,
        )

        return GraniteResponse(
            generated_text=generated_text,
            model_id=s.granite_model_id,
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            stop_reason=stop_reason,
            latency_seconds=round(latency, 3),
            raw_response=raw,
        )

    # ── Connection test ───────────────────────────────────────────────────────

    def test_connection(self) -> ConnectionTestResult:
        """
        Perform a real minimal inference request to verify end-to-end connectivity.
        This is the authoritative check — credential validation alone is NOT enough.

        Does NOT assume the model is accessible — reports the exact IBM error if not.
        Also runs a separate Tamil generation probe (labelled as experimental).
        """
        s = self._settings
        result = ConnectionTestResult(
            success=False,
            model_id=s.granite_model_id,
            endpoint=s.watsonx_url,
            project_id_configured=bool(s.watsonx_project_id),
            api_key_configured=bool(s.watsonx_api_key),
        )

        # ── English inference probe ───────────────────────────────────────────
        english_probe = (
            "You are an agricultural assistant. "
            "In one sentence, what is the most important factor for rice cultivation?"
        )
        try:
            resp = self.generate(english_probe, max_new_tokens=80, temperature=0.1)
            result.success = True
            result.sample_response = resp.generated_text
            result.input_tokens = resp.input_token_count
            result.output_tokens = resp.output_token_count
            result.latency_seconds = resp.latency_seconds
        except GraniteNotConfiguredError as exc:
            result.ibm_error_type = "GraniteNotConfiguredError"
            result.ibm_error_message = str(exc)
            return result
        except GraniteUnavailableError as exc:
            result.ibm_error_type = "GraniteUnavailableError"
            result.ibm_error_message = exc.ibm_error or exc.message
            return result

        # ── Tamil generation probe (experimental) ─────────────────────────────
        # Granite 4 H Small does NOT officially advertise Tamil support.
        # This probe attempts Tamil output and reports the actual result without
        # claiming it as a supported feature.
        result.tamil_test_attempted = True
        tamil_probe = (
            "You are an agricultural assistant. "
            "Answer the following question in Tamil (தமிழ்): "
            "நெல் சாகுபடியில் மிக முக்கியமான காரணி என்ன? "
            "(What is the most important factor in rice cultivation?)"
        )
        try:
            tamil_resp = self.generate(tamil_probe, max_new_tokens=120, temperature=0.2)
            result.tamil_test_response = tamil_resp.generated_text
            result.tamil_test_note = (
                "Tamil probe completed. Review the response above to evaluate quality. "
                "Granite 4 H Small does not officially list Tamil as a supported language — "
                "actual output quality may vary."
            )
        except GraniteUnavailableError as exc:
            result.tamil_test_response = ""
            result.tamil_test_note = (
                f"Tamil probe failed (this is separate from the main connection test): "
                f"{exc.ibm_error or exc.message}"
            )

        return result
