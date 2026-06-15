import pytest
from unittest.mock import patch, MagicMock, call

from core.telemetry import setup_telemetry


@pytest.fixture(autouse=True)
def clean_otel_env(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)


def _make_patches():
    return [
        patch("core.telemetry.trace"),
        patch("core.telemetry.TracerProvider"),
        patch("core.telemetry.BatchSpanProcessor"),
        patch("core.telemetry.OTLPSpanExporter"),
        patch("core.telemetry.FastAPIInstrumentor"),
        patch("core.telemetry.HTTPXClientInstrumentor"),
        patch("core.telemetry.Resource"),
    ]


def test_no_op_without_endpoint():
    with patch("core.telemetry.trace") as mock_trace, \
         patch("core.telemetry.FastAPIInstrumentor"), \
         patch("core.telemetry.HTTPXClientInstrumentor"):
        setup_telemetry(MagicMock())
        mock_trace.set_tracer_provider.assert_not_called()


def test_configures_provider_with_endpoint(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    with patch("core.telemetry.trace") as mock_trace, \
         patch("core.telemetry.TracerProvider") as MockProvider, \
         patch("core.telemetry.BatchSpanProcessor"), \
         patch("core.telemetry.OTLPSpanExporter"), \
         patch("core.telemetry.FastAPIInstrumentor"), \
         patch("core.telemetry.HTTPXClientInstrumentor"), \
         patch("core.telemetry.Resource"):
        setup_telemetry(MagicMock())
        mock_trace.set_tracer_provider.assert_called_once_with(MockProvider.return_value)


def test_fastapi_instrumented(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    mock_app = MagicMock()
    with patch("core.telemetry.trace"), \
         patch("core.telemetry.TracerProvider"), \
         patch("core.telemetry.BatchSpanProcessor"), \
         patch("core.telemetry.OTLPSpanExporter"), \
         patch("core.telemetry.FastAPIInstrumentor") as MockFastAPI, \
         patch("core.telemetry.HTTPXClientInstrumentor"), \
         patch("core.telemetry.Resource"):
        setup_telemetry(mock_app)
        MockFastAPI.instrument_app.assert_called_once_with(mock_app)


def test_httpx_instrumented(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    with patch("core.telemetry.trace"), \
         patch("core.telemetry.TracerProvider"), \
         patch("core.telemetry.BatchSpanProcessor"), \
         patch("core.telemetry.OTLPSpanExporter"), \
         patch("core.telemetry.FastAPIInstrumentor"), \
         patch("core.telemetry.HTTPXClientInstrumentor") as MockHTTPX, \
         patch("core.telemetry.Resource"):
        setup_telemetry(MagicMock())
        MockHTTPX.return_value.instrument.assert_called_once()


def test_service_name_default(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    with patch("core.telemetry.trace"), \
         patch("core.telemetry.TracerProvider"), \
         patch("core.telemetry.BatchSpanProcessor"), \
         patch("core.telemetry.OTLPSpanExporter"), \
         patch("core.telemetry.FastAPIInstrumentor"), \
         patch("core.telemetry.HTTPXClientInstrumentor"), \
         patch("core.telemetry.Resource") as MockResource:
        setup_telemetry(MagicMock())
        MockResource.create.assert_called_once_with({"service.name": "code-review-demo"})


def test_service_name_from_env(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "my-custom-service")
    with patch("core.telemetry.trace"), \
         patch("core.telemetry.TracerProvider"), \
         patch("core.telemetry.BatchSpanProcessor"), \
         patch("core.telemetry.OTLPSpanExporter"), \
         patch("core.telemetry.FastAPIInstrumentor"), \
         patch("core.telemetry.HTTPXClientInstrumentor"), \
         patch("core.telemetry.Resource") as MockResource:
        setup_telemetry(MagicMock())
        MockResource.create.assert_called_once_with({"service.name": "my-custom-service"})
