#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil
from PyQt5 import QtWidgets, QtGui, QtCore

# ---- Helper functions ----
def find_blender(path=None):
    """Return Blender executable path."""
    return path or os.environ.get("BLENDER_PATH", "blender")

def get_gazebo_models_dir():
    """Get the Gazebo models directory."""
    return os.path.expanduser("~/.gazebo/models")

def run_pipeline(image_path, output_dir, primitive, blender_exec, width, depth, height, log_func=print):
    """Run Blender wrapping and SDF generation pipeline with log capture."""
    scratch = os.path.abspath("output_tmp")
    if os.path.exists(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch)

    # Convert cm to meters for Blender
    width_m = width / 100.0
    depth_m = depth / 100.0
    height_m = height / 100.0
    
    log_func(f"Dimensions: {width}×{depth}×{height} cm → {width_m:.3f}×{depth_m:.3f}×{height_m:.3f} m")

    # Blender wrap step
    log_func("➡ Running Blender wrap_image_box.py...")
    blender_cmd = [
        blender_exec,
        "--background", "--python", "wrap_image_box.py", "--",
        "--primitive", primitive,
        "--image", os.path.abspath(image_path),
        "--outdir", scratch,
        "--width", str(width_m),    # Now in meters
        "--depth", str(depth_m),    # Now in meters
        "--height", str(height_m)   # Now in meters
    ]
    proc = subprocess.run(blender_cmd, capture_output=True, text=True)
    log_func(proc.stdout)
    if proc.returncode != 0:
        log_func(proc.stderr)
        raise RuntimeError("Blender process failed")

    # Find exported files
    files = os.listdir(scratch)
    dae_file = next((f for f in files if f.endswith(".dae")), None)
    tex_file = next((f for f in files if f.startswith("texture_")), None)
    if not dae_file:
        raise RuntimeError("Blender did not produce a .dae file")
    if not tex_file:
        tex_file = os.path.basename(image_path)
        shutil.copy(image_path, os.path.join(scratch, tex_file))

    dae_path = os.path.join(scratch, dae_file)
    tex_path = os.path.join(scratch, tex_file)

    # SDF generation step
    log_func("➡ Generating SDF model...")
    sdf_cmd = [
        sys.executable,
        "generate_sdf_model.py",
        "--dae", dae_path,
        "--texture", tex_path,
        "--output", os.path.abspath(output_dir)
    ]
    proc2 = subprocess.run(sdf_cmd, capture_output=True, text=True)
    log_func(proc2.stdout)
    if proc2.returncode != 0:
        log_func(proc2.stderr)
        raise RuntimeError("SDF generation failed")

    return output_dir

