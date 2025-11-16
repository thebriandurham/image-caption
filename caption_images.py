#!/usr/bin/env python3
"""
Image Caption Script using Ollama
Processes all images in /images/ folder and generates captions using qwen3-vl:4b-instruct model.
"""

import os
import sys
import base64
import time
import re
import argparse
from pathlib import Path
from datetime import datetime
import ollama


def is_macos_screenshot_filename(filename):
    """Check if filename matches macOS screenshot format: 'Screenshot YYYY-MM-DD at HH.MM.SS'."""
    # Pattern: Screenshot (case-insensitive) + space + date (YYYY-MM-DD) + space + "at" + space + time (HH.MM.SS)
    pattern = r'(?i)^Screenshot \d{4}-\d{2}-\d{2} at \d{2}\.\d{2}\.\d{2}'
    return bool(re.match(pattern, filename))


def get_image_files(images_dir):
    """Get all image files matching macOS screenshot filename format from the images directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    # Support both relative and absolute paths
    images_path = Path(images_dir).expanduser().resolve()
    
    if not images_path.exists():
        print(f"Error: Directory '{images_path}' does not exist.")
        sys.exit(1)
    
    for file_path in images_path.iterdir():
        # Only process files matching macOS screenshot filename format
        if (file_path.is_file() and 
            file_path.suffix.lower() in image_extensions and
            is_macos_screenshot_filename(file_path.stem)):
            image_files.append(file_path)
    
    return sorted(image_files)


def log_error(error_log_path, image_path, error_message):
    """Log error to error log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(error_log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {image_path}: {error_message}\n")


def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def caption_image(image_path, model_name="qwen3-vl:4b-instruct", ollama_client=None):
    """Generate caption for an image using Ollama."""
    prompt = """Describe this image in detail. If this is a screenshot of a computer interface, application, or program:
- Identify the application, program, or website being shown
- Read and include any visible text, window titles, menu items, or UI labels
- Describe the specific content, data, or interface elements displayed
- Note any error messages, dialogs, or notifications
- Include technical details like file paths, URLs, or configuration shown

If this is a regular photo or image, describe the visual content, people, objects, and scene.

Provide a clear and comprehensive caption."""
    
    try:
        # Encode image to base64
        image_base64 = encode_image(image_path)
        
        # Use custom client if provided, otherwise use default
        client = ollama_client if ollama_client else ollama
        
        response = client.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                    'images': [image_base64]
                }
            ]
        )
        
        caption = response['message']['content'].strip()
        return caption
    except Exception as e:
        raise Exception(f"Ollama API error: {str(e)}")


def generate_filename(image_path, model_name="qwen3-vl:4b-instruct", ollama_client=None):
    """Generate a descriptive filename for an image using Ollama."""
    prompt = """Look at this image and generate a concise, descriptive filename (without extension) that best describes its content.

If this is a screenshot of a computer interface, application, or program:
- Include the application/program name (e.g., chrome, vscode, terminal, excel)
- Include the main content or purpose shown (e.g., settings-page, error-dialog, code-editor)
- Include key identifiers like page titles, file names, or specific features visible
- Examples: "chrome-security-settings", "vscode-python-debugger", "terminal-git-status"

If this is a regular photo or image:
- Focus on the main subject, people, objects, or scene
- Include location or context if relevant

The filename should be:
- Short and descriptive (ideally 3-8 words)
- Use lowercase letters, numbers, and hyphens only
- No spaces (use hyphens instead)
- No special characters except hyphens

Respond with ONLY the filename, nothing else."""
    
    try:
        # Encode image to base64
        image_base64 = encode_image(image_path)
        
        # Use custom client if provided, otherwise use default
        client = ollama_client if ollama_client else ollama
        
        response = client.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                    'images': [image_base64]
                }
            ]
        )
        
        filename = response['message']['content'].strip()
        # Clean up the filename - remove any quotes, newlines, and sanitize
        filename = filename.strip('"\'')
        filename = re.sub(r'[^\w\-]', '-', filename)  # Replace invalid chars with hyphens
        filename = re.sub(r'-+', '-', filename)  # Replace multiple hyphens with single
        filename = filename.strip('-')  # Remove leading/trailing hyphens
        
        # Ensure filename is not empty
        if not filename:
            filename = "untitled"
        
        return filename
    except Exception as e:
        raise Exception(f"Ollama API error: {str(e)}")


