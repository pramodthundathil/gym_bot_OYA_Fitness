from django.shortcuts import render, redirect
from .forms import MemberAddForm, SubscriptionAddForm, PaymentForm, MemberAddQuickForm
from .models import MemberData, Subscription, Payment, AccessToGate, Discounts
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse
import csv
from django.template.loader import get_template
from xhtml2pdf import pisa
from Index.models import ConfigarationDB
# import requests
import requests
import json
from django.contrib.auth.decorators import login_required
from Index.models import Logo
from Index.decorator import allowed_users



this_month = timezone.now().month
today = timezone.now()
start_date = today + timedelta(days=-5)
end_date = today + timedelta(days=5)
resign_date = today +timedelta(days = -30)

notification_payments = Payment.objects.filter(Payment_Date__gte = start_date,Payment_Date__lte = today,Payment_Date = today )


def ScheduledTask():
    try:
        confdata = ConfigarationDB.objects.get(id=1)
    except ConfigarationDB.DoesNotExist:
        confdata = {
            "JWT_IP": '0',
            "JWT_PORT": "0",
            "Call_Back_IP": '0',
            "Call_Back_Port": "0",
            "Admin_Username": "",
            "Admin_Password": ""
        }

    # Get JWT token on local host Ztehodevice
    url = f'http://http://127.0.0.1:80/jwt-api-token-auth/'
    print(url)
    header1 = {
        'Content-Type': 'application/json'
    }
    token = "nil"
    body = {
        "username": confdata.Admin_Username,
        "password": confdata.Admin_Password
    }
    json_payload = json.dumps(body)

    try:
        response = requests.post(url, headers=header1, data=json_payload)
        if response.status_code == 200:
            print('Request successful!')
            token_dict = response.json()
            token = token_dict['token']
            print(token_dict)
        else:
            print("No connection")
    except requests.RequestException:
        print("No connection........")
    
    urlforapi = 'http://http://127.0.0.1:80/api-token-auth/'
    header2 = {
        'Content-Type': 'application/json',
        'Authorization': f'{token}'
    }
    try:
        tokenresponse = requests.post(urlforapi, headers=header2,data=json_payload)
        if tokenresponse.status_code == 200:
            token_val = tokenresponse.json()
            mytoken = token_val['token']
    except:
        print("No connection...")
        mytoken = 0

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {mytoken}'
    }

    end_date = datetime.now()  # Assuming end_date is current datetime, adjust as necessary
    resign_date = datetime.now()  # Assuming resign_date is current datetime, adjust as necessary

    subscrib = Subscription.objects.filter(Subscription_End_Date__lte=end_date)
    subscriptions_to_update = []
    access_to_update = []

    for subscription in subscrib:
        subscription.Payment_Status = False
        subscriptions_to_update.append(subscription)
        subscription.Member.update_active_status()
        try:
            access = AccessToGate.objects.get(Subscription=subscription)
            access.Status = False
            access_to_update.append(access)
        except AccessToGate.DoesNotExist:
            continue

    Subscription.objects.bulk_update(subscriptions_to_update, ['Payment_Status'])
    AccessToGate.objects.bulk_update(access_to_update, ['Status'])

    acc = AccessToGate.objects.all()

    with requests.Session() as session:
        for access in acc:
            accessid = access.Member.Access_Token_Id
            if access.Status is False:
                url = f"http://127.0.0.1:80/personnel/api/resigns/"
                data = {
                    "employee": accessid,
                    "disableatt": True,
                    "resign_type": 1,
                    "resign_date": str(resign_date),
                    "reason": "Payment Pending",
                }
            else:
                url = f"http://127.0.0.1:80/personnel/api/reinstatement/"
                data = {
                    "resigns": [accessid]
                }

            json_payload = json.dumps(data)

            try:
                response = session.patch(url, headers=headers, data=json_payload)
                if response.status_code == 200:
                    print("Succeed...")
                else:
                    print("Failed.....")
            except requests.RequestException:
                print("No connection from resigns")
                break

    print("workinggggg.....")

            

    
    

# member configarations and subscription add on same method 
# one forign key field is prent in subscription Meber forign key, priod forign key, Batch forgin key

from Finance.models import Income, Expence


