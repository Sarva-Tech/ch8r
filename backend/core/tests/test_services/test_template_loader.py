import pytest
from unittest.mock import Mock, patch, MagicMock

from core.services.template_loader import TemplateLoader


@pytest.fixture(autouse=True)
def reset_template_loader_cache():
    yield
    TemplateLoader._env = None
    TemplateLoader._templates_cache = {}


@pytest.mark.unit
class TestGetEnvironment:
    @patch('core.services.template_loader.Environment')
    @patch('core.services.template_loader.settings')
    def test_get_environment_first_call(self, mock_settings, mock_env_class):
        mock_settings.JINJA_TEMPLATE_DIR = '/templates'
        mock_env_instance = Mock()
        mock_env_class.return_value = mock_env_instance
        
        result = TemplateLoader.get_environment()
        
        assert mock_env_class.called
        assert result == mock_env_instance

    @patch('core.services.template_loader.Environment')
    @patch('core.services.template_loader.settings')
    def test_get_environment_cached(self, mock_settings, mock_env_class):
        mock_settings.JINJA_TEMPLATE_DIR = '/templates'
        mock_env_instance = Mock()
        mock_env_class.return_value = mock_env_instance
        
        result1 = TemplateLoader.get_environment()
        result2 = TemplateLoader.get_environment()
        
        assert mock_env_class.call_count == 1
        assert result1 == result2

    @patch('core.services.template_loader.Environment')
    def test_get_environment_custom_dir(self, mock_env_class):
        mock_env_instance = Mock()
        mock_env_class.return_value = mock_env_instance
        
        result = TemplateLoader.get_environment(template_dir='/custom/templates')
        
        assert mock_env_class.called
        assert result == mock_env_instance

    @patch('core.services.template_loader.Environment')
    @patch('core.services.template_loader.settings')
    def test_get_environment_default_dir(self, mock_settings, mock_env_class):
        mock_settings.JINJA_TEMPLATE_DIR = '/default/templates'
        mock_env_instance = Mock()
        mock_env_class.return_value = mock_env_instance
        
        result = TemplateLoader.get_environment()
        
        assert mock_env_class.called


@pytest.mark.unit
class TestGetTemplate:
    @patch('core.services.template_loader.TemplateLoader.get_environment')
    def test_get_template_first_call(self, mock_get_env):
        mock_env = Mock()
        mock_template = Mock()
        mock_env.get_template.return_value = mock_template
        mock_get_env.return_value = mock_env
        
        result = TemplateLoader.get_template('test_template.html')
        
        mock_get_env.assert_called_once_with(None)
        mock_env.get_template.assert_called_once_with('test_template.html')
        assert result == mock_template

    @patch('core.services.template_loader.TemplateLoader.get_environment')
    def test_get_template_cached(self, mock_get_env):
        mock_env = Mock()
        mock_template = Mock()
        mock_env.get_template.return_value = mock_template
        mock_get_env.return_value = mock_env
        
        result1 = TemplateLoader.get_template('test_template.html')
        result2 = TemplateLoader.get_template('test_template.html')
        
        assert mock_get_env.call_count == 1
        assert mock_env.get_template.call_count == 1
        assert result1 == result2

    @patch('core.services.template_loader.TemplateLoader.get_environment')
    def test_get_template_custom_dir(self, mock_get_env):
        mock_env = Mock()
        mock_template = Mock()
        mock_env.get_template.return_value = mock_template
        mock_get_env.return_value = mock_env
        
        result = TemplateLoader.get_template('test_template.html', template_dir='/custom')
        
        mock_get_env.assert_called_once_with('/custom')
        mock_env.get_template.assert_called_once_with('test_template.html')
        assert result == mock_template

    @patch('core.services.template_loader.TemplateLoader.get_environment')
    def test_get_template_different_dirs_separate_cache(self, mock_get_env):
        mock_env = Mock()
        mock_template1 = Mock()
        mock_template2 = Mock()
        mock_env.get_template.side_effect = [mock_template1, mock_template2]
        mock_get_env.return_value = mock_env
        
        result1 = TemplateLoader.get_template('test_template.html', template_dir='/dir1')
        result2 = TemplateLoader.get_template('test_template.html', template_dir='/dir2')
        
        assert mock_get_env.call_count == 2
        assert mock_env.get_template.call_count == 2

    @patch('core.services.template_loader.TemplateLoader.get_environment')
    def test_get_template_different_names_separate_cache(self, mock_get_env):
        mock_env = Mock()
        mock_template1 = Mock()
        mock_template2 = Mock()
        mock_env.get_template.side_effect = [mock_template1, mock_template2]
        mock_get_env.return_value = mock_env
        
        result1 = TemplateLoader.get_template('template1.html')
        result2 = TemplateLoader.get_template('template2.html')
        
        assert mock_get_env.call_count == 2
        assert mock_env.get_template.call_count == 2


@pytest.mark.unit
class TestRenderTemplate:
    @patch('core.services.template_loader.TemplateLoader.get_template')
    def test_render_template_success(self, mock_get_template):
        mock_template = Mock()
        mock_template.render.return_value = 'Rendered content'
        mock_get_template.return_value = mock_template
        
        context = {'name': 'John', 'action': 'created'}
        result = TemplateLoader.render_template('test_template.html', context)
        
        mock_get_template.assert_called_once_with('test_template.html', None)
        mock_template.render.assert_called_once_with(name='John', action='created')
        assert result == 'Rendered content'

    @patch('core.services.template_loader.TemplateLoader.get_template')
    def test_render_template_with_custom_dir(self, mock_get_template):
        mock_template = Mock()
        mock_template.render.return_value = 'Rendered content'
        mock_get_template.return_value = mock_template
        
        context = {'key': 'value'}
        result = TemplateLoader.render_template('test_template.html', context, template_dir='/custom')
        
        mock_get_template.assert_called_once_with('test_template.html', '/custom')
        mock_template.render.assert_called_once_with(key='value')
        assert result == 'Rendered content'

    @patch('core.services.template_loader.TemplateLoader.get_template')
    def test_render_template_empty_context(self, mock_get_template):
        mock_template = Mock()
        mock_template.render.return_value = 'Rendered content'
        mock_get_template.return_value = mock_template
        
        result = TemplateLoader.render_template('test_template.html', {})
        
        mock_template.render.assert_called_once_with()
        assert result == 'Rendered content'

    @patch('core.services.template_loader.TemplateLoader.get_template')
    def test_render_template_uses_cache(self, mock_get_template):
        mock_template = Mock()
        mock_template.render.return_value = 'Rendered content'
        mock_get_template.return_value = mock_template
        
        context = {'key': 'value'}
        TemplateLoader.render_template('test_template.html', context)
        TemplateLoader.render_template('test_template.html', context)
        
        assert mock_get_template.call_count == 2
