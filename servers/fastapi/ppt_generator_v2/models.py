"""V2 Models with flexible validation for LLM outputs"""
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class SlideType(int, Enum):
    TYPE_1 = 1  # Title + Body + Image
    TYPE_2 = 2  # Title + List Items
    TYPE_3 = 3  # Title + List Items + Image
    TYPE_4 = 4  # Title + List Items with Images
    TYPE_5 = 5  # Title + Body + Graph
    TYPE_6 = 6  # Title + Description + List Items
    TYPE_7 = 7  # Title + List Items with Icons
    TYPE_8 = 8  # Title + Description + List Items with Images
    TYPE_9 = 9  # Title + Description + Table + Graph


class GraphType(str, Enum):
    PIE = "pie"
    BAR = "bar"
    LINE = "line"


# Flexible item model that accepts both title and heading
class FlexibleListItem(BaseModel):
    """List item that accepts either 'title' or 'heading' field"""
    heading: Optional[str] = None
    title: Optional[str] = None
    description: str
    image_prompt: Optional[str] = None
    icon_query: Optional[str] = None
    
    @model_validator(mode='after')
    def ensure_heading(self):
        """Ensure we have a heading, using title as fallback"""
        if not self.heading and not self.title:
            self.heading = "Item"  # Default if both missing
        elif not self.heading:
            self.heading = self.title
        return self


# Graph models with flexible validation
class GraphData(BaseModel):
    """Flexible graph data that handles various LLM outputs"""
    # Accept various formats
    labels: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    values: Optional[List[Union[int, float]]] = None
    data: Optional[List[Union[int, float]]] = None
    series: Optional[List[Dict[str, Any]]] = None
    
    @model_validator(mode='after')
    def normalize_data(self):
        """Normalize various graph data formats to consistent structure"""
        # If we have the proper series format, we're good
        if self.series and isinstance(self.series, list):
            return self
            
        # Convert labels/values format
        if self.labels and self.values:
            self.categories = self.labels
            self.series = [{"name": "Data", "data": self.values}]
        elif self.categories and self.data:
            self.series = [{"name": "Data", "data": self.data}]
            
        return self


class Graph(BaseModel):
    """Graph with flexible validation"""
    type: GraphType
    name: Optional[str] = "Chart"
    unit: Optional[str] = ""
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    data: Optional[GraphData] = None
    # Also accept series/categories at top level (common LLM mistake)
    series: Optional[List[Dict[str, Any]]] = None
    categories: Optional[List[str]] = None
    
    @model_validator(mode='after')
    def normalize_graph(self):
        """Normalize graph structure"""
        # Set defaults for axes
        if not self.x_axis:
            self.x_axis = self.name or "X-axis"
        if not self.y_axis:
            self.y_axis = self.unit or "Y-axis"
            
        # Handle data at top level
        if self.series and not self.data:
            self.data = GraphData(series=self.series, categories=self.categories)
            
        # Ensure we have data
        if not self.data:
            self.data = GraphData(series=[])
            
        return self


# Slide content models - very flexible
class SlideContent(BaseModel):
    """Flexible slide content that accepts various formats"""
    title: str
    # Accept body as either string or list
    body: Optional[Union[str, List[FlexibleListItem]]] = None
    # Also accept 'items' as alias for body (common LLM output)
    items: Optional[List[FlexibleListItem]] = None
    description: Optional[str] = None
    image_prompt: Optional[str] = None
    icon_queries: Optional[List[str]] = None  # For type 7
    graph: Optional[Graph] = None
    
    @model_validator(mode='after')
    def normalize_content(self):
        """Normalize content based on what's provided"""
        # Handle items vs body for list types
        if self.items and not self.body:
            self.body = self.items
        return self


class Slide(BaseModel):
    """Flexible slide model"""
    type: int  # Accept as int, will validate range
    content: SlideContent
    notes: Optional[str] = ""
    
    @field_validator('type')
    def validate_type(cls, v):
        if v not in range(1, 10):
            # Default to type 1 if invalid
            return 1
        return v


class Presentation(BaseModel):
    """Complete presentation model"""
    title: str
    slides: List[Slide]
    
    @field_validator('slides')
    def validate_slides(cls, v):
        if not v:
            raise ValueError("Presentation must have at least one slide")
        return v


# Response model for API
class PresentationResponse(BaseModel):
    """API response model"""
    success: bool = True
    presentation: Dict[str, Any]
    message: Optional[str] = None