@login_required(login_url='SignIn')
def Member(request):
    form = MemberAddQuickForm()
    sub_form = SubscriptionAddForm()
    Trainee = MemberData.objects.all()[:8][::-1]
    subscribers = Subscription.objects.all()[:8][::-1]
    notification_payments = Payment.objects.filter(Payment_Date__gte = start_date, Payment_Date__lte = today)

    if request.method == "POST":
        form = MemberAddQuickForm(request.POST, request.FILES)
        sub_form = SubscriptionAddForm(request.POST)
        if form.is_valid() and sub_form.is_valid():
            member = form.save()
            member.Discount = 0
            member.save()
            
            sub_data = sub_form.save()
            start_dat = sub_data.Subscribed_Date
            
            # Calculate end date based on any category
            if sub_data.Period_Of_Subscription.Category == "Month":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=(sub_data.Period_Of_Subscription.Period * 30))
            elif sub_data.Period_Of_Subscription.Category == "Year":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=(sub_data.Period_Of_Subscription.Period * 365))
            elif sub_data.Period_Of_Subscription.Category == "Week":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=(sub_data.Period_Of_Subscription.Period * 7))
            elif sub_data.Period_Of_Subscription.Category == "Day":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=sub_data.Period_Of_Subscription.Period)
            else:
                # Default fallback - set to 30 days if category is unknown
                sub_data.Subscription_End_Date = start_dat + timedelta(days=30)
                
            sub_data.Member = member
            sub_data.save()
            
            # Now we're sure Subscription_End_Date has a value
            access_gate = AccessToGate.objects.create(
                Member=member,
                Subscription=sub_data,
                Validity_Date=sub_data.Subscription_End_Date
            )
            access_gate.save()
            
            messages.success(request, "New Member Was Added Successfully Please Make Payment")
            return redirect("Member")
        else:
            if not form.is_valid():
                messages.error(request, "Entered Personal Data is Not Validated Please try again")
            if not sub_form.is_valid():
                messages.error(request, "Entered Subscription Data is Not Validated Please try again")
            return redirect("Member")
            
    context = {
        "notification_payments": notification_payments,
        "form": form,
        "sub_form": sub_form,
        "Trainee": Trainee,
        "subscribers": subscribers,
        "notificationcount": notification_payments.count()
    }
    return render(request, "members.html", context)

@login_required(login_url='SignIn')
def MembersSingleView(request,pk):
    member = MemberData.objects.get(id = pk)
    subscription = Subscription.objects.get(Member = member)
    try:
        access = AccessToGate.objects.get(Member = member)
    except:
        access = AccessToGate.objects.create(Member = member,Subscription = subscription,Validity_Date = datetime.now()) 
        access.save()
    sub_form = SubscriptionAddForm()
    payments = Payment.objects.filter(Member = member)
    

    context = {
        "member":member,
        "subscription":subscription,
        'sub_form':sub_form,
        "access":access,
        "notification_payments":notification_payments,
        "payments":payments

    }
    return render(request,"memberssingleview.html",context)

@login_required(login_url='SignIn')
def UpdateMember(request,pk):
    member = MemberData.objects.get(id = pk)
    if request.method == "POST":
        fname = request.POST["fname"]
        lname = request.POST["lname"]
        email = request.POST["email"]
        phone = request.POST["phone"]
        # dob = request.POST.get("dob")
        address = request.POST["address"]
        medical_history = request.POST["mhistory"]
        height = request.POST["height"]
        weight = request.POST["weight"]

        member.First_Name = fname
        member.Last_Name = lname
        # member.Date_Of_Birth = dob
        member.Mobile_Number = phone
        member.Email = email
        member.Address = address
        member.Medical_History = medical_history
        member.Height = height
        member.Weight = weight
        member.save()
        messages.success(request,"User Data Updated..")
        return redirect("MembersSingleView",pk)

    return redirect("MembersSingleView",pk)

@login_required(login_url='SignIn')
def ProfilephotoUpdate(request,pk):
    if request.method == "POST":
        file = request.FILES["photo"]
        member = MemberData.objects.get(id = pk)
        member.Photo.delete()
        member.Photo = file
        member.save()
        messages.success(request, "Photo Changed...")
        return redirect("MembersSingleView",pk)
    return redirect("MembersSingleView",pk)

@login_required(login_url='SignIn')
def IdphotoUpdate(request,pk):
    if request.method == "POST":
        file = request.FILES["photo"]
        member = MemberData.objects.get(id = pk)
        member.Id_Upload.delete()
        member.Id_Upload = file
        member.save()
        messages.success(request, "Id Proof updated...")
        return redirect("MembersSingleView",pk)
    return redirect("MembersSingleView",pk)
    

@login_required(login_url='SignIn')
def UpdateAccessToken(request,pk):
    if request.method == "POST":
        newtoken = request.POST['newtkn']
        member = MemberData.objects.get(id=pk)
        member.Access_Token_Id = newtoken
        member.save()
        messages.info(request,"Token Changed")
        return redirect("MembersSingleView",pk)

    return redirect("MembersSingleView",pk)

