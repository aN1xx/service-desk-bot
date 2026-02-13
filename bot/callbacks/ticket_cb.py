from aiogram.filters.callback_data import CallbackData


class TicketViewCB(CallbackData, prefix="tv"):
    ticket_pk: int


class TicketActionCB(CallbackData, prefix="ta"):
    action: str   # confirm, cancel, edit
    ticket_pk: int = 0


class TicketRateCB(CallbackData, prefix="rate"):
    ticket_pk: int
    stars: int


class MasterActionCB(CallbackData, prefix="ma"):
    ticket_pk: int
    action: str   # accept, complete


class ComplexCB(CallbackData, prefix="cx"):
    value: str


class CategoryCB(CallbackData, prefix="cat"):
    value: str


class BlockCB(CallbackData, prefix="blk"):
    value: str


class EntranceCB(CallbackData, prefix="ent"):
    value: str


class SubCategoryCB(CallbackData, prefix="sub"):
    value: str


class ConfirmCB(CallbackData, prefix="cf"):
    action: str   # send, edit, cancel


class PhotoDoneCB(CallbackData, prefix="pd"):
    kind: str     # attachments, face_id


class KeyCountCB(CallbackData, prefix="kc"):
    value: int


class KeyTypeCB(CallbackData, prefix="kt"):
    value: str    # new, reprogram


class GateCB(CallbackData, prefix="gt"):
    value: str


class CameraInstructionCB(CallbackData, prefix="ci"):
    action: str   # continue, back


class SkipCB(CallbackData, prefix="sk"):
    field: str


class RateCommentCB(CallbackData, prefix="rc"):
    action: str   # add, skip


class InstructionCB(CallbackData, prefix="ins"):
    value: str    # hik, easy


class HasParkingCB(CallbackData, prefix="hp"):
    value: str    # yes, no


class CarPlateApprovalCB(CallbackData, prefix="cpa"):
    ticket_pk: int
    action: str   # approve, reject (for master and admin)
