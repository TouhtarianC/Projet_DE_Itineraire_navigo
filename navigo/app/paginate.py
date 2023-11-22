from typing import Generic, List, TypeVar
from pydantic import BaseModel, conint
from pydantic.generics import GenericModel
from fastapi import HTTPException


class PageParams(BaseModel):
    """ Request query params for paginated API. """
    page: conint(ge=1) = 1
    size: conint(ge=1, le=100) = 10


T = TypeVar("T")


class PagedResponseSchema(GenericModel, Generic[T]):
    """Response schema for any paged API."""

    total: int
    page: int
    size: int
    results: List[T]


def paginate(page_params: PageParams, result_list, ResponseSchema: BaseModel) -> PagedResponseSchema[T]:
    """Paginate the response."""
    first_el = (page_params.page-1) * page_params.size
    last_el = (page_params.page) * page_params.size
    # return an error if the page is out of range
    if first_el > len(result_list):
        raise HTTPException(status_code=404, detail="Page out of range")

    return PagedResponseSchema(
        total=len(result_list),
        page=page_params.page,
        size=page_params.size,
        results=result_list[first_el:last_el],
    )