@login_required(login_url='SignIn')
def DeleteMember(request,pk):
    member = MemberData.objects.get(id=pk)
    member.Photo.delete()
    member.delete()
    messages.error(request,"Member Data Deleted Success")
    return redirect("Member")

@login_required(login_url='SignIn')
def MemberAccess(request):
    return render(request,"memberaccess.html")



@login_required(login_url='SignIn')
def ChangeSubscription(request,pk):
    print("function Started..................")
    sub_form = SubscriptionAddForm()
    member = MemberData.objects.get(id = pk )

    if request.method == "POST":
        sub_form = SubscriptionAddForm(request.POST)
        if sub_form.is_valid():
            member = MemberData.objects.get(id = pk )
         
            subscription = Subscription.objects.filter(Member = member)
            for i in subscription:
                i.delete()

            sub_data = sub_form.save()
            sub_data.Member = member
            start_dat = sub_data.Subscribed_Date
            if sub_data.Period_Of_Subscription.Category == "Month":
                # days = sub_data.Period_Of_Subscription
                sub_data.Subscription_End_Date = start_dat +timedelta(days = (sub_data.Period_Of_Subscription.Period * 30))
            elif sub_data.Period_Of_Subscription.Category == "Year":
                # days = sub_data.Period_Of_Subscription
                sub_data.Subscription_End_Date = start_dat +timedelta(days = (sub_data.Period_Of_Subscription.Period * 365))
            sub_data.save()



            access = AccessToGate.objects.filter(Member = member)

            for i in access:
                i.delete()

            access_gate = AccessToGate.objects.create(Member = member,Subscription = sub_data,Validity_Date = sub_data.Subscription_End_Date )
            access_gate.save()

            messages.success(request,"Subscription Changed Success..")
            return redirect(MembersSingleView,pk)
            
        messages.error(request,"Form Is not valid")
        return redirect(MembersSingleView,pk)

    context = {
        "sub_form":sub_form,
        "member":member
    }
    return render(request,'changesubscription.html',context)
        
            
@login_required(login_url='SignIn')
def Payments(request):
    form = PaymentForm()
    pay = Payment.objects.all()[:8][::-1]
    sub_today = Subscription.objects.filter(Subscription_End_Date = today,Payment_Status = False)[:8][::-1]
    sub_past = Subscription.objects.filter(Subscription_End_Date__lte = today,Payment_Status = False)[:8][::-1]
    sub_Upcoming = Subscription.objects.filter(Subscription_End_Date__gte = today,Subscription_End_Date__lte = end_date, Payment_Status = False)[:8][::-1]
    member = MemberData.objects.all()
    
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            access = AccessToGate.objects.get(Member = payment.Member)
            sub = Subscription.objects.get(Member = payment.Member)

            payment.Subscription_ID = sub
            payment.Amount = sub.Amount
            payment.Payment_Status = True 
            payment.Access_status = True
            payment.save()
            sub.Payment_Status = True
            sub.save()
            user = payment.Member
            user.Access_status = True
            user.save()
           
            try:
                sub_date = request.POST["sub_extendate"]
                access.Validity_Date = sub_date
                access.save()

            except:
                sub_date = sub.Subscription_End_Date
                access.Validity_Date = sub_date
                access.save()
                
            sub.Subscription_End_Date = sub_date
            sub.save()
            
            if AccessToGate.objects.filter(Validity_Date__gte = today, Member = payment.Member ).exists():
                access.Status = True 
                access.Payment_status = True
            else:
                access.Status = False 
            access.save()
            ScheduledTask()
            messages.success(request,"Payment Updated for member {}".format(user))
            return redirect("Payments")
        else:
            messages.error(request,"Payment Not Updated")
            return redirect("Payments")


    context = {
        "form":form,
        "pay":pay,
        "notification_payments":notification_payments,
        "sub_today":sub_today,
        "sub_past":sub_past,
        "sub_Upcoming":sub_Upcoming,
        "member":member,
    }
    return render(request, "payments.html",context)


# Add this view to your views.py
from django.http import JsonResponse
from django.db.models import Q

def search_members(request):
    search_term = request.GET.get('term', '')
    
    if len(search_term) < 2:
        return JsonResponse([], safe=False)
    
    members = MemberData.objects.filter(
        Q(First_Name__icontains=search_term) | 
        Q(Last_Name__icontains=search_term)
    )
    
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'name': f"{member.First_Name} {member.Last_Name}"
        })
    
    return JsonResponse(results, safe=False)

