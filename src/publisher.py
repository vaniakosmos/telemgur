import traceback

from telegram.constants import MAX_CAPTION_LENGTH, MAX_MESSAGE_LENGTH
from telegram.error import TimedOut, BadRequest, TelegramError

from autoposter import AbstractPublisher
from settings import POST_TIMEOUT
from .wrappers import Image, Post, RedditPost


class ExceptionsHandlerMixin(object):
    def __init__(self):
        self.logger = None

    def exceptions_handler_wrapper(self, f, obj):
        def decorated(*args, **kwargs):
            try:
                f(*args, **kwargs)
            except (TimedOut, BadRequest) as e:
                self.log_error(e, obj, print_traceback=True)
            except (TelegramError, Exception) as e:
                self.log_error(e, obj, print_traceback=True)

        return decorated

    def log_error(self, err: Exception, obj,
                  print_traceback=False,
                  print_post=True):
        self.logger.warning(err.__class__.__name__)
        self.logger.warning(err)
        if print_traceback:
            for line in traceback.format_exc().split('\n'):
                self.logger.warning(line)
        if print_post:
            self.logger.warning(obj)


class CutterMixin(object):
    @staticmethod
    def cut_text(text: str, limit: int):
        if text is None:
            return ''
        elif len(text) > limit:
            text = text[:limit - 5]
            without_last = text.split()[:-1]
            text = ' '.join(without_last)
            return text + '...'
        else:
            return text


class ImgurPostPublisher(AbstractPublisher, ExceptionsHandlerMixin, CutterMixin):
    def publish(self, post: Post):
        self.logger.debug(post)
        self.exceptions_handler_wrapper(self.publish_title, post)(post)

        self.db.add(post.id, post.datetime)

        for image in post.images:
            self.logger.debug(f'    | {image}')
            self.exceptions_handler_wrapper(self.publish_item, image)(image, post)

    def publish_title(self, post: Post):
        text = self.format_title(post)
        self.bot.send_message(chat_id=self.channel_id,
                              text=text,
                              disable_web_page_preview=True,
                              timeout=POST_TIMEOUT)

    def publish_item(self, image: Image, post: Post):
        is_single_image = post.images_count == 1
        text = self.format_image_caption(image, is_single_image)

        kwargs = {
            'caption': text,
            'chat_id': self.channel_id,
            'disable_notification': True,
            'timeout': POST_TIMEOUT,
        }

        if image.animated:
            self.bot.send_video(video=image.src, **kwargs)
        else:
            self.bot.send_photo(photo=image.src, **kwargs)

    def format_title(self, post: Post):
        strings = ['🌚 ' + butch for butch in post.title.split('\n')]
        if post.is_dump:
            strings.append(f'🔥 Album with {post.images_count} items')
        strings.append('🔗 ' + post.link)
        if post.tags:
            strings.append('🏷 ' + ' '.join(post.tags))
        if post.images_count == 1:
            strings.append(post.desc)
        text = '\n'.join(strings)
        return self.cut_text(text, limit=MAX_MESSAGE_LENGTH)

    def format_image_caption(self, image: Image, is_single_image: bool):
        if not is_single_image:
            return self.cut_text(image.desc, limit=MAX_CAPTION_LENGTH)
        else:
            return ''


class RedditPublisher(AbstractPublisher, ExceptionsHandlerMixin, CutterMixin):
    def publish(self, post: RedditPost):
        self.logger.debug(post)
        self.db.add(post.id, post.datetime)

        self.exceptions_handler_wrapper(self.publish_item, post)(post)

    def publish_item(self, post: RedditPost):
        if post.type == 'link':
            text = post.title
            text += '\n' + post.url
            text += '\n#' + post.subreddit + ' ' + post.comments
            self.bot.send_message(text=text,
                                  chat_id=self.channel_id,
                                  timeout=POST_TIMEOUT)
        else:
            text = self.cut_text(post.title, limit=MAX_CAPTION_LENGTH-40)
            text += '\n#' + post.subreddit + ' ' + post.comments
            kwargs = {
                'caption': text,
                'chat_id': self.channel_id,
                'timeout': POST_TIMEOUT,
            }
            if post.type == 'photo':
                self.bot.send_photo(photo=post.url, **kwargs)
            elif post.type == 'video':
                self.bot.send_video(video=post.url, **kwargs)