# ---- GUI ----
class ModelGeneratorGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image → Gazebo Model Generator")
        self.setGeometry(200, 200, 600, 550)
        self.setup_ui()
        
        # Auto-set output to Gazebo models directory
        self.output_folder = get_gazebo_models_dir()
        self.output_label.setText(f"{self.output_folder} (Auto-set to Gazebo models)")
        self.output_label.setStyleSheet("color: green;")

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Image selection
        self.image_label = QtWidgets.QLabel("No image selected")
        self.image_button = QtWidgets.QPushButton("Select Image")
        self.image_button.clicked.connect(self.select_image)

        # Output folder - fixed to Gazebo models directory
        self.output_label = QtWidgets.QLabel("No output folder selected")
        layout.addWidget(QtWidgets.QLabel("Output Folder (Fixed):"))
        layout.addWidget(self.output_label)

        # Model name input - NEW ADDITION
        layout.addWidget(QtWidgets.QLabel("Model Name:"))
        self.model_name_input = QtWidgets.QLineEdit()
        self.model_name_input.setPlaceholderText("Enter custom model name (optional)")
        layout.addWidget(self.model_name_input)

        # Primitive choice
        self.primitive_combo = QtWidgets.QComboBox()
        self.primitive_combo.addItems(["box", "cylinder"])

        # Dimensions inputs - updated ranges for more reasonable sizes
        self.width_input = QtWidgets.QDoubleSpinBox()
        self.width_input.setRange(1.0, 500.0)  # 1cm to 5m
        self.width_input.setValue(20.0)        # More reasonable default
        self.width_input.setSuffix(" cm")

        self.depth_input = QtWidgets.QDoubleSpinBox()
        self.depth_input.setRange(1.0, 500.0)
        self.depth_input.setValue(20.0)
        self.depth_input.setSuffix(" cm")

        self.height_input = QtWidgets.QDoubleSpinBox()
        self.height_input.setRange(1.0, 500.0)
        self.height_input.setValue(20.0)
        self.height_input.setSuffix(" cm")

        # Blender path
        self.blender_input = QtWidgets.QLineEdit()
        self.blender_input.setPlaceholderText("Blender executable path (optional)")

        # Run button
        self.run_button = QtWidgets.QPushButton("Generate Model")
        self.run_button.clicked.connect(self.generate_model)

        # Log output
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)

        # Layout setup
        layout.addWidget(QtWidgets.QLabel("Image:"))
        layout.addWidget(self.image_label)
        layout.addWidget(self.image_button)
        
        layout.addWidget(QtWidgets.QLabel("Primitive:"))
        layout.addWidget(self.primitive_combo)

        # Dimensions layout - FIXED: Now includes all three dimensions
        layout.addWidget(QtWidgets.QLabel("Dimensions:"))
        dim_layout = QtWidgets.QHBoxLayout()
        dim_layout.addWidget(QtWidgets.QLabel("Width:"))
        dim_layout.addWidget(self.width_input)
        dim_layout.addWidget(QtWidgets.QLabel("Depth:"))
        dim_layout.addWidget(self.depth_input)
        dim_layout.addWidget(QtWidgets.QLabel("Height:"))
        dim_layout.addWidget(self.height_input)
        layout.addLayout(dim_layout)

        layout.addWidget(QtWidgets.QLabel("Blender Path:"))
        layout.addWidget(self.blender_input)
        layout.addWidget(self.run_button)
        layout.addWidget(QtWidgets.QLabel("Log:"))
        layout.addWidget(self.log)

        self.setLayout(layout)

    def select_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.image_path = path
            self.image_label.setText(os.path.basename(path))
            self.image_label.setStyleSheet("color: green;")

    def generate_model(self):
        if not hasattr(self, "image_path"):
            QtWidgets.QMessageBox.warning(self, "Error", "Select image first")
            return

        primitive = self.primitive_combo.currentText()
        blender_exec = find_blender(self.blender_input.text().strip() or None)

        width = self.width_input.value()
        depth = self.depth_input.value()
        height = self.height_input.value()

        # Determine model name - NEW LOGIC
        if self.model_name_input.text().strip():
            model_name = self.model_name_input.text().strip()
        else:
            # Use image name as default if no custom name provided
            model_name = os.path.splitext(os.path.basename(self.image_path))[0]

        self.log.append(f"Running pipeline for {os.path.basename(self.image_path)}...")
        self.log.append(f"Model name: {model_name}")
        self.log.append(f"Dimensions: {width}×{depth}×{height} cm")
        self.log.append(f"Output directory: {self.output_folder}")
        QtWidgets.QApplication.processEvents()

        try:
            # Create model directory with custom name - UPDATED
            out_dir = os.path.join(self.output_folder, model_name)
            
            # Check if model already exists
            if os.path.exists(out_dir):
                reply = QtWidgets.QMessageBox.question(
                    self, 
                    "Model Exists", 
                    f"Model '{model_name}' already exists in Gazebo models. Overwrite?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.No:
                    self.log.append("❌ Operation cancelled - model already exists")
                    return

            os.makedirs(out_dir, exist_ok=True)

            run_pipeline(
                self.image_path,
                out_dir,
                primitive,
                blender_exec,
                width,
                depth,
                height,
                log_func=self.log.append  # capture all logs
            )
            self.log.append(f"\n✅ Model created: {out_dir}")
            self.log.append("You can now use this model in Gazebo!\n")
            
        except subprocess.CalledProcessError as e:
            self.log.append(f"\n❌ Subprocess error: {e}\n")
        except Exception as e:
            self.log.append(f"\n❌ Unexpected error: {e}\n")

# ---- Main ----
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ModelGeneratorGUI()
    window.show()
    sys.exit(app.exec_())