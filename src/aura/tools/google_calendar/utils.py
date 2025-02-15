"""Google Calendar tool utils."""

from __future__ import annotations

from datetime import datetime
import logging
import os
from typing import List, Optional, Tuple, TYPE_CHECKING

from dateutil import tz
from utils.timezone import get_local_timezone

if TYPE_CHECKING:
    from google.auth.transport.requests import Request  # type: ignore[import]
    from google.oauth2.credentials import Credentials  # type: ignore[import]
    from google.oauth2.service_account import Credentials as ServiceCredentials
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import]
    from googleapiclient.discovery import Resource  # type: ignore[import]
    from googleapiclient.discovery import build as build_resource

logger = logging.getLogger(__name__)


def import_google() -> Tuple[Request, Credentials, ServiceCredentials]:
    """Import google libraries.

    Returns:
        Tuple[Request, Credentials]: Request and Credentials classes.
    """
    try:
        from google.auth.transport.requests import Request  # noqa: F401
        from google.oauth2.credentials import Credentials  # noqa: F401
        from google.oauth2.service_account import Credentials as ServiceCredentials
    except ImportError:
        raise ImportError(
            "You need to install gmail dependencies to use this toolkit. "
            "Try running poetry install --with gmail"
        )
    return Request, Credentials, ServiceCredentials  # type: ignore[return-value]


def import_installed_app_flow() -> InstalledAppFlow:
    """Import InstalledAppFlow class.

    Returns:
        InstalledAppFlow: InstalledAppFlow class.
    """
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise ImportError(
            "You need to install gmail dependencies to use this toolkit. "
            "Please, install bigquery dependency group: "
            "`pip install langchain-google-community[gmail]`"
        )
    return InstalledAppFlow


def import_googleapiclient_resource_builder() -> build_resource:
    """Import googleapiclient.discovery.build function.

    Returns:
        build_resource: googleapiclient.discovery.build function.
    """
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "You need to install all dependencies to use this toolkit. "
            "Try running pip install langchain-google-community"
        )
    return build


DEFAULT_SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_SERVICE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]
DEFAULT_CREDS_TOKEN_FILE = "token.json"
DEFAULT_CLIENT_SECRETS_FILE = "credentials.json"
DEFAULT_SERVICE_ACCOUNT_FILE = "service_account.json"


def get_gmail_credentials(
    token_file: Optional[str] = None,
    client_secrets_file: Optional[str] = None,
    service_account_file: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    use_domain_wide: bool = False,
    delegated_user: Optional[str] = None,
) -> Credentials:
    """Get credentials."""
    if use_domain_wide:
        _, _, ServiceCredentials = import_google()
        service_account_file = service_account_file or DEFAULT_SERVICE_ACCOUNT_FILE
        scopes = scopes or DEFAULT_SERVICE_SCOPES
        credentials = ServiceCredentials.from_service_account_file(
            service_account_file, scopes=scopes
        )

        if delegated_user:
            credentials = credentials.with_subject(delegated_user)

        return credentials
    else:
        # From https://developers.google.com/gmail/api/quickstart/python
        Request, Credentials, _ = import_google()
        InstalledAppFlow = import_installed_app_flow()
        creds = None
        scopes = scopes or DEFAULT_SCOPES
        token_file = token_file or DEFAULT_CREDS_TOKEN_FILE
        client_secrets_file = client_secrets_file or DEFAULT_CLIENT_SECRETS_FILE
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())  # type: ignore[call-arg]
            else:
                # https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application # noqa
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file, scopes
                )
                creds = flow.run_local_server(port=0)

            with open(token_file, "w") as token:
                token.write(creds.to_json())

        return creds


def build_resource_service(
    credentials: Optional[Credentials] = None,
    service_name: str = "calendar",
    service_version: str = "v3",
    use_domain_wide: bool = False,
    delegated_user: Optional[str] = None,
    service_account_file: Optional[str] = None,
    scopes: Optional[List[str]] = None,
) -> Resource:
    """Build a Gmail service."""
    credentials = credentials or get_gmail_credentials(
        use_domain_wide=use_domain_wide,
        delegated_user=delegated_user,
        service_account_file=service_account_file,
        scopes=scopes,
    )
    builder = import_googleapiclient_resource_builder()
    return builder(service_name, service_version, credentials=credentials)


def parse_and_format_datetime(
    start_datetime: str, end_datetime: str, timezone: str = None
) -> Tuple[str, str, str]:
    """
    Parse datetime strings and return RFC3339 formatted strings with timezone.

    Args:
        start_datetime: Start datetime string in format "YYYY-MM-DDTHH:MM:SS"
        end_datetime: End datetime string in format "YYYY-MM-DDTHH:MM:SS"
        timezone: Optional timezone string (e.g. 'America/New_York')

    Returns:
        Tuple of (start_rfc, end_rfc, timezone)
    """
    if timezone is None:
        timezone = str(get_local_timezone())

    start = datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S")
    end = datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M:%S")

    start = start.replace(tzinfo=tz.gettz(timezone))
    end = end.replace(tzinfo=tz.gettz(timezone))

    return start.isoformat(), end.isoformat(), timezone
