# a collection of utility classes and functions
import re
import flask_misaka
from misaka.api import HtmlRenderer
from urlparse import urlparse
import requests
from bs4 import BeautifulSoup
from flask import render_template, get_template_attribute


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


class CustomMisakaRenderer(HtmlRenderer):

    def autolink(self, link, is_email):
        if is_email:
            return '<a href="mailto:{0}">{0}</a>'.format(link)
        # analyze url
        parsed = urlparse(link)
        if 'youtube.com' in parsed.netloc:
            vid_id = dict(item.split('=') for item in parsed.query.split('&'))['v']
            return youtube_embed(vid_id)
        if 'youtu.be' in parsed.netloc:
            vid_id = parsed.path
            return youtube_embed(vid_id)
        if parsed.path.lower().endswith(('.jpg', '.jpeg', '.jpe', '.jif', '.jfif', '.jfi', '.gif', '.png')):
            return '<a href="{0}"><img src="{0}" class="img-responsive img-thumbnail" /></a>'.format(link)
        # standard case autolink
        res = requests.get(link)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string
        if len(title) > 50:
            title = title[:47] + '...'
        icon = soup.find("link", rel="shortcut icon")
        if icon:
            icon = icon['href']
            # might be not absolute
            if not icon.startswith('http'):
                # url might have changed
                parsed = urlparse(res.url)
                if not icon.startswith('/'):
                    icon = '/' + icon
                icon = parsed.scheme + '://' + parsed.netloc + icon
        render_autolink = get_template_attribute('macros.html', 'render_autolink')
        return render_autolink(link, title, icon).unescape()


def youtube_embed(vid_id):
    return '<div class="embed-responsive embed-responsive-16by9"><iframe src="https://www.youtube.com/embed/{0}" ' \
           'class="embed-responsive-item" allowfullscreen></iframe></div>'.format(vid_id)


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
