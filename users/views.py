from rest_framework.generics import RetrieveUpdateAPIView

from .models import User
from .serializers import UserSerializer


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
