"""Tests for bot.utils.pagination module."""
import pytest

from bot.utils.pagination import paginate, PER_PAGE


class TestPaginate:
    def test_first_page(self):
        offset, limit, total_pages = paginate(total=25, page=1)
        assert offset == 0
        assert limit == PER_PAGE
        assert total_pages == 5

    def test_middle_page(self):
        offset, limit, total_pages = paginate(total=25, page=3)
        assert offset == 10
        assert limit == PER_PAGE
        assert total_pages == 5

    def test_last_page(self):
        offset, limit, total_pages = paginate(total=25, page=5)
        assert offset == 20
        assert limit == PER_PAGE
        assert total_pages == 5

    def test_page_out_of_range_clamped(self):
        offset, limit, total_pages = paginate(total=25, page=100)
        assert total_pages == 5
        assert offset == 20  # clamped to last page

    def test_page_zero_clamped_to_first(self):
        offset, limit, total_pages = paginate(total=25, page=0)
        assert offset == 0

    def test_negative_page_clamped(self):
        offset, limit, total_pages = paginate(total=25, page=-5)
        assert offset == 0

    def test_single_item(self):
        offset, limit, total_pages = paginate(total=1, page=1)
        assert total_pages == 1
        assert offset == 0

    def test_zero_items(self):
        offset, limit, total_pages = paginate(total=0, page=1)
        assert total_pages == 1
        assert offset == 0

    def test_custom_per_page(self):
        offset, limit, total_pages = paginate(total=30, page=2, per_page=10)
        assert offset == 10
        assert limit == 10
        assert total_pages == 3

    def test_partial_last_page(self):
        offset, limit, total_pages = paginate(total=22, page=5)
        assert total_pages == 5  # ceil(22/5) = 5

    def test_exact_multiple(self):
        offset, limit, total_pages = paginate(total=20, page=4)
        assert total_pages == 4
        assert offset == 15
