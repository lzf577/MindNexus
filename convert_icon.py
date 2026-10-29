from PIL import Image, ImageChops

def main():
    img_path = r"D:\Mind Nexus\logo.png"
    out_path = r"D:\Mind Nexus\logo.ico"
    
    img = Image.open(img_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Trim transparent borders
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # Trim solid background (like white) if the corners are solid
    bg_pixel = img.getpixel((0,0))
    bg = Image.new(img.mode, img.size, bg_pixel)
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox2 = diff.getbbox()
    if bbox2:
        img = img.crop(bbox2)

    # Save as multi-size ICO
    icon_sizes = [(16,16), (32, 32), (48, 48), (64,64), (128, 128), (256, 256)]
    img.save(out_path, format="ICO", sizes=icon_sizes)
    print("Generated logo.ico successfully.")

if __name__ == "__main__":
    main()
