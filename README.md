# Image Caption

A Python tool that uses vision models through Ollama to automatically generate captions or rename images based on their content. Perfect for organizing screenshots and images with AI-powered descriptions.

## Features

- **Caption Generation**: Automatically generates detailed text captions for images
- **Smart Renaming**: Renames images with descriptive filenames based on their content
- **Screenshot Focus**: Specifically designed to process screenshots, identifying applications, UI elements, and visible text
- **Error Handling**: Robust retry mechanism with error logging
- **Flexible Configuration**: Support for custom Ollama hosts and model selection
- **Batch Processing**: Processes all matching images in a directory automatically

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- The `qwen3-vl:4b-instruct` model (or another compatible vision model) available in Ollama

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd image-caption
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Ensure Ollama is running and pull the required model:
```bash
ollama pull qwen3-vl:4b-instruct
```

## Usage

### Basic Usage

Process images in the default `images/` directory:

```bash
python caption_images.py
```

### Specify Custom Directory

```bash
python caption_images.py /path/to/your/images
```

### Modes

#### Caption Mode (Default)

Generates `.txt` caption files for each image:

```bash
python caption_images.py -mode caption
```

The script will create a `.txt` file next to each image containing a detailed description.

#### Name Mode

Renames images with descriptive filenames based on their content:

```bash
python caption_images.py -mode name
```

Images will be renamed with descriptive, filesystem-safe names (e.g., `chrome-security-settings.png`, `vscode-python-debugger.jpg`).

### Custom Ollama Host

If your Ollama instance is running on a different host:

```bash
python caption_images.py -host http://192.168.1.100:11434
```

Or use the long form:

```bash
python caption_images.py --ollama-host http://192.168.1.100:11434
```

## How It Works

1. **Image Discovery**: The script scans the specified directory for image files (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.tiff`) that contain "screenshot" in their filename (case-insensitive).

2. **Processing**: For each image:
   - Encodes the image to base64
   - Sends it to Ollama with a specialized prompt
   - Receives AI-generated caption or filename
   - Saves the result (caption file or renamed image)

3. **Error Handling**: Failed attempts are retried up to 3 times with a 5-second delay. All errors are logged to `error_log.txt` in the images directory.

## Image Requirements

- Only images with "screenshot" in the filename are processed
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.tiff`, `.tif`
- Images are processed in alphabetical order

## Output

### Caption Mode
- Creates a `.txt` file next to each image with the same base name
- Contains detailed description of the image content
- For screenshots, includes application names, UI elements, visible text, and technical details

### Name Mode
- Renames images with descriptive, filesystem-safe filenames
- Handles filename conflicts by appending a counter (e.g., `-1`, `-2`)
- Skips renaming if the generated name matches the current name

## Error Logging

Errors are logged to `error_log.txt` in the images directory with timestamps. Check this file if any images fail to process.

## Examples

### Example 1: Generate Captions

```bash
python caption_images.py images/
```

This will process all screenshots in `images/` and create caption files like:
- `screenshot-2024-01-15.png` → `screenshot-2024-01-15.txt`

### Example 2: Rename Screenshots

```bash
python caption_images.py images/ -mode name
```

This will rename screenshots based on their content:
- `screenshot-2024-01-15.png` → `chrome-settings-security.png`
- `screenshot-2024-01-16.jpg` → `vscode-python-debugger.jpg`

### Example 3: Remote Ollama Instance

```bash
python caption_images.py ~/Pictures/screenshots -host http://192.168.1.100:11434 -mode caption
```

## Model Information

The default model is `qwen3-vl:4b-instruct`, a 4-billion parameter vision-language model optimized for image understanding and description. You can modify the model in the script if needed.

## Troubleshooting

- **"No image files found"**: Ensure your images have "screenshot" in the filename
- **Connection errors**: Verify Ollama is running (`ollama list` to check)
- **Model not found**: Pull the model with `ollama pull qwen3-vl:4b-instruct`
- **Permission errors**: Ensure you have read/write permissions for the images directory

## License

Whatevs man

