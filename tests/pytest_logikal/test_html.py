from collections.abc import Callable

from pytest import raises

from pytest_logikal import html
from pytest_logikal.plugin import Item, ItemRunError
from tests.pytest_logikal.conftest import FILES_DIR


def test_htmlj_template_item_run(plugin_item: Callable[..., Item]) -> None:
    item = plugin_item(
        plugin=html.HTMLTemplatePlugin,
        item=html.HTMLTemplateItem,
        file_contents={'invalid.html.j': (FILES_DIR / 'invalid.html.j').read_text()},
    )
    with raises(ItemRunError) as error:
        item.runtest()

    print('Reported errors:\n=====')
    print(str(error.value))
    print('=====')

    # Formatting errors
    # error.match('\n\\x1b\\[31m-</html>')
    # error.match('\n\\x1b\\[32m\\+  </html>')

    # Linting errors
    error.match('1:0: error: Html tag should have lang attribute\\. \\(H005\\)')
    error.match('1:0: error: Missing title tag in html\\. \\(H016\\)')
    error.match('1:0: error: Consider adding a meta description\\. \\(H030\\)')
    error.match('7:2: error: Img tag should have height and width attributes\\. \\(H006\\)')
    error.match('7:2: error: Img tag should have an alt attribute\\. \\(H013\\)')
    error.match('19:0: error: Tag seems to be an orphan\\. \\(H025\\)')
