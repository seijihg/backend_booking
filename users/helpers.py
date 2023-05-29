from rest_framework_simplejwt.tokens import RefreshToken


def generate_tokens(user):
    token = RefreshToken.for_user(user)
    tokens = {"access_token": str(token.access_token), "refresh_token": str(token)}

    return tokens
