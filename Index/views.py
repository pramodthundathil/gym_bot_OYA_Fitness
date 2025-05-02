from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.contrib.auth import authenticate,login,logout
from Members.models import Subscription_Period, Subscription, Batch_DB, TypeSubsription,MemberData,Payment, AccessToGate, Discounts, BalancePayment
from Members.forms import Subscription_PeriodForm, BatchForm, TypeSubsriptionForm, MemberAddQuickForm, SubscriptionAddForm
from datetime import datetime, timedelta
from django.utils import timezone
from .models import ConfigarationDB, Support
from Members.views import ScheduledTask
from .decorator import unautenticated_user, allowed_users
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from Finance.models import Income, Expence



this_month = timezone.now().month
end_date = timezone.now()
start_date = end_date + timedelta(days=-7)

from datetime import datetime
from django.db.models import Sum


from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
import json

def get_chart_data(request):
    """JSON endpoint for chart data that can be called via AJAX"""
    # Get period from request parameters (default to monthly)
    period = request.GET.get('period', 'monthly')
    
    # Calculate date range for filtering
    end_date = datetime.now().date()
    
    if period == 'monthly':
        start_date = end_date - timedelta(days=180)  # Last 6 months
        date_trunc = TruncMonth('date')
        format_str = '%b %Y'  # Month Year
    elif period == 'weekly':
        start_date = end_date - timedelta(weeks=6)  # Last 6 weeks
        date_trunc = TruncWeek('date')
        format_str = 'Week %W, %Y'  # Week number, Year
    else:  # daily
        start_date = end_date - timedelta(days=30)  # Last 30 days
        date_trunc = TruncDay('date')
        format_str = '%d %b'  # Day Month
    
    # Get income data grouped by period
    income_data = Income.objects.filter(
        date__gte=start_date, 
        date__lte=end_date
    ).annotate(
        period=date_trunc
    ).values('period').annotate(
        total=Sum('amount')
    ).order_by('period')
    
    # Get expense data grouped by period
    expense_data = Expence.objects.filter(
        date__gte=start_date, 
        date__lte=end_date
    ).annotate(
        period=date_trunc
    ).values('period').annotate(
        total=Sum('amount')
    ).order_by('period')
    
    # Prepare data for the chart
    labels = []
    income_amounts = []
    expense_amounts = []
    profit_amounts = []
    
    # Create a dictionary for quick lookup
    income_dict = {item['period']: item['total'] for item in income_data}
    expense_dict = {item['period']: item['total'] for item in expense_data}
    
    # Combine all unique periods
    all_periods = sorted(set(list(income_dict.keys()) + list(expense_dict.keys())))
    
    for period_date in all_periods:
        # Format the date according to the period type
        formatted_date = period_date.strftime(format_str)
        labels.append(formatted_date)
        
        # Get amounts (default to 0 if no data for that period)
        income_amount = income_dict.get(period_date, 0)
        expense_amount = expense_dict.get(period_date, 0)
        profit = income_amount - expense_amount
        
        income_amounts.append(income_amount)
        expense_amounts.append(expense_amount)
        profit_amounts.append(profit)
    
    # Calculate totals for summary
    total_income = sum(income_amounts)
    total_expense = sum(expense_amounts)
    total_profit = total_income - total_expense
    
    data = {
        'labels': labels,
        'income': income_amounts,
        'expense': expense_amounts,
        'profit': profit_amounts,
        'summary': {
            'income': total_income,
            'expense': total_expense,
            'profit': total_profit
        }
    }
    
    return JsonResponse(data)

@login_required(login_url='SignIn')
def Home(request):
    # Get the first 8 subscribers in reverse order directly
    form = MemberAddQuickForm()
    sub_form = SubscriptionAddForm()
    subscribers = Subscription.objects.order_by('-id')[:8]
    subscribers_pending = Subscription.objects.filter(Payment_Status = False).order_by('-id')
    members = MemberData.objects.all()
    month = datetime.now().strftime('%B')
    
    # Assuming start_date and end_date are defined elsewhere in your code
    notification_payments = Payment.objects.filter(Payment_Date__gte=start_date, Payment_Date__lte=end_date)
    disc = Discounts.objects.filter(Till_Date__lte=end_date)

    # Bulk update Payment_Status and AccessToGate status
    subscrib = Subscription.objects.filter(Subscription_End_Date__lte=end_date)
    subscrib.update(Payment_Status=False)

    # access_ids = subscrib.values_list('AccessToGate__id', flat=True)
    AccessToGate.objects.filter(Subscription__in=list(subscrib)).update(Status=False)

    access = AccessToGate.objects.filter(Validity_Date__lte=end_date)
    access.update(Status=False)

    # Aggregate collected amount
    this_month = datetime.now().month
    # collected_amount = Payment.objects.filter(Payment_Date__month=this_month).aggregate(Sum('Amount'))['Amount__sum'] or 0
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    collected_amount = Payment.objects.filter(
        Payment_Date__month=current_month,
        Payment_Date__year=current_year
    ).aggregate(Sum('Amount'))['Amount__sum'] or 0
    # Delete discounts and update member discounts in bulk
    disc.delete()
    members.update(Discount=0)
    
    print("return... the task")
    # Count active members
    active_count = MemberData.objects.filter(Active_status=True).count()

    # Count inactive members
    inactive_count = MemberData.objects.filter(Active_status=False).count()

    context = {
        "subscribers": subscribers,
        "subscribers_pending":subscribers_pending,
        "membercount": members.count(),
        "feepending": Subscription.objects.filter(Payment_Status=False).count(),
        "month": month,
        "collected_amount": collected_amount,
        "notification_payments": notification_payments,
        "notificationcount": notification_payments.count(),
        "current_year":current_year,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "form":form,
        "sub_form":sub_form,
        "members":members,
        'initial_period': 'monthly',
    }


    return render(request, "index.html", context)

