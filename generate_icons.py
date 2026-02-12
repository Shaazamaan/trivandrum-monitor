from PIL import Image
import os

def generate_icons():
    source = "logo-icon.png"
    if not os.path.exists(source):
        print(f"Error: {source} not found.")
        return

    img = Image.open(source)
    
    # Generate 192x192
    img_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    img_192.save("icon-192.png")
    print("Created icon-192.png")
    
    # Generate 512x512
    img_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    img_512.save("icon-512.png")
    print("Created icon-512.png")

if __name__ == "__main__":
    generate_icons()
