import os
import yaml
from jinja2 import BaseLoader, Environment, TemplateNotFound


class YamlLoader(BaseLoader):
    """ Adapted from flask.templating """

    def __init__(self, path):
        self.path = path
        self.mapping = {}
        self._reload_mapping()

    def _reload_mapping(self):
        if os.path.isfile(self.path):
            self.last_mtime = os.path.getmtime(self.path)
            with open(self.path) as f:
                self.mapping = yaml.safe_load(f.read())

    def get_source(self, environment, template):
        if not os.path.isfile(self.path):
            return None, None, None
        if self.last_mtime != os.path.getmtime(self.path):
            self._reload_mapping()
        if template in self.mapping:
            source = self.mapping[template]
            return source, None, lambda: source == self.mapping.get(template)
        raise TemplateNotFound(template)


this_dir = os.path.dirname(os.path.realpath(__file__))
templates = os.path.join(this_dir, 'templates.yaml')
env = Environment(loader=YamlLoader(templates), trim_blocks=True, lstrip_blocks=True)


def render_template(template_name_or_list, **context):
    return env.get_or_select_template(template_name_or_list).render(context)