@login_required(login_url='SignIn')
def AddNewPayment(request):
    if request.method == "POST":
        try:
            mid = request.POST["member"]
            member = MemberData.objects.get(id = mid)
            Sub = Subscription.objects.get(Member = member)

            context = {
                "member":member,
                "sub":Sub,
                "discounted":Sub.Amount - (Sub.Amount*member.Discount)/100
            }
            return render(request,"paymentscreen.html",context)
        except:
            messages.error(request, "Member is not exists")
            return redirect("Payments")
    else:
        messages.info(request, "Please select member to continue...")
        return redirect("Payments")

    
@login_required(login_url='SignIn')
def AddNewPaymentFromMember(request,pk):

    member = MemberData.objects.get(id = pk)
    Sub = Subscription.objects.get(Member = member)

    context = {
        "member":member,
        "sub":Sub,
        "discounted":Sub.Amount - (Sub.Amount*member.Discount)/100
    }
    return render(request,"paymentscreen.html",context)
    

@login_required(login_url='SignIn')
def PostNewPayment(request,pk):

    if request.method == "POST":

        mode = request.POST["mode"]
        date = request.POST["date"]
        member = MemberData.objects.get(id = pk)
        access = AccessToGate.objects.get(Member = member)
        sub = Subscription.objects.get(Member = member)
        payment = Payment.objects.create(Member = member, Subscription_ID = sub,Mode_of_Payment = mode,Payment_Date = date, Amount = sub.Amount - (sub.Amount*member.Discount)/100 )
        payment.save()

        payment.Payment_Status = True 
        payment.Access_status = True
        payment.save()
        sub.Payment_Status = True
        sub.save()
        user = payment.Member
        user.Access_status = True
        user.save()
        

        try:
            sub_date = request.POST.get("sub_extendate")
            if sub_date:
                access.Validity_Date = sub_date
                access.save()
            
                sub.Subscription_End_Date = sub_date
                sub.save()
            else:
                sub_date = sub.Subscription_End_Date
                access.Validity_Date = sub_date
                access.save()

        except:
            sub_date = sub.Subscription_End_Date
            access.Validity_Date = sub_date
            access.save()
           
        sub.Subscription_End_Date = sub_date
        sub.save()

        try:
             
            amount = request.POST.get("Custome_amount")
            if amount:
                payment.Amount = amount
                balance = float(sub.Amount) - float(amount)
                print(balance,"-------------------------------------------------")
                payment.Payment_Balance = balance
                payment.save()
            
            
        except:
            a = 100
    
            
        if AccessToGate.objects.filter(Validity_Date__gte = today, Member = member ).exists():
            access.Status = True 
            access.Payment_status = True
        else:
            access.Status = False 
        access.save()
        ScheduledTask()
        print(payment.Amount,"------------------------------------")

        income = Income.objects.create(perticulers = f"Payment from {member} by {payment.Mode_of_Payment}",amount = payment.Amount,date = date)
        income.save()

        messages.success(request,"Payment Updated for member: {}".format(user))
        return redirect("Payments")

    return redirect("Payments")

from .models import BalancePayment

def make_balance_payment(request, pk):
    payment = Payment.objects.get(id=pk)
    balance = payment.Payment_Balance
    if request.method == "POST":
        payment.Payment_Status = True
        payment.Payment_Balance = 0
        payment.save() 
        balance_bill = BalancePayment.objects.create(payment = payment,Amount = balance)
        balance_bill.save()

        income = Income.objects.create(perticulers = f"Payment from {payment.Member} by {payment.Mode_of_Payment}",amount = balance)
        income.save()
        messages.success(request,"Balance Payment Updated for member {}".format(payment.Member))
        return redirect("AllPayments")

@login_required(login_url='SignIn')
def AddPaymentFromMemberTab(request,pk):
    member = MemberData.objects.get(id = pk)
    if request.method == "POST":
        date = request.POST["pay_date"]
        access = AccessToGate.objects.get(Member = member)
        sub = Subscription.objects.get(Member = member)

        payment = Payment.objects.create(Member = member,Payment_Date = date, Subscription_ID = sub,Amount = sub.Amount,Payment_Status = True,Access_status = True )
        payment.save()
        sub.Payment_Status = True
        sub.save()
        user = member
        user.Access_status = True
        user.save()

        try:
            sub_date = request.POST.get("sub_extendate")
            if sub_date:
                access.Validity_Date = sub_date
                access.save()

        except:
            sub_date = sub.Subscription_End_Date
            access.Validity_Date = sub_date
            access.save()

        
            
        sub.Subscription_End_Date = sub_date
        sub.save()
        if AccessToGate.objects.filter(Validity_Date__gte = today, Member = payment.Member ).exists():
            access.Status = True 
            access.Payment_status = True
        else:
            access.Status = False 
        access.save()
        ScheduledTask()

        income = Income.objects.create(perticulers = f"Payment from {member}",amount = payment.Amount,date = date)
        income.save()
        messages.success(request,"Payment Updated for member {}".format(user))
        return redirect("MembersSingleView",pk)

    context ={
        "member":member
    }
    # messages.success(request, "Payment Added")
    return render(request,"paymentaddsingle.html",context)