def sanitize_filename(filename):
    """Sanitize filename to ensure it's filesystem-safe."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
    # Replace multiple spaces/hyphens with single hyphen
    filename = re.sub(r'[\s\-]+', '-', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length (keep it reasonable)
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def prompt_user_after_failures(image_name):
    """Prompt user for action after 3 failed attempts."""
    print(f"\n  ⚠ File '{image_name}' failed after 3 attempts.")
    print("  What would you like to do?")
    print("  1. Stop and exit")
    print("  2. Return to 3 tries loop (retry)")
    print("  3. Step-over this file (skip to next)")
    
    while True:
        try:
            choice = input("  Enter your choice (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                return choice
            else:
                print("  Invalid choice. Please enter 1, 2, or 3.")
        except (EOFError, KeyboardInterrupt):
            # Handle Ctrl+C or EOF gracefully
            print("\n  Interrupted. Exiting...")
            return '1'  # Default to exit on interruption


def process_images(images_dir="images", model_name="qwen3-vl:4b-instruct", mode="caption", ollama_host=None):
    """Process all images in the directory based on the specified mode."""
    # Support both relative and absolute paths
    images_dir_path = Path(images_dir).expanduser().resolve()
    error_log_path = images_dir_path / "error_log.txt"
    
    # Create Ollama client with custom host if provided
    ollama_client = None
    if ollama_host:
        ollama_client = ollama.Client(host=ollama_host)
        print(f"Using Ollama host: {ollama_host}")
    else:
        print(f"Using Ollama host: http://localhost:11434 (default)")
    
    # Clear existing error log
    if error_log_path.exists():
        error_log_path.unlink()
    
    image_files = get_image_files(images_dir)
    
    if not image_files:
        print(f"No image files matching macOS screenshot filename format found in '{images_dir}'.")
        return
    
    mode_display = "captioning" if mode == "caption" else "renaming"
    print(f"Found {len(image_files)} image(s) to process.")
    print(f"Mode: {mode} ({mode_display})")
    print(f"Using model: {model_name}\n")
    
    i = 0
    while i < len(image_files):
        image_path = image_files[i]
        i += 1
        print(f"[{i}/{len(image_files)}] Processing: {image_path.name}")
        
        max_retries = 3
        result = None
        last_error = None
        error_logged = False
        
        while True:  # Loop until success or user chooses to skip/exit
            for attempt in range(1, max_retries + 1):
                try:
                    if mode == "caption":
                        # Generate caption
                        result = caption_image(image_path, model_name, ollama_client)
                    elif mode == "name":
                        # Generate filename
                        result = generate_filename(image_path, model_name, ollama_client)
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        print(f"  ⚠ Attempt {attempt} failed, waiting 5s before retry... ({str(e)})")
                        time.sleep(5)
                    else:
                        print(f"  ✗ Failed after {max_retries} attempts: {str(e)}")
            
            # If we got a result, break out of the retry loop
            if result is not None:
                break
            
            # After 3 failed attempts, prompt user
            user_choice = prompt_user_after_failures(image_path.name)
            
            if user_choice == '1':
                # Stop and exit
                print("\nStopping processing as requested.")
                # Log the error before exiting
                if not error_logged:
                    error_msg = str(last_error)
                    log_error(error_log_path, image_path.name, error_msg)
                return
            elif user_choice == '2':
                # Return to 3 tries loop - continue the while True loop
                print("  Retrying with 3 attempts...")
                continue
            elif user_choice == '3':
                # Step-over the file - break out of retry loop, continue to next file
                print(f"  ⊘ Skipping file: {image_path.name}")
                error_msg = f"Skipped by user after 3 failed attempts. Last error: {str(last_error)}"
                log_error(error_log_path, image_path.name, error_msg)
                error_logged = True
                result = None  # Ensure result is None so we skip processing
                break
        
        if result is not None:
            if mode == "caption":
                # Write caption to .txt file
                txt_path = image_path.with_suffix('.txt')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                print(f"  ✓ Caption saved to: {txt_path.name}")
            elif mode == "name":
                # Rename the file
                sanitized_name = sanitize_filename(result)
                
                # Edge case: Empty filename after sanitization
                if not sanitized_name:
                    error_msg = "Generated filename is empty after sanitization"
                    print(f"  ✗ {error_msg}")
                    log_error(error_log_path, image_path.name, error_msg)
                    continue
                
                new_path = image_path.parent / f"{sanitized_name}{image_path.suffix}"
                
                # Edge case: Skip if filename is unchanged (case-insensitive check)
                if new_path.name.lower() == image_path.name.lower():
                    print(f"  ⊘ Filename unchanged, skipping: {image_path.name}")
                    continue
                
                # Handle filename conflicts with counter
                counter = 1
                original_new_path = new_path
                max_attempts = 1000  # Prevent infinite loops
                
                # Check for conflicts (case-insensitive on case-insensitive filesystems)
                while counter <= max_attempts:
                    # Check if file exists (case-sensitive check)
                    if new_path.exists():
                        # If it's the same file we're renaming, we can proceed
                        if new_path.resolve() == image_path.resolve():
                            break
                        # Otherwise, try next counter
                        new_path = image_path.parent / f"{sanitized_name}-{counter}{image_path.suffix}"
                        counter += 1
                    else:
                        # Also check case-insensitive match (for case-insensitive filesystems)
                        # List files in directory and check case-insensitive match
                        existing_files = [f.name.lower() for f in image_path.parent.iterdir() if f.is_file()]
                        if new_path.name.lower() in existing_files:
                            new_path = image_path.parent / f"{sanitized_name}-{counter}{image_path.suffix}"
                            counter += 1
                        else:
                            break
                
                if counter > max_attempts:
                    error_msg = f"Could not find available filename after {max_attempts} attempts"
                    print(f"  ✗ {error_msg}")
                    log_error(error_log_path, image_path.name, error_msg)
                    continue
                
                try:
                    image_path.rename(new_path)
                    if new_path != original_new_path:
                        print(f"  ✓ Renamed to: {new_path.name} (conflict resolved with counter)")
                    else:
                        print(f"  ✓ Renamed to: {new_path.name}")
                except Exception as e:
                    error_msg = f"Failed to rename file: {str(e)}"
                    print(f"  ✗ {error_msg}")
                    log_error(error_log_path, image_path.name, error_msg)
        else:
            # Log error after all retries failed (only if not already logged)
            if not error_logged and last_error is not None:
                error_msg = str(last_error)
                log_error(error_log_path, image_path.name, error_msg)
    
    print(f"\nProcessing complete!")
    if error_log_path.exists() and error_log_path.stat().st_size > 0:
        print(f"Errors logged to: {error_log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process images with Ollama vision model to generate captions or rename files. Only processes files matching macOS screenshot filename format (e.g., 'Screenshot 2025-11-16 at 18.23.47')."
    )
    parser.add_argument(
        "images_dir",
        nargs="?",
        default="images",
        help="Directory containing images (supports relative and absolute paths, default: 'images')"
    )
    parser.add_argument(
        "-mode",
        choices=["caption", "name"],
        default="caption",
        help="Processing mode: 'caption' generates .txt caption files, 'name' renames images with descriptive filenames (default: 'caption')"
    )
    parser.add_argument(
        "-host",
        "--ollama-host",
        dest="ollama_host",
        default=None,
        help="Ollama server host URL (e.g., 'http://192.168.1.100:11434'). If not specified, uses localhost (default: 'http://localhost:11434')"
    )
    
    args = parser.parse_args()
    process_images(args.images_dir, mode=args.mode, ollama_host=args.ollama_host)

