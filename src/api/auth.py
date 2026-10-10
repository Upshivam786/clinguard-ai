import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext


SECRET_KEY = os.getenv(
    "CLINGUARD_JWT_SECRET",
    "change-this-development-secret",
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


# Demo users for the portfolio project.
# Passwords are stored as bcrypt hashes.
USERS = {
    "clinician": {
        "username": "clinician",
        "role": "clinician",
        "password_hash": pwd_context.hash(
            os.getenv(
                "CLINGUARD_CLINICIAN_PASSWORD",
                "clinician-demo",
            )
        ),
    },
    "admin": {
        "username": "admin",
        "role": "admin",
        "password_hash": pwd_context.hash(
            os.getenv(
                "CLINGUARD_ADMIN_PASSWORD",
                "admin-demo",
            )
        ),
    },
}


def authenticate_user(
    username: str,
    password: str,
):
    user = USERS.get(username)

    if not user:
        return None

    if not pwd_context.verify(
        password,
        user["password_hash"],
    ):
        return None

    return user


def create_access_token(
    username: str,
    role: str,
):
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "role": role,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        username = payload.get("sub")
        role = payload.get("role")

        if not username or not role:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = USERS.get(username)

    if not user:
        raise credentials_exception

    return {
        "username": username,
        "role": role,
    }



def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Required environment variable {name} is not configured."
        )
    return value


SECRET_KEY = require_env("CLINGUARD_JWT_SECRET")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)

# Demo users for this portfolio project.
# Passwords are stored as bcrypt hashes.
USERS = {
    "clinician": {
        "username": "clinician",
        "role": "clinician",
        "password_hash": pwd_context.hash(
            require_env("CLINGUARD_CLINICIAN_PASSWORD")
        ),
    },
    "admin": {
        "username": "admin",
        "role": "admin",
        "password_hash": pwd_context.hash(
            require_env("CLINGUARD_ADMIN_PASSWORD")
        ),
    },
}
