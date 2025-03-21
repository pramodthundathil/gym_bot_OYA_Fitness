from django.core.management.base import BaseCommand
from Members.models import MemberData

class Command(BaseCommand):
    help = "Update Active_status for members based on unpaid subscriptions."

    def handle(self, *args, **kwargs):
        members = MemberData.objects.all()
        for member in members:
            member.update_active_status()
        self.stdout.write(self.style.SUCCESS("Successfully updated member statuses!"))
