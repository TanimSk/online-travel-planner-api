from django.shortcuts import render



class ConsumerRegistrationView(RegisterView):
    serializer_class = ConsumerCustomRegistrationSerializer
