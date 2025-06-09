"""
Pagination utilities for the tasks module.
"""

import math
from typing import TypeVar, Generic, List, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""

    items: List[T] = Field(description="List of items for current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    @classmethod
    def create(
        cls, items: List[T], total: int, pagination: PaginationParams
    ) -> "PaginatedResponse[T]":
        """
        Create paginated response from items and pagination params.

        Args:
            items: List of items for current page
            total: Total number of items
            pagination: Pagination parameters

        Returns:
            PaginatedResponse instance
        """
        total_pages = math.ceil(total / pagination.page_size) if total > 0 else 0

        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1,
        )


def paginate_query(query: Query, pagination: PaginationParams) -> tuple[List[Any], int]:
    """
    Apply pagination to a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        pagination: Pagination parameters

    Returns:
        Tuple of (items, total_count)
    """
    # Get total count before applying pagination
    total = query.count()

    # Apply pagination
    items = query.offset(pagination.offset).limit(pagination.limit).all()

    return items, total


class SortParams(BaseModel):
    """Standard sorting parameters."""

    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

    def apply_to_query(self, query: Query, model_class: type) -> Query:
        """
        Apply sorting to a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object
            model_class: SQLAlchemy model class

        Returns:
            Query with sorting applied
        """
        if hasattr(model_class, self.sort_by):
            sort_column = getattr(model_class, self.sort_by)
            if self.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        return query


class SearchParams(BaseModel):
    """Standard search parameters."""

    search: str = Field(None, description="Search term")
    search_fields: List[str] = Field(
        default_factory=list, description="Fields to search in"
    )

    def apply_to_query(self, query: Query, model_class: type) -> Query:
        """
        Apply search to a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object
            model_class: SQLAlchemy model class

        Returns:
            Query with search applied
        """
        if not self.search or not self.search_fields:
            return query

        from sqlalchemy import or_

        search_term = f"%{self.search}%"
        search_conditions = []

        for field in self.search_fields:
            if hasattr(model_class, field):
                column = getattr(model_class, field)
                search_conditions.append(column.ilike(search_term))

        if search_conditions:
            query = query.filter(or_(*search_conditions))

        return query


class FilterParams(BaseModel):
    """Base class for filter parameters."""

    def apply_to_query(self, query: Query) -> Query:
        """
        Apply filters to a SQLAlchemy query.
        Override this method in subclasses.

        Args:
            query: SQLAlchemy query object

        Returns:
            Query with filters applied
        """
        return query

    def get_active_filters(self) -> dict:
        """Get dictionary of active filters (non-None values)."""
        return {
            key: value for key, value in self.model_dump().items() if value is not None
        }


class QueryBuilder:
    """Helper class for building complex queries with pagination, sorting, and filtering."""

    def __init__(self, base_query: Query, model_class: type):
        self.query = base_query
        self.model_class = model_class

    def add_filters(self, filters: FilterParams) -> "QueryBuilder":
        """Add filters to the query."""
        self.query = filters.apply_to_query(self.query)
        return self

    def add_search(self, search: SearchParams) -> "QueryBuilder":
        """Add search to the query."""
        self.query = search.apply_to_query(self.query, self.model_class)
        return self

    def add_sorting(self, sort: SortParams) -> "QueryBuilder":
        """Add sorting to the query."""
        self.query = sort.apply_to_query(self.query, self.model_class)
        return self

    def paginate(self, pagination: PaginationParams) -> tuple[List[Any], int]:
        """Apply pagination and return results."""
        return paginate_query(self.query, pagination)

    def execute(self) -> List[Any]:
        """Execute the query and return all results."""
        return self.query.all()

    def count(self) -> int:
        """Get the count of results."""
        return self.query.count()


# Utility functions for common pagination patterns
def create_paginated_response(
    items: List[T], total: int, page: int, page_size: int
) -> PaginatedResponse[T]:
    """
    Create a paginated response from raw data.

    Args:
        items: List of items
        total: Total count
        page: Current page
        page_size: Page size

    Returns:
        PaginatedResponse instance
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    return PaginatedResponse.create(items, total, pagination)


def calculate_pagination_info(total: int, page: int, page_size: int) -> dict:
    """
    Calculate pagination information.

    Args:
        total: Total number of items
        page: Current page
        page_size: Page size

    Returns:
        Dictionary with pagination info
    """
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "start_item": (page - 1) * page_size + 1 if total > 0 else 0,
        "end_item": min(page * page_size, total),
    }
