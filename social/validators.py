from django.core.exceptions import ValidationError

def validate_file_size(file):
    max_size_mb = 100
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File cannot be larger than {max_size_mb}mb")

def validate_image_size(image):
    max_size_mb = 10
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Image cannot be larger than {max_size_mb}mb")
        
