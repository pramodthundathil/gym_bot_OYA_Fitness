from django.db import models


# Setting classess 

class Batch_DB(models.Model):
    Batch_Name = models.CharField(max_length=255,choices=(("Morning","Morning"),("Evening","Evening"),("Stoped","Stoped")))
    Batch_Status = models.BooleanField(default=True)
    Batch_Time = models.TimeField(auto_now_add=False)

    def __str__(self):
        return (str(self.Batch_Name) + " " + str(self.Batch_Time))


class TypeSubsription(models.Model):
    Type = models.CharField(max_length=255)
    def __str__(self):
        return self.Type



class Subscription_Period(models.Model):
    Period = models.PositiveIntegerField()
    Category = models.CharField(max_length=255, choices=(("Day","Day"),("Week","Week"),("Month","Month"),("Year","Year")))

    def __str__(self):
        return (str(self.Period) + " " +str(self.Category))
    

class MemberData(models.Model):
    First_Name = models.CharField(max_length=255)
    Last_Name = models.CharField(max_length=255)
    Date_Of_Birth = models.DateField(auto_now_add=False)
    Gender = models.CharField(max_length=255,choices=(("Male","Male"),("Female","Female"),("Other","Other")))
    Mobile_Number = models.CharField(max_length=255)
    Discount = models.FloatField(null=True, blank= True)
    Special_Discount = models.BooleanField(default = False)
    Email = models.EmailField(null=True, blank=True)
    Address = models.TextField(max_length=200)
    Medical_History = models.TextField(max_length=2000,null=True,blank=True)
    Registration_Date = models.DateField(auto_now_add=False)
    Photo = models.FileField(upload_to='member_photo')
    Id_Upload = models.FileField(upload_to="member_id", null=True, blank=True)
    Date_Added = models.DateField(auto_now_add=True)
    Active_status = models.BooleanField(default=True)
    Access_status = models.BooleanField(default=False)
    Access_Token_Id = models.CharField(max_length=255,null=True,blank=True)

    def update_active_status(self):
        """
        Check if the member has any unpaid subscriptions.
        If any subscription has Payment_Status=False, set Active_status=False.
        """
        has_unpaid_subscriptions = self.Member_subscription.filter(Payment_Status=False).exists()
        
        if has_unpaid_subscriptions:
            self.Active_status = False
        else:
            self.Active_status = True  # Optionally re-enable if all are paid
        
        self.save()

    def __str__(self):
        return self.First_Name +" "+self.Last_Name

class Subscription(models.Model):
    Member = models.ForeignKey(MemberData, on_delete=models.CASCADE,null=True, blank=True, related_name="Member_subscription")
    Type_Of_Subscription = models.ForeignKey(TypeSubsription,on_delete=models.SET_NULL,null=True,blank=True)
    Period_Of_Subscription = models.ForeignKey(Subscription_Period, on_delete=models.SET_NULL,null=True, blank=True)
    Amount = models.IntegerField()
    Subscribed_Date = models.DateField(auto_now_add=False)
    Subscription_End_Date = models.DateField(auto_now_add=False,null=True,blank=True)
    Batch = models.ForeignKey(Batch_DB, on_delete=models.SET_NULL,null=True, blank=True, related_name="batch_time")
    Batch_Status = models.BooleanField(default=True)
    Payment_Status = models.BooleanField(default=False)

    def __str__(self):
        return str(self.Type_Of_Subscription) + " " + str(self.Period_Of_Subscription)
    

class Payment(models.Model):
    Member = models.ForeignKey(MemberData, on_delete=models.CASCADE)
    Subscription_ID = models.ForeignKey(Subscription, on_delete=models.SET_NULL,null=True,blank=True, related_name="Subscription_payment")
    Amount = models.IntegerField(null=True, blank=True)
    Mode_of_Payment = models.CharField(max_length = 255, null=True, blank= True, choices = (("Cash","Cash"),("Bank Transfer","Bank Transfer"),("Card","Card")) )
    Payment_Date = models.DateField(auto_now_add=False,null=True,blank=True)
    Payment_Balance = models.FloatField(default=0)
    Payment_Status = models.BooleanField(default=False)
    Access_status = models.BooleanField(default=False)

class BalancePayment(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="balance_payment")
    Amount = models.FloatField()
    Payment_Date = models.DateField(auto_now_add=True) 

class AccessToGate(models.Model):
    Member = models.ForeignKey(MemberData, on_delete=models.CASCADE)
    Subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    Validity_Date = models.DateField(auto_now_add=False)
    Status = models.BooleanField(default=False)
    Payment_status = models.BooleanField(default=False)

class Discounts(models.Model):
    Discount_Percentage = models.FloatField()
    Till_Date = models.DateField()




