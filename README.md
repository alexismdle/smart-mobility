# Project Title (You can change this)

A brief description of what this project does.

## Project Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and activate a virtual environment:**
    It's recommended to use a virtual environment to manage project dependencies.

    *   For Unix/macOS:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
    *   For Windows:
        ```bash
        python -m venv .venv
        .\.venv\Scripts\activate
        ```
    *(Note: If you have a `.python-version` file and use `pyenv`, the environment might be managed differently. Adjust as needed.)*

3.  **Install dependencies:**
    This project uses `requirement.txt` to list its dependencies.
    ```bash
    pip install -r requirement.txt
    ```

## Running the Application

This project uses Matplotlib to generate a visual representation of the knowledge graph.

To run the application, execute the main script from the root directory of the project:

```bash
python app.py
```
Or, if you typically use `python3`:
```bash
python3 app.py
```

The script will process the data located in `assets/sample_data.json` and generate an image file named `knowledge_graph.png` in the project's root directory. This image contains the visualized graph.

## Dependencies

Project dependencies are listed in `requirement.txt`. They can be installed using pip:
```bash
pip install -r requirement.txt
```
The primary visualization library used is Matplotlib.

## Contributing

[Optional: Add guidelines for contributing to this project.]

## License

[Optional: Add license information for this project.]
