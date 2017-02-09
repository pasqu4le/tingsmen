# a collection of utility classes and functions
from misaka.api import HtmlRenderer


class CustomMisakaRenderer(HtmlRenderer):

    def normal_text(self, text):
        processed = []
        for word in text.split(' '):
            if word.startswith('@'):
                processed.append('<a href="/user/{0}">{1}</a>'.format(word[1:], word))
            elif word.startswith('#'):
                processed.append('<a href="/topic/{0}">{1}</a>'.format(word[1:].lower(), word))
            elif word.startswith('$'):
                processed.append('<a href="/law/{0}">Law {0}</a>'.format(word[1:]))
            elif word.startswith('%'):
                processed.append('<a href="/proposal/{0}">Proposal {0}</a>'.format(word[1:]))
            else:
                processed.append(word)
        return ' '.join(processed)

    def image(self, link, title, alt):
        return '<img class="img-responsive" src="{0}" title="{1}" alt="{2}">'.format(link, title, alt)
