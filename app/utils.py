# a collection of utility classes and functions
from misaka.api import HtmlRenderer


class CustomMisakaRenderer(HtmlRenderer):

    def normal_text(self, text):
        processed = []
        for word in text.split(' '):
            if word.startswith('@') and len(word) > 1:
                processed.append('<a href="/user/{0}">{1}</a>'.format(word[1:], word))
            elif word.startswith('#') and len(word) > 1:
                processed.append('<a href="/topic/{0}">{1}</a>'.format(word[1:].lower(), word))
            elif word.startswith('$') and len(word) > 1:
                processed.append('<a href="/law/{0}">Law {0}</a>'.format(word[1:]))
            elif word.startswith('%') and len(word) > 1:
                processed.append('<a href="/proposal/{0}">Proposal {0}</a>'.format(word[1:]))
            else:
                processed.append(word)
        return ' '.join(processed)

    def image(self, link, title, alt):
        return '<img class="img-responsive" src="{0}" title="{1}" alt="{2}">'.format(link, title, alt)


def get_topic_name(name):
    topic_name = []
    after_hyphens = False
    for l in name:
        if l.isalnum():
            topic_name.append(l)
            after_hyphens = False
        elif l == '-' and not after_hyphens:
            topic_name.append(l)
            after_hyphens = True
    return ''.join(topic_name).strip('-').lower()
