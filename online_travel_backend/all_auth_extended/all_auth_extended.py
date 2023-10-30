# custom_adapter.py
from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        return f"{emailconfirmation.key}"

    # def is_open_for_signup(self, request):
    #     # Check if a user with the given email already exists before verification
    #     email = self.cleaned_data.get("email")
    #     if email:
    #         if self.user_model.objects.filter(email=email, is_active=False).exists():
    #             return True
    #     return super().is_open_for_signup(request)
