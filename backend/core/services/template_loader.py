import os

from django.conf import settings
from jinja2 import Environment, FileSystemLoader, Template

class TemplateLoader:
    _env = None
    _templates_cache = {}

    @classmethod
    def get_environment(cls, template_dir=None):
        if cls._env is None:
            if template_dir is None:
                template_dir = str(settings.JINJA_TEMPLATE_DIR)
            cls._env = Environment(loader=FileSystemLoader(template_dir))
        return cls._env

    @classmethod
    def get_template(cls, template_name, template_dir=None) -> Template:
        key = (template_dir, template_name)
        if key not in cls._templates_cache:
            env = cls.get_environment(template_dir)
            cls._templates_cache[key] = env.get_template(template_name)
        return cls._templates_cache[key]

    @classmethod
    def render_template(cls, template_name, context, template_dir=None) -> str:
        template = cls.get_template(template_name, template_dir)
        return template.render(**context)
