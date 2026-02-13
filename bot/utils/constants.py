from enum import Enum


class ResidentialComplex(str, Enum):
    ALASHA = "alasha"
    TEREKTI = "terekti"
    KEMEL = "kemel"
    JANA_OMIR = "jana_omir"


class TicketStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    WAITING_CLIENT = "waiting_client"
    PENDING_APPROVAL = "pending_approval"  # Car plate waiting for master/admin approval
    MASTER_APPROVED = "master_approved"  # Master approved, waiting for admin
    MASTER_REJECTED = "master_rejected"  # Master rejected
    APPROVED = "approved"  # Admin approved
    REJECTED = "rejected"  # Admin rejected


class TicketCategory(str, Enum):
    CCTV = "cctv"
    FACE_ID = "face_id"
    CAR_PLATE = "car_plate"
    CAMERA_ACCESS = "camera_access"
    INTERCOM = "intercom"
    KEY_MAGNET = "key_magnet"
    OTHER = "other"


class UserRole(str, Enum):
    OWNER = "owner"
    MASTER = "master"
    ADMIN = "admin"


# --- Display names (Russian) ---

COMPLEX_DISPLAY: dict[ResidentialComplex, str] = {
    ResidentialComplex.ALASHA: "ЖК Alasha Residence",
    ResidentialComplex.TEREKTI: "ЖК Terekti Park",
    ResidentialComplex.KEMEL: "ЖК Kemel UI",
    ResidentialComplex.JANA_OMIR: "ЖК Jana Omir",
}

CATEGORY_DISPLAY: dict[TicketCategory, str] = {
    TicketCategory.CCTV: "Системы видеонаблюдения",
    TicketCategory.FACE_ID: "Добавление в базу FACE ID",
    TicketCategory.CAR_PLATE: "Добавление госномера (шлагбаум)",
    TicketCategory.CAMERA_ACCESS: "Доступ к видеокамерам",
    TicketCategory.INTERCOM: "Поломка или установка домофона",
    TicketCategory.KEY_MAGNET: "Прошивка ключа/магнита",
    TicketCategory.OTHER: "Прочее",
}

STATUS_DISPLAY: dict[TicketStatus, str] = {
    TicketStatus.NEW: "Новая",
    TicketStatus.IN_PROGRESS: "В работе",
    TicketStatus.COMPLETED: "Выполнена",
    TicketStatus.CLOSED: "Закрыта",
    TicketStatus.CANCELLED: "Отменена",
    TicketStatus.WAITING_CLIENT: "Ожидание клиента",
    TicketStatus.PENDING_APPROVAL: "На рассмотрении",
    TicketStatus.MASTER_APPROVED: "Одобрено мастером",
    TicketStatus.MASTER_REJECTED: "Отклонено мастером",
    TicketStatus.APPROVED: "Одобрено",
    TicketStatus.REJECTED: "Отклонено",
}

# --- Categories per complex ---

COMPLEX_CATEGORIES: dict[ResidentialComplex, list[TicketCategory]] = {
    ResidentialComplex.ALASHA: [
        TicketCategory.CCTV,
        TicketCategory.FACE_ID,
        TicketCategory.CAR_PLATE,
        TicketCategory.CAMERA_ACCESS,
        TicketCategory.INTERCOM,
        TicketCategory.OTHER,
    ],
    ResidentialComplex.TEREKTI: [
        TicketCategory.KEY_MAGNET,
        TicketCategory.CAMERA_ACCESS,
        TicketCategory.INTERCOM,
        TicketCategory.OTHER,
    ],
    ResidentialComplex.KEMEL: [
        TicketCategory.KEY_MAGNET,
        TicketCategory.CAMERA_ACCESS,
        TicketCategory.INTERCOM,
        TicketCategory.OTHER,
    ],
    ResidentialComplex.JANA_OMIR: [
        TicketCategory.KEY_MAGNET,
        TicketCategory.CAMERA_ACCESS,
        TicketCategory.INTERCOM,
        TicketCategory.OTHER,
    ],
}

# --- Block/entrance ranges per complex ---
# Alasha uses entrances (no blocks), others use blocks

COMPLEX_BLOCKS: dict[ResidentialComplex, tuple[int, int]] = {
    ResidentialComplex.TEREKTI: (14, 39),
    ResidentialComplex.KEMEL: (1, 19),
    ResidentialComplex.JANA_OMIR: (8, 15),
}

ALASHA_ENTRANCES = 20

# --- CCTV sub-types (Alasha only) ---

CCTV_SUBTYPES = [
    "Не работает камера / нет картинки",
    "Проблема с интернетом/подключением",
    "Установка/добавление камеры",
    "Настройка/перенос/ремонт",
    "Другое",
]

# --- Intercom sub-types ---

INTERCOM_SUBTYPES = [
    "Не открывается дверь / не проходит вызов",
    "Нет звука / не работает трубка",
    "Не включается панель / питание",
    "Установка/замена домофона",
    "Нужен ключ/доступ",
    "Другое",
]

# --- Alasha gate entries ---

ALASHA_GATES = [
    "2 заезд (центральный)",
    "3 заезд (нижний)",
]

# --- Camera access instructions ---

INSTRUCTION_HIK_CONNECT = (
    "<b>Доступ к видеокамерам (Hik-Connect) — инструкция</b>\n\n"
    "1. Скачайте приложение <b>Hik-Connect</b>:\n"
    "   • <a href='https://apps.apple.com/ru/app/hik-connect/id1087803190'>iOS (App Store)</a>\n"
    "   • <a href='https://play.google.com/store/apps/details?id=com.connect.enduser&hl=ru'>Android (Google Play)</a>\n\n"
    "2. Откройте приложение и <b>зарегистрируйтесь</b> "
    "(важно: регистрация на вашу почту).\n\n"
    "3. После регистрации нажмите «Продолжить» и отправьте нам вашу "
    "<b>почту (email)</b> — мы выдадим доступ.\n\n"
    "✅ <b>Важно:</b> почта должна быть та же, на которую вы "
    "зарегистрировали Hik-Connect."
)

INSTRUCTION_EASYVIEWER = (
    "<b>Доступ к видеокамерам (EasyViewer) — инструкция</b>\n\n"
    "1. Скачайте приложение <b>EasyViewer</b>:\n"
    "   • <a href='https://apps.apple.com/us/app/easyviewer-plus/id883885959'>iOS (App Store)</a>\n"
    "   • <a href='https://play.google.com/store/apps/details?id=com.mm.android.direct.EasyViewerPro'>Android (Google Play)</a>\n\n"
    "2. Откройте приложение → нажмите «+ Добавить устройство».\n\n"
    "3. Выберите подключение по <b>IP / Domain</b>.\n\n"
    "4. Введите данные, которые мы вам выдадим:\n"
    "   a. IP-адрес регистратора\n"
    "   b. Логин\n"
    "   c. Пароль\n"
    "   d. Порт\n\n"
    "5. Нажмите <b>Сохранить</b> → проверьте, что камеры открываются.\n\n"
    "✅ <b>Важно:</b> доступ выдаётся только собственникам. "
    "Не передавайте пароль третьим лицам."
)
