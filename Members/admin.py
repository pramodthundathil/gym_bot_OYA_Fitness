from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Subscription)
admin.site.register(Payment)
admin.site.register(MemberData)
admin.site.register(Subscription_Period)
admin.site.register(TypeSubsription)
admin.site.register(Batch_DB)
admin.site.register(AccessToGate)



