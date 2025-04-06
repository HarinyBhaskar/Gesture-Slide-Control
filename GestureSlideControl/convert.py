import os
import win32com.client

def convert_ppt_to_png(ppt_path, output_folder):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Start PowerPoint application
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = 1

    # Open the PowerPoint file
    presentation = powerpoint.Presentations.Open(ppt_path)

    # Export slides as PNG
    presentation.SaveAs(output_folder, 18)  # 18 = ppSaveAsPNG
    
    # Close the presentation and quit PowerPoint
    presentation.Close()
    powerpoint.Quit()

    print(f"Slides saved as PNG in: {output_folder}")

# Example Usage
ppt_file = r"C:\Users\harin\OneDrive\Desktop\mini\review.pptx"
output_dir = r"C:\Users\harin\OneDrive\Desktop\ProjD\OutputFolder"
convert_ppt_to_png(ppt_file, output_dir)