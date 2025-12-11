import qrcode
from PIL import Image, ImageDraw, ImageFont

def create_roopak_qr():
    # 1. Configuration
    qr_data = "roopak is awesome"
    bottom_text = "(Verified and Authenticated by SkillKendra.)"
    file_name = "roopak_verified_qr.png"

    # 2. Generate the QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # 3. Setup Canvas for Text
    # We load a default font. For custom fonts, you would use ImageFont.truetype()
    try:
        # Try to use Arial or similar if available, otherwise default
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text size to ensure image is wide enough
    draw = ImageDraw.Draw(qr_img)
    # Get text bounding box
    left, top, right, bottom = draw.textbbox((0, 0), bottom_text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    # Calculate total image dimensions (QR + padding for text)
    qr_width, qr_height = qr_img.size
    total_width = max(qr_width, text_width + 40) # Ensure width fits text
    total_height = qr_height + text_height + 50 # Add space at bottom

    # Create new white background image
    final_img = Image.new('RGB', (total_width, total_height), 'white')

    # 4. Paste QR Code and Draw Text
    # Paste QR in the center
    qr_x = (total_width - qr_width) // 2
    final_img.paste(qr_img, (qr_x, 0))

    # Draw Text at the bottom
    draw_final = ImageDraw.Draw(final_img)
    text_x = (total_width - text_width) // 2
    text_y = qr_height + 15 # Padding between QR and text
    
    draw_final.text((text_x, text_y), bottom_text, fill="black", font=font)

    # 5. Save
    final_img.save(file_name)
    print(f"Success! Image saved as {file_name}")

if __name__ == "__main__":
    create_roopak_qr()