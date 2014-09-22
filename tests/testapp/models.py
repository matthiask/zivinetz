from feincms.content.raw.models import RawContent
from feincms.module.page.models import Page


Page.register_templates({
    'key': 'base',
    'title': 'base',
    'path': 'base.html',
    'regions': (
        ('main', 'Main content area'),
    ),
})
Page.create_content_type(RawContent)