# creating receipt for payment 

# @login_required(login_url='SignIn')
# def ReceiptGenerate(request,pk):
#     logo = Logo.objects.get(id = 1)
#     payment  = Payment.objects.get(id = pk)
#     member = payment.Member
#     amount  = payment.Amount
#     payid  = pk
#     payment_date = payment.Payment_Date
#     try:
#         sub_start = payment.Subscription_ID.Subscribed_Date
#         sub_end = payment.Subscription_ID.Subscription_End_Date
#         period = payment.Subscription_ID.Period_Of_Subscription
#     except:
#         sub_start = "Null"
#         sub_end = "Null"
#         period = "Null"
#     template_path = "receipt.html"

#     context = {
#        "member":member,
#        "amount":amount,
#        "payid":payid,
#        "payment_date":payment_date,
#        "sub_start":sub_start,
#        "sub_end":sub_end,
#        "period":period,
#        "pk":pk,
#        "logo":logo
#     }
#     response = HttpResponse(content_type = "application/pdf")
#     response['Content-Disposition'] = 'filename=f"payment_receipt_{member}.pdf"'
#     template = get_template(template_path)
#     html = template.render(context)

#     # create PDF
#     pisa_status = pisa.CreatePDF(html, dest = response)
#     if pisa_status.err:
#         return HttpResponse("we are some erros <pre>" + html + '</pre>')
#     return response


def get_balance_receipt(request, pk):
    """
    Generate a professional PDF receipt for a payment.
    Uses WeasyPrint for higher quality PDF generation with better CSS support.
    """
    # Get necessary data
    logo = Logo.objects.get(id=1)
    balance_ = BalancePayment.objects.get(id=pk)
    payment = balance_.payment
    member = payment.Member
    amount = balance_.Amount
    payid = pk
    payment_date = payment.Payment_Date
    
    try:
        sub_start = payment.Subscription_ID.Subscribed_Date
        sub_end = payment.Subscription_ID.Subscription_End_Date
        period = payment.Subscription_ID.Period_Of_Subscription
    except:
        sub_start = "N/A"
        sub_end = "N/A"
        period = "N/A"
    
    # Generate barcode for receipt
    import barcode
    from barcode.writer import ImageWriter
    import base64
    from io import BytesIO
    
    # Create EAN13 barcode (you can use other formats too)
    ean = barcode.get_barcode_class('code128')
    ean_barcode = ean(f'OYAFITNESS{payid}', writer=ImageWriter())
    
    # Convert barcode to base64 for embedding in HTML
    buffer = BytesIO()
    ean_barcode.write(buffer)
    buffer.seek(0)
    barcode_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Prepare context for template
    context = {
       "member": member,
       "amount": amount,
       "payid": payid,
       "payment_date": payment_date,
       "sub_start": sub_start,
       "sub_end": sub_end,
       "period": period,
       "barcode_image": barcode_image,
       "logo": logo,
       "balance":"balance"
    }
    
    # Render template to HTML
    template_path = "receipt.html"
    template = get_template(template_path)
    html = template.render(context)
    
    # Generate PDF using WeasyPrint for better CSS support
    try:
        from weasyprint import HTML, CSS
        from django.conf import settings
        import os
        
        # Create response object
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{member}_{payid}.pdf"'
        
        # Generate PDF with WeasyPrint
        base_url = request.build_absolute_uri('/')
        pdf = HTML(string=html, base_url=base_url).write_pdf()
        
        # Write PDF to response
        response.write(pdf)
        return response
        
    except ImportError:
        # Fallback to xhtml2pdf if WeasyPrint is not available
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{member}_{payid}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse("We encountered some errors <pre>" + html + '</pre>')
        return response

