"""Tests for bot.utils.constants — data integrity validation."""
import pytest

from bot.utils.constants import (
    ResidentialComplex,
    TicketCategory,
    TicketStatus,
    COMPLEX_DISPLAY,
    CATEGORY_DISPLAY,
    STATUS_DISPLAY,
    COMPLEX_CATEGORIES,
    COMPLEX_BLOCKS,
    CCTV_SUBTYPES,
    INTERCOM_SUBTYPES,
    ALASHA_GATES,
    ALASHA_ENTRANCES,
)


class TestComplexDisplay:
    def test_all_complexes_have_display(self):
        for rc in ResidentialComplex:
            assert rc in COMPLEX_DISPLAY, f"Missing display name for {rc}"

    def test_display_values_non_empty(self):
        for rc, name in COMPLEX_DISPLAY.items():
            assert name.strip(), f"Empty display name for {rc}"


class TestCategoryDisplay:
    def test_all_categories_have_display(self):
        for cat in TicketCategory:
            assert cat in CATEGORY_DISPLAY, f"Missing display name for {cat}"

    def test_display_values_non_empty(self):
        for cat, name in CATEGORY_DISPLAY.items():
            assert name.strip(), f"Empty display name for {cat}"


class TestStatusDisplay:
    def test_all_statuses_have_display(self):
        for status in TicketStatus:
            assert status in STATUS_DISPLAY, f"Missing display name for {status}"

    def test_display_values_non_empty(self):
        for status, name in STATUS_DISPLAY.items():
            assert name.strip(), f"Empty display name for {status}"


class TestComplexCategories:
    def test_all_complexes_have_categories(self):
        for rc in ResidentialComplex:
            assert rc in COMPLEX_CATEGORIES, f"Missing categories for {rc}"

    def test_categories_not_empty(self):
        for rc, cats in COMPLEX_CATEGORIES.items():
            assert len(cats) > 0, f"Empty categories for {rc}"

    def test_category_values_are_valid(self):
        for rc, cats in COMPLEX_CATEGORIES.items():
            for cat in cats:
                assert isinstance(cat, TicketCategory), f"Invalid category {cat} in {rc}"

    def test_alasha_has_cctv_face_car(self):
        alasha_cats = COMPLEX_CATEGORIES[ResidentialComplex.ALASHA]
        assert TicketCategory.CCTV in alasha_cats
        assert TicketCategory.FACE_ID in alasha_cats
        assert TicketCategory.CAR_PLATE in alasha_cats

    def test_non_alasha_no_face_car(self):
        for rc in [ResidentialComplex.TEREKTI, ResidentialComplex.KEMEL, ResidentialComplex.JANA_OMIR]:
            cats = COMPLEX_CATEGORIES[rc]
            assert TicketCategory.FACE_ID not in cats
            assert TicketCategory.CAR_PLATE not in cats


class TestComplexBlocks:
    def test_all_non_alasha_have_blocks(self):
        for rc in ResidentialComplex:
            if rc != ResidentialComplex.ALASHA:
                assert rc in COMPLEX_BLOCKS, f"Missing blocks for {rc}"

    def test_block_ranges_valid(self):
        for rc, (min_block, max_block) in COMPLEX_BLOCKS.items():
            assert min_block < max_block, f"Invalid block range for {rc}: {min_block}-{max_block}"
            assert min_block >= 1, f"Block min must be >= 1 for {rc}"

    def test_alasha_not_in_blocks(self):
        assert ResidentialComplex.ALASHA not in COMPLEX_BLOCKS


class TestSubtypes:
    def test_cctv_subtypes_not_empty(self):
        assert len(CCTV_SUBTYPES) > 0

    def test_intercom_subtypes_not_empty(self):
        assert len(INTERCOM_SUBTYPES) > 0

    def test_alasha_gates_not_empty(self):
        assert len(ALASHA_GATES) > 0

    def test_alasha_entrances_positive(self):
        assert ALASHA_ENTRANCES > 0

    def test_no_duplicate_cctv_subtypes(self):
        assert len(CCTV_SUBTYPES) == len(set(CCTV_SUBTYPES))

    def test_no_duplicate_intercom_subtypes(self):
        assert len(INTERCOM_SUBTYPES) == len(set(INTERCOM_SUBTYPES))
