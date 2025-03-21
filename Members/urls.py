from django.urls import path 
from .import views 

urlpatterns = [
    path("Member",views.Member,name="Member"),
    path("Payments",views.Payments,name="Payments"),
    path("MembersSingleView/<int:pk>",views.MembersSingleView,name="MembersSingleView"),
    path("MemberAccess",views.MemberAccess,name="MemberAccess"),
    path("DeletePayment/<int:pk>",views.DeletePayment,name="DeletePayment"),
    path("DeleteMember/<int:pk>",views.DeleteMember,name="DeleteMember"),
    path("UpdateMember/<int:pk>",views.UpdateMember,name="UpdateMember"),
    path("UpdateAccessToken/<int:pk>",views.UpdateAccessToken,name="UpdateAccessToken"),
    path("ChangeSubscription/<int:pk>",views.ChangeSubscription,name="ChangeSubscription"),
    path("ExtendAccessToGate/<int:pk>",views.ExtendAccessToGate,name="ExtendAccessToGate"),
    path("BlockAccess/<int:pk>",views.BlockAccess,name="BlockAccess"),
    path("ProfilephotoUpdate/<int:pk>",views.ProfilephotoUpdate,name="ProfilephotoUpdate"),
    path("AllMembers",views.AllMembers,name="AllMembers"),
    path("AllPayments",views.AllPayments,name="AllPayments"),
    path("AddPaymentFromMemberTab/<int:pk>",views.AddPaymentFromMemberTab,name="AddPaymentFromMemberTab"),
    
    
    path("FullMemberReport",views.FullMemberReport,name="FullMemberReport"),
    path("MonthMemberReport",views.MonthMemberReport,name="MonthMemberReport"),
    path("DateWiseMemberReport",views.DateWiseMemberReport,name="DateWiseMemberReport"),
    path("DateWisePaymentReport",views.DateWisePaymentReport,name="DateWisePaymentReport"),
    path("PaymentReport",views.PaymentReport,name="PaymentReport"),
    path("PaymentReportMonth",views.PaymentReportMonth,name="PaymentReportMonth"),
    path("ReceiptGenerate,<int:pk>",views.ReceiptGenerate,name="ReceiptGenerate"),
    path("PDFprintFullMemberReport",views.PDFprintFullMemberReport,name="PDFprintFullMemberReport"),
    path("PDFprintFullPaymentReport",views.PDFprintFullPaymentReport,name="PDFprintFullPaymentReport"),
    path("PDFmonthMember",views.PDFmonthMember,name="PDFmonthMember"),
    path("PDFmonthpayment",views.PDFmonthpayment,name="PDFmonthpayment"),

    
    path("EditPayment/<int:pk>",views.EditPayment,name="EditPayment"),
    path("Discount",views.Discount,name="Discount"),
    path("DiscountAllAdd",views.DiscountAllAdd,name="DiscountAllAdd"),
    path("DiscountSingleAdd",views.DiscountSingleAdd,name="DiscountSingleAdd"),
    path("DeleteAllDiscounts/<int:pk>",views.DeleteAllDiscounts,name="DeleteAllDiscounts"),
    path("DeletespecialDiscount/<int:pk>",views.DeletespecialDiscount,name="DeletespecialDiscount"),
    path("AddNewPayment",views.AddNewPayment,name="AddNewPayment"),
    path("PostNewPayment/<int:pk>",views.PostNewPayment,name="PostNewPayment"),
    path("AddNewPaymentFromMember/<int:pk>",views.AddNewPaymentFromMember,name="AddNewPaymentFromMember"),
    path("IdphotoUpdate/<int:pk>",views.IdphotoUpdate,name="IdphotoUpdate"),


    path("FeePendingMembers",views.FeePendingMembers,name="FeePendingMembers"),

    
]
