from django.urls import path 
from .import views 

urlpatterns = [
    path("Home",views.Home,name="Home"),
    path("",views.SignIn,name="SignIn"),
    path("SignOut",views.SignOut,name="SignOut"),
    path("Setting_Module",views.Setting_Module,name="Setting_Module"),
    path("BatchSave",views.BatchSave,name="BatchSave"),
    path("Batch_Delete/<int:pk>",views.Batch_Delete,name="Batch_Delete"),  
    path("SubscriptionPeriodSave",views.SubscriptionPeriodSave,name="SubscriptionPeriodSave"),
    path("SubScriptionPeriod_Delete/<int:pk>",views.SubScriptionPeriod_Delete,name="SubScriptionPeriod_Delete"),  
    path("SubscriptionTypeSave",views.SubscriptionTypeSave,name="SubscriptionTypeSave"),
    path("SubScriptionType_Delete/<int:pk>",views.SubScriptionType_Delete,name="SubScriptionType_Delete"),  
    path("ChangePassword",views.ChangePassword,name="ChangePassword"),
    path("Search",views.Search,name="Search"),
    path("DeviceConfig/<int:pk>",views.DeviceConfig,name="DeviceConfig"),  
    path("ViewAllActivities",views.ViewAllActivities,name="ViewAllActivities"),
    path("EditBatch/<int:pk>",views.EditBatch,name="EditBatch"),  
    path("EditsubscriptionPeriod/<int:pk>",views.EditsubscriptionPeriod,name="EditsubscriptionPeriod"),  
    path("EditSub/<int:pk>",views.EditSub,name="EditSub"),  
    path("StaffDetails",views.StaffDetails,name="StaffDetails"),
    path("DeleteStaffUser/<int:pk>",views.DeleteStaffUser,name="DeleteStaffUser"),  
    path("Supports",views.Supports,name="Supports"),
    path('trigger-task/', views.trigger_scheduled_task, name='trigger-task'),




]
