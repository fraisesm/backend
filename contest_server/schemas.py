from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

class BoundingBox(BaseModel):
    x: float = Field(..., description="X coordinate of the top-left corner")
    y: float = Field(..., description="Y coordinate of the top-left corner")
    width: float = Field(..., description="Width of the bounding box")
    height: float = Field(..., description="Height of the bounding box")
    class_name: str = Field(..., description="Class name of the detected object")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

class Keypoint(BaseModel):
    x: float = Field(..., description="X coordinate of the keypoint")
    y: float = Field(..., description="Y coordinate of the keypoint")
    name: str = Field(..., description="Name of the keypoint (e.g., 'nose', 'left_eye')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

class SegmentationMask(BaseModel):
    mask: List[List[int]] = Field(..., description="2D array representing the segmentation mask")
    class_mapping: Dict[int, str] = Field(..., description="Mapping of mask values to class names")

class TaskAnnotation(BaseModel):
    """Base annotation model that can handle different types of tasks"""
    task_id: int = Field(..., description="ID of the task being annotated")
    task_type: str = Field(..., description="Type of the task (classification, object_detection, etc.)")
    
    # Классификация
    classifications: Optional[List[str]] = Field(None, description="List of detected classes")
    
    # Обнаружение объектов
    bounding_boxes: Optional[List[BoundingBox]] = Field(None, description="List of detected objects with bounding boxes")
    
    # Определение ключевых точек
    keypoints: Optional[List[Keypoint]] = Field(None, description="List of detected keypoints")
    
    # Сегментация
    segmentation: Optional[SegmentationMask] = Field(None, description="Segmentation mask with class mapping")
    
    # Общие метаданные
    confidence: float = Field(
        ..., 
        ge=0.0,
        le=1.0,
        description="Overall confidence score for the annotation"
    )
    processing_time: float = Field(
        ...,
        gt=0,
        description="Time taken to process the task in seconds"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the annotation process"
    )

    class Config:
        schema_extra = {
            "example": {
                "task_id": 1,
                "task_type": "object_detection",
                "bounding_boxes": [
                    {
                        "x": 100,
                        "y": 100,
                        "width": 50,
                        "height": 50,
                        "class_name": "person",
                        "confidence": 0.95
                    }
                ],
                "confidence": 0.95,
                "processing_time": 1.5,
                "metadata": {
                    "model_name": "YOLOv8",
                    "model_version": "1.0.0",
                    "gpu_used": True
                }
            }
        }

class TaskSubmissionRequest(BaseModel):
    task_id: int = Field(..., description="ID of the task being solved")
    annotation: TaskAnnotation = Field(..., description="Annotation data for the task")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the submission")

class TaskSubmissionResponse(BaseModel):
    submission_id: int
    status: str
    received_at: datetime
    message: Optional[str] = None

class ExpectedTaskResponse(BaseModel):
    """Schema describing the expected format of task solutions"""
    annotations: Dict[str, Any] = Field(
        ...,
        description="Annotations for the task. The structure depends on the task type",
        example={
            "bounding_boxes": [
                {"x": 100, "y": 100, "width": 50, "height": 50, "class": "object"},
            ],
            "classifications": ["class1", "class2"],
            "segmentation_mask": [[0, 0, 1], [0, 1, 0]],
        }
    )
    confidence: float = Field(
        ..., 
        description="Confidence score for the solution (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    processing_time: float = Field(
        ...,
        description="Time taken to process the task in seconds",
        gt=0
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the solution process"
    ) 