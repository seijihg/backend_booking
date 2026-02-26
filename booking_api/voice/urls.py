from django.urls import path

from .views import ChatView, TranscribeView

app_name = "voice"
urlpatterns = [
    path("transcribe/", TranscribeView.as_view(), name="transcribe"),
    path("chat/", ChatView.as_view(), name="chat"),
]