@login_required(login_url='SignIn')
def ReceiptGenerate(request, pk):
    """
    Generate a professional PDF receipt for a payment.
    Uses WeasyPrint for higher quality PDF generation with better CSS support.
    """
    # Get necessary data
    logo = Logo.objects.get(id=1)
    payment = Payment.objects.get(id=pk)
    member = payment.Member
    amount = payment.Amount
    payid = pk
    payment_date = payment.Payment_Date
    
    try:
        sub_start = payment.Subscription_ID.Subscribed_Date
        sub_end = payment.Subscription_ID.Subscription_End_Date
        period = payment.Subscription_ID.Period_Of_Subscription
    except:
        sub_start = "N/A"
        sub_end = "N/A"
        period = "N/A"
    
    # Generate barcode for receipt
    import barcode
    from barcode.writer import ImageWriter
    import base64
    from io import BytesIO
    
    # Create EAN13 barcode (you can use other formats too)
    ean = barcode.get_barcode_class('code128')
    ean_barcode = ean(f'OYAFITNESS{payid}', writer=ImageWriter())
    
    # Convert barcode to base64 for embedding in HTML
    buffer = BytesIO()
    ean_barcode.write(buffer)
    buffer.seek(0)
    barcode_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Prepare context for template
    context = {
       "member": member,
       "amount": amount,
       "payid": payid,
       "payment_date": payment_date,
       "sub_start": sub_start,
       "sub_end": sub_end,
       "period": period,
       "barcode_image": barcode_image,
       "logo": logo,
       "balance":" "
    }
    
    # Render template to HTML
    template_path = "receipt.html"
    template = get_template(template_path)
    html = template.render(context)
    
    # Generate PDF using WeasyPrint for better CSS support
    try:
        from weasyprint import HTML, CSS
        from django.conf import settings
        import os
        
        # Create response object
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{member}_{payid}.pdf"'
        
        # Generate PDF with WeasyPrint
        base_url = request.build_absolute_uri('/')
        pdf = HTML(string=html, base_url=base_url).write_pdf()
        
        # Write PDF to response
        response.write(pdf)
        return response
        
    except ImportError:
        # Fallback to xhtml2pdf if WeasyPrint is not available
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{member}_{payid}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse("We encountered some errors <pre>" + html + '</pre>')
        return response

@login_required(login_url='SignIn')
def DeletePayment(request,pk):
    Pay = Payment.objects.get(id = pk).delete()
    messages.info(request,"Payment Deleted")
    return redirect("Payments")

@login_required(login_url='SignIn')
def ExtendAccessToGate(request,pk):
    member = MemberData.objects.get(id = pk)
    subscrib = Subscription.objects.get(Member = member)
    if request.method == "POST":
        extention = request.POST['exend']
        access = AccessToGate.objects.get(Member = member)
        access.Validity_Date = extention
        access.Status = True
        access.save()
        subscrib.Subscription_End_Date = extention
        subscrib.save()
        messages.success(request, "Access Granded Till {}".format(extention))
        return redirect(MembersSingleView, pk)
    context = {
        "member":member,
        "notification_payments":notification_payments
    }  
    return render(request,"grandaccessforgate.html",context)

@login_required(login_url='SignIn')
def BlockAccess(request,pk):
    member = MemberData.objects.get(id = pk)
    access = AccessToGate.objects.get(Member = member)
    access.Status = False
    access.save()
    messages.success(request,"Access Status Changed....")
    return redirect(MembersSingleView,pk)

@login_required(login_url='SignIn')
def AllMembers(request):
    members = MemberData.objects.all()[::-1]
    return render(request, "allmembers.html",{"member":members})

@login_required(login_url='SignIn')
def AllPayments(request):
    payments = Payment.objects.all()[::-1]
    return render(request,"allpayments.html",{"payments":payments})



@login_required(login_url='SignIn')
def FeePendingMembers(request):
    subscribers = Subscription.objects.all()

    return render(request,"feependingmembers.html",{"subscribers":subscribers})
# Reports generation

@login_required(login_url='SignIn')
def FullMemberReport(request):
    
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=Memberreportfull{}-{}.csv'.format(date,date_year)
    
    member = MemberData.objects.all().order_by("-Date_Added")
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()
    writer = csv.writer(response)
    writer.writerow(["Sl No",'First_Name',"Last_Name","Date_Of_Birth","Gender","Mobile_Number","Email","Address","Registration_Date","Date_Added","Access_Token","Subscription","Batch"])
    counter = 0
    for i in member:
        sub = Subscription.objects.get(Member = i)
        batch = sub.Batch
        counter +=1
        writer.writerow([counter,i.First_Name,i.Last_Name,i.Date_Of_Birth,i.Gender,i.Mobile_Number,i.Email,i.Address,i.Registration_Date,i.Date_Added,i.Access_Token_Id,sub,batch])
    response.write('\n')  # Move to the next line after the first row
    response.write(f"Doc Number: {TokenU}")  # Write the unique report number to the next line
    return response


