from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template, render_to_string
from django.utils import timezone


def get_local_time():
    return timezone.now().astimezone()


def render_text(template_name, context):
    template = get_template(template_name).template
    return template.render(Context(context, autoescape=False)).strip()


def send_email(app, event, context, recipients=(), from_email=None):

    subject_template_name = "%s/%s/subject.txt" % (app, event)
    subject = render_text(subject_template_name, context)

    text_template_name = "%s/%s/message.txt" % (app, event)
    text_message = render_text(text_template_name, context)

    html_template_name = "%s/%s/message.html" % (app, event)
    html_message = render_to_string(html_template_name, context)

    for recipient in recipients:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        email = EmailMultiAlternatives(
            subject=subject, body=text_message, to=[recipient], from_email=from_email
        )

        email.attach_alternative(html_message, "text/html")

        email.send()
