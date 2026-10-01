from pydantic import BaseModel

class ModelMetadata(BaseModel):
    model_name: str
    model_version: str
    model_type: str
    training_data_version: str
    environment: str