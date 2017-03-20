# a collection of utility classes and functions
import re
import flask_misaka


class CustomMisaka(flask_misaka.Misaka):

    def render(self, text, **overrides):
        # this method is a copy of the original one, except the input text is preprocessed
        preprocessed = []
        for word in re.findall(r"[\w%$@#-]+|[^\w]", text):
            if len(word) > 1:
                if word.startswith('@'):
                    preprocessed.append('[{0}](/user/{1})'.format(word, word[1:]))
                elif word.startswith('#'):
                    preprocessed.append('[{0}](/topic/{1})'.format(word, sane_topic_name(word)))
                elif word.startswith('$'):
                    preprocessed.append('[Law {0}](/law/{0})'.format(word[1:]))
                elif word.startswith('%'):
                    preprocessed.append('[Proposal {0}](/proposal/{0})'.format(word[1:]))
                else:
                    preprocessed.append(word)
            else:
                preprocessed.append(word)

        options = self.defaults
        if overrides:
            options = flask_misaka.copy(options)
            options.update(overrides)
        return flask_misaka.markdown(''.join(preprocessed), self.renderer, **options)


def sane_topic_name(name):
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
