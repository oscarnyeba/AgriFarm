from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from firebase_admin import messaging

def send_email_alert(recipient_email, subject, template, context):
    """
    Send an email alert to the specified recipient.
    
    :param recipient_email: Email address of the recipient
    :param subject: Subject of the email
    :param template: Path to the HTML template for the email body
    :param context: Dictionary containing context data for the template
    """
    html_message = render_to_string(template, context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        html_message=html_message,
        fail_silently=False,
    )

def send_push_notification(token, title, body):
    """
    Send a push notification to a device with the specified token.
    
    :param token: The FCM token of the device
    :param title: Title of the notification
    :param body: Body text of the notification
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )
    
    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print('Error sending message:', str(e))
def create_alert(farm, message):
    """
    Create an alert for a farm and send notifications.
    
    :param farm: The Farm object for which to create the alert
    :param message: The alert message
    """
    from .models import Alert  # Import here to avoid circular imports
    
    # Create and save the alert
    alert = Alert.objects.create(farm=farm, message=message)
    
    # Send email notification
    subject = f"Weather Alert for {farm.farm_name}"
    template = 'farm_management/weather_alert.html'
    context = {'farm': farm, 'message': message}
    send_email_alert(farm.user.email, subject, template, context)
    
    # Send push notification if the user has a FCM token
    if hasattr(farm.user, 'profile') and farm.user.profile.fcm_token:
        send_push_notification(
            farm.user.profile.fcm_token,
            f"Weather Alert for {farm.farm_name}",
            message
        )
    
    return alert

