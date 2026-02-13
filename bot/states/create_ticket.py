from aiogram.fsm.state import State, StatesGroup


class CreateTicketState(StatesGroup):
    choosing_complex = State()
    choosing_block = State()
    choosing_entrance = State()
    entering_apartment = State()
    choosing_category = State()

    # Category-specific states
    choosing_cctv_subtype = State()
    choosing_intercom_subtype = State()

    # Face ID (Alasha)
    entering_face_id_photos = State()

    # Car plate (Alasha)
    entering_car_plate = State()
    choosing_gate = State()
    choosing_has_parking = State()  # New: yes/no question
    entering_parking_reason = State()  # New: reason if no parking
    uploading_parking_contract = State()  # New: contract photo if has parking
    entering_parking = State()

    # Camera access
    viewing_camera_instruction = State()
    entering_camera_email = State()
    entering_camera_details = State()

    # Key/magnet (Terekti, Kemel, Jana)
    choosing_key_count = State()
    choosing_key_type = State()

    # Common final steps
    entering_description = State()
    uploading_photos = State()
    confirming = State()
