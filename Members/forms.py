from django.forms import ModelForm, TextInput, Textarea, FileInput, Select
from .models import MemberData, Subscription, Batch_DB, Subscription_Period, TypeSubsription, Payment
from datetime import datetime

date =  str(datetime.now()).split(" ")[0]


class MemberAddForm(ModelForm):
    class Meta:
        model = MemberData
        fields = [
            "First_Name",
            "Last_Name",
            "Date_Of_Birth",
            "Gender",
            "Mobile_Number",
            "Email",
            "Registration_Date",
            "Access_Token_Id",
            "Photo",
            "Id_Upload",
            "Address",
            "Medical_History",
        ]

        widgets = {
            "First_Name":TextInput(attrs={"class":"form-control"}),
            "Last_Name":TextInput(attrs={"class":"form-control"}),
            "Date_Of_Birth":TextInput(attrs={"class":"form-control","type":"date","max":date}),
            "Gender":Select(attrs={"class":"form-control"}),
            # "Date_Of_Birth":TextInput(attrs={"class":"form-control","type":"date","min":date}),
            "Mobile_Number":TextInput(attrs={"class":"form-control","type":"number"}),
            "Email":TextInput(attrs={"class":"form-control","type":"email"}),
            "Registration_Date":TextInput(attrs={"class":"form-control","type":"date","max":date}),
            # "Address":TextInput(attrs={"class":"form-control",'style': 'height: 3em !importent;'}),
            # "Medical_History":TextInput(attrs={"class":"form-control"}),
            "Photo":FileInput(attrs={"class":"form-control",'accept': 'image/*', 'capture':'camera', "id":"profilePic"}),
            "Id_Upload":FileInput(attrs={"class":"form-control",'accept': 'image/*', 'capture':'camera'}),
            "Access_Token_Id":TextInput(attrs={"class":"form-control"})

        }

class SubscriptionAddForm(ModelForm):
    class Meta:
        model = Subscription
        fields = [
            "Type_Of_Subscription",
            "Period_Of_Subscription",
            "Amount",
            "Subscribed_Date",
            # "Subscription_End_Date",
            "Batch",
        ]

        widgets = {
            "Type_Of_Subscription":Select(attrs={"class":"form-control","required":"required"}),
            "Period_Of_Subscription":Select(attrs={"class":"form-control","required":"required"}),
            "Amount":TextInput(attrs={"class":"form-control","type":"number"}),
            "Subscribed_Date":TextInput(attrs={"class":"form-control","type":"date","max":date}),
            # "Subscription_End_Date":TextInput(attrs={"class":"form-control","type":"date","min":date}),
            "Batch":Select(attrs={"class":"form-control","required":"required"}),

        }

class BatchForm(ModelForm):
    class Meta:
        model = Batch_DB
        fields = ["Batch_Name","Batch_Time"]

        widgets = {
            "Batch_Name":Select(attrs={"class":"form-control"}),
            "Batch_Time":TextInput(attrs={"class":"form-control",'type':"time"}),
        }

class Subscription_PeriodForm(ModelForm):
    class Meta:
        model = Subscription_Period
        fields = ["Period","Category"]

        widgets = {
            "Period":TextInput(attrs={"class":"form-control","type":"number"}),
            "Category":Select(attrs={"class":"form-control"}),
        }

class TypeSubsriptionForm(ModelForm):
    class Meta:
        model = TypeSubsription
        fields = ["Type"]
        widgets = {
           
            "Type":TextInput(attrs={"class":"form-control"}),

        }

class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ["Member", "Payment_Date","Mode_of_Payment"]

        widgets = {

            "Member":Select(attrs={"class":"form-control"}),
            "Amount":TextInput(attrs={"class":"form-control","type":"number"}),
            "Payment_Date":TextInput(attrs={"class":"form-control","type":"date"}),
            "Mode_of_Payment":Select(attrs={"class":"form-control"})
        }


