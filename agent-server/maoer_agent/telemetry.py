"""Optional local Langfuse observations; never own task state or execution."""
import hashlib
import logging
from contextlib import contextmanager
from contextvars import ContextVar

LOG = logging.getLogger('maoer.agent.telemetry')


class Telemetry:
    def __init__(self, settings):
        self.client = None
        self.parent = ContextVar('telemetry_parent', default=None)
        self.secrets = tuple(v for v in (settings.api_key, settings.access_token,
            settings.tavily_key, settings.langfuse_secret_key) if v)
        if settings.langfuse_public_key:
            import httpx
            from langfuse import Langfuse
            from opentelemetry.sdk.trace import TracerProvider
            self.http = httpx.Client(trust_env=False, timeout=2)
            self.client = Langfuse(public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key, base_url=settings.langfuse_base_url,
                environment=settings.langfuse_environment, release=settings.langfuse_release or None, timeout=2, flush_interval=3,
                httpx_client=self.http, tracer_provider=TracerProvider())

    def clean(self, value):
        if isinstance(value, dict):
            return {k: ({'characters': len(str(v)), 'sha256': hashlib.sha256(str(v).encode()).hexdigest()}
                       if k == 'reasoning_content' else self.clean(v))
                    for k, v in value.items() if k.lower() not in
                    {'api_key', 'authorization', 'access_token', 'secret_key', 'password', 'token'}}
        if isinstance(value, (list, tuple)):
            return [self.clean(v) for v in value]
        if isinstance(value, str):
            for secret in self.secrets:
                value = value.replace(secret, '[redacted]')
        return value

    def start(self, run, name, *, input=None, kind='span', **fields):
        if not self.client:
            return None
        try:
            from langfuse import propagate_attributes
            trace = {'trace_id': hashlib.sha256(run['id'].encode()).hexdigest()[:32]}
            if self.parent.get():
                trace['parent_span_id'] = self.parent.get()
            with propagate_attributes(session_id=run['conversation_id'], trace_name='MaoerAgent',
                                      metadata={'run_id': run['id']}):
                return self.client.start_observation(name=name, as_type=kind, trace_context=trace,
                    input=self.clean(input), **self.clean(fields))
        except Exception as exc:
            LOG.warning('observation_start_failed type=%s', type(exc).__name__)
            return None

    def finish(self, span, *, output=None, **fields):
        if span is not None:
            try:
                span.update(output=self.clean(output), **self.clean(fields))
                span.end()
            except Exception as exc:
                LOG.warning('observation_finish_failed type=%s', type(exc).__name__)

    def event(self, run, name, *, input=None, output=None, **fields):
        self.finish(self.start(run, name, input=input, **fields), output=output)

    @contextmanager
    def segment(self, run, name):
        span = self.start(run, name, input=run.get('input'))
        token = self.parent.set(span.id if span is not None else None)
        try:
            yield
        finally:
            self.parent.reset(token)
            self.finish(span)

    @staticmethod
    def snapshot(run):
        return {k: run[k] for k in ('status', 'phase', 'text', 'error', 'route', 'page_resolution',
            'goal_bindings', 'goal_progress', 'calls', 'outcome') if k in run}

    def close(self):
        if self.client:
            self.client.shutdown()
            self.http.close()