# views.py



def get_payment_chart_data(request):
    """JSON endpoint for payment chart data by payment mode"""
    # Get period from request parameters
    period = request.GET.get('period', 'monthly')
    
    # Calculate date range for filtering
    end_date = datetime.now().date()
    
    if period == 'monthly':
        start_date = end_date - timedelta(days=180)  # Last 6 months
        date_trunc = TruncMonth('Payment_Date')
        format_str = '%b %Y'  # Month Year
    elif period == 'weekly':
        start_date = end_date - timedelta(weeks=6)  # Last 6 weeks
        date_trunc = TruncWeek('Payment_Date')
        format_str = 'Week %W, %Y'  # Week number, Year
    else:  # daily
        start_date = end_date - timedelta(days=30)  # Last 30 days
        date_trunc = TruncDay('Payment_Date')
        format_str = '%d %b'  # Day Month
    
    # Get all payment modes
    payment_modes = Payment.objects.exclude(Mode_of_Payment__isnull=True).values_list('Mode_of_Payment', flat=True).distinct()
    
    # Initialize result dictionary
    result = {
        'labels': [],
        'datasets': [],
        'summary': {
            'total_payments': 0,
            'payment_modes': {},
            'balance_payments': 0
        }
    }
    
    # Prepare datasets for each payment mode
    mode_datasets = {}
    for mode in payment_modes:
        mode_datasets[mode] = []
    
    # Add dataset for balance payments
    mode_datasets['Balance'] = []
    
    # Get main payments data grouped by period and payment mode
    payments_data = Payment.objects.filter(
        Payment_Date__gte=start_date,
        Payment_Date__lte=end_date
    ).annotate(
        period=date_trunc
    ).values('period', 'Mode_of_Payment').annotate(
        total=Sum('Amount')
    ).order_by('period', 'Mode_of_Payment')
    
    # Get balance payments data grouped by period
    balance_data = BalancePayment.objects.filter(
        Payment_Date__gte=start_date,
        Payment_Date__lte=end_date
    ).annotate(
        period=date_trunc
    ).values('period').annotate(
        total=Sum('Amount')
    ).order_by('period')
    
    # Create dictionaries for quick lookup
    payments_dict = {}
    for item in payments_data:
        period = item['period']
        mode = item['Mode_of_Payment'] or 'Unknown'
        if period not in payments_dict:
            payments_dict[period] = {}
        payments_dict[period][mode] = item['total']
    
    balance_dict = {item['period']: item['total'] for item in balance_data}
    
    # Combine all unique periods
    all_periods = sorted(set(
        list(payments_dict.keys()) + 
        list(balance_dict.keys())
    ))
    
    # Generate labels and data for each period
    for period_date in all_periods:
        formatted_date = period_date.strftime(format_str)
        result['labels'].append(formatted_date)
        
        # Add data for each payment mode
        for mode in payment_modes:
            if period_date in payments_dict and mode in payments_dict[period_date]:
                mode_datasets[mode].append(payments_dict[period_date][mode])
            else:
                mode_datasets[mode].append(0)
        
        # Add data for balance payments
        balance_amount = balance_dict.get(period_date, 0)
        mode_datasets['Balance'].append(balance_amount)
    
    # Calculate totals for summary
    mode_totals = {}
    total_payments = 0
    
    for mode in payment_modes:
        mode_total = sum(mode_datasets[mode])
        mode_totals[mode] = mode_total
        total_payments += mode_total
    
    balance_total = sum(mode_datasets['Balance'])
    
    # Add datasets to result
    colors = {
        'Cash': 'rgba(46, 204, 113, 0.6)',
        'Bank Transfer': 'rgba(52, 152, 219, 0.6)',
        'Card': 'rgba(155, 89, 182, 0.6)',
        'Balance': 'rgba(231, 76, 60, 0.6)',
        'Unknown': 'rgba(189, 195, 199, 0.6)'
    }
    
    borders = {
        'Cash': 'rgba(46, 204, 113, 1)',
        'Bank Transfer': 'rgba(52, 152, 219, 1)',
        'Card': 'rgba(155, 89, 182, 1)',
        'Balance': 'rgba(231, 76, 60, 1)',
        'Unknown': 'rgba(189, 195, 199, 1)'
    }
    
    # Add dataset for each payment mode
    for mode in list(payment_modes) + ['Balance']:
        result['datasets'].append({
            'label': mode,
            'data': mode_datasets[mode],
            'backgroundColor': colors.get(mode, 'rgba(189, 195, 199, 0.6)'),
            'borderColor': borders.get(mode, 'rgba(189, 195, 199, 1)'),
            'borderWidth': 1
        })
    
    # Update summary
    result['summary']['total_payments'] = total_payments
    result['summary']['payment_modes'] = mode_totals
    result['summary']['balance_payments'] = balance_total
    
    return JsonResponse(result)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def trigger_scheduled_task(request):
    if request.method == 'POST':
        try:
            ScheduledTask()  # Call your function here
            return JsonResponse({'status': 'success', 'message': 'Task executed successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



@login_required(login_url='SignIn')
def Setting_Module(request):

    form = BatchForm()
    sub_form = Subscription_PeriodForm()
    typesub_form = TypeSubsriptionForm()

    batch = Batch_DB.objects.all()
    speriod = Subscription_Period.objects.all()
    Sub_type = TypeSubsription.objects.all()
    try:
        config = ConfigarationDB.objects.all()[0]
    except:
        config = ConfigarationDB.objects.create(
                JWT_IP="192.168.1.1",
                JWT_PORT="8080",
                Call_Back_IP="192.168.1.2",
                Call_Back_Port="9090",
                Admin_Username="admin_user",
                Admin_Password="securepassword123"
            )
        config.save()


    context = {
        "form":form,
        "sub_form":sub_form,
        "batch":batch,
        "speriod":speriod,
        "typesub_form":typesub_form,
        "Sub_type":Sub_type,
        "config":config
    }
    return  render(request, "settings.html",context)

@login_required(login_url='SignIn')
def BatchSave(request):
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Batch Data Saved")
            return redirect("Setting_Module")
        else:
            messages.error(request,"Something Went wrong")
            return redirect("Setting_Module")
    return redirect("Setting_Module")

def Batch_Delete(request,pk):
    batch = Batch_DB.objects.get(id = pk).delete()
    messages.success(request,"Batch Data Deleted")
    return redirect("Setting_Module")


@login_required(login_url='SignIn')
def SubscriptionPeriodSave(request):
    if request.method == "POST":
        form = Subscription_PeriodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Subscription Period Saved")
            return redirect("Setting_Module")
        else:
            messages.error(request,"Something Went wrong")
            return redirect("Setting_Module")
    return redirect("Setting_Module")

@login_required(login_url='SignIn')
def SubScriptionPeriod_Delete(request,pk):
    batch = Subscription_Period.objects.get(id = pk).delete()
    messages.success(request,"Subscription period Data Deleted")
    return redirect("Setting_Module")

def SubscriptionTypeSave(request):
    if request.method == "POST":
        form = TypeSubsriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Subscription Type Saved")
            return redirect("Setting_Module")
        else:
            messages.error(request,"Something Went wrong")
            return redirect("Setting_Module")
    return redirect("Setting_Module")

@login_required(login_url='SignIn')
def SubScriptionType_Delete(request,pk):
    batch = TypeSubsription.objects.get(id = pk).delete()
    messages.success(request,"Subscription Type Deleted")
    return redirect("Setting_Module")


@login_required(login_url='SignIn')
def ChangePassword(request):
    if request.method == "POST":
        oldpass = request.POST["oldpassword"]
        newpass1 = request.POST['newpassword1']
        newpass2 = request.POST['newpassword2']
        user1 = authenticate(request,username = request.user.username,password = oldpass)
        if user1 is not None:
            if newpass1 == newpass2:
                user  = request.user 
                user.set_password(newpass1)
                user.save()
                messages.success(request, "Password Change Success Please Login To Continue..")
                return redirect("SignIn")
            else:
                messages.error(request, "Password not Matching..")
                return redirect("Setting_Module")
        else:
            messages.error(request, "Password is incorrect")
            return redirect("Setting_Module")

    return redirect("Setting_Module")

@login_required(login_url='SignIn')
def DeviceConfig(request,pk):
    conf = ConfigarationDB.objects.get(id = pk)
    if request.method == "POST":
        jwt = request.POST["jwtip"]
        jwt_port = request.POST["jwtport"]
        callip = request.POST["callip"]
        callport = request.POST["callport"]
        adminusr = request.POST["adminusr"]
        adminpswd = request.POST["adminpswd"]

        conf.JWT_IP = jwt
        conf.JWT_PORT = jwt_port
        conf.Call_Back_IP = callip
        conf.Call_Back_Port = callport
        conf.Admin_Username = adminusr
        conf.Admin_Password = adminpswd

        conf.save()
        messages.success(request,"Configuration data updated..")
        return redirect("Setting_Module")

    return redirect("Setting_Module")

    
    

@unautenticated_user
def SignIn(request):
    if request.method == "POST":
        uname = request.POST['uname']
        pswd = request.POST['pswd']
        user = authenticate(request, username=uname, password = pswd)
        if user is not None:
            login(request, user)
            return redirect("Home")
        else:
            messages.error(request, "User Name or Password Incorrect")
            return redirect("SignIn")
    return render(request,"login.html")

def SignOut(request):
    logout(request)
    return redirect(SignIn)

@login_required(login_url='SignIn')
def Search(request):
    if request.method == "POST":
        key = request.POST["key"]
        # Get members matching first or last name
        members1 = MemberData.objects.filter(First_Name__contains=key)
        members2 = MemberData.objects.filter(Last_Name__contains=key)
        
        # Combine using Python sets to remove duplicates
        members_set = set(list(members1) + list(members2))
        members = list(members_set)
        
        # For each member, get the last payment and add it as an attribute
        for member in members:
            last_payment = Payment.objects.filter(Member=member).order_by('-Payment_Date').first()
            member.last_payment = last_payment
        
        context = {
            "member": members
        }
        return render(request, "search.html", context)
    return render(request, "search.html")

def ViewAllActivities(request):
    notification_payments = Payment.objects.filter(Payment_Date__gte = start_date,Payment_Date__lte = end_date )
    context = {
        "notification_payments":notification_payments,
        "notificationcount":notification_payments.count(),

    }
    return render(request,'viewallactivities.html',context)
    
def EditBatch(request,pk):
    if request.method == "POST":
        batch = request.POST["batch"]
        time = request.POST["time"]

        bat = Batch_DB.objects.get(id = pk)
        bat.Batch_Name = batch
        bat.Batch_Time = time
        bat.save()
        messages.success(request, "Batch updated")
        return redirect("Setting_Module")


    return render(request,"editbatch.html")

def EditsubscriptionPeriod(request,pk):
    if request.method == "POST":
        Period = request.POST["peri"]
        Category = request.POST["ten"]

        bat = Subscription_Period.objects.get(id = pk)
        bat.Period = Period
        bat.Category = Category
        bat.save()
        messages.success(request, "Subscription Period Updated")
        return redirect("Setting_Module")

    return render(request,"editsubperiod.html")

def EditSub(request,pk):
    if request.method == "POST":
        sub = request.POST["sub"]
       
        bat = TypeSubsription.objects.get(id = pk)
        bat.Type = sub
        
        bat.save()
        messages.success(request, "Subscription  Updated")
        return redirect("Setting_Module")
     
    return render(request,"editsubscription.html")



# add new staff 

@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def StaffDetails(request):
    users = User.objects.filter(groups__name='staff')
    if request.method == "POST":
        fname = request.POST['fname']
        uname = request.POST['uname']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request,"Password Do not matching....")
            return redirect("StaffDetails")
        elif User.objects.filter(username = uname).exists():
            messages.error(request,"Username already exists please try different username..")
            return redirect("StaffDetails")
        else:
            user = User.objects.create_user(first_name = fname, username = uname, password = password1)
            user.save()
            group = Group.objects.get(name='staff')
            user.groups.add(group)
            messages.success(request,"New Staff Created Please save password {}".format(password1))
            return redirect("StaffDetails")
    context = {
        "users":users
    } 
        
    return render(request,'usermanagement.html',context)

@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DeleteStaffUser(request,pk):
    User.objects.get(id = pk).delete()
    messages.info(request,"User Deleted...")
    return redirect("StaffDetails")


# support for users 

def Supports(request):
    if request.method == "POST":
        name = request.POST['name']
        quary = request.POST['qury']

        support = Support.objects.create(name = name,Quary = quary)
        support.save()

        mail_subject = 'Ticket Generated - EMMY- FITNESS'
        message = render_to_string('emailbody.html', {'name': name,
                                                      "email":quary,
                                                      "date":datetime.now(),
                                                      "message":quary,
                                                      "id":support.id
                                                      })

        email = EmailMessage(mail_subject, message, to=['gopinath.pramod@gmail.com','support@reddefend.ae'])
        email.send(fail_silently=True)
        
        messages.info(request,"Support mail Sent")
        return redirect("Supports")

    return render(request,"support.html")