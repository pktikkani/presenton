import os
from typing import List

from fastapi import HTTPException, UploadFile


def validate_files(
    field,
    nullable: bool,
    multiple: bool,
    max_size: int,
    accepted_types: List[str],
):

    if field:
        files: List[UploadFile] = field if multiple else [field]
        for each_file in files:
            if (max_size * 1024 * 1024) < each_file.size:
                raise HTTPException(
                    400,
                    f"File '{each_file.filename}' exceeded max upload size of {max_size} MB",
                )
            elif each_file.content_type not in accepted_types:
                raise HTTPException(400, f"File '{each_file.filename}' not accepted.")
            
            # Additional validation: check file extension
            allowed_extensions = {
                "application/pdf": [".pdf"],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
                "image/jpeg": [".jpg", ".jpeg"],
                "image/png": [".png"],
                "image/gif": [".gif"],
                "image/webp": [".webp"]
            }
            
            file_ext = os.path.splitext(each_file.filename.lower())[1]
            allowed_exts = allowed_extensions.get(each_file.content_type, [])
            
            if file_ext not in allowed_exts:
                raise HTTPException(
                    400, 
                    f"File extension '{file_ext}' does not match content type '{each_file.content_type}'"
                )

    elif not (field or nullable):
        raise HTTPException(400, "File must be provided.")