@login_required(login_url='SignIn')
def MonthMemberReport(request):
    
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=Memberreportmonth{}-{}.csv'.format(date,date_year)
    counter = 0
    
    member = MemberData.objects.filter(Date_Added__month = date).order_by("-Date_Added")
    
    writer = csv.writer(response)
    writer.writerow(["Sl No",'First_Name',"Last_Name","Date_Of_Birth","Gender","Mobile_Number","Email","Address","Medical_History","Registration_Date","Date_Added","Access_Token"])
    for i in member:
        counter +=1
        writer.writerow([counter,i.First_Name,i.Last_Name,i.Date_Of_Birth,i.Gender,i.Mobile_Number,i.Email,i.Address,i.Medical_History,i.Registration_Date,i.Date_Added,i.Access_Token_Id])

    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()

    response.write('\n')  # Move to the next line after the first row
    response.write(f"Doc Number: {TokenU}")  # Write the unique report number to the next line

    return response

@login_required(login_url='SignIn')
def DateWiseMemberReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=MemberreportDate{}-{}.csv'.format(date,date_year)
    if request.method == "POST":
        sdate = request.POST["sdate"]
        edate = request.POST["enddate"]
        
    counter = 0
    member = MemberData.objects.filter(Date_Added__gte = sdate,Date_Added__lte = edate ).order_by("-Date_Added")
    
    writer = csv.writer(response)
    writer.writerow(["Slno",'First_Name',"Last_Name","Date_Of_Birth","Gender","Mobile_Number","Email","Address","Medical_History","Registration_Date","Date_Added","Access_Token"])
    for i in member:
        counter +=1
        writer.writerow([counter,i.First_Name,i.Last_Name,i.Date_Of_Birth,i.Gender,i.Mobile_Number,i.Email,i.Address,i.Medical_History,i.Registration_Date,i.Date_Added,i.Access_Token_Id])


    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()
    response.write('\n')  # Move to the next line after the first row
    response.write(f"Doc Number: {TokenU}")  # Write the unique report number to the next line
    
    return response


@login_required(login_url='SignIn')
def DateWisePaymentReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=paymentreportDate{}-{}.csv'.format(date,date_year)
    if request.method == "POST":
        sdate = request.POST["sdate"]
        edate = request.POST["enddate"]
        counter = 0
    
        payment = Payment.objects.filter(Payment_Date__gte = sdate,Payment_Date__lte = edate ).order_by("-Payment_Date")
        
        writer = csv.writer(response)
        writer.writerow(["Slno","Member","Subscription_ID","Amount","Payment_Date"])
        for i in payment:
            counter +=1
            writer.writerow([counter,i.Member,i.Subscription_ID,i.Amount,i.Payment_Date])

        def generate_serial_number():
            current_time = datetime.now()
            serial_number = current_time.strftime("%Y%m%d%H%M%S")
            return serial_number
        TokenU = generate_serial_number()
        response.write('\n')  # Move to the next line after the first row
        response.write(f"Doc Number: {TokenU}") 
        return response
    return HttpResponse("No Valid Fiels")
    

def PaymentReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=paymentreportfull{}-{}.csv'.format(date,date_year)
    counter = 0
        
    try:
        payment = Payment.objects.all().order_by("-Payment_Date")
        
        writer = csv.writer(response)
        writer.writerow(["Slno","Member","Subscription_ID","Amount","Payment_Date"])
        for i in payment:
            counter +=1
            writer.writerow([counter,i.Member,i.Subscription_ID,i.Amount,i.Payment_Date])

        
        def generate_serial_number():
            current_time = datetime.now()
            serial_number = current_time.strftime("%Y%m%d%H%M%S")
            return serial_number
        TokenU = generate_serial_number()
        response.write('\n')  # Move to the next line after the first row
        response.write(f"Doc Number: {TokenU}") 

        return response
    except:
        return HttpResponse("No Valid Fiels")
    

@login_required(login_url='SignIn')
def PaymentReportMonth(request):
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=paymentreportmonth{}-{}.csv'.format(date,date_year)
    counter = 0
        
    try:
        payment = Payment.objects.filter(Payment_Date__month = date ).order_by("-Payment_Date")
        
        writer = csv.writer(response)
        writer.writerow(["SlNo","Member","Subscription_ID","Amount","Payment_Date"])
        for i in payment:
            counter += 1
            writer.writerow([counter,i.Member,i.Subscription_ID,i.Amount,i.Payment_Date])

        
        def generate_serial_number():
            current_time = datetime.now()
            serial_number = current_time.strftime("%Y%m%d%H%M%S")
            return serial_number
        TokenU = generate_serial_number()
        response.write('\n')  # Move to the next line after the first row
        response.write(f"Doc Number: {TokenU}") 
        return response
    except:
        return HttpResponse("No Valid Fiels")


