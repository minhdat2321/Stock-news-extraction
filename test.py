import subprocess

# Path to the .exe file
exe_path = r"C:/Git Project/Vnstock_news/Vnstock_Installer/setup_wizard.exe"

# Run the .exe file
result = subprocess.run([exe_path], capture_output=True, text=True)

# Print the output
print("Output:", result.stdout)
print("Errors:", result.stderr)

