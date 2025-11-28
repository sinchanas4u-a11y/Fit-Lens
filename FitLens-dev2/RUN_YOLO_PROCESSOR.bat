@echo off
echo ========================================
echo YOLOv8 + MediaPipe Image Processor
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv311\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv311\Scripts\activate.bat
)

echo.
echo Usage Examples:
echo   1. Process single image:
echo      python process_images_yolo.py image1.jpg
echo.
echo   2. Process multiple images:
echo      python process_images_yolo.py image1.jpg image2.jpg image3.jpg
echo.
echo   3. With reference size calibration:
echo      python process_images_yolo.py image1.jpg --reference-size 170
echo.
echo   4. Display results:
echo      python process_images_yolo.py image1.jpg --display
echo.
echo ========================================
echo.

REM Check if images were provided as arguments
if "%~1"=="" (
    echo ERROR: No images provided!
    echo.
    echo Please provide image paths as arguments:
    echo   RUN_YOLO_PROCESSOR.bat image1.jpg image2.jpg image3.jpg
    echo.
    pause
    exit /b 1
)

REM Run the processor with all provided arguments
python process_images_yolo.py %*

echo.
echo ========================================
echo Processing complete!
echo Check the 'output' folder for results.
echo ========================================
pause
