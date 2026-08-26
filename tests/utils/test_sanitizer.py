"""Unit tests for XSS sanitizer — pure Python, no DB."""
from app.utils.sanitizer import sanitize_string, sanitize_dict, SanitizeMixin
import marshmallow as ma


class TestSanitizeString:
    def test_strips_script_tags(self):
        assert sanitize_string('<script>alert("xss")</script>hello') == 'hello'

    def test_strips_img_onerror(self):
        assert sanitize_string('<img src=x onerror=alert(1)>text') == 'text'

    def test_preserves_plain_text(self):
        assert sanitize_string('normal text') == 'normal text'

    def test_strips_bold_tags(self):
        assert sanitize_string('<b>bold</b> text') == 'bold text'

    def test_empty_string(self):
        assert sanitize_string('') == ''

    def test_non_string_passthrough(self):
        assert sanitize_string(123) == 123
        assert sanitize_string(None) is None

    def test_nested_tags(self):
        assert sanitize_string('<div><span>hi</span></div>') == 'hi'

    def test_preserves_ampersand(self):
        result = sanitize_string('a & b')
        assert '&' in result


class TestSanitizeDict:
    def test_sanitizes_string_values(self):
        data = {'name': '<script>x</script>laptop', 'price': 100}
        result = sanitize_dict(data)
        assert result['name'] == 'laptop'
        assert result['price'] == 100

    def test_nested_dict(self):
        data = {'outer': {'inner': '<b>text</b>'}}
        result = sanitize_dict(data)
        assert result['outer']['inner'] == 'text'

    def test_list_values(self):
        data = {'items': ['<script>x</script>a', 'normal']}
        result = sanitize_dict(data)
        assert result['items'] == ['a', 'normal']

    def test_empty_dict(self):
        assert sanitize_dict({}) == {}

    def test_non_dict_string(self):
        assert sanitize_dict('<b>hi</b>') == 'hi'


class TestSanitizeMixin:
    def test_pre_load_sanitizes(self):
        class TestSchema(SanitizeMixin, ma.Schema):
            name = ma.fields.Str()

        schema = TestSchema()
        result = schema.load({'name': '<script>x</script>clean'})
        assert result['name'] == 'clean'

    def test_pre_load_preserves_non_string(self):
        class TestSchema(SanitizeMixin, ma.Schema):
            count = ma.fields.Int()

        schema = TestSchema()
        result = schema.load({'count': 5})
        assert result['count'] == 5
