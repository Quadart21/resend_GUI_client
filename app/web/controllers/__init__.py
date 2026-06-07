"""HTTP-контроллеры."""

from app.web.controllers.config_controller import ConfigController
from app.web.controllers.mail_controller import MailController
from app.web.controllers.page_controller import PageController

__all__ = ["ConfigController", "MailController", "PageController"]