@login_required(login_url='SignIn')
def PDFprintFullMemberReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    member = MemberData.objects.all()
    template_path = "reportpdf_fulldata.html"
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()
    context = {
       "member":member,
       "Token":TokenU
    }
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = "filename=Memberreportfull{}-{}.pdf".format(date,date_year)
    template = get_template(template_path)
    html = template.render(context)

    # create PDF
    pisa_status = pisa.CreatePDF(html, dest = response)
    if pisa_status.err:
        return HttpResponse("we are some erros <pre>" + html + '</pre>')
    return response


@login_required(login_url='SignIn')
def PDFprintFullPaymentReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    payment = Payment.objects.all()
    template_path = "reportpdf_fulldata_payment.html"
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()

    context = {
       "payment":payment,
       "Token":TokenU
    }
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = "filename=Paymentreportfull{}-{}.pdf".format(date,date_year)
    template = get_template(template_path)
    html = template.render(context)

    # create PDF
    pisa_status = pisa.CreatePDF(html, dest = response)
    if pisa_status.err:
        return HttpResponse("we are some erros <pre>" + html + '</pre>')
    return response

@login_required(login_url='SignIn')
def PDFmonthMember(request):
    date = timezone.now().month
    date_year = timezone.now().year
    member = MemberData.objects.filter(Date_Added__month = date)
    template_path = "reportPDFmonthMember.html"
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()

    context = {
       "member":member,
       "date":date,
       "Token":TokenU
    }
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = "filename=Memberreportmonth{}-{}.pdf".format(date,date_year)
    template = get_template(template_path)
    html = template.render(context)

    # create PDF
    pisa_status = pisa.CreatePDF(html, dest = response)
    if pisa_status.err:
        return HttpResponse("we are some erros <pre>" + html + '</pre>')
    return response


@login_required(login_url='SignIn')
def PDFmonthpayment(request):
    date = timezone.now().month
    date_year = timezone.now().year
    payment = Payment.objects.filter(Payment_Date__month = date)
    template_path = "reportPDFmonthpayment.html"
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()

    context = {
       "payment":payment,
       "date":date,
       "Token":TokenU
    }
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = "filename=Paymentreportmonth{}-{}.pdf".format(date,date_year)
    template = get_template(template_path)
    html = template.render(context)

    # create PDF
    pisa_status = pisa.CreatePDF(html, dest = response)
    if pisa_status.err:
        return HttpResponse("we are some erros <pre>" + html + '</pre>')
    return response

    

# Payments and now updates after deploy


@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def EditPayment(request,pk):
    mypay = Payment.objects.get(id = pk)
    sub = mypay.Subscription_ID
    print("sub----------------------------",sub)
    if request.method == "POST":
        mode = request.POST["Mode"]
        Amount = request.POST["amount"]
        date = request.POST["date"]

        mypay.Amount = Amount
        print(mypay.Amount)
        try:
            balance = float(sub.Amount) - float(Amount)
            mypay.Payment_Balance = balance
        except:
            pass
        mypay.Mode_of_Payment = mode 
        mypay.Payment_Date = date
        mypay.save()
        messages.success(request,"Payment Data Updated")
        return redirect("Payments")

    context = {
        "mypay":mypay
    }
    return render(request,"editpayment.html",context)


# discounts to members 
@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def Discount(request):
    member = MemberData.objects.all()
    discount = Discounts.objects.all()
    context = {
        "member":member,
        "discount":discount
    }
    return render(request,"discounts.html",context)


@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DiscountAllAdd(request):
    if request.method == "POST":
        dateend = request.POST["dateend"]
        disper  = request.POST["disper"]
        member  = MemberData.objects.filter(Special_Discount = False)
        dis = Discounts.objects.create(Discount_Percentage = disper,Till_Date = dateend)
        dis.save()
        member.update(Discount = disper)
        # member.save()
        messages.success(request,"Discount Applied for all members")
        return redirect("Discount")

    return redirect("Discounts")

@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DiscountSingleAdd(request):
    if request.method == "POST":
        member = MemberData.objects.get(id = request.POST["member"])
        dis = request.POST["disper"]
        member.Discount = dis
        member.Special_Discount = True
        member.save()
        messages.success(request,"Special Discount Applied Members")
        return redirect("Discount")


@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DeleteAllDiscounts(request,pk):
    Discounts.objects.get(id = pk).delete()
    member = MemberData.objects.filter(Special_Discount = False)
    member.update(Discount = 0)
    # member.save()
    messages.success(request,"Discount Deleted")
    return redirect("Discount")

@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DeletespecialDiscount(request,pk):
    member = MemberData.objects.get(id = pk)
    member.Discount = 0
    member.Special_Discount = False
    member.save()
    messages.success(request,"Discount Deleted")
    return redirect("Discount")







    


