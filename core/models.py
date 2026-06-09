from dataclasses import dataclass
from typing import List
from enum import Enum


class ScrapingStatus(Enum):
    PENDING: 0
    COMPLETED: 1
    IN_PROGRESS: 2
    FAILED: 3


@dataclass
class RoyalRoadConfig:
    royalroad_url = "https://www.royalroad.com"
    categories = {'best':'https://www.royalroad.com/fictions/best-rated',
                  'trending':'https://www.royalroad.com/fictions/trending',
                  'active':'https://www.royalroad.com/fictions/active-popular',
                  'complete':'https://www.royalroad.com/fictions/complete',
                  'weekly':'https://www.royalroad.com/fictions/weekly-popular',
                  'latest':'https://www.royalroad.com/fictions/latest-updates',
                  'new':'https://www.royalroad.com/fictions/new',
                  'rising':'https://www.royalroad.com/fictions/rising-stars'
                  }


# Data Models (Simple data containers)
@dataclass
class NovelDetailedInfo:
    """Detailed novel info from deep scraping"""
    novel_name : str
    novel_url: str
    author: str
    summary: str
    score: float
    overall_score: float
    style_score: float
    story_score: float
    grammar_score: float
    character_score: float
    total_views: int
    average_views: int
    favourites: int
    ratings: int
    word_count: int
    chapter_count: int
    patreon_name: str
    patreon_url: str
    patreon_lowest_tier: float
    patreon_highest_tier: float
    patreon_subs: float

    # Status fields
    are_reviews_obtained: int
    is_scraped: int

@dataclass
class ScrapingParams:
    """User input parameters"""
    category: str
    num_novels: int


class DatabaseParams:
    """Database params"""
    def __init__(self, db_name:str):
        self.db_name = db_name


